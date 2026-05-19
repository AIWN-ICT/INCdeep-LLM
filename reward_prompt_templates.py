"""Prompt templates used for reward-function generation and evaluation."""

REWARD_FUNCTION_DESIGN_PROMPT_EN = r"""
[Role Definition]
You are an expert in network coding, deep reinforcement learning, and code generation.

[Environment Description]
In the task environment, there is a topology consisting of one source node, multiple relay nodes, and one destination node. Different nodes are connected through paths that transmit encoded packets. All nodes in the network receive encoded packets and forward them to all other nodes they are connected to. Each encoded bit has an action space of 0 or 1. If the number of connecting paths is N, then one encoded packet sent by the source node can potentially increase the rank at the destination node by at most N, after passing through relay nodes on different paths.

The task is as follows: the source node sends a coded packet of length K each time. Relay nodes re-encode the packets, and the encoded packets are passed to the destination node. If the linear equation system formed by all encoded packets received at the destination reaches full rank K, the source node stops transmitting, and the task is complete. Otherwise, the source node continues sending the next coded packet.

I need your help designing a reward mechanism for the source node. The design of this reward mechanism should include the following parts:

1. The effect of the currently generated encoded packet from the source node on the rank increment of the linear equation system formed by previously received packets at the next-hop nodes.
2. The effect of the currently generated encoded packet from the source node on how quickly the destination node can decode the linear network-coded packets.

[Variable Definitions]
Consider the following variable properties (some parts are optional and should only be included when truly necessary):

1. The length of the coded packet from the source node is K.
2. The number of connecting paths is N.
3. After the source node sends one coded packet, the rank increment of the linear equation system formed by packets at the next-hop node is rank_add_next, where rank_add_next can only be 0 or 1.
4. After the source node sends one coded packet, the rank increment of the linear equation system formed by all received packets at the destination node is rank_add_des.
5. The current rank of the linear equation system formed by all previously received packets at the destination node is rank_des.

The objective of this task is for the source node to use as few coded packets as possible to make the rank of the equation system at the destination node equal to K.

[Task Instructions]
Please help me complete the following:

1. Think through what this task means, step by step.
2. Then write a function that returns a reward value.
3. List the formula for the reward function and explain the meaning of each parameter.
4. While writing the code, you may also add comments to explain your logic.
5. Do not invent any variables or properties that are not explicitly given.
""".strip()

REWARD_FUNCTION_DESIGN_PROMPT_ZH = r"""
[角色定义]
你是网络编码、深度强化学习和代码生成方面的专家。

[环境描述]
在任务环境中，网络拓扑由一个源节点、多个中继节点和一个目的节点组成。不同节点之间通过路径连接并传输编码包。网络中的所有节点都会接收编码包，并将其转发给与自己相连的所有其他节点。每一位编码动作的取值空间为0或1。若连接路径数量为N，则源节点发送的一个编码包经过不同路径上的中继节点后，最多可使目的节点的秩增加N。

任务如下：源节点每次发送一个长度为K的编码包。中继节点对编码包进行再次编码，编码包随后传递到目的节点。若目的节点接收到的所有编码包构成的线性方程组达到满秩K，则源节点停止发送，任务完成；否则源节点继续发送下一个编码包。

我需要你帮助设计源节点的奖励机制。该奖励机制应包含以下部分：

1. 源节点当前生成的编码包对下一跳节点已接收编码包所构成线性方程组秩增量的影响。
2. 源节点当前生成的编码包对目的节点解码线性网络编码包速度的影响。

[变量定义]
请考虑以下变量属性（其中部分是可选的，仅在确有必要时使用）：

1. 源节点编码包长度为K。
2. 连接路径数量为N。
3. 源节点发送一个编码包后，下一跳节点线性方程组秩的增量记为rank_add_next，且rank_add_next只能为0或1。
4. 源节点发送一个编码包后，目的节点线性方程组秩的增量记为rank_add_des。
5. 源节点发送该编码包前，目的节点线性方程组当前秩记为rank_des。

本任务目标是让源节点用尽可能少的编码包，使目的节点线性方程组的秩达到K。

[任务要求]
请完成以下内容：

1. 逐步思考该任务的含义。
2. 编写一个返回奖励值的函数。
3. 给出奖励函数公式并解释各参数含义。
4. 在代码中可适当加入注释说明逻辑。
5. 不要发明任何未明确给出的变量或属性。
""".strip()

# Backward-compatible alias: default generation prompt (English).
REWARD_FUNCTION_DESIGN_PROMPT = REWARD_FUNCTION_DESIGN_PROMPT_EN

# Prompt registry for selecting generation prompt by language code.
REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE = {
    "en": REWARD_FUNCTION_DESIGN_PROMPT_EN,
    "zh": REWARD_FUNCTION_DESIGN_PROMPT_ZH,
}

