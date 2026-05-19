<<<<<<< HEAD
from __future__ import annotations

"""Standalone testing entry for INCdeep-LLM.

Loads saved best checkpoints and runs evaluation without training updates.
"""

import argparse
import os
from pathlib import Path

import numpy as np
import torch

import data_processor
from config_parser import load_config
from evaluate import run_evaluate
from utils.dqn_R import DQNAgent_R
from utils.dqn_S import DQNAgent_S


torch.backends.cudnn.enabled = False
np.set_printoptions(threshold=np.inf)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = BASE_DIR / "models" / "examples" / "best_by_avg_source_send"
DEFAULT_RESULT_DIR = BASE_DIR / "result"
PACKET_LOG_DIR = BASE_DIR / "Packet_log"
METRICS_DIR = BASE_DIR / "data_INCdeep_LLM"
PACKET_COUNT_LOG = "source_send_counts.csv"
AGGREGATED_METRICS_BASENAME = "decode_probability_overhead_summary"


def build_parser():
    """Create the CLI parser for standalone evaluation.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """
    parser = argparse.ArgumentParser(description="INCdeep-LLM testing")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR), help="Directory containing pretrained model files")
    parser.add_argument("--result-dir", default=str(DEFAULT_RESULT_DIR), help="Directory for generated outputs")
    parser.add_argument("--best-state", default=str(DEFAULT_MODEL_DIR / "best_epoch.pkl"), help="Path to the saved best random state file")
    parser.add_argument("--skip-compile", action="store_true", help="Disable torch.compile for compatibility")
    return parser


def safe_load_network(agent, model_path):
    """Load model parameters from disk.

    Args:
        agent: Agent instance that exposes `load_network`.
        model_path: Filesystem path to checkpoint file.

    Returns:
        None

    Raises:
        FileNotFoundError: If `model_path` does not exist.
    """
    if os.path.exists(model_path):
        agent.load_network(model_path)
    else:
        raise FileNotFoundError(f"Required model file not found: {model_path}")


def resolve_paths(args):
    """Resolve runtime paths for standalone testing.

    Args:
        args: Parsed CLI arguments.

    Returns:
        tuple[Path, Path, Path]: `(result_dir, model_dir, best_state_path)`.
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
    return result_dir, model_dir, best_state_path


def main(argv=None):
    """Run standalone evaluation with saved best checkpoints.

    Args:
        argv: Optional CLI argument list.

    Returns:
        None
    """
    args = build_parser().parse_args(argv)

    config = load_config()
    node_num = config["node_count"]
    neighbor_matrix = config["neighbor_matrix"]
    links = config["links"]
    device = config["device"]
    max_source_sends = config["max_source_sends_per_episode"]
    max_test = config["num_eval_episodes"]
    extrinsic_reward = config["extrinsic_reward"]
    parallel_path = config["num_parallel_paths"]
    max_nb = config["max_neighbor_count"]
    K = config["generation_size"]
    M = config["relay_memory_rows"]

    source_state_size = (M * parallel_path + 2) * K
    relay_state_size = (M * max_nb + 2) * K

    source_id = 0
    agent_s = DQNAgent_S(source_state_size, config, device)
    agent_r = DQNAgent_R(relay_state_size, config, device)

    if not args.skip_compile and hasattr(torch, "compile"):
        agent_s = torch.compile(agent_s)
        agent_r = torch.compile(agent_r)

    result_dir, model_dir, best_state_path = resolve_paths(args)

    safe_load_network(agent_r, str(model_dir / "dqn_agent_r_min.pt"))
    safe_load_network(agent_s, str(model_dir / "dqn_agent_s_min.pt"))

    source_send_count_list = []
    best_avg_source_send = max_source_sends

    best_avg_source_send, avg_overhead, avg_s_f, _is_best, _best_state = run_evaluate(
        e=0,
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
    )

    data_processor.write_counts_to_csv(source_send_count_list, str(PACKET_LOG_DIR), PACKET_COUNT_LOG)
    decode_probability = data_processor.calculate_decode_probability(source_send_count_list)
    data_processor.write_results_to_csv(
        AGGREGATED_METRICS_BASENAME,
        decode_probability,
        avg_overhead,
        data_processor.std_dev(source_send_count_list),
        avg_s_f,
        str(METRICS_DIR),
    )

    print(f"Test done. avg_s_f={avg_s_f:.4f}, avg_overhead={avg_overhead:.4f}")


if __name__ == "__main__":
    main()
=======
from __future__ import annotations

"""Standalone testing entry for INCdeep-LLM.

