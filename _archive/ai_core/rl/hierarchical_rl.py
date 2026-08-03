"""
Hierarchical Reinforcement Learning with Options Framework

Implements temporal abstraction for trading:
- High-level: Strategy selection (trend-following, mean-reversion, breakout)
- Low-level: Execution (entry, exit, position sizing)

Paper: "Between MDPs and semi-MDPs: A framework for temporal abstraction in RL"
Sutton, Precup, Singh (1999)
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import numpy

logger = logging.getLogger(__name__)


class TradingStrategy(Enum):
    """High-level trading strategies (options)."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    HOLD = "hold"


@dataclass
class Option:
    """Trading option (high-level action)."""
    strategy: TradingStrategy
    initiation_set: callable  # When to start this option
    termination_condition: callable  # When to end this option
    policy: nn.Module  # Low-level policy for this option
    beta: float = 0.9  # Termination probability


class OptionPolicy(nn.Module):
    """Low-level policy for a specific option."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        
        self.ln1 = nn.LayerNorm(hidden_dim)
        self.ln2 = nn.LayerNorm(hidden_dim)
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.ln1(self.fc1(state)))
        x = F.relu(self.ln2(self.fc2(x)))
        return torch.tanh(self.fc3(x))


class OptionCritic(nn.Module):
    """Option-Critic architecture for learning options."""
    
    def __init__(self, state_dim: int, action_dim: int, num_options: int, hidden_dim: int = 256):
        super().__init__()
        self.num_options = num_options
        
        # Q-value over options
        self.q_omega = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_options)
        )
        
        # Intra-option policies
        self.option_policies = nn.ModuleList([
            OptionPolicy(state_dim, action_dim, hidden_dim)
            for _ in range(num_options)
        ])
        
        # Termination functions
        self.terminations = nn.ModuleList([
            nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
                nn.Sigmoid()
            )
            for _ in range(num_options)
        ])
    
    def forward(self, state: torch.Tensor, option: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            state: Current state
            option: Current option index
        
        Returns:
            action: Action from option policy
            termination_prob: Probability of terminating option
        """
        action = self.option_policies[option](state)
        termination_prob = self.terminations[option](state)
        return action, termination_prob
    
    def get_option_values(self, state: torch.Tensor) -> torch.Tensor:
        """Get Q-values for all options."""
        return self.q_omega(state)


