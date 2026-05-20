from __future__ import annotations

"""Training entry for INCdeep-LLM.

This module keeps the original algorithmic behavior intact while organizing
training into small, named helpers so the episode lifecycle is easier to read.
"""

import argparse
import datetime
import os
import pickle
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from config_parser import load_config
from evaluate import run_evaluate
from node import NODE
from simulator import act_noise, calculate_reward, forward_data, getneighborNum, p_xor
from utils.dqn_R import DQNAgent_R
from utils.dqn_S import DQNAgent_S


torch.backends.cudnn.enabled = False
np.set_printoptions(threshold=np.inf)

seed = 555
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = BASE_DIR / "models"
DEFAULT_RESULT_DIR = BASE_DIR / "result"

TRAIN_SOURCE_SEND_LOG = "train_source_send_counts.txt"
EVAL_SOURCE_SEND_LOG = "evaluation_avg_source_sends.txt"
EVAL_REWARD_LOG = "evaluation_reward.txt"

torch.manual_seed(seed)
np.random.seed(seed)


def build_parser():
    """Create the CLI parser for training.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """
    parser = argparse.ArgumentParser(description="INCdeep-LLM training")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR), help="Directory for saving best model files")
    parser.add_argument("--result-dir", default=str(DEFAULT_RESULT_DIR), help="Directory for generated outputs")
    parser.add_argument("--best-state", default=str(DEFAULT_MODEL_DIR / "best_epoch.pkl"), help="Path to save best random state")
    parser.add_argument("--skip-compile", action="store_true", help="Disable torch.compile for compatibility")
    return parser


def resolve_paths(args):
    """Resolve runtime output paths and create missing directories.

    Args:
        args: Parsed CLI arguments.

    Returns:
        tuple[Path, Path, Path, Path]:
            `(result_dir, model_dir, best_state_path, best_model_dir)`.
    """
    result_dir = Path(args.result_dir)
    if not result_dir.is_absolute():
        result_dir = BASE_DIR / result_dir

    model_dir = Path(args.model_dir)
    if not model_dir.is_absolute():
        model_dir = BASE_DIR / model_dir

    best_state_path = Path(args.best_state)
    if not best_state_path.is_absolute():
        best_state_path = model_dir / best_state_path

    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    best_model_dir = model_dir / "best_by_avg_source_send"
    os.makedirs(best_model_dir, exist_ok=True)

    return result_dir, model_dir, best_state_path, best_model_dir


def init_source_episode_buffers(node, K):
    """Reset per-step transition buffers for one node.

    Args:
        node: Node instance whose episode buffers are reset.
        K: Generation size.

    Returns:
        None
    """
    node.list_action = np.zeros(K)
    node.list_state = []
    node.list_n_state = []
    node.list_len = 0
    node.list_rewards = np.zeros(K)


def build_source_state(nodelist, neighbor_matrix, source_id, k_data, pre_data, source_state_size, K, M):
    """Construct the source-agent state vector.

    Args:
        nodelist: List of network nodes.
        neighbor_matrix: Directed adjacency matrix.
        source_id: Source node index.
        k_data: One-hot phase indicator vector.
        pre_data: Previously selected source actions.
        source_state_size: Flattened source state dimension.
        K: Generation size.
        M: Relay memory rows.

    Returns:
        np.ndarray: Flattened source state.
    """
    state = np.zeros(source_state_size)
    state[0:K] = k_data
    state[K:2 * K] = pre_data
    neighbors = getneighborNum(neighbor_matrix, source_id)
    for nb_idx, nb in enumerate(neighbors):
        for r_idx in range(M):
            start = 2 * K + nb_idx * M * K + r_idx * K
            state[start:start + K] = nodelist[nb].receivememory[r_idx]
    return state


