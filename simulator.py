from __future__ import annotations

"""Environment-side helper functions for forwarding and coding simulation.

This module provides action policies, XOR-based packet combination,
neighborhood queries, and reward-producing forwarding transitions.
"""

import random

import numpy as np


def act_noise(q, action_size, epsilon):
    """Sample an action using epsilon-greedy exploration.

    Args:
        q: Q-value array for available actions.
        action_size: Number of discrete actions.
        epsilon: Exploration probability.

    Returns:
        Selected action index.
    """
    rd = np.random.rand()
    if rd <= epsilon:
        a = random.randrange(action_size)
        return int(a)
    return int(np.argmax(q))


def act(q):
    """Select the greedy action from Q-values.

    Args:
        q: Q-value array for available actions.

    Returns:
        Action index with maximum Q-value.
    """
    return int(np.argmax(q))


def p_xor(p1, p2, K):
    """Compute binary XOR between two coded packets.

    Args:
        p1: First packet vector.
        p2: Second packet vector.
        K: Generation size.

    Returns:
        XOR-combined packet vector.
    """
    p_new = np.zeros(K)
    for i in range(K):
        p_new[i] = 0 if p1[i] == p2[i] else 1
    return p_new


def getneighborNum(nb_M, node_id):
    """Return forward neighbors of a node from adjacency matrix.

    Args:
        nb_M: Directed adjacency matrix.
        node_id: Current node index.

    Returns:
        List of reachable downstream node indices.
    """
    num = []
    for i in range(node_id + 1, len(nb_M)):
        if nb_M[node_id][i] == 1:
            num.append(i)
    return num


def forward_data(nodelist, links, neighbor_M, node_id, data, K, M, extrinsic_reward):
    """Forward one packet/vector to all downstream neighbors and accumulate reward.

    Reward is positive when the received packet increases destination rank at the
    receiving node, and negative otherwise.

    Args:
        nodelist: List of node objects in the environment.
        links: Link-success probability matrix.
        neighbor_M: Directed adjacency matrix.
        node_id: Sender node index.
        data: Packet/coding vector to forward.
        K: Generation size.
        M: Receiver memory depth.
        extrinsic_reward: Absolute reward magnitude.

    Returns:
        Sum of rewards over all attempted transmissions.
    """
    sum_reward = 0
    for i in range(node_id + 1, len(neighbor_M)):
        if neighbor_M[node_id][i] == 1:
            rand = np.random.rand()
            if rand > links[node_id][i]:
                temp_memory = []
                l_m = len(nodelist[i].datamemory)
                for m in range(l_m):
                    temp_memory.append(nodelist[i].datamemory[m])
                rank1 = np.linalg.matrix_rank(temp_memory)
                rece_data = np.zeros(K)
                for j in range(K):
                    rece_data[j] = data[j]
                temp_memory.append(rece_data)
                rank2 = np.linalg.matrix_rank(temp_memory)
                rank_add_des = rank2 - rank1
                reward = calculate_reward(K, rank_add_des, rank2, extrinsic_reward)
                sum_reward += reward
            else:
                nodelist[i].receive_flag = True
                rank1 = np.linalg.matrix_rank(nodelist[i].datamemory)
                rece_data = np.zeros(K)
                for j in range(K):
                    rece_data[j] = data[j]
                nodelist[i].datamemory.append(rece_data)
                rank2 = np.linalg.matrix_rank(nodelist[i].datamemory)
                rank_add_des = rank2 - rank1
                reward = calculate_reward(K, rank_add_des, rank2, extrinsic_reward)
                sum_reward += reward
                nodelist[i].packet.append(data)

                l = nodelist[i].receivelen
                nodelist[i].receivememory[int(l % M)] = rece_data
                nodelist[i].receivelen = nodelist[i].receivelen + 1
    return sum_reward


def calculate_reward(K, rank_add_des, rank_des, extrinsic_reward, add_destination_bonus=False):
    """Compute reward with optional destination-rank bonus.

    Args:
        K: Generation size.
        rank_add_des: Rank increment at destination/receiver.
        rank_des: Current rank after reception.
        extrinsic_reward: Base reward magnitude.
        add_destination_bonus: Whether to add rank-shaping bonus.

    Returns:
        Scalar reward.
    """
    reward = extrinsic_reward if rank_add_des > 0 else -extrinsic_reward
    if add_destination_bonus:
        reward += rank_add_des * (K - (rank_des - rank_add_des)) / K
    return reward
