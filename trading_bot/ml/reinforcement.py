"""Reinforcement learning for trading strategy optimization.

This module implements reinforcement learning techniques for optimizing
trading strategies, parameter tuning, and adapting to changing market conditions.
"""

import logging
import os
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional, Any, Set
from loguru import logger

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    torch = None
    nn = None
    F = None


class StrategyOptimizer:
    """Reinforcement learning for trading strategy optimization.
    
    Uses reinforcement learning techniques to optimize trading strategies,
    tune parameters, and adapt to changing market conditions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the strategy optimizer.
        
        Args:
            config: Configuration dictionary with optimizer parameters.
                   If None, default parameters will be used.
        """
        self.config = config or {
            'learning_rate': 0.001,
            'discount_factor': 0.95,
            'exploration_rate': 0.1,
            'episodes': 1000,
            'min_confidence': 60.0,
            'max_signals': 3
        }
        self.model = None
        self.is_trained = False
        self.state_history = []
        self.action_history = []
        self.reward_history = []
        logger.info("StrategyOptimizer initialized")

    def resolve_conflicts(self, signals: List[Any]) -> List[Any]:
        """Resolve conflicting trading signals.
        
        Args:
            signals: List of trading signals to resolve
            
        Returns:
            List of filtered and prioritized signals
        """
        if not signals:
            return []

        # Sort signals by confidence (descending)
        sorted_signals = sorted(signals, key=lambda x: x.confidence, reverse=True)

        # Filter by minimum confidence
        min_confidence = self.config.get('min_confidence', 60.0)
        filtered_signals = [s for s in sorted_signals if s.confidence >= min_confidence]

        # Group signals by direction
        buy_signals = [s for s in filtered_signals if s.direction == "buy"]
        sell_signals = [s for s in filtered_signals if s.direction == "sell"]

        # If we have both buy and sell signals, take the higher confidence ones
        if buy_signals and sell_signals:
            if buy_signals[0].confidence > sell_signals[0].confidence:
                result = buy_signals
            else:
                result = sell_signals
        else:
            result = buy_signals or sell_signals

        # Limit number of signals
        max_signals = self.config.get('max_signals', 3)
        return result[:max_signals]
    
    def define_state_space(self, df: pd.DataFrame) -> np.ndarray:
        """Define the state space from market data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Numpy array with state representation
        """
        # Extract relevant features for state representation
        states = []
        
        if not df.empty and all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # Calculate technical indicators for state representation
            # These are simplified examples - a real implementation would use more sophisticated features
            
            # Price momentum
            df['returns'] = df['close'].pct_change()
            df['momentum'] = df['returns'].rolling(window=10).mean()
            
            # Volatility
            df['volatility'] = df['returns'].rolling(window=20).std()
            
            # Moving average crossovers
            df['sma_fast'] = df['close'].rolling(window=10).mean()
            df['sma_slow'] = df['close'].rolling(window=30).mean()
            df['ma_crossover'] = (df['sma_fast'] > df['sma_slow']).astype(int)
            
            # Relative strength
            df['rsi_raw'] = df['returns'].apply(lambda x: max(x, 0)).rolling(window=14).mean() / \
                           df['returns'].abs().rolling(window=14).mean()
            df['rsi'] = 100 - (100 / (1 + df['rsi_raw']))
            
            # Drop NaN values
            df = df.dropna()
            
            # Select features for state representation
            feature_cols = ['momentum', 'volatility', 'ma_crossover', 'rsi']
            states = df[feature_cols].values
            
        return np.array(states)
    
    def define_action_space(self) -> Dict[int, str]:
        """Define the action space for the trading agent.
        
        Returns:
            Dictionary mapping action indices to action names
        """
        # Simple action space: buy, sell, hold
        return {
            0: 'hold',
            1: 'buy',
            2: 'sell'
        }
    
    def calculate_reward(self, action: int, next_state: np.ndarray, 
                         price_change: float) -> float:
        """Calculate the reward for a given action and resulting state.
        
        Args:
            action: Action taken (0=hold, 1=buy, 2=sell)
            next_state: Resulting state after action
            price_change: Percentage price change
            
        Returns:
            Reward value
        """
        # Simple reward function based on action and price change
        if action == 0:  # hold
            return 0  # neutral reward for holding
        elif action == 1:  # buy
            return price_change * 100  # positive reward if price increases
        elif action == 2:  # sell
            return -price_change * 100  # positive reward if price decreases
        
        return 0
    
    def train(self, df: pd.DataFrame, epochs: int = None) -> Dict[str, Any]:
        """Train the reinforcement learning model on historical data.
        
        Args:
            df: DataFrame with OHLCV data
            epochs: Number of training epochs (overrides config if provided)
            
        Returns:
            Dictionary with training metrics
        """
        # This is a placeholder for actual RL training
        # In a real implementation, this would use a framework like TensorFlow or PyTorch
        
        epochs = epochs or self.config.get('episodes', 1000)
        logger.info(f"Training RL model for {epochs} episodes")
        
        # Prepare state space
        states = self.define_state_space(df)
        
        if len(states) == 0:
            logger.warning("No valid states extracted for training")
            return {'success': False, 'error': 'No valid states'}
            
        # Define action space
        actions = self.define_action_space()
        
        # Calculate price changes for reward calculation
        price_changes = df['close'].pct_change().fillna(0).values
        
        # Training metrics
        metrics = {
            'total_reward': 0,
            'avg_reward': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }
        
        # Simulate training process
        total_reward = 0
        episode_rewards = []
        
        for episode in range(min(epochs, 100)):  # Limit to 100 for demonstration
            # Reset episode state
            episode_reward = 0
            current_position = 0  # -1=short, 0=neutral, 1=long
            
            # Iterate through the time series
            for t in range(len(states) - 1):
                # Current state
                state = states[t]
                
                # Choose action (with exploration)
                if np.random.random() < self.config.get('exploration_rate', 0.1):
                    action = np.random.choice(list(actions.keys()))
                else:
                    # In a real implementation, this would use the trained policy
                    # For now, use a simple heuristic based on momentum
                    momentum = state[0]
                    if momentum > 0.001:
                        action = 1  # buy
                    elif momentum < -0.001:
                        action = 2  # sell
                    else:
                        action = 0  # hold
                
                # Execute action and get next state
                next_state = states[t + 1]
                price_change = price_changes[t + 1]
                
                # Calculate reward
                reward = self.calculate_reward(action, next_state, price_change)
                episode_reward += reward
                
                # Update position
                if action == 1:  # buy
                    current_position = 1
                elif action == 2:  # sell
                    current_position = -1
                
                # Store transition for learning
                self.state_history.append(state)
                self.action_history.append(action)
                self.reward_history.append(reward)
                
                # In a real implementation, this would update the policy/value function
                
            # Track episode metrics
            total_reward += episode_reward
            episode_rewards.append(episode_reward)
            
            if (episode + 1) % 10 == 0:
                logger.debug(f"Episode {episode+1}/{epochs}: Reward = {episode_reward:.2f}")
        
        # Calculate final metrics
        metrics['total_reward'] = total_reward
        metrics['avg_reward'] = total_reward / epochs if epochs > 0 else 0
        
        # Calculate win rate (positive reward episodes)
        positive_episodes = sum(1 for r in episode_rewards if r > 0)
        metrics['win_rate'] = positive_episodes / len(episode_rewards) if episode_rewards else 0
        
        # Calculate maximum drawdown
        cumulative_rewards = np.cumsum(episode_rewards)
        max_dd = 0
        peak = cumulative_rewards[0]
        
        for value in cumulative_rewards:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        metrics['max_drawdown'] = max_dd
        
        # Calculate Sharpe ratio (simplified)
        if len(episode_rewards) > 1:
            mean_reward = np.mean(episode_rewards)
            std_reward = np.std(episode_rewards)
            metrics['sharpe_ratio'] = mean_reward / std_reward if std_reward > 0 else 0
        
        self.is_trained = True
        logger.success(f"RL training completed with avg reward: {metrics['avg_reward']:.2f}")
        return metrics
    
    def optimize_parameters(self, strategy_params: Dict[str, Union[float, int]], 
                           df: pd.DataFrame) -> Dict[str, Union[float, int]]:
        """Optimize strategy parameters using reinforcement learning.
        
        Args:
            strategy_params: Current strategy parameters
            df: DataFrame with OHLCV data
            
        Returns:
            Optimized strategy parameters
        """
        if not self.is_trained:
            logger.warning("Model not trained yet. Call train() first.")
            return strategy_params
            
        logger.info("Optimizing strategy parameters")
        
        # This is a placeholder for actual parameter optimization
        # In a real implementation, this would use the trained RL model
        
        # Simple random search for demonstration
        optimized_params = strategy_params.copy()
        
        # Slightly adjust each parameter
        for param, value in optimized_params.items():
            # Add small random adjustment
            if isinstance(value, float):
                adjustment = np.random.normal(0, 0.1 * value)
                optimized_params[param] = max(0.001, value + adjustment)
            elif isinstance(value, int):
                adjustment = np.random.randint(-1, 2)  # -1, 0, or 1
                optimized_params[param] = max(1, value + adjustment)
        
        logger.info("Parameter optimization complete")
        return optimized_params
    
    def detect_market_regime(self, df: pd.DataFrame) -> Dict[str, float]:
        """Detect the current market regime using state classification.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with regime probabilities
        """
        # Define market regimes
        regimes = {
            'trending_up': 0.0,
            'trending_down': 0.0,
            'ranging': 0.0,
            'volatile': 0.0,
            'breakout': 0.0
        }
        
        if len(df) < 50:
            logger.warning("Not enough data for regime detection")
            return regimes
            
        # Calculate indicators for regime detection
        # Trend strength
        df['atr'] = self._calculate_atr(df)
        df['adx'] = self._calculate_adx(df)
        
        # Volatility
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Drop NaN values
        df = df.dropna()
        
        if len(df) == 0:
            return regimes
            
        # Get latest values
        latest = df.iloc[-1]
        
        # Determine regime probabilities
        adx = latest.get('adx', 0)
        volatility = latest.get('volatility', 0)
        sma_20 = latest.get('sma_20', 0)
        sma_50 = latest.get('sma_50', 0)
        
        # Trending up probability
        if sma_20 > sma_50 and adx > 25:
            regimes['trending_up'] = min(1.0, adx / 100)
            
        # Trending down probability
        if sma_20 < sma_50 and adx > 25:
            regimes['trending_down'] = min(1.0, adx / 100)
            
        # Ranging probability
        if adx < 25:
            regimes['ranging'] = max(0, 1 - (adx / 25))
            
        # Volatility probability
        avg_volatility = df['volatility'].mean()
        if volatility > avg_volatility:
            regimes['volatile'] = min(1.0, volatility / (2 * avg_volatility))
            
        # Breakout probability
        price = latest.get('close', 0)
        upper_band = df['high'].rolling(window=20).max().iloc[-1]
        lower_band = df['low'].rolling(window=20).min().iloc[-1]
        
        if price > upper_band * 0.99:
            regimes['breakout'] = 0.8
        elif price < lower_band * 1.01:
            regimes['breakout'] = 0.8
            
        logger.info("Market regime detection complete")
        return regimes
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range.
        
        Args:
            df: DataFrame with OHLCV data
            period: ATR period
            
        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index.
        
        Args:
            df: DataFrame with OHLCV data
            period: ADX period
            
        Returns:
            Series with ADX values
        """
        # This is a simplified ADX calculation
        # A real implementation would be more precise
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        # Filter +DM and -DM
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm.abs()), 0)
        minus_dm = minus_dm.abs().where((minus_dm < 0) & (minus_dm.abs() > plus_dm), 0)
        
        # Calculate ATR
        atr = self._calculate_atr(df, period)
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        
        # Calculate ADX
        adx = dx.rolling(window=period).mean()
        
        return adx


class MarketRegimeClassifier:
    """Classifier for detecting market regimes.
    
    Identifies different market conditions like trending, ranging,
    volatile, and transitional regimes.
    """
    
    def __init__(self):
        """Initialize the market regime classifier."""
        self.regimes = {
            'trending_up': 0,
            'trending_down': 0,
            'ranging': 0,
            'volatile': 0,
            'breakout': 0
        }
        logger.info("MarketRegimeClassifier initialized")
    
    def classify(self, df: pd.DataFrame) -> Dict[str, float]:
        """Classify the current market regime.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with regime probabilities
        """
        # This is a placeholder for actual regime classification
        # In a real implementation, this would use machine learning models
        
        if len(df) < 50:
            logger.warning("Not enough data for regime classification")
            return self.regimes
            
        # Calculate technical indicators
        df['atr'] = self._calculate_atr(df)
        df['adx'] = self._calculate_adx(df)
        df['volatility'] = df['close'].pct_change().rolling(window=20).std()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Drop NaN values
        df = df.dropna()
        
        if len(df) == 0:
            return self.regimes
            
        # Get latest values
        latest = df.iloc[-1]
        
        # Determine regime probabilities
        adx = latest.get('adx', 0)
        volatility = latest.get('volatility', 0)
        sma_20 = latest.get('sma_20', 0)
        sma_50 = latest.get('sma_50', 0)
        
        regimes = self.regimes.copy()
        
        # Trending up probability
        if sma_20 > sma_50 and adx > 25:
            regimes['trending_up'] = min(1.0, adx / 100)
            
        # Trending down probability
        if sma_20 < sma_50 and adx > 25:
            regimes['trending_down'] = min(1.0, adx / 100)
            
        # Ranging probability
        if adx < 25:
            regimes['ranging'] = max(0, 1 - (adx / 25))
            
        # Volatility probability
        avg_volatility = df['volatility'].mean()
        if volatility > avg_volatility:
            regimes['volatile'] = min(1.0, volatility / (2 * avg_volatility))
            
        # Breakout probability
        price = latest.get('close', 0)
        upper_band = df['high'].rolling(window=20).max().iloc[-1]
        lower_band = df['low'].rolling(window=20).min().iloc[-1]
        
        if price > upper_band * 0.99:
            regimes['breakout'] = 0.8
        elif price < lower_band * 1.01:
            regimes['breakout'] = 0.8
            
        logger.info("Market regime classification complete")
        return regimes
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index."""
        # Simplified ADX calculation
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm.abs()), 0)
        minus_dm = minus_dm.abs().where((minus_dm < 0) & (minus_dm.abs() > plus_dm), 0)
        
        atr = self._calculate_atr(df, period)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.rolling(window=period).mean()
        
        return adx


