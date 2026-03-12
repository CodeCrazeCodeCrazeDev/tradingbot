"""
Distributional Reinforcement Learning - Phase 1
Predict full return distributions instead of just expected values
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QuantileNetwork(nn.Module):
    """Neural network that outputs quantile predictions."""
    
    def __init__(self, state_dim: int, action_dim: int, num_quantiles: int = 51):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_quantiles = num_quantiles
        
        # Shared feature extraction
        self.feature_network = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Quantile prediction head
        self.quantile_head = nn.Linear(256, action_dim * num_quantiles)
    
    def forward(self, state):
        """
        Returns quantile predictions for each action.
        Output shape: [batch_size, action_dim, num_quantiles]
        """
        features = self.feature_network(state)
        quantiles = self.quantile_head(features)
        return quantiles.view(-1, self.action_dim, self.num_quantiles)


class DistributionalQLearning:
    """
    Quantile Regression DQN (QR-DQN)
    Learns full distribution of returns for better risk assessment
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        num_quantiles: int = 51,
        learning_rate: float = 0.0001,
        gamma: float = 0.99
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_quantiles = num_quantiles
        self.gamma = gamma
        
        # Quantile midpoints
        self.quantiles = torch.linspace(0.0, 1.0, num_quantiles)
        
        # Networks
        self.network = QuantileNetwork(state_dim, action_dim, num_quantiles)
        self.target_network = QuantileNetwork(state_dim, action_dim, num_quantiles)
        self.target_network.load_state_dict(self.network.state_dict())
        
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=learning_rate)
        
        logger.info(f"✅ Distributional RL initialized: {num_quantiles} quantiles")
    
    def predict_distribution(self, state: torch.Tensor) -> np.ndarray:
        """
        Predict full return distribution for each action.
        Returns: [action_dim, num_quantiles]
        """
        self.network.eval()
        with torch.no_grad():
            if len(state.shape) == 1:
                state = state.unsqueeze(0)
            quantiles = self.network(state)
        return quantiles.squeeze(0).numpy()
    
    def calculate_cvar(self, distribution: np.ndarray, alpha: float = 0.05) -> float:
        """
        Conditional Value at Risk (CVaR) - Expected loss in worst alpha% of cases.
        Lower is worse (more negative).
        """
        sorted_dist = np.sort(distribution)
        tail_index = int(alpha * len(sorted_dist))
        if tail_index == 0:
            tail_index = 1
        return sorted_dist[:tail_index].mean()
    
    def calculate_var(self, distribution: np.ndarray, alpha: float = 0.05) -> float:
        """
        Value at Risk (VaR) - Worst expected loss at alpha confidence level.
        """
        return np.quantile(distribution, alpha)
    
    def calculate_expected_return(self, distribution: np.ndarray) -> float:
        """Expected return (mean of distribution)."""
        return distribution.mean()
    
    def select_action(
        self,
        state: torch.Tensor,
        risk_aversion: float = 0.5,
        epsilon: float = 0.0
    ) -> int:
        """
        Select action considering risk.
        
        Args:
            state: Current market state
            risk_aversion: 0 = risk-neutral, 1 = very risk-averse
            epsilon: Exploration rate
        
        Returns:
            Selected action index
        """
        # Epsilon-greedy exploration
        if np.random.random() < epsilon:
            return np.random.randint(self.action_dim)
        
        distributions = self.predict_distribution(state)
        
        # For each action, compute risk-adjusted value
        action_values = []
        for action_dist in distributions:
            mean_return = self.calculate_expected_return(action_dist)
            cvar = self.calculate_cvar(action_dist, alpha=0.05)
            
            # Risk-adjusted value: blend expected return with tail risk
            # risk_aversion=0: only care about expected return
            # risk_aversion=1: only care about avoiding losses
            value = (1 - risk_aversion) * mean_return + risk_aversion * cvar
            action_values.append(value)
        
        return int(np.argmax(action_values))
    
    def quantile_huber_loss(
        self,
        quantiles: torch.Tensor,
        target_quantiles: torch.Tensor,
        kappa: float = 1.0
    ) -> torch.Tensor:
        """
        Quantile Huber loss for distributional RL.
        
        Args:
            quantiles: Predicted quantiles [batch, num_quantiles]
            target_quantiles: Target quantiles [batch, num_quantiles]
            kappa: Huber loss threshold
        """
        # Pairwise differences
        td_errors = target_quantiles.unsqueeze(-1) - quantiles.unsqueeze(-2)
        
        # Huber loss
        huber_loss = torch.where(
            td_errors.abs() <= kappa,
            0.5 * td_errors.pow(2),
            kappa * (td_errors.abs() - 0.5 * kappa)
        )
        
        # Quantile weights
        tau = self.quantiles.unsqueeze(0).unsqueeze(-1)
        quantile_weights = torch.abs(tau - (td_errors < 0).float())
        
        loss = (quantile_weights * huber_loss).mean()
        return loss
    
    def update(
        self,
        state: torch.Tensor,
        action: int,
        reward: float,
        next_state: torch.Tensor,
        done: bool
    ) -> float:
        """
        Update network with experience.
        
        Returns:
            Training loss
        """
        self.network.train()
        
        # Current quantiles
        current_quantiles = self.network(state)[0, action, :]
        
        # Target quantiles
        with torch.no_grad():
            if done:
                target_quantiles = torch.full_like(current_quantiles, reward)
            else:
                next_quantiles = self.target_network(next_state)[0]
                
                # Select best action based on expected return
                next_action = next_quantiles.mean(dim=1).argmax()
                
                # Bellman update for quantiles
                target_quantiles = reward + self.gamma * next_quantiles[next_action]
        
        # Compute loss
        loss = self.quantile_huber_loss(
            current_quantiles.unsqueeze(0),
            target_quantiles.unsqueeze(0)
        )
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.network.parameters(), 1.0)
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self, tau: float = 0.005):
        """Soft update of target network."""
        for target_param, param in zip(
            self.target_network.parameters(),
            self.network.parameters()
        ):
            target_param.data.copy_(
                tau * param.data + (1 - tau) * target_param.data
            )
    
    def get_risk_metrics(self, state: torch.Tensor, action: int) -> dict:
        """
        Get comprehensive risk metrics for an action.
        
        Returns:
            Dictionary with risk metrics
        """
        distributions = self.predict_distribution(state)
        action_dist = distributions[action]
        
        return {
            'expected_return': self.calculate_expected_return(action_dist),
            'var_5%': self.calculate_var(action_dist, 0.05),
            'cvar_5%': self.calculate_cvar(action_dist, 0.05),
            'var_1%': self.calculate_var(action_dist, 0.01),
            'cvar_1%': self.calculate_cvar(action_dist, 0.01),
            'std': action_dist.std(),
            'skewness': self._calculate_skewness(action_dist),
            'kurtosis': self._calculate_kurtosis(action_dist),
            'downside_risk': self._calculate_downside_risk(action_dist)
        }
    
    def _calculate_skewness(self, distribution: np.ndarray) -> float:
        """Calculate skewness of distribution."""
        mean = distribution.mean()
        std = distribution.std()
        if std == 0:
            return 0.0
        return ((distribution - mean) ** 3).mean() / (std ** 3)
    
    def _calculate_kurtosis(self, distribution: np.ndarray) -> float:
        """Calculate kurtosis of distribution."""
        mean = distribution.mean()
        std = distribution.std()
        if std == 0:
            return 0.0
        return ((distribution - mean) ** 4).mean() / (std ** 4) - 3
    
    def _calculate_downside_risk(self, distribution: np.ndarray) -> float:
        """Calculate downside deviation (semi-deviation)."""
        negative_returns = distribution[distribution < 0]
        if len(negative_returns) == 0:
            return 0.0
        return np.sqrt((negative_returns ** 2).mean())
    
    def save(self, filepath: str):
        """Save model."""
        torch.save({
            'network': self.network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict()
        }, filepath)
        logger.info(f"💾 Distributional RL saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model."""
        checkpoint = torch.load(filepath)
        self.network.load_state_dict(checkpoint['network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        logger.info(f"📂 Distributional RL loaded from {filepath}")