def run_source_transmission_cycle(nodelist, source_id, neighbor_matrix, links, K, M, source_state_size, action_size, agent_s, extrinsic_reward):
    """Run one source transmission decision cycle for a generation.

    Args:
        nodelist: List of network nodes.
        source_id: Source node index.
        neighbor_matrix: Directed adjacency matrix.
        links: Link-success probability matrix.
        K: Generation size.
        M: Relay memory rows.
        source_state_size: Flattened source state dimension.
        action_size: Number of source actions.
        agent_s: Source-side DQN agent.
        extrinsic_reward: Reward magnitude for rank gain/loss.

    Returns:
        int: Number of source sends consumed in this cycle.
    """
    init_source_episode_buffers(nodelist[source_id], K)

    source_send_count = 1
    k_data = np.zeros(K)
    pre_data = np.zeros(K)
    k_data[0] = 1
    state = build_source_state(nodelist, neighbor_matrix, source_id, k_data, pre_data, source_state_size, K, M)

    for t in range(K):
        nodelist[source_id].list_len += 1
        nodelist[source_id].list_state.append(state)
        xstate = np.resize(state, [1, source_state_size])

        with torch.no_grad():
            q = agent_s.get_q_val(xstate)
        action = act_noise(q, action_size, agent_s.epsilon)
        nodelist[source_id].list_action[t] = action

        next_state = np.zeros(source_state_size)
        if t < K - 1:
            k_data = np.zeros(K)
            k_data[t + 1] = 1
            pre_data[t] = action
            next_state = build_source_state(nodelist, neighbor_matrix, source_id, k_data, pre_data, source_state_size, K, M)

        nodelist[source_id].list_n_state.append(next_state)
        state = next_state

    send_data = np.array(nodelist[source_id].list_action, copy=True)
    rewards = forward_data(nodelist, links, neighbor_matrix, source_id, send_data, K, M, extrinsic_reward)
    for idx in range(nodelist[source_id].list_len):
        nodelist[source_id].list_rewards[idx] = rewards

    return source_send_count


def run_relay_forward_cycle(nodelist, node_id, neighbor_matrix, links, K, M, relay_state_size, action_size, agent_r, extrinsic_reward):
    """Run relay forwarding/recoding for all queued packets at one relay node.

    Args:
        nodelist: List of network nodes.
        node_id: Relay node index.
        neighbor_matrix: Directed adjacency matrix.
        links: Link-success probability matrix.
        K: Generation size.
        M: Relay memory rows.
        relay_state_size: Flattened relay state dimension.
        action_size: Number of relay actions.
        agent_r: Relay-side DQN agent.
        extrinsic_reward: Reward magnitude for rank gain/loss.

    Returns:
        int: Number of processed packets at this node.
    """
    processed_packets = 0
    node = nodelist[node_id]

    if not node.receive_flag:
        return processed_packets

    node.receive_flag = False
    while len(node.packet) > 0:
        processed_packets += 1
        last_data = node.getpacket()

        init_source_episode_buffers(node, K)

        relay_data = np.array(last_data, copy=True)
        state = np.zeros(relay_state_size)
        state[0:K] = last_data
        state[K:2 * K] = node.codememory[0]

        neighbors = getneighborNum(neighbor_matrix, node_id)
        for nb_idx, nb in enumerate(neighbors):
            for r_idx in range(M):
                start = 2 * K + nb_idx * M * K + r_idx * K
                state[start:start + K] = nodelist[nb].receivememory[r_idx]

        code_len = node.codelen
        coding_steps = np.minimum(code_len, M)
        for t in range(coding_steps):
            node.list_len += 1
            node.list_state.append(state)
            xstate = np.resize(state, [1, relay_state_size])

            with torch.no_grad():
                q = agent_r.get_q_val(xstate)
            action = act_noise(q, action_size, agent_r.epsilon)
            node.list_action[t] = action

            next_state = np.zeros(relay_state_size)
            if action == 1:
                relay_data = p_xor(relay_data, node.codememory[t], K)
            if t < M - 1:
                next_state[0:K] = relay_data
                next_state[K:2 * K] = node.codememory[t + 1]
                for nb_idx, nb in enumerate(neighbors):
                    for r_idx in range(M):
                        start = 2 * K + nb_idx * M * K + r_idx * K
                        next_state[start:start + K] = nodelist[nb].receivememory[r_idx]

            node.list_n_state.append(next_state)
            state = next_state

        code_len = node.codelen
        node.codememory[int(code_len % M)] = last_data
        node.codelen += 1

        rewards = forward_data(nodelist, links, neighbor_matrix, node_id, relay_data, K, M, extrinsic_reward)
        for idx in range(node.list_len):
            node.list_rewards[idx] = rewards

    return processed_packets


