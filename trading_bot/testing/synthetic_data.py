"""
Synthetic Market Data Generator
Generates realistic market data for testing and validation
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
import uuid
from enum import Enum
import json
import random

from trading_bot.schemas.market_data import TimeFrame, MarketTick, OHLCBar
from typing import Set
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types for synthetic data generation"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"


class SyntheticDataGenerator:
    """
    Generates synthetic market data for testing
    Features:
    - Realistic price movements
    - Multiple market regimes
    - Configurable volatility and trends
    - Multi-timeframe data
    - Order book simulation
    - Volume profile generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Default parameters
            self.price_mean = self.config.get('price_mean', 100.0)
            self.price_std = self.config.get('price_std', 1.0)
            self.volatility = self.config.get('volatility', 0.01)
            self.trend = self.config.get('trend', 0.0)
            self.mean_reversion = self.config.get('mean_reversion', 0.05)
            self.random_seed = self.config.get('random_seed')
        
            # Set random seed if provided
            if self.random_seed is not None:
                np.random.seed(self.random_seed)
                random.seed(self.random_seed)
        
            # Market regimes
            self.regime_duration = self.config.get('regime_duration', 1000)
            self.regime_transition_prob = self.config.get('regime_transition_prob', 0.001)
            self.current_regime = MarketRegime.RANGING
            self.regime_params = {
                MarketRegime.TRENDING_UP: {'trend': 0.0002, 'volatility': 0.001, 'mean_reversion': 0.01},
                MarketRegime.TRENDING_DOWN: {'trend': -0.0002, 'volatility': 0.001, 'mean_reversion': 0.01},
                MarketRegime.RANGING: {'trend': 0.0, 'volatility': 0.0005, 'mean_reversion': 0.1},
                MarketRegime.VOLATILE: {'trend': 0.0, 'volatility': 0.003, 'mean_reversion': 0.03},
                MarketRegime.BREAKOUT: {'trend': 0.0005, 'volatility': 0.002, 'mean_reversion': 0.0},
                MarketRegime.REVERSAL: {'trend': -0.0003, 'volatility': 0.002, 'mean_reversion': 0.05}
            }
        
            # Anomaly generation
            self.anomaly_prob = self.config.get('anomaly_prob', 0.01)
            self.gap_prob = self.config.get('gap_prob', 0.005)
            self.spike_prob = self.config.get('spike_prob', 0.002)
        
            # State variables
            self.last_price = self.price_mean
            self.last_timestamp = datetime.now()
            self.regime_start = 0
            self.tick_count = 0
            self.price_history = []
            self.volume_history = []
        
            logger.info("Synthetic data generator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_tick(self, timestamp: Optional[datetime] = None) -> MarketTick:
        """
        Generate a single market tick
        
        Args:
            timestamp: Optional timestamp for the tick, defaults to now
            
        Returns:
            A MarketTick object
        """
        try:
            if timestamp is None:
                timestamp = self.last_timestamp + timedelta(seconds=1)
        
            # Update regime if needed
            self._update_regime()
        
            # Get current regime parameters
            regime_params = self.regime_params[self.current_regime]
        
            # Generate price movement
            price = self._generate_price_movement(
                self.last_price,
                trend=regime_params['trend'],
                volatility=regime_params['volatility'],
                mean_reversion=regime_params['mean_reversion']
            )
        
            # Generate volume
            volume = self._generate_volume(price, self.last_price)
        
            # Generate direction
            direction = "buy" if price >= self.last_price else "sell"
        
            # Create tick
            tick = MarketTick(
                timestamp=timestamp,
                symbol="SYNTHETIC",
                price=price,
                volume=volume,
                direction=direction,
                bid=price - self.volatility,
                ask=price + self.volatility,
                source="synthetic"
            )
        
            # Update state
            self.last_price = price
            self.last_timestamp = timestamp
            self.price_history.append(price)
            self.volume_history.append(volume)
            self.tick_count += 1
        
            return tick
        except Exception as e:
            logger.error(f"Error in generate_tick: {e}")
            raise
    
    def generate_ticks(self, 
                     count: int, 
                     start_time: Optional[datetime] = None,
                     interval_seconds: float = 1.0) -> List[MarketTick]:
        """
        Generate multiple market ticks
        
        Args:
            count: Number of ticks to generate
            start_time: Starting timestamp, defaults to now
            interval_seconds: Seconds between ticks
            
        Returns:
            List of MarketTick objects
        """
        try:
            if start_time is None:
                start_time = datetime.now()
        
            ticks = []
            timestamp = start_time
        
            for _ in range(count):
                tick = self.generate_tick(timestamp)
                ticks.append(tick)
                timestamp += timedelta(seconds=interval_seconds)
        
            return ticks
        except Exception as e:
            logger.error(f"Error in generate_ticks: {e}")
            raise
    
    def generate_ohlc_bars(self,
                         count: int,
                         timeframe: TimeFrame,
                         start_time: Optional[datetime] = None) -> List[OHLCBar]:
        """
        Generate OHLC bars
        
        Args:
            count: Number of bars to generate
            timeframe: Bar timeframe
            start_time: Starting timestamp, defaults to now
            
        Returns:
            List of OHLCBar objects
        """
        try:
            if start_time is None:
                start_time = datetime.now()
        
            # Determine seconds per bar
            seconds_map = {
                TimeFrame.TICK: 1,
                TimeFrame.M1: 60,
                TimeFrame.M5: 300,
                TimeFrame.M15: 900,
                TimeFrame.M30: 1800,
                TimeFrame.H1: 3600,
                TimeFrame.H4: 14400,
                TimeFrame.D1: 86400,
                TimeFrame.W1: 604800,
                TimeFrame.MN1: 2592000
            }
            seconds_per_bar = seconds_map.get(timeframe, 60)
        
            # Generate enough ticks for the bars
            ticks_per_bar = max(10, int(seconds_per_bar / 5))  # At least 10 ticks per bar
            ticks = self.generate_ticks(
                count * ticks_per_bar,
                start_time,
                seconds_per_bar / ticks_per_bar
            )
        
            # Group ticks into bars
            bars = []
            for i in range(count):
                bar_ticks = ticks[i * ticks_per_bar:(i + 1) * ticks_per_bar]
                if not bar_ticks:
                    continue
                
                bar_time = bar_ticks[0].timestamp
                prices = [tick.price for tick in bar_ticks]
                volumes = [tick.volume for tick in bar_ticks]
            
                bar = OHLCBar(
                    timestamp=bar_time,
                    symbol="SYNTHETIC",
                    timeframe=timeframe,
                    open=prices[0],
                    high=max(prices),
                    low=min(prices),
                    close=prices[-1],
                    volume=sum(volumes),
                    tick_count=len(bar_ticks)
                )
            
                bars.append(bar)
        
            return bars
        except Exception as e:
            logger.error(f"Error in generate_ohlc_bars: {e}")
            raise
    
    def generate_market_data(self,
                           symbol: str = "SYNTHETIC",
                           days: int = 30,
                           timeframes: List[TimeFrame] = None) -> Dict[TimeFrame, pd.DataFrame]:
        """
        Generate comprehensive market data for multiple timeframes
        
        Args:
            symbol: Symbol name
            days: Number of days of data to generate
            timeframes: List of timeframes to generate, defaults to [M1, M5, H1, D1]
            
        Returns:
            Dict mapping timeframes to DataFrames of OHLC data
        """
        try:
            if timeframes is None:
                timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.H1, TimeFrame.D1]
        
            # Reset state for consistent results
            self.last_price = self.price_mean
            self.last_timestamp = datetime.now() - timedelta(days=days)
            self.regime_start = 0
            self.tick_count = 0
            self.price_history = []
            self.volume_history = []
        
            result = {}
        
            for tf in timeframes:
                # Calculate number of bars
                seconds_map = {
                    TimeFrame.M1: 60,
                    TimeFrame.M5: 300,
                    TimeFrame.M15: 900,
                    TimeFrame.M30: 1800,
                    TimeFrame.H1: 3600,
                    TimeFrame.H4: 14400,
                    TimeFrame.D1: 86400,
                    TimeFrame.W1: 604800,
                    TimeFrame.MN1: 2592000
                }
                seconds_per_bar = seconds_map.get(tf, 60)
                total_seconds = days * 86400
                bar_count = total_seconds // seconds_per_bar
            
                # Generate bars
                bars = self.generate_ohlc_bars(
                    count=bar_count,
                    timeframe=tf,
                    start_time=self.last_timestamp
                )
            
                # Convert to DataFrame
                df = pd.DataFrame([
                    {
                        'timestamp': bar.timestamp,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume
                    }
                    for bar in bars
                ])
            
                result[tf] = df
        
            return result
        except Exception as e:
            logger.error(f"Error in generate_market_data: {e}")
            raise
    
    def generate_order_book(self, 
                          current_price: float, 
                          depth: int = 10) -> Dict[str, List[Dict[str, float]]]:
        """
        Generate a synthetic order book
        
        Args:
            current_price: Current market price
            depth: Number of levels on each side
            
        Returns:
            Dict with 'bids' and 'asks' lists
        """
        # Generate bid levels
        try:
            bids = []
            for i in range(depth):
                price_delta = self.volatility * (1 + i * 0.5)
                price = current_price - price_delta
                volume = np.random.exponential(100) * (depth - i) / depth
                bids.append({
                    'price': price,
                    'volume': volume
                })
        
            # Generate ask levels
            asks = []
            for i in range(depth):
                price_delta = self.volatility * (1 + i * 0.5)
                price = current_price + price_delta
                volume = np.random.exponential(100) * (depth - i) / depth
                asks.append({
                    'price': price,
                    'volume': volume
                })
        
            return {
                'bids': bids,
                'asks': asks
            }
        except Exception as e:
            logger.error(f"Error in generate_order_book: {e}")
            raise
    
    def generate_order_flow(self, 
                          current_price: float,
                          num_trades: int = 100) -> List[Dict[str, Any]]:
        """
        Generate synthetic order flow data
        
        Args:
            current_price: Current market price
            num_trades: Number of trades to generate
            
        Returns:
            List of trade dictionaries
        """
        try:
            trades = []
        
            # Generate trades
            for _ in range(num_trades):
                # Determine direction
                is_buy = np.random.random() < 0.5
                direction = "buy" if is_buy else "sell"
            
                # Generate price with slight bias
                price_bias = 0.0001 if is_buy else -0.0001
                price = current_price + np.random.normal(price_bias, self.volatility / 2)
            
                # Generate volume with occasional large orders
                is_large = np.random.random() < 0.05
                volume_scale = 10 if is_large else 1
                volume = np.random.exponential(10 * volume_scale)
            
                # Generate trade
                trade = {
                    'timestamp': datetime.now(),
                    'price': price,
                    'volume': volume,
                    'direction': direction,
                    'is_large': is_large,
                    'aggressor': direction
                }
            
                trades.append(trade)
        
            return trades
        except Exception as e:
            logger.error(f"Error in generate_order_flow: {e}")
            raise
    
    def _generate_price_movement(self, 
                               last_price: float, 
                               trend: float = 0.0,
                               volatility: float = 0.01,
                               mean_reversion: float = 0.05) -> float:
        """Generate realistic price movement"""
        # Random component
        try:
            random_component = np.random.normal(0, volatility)
        
            # Trend component
            trend_component = trend
        
            # Mean reversion component
            reversion_component = mean_reversion * (self.price_mean - last_price) / self.price_mean
        
            # Combine components
            price_change = random_component + trend_component + reversion_component
        
            # Apply anomalies
            if np.random.random() < self.anomaly_prob:
                if np.random.random() < self.gap_prob:
                    # Price gap
                    gap_direction = 1 if np.random.random() < 0.5 else -1
                    price_change += gap_direction * volatility * 10
                elif np.random.random() < self.spike_prob:
                    # Price spike (will revert)
                    spike_direction = 1 if np.random.random() < 0.5 else -1
                    price_change += spike_direction * volatility * 15
        
            # Calculate new price
            new_price = max(0.01, last_price * (1 + price_change))
        
            return new_price
        except Exception as e:
            logger.error(f"Error in _generate_price_movement: {e}")
            raise
    
    def _generate_volume(self, current_price: float, last_price: float) -> float:
        """Generate realistic volume"""
        # Base volume
        try:
            base_volume = np.random.exponential(10)
        
            # Volume increases with price movement
            price_change = abs(current_price - last_price) / last_price
            volume_factor = 1 + 10 * price_change
        
            # Volume has time-of-day pattern
            hour = self.last_timestamp.hour
            time_factor = 1 + 0.5 * np.sin((hour - 9) * np.pi / 12)
        
            # Combine factors
            volume = base_volume * volume_factor * time_factor
        
            return volume
        except Exception as e:
            logger.error(f"Error in _generate_volume: {e}")
            raise
    
    def _update_regime(self):
        """Update market regime based on time and probability"""
        # Check if it's time for a regime change
        try:
            if self.tick_count - self.regime_start >= self.regime_duration:
                # Forced regime change
                self._change_regime()
            elif np.random.random() < self.regime_transition_prob:
                # Random regime change
                self._change_regime()
        except Exception as e:
            logger.error(f"Error in _update_regime: {e}")
            raise
    
    def _change_regime(self):
        """Change to a new market regime"""
        # Get all regimes except current
        try:
            regimes = list(MarketRegime)
            regimes.remove(self.current_regime)
        
            # Select new regime
            new_regime = np.random.choice(regimes)
        
            logger.info(f"Market regime changing from {self.current_regime.value} to {new_regime.value}")
        
            self.current_regime = new_regime
            self.regime_start = self.tick_count
        except Exception as e:
            logger.error(f"Error in _change_regime: {e}")
            raise


