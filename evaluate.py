from __future__ import annotations

"""Evaluation routine for INCdeep-LLM."""

import os
import pickle
import random
import time
from pathlib import Path

import numpy as np
import torch

from node import NODE
from simulator import act, forward_data, getneighborNum, p_xor


def sanitize_filename(name: str, fallback: str = "output.txt") -> str:
    """Return a safe filename (no directory traversal), with fallback.

    Keeps only the basename and strips surrounding spaces. If the result is
    empty (or dot names), returns ``fallback``.
    """
    base = os.path.basename(str(name)).strip()
    if base in {"", ".", ".."}:
        return fallback
    return base


def _build_source_state(nodelist, neighbor_matrix, source_id, k_data, pre_data, source_state_size, K, M):
    """Construct the source-agent evaluation state vector.

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
        for m_idx in range(M):
            start = 2 * K + nb_idx * M * K + m_idx * K
            state[start:start + K] = nodelist[nb].receivememory[m_idx]
    return state


def _run_source_phase(test_nodelist, source_id, neighbor_matrix, links, K, M, source_state_size, agent_s, extrinsic_reward, source_send_id):
    """Run one greedy source decision phase during evaluation.

    Args:
        test_nodelist: List of evaluation nodes.
        source_id: Source node index.
        neighbor_matrix: Directed adjacency matrix.
        links: Link-success probability matrix.
        K: Generation size.
        M: Relay memory rows.
        source_state_size: Flattened source state dimension.
        agent_s: Source-side DQN agent.
        extrinsic_reward: Reward magnitude for rank gain/loss.

    Returns:
        tuple[float, int]: `(phase_reward, source_send_count)`.
    """
    test_nodelist[source_id].list_action = np.zeros(K)
    k_data = np.zeros(K)
    pre_data = np.zeros(K)
    k_data[0] = 1
    state = _build_source_state(test_nodelist, neighbor_matrix, source_id, k_data, pre_data, source_state_size, K, M)

    for t in range(K):
        xstate = np.resize(state, [1, source_state_size])
        with torch.no_grad():
            q = agent_s.get_q_val(xstate)
        action = act(q)
        test_nodelist[source_id].list_action[t] = action

        next_state = np.zeros(source_state_size)
        if t < K - 1:
            k_data = np.zeros(K)
            k_data[t + 1] = 1
            pre_data[t] = action
            next_state = _build_source_state(test_nodelist, neighbor_matrix, source_id, k_data, pre_data, source_state_size, K, M)
        state = next_state

    send_data = np.array(test_nodelist[source_id].list_action, copy=True)
    reward = forward_data(
        test_nodelist,
        links,
        neighbor_matrix,
        source_id,
        send_data,
        K,
        M,
        extrinsic_reward,
        source_send_id=source_send_id,
    )
    return reward, 1


def _run_relay_phase(test_nodelist, node_id, neighbor_matrix, links, K, M, relay_state_size, agent_r, extrinsic_reward):
    """Run greedy relay forwarding/recoding for one relay node.

    Args:
        test_nodelist: List of evaluation nodes.
        node_id: Relay node index.
        neighbor_matrix: Directed adjacency matrix.
        links: Link-success probability matrix.
        K: Generation size.
        M: Relay memory rows.
        relay_state_size: Flattened relay state dimension.
        agent_r: Relay-side DQN agent.
        extrinsic_reward: Reward magnitude for rank gain/loss.

    Returns:
        tuple[int, float, bool]:
            `(processed_packets, total_reward, relay_used_coding)`.
    """
    processed_packets = 0
    total_reward = 0
    relay_used_coding = False

    node = test_nodelist[node_id]
    if not node.receive_flag:
        return processed_packets, total_reward, relay_used_coding

    node.receive_flag = False
    while len(node.packet) > 0:
        processed_packets += 1
        last_packet = node.getpacket()
        if isinstance(last_packet, tuple) and len(last_packet) == 2:
            last_data, packet_source_send_id = last_packet
        else:
            last_data, packet_source_send_id = last_packet, None
        node.list_action = np.zeros(K)

        relay_data = np.array(last_data, copy=True)
        state = np.zeros(relay_state_size)
        state[0:K] = last_data
        state[K:2 * K] = node.codememory[0]

        neighbors = getneighborNum(neighbor_matrix, node_id)
        for nb_idx, nb in enumerate(neighbors):
            for m_idx in range(M):
                start = 2 * K + nb_idx * M * K + m_idx * K
                state[start:start + K] = test_nodelist[nb].receivememory[m_idx]

        coding_steps = min(node.codelen, M)
        for t in range(coding_steps):
            xstate = np.resize(state, [1, relay_state_size])
            with torch.no_grad():
                q = agent_r.get_q_val(xstate)
            action = act(q)
            node.list_action[t] = action

            next_state = np.zeros(relay_state_size)
            if action == 1:
                relay_data = p_xor(relay_data, node.codememory[t], K)
            if t < M - 1:
                next_state[0:K] = relay_data
                next_state[K:2 * K] = node.codememory[t + 1]
                for nb_idx, nb in enumerate(neighbors):
                    for m_idx in range(M):
                        start = 2 * K + nb_idx * M * K + m_idx * K
                        next_state[start:start + K] = test_nodelist[nb].receivememory[m_idx]
            state = next_state

        if any(a == 1 for a in node.list_action):
            relay_used_coding = True

        node.codememory[int(node.codelen % M)] = last_data
        node.codelen += 1

        total_reward += forward_data(
            test_nodelist,
            links,
            neighbor_matrix,
            node_id,
            relay_data,
            K,
            M,
            extrinsic_reward,
            source_send_id=packet_source_send_id,
        )

    return processed_packets, total_reward, relay_used_coding


def run_evaluate(
    *,
    e,
    Max_test,
    Max_s_f,
    node_num,
    K,
    M=None,
    R=None,
    S_state_size,
    R_state_size,
    source_id,
    neighbor_matrix,
    links,
    extrinsic_reward,
    agent_s,
    agent_r,
    best_state_path,
    result_dir,
    model_dir,
    min_f,
    source_send_count_list,
    test_log_filename="evaluation_avg_source_sends.txt",
    reward_log_filename="evaluation_reward.txt",
    show_test_progress=True,
):
    """Run evaluation episodes and aggregate metrics.

    Args:
        e: Current training episode index.
        Max_test: Number of evaluation episodes.
        Max_s_f: Maximum source sends per evaluation episode.
        node_num: Number of nodes in topology.
        K: Generation size.
        M: Relay memory rows.
        R: Legacy alias for relay memory rows.
        S_state_size: Flattened source state dimension.
        R_state_size: Flattened relay state dimension.
        source_id: Source node index.
        neighbor_matrix: Directed adjacency matrix.
        links: Link-success probability matrix.
        extrinsic_reward: Reward magnitude for rank gain/loss.
        agent_s: Source-side DQN agent.
        agent_r: Relay-side DQN agent.
        best_state_path: Path to serialized best random-state snapshot.
        result_dir: Directory for evaluation logs.
        model_dir: Model directory (kept for compatibility).
        min_f: Best historical average source-send metric.
        source_send_count_list: Collector for per-episode source-send counts.
        test_log_filename: Filename for average source-send logs.
        reward_log_filename: Filename for reward logs.
        show_test_progress: Whether to print per-test remaining time.

    Returns:
        tuple[float, float, float, bool, tuple]:
            `(min_f, avg_overhead, avg_source_send, is_best, random_states)`.
    """
    if M is None:
        if R is None:
            raise ValueError("run_evaluate requires M (or legacy R) to be provided")
        M = R
    fl_path = os.path.join(result_dir, sanitize_filename(test_log_filename, fallback="evaluation_avg_source_sends.txt"))
    fe_path = os.path.join(result_dir, sanitize_filename(reward_log_filename, fallback="evaluation_reward.txt"))

    avg_reward = 0.0
    avg_source_send = 0.0
    avg_overhead = 0.0

    if best_state_path.exists():
        with open(best_state_path, "rb") as f:
            best_state = pickle.load(f)["best_state"]
        np.random.set_state(best_state[0])
        random.setstate(best_state[1])

    start_time = time.time()
    np_random_state = np.random.get_state()
    random_state = random.getstate()

    for test_idx in range(Max_test):
        total_reward = 0.0
        test_nodelist = [NODE(K, M, i) for i in range(node_num)]
        should_start_from_source = True
        source_send_count = 0

        while source_send_count < Max_s_f:
            if should_start_from_source:
                reward, send_count = _run_source_phase(
                    test_nodelist,
                    source_id,
                    neighbor_matrix,
                    links,
                    K,
                    M,
                    S_state_size,
                    agent_s,
                    extrinsic_reward,
                    source_send_count + 1,
                )
                total_reward += reward
                source_send_count += send_count
                should_start_from_source = False
                continue

            processed_packets = 0
            for node_id in range(node_num - 1):
                node_processed, node_reward, _ = _run_relay_phase(test_nodelist, node_id, neighbor_matrix, links, K, M, R_state_size, agent_r, extrinsic_reward)
                processed_packets += node_processed
                total_reward += node_reward

            if processed_packets == 0:
                should_start_from_source = True
                dest_node = test_nodelist[node_num - 1]
                dest_rank_ok = np.linalg.matrix_rank(dest_node.datamemory) == K
                dest_unique_source_packets_ok = len(dest_node.received_source_send_ids) >= K
                if dest_rank_ok and dest_unique_source_packets_ok:
                    break

        # Normalize episode reward by source send count for this episode
        # before averaging across evaluation episodes.
        normalized_reward = total_reward / max(source_send_count, 1)

        avg_reward += normalized_reward
        source_send_count_list.append(source_send_count)
        avg_source_send += source_send_count
        avg_overhead += (1 / K) * (len(test_nodelist[node_num - 1].datamemory) - K) * 100

        if show_test_progress:
            elapsed_time = time.time() - start_time
            average_time = elapsed_time / (test_idx + 1)
            remaining_time = average_time * (Max_test - (test_idx + 1))
            print("\r test: %d, remaining: %d s" % (test_idx, remaining_time), end="")

    avg_source_send /= Max_test
    avg_reward /= Max_test
    avg_overhead /= Max_test

    with open(fl_path, "a+", encoding="utf-8") as fl, open(fe_path, "a+", encoding="utf-8") as fe:
        print(e, " ", avg_source_send, file=fl)
        print(" ", file=fl)
        print(e, " ", avg_reward, file=fe)
        print(" ", file=fe)

    is_best = avg_source_send < min_f
    return min_f, avg_overhead, avg_source_send, is_best, (np_random_state, random_state)
