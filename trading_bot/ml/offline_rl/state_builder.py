"""
State Builder for AlphaAlgo Offline RL

Converts market data into state vectors for RL agents.
Handles feature engineering, normalization, and state representation.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from collections import deque
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketStateBuilder:
    """
    Builds state vectors from market data for RL agents.
    
    Features:
    - Technical indicators
    - Price patterns
    - Volume analysis
    - Market microstructure
    - Multi-timeframe features
    """
    
    def __init__(
        self,
        lookback_window: int = 50,
        include_features: Optional[List[str]] = None,
        normalize: bool = True
    ):
        """
        Initialize state builder.
        
        Args:
            lookback_window: Number of historical bars to include
            include_features: List of features to include (None = all)
            normalize: Whether to normalize features
        """
        try:
            self.lookback_window = lookback_window
            self.include_features = include_features
            self.normalize = normalize
        
            # Feature statistics for normalization
            self.feature_stats = {}
            self.is_fitted = False
        
            # History buffer
            self.history = deque(maxlen=lookback_window)
        
            logger.info(f"State builder initialized: lookback={lookback_window}, normalize={normalize}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def build_state(
        self,
        market_data: pd.DataFrame,
        current_position: float = 0.0,
        account_info: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Build state vector from market data.
        
        Args:
            market_data: DataFrame with OHLCV and indicators
            current_position: Current position (-1 to 1)
            account_info: Account information (balance, equity, etc.)
        
        Returns:
            State vector
        """
        try:
            features = []
        
            # Price features
            if 'close' in market_data.columns:
                close_prices = market_data['close'].values[-self.lookback_window:]
            
                # Returns
                returns = np.diff(close_prices) / close_prices[:-1]
                features.extend(returns[-10:].tolist())  # Last 10 returns
            
                # Price momentum
                if len(close_prices) >= 5:
                    momentum_5 = (close_prices[-1] - close_prices[-5]) / close_prices[-5]
                    features.append(momentum_5)
            
                if len(close_prices) >= 20:
                    momentum_20 = (close_prices[-1] - close_prices[-20]) / close_prices[-20]
                    features.append(momentum_20)
        
            # Technical indicators
            indicator_names = ['rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower', 
                              'atr', 'adx', 'cci', 'stoch_k', 'stoch_d']
        
            for indicator in indicator_names:
                if indicator in market_data.columns:
                    value = market_data[indicator].iloc[-1]
                    features.append(value)
        
            # Volume features
            if 'volume' in market_data.columns:
                volumes = market_data['volume'].values[-self.lookback_window:]
            
                # Volume ratio
                if len(volumes) >= 20:
                    vol_ratio = volumes[-1] / np.mean(volumes[-20:])
                    features.append(vol_ratio)
            
                # Volume trend
                if len(volumes) >= 5:
                    vol_trend = (volumes[-1] - volumes[-5]) / volumes[-5]
                    features.append(vol_trend)
        
            # Volatility features
            if 'close' in market_data.columns:
                close_prices = market_data['close'].values[-self.lookback_window:]
            
                if len(close_prices) >= 20:
                    volatility = np.std(np.diff(close_prices[-20:]) / close_prices[-21:-1])
                    features.append(volatility)
        
            # Position features
            features.append(current_position)
        
            # Account features
            if account_info:
                features.append(account_info.get('equity', 10000) / 10000)  # Normalized equity
                features.append(account_info.get('margin_level', 100) / 100)  # Normalized margin
                features.append(account_info.get('free_margin', 10000) / 10000)
        
            # Convert to numpy array
            state = np.array(features, dtype=np.float32)
        
            # Normalize if enabled
            if self.normalize:
                state = self._normalize_state(state)
        
            # Handle NaN/Inf
            state = np.nan_to_num(state, nan=0.0, posinf=1.0, neginf=-1.0)
        
            return state
        except Exception as e:
            logger.error(f"Error in build_state: {e}")
            raise
    
    def _normalize_state(self, state: np.ndarray) -> np.ndarray:
        """
        Normalize state vector.
        
        Args:
            state: Raw state vector
        
        Returns:
            Normalized state vector
        """
        try:
            if not self.is_fitted:
                # Initialize statistics
                self.feature_stats['mean'] = state.copy()
                self.feature_stats['std'] = np.ones_like(state)
                self.feature_stats['count'] = 1
                self.is_fitted = True
                return state
        
            # Update running statistics
            self.feature_stats['count'] += 1
            delta = state - self.feature_stats['mean']
            self.feature_stats['mean'] += delta / self.feature_stats['count']
            delta2 = state - self.feature_stats['mean']
            self.feature_stats['std'] = np.sqrt(
                (self.feature_stats['std']**2 * (self.feature_stats['count'] - 1) + delta * delta2) / 
                self.feature_stats['count']
            )
        
            # Normalize
            normalized = (state - self.feature_stats['mean']) / (self.feature_stats['std'] + 1e-8)
        
            # Clip to reasonable range
            normalized = np.clip(normalized, -5, 5)
        
            return normalized
        except Exception as e:
            logger.error(f"Error in _normalize_state: {e}")
            raise
    
    def get_state_dim(self) -> int:
        """
        Get state dimension.
        
        Returns:
            State dimension
        """
        # This is an estimate - actual dimension depends on available features
        try:
            base_features = 10  # Returns
            indicators = 10  # Technical indicators
            volume = 2  # Volume features
            volatility = 1
            position = 1
            account = 3
        
            return base_features + indicators + volume + volatility + position + account
        except Exception as e:
            logger.error(f"Error in get_state_dim: {e}")
            raise
    
    def reset(self):
        """Reset state builder."""
        try:
            self.history.clear()
            logger.debug("State builder reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


class ActionMapper:
    """
    Maps discrete RL actions to trading actions.
    
    Supports multiple action spaces:
    - Simple: Hold, Buy, Sell
    - Extended: Hold, Buy Small, Buy Large, Sell Small, Sell Large
    - Continuous: Position size from -1 to 1
    """
    
    def __init__(self, action_space: str = 'simple'):
        """
        Initialize action mapper.
        
        Args:
            action_space: Type of action space ('simple', 'extended', 'continuous')
        """
        try:
            self.action_space = action_space
        
            if action_space == 'simple':
                self.action_dim = 3
                self.action_names = ['hold', 'buy', 'sell']
            elif action_space == 'extended':
                self.action_dim = 5
                self.action_names = ['hold', 'buy_small', 'buy_large', 'sell_small', 'sell_large']
            elif action_space == 'continuous':
                self.action_dim = 1
                self.action_names = ['position']
            else:
                raise ValueError(f"Unknown action space: {action_space}")
        
            logger.info(f"Action mapper initialized: space={action_space}, dim={self.action_dim}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def map_action(self, action: int) -> Dict[str, Any]:
        """
        Map RL action to trading action.
        
        Args:
            action: RL action index
        
        Returns:
            Trading action dictionary
        """
        try:
            if self.action_space == 'simple':
                if action == 0:
                    return {'type': 'hold', 'size': 0.0}
                elif action == 1:
                    return {'type': 'buy', 'size': 1.0}
                elif action == 2:
                    return {'type': 'sell', 'size': 1.0}
        
            elif self.action_space == 'extended':
                if action == 0:
                    return {'type': 'hold', 'size': 0.0}
                elif action == 1:
                    return {'type': 'buy', 'size': 0.5}
                elif action == 2:
                    return {'type': 'buy', 'size': 1.0}
                elif action == 3:
                    return {'type': 'sell', 'size': 0.5}
                elif action == 4:
                    return {'type': 'sell', 'size': 1.0}
        
            return {'type': 'hold', 'size': 0.0}
        except Exception as e:
            logger.error(f"Error in map_action: {e}")
            raise
    
    def get_action_dim(self) -> int:
        """Get action dimension."""
        return self.action_dim


class RewardCalculator:
    """
    Calculates rewards for RL training.
    
    Supports multiple reward functions:
    - Simple: PnL
    - Sharpe: Risk-adjusted returns
    - Sortino: Downside risk-adjusted
    - Custom: User-defined
    """
    
    def __init__(self, reward_type: str = 'sharpe', risk_free_rate: float = 0.0):
        """
        Initialize reward calculator.
        
        Args:
            reward_type: Type of reward ('simple', 'sharpe', 'sortino', 'custom')
            risk_free_rate: Risk-free rate for Sharpe calculation
        """
        try:
            self.reward_type = reward_type
            self.risk_free_rate = risk_free_rate
        
            # History for risk-adjusted metrics
            self.returns_history = deque(maxlen=100)
        
            logger.info(f"Reward calculator initialized: type={reward_type}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_reward(
        self,
        pnl: float,
        position_change: float = 0.0,
        transaction_cost: float = 0.0
    ) -> float:
        """
        Calculate reward.
        
        Args:
            pnl: Profit/loss
            position_change: Change in position size
            transaction_cost: Transaction cost
        
        Returns:
            Reward value
        """
        # Net PnL after costs
        try:
            net_pnl = pnl - transaction_cost
        
            # Store return
            self.returns_history.append(net_pnl)
        
            if self.reward_type == 'simple':
                return net_pnl
        
            elif self.reward_type == 'sharpe':
                if len(self.returns_history) < 2:
                    return net_pnl
            
                returns = np.array(self.returns_history)
                mean_return = np.mean(returns)
                std_return = np.std(returns)
            
                if std_return > 0:
                    sharpe = (mean_return - self.risk_free_rate) / std_return
                    return sharpe * net_pnl
                else:
                    return net_pnl
        
            elif self.reward_type == 'sortino':
                if len(self.returns_history) < 2:
                    return net_pnl
            
                returns = np.array(self.returns_history)
                mean_return = np.mean(returns)
            
                # Downside deviation
                downside_returns = returns[returns < 0]
                if len(downside_returns) > 0:
                    downside_std = np.std(downside_returns)
                    if downside_std > 0:
                        sortino = (mean_return - self.risk_free_rate) / downside_std
                        return sortino * net_pnl
            
                return net_pnl
        
            return net_pnl
        except Exception as e:
            logger.error(f"Error in calculate_reward: {e}")
            raise
    
    def reset(self):
        """Reset reward calculator."""
        try:
            self.returns_history.clear()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    logger.info("STATE BUILDER DEMO")
    print("="*60)
    
    # Create state builder
    builder = MarketStateBuilder(lookback_window=50)
    
    # Create sample market data
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
        'rsi': np.random.uniform(30, 70, 100),
        'macd': np.random.randn(100),
        'macd_signal': np.random.randn(100),
        'atr': np.random.uniform(0.5, 2.0, 100)
    })
    
    # Build state
    state = builder.build_state(data, current_position=0.5)
    logger.info(f"\nState dimension: {len(state)}")
    logger.info(f"State sample: {state[:10]}")
    
    # Test action mapper
    print("\n" + "="*60)
    logger.info("ACTION MAPPER DEMO")
    print("="*60)
    
    mapper = ActionMapper('simple')
    for i in range(3):
        action = mapper.map_action(i)
        logger.info(f"Action {i}: {action}")
    
    # Test reward calculator
    print("\n" + "="*60)
    logger.info("REWARD CALCULATOR DEMO")
    print("="*60)
    
    calc = RewardCalculator('sharpe')
    for i in range(10):
        pnl = np.random.randn() * 10
        reward = calc.calculate_reward(pnl, transaction_cost=0.1)
        logger.info(f"PnL: {pnl:6.2f}, Reward: {reward:6.2f}")
    
    print("\n" + "="*60)
    logger.info("DEMO COMPLETE")
    print("="*60)