class MarketScenario:
    """
    Predefined market scenarios for testing specific conditions
    """
    
    @staticmethod
    def trending_up(days: int = 30, volatility: float = 0.01) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate a trending up market scenario"""
        try:
            generator = SyntheticDataGenerator({
                'trend': 0.0002,
                'volatility': volatility,
                'mean_reversion': 0.01
            })
            return generator.generate_market_data(days=days)
        except Exception as e:
            logger.error(f"Error in trending_up: {e}")
            raise
    
    @staticmethod
    def trending_down(days: int = 30, volatility: float = 0.01) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate a trending down market scenario"""
        try:
            generator = SyntheticDataGenerator({
                'trend': -0.0002,
                'volatility': volatility,
                'mean_reversion': 0.01
            })
            return generator.generate_market_data(days=days)
        except Exception as e:
            logger.error(f"Error in trending_down: {e}")
            raise
    
    @staticmethod
    def ranging(days: int = 30, volatility: float = 0.01) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate a ranging market scenario"""
        try:
            generator = SyntheticDataGenerator({
                'trend': 0.0,
                'volatility': volatility,
                'mean_reversion': 0.1
            })
            return generator.generate_market_data(days=days)
        except Exception as e:
            logger.error(f"Error in ranging: {e}")
            raise
    
    @staticmethod
    def volatile(days: int = 30, volatility: float = 0.03) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate a volatile market scenario"""
        try:
            generator = SyntheticDataGenerator({
                'trend': 0.0,
                'volatility': volatility,
                'mean_reversion': 0.03,
                'anomaly_prob': 0.05
            })
            return generator.generate_market_data(days=days)
        except Exception as e:
            logger.error(f"Error in volatile: {e}")
            raise
    
    @staticmethod
    def breakout(days: int = 30, pre_breakout_days: int = 20) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate a breakout market scenario"""
        # Generate ranging market first
        try:
            generator = SyntheticDataGenerator({
                'trend': 0.0,
                'volatility': 0.005,
                'mean_reversion': 0.1
            })
            ranging_data = generator.generate_market_data(days=pre_breakout_days)
        
            # Then generate breakout
            generator = SyntheticDataGenerator({
                'price_mean': generator.last_price,
                'trend': 0.001,
                'volatility': 0.02,
                'mean_reversion': 0.01,
                'gap_prob': 0.1
            })
            breakout_data = generator.generate_market_data(days=days-pre_breakout_days)
        
            # Combine data
            result = {}
            for tf in ranging_data.keys():
                result[tf] = pd.concat([ranging_data[tf], breakout_data[tf]])
        
            return result
        except Exception as e:
            logger.error(f"Error in breakout: {e}")
            raise
    
    @staticmethod
    def reversal(days: int = 30, pre_reversal_days: int = 20) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate a reversal market scenario"""
        # Generate trending market first
        try:
            generator = SyntheticDataGenerator({
                'trend': 0.0003,
                'volatility': 0.01,
                'mean_reversion': 0.01
            })
            trending_data = generator.generate_market_data(days=pre_reversal_days)
        
            # Then generate reversal
            generator = SyntheticDataGenerator({
                'price_mean': generator.price_mean * 0.8,  # Reverse to lower mean
                'price_std': generator.price_std,
                'trend': -0.0005,
                'volatility': 0.02,
                'mean_reversion': 0.05
            })
            reversal_data = generator.generate_market_data(days=days-pre_reversal_days)
        
            # Combine data
            result = {}
            for tf in trending_data.keys():
                result[tf] = pd.concat([trending_data[tf], reversal_data[tf]])
        
            return result
        except Exception as e:
            logger.error(f"Error in reversal: {e}")
            raise
