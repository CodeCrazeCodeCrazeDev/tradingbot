import logging
"""
Institutional-grade trading strategies for market expansion.
Multi-asset class strategies with advanced execution.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum
from loguru import logger


class StrategyType(Enum):
    """Strategy types."""
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    STATISTICAL_ARBITRAGE = "stat_arb"
    PAIRS_TRADING = "pairs"
    MARKET_MAKING = "market_making"
    VOLATILITY_ARBITRAGE = "vol_arb"
    CROSS_ASSET = "cross_asset"


class MeanReversionStrategy:
    """Mean reversion strategy with Z-score."""
    
    def __init__(self, lookback: int = 20, entry_threshold: float = 2.0, 
                 exit_threshold: float = 0.5):
        """
        Initialize mean reversion strategy.
        
        Args:
            lookback: Lookback period for mean calculation
            entry_threshold: Z-score threshold for entry
            exit_threshold: Z-score threshold for exit
        """
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        
        logger.info(f"Mean reversion strategy initialized (lookback: {lookback})")
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate mean reversion signal."""
        # Calculate rolling mean and std
        rolling_mean = df['close'].rolling(self.lookback).mean()
        rolling_std = df['close'].rolling(self.lookback).std()
        
        # Calculate Z-score
        z_score = (df['close'] - rolling_mean) / rolling_std
        current_z = z_score.iloc[-1]
        
        # Generate signal
        if current_z < -self.entry_threshold:
            action = 'buy'
            confidence = min(abs(current_z) / 3.0, 1.0)
        elif current_z > self.entry_threshold:
            action = 'sell'
            confidence = min(abs(current_z) / 3.0, 1.0)
        elif abs(current_z) < self.exit_threshold:
            action = 'close'
            confidence = 0.8
        else:
            action = 'hold'
            confidence = 0.0
        
        return {
            'strategy': 'mean_reversion',
            'action': action,
            'confidence': confidence,
            'z_score': float(current_z),
            'mean': float(rolling_mean.iloc[-1]),
            'std': float(rolling_std.iloc[-1])
        }


class MomentumStrategy:
    """Multi-timeframe momentum strategy."""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 50):
        """
        Initialize momentum strategy.
        
        Args:
            fast_period: Fast moving average period
            slow_period: Slow moving average period
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        
        logger.info(f"Momentum strategy initialized (fast: {fast_period}, slow: {slow_period})")
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate momentum signal."""
        # Calculate moving averages
        fast_ma = df['close'].rolling(self.fast_period).mean()
        slow_ma = df['close'].rolling(self.slow_period).mean()
        
        # Calculate momentum
        momentum = (fast_ma - slow_ma) / slow_ma
        current_momentum = momentum.iloc[-1]
        
        # Rate of change
        roc = df['close'].pct_change(self.fast_period).iloc[-1]
        
        # Generate signal
        if current_momentum > 0.01 and roc > 0:
            action = 'buy'
            confidence = min(abs(current_momentum) * 10, 1.0)
        elif current_momentum < -0.01 and roc < 0:
            action = 'sell'
            confidence = min(abs(current_momentum) * 10, 1.0)
        else:
            action = 'hold'
            confidence = 0.0
        
        return {
            'strategy': 'momentum',
            'action': action,
            'confidence': confidence,
            'momentum': float(current_momentum),
            'roc': float(roc)
        }


