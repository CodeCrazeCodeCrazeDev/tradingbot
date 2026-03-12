"""
Real PPO (Proximal Policy Optimization) agent for trading.
Replaces placeholder RL with actual actor-critic implementation.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
import numpy as np
from typing import Dict, List, Tuple
from loguru import logger
from collections import deque
import numpy

import logging
logger = logging.getLogger(__name__)



class ActorCritic(nn.Module):
    """Actor-Critic network for PPO."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        # Shared feature extractor
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )
        
        # Actor head (policy)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim)
        )
        
        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(self, state):
        features = self.shared(state)
        action_logits = self.actor(features)
        value = self.critic(features)
        return action_logits, value
    
    def act(self, state):
        """Select action with exploration."""
        action_logits, value = self.forward(state)
        action_probs = F.softmax(action_logits, dim=-1)
        dist = Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        return action.item(), log_prob, value, entropy


class PPOAgent:
    """Proximal Policy Optimization for trading."""
    
    def __init__(self, state_dim: int, action_dim: int, config: Dict = None):
        self.config = config or {
            'lr': 3e-4,
            'gamma': 0.99,
            'epsilon': 0.2,
            'epochs': 10,
            'batch_size': 64,
            'gae_lambda': 0.95,
            'value_coef': 0.5,
            'entropy_coef': 0.01,
            'max_grad_norm': 0.5,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }
        
        self.device = self.config['device']
        self.policy = ActorCritic(state_dim, action_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=self.config['lr'])
        
        # Experience buffer
        self.memory = {
            'states': [],
            'actions': [],
            'log_probs': [],
            'rewards': [],
            'values': [],
            'dones': []
        }
        
        # Training metrics
        self.episode_rewards = deque(maxlen=100)
        self.training_step = 0
        
        logger.info(f"PPO Agent initialized on {self.device}")
    
    def store_transition(self, state, action, log_prob, reward, value, done):
        """Store experience in memory."""
        self.memory['states'].append(state)
        self.memory['actions'].append(action)
        self.memory['log_probs'].append(log_prob.item())
        self.memory['rewards'].append(reward)
        self.memory['values'].append(value.item())
        self.memory['dones'].append(done)
    
    def compute_gae(self, rewards, values, dones, next_value):
        """Compute Generalized Advantage Estimation."""
        advantages = []
        gae = 0
        
        values = values + [next_value]
        gamma = self.config['gamma']
        lam = self.config['gae_lambda']
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + gamma * lam * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        returns = [adv + val for adv, val in zip(advantages, values[:-1])]
        return advantages, returns
    
    def update(self) -> Dict:
        """Update policy using PPO algorithm."""
        
        if len(self.memory['states']) == 0:
            return {}
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(self.memory['states'])).to(self.device)
        actions = torch.LongTensor(self.memory['actions']).to(self.device)
        old_log_probs = torch.FloatTensor(self.memory['log_probs']).to(self.device)
        rewards = self.memory['rewards']
        values = self.memory['values']
        dones = self.memory['dones']
        
        # Compute advantages
        with torch.no_grad():
            _, next_value = self.policy(states[-1].unsqueeze(0))
        
        advantages, returns = self.compute_gae(rewards, values, dones, next_value.item())
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO update for multiple epochs
        total_actor_loss = 0
        total_critic_loss = 0
        total_entropy = 0
        
        for _ in range(self.config['epochs']):
            # Get current policy
            action_logits, values = self.policy(states)
            action_probs = F.softmax(action_logits, dim=-1)
            dist = Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()
            
            # Compute ratio
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # Clipped surrogate objective
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.config['epsilon'], 1 + self.config['epsilon']) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            
            # Value loss
            critic_loss = F.mse_loss(values.squeeze(), returns)
            
            # Total loss
            loss = (actor_loss + 
                   self.config['value_coef'] * critic_loss - 
                   self.config['entropy_coef'] * entropy)
            
            # Update
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                self.policy.parameters(), 
                max_norm=self.config['max_grad_norm']
            )
            self.optimizer.step()
            
            total_actor_loss += actor_loss.item()
            total_critic_loss += critic_loss.item()
            total_entropy += entropy.item()
        
        # Clear memory
        for key in self.memory:
            self.memory[key] = []
        
        self.training_step += 1
        
        metrics = {
            'actor_loss': total_actor_loss / self.config['epochs'],
            'critic_loss': total_critic_loss / self.config['epochs'],
            'entropy': total_entropy / self.config['epochs'],
            'training_step': self.training_step
        }
        
        if self.training_step % 10 == 0:
            logger.info(f"PPO Update #{self.training_step}: {metrics}")
        
        return metrics
    
    def select_action(self, state: np.ndarray, deterministic: bool = False):
        """Select action using current policy."""
        self.policy.eval()
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action_logits, value = self.policy(state_tensor)
            
            if deterministic:
                action = torch.argmax(action_logits, dim=-1).item()
                log_prob = torch.tensor(0.0)
                entropy = torch.tensor(0.0)
            else:
                action_probs = F.softmax(action_logits, dim=-1)
                dist = Categorical(action_probs)
                action = dist.sample().item()
                log_prob = dist.log_prob(torch.tensor(action))
                entropy = dist.entropy()
        
        self.policy.train()
        return action, log_prob, value, entropy
    
    def save_model(self, path: str):
        """Save model weights."""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_step': self.training_step,
            'config': self.config
        }, path)
        logger.info(f"PPO model saved to {path}")
    
    def load_model(self, path: str):
        """Load model weights."""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_step = checkpoint['training_step']
        logger.info(f"PPO model loaded from {path}")


class TradingEnvironment:
    """Trading environment for RL training."""
    
    def __init__(self, data: np.ndarray, initial_balance: float = 10000):
        self.data = data
        self.initial_balance = initial_balance
        self.reset()
    
    def reset(self):
        """Reset environment to initial state."""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.entry_price = 0
        self.done = False
        return self._get_state()
    
    def _get_state(self):
        """Get current state observation."""
        if self.current_step >= len(self.data):
            return np.zeros(self.data.shape[1])
        return self.data[self.current_step]
    
    def step(self, action: int):
        """Execute action and return next state, reward, done."""
        # Action: 0=hold, 1=buy, 2=sell
        
        if self.current_step >= len(self.data) - 1:
            self.done = True
            return self._get_state(), 0, self.done
        
        current_price = self.data[self.current_step, 0]  # Assuming first feature is price
        next_price = self.data[self.current_step + 1, 0]
        
        reward = 0
        
        # Execute action
        if action == 1 and self.position == 0:  # Buy
            self.position = 1
            self.entry_price = current_price
        elif action == 2 and self.position == 0:  # Sell
            self.position = -1
            self.entry_price = current_price
        elif action == 0 and self.position != 0:  # Close position
            price_change = (next_price - self.entry_price) / self.entry_price
            reward = price_change * self.position * 100  # Scale reward
            self.position = 0
        
        # Holding reward
        if self.position != 0:
            price_change = (next_price - current_price) / current_price
            reward += price_change * self.position * 10
        
        self.current_step += 1
        next_state = self._get_state()
        
        return next_state, reward, self.done
