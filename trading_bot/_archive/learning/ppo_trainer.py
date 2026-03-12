"""
Proximal Policy Optimization (PPO) for Continuous Strategy Optimization

Implements state-of-the-art reinforcement learning for adaptive trading strategies.
"""

import numpy as np
try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Normal
from typing import Dict, List, Optional, Tuple
import logging
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class ActorCritic(nn.Module):
    """Actor-Critic network for PPO"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super(ActorCritic, self).__init__()
        
        # Shared feature extractor
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Actor head (policy)
        self.actor_mean = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Tanh()  # Actions in [-1, 1]
        )
        
        self.actor_log_std = nn.Parameter(torch.zeros(action_dim))
        
        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, state):
        features = self.shared(state)
        return features
    
    def act(self, state):
        """Sample action from policy"""
        features = self.forward(state)
        action_mean = self.actor_mean(features)
        action_std = torch.exp(self.actor_log_std)
        
        dist = Normal(action_mean, action_std)
        action = dist.sample()
        action_log_prob = dist.log_prob(action).sum(dim=-1)
        
        return action, action_log_prob
    
    def evaluate(self, state, action):
        """Evaluate action under current policy"""
        features = self.forward(state)
        action_mean = self.actor_mean(features)
        action_std = torch.exp(self.actor_log_std)
        
        dist = Normal(action_mean, action_std)
        action_log_prob = dist.log_prob(action).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        
        value = self.critic(features).squeeze(-1)
        
        return action_log_prob, value, entropy


class PPOTrainer:
    """
    Proximal Policy Optimization Trainer
    
    Optimizes trading strategies through continuous interaction with market environment.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # PPO hyperparameters
        self.gamma = self.config.get('gamma', 0.99)
        self.gae_lambda = self.config.get('gae_lambda', 0.95)
        self.clip_epsilon = self.config.get('clip_epsilon', 0.2)
        self.value_coef = self.config.get('value_coef', 0.5)
        self.entropy_coef = self.config.get('entropy_coef', 0.01)
        self.max_grad_norm = self.config.get('max_grad_norm', 0.5)
        self.ppo_epochs = self.config.get('ppo_epochs', 10)
        self.batch_size = self.config.get('batch_size', 64)
        self.learning_rate = self.config.get('learning_rate', 3e-4)
        
        # State and action dimensions
        self.state_dim = self.config.get('state_dim', 128)
        self.action_dim = self.config.get('action_dim', 3)  # position_size, entry_price, exit_price
        
        # Initialize network
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.policy = ActorCritic(self.state_dim, self.action_dim).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=self.learning_rate)
        
        # Experience buffer
        self.buffer = {
            'states': [],
            'actions': [],
            'rewards': [],
            'values': [],
            'log_probs': [],
            'dones': []
        }
        
        # Training metrics
        self.episode_rewards = deque(maxlen=100)
        self.episode_lengths = deque(maxlen=100)
        self.training_step = 0
        
        logger.info(f"PPO Trainer initialized on {self.device}")
        logger.info(f"State dim: {self.state_dim}, Action dim: {self.action_dim}")
    
    def select_action(self, state: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """
        Select action using current policy
        
        Args:
            state: Current market state
            
        Returns:
            action, log_prob, value
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action, log_prob = self.policy.act(state_tensor)
            features = self.policy.forward(state_tensor)
            value = self.policy.critic(features).squeeze(-1)
        
        return action.cpu().numpy()[0], log_prob.cpu().item(), value.cpu().item()
    
    def store_transition(self, state, action, reward, value, log_prob, done):
        """Store transition in buffer"""
        self.buffer['states'].append(state)
        self.buffer['actions'].append(action)
        self.buffer['rewards'].append(reward)
        self.buffer['values'].append(value)
        self.buffer['log_probs'].append(log_prob)
        self.buffer['dones'].append(done)
    
    def compute_gae(self, rewards, values, dones, next_value):
        """
        Compute Generalized Advantage Estimation (GAE)
        
        Args:
            rewards: List of rewards
            values: List of value estimates
            dones: List of done flags
            next_value: Value estimate for next state
            
        Returns:
            advantages, returns
        """
        advantages = []
        gae = 0
        
        values = values + [next_value]
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        returns = [adv + val for adv, val in zip(advantages, values[:-1])]
        
        return advantages, returns
    
    def update_policy(self):
        """Update policy using PPO algorithm"""
        if len(self.buffer['states']) < self.batch_size:
            return {}
        
        # Prepare data
        states = torch.FloatTensor(np.array(self.buffer['states'])).to(self.device)
        actions = torch.FloatTensor(np.array(self.buffer['actions'])).to(self.device)
        old_log_probs = torch.FloatTensor(self.buffer['log_probs']).to(self.device)
        
        # Compute advantages and returns
        with torch.no_grad():
            next_state = states[-1]
            features = self.policy.forward(next_state.unsqueeze(0))
            next_value = self.policy.critic(features).squeeze(-1).item()
        
        advantages, returns = self.compute_gae(
            self.buffer['rewards'],
            self.buffer['values'],
            self.buffer['dones'],
            next_value
        )
        
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO update
        total_loss = 0
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy = 0
        
        for _ in range(self.ppo_epochs):
            # Sample mini-batches
            indices = np.random.permutation(len(states))
            
            for start in range(0, len(states), self.batch_size):
                end = start + self.batch_size
                batch_indices = indices[start:end]
                
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                
                # Evaluate actions under current policy
                log_probs, values, entropy = self.policy.evaluate(batch_states, batch_actions)
                
                # Policy loss (clipped surrogate objective)
                ratio = torch.exp(log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # Value loss
                value_loss = nn.MSELoss()(values, batch_returns)
                
                # Entropy bonus
                entropy_loss = -entropy.mean()
                
                # Total loss
                loss = policy_loss + self.value_coef * value_loss + self.entropy_coef * entropy_loss
                
                # Optimize
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.optimizer.step()
                
                total_loss += loss.item()
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()
        
        # Clear buffer
        for key in self.buffer:
            self.buffer[key] = []
        
        self.training_step += 1
        
        metrics = {
            'loss': total_loss / self.ppo_epochs,
            'policy_loss': total_policy_loss / self.ppo_epochs,
            'value_loss': total_value_loss / self.ppo_epochs,
            'entropy': total_entropy / self.ppo_epochs,
            'training_step': self.training_step
        }
        
        logger.info(f"PPO Update - Step {self.training_step}: Loss={metrics['loss']:.4f}, "
                   f"Policy Loss={metrics['policy_loss']:.4f}, Value Loss={metrics['value_loss']:.4f}")
        
        return metrics
    
    def train_episode(self, env, max_steps: int = 1000):
        """
        Train for one episode
        
        Args:
            env: Trading environment
            max_steps: Maximum steps per episode
            
        Returns:
            episode_reward, episode_length
        """
        state = env.reset()
        episode_reward = 0
        episode_length = 0
        
        for step in range(max_steps):
            # Select action
            action, log_prob, value = self.select_action(state)
            
            # Take action in environment
            next_state, reward, done, info = env.step(action)
            
            # Store transition
            self.store_transition(state, action, reward, value, log_prob, done)
            
            episode_reward += reward
            episode_length += 1
            
            state = next_state
            
            if done:
                break
        
        # Update policy
        metrics = self.update_policy()
        
        self.episode_rewards.append(episode_reward)
        self.episode_lengths.append(episode_length)
        
        return episode_reward, episode_length, metrics
    
    def save_model(self, path: str):
        """Save model checkpoint"""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_step': self.training_step,
            'config': self.config
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_step = checkpoint['training_step']
        logger.info(f"Model loaded from {path}")
    
    def get_statistics(self) -> Dict:
        """Get training statistics"""
        return {
            'mean_episode_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0,
            'mean_episode_length': np.mean(self.episode_lengths) if self.episode_lengths else 0,
            'training_steps': self.training_step,
            'episodes_completed': len(self.episode_rewards)
        }


class TradingEnvironment:
    """
    Trading environment for PPO training
    
    Simulates market conditions and evaluates trading decisions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.state_dim = self.config.get('state_dim', 128)
        self.action_dim = self.config.get('action_dim', 3)
        
        # Market state
        self.current_step = 0
        self.max_steps = self.config.get('max_steps', 1000)
        self.initial_balance = self.config.get('initial_balance', 10000)
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        
        # Risk parameters
        self.max_position_size = self.config.get('max_position_size', 1.0)
        self.transaction_cost = self.config.get('transaction_cost', 0.001)
        
    def reset(self) -> np.ndarray:
        """Reset environment"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        
        return self._get_state()
    
    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        # Placeholder: In production, this would include:
        # - Price history
        # - Technical indicators
        # - Order book data
        # - Market microstructure features
        # - Portfolio state
        return np.random.randn(self.state_dim)
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Take action in environment
        
        Args:
            action: [position_size, entry_price_adjustment, exit_price_adjustment]
            
        Returns:
            next_state, reward, done, info
        """
        self.current_step += 1
        
        # Parse action
        position_size = np.clip(action[0], -self.max_position_size, self.max_position_size)
        
        # Simulate market movement (placeholder)
        price_change = np.random.randn() * 0.01
        
        # Calculate reward (risk-adjusted returns)
        if self.position != 0:
            pnl = self.position * price_change * self.balance
            transaction_cost = abs(position_size - self.position) * self.transaction_cost * self.balance
            reward = pnl - transaction_cost
        else:
            reward = 0
        
        # Update position
        self.position = position_size
        self.balance += reward
        
        # Check if done
        done = (self.current_step >= self.max_steps) or (self.balance <= 0)
        
        # Get next state
        next_state = self._get_state()
        
        info = {
            'balance': self.balance,
            'position': self.position,
            'step': self.current_step
        }
        
        return next_state, reward, done, info


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'state_dim': 128,
        'action_dim': 3,
        'gamma': 0.99,
        'learning_rate': 3e-4,
        'batch_size': 64
    }
    
    trainer = PPOTrainer(config)
    env = TradingEnvironment(config)
    
    # Train for a few episodes
    for episode in range(10):
        episode_reward, episode_length, metrics = trainer.train_episode(env)
        logger.info(f"Episode {episode}: Reward={episode_reward:.2f}, Length={episode_length}")
    
    # Get statistics
    stats = trainer.get_statistics()
    logger.info(f"\nTraining Statistics: {stats}")