Loads saved best checkpoints and runs evaluation without training updates.
"""

import argparse
import os
from pathlib import Path

import numpy as np
import torch

import data_processor
from config_parser import load_config
from evaluate import run_evaluate
from utils.dqn_R import DQNAgent_R
from utils.dqn_S import DQNAgent_S


torch.backends.cudnn.enabled = False
np.set_printoptions(threshold=np.inf)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = BASE_DIR / "models" / "examples" / "best_by_avg_source_send"
DEFAULT_RESULT_DIR = BASE_DIR / "result"
PACKET_LOG_DIR = BASE_DIR / "Packet_log"
METRICS_DIR = BASE_DIR / "data_INCdeep_LLM"
PACKET_COUNT_LOG = "source_send_counts.csv"
AGGREGATED_METRICS_BASENAME = "decode_probability_overhead_summary"


def build_parser():
    """Create the CLI parser for standalone evaluation.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """
    parser = argparse.ArgumentParser(description="INCdeep-LLM testing")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR), help="Directory containing pretrained model files")
    parser.add_argument("--result-dir", default=str(DEFAULT_RESULT_DIR), help="Directory for generated outputs")
    parser.add_argument("--best-state", default=str(DEFAULT_MODEL_DIR / "best_epoch.pkl"), help="Path to the saved best random state file")
    parser.add_argument("--skip-compile", action="store_true", help="Disable torch.compile for compatibility")
    return parser


def safe_load_network(agent, model_path):
    """Load model parameters from disk.

    Args:
        agent: Agent instance that exposes `load_network`.
        model_path: Filesystem path to checkpoint file.

    Returns:
        None

    Raises:
        FileNotFoundError: If `model_path` does not exist.
    """
    if os.path.exists(model_path):
        agent.load_network(model_path)
    else:
        raise FileNotFoundError(f"Required model file not found: {model_path}")


def resolve_paths(args):
    """Resolve runtime paths for standalone testing.

    Args:
        args: Parsed CLI arguments.

    Returns:
        tuple[Path, Path, Path]: `(result_dir, model_dir, best_state_path)`.
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
    return result_dir, model_dir, best_state_path


def main(argv=None):
    """Run standalone evaluation with saved best checkpoints.

    Args:
        argv: Optional CLI argument list.

    Returns:
        None
    """
    args = build_parser().parse_args(argv)

    config = load_config()
    node_num = config["node_count"]
    neighbor_matrix = config["neighbor_matrix"]
    links = config["links"]
    device = config["device"]
    max_source_sends = config["max_source_sends_per_episode"]
    max_test = config["num_eval_episodes"]
    extrinsic_reward = config["extrinsic_reward"]
    parallel_path = config["num_parallel_paths"]
    max_nb = config["max_neighbor_count"]
    K = config["generation_size"]
    M = config["relay_memory_rows"]

    source_state_size = (M * parallel_path + 2) * K
    relay_state_size = (M * max_nb + 2) * K

    source_id = 0
    agent_s = DQNAgent_S(source_state_size, config, device)
    agent_r = DQNAgent_R(relay_state_size, config, device)

    if not args.skip_compile and hasattr(torch, "compile"):
        agent_s = torch.compile(agent_s)
        agent_r = torch.compile(agent_r)

    result_dir, model_dir, best_state_path = resolve_paths(args)

    safe_load_network(agent_r, str(model_dir / "dqn_agent_r_min.pt"))
    safe_load_network(agent_s, str(model_dir / "dqn_agent_s_min.pt"))

    source_send_count_list = []
    best_avg_source_send = max_source_sends

    best_avg_source_send, avg_overhead, avg_s_f, _is_best, _best_state = run_evaluate(
        e=0,
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
    )

    data_processor.write_counts_to_csv(source_send_count_list, str(PACKET_LOG_DIR), PACKET_COUNT_LOG)
    decode_probability = data_processor.calculate_decode_probability(source_send_count_list)
    data_processor.write_results_to_csv(
        AGGREGATED_METRICS_BASENAME,
        decode_probability,
        avg_overhead,
        data_processor.std_dev(source_send_count_list),
        avg_s_f,
        str(METRICS_DIR),
    )

    print(f"Test done. avg_s_f={avg_s_f:.4f}, avg_overhead={avg_overhead:.4f}")


if __name__ == "__main__":
    main()
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