def flush_episode_memory_to_replay(nodelist, node_num, K, agent_s, agent_r):
    """Flush collected per-node transitions into replay buffers.

    Args:
        nodelist: List of network nodes.
        node_num: Number of nodes.
        K: Generation size.
        agent_s: Source-side DQN agent.
        agent_r: Relay-side DQN agent.

    Returns:
        None
    """
    for node_id in range(node_num):
        node = nodelist[node_id]
        for j in range(node.list_len):
            done = 1 if j == K - 1 else 0
            if node_id == 0:
                agent_s.remember(node.list_state[j], node.list_action[j], node.list_rewards[j], node.list_n_state[j], done)
            else:
                agent_r.remember(node.list_state[j], node.list_action[j], node.list_rewards[j], node.list_n_state[j], done)


def update_epsilon(agent_s, agent_r, episode_idx, epsilon_period, initial_epsilon, epsilon_min):
    """Update epsilon for both agents using linear decay.

    Args:
        agent_s: Source-side DQN agent.
        agent_r: Relay-side DQN agent.
        episode_idx: Current episode index.
        epsilon_period: Number of decay episodes.
        initial_epsilon: Initial exploration rate.
        epsilon_min: Minimum exploration rate.

    Returns:
        None
    """
    if episode_idx > epsilon_period:
        epsilon = epsilon_min
    else:
        epsilon = initial_epsilon - float(episode_idx) * (initial_epsilon - epsilon_min) / epsilon_period
    agent_s.epsilon = epsilon
    agent_r.epsilon = epsilon


@dataclass
class EpisodeRuntime:
    """Compact runtime context to reduce long parameter chains."""

    source_id: int
    node_num: int
    neighbor_matrix: np.ndarray
    links: np.ndarray
    K: int
    M: int
    source_state_size: int
    relay_state_size: int
    action_size: int
    max_source_sends: int
    extrinsic_reward: float


def run_single_episode(*, nodelist, runtime: EpisodeRuntime, agent_s, agent_r):
    """Execute one complete training episode.

    Args:
        nodelist: List of initialized nodes.
        runtime: Episode runtime configuration.
        agent_s: Source-side DQN agent.
        agent_r: Relay-side DQN agent.

    Returns:
        int: Source-send count used by this episode.
    """
    should_start_from_source = True
    source_send_count = 0

    while source_send_count < runtime.max_source_sends:
        dest_idx = runtime.node_num - 1
        round_dest_rank_before = np.linalg.matrix_rank(nodelist[dest_idx].datamemory)

        if should_start_from_source:
            source_send_count += run_source_transmission_cycle(
                nodelist=nodelist,
                source_id=runtime.source_id,
                neighbor_matrix=runtime.neighbor_matrix,
                links=runtime.links,
                K=runtime.K,
                M=runtime.M,
                source_state_size=runtime.source_state_size,
                action_size=runtime.action_size,
                agent_s=agent_s,
                extrinsic_reward=runtime.extrinsic_reward,
            )
            should_start_from_source = False
            continue

        processed_packets = 0
        for node_id in range(runtime.node_num - 1):
            processed_packets += run_relay_forward_cycle(
                nodelist=nodelist,
                node_id=node_id,
                neighbor_matrix=runtime.neighbor_matrix,
                links=runtime.links,
                K=runtime.K,
                M=runtime.M,
                relay_state_size=runtime.relay_state_size,
                action_size=runtime.action_size,
                agent_r=agent_r,
                extrinsic_reward=runtime.extrinsic_reward,
            )

        if processed_packets == 0:
            should_start_from_source = True

            round_dest_rank_after = np.linalg.matrix_rank(nodelist[dest_idx].datamemory)
            round_rank_add_des = round_dest_rank_after - round_dest_rank_before
            destination_bonus = calculate_reward(
                runtime.K,
                round_rank_add_des,
                round_dest_rank_after,
                0.0,
                add_destination_bonus=True,
            )

            # Apply the round-end destination bonus to all nodes that have
            # collected transitions in this round.
            for node in nodelist:
                for idx in range(node.list_len):
                    node.list_rewards[idx] += destination_bonus

            rank = round_dest_rank_after
            flush_episode_memory_to_replay(nodelist, runtime.node_num, runtime.K, agent_s, agent_r)
            if rank == runtime.K:
                break

    return source_send_count


