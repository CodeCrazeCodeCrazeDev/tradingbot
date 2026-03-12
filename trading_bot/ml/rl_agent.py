"""
from pathlib import Path
Multi-Timeframe Reinforcement Learning Agent for Trading
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
import os
import time
from datetime import datetime
import random
import json
import pickle

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Normal

from trading_bot.ml.rl_environment import TradingEnvironment
from typing import Set
import pathlib
import numpy
import pandas

logger = logging.getLogger(__name__)


class MultiTimeframeNetwork(nn.Module):
    """
    Neural network for multi-timeframe analysis
    
    Features:
    - CNN for each timeframe
    - LSTM for temporal dependencies
    - Attention mechanism for timeframe importance
    """
    
    def __init__(self, input_shape: Tuple[int, int, int], hidden_size: int = 128):
        """
        Initialize the network
        
        Args:
            input_shape: (num_timeframes, num_features, window_size)
            hidden_size: Size of hidden layers
        """
        super(MultiTimeframeNetwork, self).__init__()
        
        num_timeframes, num_features, window_size = input_shape
        
        # CNN for each timeframe
        self.conv_layers = nn.ModuleList([
            nn.Sequential(
                nn.Conv1d(num_features, 32, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.Conv1d(32, 64, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.Conv1d(64, 64, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool1d(1)  # Global average pooling
            )
            for _ in range(num_timeframes)
        ])
        
        # LSTM for temporal dependencies
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softmax(dim=1)
        )
        
        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU()
        )
    
    def forward(self, x):
        """Forward pass"""
        batch_size = x.size(0)
        num_timeframes = x.size(1)
        
        # Process each timeframe with CNN
        timeframe_features = []
        for i in range(num_timeframes):
            # Extract timeframe data
            timeframe_data = x[:, i, :, :]  # (batch_size, num_features, window_size)
            
            # Apply CNN
            features = self.conv_layers[i](timeframe_data)  # (batch_size, 64, 1)
            features = features.squeeze(-1)  # (batch_size, 64)
            
            timeframe_features.append(features)
        
        # Stack timeframe features
        timeframe_features = torch.stack(timeframe_features, dim=1)  # (batch_size, num_timeframes, 64)
        
        # Apply attention
        attention_weights = self.attention(timeframe_features)  # (batch_size, num_timeframes, 1)
        weighted_features = timeframe_features * attention_weights  # (batch_size, num_timeframes, 64)
        
        # Sum weighted features
        combined_features = weighted_features.sum(dim=1)  # (batch_size, 64)
        
        # Reshape for LSTM
        lstm_input = combined_features.unsqueeze(1)  # (batch_size, 1, 64)
        
        # Apply LSTM
        lstm_out, _ = self.lstm(lstm_input)  # (batch_size, 1, hidden_size)
        lstm_out = lstm_out[:, -1, :]  # (batch_size, hidden_size)
        
        # Apply fully connected layers
        x = self.fc(lstm_out)  # (batch_size, hidden_size // 2)
        
        return x


class ActorCritic(nn.Module):
    """
    Actor-Critic network for continuous action space
    
    Features:
    - Shared feature extraction
    - Actor network for policy
    - Critic network for value function
    """
    
    def __init__(self, input_shape: Tuple[int, int, int], hidden_size: int = 128):
        """
        Initialize the network
        
        Args:
            input_shape: (num_timeframes, num_features, window_size)
            hidden_size: Size of hidden layers
        """
        super(ActorCritic, self).__init__()
        
        # Shared feature extraction
        self.feature_network = MultiTimeframeNetwork(input_shape, hidden_size)
        
        # Actor network (policy)
        self.actor_mean = nn.Linear(hidden_size // 2, 1)
        self.actor_log_std = nn.Parameter(torch.zeros(1))
        
        # Critic network (value function)
        self.critic = nn.Linear(hidden_size // 2, 1)
    
    def forward(self, x):
        """Forward pass"""
        features = self.feature_network(x)
        
        # Actor output
        action_mean = torch.tanh(self.actor_mean(features))
        action_std = torch.exp(self.actor_log_std)
        
        # Critic output
        value = self.critic(features)
        
        return action_mean, action_std, value
    
    def get_action(self, state, deterministic=False):
        """
        Get action from policy
        
        Args:
            state: Environment state
            deterministic: Whether to use deterministic policy
            
        Returns:
            action, log_prob, value
        """
        state = torch.FloatTensor(state).unsqueeze(0)
        action_mean, action_std, value = self.forward(state)
        
        if deterministic:
            action = action_mean
            log_prob = None
        else:
            normal = Normal(action_mean, action_std)
            action = normal.sample()
            log_prob = normal.log_prob(action)
        
        return action.detach().numpy()[0], log_prob, value.detach().numpy()[0]


class PPOAgent:
    """
    Proximal Policy Optimization (PPO) agent for trading
    
    Features:
    - Multi-timeframe analysis
    - Actor-critic architecture
    - PPO algorithm for stable learning
    - Experience replay
    - Early stopping
    """
    
    def __init__(self, env: TradingEnvironment, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent
        
        Args:
            env: Trading environment
            config: Agent configuration
        """
        self.env = env
        self.config = config or {}
        
        # PPO parameters
        self.gamma = self.config.get('gamma', 0.99)
        self.gae_lambda = self.config.get('gae_lambda', 0.95)
        self.clip_ratio = self.config.get('clip_ratio', 0.2)
        self.value_coef = self.config.get('value_coef', 0.5)
        self.entropy_coef = self.config.get('entropy_coef', 0.01)
        self.max_grad_norm = self.config.get('max_grad_norm', 0.5)
        
        # Training parameters
        self.batch_size = self.config.get('batch_size', 64)
        self.num_epochs = self.config.get('num_epochs', 10)
        self.learning_rate = self.config.get('learning_rate', 0.0003)
        
        # Create actor-critic network
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network = ActorCritic(env.observation_space.shape).to(self.device)
        self.optimizer = optim.Adam(self.network.parameters(), lr=self.learning_rate)
        
        # Experience buffer
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []
        
        # Training metrics
        self.episode_rewards = []
        self.episode_lengths = []
        self.value_losses = []
        self.policy_losses = []
        self.entropy_losses = []
        
        logger.info(f"PPO Agent initialized on device: {self.device}")
    
    def select_action(self, state, deterministic=False):
        """
        Select action from policy
        
        Args:
            state: Environment state
            deterministic: Whether to use deterministic policy
            
        Returns:
            action, log_prob, value
        """
        return self.network.get_action(state, deterministic)
    
    def update_policy(self):
        """Update policy using PPO algorithm"""
        # Convert experience to tensors
        states = torch.FloatTensor(np.array(self.states)).to(self.device)
        actions = torch.FloatTensor(np.array(self.actions)).to(self.device)
        old_log_probs = torch.FloatTensor(np.array(self.log_probs)).to(self.device)
        
        # Compute returns and advantages
        returns, advantages = self._compute_gae()
        returns = torch.FloatTensor(returns).to(self.device)
        advantages = torch.FloatTensor(advantages).to(self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO update
        for _ in range(self.num_epochs):
            # Generate random mini-batches
            batch_indices = np.random.permutation(len(self.states))
            
            for start_idx in range(0, len(self.states), self.batch_size):
                # Get mini-batch
                batch_indices_subset = batch_indices[start_idx:start_idx + self.batch_size]
                
                # Extract batch data
                batch_states = states[batch_indices_subset]
                batch_actions = actions[batch_indices_subset]
                batch_old_log_probs = old_log_probs[batch_indices_subset]
                batch_returns = returns[batch_indices_subset]
                batch_advantages = advantages[batch_indices_subset]
                
                # Forward pass
                action_mean, action_std, values = self.network(batch_states)
                
                # Calculate new log probabilities
                normal = Normal(action_mean, action_std)
                new_log_probs = normal.log_prob(batch_actions)
                
                # Calculate ratio and clipped ratio
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                clipped_ratio = torch.clamp(ratio, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio)
                
                # Calculate policy loss
                policy_loss_1 = -batch_advantages * ratio
                policy_loss_2 = -batch_advantages * clipped_ratio
                policy_loss = torch.max(policy_loss_1, policy_loss_2).mean()
                
                # Calculate value loss
                value_loss = F.mse_loss(values.squeeze(), batch_returns)
                
                # Calculate entropy loss
                entropy_loss = -normal.entropy().mean()
                
                # Calculate total loss
                loss = policy_loss + self.value_coef * value_loss + self.entropy_coef * entropy_loss
                
                # Backpropagation
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
                self.optimizer.step()
                
                # Record losses
                self.value_losses.append(value_loss.item())
                self.policy_losses.append(policy_loss.item())
                self.entropy_losses.append(entropy_loss.item())
        
        # Clear experience buffer
        self._clear_buffer()
    
    def _compute_gae(self):
        """
        Compute Generalized Advantage Estimation (GAE)
        
        Returns:
            returns, advantages
        """
        # Convert to numpy arrays
        rewards = np.array(self.rewards)
        values = np.array(self.values)
        dones = np.array(self.dones)
        
        # Initialize returns and advantages
        returns = np.zeros_like(rewards)
        advantages = np.zeros_like(rewards)
        
        # Initialize variables
        next_value = 0
        next_advantage = 0
        
        # Compute returns and advantages in reverse order
        for t in reversed(range(len(rewards))):
            # Compute TD target
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
            
            # Compute TD error
            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            
            # Compute advantage
            advantages[t] = delta + self.gamma * self.gae_lambda * next_advantage * (1 - dones[t])
            next_advantage = advantages[t]
            
            # Compute return
            returns[t] = advantages[t] + values[t]
        
        return returns, advantages
    
    def _clear_buffer(self):
        """Clear experience buffer"""
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []
    
    def train(self, num_episodes: int, max_steps_per_episode: int = None,
             update_frequency: int = 2048, eval_frequency: int = 10,
             save_path: Optional[str] = None):
        """
        Train the agent
        
        Args:
            num_episodes: Number of episodes to train
            max_steps_per_episode: Maximum steps per episode
            update_frequency: Frequency of policy updates
            eval_frequency: Frequency of evaluation
            save_path: Path to save model
        """
        if max_steps_per_episode is None:
            max_steps_per_episode = self.env.max_episode_steps
        
        total_steps = 0
        best_reward = float('-inf')
        
        for episode in range(1, num_episodes + 1):
            # Reset environment
            state = self.env.reset()
            episode_reward = 0
            episode_steps = 0
            done = False
            
            # Run episode
            while not done and episode_steps < max_steps_per_episode:
                # Select action
                action, log_prob, value = self.select_action(state)
                
                # Take step in environment
                next_state, reward, done, info = self.env.step(action)
                
                # Store experience
                self.states.append(state)
                self.actions.append(action)
                self.log_probs.append(log_prob.item() if log_prob is not None else 0.0)
                self.rewards.append(reward)
                self.values.append(value[0] if isinstance(value, np.ndarray) else value)
                self.dones.append(done)
                
                # Update state
                state = next_state
                episode_reward += reward
                episode_steps += 1
                total_steps += 1
                
                # Update policy if buffer is full
                if len(self.states) >= update_frequency:
                    self.update_policy()
            
            # Record episode metrics
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_steps)
            
            # Log progress
            logger.info(f"Episode {episode}/{num_episodes}, Reward: {episode_reward:.2f}, Steps: {episode_steps}")
            
            # Evaluate and save model
            if episode % eval_frequency == 0:
                eval_reward = self.evaluate(5)
                logger.info(f"Evaluation: Average Reward: {eval_reward:.2f}")
                
                # Save best model
                if save_path and eval_reward > best_reward:
                    best_reward = eval_reward
                    self.save_model(save_path)
                    logger.info(f"Saved best model with reward: {best_reward:.2f}")
        
        # Final evaluation
        eval_reward = self.evaluate(10)
        logger.info(f"Final Evaluation: Average Reward: {eval_reward:.2f}")
        
        # Save final model
        if save_path:
            self.save_model(f"{save_path}_final")
            logger.info("Saved final model")
    
    def evaluate(self, num_episodes: int) -> float:
        """
        Evaluate the agent
        
        Args:
            num_episodes: Number of episodes to evaluate
            
        Returns:
            Average reward
        """
        total_reward = 0.0
        
        for _ in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                # Select action deterministically
                action, _, _ = self.select_action(state, deterministic=True)
                
                # Take step in environment
                next_state, reward, done, _ = self.env.step(action)
                
                # Update state and reward
                state = next_state
                episode_reward += reward
            
            total_reward += episode_reward
        
        return total_reward / num_episodes
    
    def save_model(self, path: str):
        """
        Save model to disk
        
        Args:
            path: Path to save model
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save model
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'value_losses': self.value_losses,
            'policy_losses': self.policy_losses,
            'entropy_losses': self.entropy_losses
        }, path)
    
    def load_model(self, path: str):
        """
        Load model from disk
        
        Args:
            path: Path to load model from
        """
        # Load model
        checkpoint = torch.load(path, map_location=self.device)
        
        # Load network and optimizer state
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        # Load metrics
        self.episode_rewards = checkpoint.get('episode_rewards', [])
        self.episode_lengths = checkpoint.get('episode_lengths', [])
        self.value_losses = checkpoint.get('value_losses', [])
        self.policy_losses = checkpoint.get('policy_losses', [])
        self.entropy_losses = checkpoint.get('entropy_losses', [])
        
        logger.info(f"Loaded model from {path}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create environment
    env = TradingEnvironment()
    
    # Generate sample data
    data = {}
    for timeframe in ['1m', '5m', '15m', '1h', '4h', '1d']:
        # Create DataFrame with OHLCV data
        df = pd.DataFrame({
            'open': np.random.normal(100, 1, 1000),
            'high': np.random.normal(101, 1, 1000),
            'low': np.random.normal(99, 1, 1000),
            'close': np.random.normal(100, 1, 1000),
            'volume': np.random.normal(1000, 100, 1000)
        })
        
        # Add technical indicators
        df['rsi'] = np.random.normal(50, 10, 1000)
        df['macd'] = np.random.normal(0, 1, 1000)
        df['bb_upper'] = df['close'] + np.random.normal(2, 0.2, 1000)
        df['bb_lower'] = df['close'] - np.random.normal(2, 0.2, 1000)
        df['atr'] = np.random.normal(1, 0.1, 1000)
        
        data[timeframe] = df
    
    # Set data
    env.set_data(data)
    
    # Create agent
    agent = PPOAgent(env)
    
    # Train agent
    agent.train(num_episodes=10, update_frequency=128, eval_frequency=2)
    
    # Evaluate agent
    eval_reward = agent.evaluate(5)
    logger.info(f"Final evaluation reward: {eval_reward:.2f}")