class StatisticalArbitrageStrategy:
    """Statistical arbitrage using cointegration."""
    
    def __init__(self, lookback: int = 60):
        """
        Initialize statistical arbitrage strategy.
        
        Args:
            lookback: Lookback period for cointegration
        """
        self.lookback = lookback
        self.hedge_ratio = None
        
        logger.info(f"Statistical arbitrage strategy initialized")
    
    def calculate_hedge_ratio(self, asset1: pd.Series, asset2: pd.Series) -> float:
        """Calculate hedge ratio between two assets."""
        from scipy import stats

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(asset1, asset2)
        
        self.hedge_ratio = slope
        return slope
    
    def generate_signal(self, asset1_df: pd.DataFrame, asset2_df: pd.DataFrame) -> Dict:
        """Generate stat arb signal for pair."""
        asset1_price = asset1_df['close']
        asset2_price = asset2_df['close']
        
        # Calculate hedge ratio
        if self.hedge_ratio is None:
            self.hedge_ratio = self.calculate_hedge_ratio(
                asset1_price[-self.lookback:],
                asset2_price[-self.lookback:]
            )
        
        # Calculate spread
        spread = asset1_price - self.hedge_ratio * asset2_price
        
        # Z-score of spread
        spread_mean = spread[-self.lookback:].mean()
        spread_std = spread[-self.lookback:].std()
        z_score = (spread.iloc[-1] - spread_mean) / spread_std
        
        # Generate signal
        if z_score < -2.0:
            action = 'long_spread'  # Buy asset1, sell asset2
            confidence = min(abs(z_score) / 3.0, 1.0)
        elif z_score > 2.0:
            action = 'short_spread'  # Sell asset1, buy asset2
            confidence = min(abs(z_score) / 3.0, 1.0)
        elif abs(z_score) < 0.5:
            action = 'close'
            confidence = 0.8
        else:
            action = 'hold'
            confidence = 0.0
        
        return {
            'strategy': 'stat_arb',
            'action': action,
            'confidence': confidence,
            'z_score': float(z_score),
            'hedge_ratio': float(self.hedge_ratio),
            'spread': float(spread.iloc[-1])
        }


class VolatilityArbitrageStrategy:
    """Volatility arbitrage strategy."""
    
    def __init__(self, lookback: int = 20):
        """
        Initialize volatility arbitrage strategy.
        
        Args:
            lookback: Lookback period for volatility
        """
        self.lookback = lookback
        
        logger.info("Volatility arbitrage strategy initialized")
    
    def generate_signal(self, df: pd.DataFrame, implied_vol: Optional[float] = None) -> Dict:
        """Generate volatility arbitrage signal."""
        # Calculate historical volatility
        returns = df['close'].pct_change()
        hist_vol = returns.rolling(self.lookback).std() * np.sqrt(252)
        current_hist_vol = hist_vol.iloc[-1]
        
        # If implied volatility available, compare
        if implied_vol is not None:
            vol_spread = implied_vol - current_hist_vol
            
            # Trade the spread
            if vol_spread > 0.05:  # Implied > Historical
                action = 'sell_vol'  # Sell options
                confidence = min(abs(vol_spread) * 10, 1.0)
            elif vol_spread < -0.05:  # Historical > Implied
                action = 'buy_vol'  # Buy options
                confidence = min(abs(vol_spread) * 10, 1.0)
            else:
                action = 'hold'
                confidence = 0.0
            
            return {
                'strategy': 'vol_arb',
                'action': action,
                'confidence': confidence,
                'hist_vol': float(current_hist_vol),
                'implied_vol': float(implied_vol),
                'vol_spread': float(vol_spread)
            }
        else:
            # Trade based on volatility regime
            vol_ma = hist_vol.rolling(self.lookback).mean()
            vol_regime = 'high' if current_hist_vol > vol_ma.iloc[-1] else 'low'
            
            return {
                'strategy': 'vol_arb',
                'action': 'hold',
                'confidence': 0.0,
                'hist_vol': float(current_hist_vol),
                'vol_regime': vol_regime
            }