def main(argv=None):
    """Run training from CLI arguments.

    Args:
        argv: Optional argument list overriding `sys.argv`.

    Returns:
        None
    """
    args = build_parser().parse_args(argv)
    start_time = time.time()

    config = load_config()
    node_num = config["node_count"]
    neighbor_matrix = config["neighbor_matrix"]
    links = config["links"]
    device = config["device"]
    max_source_sends = config["max_source_sends_per_episode"]
    episodes = config["num_episodes"]
    max_test = config["num_eval_episodes"]
    extrinsic_reward = config["extrinsic_reward"]
    parallel_path = config["num_parallel_paths"]
    max_nb = config["max_neighbor_count"]
    K = config["generation_size"]
    M = config["relay_memory_rows"]
    action_size = config["action_size"]
    epsilon_period = config["epsilon_decay_episodes"]
    initial_epsilon = config["initial_epsilon"]
    epsilon_min = config["epsilon_min"]

    source_state_size = (M * parallel_path + 2) * K
    relay_state_size = (M * max_nb + 2) * K

    source_id = 0
    runtime = EpisodeRuntime(
        source_id=source_id,
        node_num=node_num,
        neighbor_matrix=neighbor_matrix,
        links=links,
        K=K,
        M=M,
        source_state_size=source_state_size,
        relay_state_size=relay_state_size,
        action_size=action_size,
        max_source_sends=max_source_sends,
        extrinsic_reward=extrinsic_reward,
    )

    agent_s = DQNAgent_S(source_state_size, config, device)
    agent_r = DQNAgent_R(relay_state_size, config, device)

    if not args.skip_compile and hasattr(torch, "compile"):
        agent_s = torch.compile(agent_s)
        agent_r = torch.compile(agent_r)

    result_dir, model_dir, best_state_path, best_model_dir = resolve_paths(args)

    source_send_count_list = []
    best_avg_source_send = max_source_sends

    for episode_idx in range(episodes):
        nodelist = [NODE(K, M, i) for i in range(node_num)]
        source_send_count = run_single_episode(
            nodelist=nodelist,
            runtime=runtime,
            agent_s=agent_s,
            agent_r=agent_r,
        )

        update_epsilon(agent_s, agent_r, episode_idx, epsilon_period, initial_epsilon, epsilon_min)

        train_log_path = os.path.join(str(result_dir), TRAIN_SOURCE_SEND_LOG)
        with open(train_log_path, "a+", encoding="utf-8") as fz:
            print(episode_idx, " ", source_send_count, file=fz)
            print(" ", file=fz)

        previous_best = best_avg_source_send
        show_eval_progress = ((episode_idx + 1) % 10 == 0)
        best_avg_source_send, avg_overhead, avg_s_f, is_best, best_state = run_evaluate(
            e=episode_idx,
            Max_test=max_test,
            Max_s_f=max_source_sends,
            node_num=node_num,
            K=K,
            M=M,
            S_state_size=source_state_size,
            R_state_size=relay_state_size,
            source_id=source_id,
            neighbor_matrix=neighbor_matrix,
            links=links,
            extrinsic_reward=extrinsic_reward,
            agent_s=agent_s,
            agent_r=agent_r,
            best_state_path=best_state_path,
            result_dir=result_dir,
            model_dir=model_dir,
            min_f=best_avg_source_send,
            source_send_count_list=source_send_count_list,
            test_log_filename=EVAL_SOURCE_SEND_LOG,
            reward_log_filename=EVAL_REWARD_LOG,
            show_test_progress=show_eval_progress,
        )

        if is_best:
            best_avg_source_send = avg_s_f
            agent_s.save_network(path=str(best_model_dir / "dqn_agent_s_min.pt"))
            agent_r.save_network(path=str(best_model_dir / "dqn_agent_r_min.pt"))
            with open(best_model_dir / "best_epoch.pkl", "wb") as f:
                pickle.dump({"best_state": best_state}, f)
            with open(best_model_dir / "best_metric.txt", "w", encoding="utf-8") as f:
                f.write(f"episode={episode_idx}\n")
                f.write(f"avg_source_send={avg_s_f}\n")
                f.write(f"previous_best={previous_best}\n")

        elapsed_time = time.time() - start_time
        average_time = elapsed_time / (episode_idx + 1)
        remaining_time = average_time * (episodes - (episode_idx + 1))
        if episode_idx % 10 == 0:
            print("\r episode: %d, remaining: %d s" % (episode_idx, remaining_time), end="")



if __name__ == "__main__":
    main()
