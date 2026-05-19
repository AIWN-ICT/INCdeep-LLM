from __future__ import annotations

"""Configuration adapter for training and evaluation modules.

This module maps values from `config.py` and `config_topology.py` into a
single runtime dictionary and preserves legacy aliases for compatibility.
"""

import config
import config_topology


def load_config():
    """Load semantic config keys and backward-compatible aliases.

    Returns:
        dict: Unified configuration dictionary used across the project.
    """
    cfg = {
        # Preferred semantic keys
        "num_episodes": config.EPISODES,
        "num_eval_episodes": config.Max_test,
        "generation_size": config.K,
        "relay_memory_rows": config.M,
        "device": config.device,
        "batch_size": config.batch_size,
        "extrinsic_reward": config.extrinsic_reward,
        "epsilon": config.epsilon,
        "epsilon_min": config.epsilon_min,
        "epsilon_decay_episodes": config.epsilon_period,
        "num_parallel_paths": config_topology.parallel_path,
        "max_neighbor_count": config_topology.max_nb,
        "S_conv1_out_channels": config.S_conv1_out_channels,
        "S_conv2_out_channels": config.S_conv2_out_channels,
        "R_conv1_out_channels": config.R_conv1_out_channels,
        "R_conv2_out_channels": config.R_conv2_out_channels,
        "S_conv1_kernel_size": config.S_conv1_kernel_size,
        "S_conv2_kernel_size": config.S_conv2_kernel_size,
        "R_conv1_kernel_size": config.R_conv1_kernel_size,
        "R_conv2_kernel_size": config.R_conv2_kernel_size,
        "fc1_out_features": config.fc1_out_features,
        "action_size": config.action_size,
        "max_source_sends_per_episode": config.Max_s_f,
        "initial_epsilon": config.inital_epsilon,
        "restart_max": config.restart_max,
        "node_count": config_topology.node_num,
        "neighbor_matrix": config_topology.neighbor_matrix,
        "links": config_topology.links,
    }

    # Backward-compatible aliases (legacy key names)
    cfg.update(
        {
            "EPISODES": cfg["num_episodes"],
            "Max_test": cfg["num_eval_episodes"],
            "K": cfg["generation_size"],
            "M": cfg["relay_memory_rows"],
            "R": cfg["relay_memory_rows"],
            "epsilon_period": cfg["epsilon_decay_episodes"],
            "parallel_path": cfg["num_parallel_paths"],
            "max_nb": cfg["max_neighbor_count"],
            "Max_s_f": cfg["max_source_sends_per_episode"],
            "inital_epsilon": cfg["initial_epsilon"],
            "node_num": cfg["node_count"],
        }
    )
    return cfg
