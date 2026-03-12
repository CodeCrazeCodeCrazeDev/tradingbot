"""
Enhanced Conservative Q-Learning (CQL) Agent
Advanced implementation with risk-awareness and market adaptation
"""

import os
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available")
    TORCH_AVAILABLE = False


@dataclass
class CQLConfig:
    """Configuration for Enhanced CQL."""
    alpha: float = 1.0  # CQL regularization weight
    tau: float = 0.005  # Target network update rate
    discount: float = 0.99  # Reward discount
    lr: float = 3e-4  # Learning rate
    hidden_sizes: List[int] = None  # Hidden layer sizes
    cvar_alpha: float = 0.05  # CVaR risk level
    risk_aversion: float = 0.5  # Risk aversion parameter
    adaptive_alpha: bool = True  # Adaptive CQL weight
    use_distributional: bool = True  # Use distributional Q-learning
    num_quantiles: int = 51  # Number of quantiles for distributional
    
    def __post_init__(self):
        if self.hidden_sizes is None:
            self.hidden_sizes = [256, 256, 128]


class DistributionalCQLNetwork(nn.Module):
    """
    Neural network for distributional CQL.
    Outputs quantile predictions for risk-aware Q-values.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_sizes: List[int],
        num_quantiles: int = 51
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_quantiles = num_quantiles
        
        # Build network layers
        layers = []
        input_dim = state_dim
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(input_dim, hidden_size),
                nn.LayerNorm(hidden_size),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_size
        
        self.feature_network = nn.Sequential(*layers)
        
        # Quantile prediction heads (one per action)
        self.quantile_heads = nn.ModuleList([
            nn.Linear(hidden_sizes[-1], num_quantiles)
            for _ in range(action_dim)
        ])
        
        # Value head for baseline
        self.value_head = nn.Linear(hidden_sizes[-1], 1)
    
    def forward(self, state):
        """
        Forward pass.
        
        Returns:
            quantiles: [batch_size, action_dim, num_quantiles]
            value: [batch_size, 1]
        """
        features = self.feature_network(state)
        
        # Get quantiles for each action
        quantiles = torch.stack([
            head(features) for head in self.quantile_heads
        ], dim=1)
        
        # Get state value
        value = self.value_head(features)
        
        return quantiles, value


class EnhancedCQLAgent:
    """
    Enhanced CQL agent with:
    - Distributional Q-learning for risk awareness
    - CVaR-based policy selection
    - Adaptive CQL regularization
    - Market regime adaptation
    - Comprehensive logging and monitoring
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        config: Optional[CQLConfig] = None,
        log_dir: str = "logs/enhanced_cql"
    ):
        """
        Initialize Enhanced CQL agent.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension
            config: CQL configuration
            log_dir: Directory for logs
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for Enhanced CQL")
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config or CQLConfig()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Networks
        if self.config.use_distributional:
            self.q_network = DistributionalCQLNetwork(
                state_dim, action_dim,
                self.config.hidden_sizes,
                self.config.num_quantiles
            ).to(self.device)
            
            self.target_network = DistributionalCQLNetwork(
                state_dim, action_dim,
                self.config.hidden_sizes,
                self.config.num_quantiles
            ).to(self.device)
        else:
            # Standard Q-network (fallback)
            self.q_network = self._build_standard_network().to(self.device)
            self.target_network = self._build_standard_network().to(self.device)
        
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.config.lr)
        
        # Quantile midpoints for distributional RL
        self.quantiles = torch.linspace(
            0.0, 1.0, self.config.num_quantiles
        ).to(self.device)
        
        # Adaptive alpha
        self.current_alpha = self.config.alpha
        self.alpha_history = []
        
        # Training statistics
        self.training_stats = {
            'total_updates': 0,
            'cql_loss_history': [],
            'bellman_loss_history': [],
            'q_value_history': [],
            'cvar_history': []
        }
        
        logger.info("="*80)
        logger.info("ENHANCED CQL AGENT INITIALIZED")
        logger.info("="*80)
        logger.info(f"State dim: {state_dim}, Action dim: {action_dim}")
        logger.info(f"Distributional: {self.config.use_distributional}")
        logger.info(f"Num quantiles: {self.config.num_quantiles}")
        logger.info(f"CVaR alpha: {self.config.cvar_alpha}")
        logger.info(f"Risk aversion: {self.config.risk_aversion}")
        logger.info(f"Device: {self.device}")
        logger.info("="*80)
    
    def _build_standard_network(self) -> nn.Module:
        """Build standard Q-network (non-distributional)."""
        layers = []
        input_dim = self.state_dim
        
        for hidden_size in self.config.hidden_sizes:
            layers.extend([
                nn.Linear(input_dim, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_size
        
        layers.append(nn.Linear(input_dim, self.action_dim))
        
        return nn.Sequential(*layers)
    
    def select_action(
        self,
        state: np.ndarray,
        epsilon: float = 0.0,
        risk_aware: bool = True
    ) -> int:
        """
        Select action using risk-aware policy.
        
        Args:
            state: Current state
            epsilon: Exploration rate
            risk_aware: Use CVaR for risk-aware selection
        
        Returns:
            Selected action index
        """
        if np.random.random() < epsilon:
            return np.random.randint(self.action_dim)
        
        self.q_network.eval()
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            
            if self.config.use_distributional:
                quantiles, _ = self.q_network(state_tensor)
                quantiles = quantiles.squeeze(0)  # [action_dim, num_quantiles]
                
                if risk_aware:
                    # Use CVaR for risk-aware selection
                    cvars = self._calculate_cvar(quantiles, self.config.cvar_alpha)
                    action = torch.argmax(cvars).item()
                else:
                    # Use expected value
                    expected_values = quantiles.mean(dim=1)
                    action = torch.argmax(expected_values).item()
            else:
                q_values = self.q_network(state_tensor)
                action = torch.argmax(q_values).item()
        
        return action
    
    def _calculate_cvar(self, quantiles: torch.Tensor, alpha: float) -> torch.Tensor:
        """
        Calculate CVaR (Conditional Value at Risk) for each action.
        
        Args:
            quantiles: [action_dim, num_quantiles]
            alpha: Risk level (e.g., 0.05 for 5% worst cases)
        
        Returns:
            CVaR values for each action
        """
        # Sort quantiles
        sorted_quantiles, _ = torch.sort(quantiles, dim=1)
        
        # Get tail quantiles (worst alpha%)
        tail_size = max(1, int(alpha * self.config.num_quantiles))
        tail_quantiles = sorted_quantiles[:, :tail_size]
        
        # CVaR is mean of tail
        cvar = tail_quantiles.mean(dim=1)
        
        return cvar
    
    def update(
        self,
        batch: Dict[str, torch.Tensor],
        update_target: bool = False
    ) -> Dict[str, float]:
        """
        Update Q-network using CQL loss.
        
        Args:
            batch: Batch of transitions
            update_target: Whether to update target network
        
        Returns:
            Dictionary of losses
        """
        self.q_network.train()
        
        states = batch['states'].to(self.device)
        actions = batch['actions'].to(self.device)
        rewards = batch['rewards'].to(self.device)
        next_states = batch['next_states'].to(self.device)
        dones = batch['dones'].to(self.device)
        
        # Forward pass
        if self.config.use_distributional:
            current_quantiles, current_values = self.q_network(states)
            
            with torch.no_grad():
                next_quantiles, _ = self.target_network(next_states)
                
                # Select best action based on expected value
                next_expected = next_quantiles.mean(dim=2)
                next_actions = torch.argmax(next_expected, dim=1)
                
                # Get quantiles for selected actions
                next_quantiles_selected = next_quantiles[
                    torch.arange(next_quantiles.size(0)),
                    next_actions
                ]
                
                # Compute target quantiles
                target_quantiles = rewards.unsqueeze(1) + \
                    self.config.discount * (1 - dones.unsqueeze(1)) * next_quantiles_selected
            
            # Get current action quantiles
            current_quantiles_selected = current_quantiles[
                torch.arange(current_quantiles.size(0)),
                actions.long()
            ]
            
            # Quantile Huber loss (for distributional RL)
            td_errors = target_quantiles.unsqueeze(1) - current_quantiles_selected.unsqueeze(2)
            huber_loss = torch.where(
                td_errors.abs() <= 1.0,
                0.5 * td_errors.pow(2),
                td_errors.abs() - 0.5
            )
            
            quantile_weights = torch.abs(
                self.quantiles.unsqueeze(0).unsqueeze(0) - 
                (td_errors < 0).float()
            )
            
            bellman_loss = (quantile_weights * huber_loss).mean()
            
        else:
            # Standard Q-learning
            current_q = self.q_network(states).gather(1, actions.long().unsqueeze(1))
            
            with torch.no_grad():
                next_q = self.target_network(next_states).max(1)[0]
                target_q = rewards + self.config.discount * (1 - dones) * next_q
            
            bellman_loss = F.mse_loss(current_q.squeeze(), target_q)
        
        # CQL regularization
        if self.config.use_distributional:
            # Distributional CQL: penalize out-of-distribution quantiles
            all_quantiles = current_quantiles.mean(dim=2)  # Average over quantiles
            logsumexp = torch.logsumexp(all_quantiles, dim=1)
            cql_loss = logsumexp.mean() - current_quantiles_selected.mean()
        else:
            # Standard CQL
            all_q = self.q_network(states)
            logsumexp = torch.logsumexp(all_q, dim=1)
            cql_loss = logsumexp.mean() - current_q.mean()
        
        # Adaptive alpha
        if self.config.adaptive_alpha:
            self.current_alpha = self._adapt_alpha(cql_loss.item())
        
        # Total loss
        total_loss = bellman_loss + self.current_alpha * cql_loss
        
        # Optimize
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Update target network
        if update_target:
            self._update_target_network()
        
        # Track statistics
        self.training_stats['total_updates'] += 1
        self.training_stats['cql_loss_history'].append(cql_loss.item())
        self.training_stats['bellman_loss_history'].append(bellman_loss.item())
        
        return {
            'total_loss': total_loss.item(),
            'bellman_loss': bellman_loss.item(),
            'cql_loss': cql_loss.item(),
            'alpha': self.current_alpha
        }
    
    def _adapt_alpha(self, cql_loss: float) -> float:
        """Adapt CQL regularization weight based on loss."""
        # Increase alpha if CQL loss is high (too much OOD action value)
        # Decrease alpha if CQL loss is low (sufficient regularization)
        
        target_cql_loss = 1.0  # Target CQL loss
        adjustment_rate = 0.01
        
        if cql_loss > target_cql_loss:
            new_alpha = self.current_alpha * (1 + adjustment_rate)
        else:
            new_alpha = self.current_alpha * (1 - adjustment_rate)
        
        # Clip alpha to reasonable range
        new_alpha = np.clip(new_alpha, 0.1, 10.0)
        
        self.alpha_history.append(new_alpha)
        
        return new_alpha
    
    def _update_target_network(self):
        """Soft update of target network."""
        for target_param, param in zip(
            self.target_network.parameters(),
            self.q_network.parameters()
        ):
            target_param.data.copy_(
                self.config.tau * param.data + 
                (1 - self.config.tau) * target_param.data
            )
    
    def save(self, path: str):
        """Save model."""
        save_dict = {
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'config': {
                'alpha': self.config.alpha,
                'tau': self.config.tau,
                'discount': self.config.discount,
                'lr': self.config.lr,
                'hidden_sizes': self.config.hidden_sizes,
                'cvar_alpha': self.config.cvar_alpha,
                'risk_aversion': self.config.risk_aversion,
                'use_distributional': self.config.use_distributional,
                'num_quantiles': self.config.num_quantiles
            },
            'training_stats': self.training_stats,
            'current_alpha': self.current_alpha
        }
        
        torch.save(save_dict, path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model."""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.training_stats = checkpoint['training_stats']
        self.current_alpha = checkpoint['current_alpha']
        
        logger.info(f"Model loaded from {path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get training statistics."""
        return {
            'total_updates': self.training_stats['total_updates'],
            'avg_cql_loss': np.mean(self.training_stats['cql_loss_history'][-100:]) 
                if self.training_stats['cql_loss_history'] else 0.0,
            'avg_bellman_loss': np.mean(self.training_stats['bellman_loss_history'][-100:])
                if self.training_stats['bellman_loss_history'] else 0.0,
            'current_alpha': self.current_alpha,
            'device': str(self.device)
        }


def main():
    """Test Enhanced CQL agent."""
    agent = EnhancedCQLAgent(
        state_dim=20,
        action_dim=3,
        config=CQLConfig(
            use_distributional=True,
            adaptive_alpha=True
        )
    )
    
    # Test action selection
    state = np.random.randn(20)
    action = agent.select_action(state, risk_aware=True)
    logger.info(f"Selected action: {action}")
    
    # Test update
    batch = {
        'states': torch.randn(32, 20),
        'actions': torch.randint(0, 3, (32,)),
        'rewards': torch.randn(32),
        'next_states': torch.randn(32, 20),
        'dones': torch.zeros(32)
    }
    
    losses = agent.update(batch)
    logger.info(f"Losses: {losses}")
    
    # Get statistics
    stats = agent.get_statistics()
    logger.info(f"Statistics: {stats}")


if __name__ == '__main__':
    main()
