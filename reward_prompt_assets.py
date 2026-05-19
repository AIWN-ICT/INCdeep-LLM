<<<<<<< HEAD
"""Baseline reward-function assets used by evaluation workflows."""

# Baseline candidate reward functions keyed by source model name.
REWARD_FUNCTIONS = {
    "gemini-2.5-pro-exp-03-25": """
def calculate_source_reward(rank_add_next: int, rank_add_des: int, rank_des: int, K: int, W_next: float = 1.0, W_des: float = 5.0, C_step: float = 0.1, R_goal: float = 100.0) -> float:
   new_rank_des = rank_des + rank_add_des
   if new_rank_des >= K:
       reward = R_goal
   else:
       reward_next_hop = W_next * rank_add_next
       reward_destination = W_des * rank_add_des
       step_penalty = -C_step
       reward = reward_next_hop + reward_destination + step_penalty
   return reward
   """,
    "o3-mini": """
def compute_reward(K, N, rank_des, rank_add_next, rank_add_des):
    positive_gain = rank_add_next + rank_add_des
    penalty_per_packet = 1
    reward = positive_gain - penalty_per_packet
    return reward
""",
    "deepseek-r1": """
    def calculate_reward(rank_add_next, rank_add_des, rank_des, K):
        reward_next_hop = rank_add_next
        remaining_need = K - rank_des
        weight = remaining_need / K if K != 0 else 0.0
        reward_destination = rank_add_des * weight
        total_reward = reward_next_hop + reward_destination
        return total_reward
    """,
    "qwq-plus": """
    def calculate_reward(K, rank_add_next, rank_add_des, rank_des):
        reward_next = rank_add_next
        reward_des = rank_add_des * (K - rank_des)
        return reward_next + reward_des
    """,
    "grok-3-beta": """
   def calculate_reward(rank_add_des, rank_add_next):
        alpha = 0.1
        cost = 1.0
        reward = rank_add_des + alpha * rank_add_next - cost
        return reward
    """,
    "claude-3-7-sonnet-20250219-thinking": """
    def calculate_reward(K, N, rank_add_next, rank_add_des, rank_des):
        base_reward = -0.1
        next_hop_reward = 0.5 * rank_add_next
        destination_reward = 2.0 * rank_add_des
        new_rank_des = rank_des + rank_add_des
        progress_reward = 1.0 * new_rank_des / K
        completion_bonus = 10.0 if new_rank_des == K else 0
        reward = base_reward + next_hop_reward + destination_reward + progress_reward + completion_bonus
        return reward
    """,
    "doubao-1-5-thinking-pro-250415": """
    def calculate_reward(rank_add_next: int, rank_add_des: int,  rank_des: int,K: int, alpha: float = 1.0,beta: float = 2.0) -> float:
        reward_next = alpha * rank_add_next
        reward_des = beta * rank_add_des * (K - rank_des)
        total_reward = reward_next + reward_des
        return total_reward
    """,
}
=======
"""Baseline reward-function assets used by evaluation workflows."""

# Baseline candidate reward functions keyed by source model name.
REWARD_FUNCTIONS = {
    "gemini-2.5-pro-exp-03-25": """
def calculate_source_reward(rank_add_next: int, rank_add_des: int, rank_des: int, K: int, W_next: float = 1.0, W_des: float = 5.0, C_step: float = 0.1, R_goal: float = 100.0) -> float:
   new_rank_des = rank_des + rank_add_des
   if new_rank_des >= K:
       reward = R_goal
   else:
       reward_next_hop = W_next * rank_add_next
       reward_destination = W_des * rank_add_des
       step_penalty = -C_step
       reward = reward_next_hop + reward_destination + step_penalty
   return reward
   """,
    "o3-mini": """
def compute_reward(K, N, rank_des, rank_add_next, rank_add_des):
    positive_gain = rank_add_next + rank_add_des
    penalty_per_packet = 1
    reward = positive_gain - penalty_per_packet
    return reward
""",
    "deepseek-r1": """
    def calculate_reward(rank_add_next, rank_add_des, rank_des, K):
        reward_next_hop = rank_add_next
        remaining_need = K - rank_des
        weight = remaining_need / K if K != 0 else 0.0
        reward_destination = rank_add_des * weight
        total_reward = reward_next_hop + reward_destination
        return total_reward
    """,
    "qwq-plus": """
    def calculate_reward(K, rank_add_next, rank_add_des, rank_des):
        reward_next = rank_add_next
        reward_des = rank_add_des * (K - rank_des)
        return reward_next + reward_des
    """,
    "grok-3-beta": """
   def calculate_reward(rank_add_des, rank_add_next):
        alpha = 0.1
        cost = 1.0
        reward = rank_add_des + alpha * rank_add_next - cost
        return reward
    """,
    "claude-3-7-sonnet-20250219-thinking": """
    def calculate_reward(K, N, rank_add_next, rank_add_des, rank_des):
        base_reward = -0.1
        next_hop_reward = 0.5 * rank_add_next
        destination_reward = 2.0 * rank_add_des
        new_rank_des = rank_des + rank_add_des
        progress_reward = 1.0 * new_rank_des / K
        completion_bonus = 10.0 if new_rank_des == K else 0
        reward = base_reward + next_hop_reward + destination_reward + progress_reward + completion_bonus
        return reward
    """,
    "doubao-1-5-thinking-pro-250415": """
    def calculate_reward(rank_add_next: int, rank_add_des: int,  rank_des: int,K: int, alpha: float = 1.0,beta: float = 2.0) -> float:
        reward_next = alpha * rank_add_next
        reward_des = beta * rank_add_des * (K - rank_des)
        total_reward = reward_next + reward_des
        return total_reward
    """,
}
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