class HierarchicalRLAgent:
    """
    Hierarchical RL Agent with Options Framework.
    
    Two-level hierarchy:
    1. High-level: Select trading strategy (option)
    2. Low-level: Execute trades within strategy
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        num_options: int = 6,
        hidden_dim: int = 256,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_options = num_options
        self.device = torch.device(device)
        
        # Option-Critic network
        self.option_critic = OptionCritic(
            state_dim, action_dim, num_options, hidden_dim
        ).to(self.device)
        
        self.optimizer = torch.optim.Adam(
            self.option_critic.parameters(), lr=learning_rate
        )
        
        self.gamma = gamma
        
        # Current option
        self.current_option = None
        self.option_steps = 0
        
        # Strategy mapping
        self.strategies = list(TradingStrategy)
        
        logger.info(f"Hierarchical RL Agent initialized: {num_options} options")
    
    def select_option(self, state: np.ndarray, epsilon: float = 0.1) -> int:
        """Select high-level option (strategy)."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            option_values = self.option_critic.get_option_values(state_tensor)
        
        # Epsilon-greedy selection
        if np.random.random() < epsilon:
            return np.random.randint(self.num_options)
        else:
            return option_values.argmax().item()
    
    def get_action(
        self,
        state: np.ndarray,
        deterministic: bool = False
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Get action using hierarchical policy.
        
        Returns:
            action: Low-level action
            info: Dictionary with option info
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Select or continue option
        if self.current_option is None:
            self.current_option = self.select_option(state)
            self.option_steps = 0
        
        # Get action from current option
        with torch.no_grad():
            action, termination_prob = self.option_critic(state_tensor, self.current_option)
            
            # Check termination
            if not deterministic and np.random.random() < termination_prob.item():
                # Terminate current option, select new one
                self.current_option = self.select_option(state)
                self.option_steps = 0
                action, termination_prob = self.option_critic(state_tensor, self.current_option)
        
        self.option_steps += 1
        
        info = {
            'option': self.current_option,
            'strategy': self.strategies[self.current_option].value,
            'option_steps': self.option_steps,
            'termination_prob': termination_prob.item()
        }
        
        return action.cpu().numpy()[0], info
    
    def train(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Train hierarchical policy."""
        state = batch['state'].to(self.device)
        action = batch['action'].to(self.device)
        reward = batch['reward'].to(self.device)
        next_state = batch['next_state'].to(self.device)
        done = batch['done'].to(self.device)
        option = batch['option'].to(self.device).long()
        
        batch_size = state.shape[0]
        
        # Current option Q-values
        current_q = self.option_critic.get_option_values(state)
        current_q_option = current_q.gather(1, option.unsqueeze(1))
        
        # Next option Q-values
        with torch.no_grad():
            next_q = self.option_critic.get_option_values(next_state)
            next_q_max = next_q.max(1)[0].unsqueeze(1)
            target_q = reward + (1 - done) * self.gamma * next_q_max
        
        # Option Q-loss
        q_loss = F.mse_loss(current_q_option, target_q)
        
        # Intra-option policy loss
        policy_actions = []
        termination_probs = []
        for i in range(batch_size):
            opt = option[i].item()
            action_pred, term_prob = self.option_critic(state[i:i+1], opt)
            policy_actions.append(action_pred)
            termination_probs.append(term_prob)
        
        policy_actions = torch.cat(policy_actions, dim=0)
        policy_loss = F.mse_loss(policy_actions, action)
        
        # Termination loss
        termination_probs = torch.cat(termination_probs, dim=0)
        
        # Advantage of terminating
        with torch.no_grad():
            option_values = current_q.gather(1, option.unsqueeze(1))
            next_option_values = next_q.max(1)[0].unsqueeze(1)
            termination_advantage = next_option_values - option_values
        
        termination_loss = (termination_probs * termination_advantage.detach()).mean()
        
        # Total loss
        total_loss = q_loss + policy_loss + 0.1 * termination_loss
        
        # Update
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.option_critic.parameters(), 1.0)
        self.optimizer.step()
        
        return {
            'total_loss': total_loss.item(),
            'q_loss': q_loss.item(),
            'policy_loss': policy_loss.item(),
            'termination_loss': termination_loss.item(),
            'mean_q': current_q.mean().item()
        }
    
    def reset_option(self):
        """Reset current option (e.g., at episode end)."""
        self.current_option = None
        self.option_steps = 0


class StrategySelector:
    """High-level strategy selector based on market regime."""
    
    def __init__(self):
        self.regime_strategy_map = {
            'trending_up': TradingStrategy.TREND_FOLLOWING,
            'trending_down': TradingStrategy.TREND_FOLLOWING,
            'ranging': TradingStrategy.MEAN_REVERSION,
            'volatile': TradingStrategy.VOLATILITY,
            'breakout': TradingStrategy.BREAKOUT,
            'momentum': TradingStrategy.MOMENTUM
        }
    
    def select_strategy(
        self,
        market_regime: str,
        market_features: Dict[str, float]
    ) -> TradingStrategy:
        """Select strategy based on market regime and features."""
        
        # Default to regime-based selection
        if market_regime in self.regime_strategy_map:
            return self.regime_strategy_map[market_regime]
        
        # Feature-based selection
        volatility = market_features.get('volatility', 0.02)
        trend_strength = market_features.get('trend_strength', 0.0)
        momentum = market_features.get('momentum', 0.0)
        
        if volatility > 0.03:
            return TradingStrategy.VOLATILITY
        elif abs(trend_strength) > 0.7:
            return TradingStrategy.TREND_FOLLOWING
        elif abs(momentum) > 0.5:
            return TradingStrategy.MOMENTUM
        elif volatility < 0.015:
            return TradingStrategy.MEAN_REVERSION
        else:
            return TradingStrategy.HOLD
    
    def get_strategy_parameters(self, strategy: TradingStrategy) -> Dict[str, Any]:
        """Get parameters for specific strategy."""
        params = {
            TradingStrategy.TREND_FOLLOWING: {
                'entry_threshold': 0.6,
                'exit_threshold': 0.3,
                'stop_loss': 0.02,
                'take_profit': 0.04
            },
            TradingStrategy.MEAN_REVERSION: {
                'entry_threshold': 2.0,  # Standard deviations
                'exit_threshold': 0.5,
                'stop_loss': 0.015,
                'take_profit': 0.02
            },
            TradingStrategy.BREAKOUT: {
                'entry_threshold': 0.8,
                'exit_threshold': 0.4,
                'stop_loss': 0.025,
                'take_profit': 0.05
            },
            TradingStrategy.MOMENTUM: {
                'entry_threshold': 0.7,
                'exit_threshold': 0.3,
                'stop_loss': 0.02,
                'take_profit': 0.04
            },
            TradingStrategy.VOLATILITY: {
                'entry_threshold': 0.5,
                'exit_threshold': 0.2,
                'stop_loss': 0.03,
                'take_profit': 0.03
            },
            TradingStrategy.HOLD: {
                'entry_threshold': 1.0,
                'exit_threshold': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0
            }
        }
        
        return params.get(strategy, params[TradingStrategy.HOLD])


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("HIERARCHICAL RL DEMO")
    print("="*80)
    
    # Create agent
    agent = HierarchicalRLAgent(
        state_dim=20,
        action_dim=3,
        num_options=6,
        hidden_dim=128
    )
    
    # Test action selection
    logger.info("\n[1] Testing hierarchical action selection...")
    state = np.random.randn(20)
    
    for i in range(10):
        action, info = agent.get_action(state)
        print(f"  Step {i+1}: Strategy={info['strategy']}, "
              f"Steps={info['option_steps']}, "
              f"Termination={info['termination_prob']:.3f}")
        
        # Simulate state change
        state = np.random.randn(20)
    
    # Test strategy selector
    logger.info("\n[2] Testing strategy selector...")
    selector = StrategySelector()
    
    regimes = ['trending_up', 'ranging', 'volatile', 'breakout']
    for regime in regimes:
        strategy = selector.select_strategy(regime, {})
        params = selector.get_strategy_parameters(strategy)
        logger.info(f"  Regime: {regime} → Strategy: {strategy.value}")
        logger.info(f"    Parameters: {params}")
    
    # Test training
    logger.info("\n[3] Testing training...")
    batch = {
        'state': torch.randn(32, 20),
        'action': torch.randn(32, 3),
        'reward': torch.randn(32, 1),
        'next_state': torch.randn(32, 20),
        'done': torch.zeros(32, 1),
        'option': torch.randint(0, 6, (32,))
    }
    
    metrics = agent.train(batch)
    logger.info(f"  Training metrics:")
    for key, value in metrics.items():
        logger.info(f"    {key}: {value:.4f}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
