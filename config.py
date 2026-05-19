# config.py
from __future__ import annotations

import torch

EPISODES = 1

# --- Simulation semantics (paper notation -> engineering meaning) ---
# K: number of original source symbols per generation.
# M: relay coding-memory rows (max coding depth per relay decision cycle).
K = 10
M = 8

# Evaluation budget per training checkpoint.
Max_test = 10
# Max number of source transmission rounds allowed in one episode/test.
Max_s_f = 50

# Use the first available CUDA device when present for portability.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

batch_size = 128
extrinsic_reward = 1
epsilon = 1
S_conv1_out_channels = 16
S_conv2_out_channels = 32
R_conv1_out_channels = 16
R_conv2_out_channels = 32

S_conv1_kernel_size = 5
S_conv2_kernel_size = 5
R_conv1_kernel_size = 5
R_conv2_kernel_size = 5
fc1_out_features = 512

epsilon_min = 0.01
epsilon_period = 1000
action_size = 2
inital_epsilon = 1
restart_max = 30