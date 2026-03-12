"""
from pathlib import Path
Replay Buffer for Offline RL

Efficient storage and sampling of transitions for offline RL training.
"""

import numpy as np
import logging
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import pathlib
import numpy

logger = logging.getLogger(__name__)


class ReplayBuffer:
    """
    Replay buffer for offline RL training.
    
    Stores transitions (state, action, reward, next_state, done) and
    provides efficient sampling for batch training.
    """
    
    def __init__(self, capacity: int = 100000):
        """
        Initialize replay buffer.
        
        Args:
            capacity: Maximum number of transitions to store
        """
        try:
            self.capacity = capacity
            self.buffer = deque(maxlen=capacity)
            self.position = 0
        
            logger.info(f"Replay buffer initialized with capacity {capacity}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        info: Optional[Dict] = None
    ):
        """
        Add transition to buffer.
        
        Args:
            state: State vector
            action: Action index
            reward: Reward value
            next_state: Next state vector
            done: Terminal flag
            info: Additional information
        """
        try:
            if len(self.buffer) < self.capacity:
                self.buffer.append(None)
        
            self.buffer[self.position] = (state, action, reward, next_state, done, info or {})
            self.position = (self.position + 1) % self.capacity
        except Exception as e:
            logger.error(f"Error in push: {e}")
            raise
    
    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample random batch of transitions.
        
        Args:
            batch_size: Number of transitions to sample
        
        Returns:
            Tuple of (states, actions, rewards, next_states, dones)
        """
        try:
            batch_size = min(batch_size, len(self.buffer))
            indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        
            states, actions, rewards, next_states, dones, _ = zip(*[self.buffer[i] for i in indices])
        
            return (
                np.array(states),
                np.array(actions),
                np.array(rewards, dtype=np.float32).reshape(-1, 1),
                np.array(next_states),
                np.array(dones, dtype=np.float32).reshape(-1, 1)
            )
        except Exception as e:
            logger.error(f"Error in sample: {e}")
            raise
    
    def sample_with_info(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        """
        Sample random batch of transitions with info.
        
        Args:
            batch_size: Number of transitions to sample
        
        Returns:
            Tuple of (states, actions, rewards, next_states, dones, infos)
        """
        try:
            batch_size = min(batch_size, len(self.buffer))
            indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        
            states, actions, rewards, next_states, dones, infos = zip(*[self.buffer[i] for i in indices])
        
            return (
                np.array(states),
                np.array(actions),
                np.array(rewards, dtype=np.float32).reshape(-1, 1),
                np.array(next_states),
                np.array(dones, dtype=np.float32).reshape(-1, 1),
                list(infos)
            )
        except Exception as e:
            logger.error(f"Error in sample_with_info: {e}")
            raise
    
    def __len__(self) -> int:
        """Get buffer length."""
        return len(self.buffer)
    
    def load_from_dataset(self, dataset):
        """
        Load transitions from dataset.
        
        Args:
            dataset: OfflineRLDataset object
        """
        try:
            for i in range(len(dataset.states)):
                self.push(
                    state=dataset.states[i],
                    action=dataset.actions[i],
                    reward=dataset.rewards[i],
                    next_state=dataset.next_states[i],
                    done=dataset.dones[i],
                    info={k: v[i] for k, v in dataset.info.items()}
                )
        
            logger.info(f"Loaded {len(dataset.states)} transitions into replay buffer")
        except Exception as e:
            logger.error(f"Error in load_from_dataset: {e}")
            raise
    
    def save(self, file_path: str):
        """
        Save buffer to file.
        
        Args:
            file_path: Path to save file
        """
        try:
            if len(self.buffer) == 0:
                logger.warning("Buffer is empty, nothing to save")
                return
        
            # Convert buffer to arrays
            states, actions, rewards, next_states, dones, infos = [], [], [], [], [], []
        
            for s, a, r, ns, d, info in self.buffer:
                states.append(s)
                actions.append(a)
                rewards.append(r)
                next_states.append(ns)
                dones.append(d)
                infos.append(info)
        
            # Save arrays
            np.savez_compressed(
                file_path,
                states=np.array(states),
                actions=np.array(actions),
                rewards=np.array(rewards),
                next_states=np.array(next_states),
                dones=np.array(dones),
                infos=np.array(infos, dtype=object)
            )
        
            logger.info(f"Saved replay buffer to {file_path}")
        except Exception as e:
            logger.error(f"Error in save: {e}")
            raise
    
    def load(self, file_path: str):
        """
        Load buffer from file.
        
        Args:
            file_path: Path to load file
        """
        try:
            data = np.load(file_path, allow_pickle=True)
        
            # Clear current buffer
            self.buffer.clear()
            self.position = 0
        
            # Load transitions
            for i in range(len(data['states'])):
                self.push(
                    state=data['states'][i],
                    action=data['actions'][i],
                    reward=data['rewards'][i],
                    next_state=data['next_states'][i],
                    done=data['dones'][i],
                    info=data['infos'][i].item() if data['infos'][i] else {}
                )
        
            logger.info(f"Loaded {len(self.buffer)} transitions from {file_path}")
        except Exception as e:
            logger.error(f"Error in load: {e}")
            raise
