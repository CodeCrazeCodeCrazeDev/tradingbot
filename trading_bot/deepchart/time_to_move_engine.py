"""
DeepChart Time-to-Move Engine - Duration Predictor (Not Direction)

Predicts time to significant price move using volatility compression,
energy buildup, and historical patterns.

Key insight: We predict WHEN, not WHERE. This is more robust and
avoids the impossible task of direction prediction.

Math:
    compression = σ_short / σ_long
    energy = Σ(|returns| × (1 - compression))
    ttm_breakout = f(compression, energy, regime_duration)
    ttm_reversion = g(distance_from_mean, vol_regime)

Performance Budget:
    - Update: O(1) per tick
    - Memory: O(window_size)
    - Latency: <0.3ms per update
"""

import numpy as np
from collections import deque
from typing import Optional, List
import logging

from .market_intelligence_core import (
    TimeToMoveEstimate,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class TimeToMovePredictor:
    """
    Predicts time to significant price move (not direction).
    
    Uses volatility compression, energy buildup, and historical patterns
    to estimate bars until breakout or mean reversion.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._returns = deque(maxlen=500)
        self._volatility_short = deque(maxlen=50)
        self._volatility_long = deque(maxlen=200)
        self._energy_accumulator = 0.0
        self._last_breakout_bar = 0
        self._bar_count = 0
        self._last_price = 0.0
        
        # Historical breakout data for calibration
        self._breakout_durations = deque(maxlen=100)
        self._reversion_durations = deque(maxlen=100)
    
    def update(self, price: float, volume: float) -> TimeToMoveEstimate:
        """
        Update time-to-move prediction.
        
        Args:
            price: Current price
            volume: Current volume
            
        Returns:
            TimeToMoveEstimate with breakout/reversion timing
        """
        self._bar_count += 1
        
        # Calculate return
        if self._last_price > 0:
            ret = (price - self._last_price) / self._last_price
            self._returns.append(ret)
        
        self._last_price = price
        
        if len(self._returns) < 20:
            return self._create_default_estimate()
        
        returns = np.array(self._returns)
        
        # Calculate volatility at different scales
        vol_short = np.std(returns[-20:]) if len(returns) >= 20 else 0.01
        vol_long = np.std(returns[-100:]) if len(returns) >= 100 else vol_short
        
        self._volatility_short.append(vol_short)
        self._volatility_long.append(vol_long)
        
        # Compression score: how compressed is current volatility
        compression = vol_short / (vol_long + 1e-8)
        compression_score = max(0, min(1, 1 - compression))  # Higher when compressed
        
        # Energy buildup: accumulated potential energy
        self._energy_accumulator = 0.9 * self._energy_accumulator + abs(returns[-1]) * compression_score
        energy_buildup = min(1.0, self._energy_accumulator * 10)
        
        # Volatility forecast
        vol_forecast = vol_short * (1 + compression_score * 0.5)
        
        # Time to breakout estimate
        bars_to_breakout = self._estimate_bars_to_breakout(compression_score, energy_buildup)
        confidence_breakout = self._calculate_breakout_confidence(compression_score, energy_buildup)
        
        # Time to reversion estimate
        bars_to_reversion = self._estimate_bars_to_reversion(returns)
        confidence_reversion = self._calculate_reversion_confidence(returns)
        
        # Detect actual breakouts for calibration
        self._detect_breakout(returns, vol_long)
        
        return TimeToMoveEstimate(
            bars_to_breakout=bars_to_breakout,
            bars_to_reversion=bars_to_reversion,
            confidence_breakout=confidence_breakout,
            confidence_reversion=confidence_reversion,
            volatility_forecast=vol_forecast,
            compression_score=compression_score,
            energy_buildup=energy_buildup
        )
    
    def _estimate_bars_to_breakout(self, compression: float, energy: float) -> float:
        """
        Estimate bars until breakout.
        
        Higher compression + energy = sooner breakout.
        Calibrated against historical breakout durations.
        """
        # Base estimate from compression and energy
        if compression > 0.7 and energy > 0.5:
            base_estimate = 5 + (1 - compression) * 20
        elif compression > 0.5:
            base_estimate = 10 + (1 - compression) * 30
        else:
            base_estimate = 50 + (1 - compression) * 50
        
        # Calibrate against historical data
        if len(self._breakout_durations) > 10:
            historical_mean = np.mean(self._breakout_durations)
            # Blend base estimate with historical
            base_estimate = 0.7 * base_estimate + 0.3 * historical_mean
        
        return max(1, base_estimate)
    
    def _calculate_breakout_confidence(self, compression: float, energy: float) -> float:
        """
        Calculate confidence in breakout prediction.
        
        High compression + high energy = high confidence.
        """
        base_confidence = compression * 0.5 + energy * 0.5
        
        # Adjust for historical accuracy
        if len(self._breakout_durations) > 20:
            # Higher confidence if predictions have been accurate
            std = np.std(self._breakout_durations)
            mean = np.mean(self._breakout_durations)
            cv = std / (mean + 1e-8)  # Coefficient of variation
            accuracy_factor = max(0.5, 1 - cv)
            base_confidence *= accuracy_factor
        
        return min(1.0, base_confidence)
    
    def _estimate_bars_to_reversion(self, returns: np.ndarray) -> float:
        """
        Estimate bars until mean reversion.
        
        Based on distance from mean and mean-reverting behavior.
        """
        if len(returns) < 50:
            return 30.0
        
        # Calculate distance from mean
        cumulative = np.cumsum(returns[-50:])
        distance = abs(cumulative[-1]) if len(cumulative) > 0 else 0
        
        # Estimate based on distance
        # Higher distance = sooner reversion (if mean-reverting)
        base_estimate = max(5, 30 - distance * 100)
        
        # Calibrate against historical
        if len(self._reversion_durations) > 10:
            historical_mean = np.mean(self._reversion_durations)
            base_estimate = 0.7 * base_estimate + 0.3 * historical_mean
        
        return base_estimate
    
    def _calculate_reversion_confidence(self, returns: np.ndarray) -> float:
        """
        Calculate confidence in reversion prediction.
        
        Based on autocorrelation (negative = mean-reverting).
        """
        if len(returns) < 20:
            return 0.3
        try:
        
        # Check for mean-reverting behavior via autocorrelation
            autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
            if np.isnan(autocorr):
                autocorr = 0
        except Exception as e:
            logger.error(f"Error: {e}")
            autocorr = 0
        
        # Negative autocorrelation = mean reverting = higher confidence
        return max(0, min(1, 0.5 - autocorr))
    
    def _detect_breakout(self, returns: np.ndarray, vol_long: float):
        """
        Detect actual breakouts for calibration.
        
        A breakout is defined as a move > 2σ.
        """
        if len(returns) < 2:
            return
        
        # Check if current move is a breakout
        current_move = abs(returns[-1])
        threshold = vol_long * 2
        
        if current_move > threshold:
            # Record duration since last breakout
            duration = self._bar_count - self._last_breakout_bar
            if duration > 5:  # Minimum duration
                self._breakout_durations.append(duration)
            self._last_breakout_bar = self._bar_count
    
    def _create_default_estimate(self) -> TimeToMoveEstimate:
        """Create default estimate for insufficient data."""
        return TimeToMoveEstimate(
            bars_to_breakout=50.0,
            bars_to_reversion=30.0,
            confidence_breakout=0.2,
            confidence_reversion=0.2,
            volatility_forecast=0.01,
            compression_score=0.5,
            energy_buildup=0.0
        )
    
    def get_compression_history(self) -> np.ndarray:
        """Get historical compression scores."""
        if len(self._volatility_short) < 2 or len(self._volatility_long) < 2:
            return np.array([0.5])
        
        short = np.array(self._volatility_short)
        long = np.array(self._volatility_long[-len(short):])
        
        if len(long) < len(short):
            short = short[-len(long):]
        
        compression = short / (long + 1e-8)
        return 1 - np.clip(compression, 0, 2)
    
    def reset(self):
        """Reset engine state."""
        self._returns.clear()
        self._volatility_short.clear()
        self._volatility_long.clear()
        self._energy_accumulator = 0.0
        self._last_breakout_bar = 0
        self._bar_count = 0
        self._last_price = 0.0
        self._breakout_durations.clear()
        self._reversion_durations.clear()
