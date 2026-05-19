import os
from typing import Dict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from utils.ReplayBuffer import ReplayBuffer
from utils.relay_agent_pytorch import Network_R

UPDATE_TARGET_STEPS = 100
LR = 0.0001
t = 0.95


class DQNAgent_R(nn.Module):
    """DQN agent for relay-side recoding/forwarding decisions."""

    def __init__(self, state_size, arg_dict, device):
        super(DQNAgent_R, self).__init__()
        self.batch_size = 32
        self.state_size = state_size
        self.arg_dict = arg_dict
        self.device = device
        self.memory_size = 10000
        self.memory = ReplayBuffer(self.state_size, self.memory_size, self.batch_size)
        self.gamma = 0.99
        self.train_step = 0
        self.train_start = 0
        self.learning_rate = LR

        # Build online and target Q-networks.
        self.dqn = self.create_q_network().to(device)
        self.target_net = self.create_q_network().to(device)
        self.target_net.load_state_dict(self.dqn.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.dqn.parameters(), lr=self.learning_rate)
        self.is_test = False
        self.transition = list()
        self.epsilon = 1

    def create_q_network(self):
        """Create the relay-side Q-network."""
        return Network_R(self.state_size, self.arg_dict, self.device).to(self.device)

    def _compute_dqn_loss(self, samples: Dict[str, np.ndarray]) -> torch.Tensor:
        """Compute element-wise Huber loss for DQN updates.

        Args:
            samples: Mini-batch sampled from replay buffer.

        Returns:
            Element-wise loss tensor.
        """
        state = torch.FloatTensor(samples["obs"]).to(self.device)
        next_state = torch.FloatTensor(samples["next_obs"]).to(self.device)
        action = torch.LongTensor(samples["acts"].reshape(-1, 1)).to(self.device)
        reward = torch.FloatTensor(samples["rews"].reshape(-1, 1)).to(self.device)
        done = torch.FloatTensor(samples["done"].reshape(-1, 1)).to(self.device)

        curr_q_value = self.dqn(state).gather(1, action)
        next_q_value = self.target_net(next_state).max(dim=1, keepdim=True)[0].detach()
        mask = 1 - done
        target = reward + self.gamma * next_q_value * mask

        return F.smooth_l1_loss(curr_q_value, target, reduction="none")

    def update_model(self) -> torch.Tensor:
        """Run one optimization step and return training step count."""
        samples = self.memory.sample_batch()
        elementwise_loss = self._compute_dqn_loss(samples)
        loss = torch.mean(elementwise_loss)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.train_step = self.train_step + 1
        return self.train_step

    def remember(self, state, action, reward, next_state, done):
        """Store transition and trigger training once buffer is warm."""
        self.transition = [state, action, reward, next_state, done]
        self.memory.store(*self.transition)
        if len(self.memory) > self.batch_size:
            self.update_model()
            if self.train_step % UPDATE_TARGET_STEPS == 0:
                self.update_target_soft()

    def update_target_soft(self):
        """Soft-update target network parameters."""
        if self.train_step % UPDATE_TARGET_STEPS == 0:
            for target_param, source_param in zip(self.target_net.parameters(), self.dqn.parameters()):
                target_param.data.copy_((1 - t) * target_param.data + t * source_param.data)

    def get_q_val(self, state_batch):
        """Return Q-values for a batch of states."""
        state_batch = np.reshape(state_batch, (-1, self.state_size))
        q_val = self.dqn(torch.FloatTensor(state_batch).to(self.device)).detach().cpu().numpy()
        return q_val

    def load_network(self, path):
        """Load relay policy parameters from file."""
        loaded = torch.load(path, map_location=self.device)

        if isinstance(loaded, dict):
            self.dqn.load_state_dict(loaded)
        else:
            self.dqn.load_state_dict(loaded.state_dict())

        self.target_net.load_state_dict(self.dqn.state_dict())

    def save_network(self, path):
        """Save relay policy parameters to file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            torch.save(self.dqn.state_dict(), path)
            print(f"Model saved successfully: {path}")
        except Exception as e:
            print(f"Failed to save model: {str(e)}")