class PPOAgent:
    """Proximal Policy Optimization (PPO) agent for trading.
    
    Implements a state-of-the-art reinforcement learning algorithm for
    trading strategy optimization with improved stability and sample efficiency.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the PPO agent.
        
        Args:
            config: Configuration dictionary with agent parameters.
                   If None, default parameters will be used.
        """
        self.config = config or {
            'learning_rate': 0.0003,
            'gamma': 0.99,  # Discount factor
            'lambda_': 0.95,  # GAE parameter
            'epsilon': 0.2,  # Clipping parameter
            'value_coef': 0.5,  # Value loss coefficient
            'entropy_coef': 0.01,  # Entropy coefficient
            'max_grad_norm': 0.5,  # Gradient clipping
            'batch_size': 64,
            'epochs': 10,  # Number of epochs to optimize on each batch
            'horizon': 128,  # Rollout length
            'hidden_size': 64,  # Size of hidden layers
        }
        self.policy_network = None
        self.value_network = None
        self.optimizer = None
        self.is_trained = False
        self.training_history = []
        
        logger.info("PPOAgent initialized with config: {}", self.config)
    
    def build_networks(self, state_dim: int, action_dim: int) -> None:
        """Build policy and value networks.
        
        Args:
            state_dim: Dimension of the state space
            action_dim: Dimension of the action space
        """
            
        try:
            logger.info(f"Building networks with state_dim={state_dim}, action_dim={action_dim}")
            
            # Initialize device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            # Define policy network architecture
            class PolicyNetwork(nn.Module):
                def __init__(self, state_dim, action_dim, hidden_size=64):
                    super(PolicyNetwork, self).__init__()
                    self.fc1 = nn.Linear(state_dim, hidden_size)
                    self.fc2 = nn.Linear(hidden_size, hidden_size)
                    self.fc3 = nn.Linear(hidden_size, action_dim)
                    
                def forward(self, x):
                    x = F.relu(self.fc1(x))
                    x = F.relu(self.fc2(x))
                    action_probs = F.softmax(self.fc3(x), dim=-1)
                    return action_probs
            
            # Define value network architecture
            class ValueNetwork(nn.Module):
                def __init__(self, state_dim, hidden_size=64):
                    super(ValueNetwork, self).__init__()
                    self.fc1 = nn.Linear(state_dim, hidden_size)
                    self.fc2 = nn.Linear(hidden_size, hidden_size)
                    self.fc3 = nn.Linear(hidden_size, 1)
                    
                def forward(self, x):
                    x = F.relu(self.fc1(x))
                    x = F.relu(self.fc2(x))
                    value = self.fc3(x)
                    return value
            
            # Create network instances
            self.policy_network = PolicyNetwork(
                state_dim=state_dim, 
                action_dim=action_dim, 
                hidden_size=self.config['hidden_size']
            ).to(self.device)
            
            self.value_network = ValueNetwork(
                state_dim=state_dim,
                hidden_size=self.config['hidden_size']
            ).to(self.device)
            
            # Initialize optimizer
            self.optimizer = torch.optim.Adam(
                list(self.policy_network.parameters()) + list(self.value_network.parameters()),
                lr=self.config['learning_rate']
            )
            
            logger.success("Policy and value networks built successfully")
            
        except ImportError as e:
            logger.error(f"Failed to build networks: {e}. Please install PyTorch.")
            raise
    
    def preprocess_state(self, df: pd.DataFrame) -> np.ndarray:
        """Preprocess market data into state representation.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Numpy array with state representation
        """
        # Extract relevant features for state representation
        states = []
        
        if not df.empty and all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']):
            # Calculate technical indicators for state representation
            # Returns and log returns
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Price momentum at different timeframes
            for window in [5, 10, 20]:
                df[f'momentum_{window}'] = df['close'].pct_change(window)
            
            # Volatility measures
            df['volatility_20'] = df['returns'].rolling(window=20).std()
            df['volatility_ratio'] = df['volatility_20'] / df['volatility_20'].rolling(window=100).mean()
            
            # Moving average features
            for window in [10, 20, 50, 100]:
                df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
                df[f'close_to_sma_{window}'] = df['close'] / df[f'sma_{window}'] - 1
            
            # Moving average crossovers
            df['sma_cross_10_50'] = (df['sma_10'] > df['sma_50']).astype(float)
            df['sma_cross_20_100'] = (df['sma_20'] > df['sma_100']).astype(float)
            
            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df['rsi_14'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
            df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Volume indicators
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma_20']
            
            # ADX (Trend strength)
            df['adx'] = self._calculate_adx(df)
            
            # Drop NaN values
            df = df.dropna()
            
            # Select features for state representation
            feature_cols = [
                'returns', 'log_returns', 
                'momentum_5', 'momentum_10', 'momentum_20',
                'volatility_20', 'volatility_ratio',
                'close_to_sma_20', 'close_to_sma_50',
                'sma_cross_10_50', 'sma_cross_20_100',
                'rsi_14', 'macd', 'macd_hist',
                'bb_width', 'bb_position',
                'volume_ratio', 'adx'
            ]
            
            # Ensure all feature columns exist
            available_cols = [col for col in feature_cols if col in df.columns]
            states = df[available_cols].values
            
        return np.array(states)
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (ADX)."""
        # Calculate True Range
        df['tr1'] = abs(df['high'] - df['low'])
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate Directional Movement
        df['up_move'] = df['high'] - df['high'].shift(1)
        df['down_move'] = df['low'].shift(1) - df['low']
        
        df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
        df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
        
        # Calculate smoothed averages
        df['atr'] = df['tr'].rolling(window=period).mean()
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr'])
        
        # Calculate ADX
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        adx = df['dx'].rolling(window=period).mean()
        
        return adx
    
    def train(self, df: pd.DataFrame, n_iterations: int = 100) -> Dict[str, Any]:
        """Train the PPO agent on historical market data.
        
        Args:
            df: DataFrame with OHLCV data
            n_iterations: Number of training iterations
            
        Returns:
            Dictionary with training metrics
        """
        try:
            from tqdm import tqdm
            import copy
            
            # Preprocess data into state representation
            states = self.preprocess_state(df)
            
            if len(states) == 0:
                logger.warning("No valid states extracted for training")
                return {'success': False, 'error': 'No valid states'}
            
            # Define action space (buy, sell, hold)
            action_dim = 3
            
            # Build networks if not already built
            if self.policy_network is None or self.value_network is None:
                self.build_networks(state_dim=states.shape[1], action_dim=action_dim)
            
            # Calculate price changes for reward calculation
            price_changes = df['close'].pct_change().fillna(0).values
            
            # Training metrics
            metrics = {
                'mean_reward': [],
                'policy_loss': [],
                'value_loss': [],
                'entropy': []
            }
            
            logger.info(f"Starting PPO training for {n_iterations} iterations")
            start_time = time.time()
            
            # Create memory buffer for experience collection
            class Memory:
                def __init__(self):
                    self.states = []
                    self.actions = []
                    self.rewards = []
                    self.values = []
                    self.returns = []
                    self.advantages = []
                    self.log_probs = []
                
                def clear(self):
                    self.states.clear()
                    self.actions.clear()
                    self.rewards.clear()
                    self.values.clear()
                    self.returns.clear()
                    self.advantages.clear()
                    self.log_probs.clear()
                    
                def compute_returns_and_advantages(self, last_value, gamma, lambda_):
                    # Convert rewards to tensor
                    rewards = torch.FloatTensor(self.rewards)
                    values = torch.FloatTensor(self.values + [last_value])
                    
                    # Initialize returns and advantages
                    returns = torch.zeros_like(rewards)
                    advantages = torch.zeros_like(rewards)
                    
                    # Initialize gae
                    gae = 0
                    
                    # Compute returns and advantages
                    for t in reversed(range(len(rewards))):
                        if t == len(rewards) - 1:
                            next_value = last_value
                        else:
                            next_value = values[t + 1]
                            
                        delta = rewards[t] + gamma * next_value - values[t]
                        gae = delta + gamma * lambda_ * gae
                        
                        returns[t] = gae + values[t]
                        advantages[t] = gae
                    
                    # Store returns and advantages
                    self.returns = returns.tolist()
                    self.advantages = advantages.tolist()
            
            # Initialize memory
            memory = Memory()
            
            # Training loop
            for iteration in range(n_iterations):
                # Clear memory
                memory.clear()
                
                # Collect experience
                self.policy_network.eval()
                self.value_network.eval()
                
                # Initialize episode variables
                episode_reward = 0
                position = 0  # 0=no position, 1=long, -1=short
                entry_price = 0
                
                # Use a sliding window approach for training on sequential data
                horizon = min(self.config['horizon'], len(states) - 1)
                start_idx = np.random.randint(0, len(states) - horizon)
                
                # Collect trajectory
                for t in range(start_idx, start_idx + horizon):
                    # Get current state
                    state = states[t]
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                    
                    # Get action probabilities and value
                    with torch.no_grad():
                        action_probs = self.policy_network(state_tensor)
                        value = self.value_network(state_tensor).item()
                    
                    # Sample action
                    action_probs_np = action_probs.cpu().numpy()[0]
                    action = np.random.choice(action_dim, p=action_probs_np)
                    log_prob = torch.log(action_probs[0, action]).item()
                    
                    # Execute action
                    price_change = price_changes[t]
                    current_price = df['close'].iloc[t]
                    
                    # Calculate reward based on action and price change
                    if action == 0:  # hold
                        reward = 0
                    elif action == 1:  # buy
                        if position <= 0:  # if no position or short
                            if position == -1:  # close short position
                                profit = entry_price - current_price
                                reward = profit / entry_price * 100
                            else:
                                reward = 0
                            position = 1
                            entry_price = current_price
                        else:  # already long
                            reward = price_change * 100
                    elif action == 2:  # sell
                        if position >= 0:  # if no position or long
                            if position == 1:  # close long position
                                profit = current_price - entry_price
                                reward = profit / entry_price * 100
                            else:
                                reward = 0
                            position = -1
                            entry_price = current_price
                        else:  # already short
                            reward = -price_change * 100
                    
                    # Store experience
                    memory.states.append(state)
                    memory.actions.append(action)
                    memory.rewards.append(reward)
                    memory.values.append(value)
                    memory.log_probs.append(log_prob)
                    
                    episode_reward += reward
                
                # Calculate last value for returns calculation
                if start_idx + horizon < len(states):
                    last_state = states[start_idx + horizon]
                    last_state_tensor = torch.FloatTensor(last_state).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        last_value = self.value_network(last_state_tensor).item()
                else:
                    last_value = 0
                
                # Compute returns and advantages
                memory.compute_returns_and_advantages(
                    last_value, 
                    self.config['gamma'], 
                    self.config['lambda_']
                )
                
                # Convert experience to tensors
                states_tensor = torch.FloatTensor(memory.states).to(self.device)
                actions_tensor = torch.LongTensor(memory.actions).to(self.device)
                returns_tensor = torch.FloatTensor(memory.returns).to(self.device)
                advantages_tensor = torch.FloatTensor(memory.advantages).to(self.device)
                old_log_probs_tensor = torch.FloatTensor(memory.log_probs).to(self.device)
                
                # Normalize advantages
                advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (advantages_tensor.std() + 1e-8)
                
                # PPO update
                self.policy_network.train()
                self.value_network.train()
                
                # Mini-batch updates
                batch_size = min(self.config['batch_size'], len(memory.states))
                n_batches = len(memory.states) // batch_size
                
                # Track losses for this iteration
                iteration_policy_loss = 0
                iteration_value_loss = 0
                iteration_entropy = 0
                
                # Perform multiple epochs of mini-batch updates
                for _ in range(self.config['epochs']):
                    # Generate random indices
                    indices = np.random.permutation(len(memory.states))
                    
                    for start_idx in range(0, len(memory.states), batch_size):
                        # Get mini-batch indices
                        batch_indices = indices[start_idx:start_idx + batch_size]
                        
                        # Get mini-batch tensors
                        batch_states = states_tensor[batch_indices]
                        batch_actions = actions_tensor[batch_indices]
                        batch_returns = returns_tensor[batch_indices]
                        batch_advantages = advantages_tensor[batch_indices]
                        batch_old_log_probs = old_log_probs_tensor[batch_indices]
                        
                        # Forward pass
                        action_probs = self.policy_network(batch_states)
                        values = self.value_network(batch_states).squeeze(-1)
                        
                        # Calculate log probabilities of actions
                        dist = torch.distributions.Categorical(action_probs)
                        log_probs = dist.log_prob(batch_actions)
                        entropy = dist.entropy().mean()
                        
                        # Calculate ratio of new and old policies
                        ratio = torch.exp(log_probs - batch_old_log_probs)
                        
                        # Calculate surrogate losses
                        surr1 = ratio * batch_advantages
                        surr2 = torch.clamp(ratio, 1.0 - self.config['epsilon'], 1.0 + self.config['epsilon']) * batch_advantages
                        policy_loss = -torch.min(surr1, surr2).mean()
                        
                        # Calculate value loss
                        value_loss = F.mse_loss(values, batch_returns)
                        
                        # Calculate total loss
                        loss = policy_loss + self.config['value_coef'] * value_loss - self.config['entropy_coef'] * entropy
                        
                        # Backward pass and optimize
                        self.optimizer.zero_grad()
                        loss.backward()
                        nn.utils.clip_grad_norm_(list(self.policy_network.parameters()) + list(self.value_network.parameters()), 
                                                self.config['max_grad_norm'])
                        self.optimizer.step()
                        
                        # Track losses
                        iteration_policy_loss += policy_loss.item()
                        iteration_value_loss += value_loss.item()
                        iteration_entropy += entropy.item()
                
                # Average losses over mini-batches and epochs
                n_updates = self.config['epochs'] * n_batches
                if n_updates > 0:
                    iteration_policy_loss /= n_updates
                    iteration_value_loss /= n_updates
                    iteration_entropy /= n_updates
                
                # Record metrics
                metrics['mean_reward'].append(episode_reward)
                metrics['policy_loss'].append(iteration_policy_loss)
                metrics['value_loss'].append(iteration_value_loss)
                metrics['entropy'].append(iteration_entropy)
                
                # Store training history
                self.training_history.append({
                    'iteration': iteration,
                    'mean_reward': episode_reward,
                    'policy_loss': iteration_policy_loss,
                    'value_loss': iteration_value_loss,
                    'entropy': iteration_entropy
                })
                
                if (iteration + 1) % 10 == 0 or iteration == n_iterations - 1:
                    logger.info(f"Iteration {iteration+1}/{n_iterations}: "
                              f"Reward = {episode_reward:.4f}, "
                              f"Policy Loss = {iteration_policy_loss:.4f}, "
                              f"Value Loss = {iteration_value_loss:.4f}")
            
            training_time = time.time() - start_time
            self.is_trained = True
            logger.success(f"PPO training completed in {training_time:.2f} seconds with final reward: {metrics['mean_reward'][-1]:.4f}")
            
            return {
                'success': True,
                'final_mean_reward': metrics['mean_reward'][-1],
                'final_policy_loss': metrics['policy_loss'][-1],
                'final_value_loss': metrics['value_loss'][-1],
                'training_time': training_time,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error during PPO training: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_action(self, state: np.ndarray) -> Tuple[int, Dict[str, float]]:
        """Get action from policy network for a given state.
        
        Args:
            state: Current state vector
            
        Returns:
            Tuple of (action, action_probs)
        """
        if not self.is_trained:
            logger.warning("Model not trained yet. Call train() first.")
            return 0, {'hold': 1.0, 'buy': 0.0, 'sell': 0.0}
        try:
        
            
            # Convert state to tensor and ensure correct shape
            if len(state.shape) == 1:
                # Add batch dimension if single state
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            else:
                state_tensor = torch.FloatTensor(state).to(self.device)
            
            # Set model to evaluation mode
            self.policy_network.eval()
            
            # Forward pass through policy network
            with torch.no_grad():
                action_probs_tensor = self.policy_network(state_tensor)
                
                # Convert to numpy for easier handling
                action_probs_np = action_probs_tensor.cpu().numpy()[0]
                
                # Get action with highest probability (greedy) or sample from distribution
                if np.random.random() > 0.05:  # 5% exploration during inference
                    action = int(np.argmax(action_probs_np))
                else:
                    # Exploration: sample from the probability distribution
                    action = np.random.choice(len(action_probs_np), p=action_probs_np)
            
            # Create action probabilities dictionary
            action_names = ['hold', 'buy', 'sell']
            action_probs = {name: float(prob) for name, prob in zip(action_names, action_probs_np)}
            
            logger.debug(f"Selected action: {action_names[action]} with probs: {action_probs}")
            return action, action_probs
            
        except Exception as e:
            logger.error(f"Error during action inference: {e}")
            # Fallback to simple heuristic if neural network fails
            
            # Extract some features from the state (assuming standard order from preprocess_state)
            momentum = state[2] if len(state) > 2 else 0  # momentum_5
            rsi = state[11] if len(state) > 11 else 50  # rsi_14
            macd = state[12] if len(state) > 12 else 0  # macd
            
            # Calculate action probabilities
            buy_prob = 0.0
            sell_prob = 0.0
            hold_prob = 0.0
            
            # Simple heuristic rules
            if momentum > 0.01 and rsi < 70 and macd > 0:
                buy_prob = 0.7
                sell_prob = 0.1
                hold_prob = 0.2
            elif momentum < -0.01 and rsi > 30 and macd < 0:
                buy_prob = 0.1
                sell_prob = 0.7
                hold_prob = 0.2
            else:
                buy_prob = 0.2
                sell_prob = 0.2
                hold_prob = 0.6
            
            # Normalize probabilities
            total_prob = buy_prob + sell_prob + hold_prob
            buy_prob /= total_prob
            sell_prob /= total_prob
            hold_prob /= total_prob
            
            action_probs = {'hold': hold_prob, 'buy': buy_prob, 'sell': sell_prob}
            
            # Select action based on probabilities
            actions = [0, 1, 2]  # 0=hold, 1=buy, 2=sell
            probs = [hold_prob, buy_prob, sell_prob]
            action = np.random.choice(actions, p=probs)
            
            logger.warning("Using fallback heuristic for action selection")
            return action, action_probs
    
    def evaluate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate the trained agent on historical data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_trained:
            logger.warning("Model not trained yet. Call train() first.")
            return {'success': False, 'error': 'Model not trained'}
        
        # Preprocess data into state representation
        states = self.preprocess_state(df)
        
        if len(states) == 0:
            logger.warning("No valid states for evaluation")
            return {'success': False, 'error': 'No valid states'}
        
        # Calculate price changes for reward calculation
        price_changes = df['close'].pct_change().fillna(0).values
        
        # Simulation variables
        portfolio_value = 1000.0  # Initial portfolio value
        position = 0  # 0=no position, 1=long, -1=short
        entry_price = 0.0
        trades = []
        portfolio_values = [portfolio_value]
        positions = []
        
        # Simulate trading
        for i in range(1, len(states)):
            state = states[i]
            price_change = price_changes[i]
            current_price = df['close'].iloc[i]
            
            # Get action from policy
            action, action_probs = self.get_action(state)
            
            # Execute action
            if action == 1:  # buy
                if position <= 0:  # if no position or short
                    if position == -1:  # close short position
                        profit = entry_price - current_price
                        portfolio_value *= (1 + profit / entry_price)
                        trades.append({'type': 'close_short', 'price': current_price, 'profit': profit})
                    
                    # Open long position
                    position = 1
                    entry_price = current_price
                    trades.append({'type': 'buy', 'price': current_price})
            
            elif action == 2:  # sell
                if position >= 0:  # if no position or long
                    if position == 1:  # close long position
                        profit = current_price - entry_price
                        portfolio_value *= (1 + profit / entry_price)
                        trades.append({'type': 'close_long', 'price': current_price, 'profit': profit})
                    
                    # Open short position
                    position = -1
                    entry_price = current_price
                    trades.append({'type': 'sell', 'price': current_price})
            
            # Update portfolio value based on position
            if position == 1:  # long position
                portfolio_value *= (1 + price_change)
            elif position == -1:  # short position
                portfolio_value *= (1 - price_change)
            
            portfolio_values.append(portfolio_value)
            positions.append(position)
        
        # Calculate metrics
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Calculate drawdown
        peak = portfolio_values[0]
        drawdowns = []
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            drawdowns.append(drawdown)
        max_drawdown = max(drawdowns)
        
        # Calculate win rate
        profits = [trade['profit'] for trade in trades if 'profit' in trade]
        win_rate = sum(1 for p in profits if p > 0) / len(profits) if profits else 0
        
        metrics = {
            'final_portfolio_value': portfolio_values[-1],
            'total_return': (portfolio_values[-1] / portfolio_values[0] - 1) * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'total_trades': len(profits)
        }
        
        logger.info(f"Evaluation complete: Return={metrics['total_return']:.2f}%, "
                   f"Sharpe={metrics['sharpe_ratio']:.2f}, "
                   f"MaxDD={metrics['max_drawdown']:.2f}%, "
                   f"WinRate={metrics['win_rate']:.2f}%")
        
        return {
            'success': True,
            'metrics': metrics,
            'portfolio_values': portfolio_values,
            'positions': positions,
            'trades': trades
        }
    
    def save_model(self, path: str) -> bool:
        """Save the trained model to disk.
        
        Args:
            path: Path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_trained:
            logger.warning("Model not trained yet. Call train() first.")
            return False
        try:
        
            import json
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save model state dictionaries and configuration
            model_data = {
                'policy_network': self.policy_network.state_dict(),
                'value_network': self.value_network.state_dict(),
                'config': self.config,
                'training_history': self.training_history,
                'metadata': {
                    'timestamp': time.time(),
                    'version': '1.0',
                    'framework': 'pytorch'
                }
            }
            
            torch.save(model_data, path)
            
            # Save a human-readable summary alongside the model
            summary_path = f"{os.path.splitext(path)[0]}_summary.json"
            with open(summary_path, 'w') as f:
                summary = {
                    'config': self.config,
                    'training_history': self.training_history[-1] if self.training_history else None,
                    'metadata': model_data['metadata']
                }
                json.dump(summary, f, indent=2)
            
            logger.success(f"Model saved to {path} with summary at {summary_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self, path: str) -> bool:
        """Load a trained model from disk.
        
        Args:
            path: Path to load the model from
            
        Returns:
            True if successful, False otherwise
        """
            
        try:
            if not os.path.exists(path):
                logger.error(f"Model file not found: {path}")
                return False
                
            # Load model state dictionaries and configuration
            model_data = torch.load(path, map_location=torch.device('cpu'))
            
            # Extract configuration and state dimensions
            self.config = model_data['config']
            
            # Rebuild networks with the correct dimensions
            # We need to infer state_dim and action_dim from the loaded model
            policy_state_dict = model_data['policy_network']
            
            # Get dimensions from the first layer weights
            first_layer_key = [k for k in policy_state_dict.keys() if 'fc1.weight' in k][0]
            state_dim = policy_state_dict[first_layer_key].shape[1]
            
            # Get dimensions from the last layer weights
            last_layer_key = [k for k in policy_state_dict.keys() if 'fc3.weight' in k][0]
            action_dim = policy_state_dict[last_layer_key].shape[0]
            
            # Build networks with the correct dimensions
            self.build_networks(state_dim=state_dim, action_dim=action_dim)
            
            # Load state dictionaries
            self.policy_network.load_state_dict(model_data['policy_network'])
            self.value_network.load_state_dict(model_data['value_network'])
            
            # Load training history if available
            if 'training_history' in model_data:
                self.training_history = model_data['training_history']
            
            self.is_trained = True
            
            # Log model metadata if available
            if 'metadata' in model_data:
                version = model_data['metadata'].get('version', 'unknown')
                framework = model_data['metadata'].get('framework', 'unknown')
                logger.info(f"Loaded model version {version} (framework: {framework})")
            
            logger.success(f"Model successfully loaded from {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
