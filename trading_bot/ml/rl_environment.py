"""
Multi-Timeframe Reinforcement Learning Environment for Trading
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
import gymnasium as gym
from gymnasium import spaces
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Set
import numpy
import pandas

logger = logging.getLogger(__name__)


class TradingEnvironment(gym.Env):
    """
    Multi-timeframe trading environment for reinforcement learning
    
    Features:
    - Multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
    - Realistic market dynamics
    - Transaction costs
    - Risk management constraints
    - Customizable reward functions
    - Feature engineering
    """
    
    metadata = {'render.modes': ['human', 'rgb_array']}
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            super(TradingEnvironment, self).__init__()
        
            self.config = config or {}
        
            # Environment parameters
            self.timeframes = self.config.get('timeframes', ['1m', '5m', '15m', '1h', '4h', '1d'])
            self.window_size = self.config.get('window_size', 100)  # History length
            self.max_episode_steps = self.config.get('max_episode_steps', 1000)
            self.transaction_cost = self.config.get('transaction_cost', 0.001)  # 0.1% per trade
            self.slippage = self.config.get('slippage', 0.0005)  # 0.05% slippage
            self.capital = self.config.get('initial_capital', 10000.0)
            self.leverage = self.config.get('leverage', 1.0)
        
            # Feature parameters
            self.features = self.config.get('features', [
                'close', 'open', 'high', 'low', 'volume',
                'rsi', 'macd', 'bb_upper', 'bb_lower', 'atr'
            ])
        
            # Reward function parameters
            self.reward_function = self.config.get('reward_function', 'sharpe')
            self.reward_scaling = self.config.get('reward_scaling', 1.0)
        
            # Data
            self.data = {}
            self.current_step = 0
            self.current_time = None
            self.history = {}
        
            # State
            self.position = 0.0  # Current position size (-1.0 to 1.0)
            self.equity = self.capital
            self.returns = []
        
            # Action and observation spaces
            self._setup_spaces()
        
            # Episode tracking
            self.episode_count = 0
            self.total_reward = 0.0
            self.steps_beyond_done = None
        
            logger.info("Trading Environment initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _setup_spaces(self):
        """Setup action and observation spaces"""
        # Action space: position size from -1.0 (full short) to 1.0 (full long)
        try:
            self.action_space = spaces.Box(
                low=-1.0, high=1.0, shape=(1,), dtype=np.float32
            )
        
            # Observation space: multi-timeframe features
            num_features = len(self.features)
            num_timeframes = len(self.timeframes)
        
            # Each timeframe has a set of features for each time step in the window
            self.observation_space = spaces.Box(
                low=-np.inf, high=np.inf, 
                shape=(num_timeframes, num_features, self.window_size),
                dtype=np.float32
            )
        except Exception as e:
            logger.error(f"Error in _setup_spaces: {e}")
            raise
    
    def reset(self):
        """Reset the environment to initial state"""
        try:
            self.current_step = self.window_size
            self.position = 0.0
            self.equity = self.capital
            self.returns = []
            self.total_reward = 0.0
            self.steps_beyond_done = None
        
            # Reset history
            for timeframe in self.timeframes:
                self.history[timeframe] = deque(maxlen=self.window_size)
            
                # Fill history with initial data
                for i in range(self.window_size):
                    if timeframe in self.data and i < len(self.data[timeframe]):
                        self.history[timeframe].append(self.data[timeframe].iloc[i])
        
            # Get current time
            if self.timeframes[0] in self.data and len(self.data[self.timeframes[0]]) > self.current_step:
                self.current_time = self.data[self.timeframes[0]].iloc[self.current_step].name
        
            # Increment episode count
            self.episode_count += 1
        
            return self._get_observation()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def step(self, action):
        """
        Take a step in the environment
        
        Args:
            action: Position size from -1.0 (full short) to 1.0 (full long)
            
        Returns:
            observation, reward, done, info
        """
        try:
            if self.steps_beyond_done is not None:
                logger.warning("You are calling 'step()' even though this environment has already returned done = True. You should always call 'reset()' once you receive 'done = True'")
                return self._get_observation(), 0.0, True, {}
        
            # Ensure action is in correct format
            action = np.clip(action, -1.0, 1.0)[0]
        
            # Calculate reward based on current position and price change
            reward, info = self._calculate_reward(action)
        
            # Update position
            old_position = self.position
            self.position = action
        
            # Update equity based on price change and transaction costs
            if abs(self.position - old_position) > 0:
                # Transaction cost
                transaction_cost = abs(self.position - old_position) * self.transaction_cost * self.equity
                self.equity -= transaction_cost
                info['transaction_cost'] = transaction_cost
        
            # Update returns
            self.returns.append(info['return'])
        
            # Update total reward
            self.total_reward += reward
        
            # Move to next step
            self.current_step += 1
        
            # Update history with new data
            for timeframe in self.timeframes:
                if timeframe in self.data and self.current_step < len(self.data[timeframe]):
                    self.history[timeframe].append(self.data[timeframe].iloc[self.current_step])
        
            # Update current time
            if self.timeframes[0] in self.data and self.current_step < len(self.data[self.timeframes[0]]):
                self.current_time = self.data[self.timeframes[0]].iloc[self.current_step].name
        
            # Check if episode is done
            done = False
            if self.current_step >= len(self.data[self.timeframes[0]]) - 1 or self.current_step >= self.max_episode_steps:
                done = True
                self.steps_beyond_done = 0
        
            # Get observation
            observation = self._get_observation()
        
            # Add additional info
            info['equity'] = self.equity
            info['position'] = self.position
            info['step'] = self.current_step
            info['total_reward'] = self.total_reward
        
            return observation, reward, done, info
        except Exception as e:
            logger.error(f"Error in step: {e}")
            raise
    
    def _calculate_reward(self, new_position):
        """
        Calculate reward based on position and price change
        
        Args:
            new_position: New position size
            
        Returns:
            reward, info
        """
        try:
            info = {}
        
            # Get current and previous prices
            if self.timeframes[0] not in self.data or self.current_step >= len(self.data[self.timeframes[0]]):
                return 0.0, {'return': 0.0}
        
            current_price = self.data[self.timeframes[0]].iloc[self.current_step]['close']
            prev_price = self.data[self.timeframes[0]].iloc[self.current_step - 1]['close']
        
            # Calculate price change
            price_change = (current_price - prev_price) / prev_price
        
            # Calculate return based on position
            position_return = self.position * price_change * self.leverage
        
            # Add slippage for position changes
            if abs(new_position - self.position) > 0:
                position_return -= abs(new_position - self.position) * self.slippage
        
            info['return'] = position_return
        
            # Calculate reward based on selected reward function
            if self.reward_function == 'sharpe':
                # Sharpe ratio (approximated)
                if len(self.returns) > 1:
                    returns_std = np.std(self.returns) if np.std(self.returns) > 0 else 1e-6
                    reward = position_return / returns_std
                else:
                    reward = position_return
        
            elif self.reward_function == 'sortino':
                # Sortino ratio (approximated)
                negative_returns = [r for r in self.returns if r < 0]
                if negative_returns and len(negative_returns) > 1:
                    downside_std = np.std(negative_returns) if np.std(negative_returns) > 0 else 1e-6
                    reward = position_return / downside_std
                else:
                    reward = position_return
        
            elif self.reward_function == 'calmar':
                # Calmar ratio (approximated)
                if self.returns:
                    max_drawdown = self._calculate_max_drawdown()
                    if max_drawdown > 0:
                        reward = position_return / max_drawdown
                    else:
                        reward = position_return
                else:
                    reward = position_return
        
            else:  # Default to simple returns
                reward = position_return
        
            # Scale reward
            reward *= self.reward_scaling
        
            return reward, info
        except Exception as e:
            logger.error(f"Error in _calculate_reward: {e}")
            raise
    
    def _calculate_max_drawdown(self):
        """Calculate maximum drawdown from returns"""
        try:
            cumulative = np.cumprod(np.array(self.returns) + 1)
            peak = np.maximum.accumulate(cumulative)
            drawdown = (peak - cumulative) / peak
            return np.max(drawdown) if len(drawdown) > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown: {e}")
            raise
    
    def _get_observation(self):
        """Get current observation (state)"""
        try:
            observation = np.zeros(self.observation_space.shape, dtype=np.float32)
        
            for i, timeframe in enumerate(self.timeframes):
                if timeframe in self.history:
                    # Convert history to numpy array
                    history_array = np.array([[item[feature] for feature in self.features] 
                                             for item in self.history[timeframe]])
                
                    # Normalize features
                    history_array = self._normalize_features(history_array, timeframe)
                
                    # Fill observation
                    if history_array.shape[0] > 0:
                        # Transpose to get (features, time_steps)
                        observation[i, :, :history_array.shape[0]] = history_array.T
        
            return observation
        except Exception as e:
            logger.error(f"Error in _get_observation: {e}")
            raise
    
    def _normalize_features(self, features, timeframe):
        """Normalize features to have zero mean and unit variance"""
        # Simple normalization - subtract mean and divide by std
        try:
            epsilon = 1e-8  # To avoid division by zero
        
            for i in range(features.shape[1]):
                mean = np.mean(features[:, i])
                std = np.std(features[:, i])
                if std > epsilon:
                    features[:, i] = (features[:, i] - mean) / std
        
            return features
        except Exception as e:
            logger.error(f"Error in _normalize_features: {e}")
            raise
    
    def set_data(self, data: Dict[str, pd.DataFrame]):
        """
        Set market data for all timeframes
        
        Args:
            data: Dictionary of timeframe to DataFrame
        """
        try:
            self.data = data
        
            # Verify data
            for timeframe in self.timeframes:
                if timeframe not in data:
                    logger.warning(f"No data provided for timeframe {timeframe}")
                else:
                    logger.info(f"Loaded {len(data[timeframe])} data points for timeframe {timeframe}")
        
            # Reset environment
            self.reset()
        except Exception as e:
            logger.error(f"Error in set_data: {e}")
            raise
    
    def render(self, mode='human'):
        """Render the environment"""
        try:
            if mode == 'human':
                # Print current state
                logger.info(f"Step: {self.current_step}, Time: {self.current_time}")
                logger.info(f"Position: {self.position:.2f}, Equity: {self.equity:.2f}")
                logger.info(f"Reward: {self.total_reward:.4f}")
            
                # Print current prices for each timeframe
                for timeframe in self.timeframes:
                    if timeframe in self.data and self.current_step < len(self.data[timeframe]):
                        price = self.data[timeframe].iloc[self.current_step]['close']
                        logger.info(f"{timeframe} Price: {price:.4f}")
            
                print("-" * 50)
        
            elif mode == 'rgb_array':
                # Return an RGB array for rendering
                # This would typically be implemented for visualization
                return np.zeros((100, 100, 3), dtype=np.uint8)
        except Exception as e:
            logger.error(f"Error in render: {e}")
            raise
    
    def close(self):
        """Clean up resources"""
        pass


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
    
    # Test environment
    observation = env.reset()
    logger.info(f"Observation shape: {observation.shape}")
    
    for i in range(10):
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        env.render()
        
        if done:
            break
    
    logger.info("Environment test complete")