PROMPT_EN = """
User Question:
You are an expert in network coding, deep reinforcement learning, and code generation.
In the task environment, there is a topology consisting of a source node, multiple relay nodes, and a destination node. Nodes are connected via paths through which coded packets are transmitted. All nodes in the network receive coded packets and forward them to all other connected nodes. Each bit of the coded action space is either 0 or 1. If there are N paths, then a single coded packet sent by the source node, after passing through relay nodes on different paths, can potentially increase the rank at the destination node by up to N.
The task is for the source node to send a coded packet of length K each time. Relay nodes re-encode the packet, and the coded packets are delivered to the destination node. If the rank of the system of linear equations formed by all the coded packets received by the destination node reaches K, the source stops sending, and the task is complete. Otherwise, the source continues sending the next packet.
I need your help to design a **reward mechanism** for the source node. The reward should include the following aspects:
1. The impact of the current coded packet generated by the source node on the **rank increase of the system of equations at the next-hop nodes**.
2. The impact of the current coded packet on the **speed of decoding at the destination node** (i.e., how fast it helps reach full rank at the destination).
Please consider the following variables and properties (some are optional, include only if necessary):
1. K: Length of the coded packet.
2. N: Number of connected paths.
3. rank_add_next: Rank increment at the next-hop node due to the packet (either 0 or 1).
4. rank_add_des: Rank increment at the destination node due to the packet (between 0 and N).
5. rank_des: The current rank at the destination node before sending the packet.
The goal of the task is to have the source node send **fewer packets** to make the rank of the destination's system of equations reach K.
response:
{reward_function}

Evaluation Criteria:
1.Goal Consistency: Does the reward function directly quantify and incentivize the two core objectives—minimizing the number of transmissions and increasing the destination node’s rank—while avoiding the introduction of irrelevant metrics?
2.Exploration Effectiveness: Through the reward structure design (e.g., purely positive incentives, interference-free penalties), does it balance exploration and exploitation, preventing the suppression of actions that have high long-term potential but low short-term returns?
3.Dynamic Reward Weighting: Can the reward weights be dynamically adjusted based on the task phase (for example, the gap between the current rank and the target rank), so that early efficient actions receive higher returns and marginal returns reasonably decay in later stages?
4.Mathematical Consistency: Are cumulative reward values strictly and monotonically aligned with the task objective (achieving the goal in the minimum number of steps), ensuring that the optimal strategy always corresponds to the maximum cumulative reward?
5.Robustness: Can the reward mechanism implicitly detect changes in network state and automatically adapt to different topologies and parameters?
Please evaluate the response based on the criteria above. Each criterion is rated on a 5-point scale, where 5 means "Strongly Agree," 4 means "Agree," 3 means "Not Sure," 2 means "Disagree," and 1 means "Strongly Disagree." The overall quality of the response is assessed on a scale from 5 to 25, with 25 being the best.
"""

PROMPT_CN = """
用户问题：
你是网络编码，深度强化学习和代码生成方面的专家
任务环境中，有一个源节点、多个中继节点和一个目的节点构成的拓扑结构。不同节点之间通过路径连接用于传输编码包，网络中所有节点接收编码包并将其转发到与自己相连的所有其他节点。每一位编码的动作空间是0或1。如果连接路径条数N，那么源节点发送的一个编码包，经过不同路径上的中继节点后最多可能让目的节点的秩增加N。
任务是源节点每次发送一个长度为K的编码包。中继节点对编码包再次进行编码，编码包会传递到目的节点。如果目的节点所有收到的编码包组成的线性方程组的秩为K，源节点停止发送，任务结束。否则，源节点会继续发送下一个编码包。
我需要你帮助我设计一个源节点奖励机制，设计的这个奖励机制要包含以下几个部分：
1.源节点当前生成的编码包对下一跳节点之前收到的编码包组成的线性方程组的秩增加的影响
2.源节点当前生成的编码包对目的节点线性网络编码解码快慢的影响
考虑以下变量属性（有些部分是可选的，所以只有在真正需要时才包括它）：
1.源节点编码包的长度为K
2.连接路径条数为N
3.源节点发送一个编码包后使得下一跳编码包组成的线性方程组的秩的增量为rank_add_next， rank_add_next只能为1或0
4.源节点发送一个编码包后使得目的节点的所有编码包组成的线性方程组的秩的增量为rank_add_des
5.目的节点发送一个编码包之前的所有编码包组成的线性方程组的秩为rank_des
任务目标是让源节点发送更少的编码包使目的节点收到的编码包组成的线性方程组的秩等于K
回答：
{reward_function}
评估准则：
1.Goal Consistency：奖励函数是否直接量化并激励减少发送次数与提升目的节点秩这两个核心目标，避免引入无关指标。
2.Exploration Effectiveness：是否通过奖励结构设计（如纯正向激励、无干扰惩罚）平衡探索与利用，避免抑制对高潜力但低短期收益动作的尝试。
3.Dynamic Reward Weighting：能否根据任务阶段（如当前秩与目标秩的差距）动态调整奖励权重，使早期高效动作获得更高收益，后期边际收益合理衰减。
4.Mathematical Consistency：奖励累积值是否与任务目标（最少步数达成目标）严格单调一致，确保最优策略必然对应最大累计奖励。
5.Robustness：能否通过奖励机制隐式感知网络状态变化，自动适应不同拓扑结构和参数
请根据以上准则评估回答，每个准则5分，5分代表非常同意，4分代表同意，3分代表不确定，2分代表不同意，1分代表非常不同意，从5-25分评估回答质量，25分为最佳。
"""

PROMPTS_BY_LANGUAGE = {
    "en": PROMPT_EN,
    "zh": PROMPT_CN,
}