class CrossAssetStrategy:
    """Cross-asset correlation strategy."""
    
    def __init__(self, correlation_threshold: float = 0.7):
        """
        Initialize cross-asset strategy.
        
        Args:
            correlation_threshold: Correlation threshold for signals
        """
        self.correlation_threshold = correlation_threshold
        self.correlation_matrix = None
        
        logger.info("Cross-asset strategy initialized")
    
    def calculate_correlations(self, asset_returns: Dict[str, pd.Series]) -> pd.DataFrame:
        """Calculate correlation matrix."""
        df = pd.DataFrame(asset_returns)
        self.correlation_matrix = df.corr()
        return self.correlation_matrix
    
    def generate_signal(self, asset_returns: Dict[str, pd.Series], 
                       target_asset: str) -> Dict:
        """Generate signal based on cross-asset correlations."""
        # Calculate correlations
        if self.correlation_matrix is None:
            self.calculate_correlations(asset_returns)
        
        # Find highly correlated assets
        target_corr = self.correlation_matrix[target_asset]
        high_corr_assets = target_corr[
            (target_corr.abs() > self.correlation_threshold) & 
            (target_corr.index != target_asset)
        ]
        
        # Aggregate signals from correlated assets
        signals = []
        for asset in high_corr_assets.index:
            asset_return = asset_returns[asset].iloc[-1]
            correlation = high_corr_assets[asset]
            
            # Positive correlation: follow the trend
            # Negative correlation: counter-trend
            if correlation > 0:
                signals.append(asset_return)
            else:
                signals.append(-asset_return)
        
        if signals:
            avg_signal = np.mean(signals)
            
            if avg_signal > 0.001:
                action = 'buy'
                confidence = min(abs(avg_signal) * 100, 1.0)
            elif avg_signal < -0.001:
                action = 'sell'
                confidence = min(abs(avg_signal) * 100, 1.0)
            else:
                action = 'hold'
                confidence = 0.0
        else:
            action = 'hold'
            confidence = 0.0
        
        return {
            'strategy': 'cross_asset',
            'action': action,
            'confidence': confidence,
            'correlated_assets': list(high_corr_assets.index),
            'avg_signal': float(avg_signal) if signals else 0.0
        }


class StrategyEnsemble:
    """Ensemble of multiple strategies."""
    
    def __init__(self):
        """Initialize strategy ensemble."""
        self.strategies = {
            'mean_reversion': MeanReversionStrategy(),
            'momentum': MomentumStrategy(),
            'vol_arb': VolatilityArbitrageStrategy()
        }
        
        self.weights = {
            'mean_reversion': 0.33,
            'momentum': 0.33,
            'vol_arb': 0.34
        }
        
        logger.info(f"Strategy ensemble initialized with {len(self.strategies)} strategies")
    
    def generate_ensemble_signal(self, df: pd.DataFrame, **kwargs) -> Dict:
        """Generate ensemble signal from all strategies."""
        signals = {}
        
        # Generate signals from each strategy
        for name, strategy in self.strategies.items():
            try:
                signal = strategy.generate_signal(df, **kwargs)
                signals[name] = signal
            except Exception as e:
                logger.error(f"Error in {name} strategy: {e}")
                continue
        
        # Aggregate signals
        actions = []
        confidences = []
        
        for name, signal in signals.items():
            weight = self.weights[name]
            action = signal['action']
            confidence = signal['confidence']
            
            # Convert action to numeric
            if action == 'buy' or action == 'long_spread' or action == 'buy_vol':
                action_value = 1.0
            elif action == 'sell' or action == 'short_spread' or action == 'sell_vol':
                action_value = -1.0
            else:
                action_value = 0.0
            
            actions.append(action_value * confidence * weight)
            confidences.append(confidence * weight)
        
        # Aggregate
        final_action_value = sum(actions)
        final_confidence = sum(confidences)
        
        # Determine final action
        if final_action_value > 0.2:
            final_action = 'buy'
        elif final_action_value < -0.2:
            final_action = 'sell'
        else:
            final_action = 'hold'
        
        return {
            'strategy': 'ensemble',
            'action': final_action,
            'confidence': min(final_confidence, 1.0),
            'component_signals': signals,
            'action_value': float(final_action_value)
        }
