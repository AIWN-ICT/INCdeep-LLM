from typing import Dict

import numpy as np


class ReplayBuffer:
    """Fixed-size replay buffer backed by NumPy arrays.

    Stores transition tuples \(s, a, r, s', done\) and provides random mini-batch
    sampling for off-policy updates.
    """

    def __init__(self, obs_dim: int, size: int, batch_size: int = 32):
        """Initialize storage arrays and circular-buffer pointers.

        Args:
            obs_dim: Observation vector dimension.
            size: Maximum number of transitions to keep.
            batch_size: Number of samples returned per batch.
        """
        self.obs_buf = np.zeros([size, obs_dim], dtype=np.float32)
        self.next_obs_buf = np.zeros([size, obs_dim], dtype=np.float32)
        self.acts_buf = np.zeros([size], dtype=np.float32)
        self.rews_buf = np.zeros([size], dtype=np.float32)
        self.done_buf = np.zeros(size, dtype=np.float32)
        self.max_size, self.batch_size = size, batch_size
        self.ptr, self.size = 0, 0

    def store(
        self,
        obs: np.ndarray,
        act: int,
        rew: float,
        next_obs: np.ndarray,
        done: bool,
    ):
        """Insert one transition into the replay buffer.

        Args:
            obs: Current observation.
            act: Executed action index.
            rew: Immediate reward.
            next_obs: Next observation.
            done: Terminal flag.
        """
        self.obs_buf[self.ptr] = obs
        self.next_obs_buf[self.ptr] = next_obs
        self.acts_buf[self.ptr] = act
        self.rews_buf[self.ptr] = rew
        self.done_buf[self.ptr] = done
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample_batch(self) -> Dict[str, np.ndarray]:
        """Sample a random mini-batch of transitions.

        Returns:
            Dictionary containing arrays for observations, actions, rewards,
            next observations, and done flags.
        """
        idxs = np.random.choice(self.size, size=self.batch_size, replace=False)
        return dict(
            obs=self.obs_buf[idxs],
            next_obs=self.next_obs_buf[idxs],
            acts=self.acts_buf[idxs],
            rews=self.rews_buf[idxs],
            done=self.done_buf[idxs],
        )

    def __len__(self) -> int:
        """Return the number of stored transitions."""
        return self.size
