"""
from pathlib import Path
Multi-Timeframe Analysis with Reinforcement Learning
Integrates multiple timeframes for advanced trading decisions
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import os
import json
import asyncio
import matplotlib.pyplot as plt
import seaborn as sns

import torch

from trading_bot.ml.rl_environment import TradingEnvironment
from trading_bot.ml.rl_agent import PPOAgent
from trading_bot.analysis.technical_indicators import calculate_indicators

logger = logging.getLogger(__name__)


class MultiTimeframeRL:
    """
    Multi-timeframe analysis with reinforcement learning
    
    Features:
    - Multiple timeframe integration
    - Reinforcement learning for optimal decisions
    - Adaptive position sizing
    - Real-time trading integration
    - Continuous learning
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Timeframe configuration
            self.timeframes = self.config.get('timeframes', ['1m', '5m', '15m', '1h', '4h', '1d'])
            self.primary_timeframe = self.config.get('primary_timeframe', '5m')
        
            # Feature configuration
            self.features = self.config.get('features', [
                'close', 'open', 'high', 'low', 'volume',
                'rsi', 'macd', 'bb_upper', 'bb_lower', 'atr'
            ])
        
            # RL configuration
            self.env_config = self.config.get('environment', {})
            self.agent_config = self.config.get('agent', {})
        
            # Trading configuration
            self.max_position_size = self.config.get('max_position_size', 1.0)
            self.risk_per_trade = self.config.get('risk_per_trade', 0.02)  # 2% risk per trade
        
            # Initialize environment and agent
            self.env = TradingEnvironment(self.env_config)
            self.agent = None  # Will be initialized when data is available
        
            # Data storage
            self.data = {}
            self.latest_data = {}
            self.predictions = []
        
            # Model path
            self.model_dir = self.config.get('model_dir', 'models')
            os.makedirs(self.model_dir, exist_ok=True)
        
            logger.info("Multi-Timeframe RL initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def load_data(self, symbols: List[str], start_date: str, end_date: str = None):
        """
        Load historical data for training
        
        Args:
            symbols: List of symbols to load data for
            start_date: Start date for data
            end_date: End date for data (default: now)
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
        
            logger.info(f"Loading data for {len(symbols)} symbols from {start_date} to {end_date}")
        
            # Load data for each symbol and timeframe
            for symbol in symbols:
                self.data[symbol] = {}
            
                for timeframe in self.timeframes:
                    # Load data (this would typically come from a data provider)
                    df = await self._load_symbol_data(symbol, timeframe, start_date, end_date)
                
                    if df is not None and not df.empty:
                        # Calculate technical indicators
                        df = calculate_indicators(df)
                    
                        # Store data
                        self.data[symbol][timeframe] = df
                        logger.info(f"Loaded {len(df)} data points for {symbol} {timeframe}")
                    else:
                        logger.warning(f"No data loaded for {symbol} {timeframe}")
        
            # Initialize agent if not already initialized
            if self.agent is None and symbols:
                symbol = symbols[0]
                if symbol in self.data and all(tf in self.data[symbol] for tf in self.timeframes):
                    self.env.set_data(self.data[symbol])
                    self.agent = PPOAgent(self.env, self.agent_config)
                    logger.info("Agent initialized")
        except Exception as e:
            logger.error(f"Error in load_data: {e}")
            raise
    
    async def _load_symbol_data(self, symbol: str, timeframe: str, 
                              start_date: str, end_date: str) -> pd.DataFrame:
        """
        Load data for a symbol and timeframe
        
        This is a placeholder that would be replaced with actual data loading
        from a broker API or database in a real implementation.
from typing import Set
import pathlib
        """
        # Simulate data loading
        # In a real implementation, this would fetch data from an API or database
        
        # Parse dates
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
        
            # Generate date range
            date_range = pd.date_range(start=start, end=end, freq=timeframe)
        
            # Create simulated data
            df = pd.DataFrame(index=date_range)
        
            # Add price data with realistic patterns
            base_price = 100.0
            price_series = [base_price]
        
            for i in range(1, len(date_range)):
                # Random walk with drift and volatility based on timeframe
                if timeframe == '1m':
                    volatility = 0.0005
                    drift = 0.0001
                elif timeframe == '5m':
                    volatility = 0.001
                    drift = 0.0002
                elif timeframe == '15m':
                    volatility = 0.002
                    drift = 0.0003
                elif timeframe == '1h':
                    volatility = 0.004
                    drift = 0.0005
                elif timeframe == '4h':
                    volatility = 0.008
                    drift = 0.001
                else:  # 1d
                    volatility = 0.015
                    drift = 0.002
            
                # Calculate price change
                change = np.random.normal(drift, volatility) * price_series[-1]
                new_price = price_series[-1] + change
                price_series.append(new_price)
        
            # Create OHLCV data
            df['close'] = price_series
            df['open'] = df['close'].shift(1).fillna(df['close'][0])
            df['high'] = df['close'] * (1 + np.random.uniform(0, 0.003, len(df)))
            df['low'] = df['close'] * (1 - np.random.uniform(0, 0.003, len(df)))
            df['volume'] = np.random.lognormal(10, 1, len(df))
        
            return df
        except Exception as e:
            logger.error(f"Error in _load_symbol_data: {e}")
            raise
    
    async def train(self, symbol: str, num_episodes: int = 100, 
                  save_path: Optional[str] = None):
        """
        Train the agent on historical data
        
        Args:
            symbol: Symbol to train on
            num_episodes: Number of episodes to train
            save_path: Path to save model
        """
        try:
            if symbol not in self.data:
                logger.error(f"No data available for {symbol}")
                return
        
            if not all(tf in self.data[symbol] for tf in self.timeframes):
                logger.error(f"Missing timeframe data for {symbol}")
                return
        
            logger.info(f"Training agent for {symbol} with {num_episodes} episodes")
        
            # Set data for environment
            self.env.set_data(self.data[symbol])
        
            # Create agent if not already initialized
            if self.agent is None:
                self.agent = PPOAgent(self.env, self.agent_config)
        
            # Train agent
            if save_path is None:
                save_path = os.path.join(self.model_dir, f"{symbol}_model")
        
            self.agent.train(
                num_episodes=num_episodes,
                update_frequency=self.agent_config.get('update_frequency', 2048),
                eval_frequency=self.agent_config.get('eval_frequency', 10),
                save_path=save_path
            )
        
            logger.info(f"Training completed, model saved to {save_path}")
        
            # Evaluate agent
            eval_reward = self.agent.evaluate(10)
            logger.info(f"Final evaluation reward: {eval_reward:.2f}")
        
            # Plot training metrics
            self._plot_training_metrics(symbol)
        except Exception as e:
            logger.error(f"Error in train: {e}")
            raise
    
    def _plot_training_metrics(self, symbol: str):
        """Plot training metrics"""
        try:
            if self.agent is None:
                return
        
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
            # Plot episode rewards
            ax1.plot(self.agent.episode_rewards)
            ax1.set_title(f'Episode Rewards for {symbol}')
            ax1.set_xlabel('Episode')
            ax1.set_ylabel('Reward')
            ax1.grid(True, alpha=0.3)
        
            # Plot losses
            if self.agent.value_losses and self.agent.policy_losses:
                ax2.plot(self.agent.value_losses, label='Value Loss')
                ax2.plot(self.agent.policy_losses, label='Policy Loss')
                ax2.set_title('Training Losses')
                ax2.set_xlabel('Update Step')
                ax2.set_ylabel('Loss')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
        
            plt.tight_layout()
        
            # Save plot
            plot_path = os.path.join(self.model_dir, f"{symbol}_training_metrics.png")
            plt.savefig(plot_path)
            plt.close()
        
            logger.info(f"Training metrics plot saved to {plot_path}")
        except Exception as e:
            logger.error(f"Error in _plot_training_metrics: {e}")
            raise
    
    async def update_data(self, symbol: str, new_data: Dict[str, pd.DataFrame]):
        """
        Update data with new market data
        
        Args:
            symbol: Symbol to update data for
            new_data: Dictionary of timeframe to DataFrame with new data
        """
        try:
            if symbol not in self.data:
                self.data[symbol] = {}
        
            # Update data for each timeframe
            for timeframe, df in new_data.items():
                if timeframe in self.timeframes:
                    if timeframe not in self.data[symbol]:
                        self.data[symbol][timeframe] = df
                    else:
                        # Append new data
                        self.data[symbol][timeframe] = pd.concat([
                            self.data[symbol][timeframe],
                            df
                        ]).drop_duplicates()
                
                    # Store latest data
                    self.latest_data[symbol] = {
                        timeframe: df.iloc[-1].to_dict() for timeframe, df in self.data[symbol].items()
                    }
        
            logger.debug(f"Updated data for {symbol}")
        except Exception as e:
            logger.error(f"Error in update_data: {e}")
            raise
    
    def predict(self, symbol: str, state: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Generate trading prediction using the trained agent
        
        Args:
            symbol: Symbol to predict for
            state: Current market state (if None, use latest data)
            
        Returns:
            Prediction with position size and confidence
        """
        try:
            if self.agent is None:
                logger.error("Agent not initialized")
                return {'position': 0, 'confidence': 0}
        
            # Use provided state or latest data
            if state is None:
                if symbol not in self.latest_data:
                    logger.error(f"No latest data for {symbol}")
                    return {'position': 0, 'confidence': 0}
                state_data = self.latest_data[symbol]
            else:
                state_data = state
        
            # Prepare state for agent
            env_state = self._prepare_state(state_data)
        
            # Get prediction from agent
            action, _, value = self.agent.select_action(env_state, deterministic=True)
        
            # Scale action to position size
            position = float(action[0]) * self.max_position_size
        
            # Calculate confidence based on value
            confidence = float(min(1.0, max(0.0, (value[0] + 1) / 2)))
        
            # Create prediction
            prediction = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'position': position,
                'confidence': confidence,
                'value': float(value[0]),
                'timeframes': list(state_data.keys())
            }
        
            # Store prediction
            self.predictions.append(prediction)
        
            return prediction
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise
    
    def _prepare_state(self, state_data: Dict[str, Dict[str, float]]) -> np.ndarray:
        """
        Prepare state data for agent
        
        Args:
            state_data: Dictionary of timeframe to market data
            
        Returns:
            State array for agent
        """
        # Initialize state array
        try:
            num_timeframes = len(self.timeframes)
            num_features = len(self.features)
            window_size = self.env.window_size
        
            state = np.zeros((num_timeframes, num_features, window_size), dtype=np.float32)
        
            # Fill state with available data
            for i, timeframe in enumerate(self.timeframes):
                if timeframe in state_data:
                    # Extract features
                    for j, feature in enumerate(self.features):
                        if feature in state_data[timeframe]:
                            # In a real implementation, this would use historical data
                            # Here we just fill the last position with the current value
                            state[i, j, -1] = state_data[timeframe].get(feature, 0.0)
        
            return state
        except Exception as e:
            logger.error(f"Error in _prepare_state: {e}")
            raise
    
    def get_position_size(self, symbol: str, account_size: float, 
                        risk_level: str = 'normal') -> Dict[str, Any]:
        """
        Calculate optimal position size based on prediction and risk management
        
        Args:
            symbol: Symbol to calculate position for
            account_size: Account size in base currency
            risk_level: Risk level (low, normal, high)
            
        Returns:
            Dictionary with position size and risk metrics
        """
        # Get latest prediction
        try:
            prediction = next((p for p in reversed(self.predictions) if p['symbol'] == symbol), None)
        
            if prediction is None:
                logger.warning(f"No prediction available for {symbol}")
                return {'position_size': 0, 'risk_amount': 0}
        
            # Adjust risk per trade based on risk level
            risk_multiplier = {
                'low': 0.5,
                'normal': 1.0,
                'high': 1.5
            }.get(risk_level, 1.0)
        
            adjusted_risk = self.risk_per_trade * risk_multiplier
        
            # Calculate risk amount
            risk_amount = account_size * adjusted_risk
        
            # Scale position size by confidence
            confidence = prediction['confidence']
            position_direction = np.sign(prediction['position'])
        
            # Calculate position size
            if position_direction == 0:
                position_size = 0
            else:
                # Base position size on risk amount
                position_size = risk_amount * confidence * position_direction
        
            return {
                'symbol': symbol,
                'position_size': position_size,
                'direction': 'long' if position_direction > 0 else 'short' if position_direction < 0 else 'neutral',
                'confidence': confidence,
                'risk_amount': risk_amount,
                'risk_level': risk_level,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error in get_position_size: {e}")
            raise
    
    def save_model(self, symbol: str, path: Optional[str] = None):
        """
        Save model to disk
        
        Args:
            symbol: Symbol identifier
            path: Path to save model
        """
        try:
            if self.agent is None:
                logger.error("Agent not initialized")
                return
        
            if path is None:
                path = os.path.join(self.model_dir, f"{symbol}_model")
        
            self.agent.save_model(path)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error in save_model: {e}")
            raise
    
    def load_model(self, symbol: str, path: Optional[str] = None):
        """
        Load model from disk
        
        Args:
            symbol: Symbol identifier
            path: Path to load model from
        """
        try:
            if path is None:
                path = os.path.join(self.model_dir, f"{symbol}_model")
        
            if not os.path.exists(path):
                logger.error(f"Model not found at {path}")
                return False
        
            # Initialize environment and agent if needed
            if self.env is None:
                self.env = TradingEnvironment(self.env_config)
        
            if self.agent is None:
                self.agent = PPOAgent(self.env, self.agent_config)
        
            # Load model
            self.agent.load_model(path)
            logger.info(f"Model loaded from {path}")
        
            return True
        except Exception as e:
            logger.error(f"Error in load_model: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the agent
        
        Returns:
            Dictionary of performance metrics
        """
        try:
            if self.agent is None or not self.agent.episode_rewards:
                return {}
        
            # Calculate metrics
            rewards = np.array(self.agent.episode_rewards)
        
            metrics = {
                'mean_reward': float(np.mean(rewards)),
                'median_reward': float(np.median(rewards)),
                'min_reward': float(np.min(rewards)),
                'max_reward': float(np.max(rewards)),
                'std_reward': float(np.std(rewards)),
                'last_reward': float(rewards[-1]),
                'total_episodes': len(rewards),
                'improvement': float((rewards[-10:].mean() / rewards[:10].mean()) - 1) if len(rewards) >= 20 else 0.0
            }
        
            return metrics
        except Exception as e:
            logger.error(f"Error in get_performance_metrics: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create multi-timeframe RL system
    mtf_rl = MultiTimeframeRL()
    
    # Run async example
    async def main():
        # Load data
        try:
            await mtf_rl.load_data(['BTCUSD'], '2022-01-01', '2022-12-31')
        
            # Train model
            await mtf_rl.train('BTCUSD', num_episodes=10)
        
            # Generate prediction
            prediction = mtf_rl.predict('BTCUSD')
            logger.info(f"Prediction: {prediction}")
        
            # Calculate position size
            position = mtf_rl.get_position_size('BTCUSD', 10000.0)
            logger.info(f"Position: {position}")
        
            # Get performance metrics
            metrics = mtf_rl.get_performance_metrics()
            logger.info(f"Metrics: {metrics}")
        except Exception as e:
            logger.error(f"Error in main: {e}")
            raise
    
    asyncio.run(main())
