"""
Skill #29: Reinforcement Learning Gym
=====================================

Custom trading environment for training RL agents
with realistic market simulation.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Action(Enum):
    """Trading actions."""
    HOLD = 0
    BUY = 1
    SELL = 2


@dataclass
class State:
    """Environment state."""
    prices: np.ndarray
    position: float
    cash: float
    portfolio_value: float
    step: int


@dataclass
class Experience:
    """Single experience tuple."""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


@dataclass
class RLResult:
    """RL training/evaluation result."""
    total_reward: float
    final_portfolio: float
    num_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    trading_signal: str


class ReinforcementLearningGym:
    """Custom RL environment for trading."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.initial_cash = self.config.get('initial_cash', 10000)
            self.transaction_cost = self.config.get('transaction_cost', 0.001)
            self.window_size = self.config.get('window_size', 20)
        
            self.prices: np.ndarray = np.array([])
            self.current_step = 0
            self.position = 0.0
            self.cash = self.initial_cash
            self.trades: List[Dict] = []
            self.portfolio_history: List[float] = []
        
            # Simple Q-table for demonstration
            self.q_table: Dict[str, np.ndarray] = {}
            self.learning_rate = 0.1
            self.discount_factor = 0.95
            self.epsilon = 0.1
        
            logger.info("ReinforcementLearningGym initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def reset(self, prices: np.ndarray) -> np.ndarray:
        """Reset environment with new price data."""
        try:
            self.prices = prices
            self.current_step = self.window_size
            self.position = 0.0
            self.cash = self.initial_cash
            self.trades = []
            self.portfolio_history = [self.initial_cash]
        
            return self._get_state()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Take action and return next state, reward, done, info."""
        try:
            current_price = self.prices[self.current_step]
        
            # Execute action
            reward = self._execute_action(action, current_price)
        
            # Move to next step
            self.current_step += 1
            done = self.current_step >= len(self.prices) - 1
        
            # Get new state
            next_state = self._get_state() if not done else np.zeros(self.window_size + 2)
        
            # Track portfolio
            portfolio_value = self.cash + self.position * current_price
            self.portfolio_history.append(portfolio_value)
        
            info = {
                'portfolio_value': portfolio_value,
                'position': self.position,
                'cash': self.cash
            }
        
            return next_state, reward, done, info
        except Exception as e:
            logger.error(f"Error in step: {e}")
            raise
    
    def _get_state(self) -> np.ndarray:
        """Get current state representation."""
        try:
            if self.current_step < self.window_size:
                return np.zeros(self.window_size + 2)
        
            # Price returns
            prices = self.prices[self.current_step - self.window_size:self.current_step]
            returns = np.diff(prices) / prices[:-1]
        
            # Normalize
            normalized_returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-10)
        
            # Add position and cash ratio
            current_price = self.prices[self.current_step]
            portfolio = self.cash + self.position * current_price
            position_ratio = self.position * current_price / portfolio if portfolio > 0 else 0
            cash_ratio = self.cash / portfolio if portfolio > 0 else 1
        
            state = np.concatenate([normalized_returns, [position_ratio, cash_ratio]])
            return state
        except Exception as e:
            logger.error(f"Error in _get_state: {e}")
            raise
    
    def _execute_action(self, action: int, price: float) -> float:
        """Execute trading action and return reward."""
        try:
            old_portfolio = self.cash + self.position * price
        
            if action == Action.BUY.value and self.cash > 0:
                # Buy with all cash
                shares = self.cash / price * (1 - self.transaction_cost)
                self.position += shares
                self.cash = 0
                self.trades.append({'type': 'buy', 'price': price, 'shares': shares})
            
            elif action == Action.SELL.value and self.position > 0:
                # Sell all position
                self.cash = self.position * price * (1 - self.transaction_cost)
                self.trades.append({'type': 'sell', 'price': price, 'shares': self.position})
                self.position = 0
        
            # Calculate reward
            new_portfolio = self.cash + self.position * price
            reward = (new_portfolio - old_portfolio) / old_portfolio
        
            return reward
        except Exception as e:
            logger.error(f"Error in _execute_action: {e}")
            raise
    
    def train(self, prices: np.ndarray, episodes: int = 100) -> RLResult:
        """Train RL agent on price data."""
        try:
            total_rewards = []
        
            for episode in range(episodes):
                state = self.reset(prices)
                episode_reward = 0
            
                while True:
                    # Epsilon-greedy action selection
                    if np.random.random() < self.epsilon:
                        action = np.random.randint(3)
                    else:
                        action = self._get_best_action(state)
                
                    next_state, reward, done, _ = self.step(action)
                
                    # Q-learning update
                    self._update_q(state, action, reward, next_state, done)
                
                    episode_reward += reward
                    state = next_state
                
                    if done:
                        break
            
                total_rewards.append(episode_reward)
            
                # Decay epsilon
                self.epsilon = max(0.01, self.epsilon * 0.99)
        
            return self._calculate_result()
        except Exception as e:
            logger.error(f"Error in train: {e}")
            raise
    
    def _get_best_action(self, state: np.ndarray) -> int:
        """Get best action from Q-table."""
        try:
            state_key = self._state_to_key(state)
            if state_key not in self.q_table:
                return np.random.randint(3)
            return int(np.argmax(self.q_table[state_key]))
        except Exception as e:
            logger.error(f"Error in _get_best_action: {e}")
            raise
    
    def _update_q(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Update Q-value."""
        try:
            state_key = self._state_to_key(state)
            next_key = self._state_to_key(next_state)
        
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(3)
            if next_key not in self.q_table:
                self.q_table[next_key] = np.zeros(3)
        
            current_q = self.q_table[state_key][action]
            next_max_q = 0 if done else np.max(self.q_table[next_key])
        
            new_q = current_q + self.learning_rate * (
                reward + self.discount_factor * next_max_q - current_q
            )
            self.q_table[state_key][action] = new_q
        except Exception as e:
            logger.error(f"Error in _update_q: {e}")
            raise
    
    def _state_to_key(self, state: np.ndarray) -> str:
        """Convert state to hashable key."""
        # Discretize state
        try:
            discretized = np.round(state * 10).astype(int)
            return str(discretized.tolist())
        except Exception as e:
            logger.error(f"Error in _state_to_key: {e}")
            raise
    
    def _calculate_result(self) -> RLResult:
        """Calculate training result metrics."""
        try:
            if not self.portfolio_history:
                return self._create_empty_result()
        
            final_portfolio = self.portfolio_history[-1]
            total_reward = (final_portfolio - self.initial_cash) / self.initial_cash
        
            # Win rate
            wins = sum(1 for i in range(1, len(self.portfolio_history))
                       if self.portfolio_history[i] > self.portfolio_history[i-1])
            win_rate = wins / (len(self.portfolio_history) - 1) if len(self.portfolio_history) > 1 else 0
        
            # Sharpe ratio
            returns = np.diff(self.portfolio_history) / self.portfolio_history[:-1]
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
        
            # Max drawdown
            peak = self.portfolio_history[0]
            max_dd = 0
            for value in self.portfolio_history:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                max_dd = max(max_dd, dd)
        
            signal = self._generate_signal(total_reward, sharpe, max_dd)
        
            return RLResult(
                total_reward=total_reward,
                final_portfolio=final_portfolio,
                num_trades=len(self.trades),
                win_rate=win_rate,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in _calculate_result: {e}")
            raise
    
    def predict_action(self, prices: np.ndarray) -> Tuple[int, float]:
        """Predict best action for current state."""
        try:
            state = self.reset(prices)
            self.current_step = len(prices) - 1
            state = self._get_state()
        
            action = self._get_best_action(state)
        
            state_key = self._state_to_key(state)
            confidence = 0.5
            if state_key in self.q_table:
                q_values = self.q_table[state_key]
                confidence = np.max(q_values) / (np.sum(np.abs(q_values)) + 1e-10)
        
            return action, confidence
        except Exception as e:
            logger.error(f"Error in predict_action: {e}")
            raise
    
    def _generate_signal(self, reward: float, sharpe: float, max_dd: float) -> str:
        """Generate trading signal."""
        try:
            if sharpe > 1 and max_dd < 0.2:
                return f"STRONG: Sharpe {sharpe:.2f}, MaxDD {max_dd:.0%}, Return {reward:.1%}"
            elif sharpe > 0.5:
                return f"MODERATE: Sharpe {sharpe:.2f}, MaxDD {max_dd:.0%}"
            return f"WEAK: Sharpe {sharpe:.2f}, needs more training"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> RLResult:
        """Create empty result."""
        return RLResult(0, 0, 0, 0, 0, 0, "Insufficient data")
