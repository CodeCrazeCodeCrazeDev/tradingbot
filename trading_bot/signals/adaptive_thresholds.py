"""
Adaptive Thresholds System
==========================

Dynamically adjusts signal thresholds based on market conditions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """Volatility regime classification"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class MarketRegime(Enum):
    """Overall market regime"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"


@dataclass
class ThresholdConfig:
    """Configuration for a threshold"""
    name: str
    base_value: float
    min_value: float
    max_value: float
    volatility_sensitivity: float = 1.0
    trend_sensitivity: float = 0.5


@dataclass
class AdaptedThreshold:
    """Result of threshold adaptation"""
    name: str
    base_value: float
    adapted_value: float
    volatility_regime: VolatilityRegime
    market_regime: MarketRegime
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class AdaptiveThresholds:
    """
    Adaptive threshold system that adjusts signal thresholds based on:
    - Current volatility regime
    - Market trend strength
    - Historical performance
    - Time of day
    
    Features:
    - Multiple threshold types (entry, exit, stop-loss, take-profit)
    - Regime-based adjustments
    - Performance feedback loop
    - Configurable sensitivity
    """
    
    # Regime multipliers
    VOLATILITY_MULTIPLIERS = {
        VolatilityRegime.VERY_LOW: 0.6,
        VolatilityRegime.LOW: 0.8,
        VolatilityRegime.MEDIUM: 1.0,
        VolatilityRegime.HIGH: 1.3,
        VolatilityRegime.EXTREME: 1.6
    }
    
    MARKET_MULTIPLIERS = {
        MarketRegime.TRENDING_UP: 0.9,
        MarketRegime.TRENDING_DOWN: 0.9,
        MarketRegime.RANGING: 1.1,
        MarketRegime.VOLATILE: 1.4,
        MarketRegime.QUIET: 0.7
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize adaptive thresholds.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
        
            # History tracking
            self.volatility_history: deque = deque(maxlen=500)
            self.returns_history: deque = deque(maxlen=500)
            self.threshold_history: Dict[str, deque] = {}
            self.performance_history: deque = deque(maxlen=100)
        
            # Current state
            self.current_volatility_regime = VolatilityRegime.MEDIUM
            self.current_market_regime = MarketRegime.RANGING
        
            # Default thresholds
            self.thresholds: Dict[str, ThresholdConfig] = {
                'entry_signal': ThresholdConfig(
                    name='entry_signal',
                    base_value=0.6,
                    min_value=0.3,
                    max_value=0.9,
                    volatility_sensitivity=1.0
                ),
                'exit_signal': ThresholdConfig(
                    name='exit_signal',
                    base_value=0.5,
                    min_value=0.2,
                    max_value=0.8,
                    volatility_sensitivity=0.8
                ),
                'stop_loss_atr': ThresholdConfig(
                    name='stop_loss_atr',
                    base_value=2.0,
                    min_value=1.0,
                    max_value=4.0,
                    volatility_sensitivity=1.2
                ),
                'take_profit_atr': ThresholdConfig(
                    name='take_profit_atr',
                    base_value=3.0,
                    min_value=1.5,
                    max_value=6.0,
                    volatility_sensitivity=1.0
                ),
                'position_size': ThresholdConfig(
                    name='position_size',
                    base_value=1.0,
                    min_value=0.25,
                    max_value=2.0,
                    volatility_sensitivity=1.5
                )
            }
        
            # Learning rate for performance feedback
            self.learning_rate = self.config.get('learning_rate', 0.1)
        
            logger.info("AdaptiveThresholds initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update_market_data(
        self,
        volatility: float,
        returns: Optional[float] = None,
        trend_strength: Optional[float] = None
    ):
        """
        Update with new market data.
        
        Args:
            volatility: Current volatility (e.g., ATR, std dev)
            returns: Recent returns
            trend_strength: Trend strength indicator (-1 to 1)
        """
        try:
            self.volatility_history.append(volatility)
        
            if returns is not None:
                self.returns_history.append(returns)
            
            # Update regimes
            self._update_volatility_regime()
        
            if trend_strength is not None:
                self._update_market_regime(trend_strength)
        except Exception as e:
            logger.error(f"Error in update_market_data: {e}")
            raise
            
    def _update_volatility_regime(self):
        """Update volatility regime based on history"""
        try:
            if len(self.volatility_history) < 20:
                return
            
            vol_array = np.array(list(self.volatility_history))
            current_vol = vol_array[-1]
        
            # Calculate percentiles
            percentiles = np.percentile(vol_array, [10, 30, 70, 90])
        
            if current_vol < percentiles[0]:
                self.current_volatility_regime = VolatilityRegime.VERY_LOW
            elif current_vol < percentiles[1]:
                self.current_volatility_regime = VolatilityRegime.LOW
            elif current_vol < percentiles[2]:
                self.current_volatility_regime = VolatilityRegime.MEDIUM
            elif current_vol < percentiles[3]:
                self.current_volatility_regime = VolatilityRegime.HIGH
            else:
                self.current_volatility_regime = VolatilityRegime.EXTREME
        except Exception as e:
            logger.error(f"Error in _update_volatility_regime: {e}")
            raise
            
    def _update_market_regime(self, trend_strength: float):
        """Update market regime based on trend strength"""
        try:
            if len(self.volatility_history) < 20:
                return
            
            vol_array = np.array(list(self.volatility_history))
            vol_percentile = np.percentile(vol_array, 75)
            current_vol = vol_array[-1]
        
            # High volatility overrides trend
            if current_vol > vol_percentile:
                self.current_market_regime = MarketRegime.VOLATILE
            elif abs(trend_strength) < 0.2:
                if current_vol < np.percentile(vol_array, 25):
                    self.current_market_regime = MarketRegime.QUIET
                else:
                    self.current_market_regime = MarketRegime.RANGING
            elif trend_strength > 0.2:
                self.current_market_regime = MarketRegime.TRENDING_UP
            else:
                self.current_market_regime = MarketRegime.TRENDING_DOWN
        except Exception as e:
            logger.error(f"Error in _update_market_regime: {e}")
            raise
            
    def get_threshold(
        self,
        name: str,
        volatility: Optional[float] = None,
        base_override: Optional[float] = None
    ) -> AdaptedThreshold:
        """
        Get adapted threshold value.
        
        Args:
            name: Threshold name
            volatility: Current volatility (optional, uses history if not provided)
            base_override: Override base value
            
        Returns:
            AdaptedThreshold with adapted value
        """
        try:
            if name not in self.thresholds:
                # Create default threshold
                self.thresholds[name] = ThresholdConfig(
                    name=name,
                    base_value=base_override or 0.5,
                    min_value=0.1,
                    max_value=1.0
                )
            
            config = self.thresholds[name]
            base_value = base_override or config.base_value
        
            # Update volatility if provided
            if volatility is not None:
                self.update_market_data(volatility)
            
            # Get multipliers
            vol_mult = self.VOLATILITY_MULTIPLIERS[self.current_volatility_regime]
            market_mult = self.MARKET_MULTIPLIERS[self.current_market_regime]
        
            # Apply sensitivity
            vol_adjustment = 1 + (vol_mult - 1) * config.volatility_sensitivity
            market_adjustment = 1 + (market_mult - 1) * config.trend_sensitivity
        
            # Calculate adapted value
            adapted_value = base_value * vol_adjustment * market_adjustment
        
            # Clamp to min/max
            adapted_value = max(config.min_value, min(config.max_value, adapted_value))
        
            # Calculate confidence based on data availability
            confidence = min(1.0, len(self.volatility_history) / 100)
        
            return AdaptedThreshold(
                name=name,
                base_value=base_value,
                adapted_value=adapted_value,
                volatility_regime=self.current_volatility_regime,
                market_regime=self.current_market_regime,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in get_threshold: {e}")
            raise
        
    def get_all_thresholds(self) -> Dict[str, AdaptedThreshold]:
        """Get all adapted thresholds"""
        return {name: self.get_threshold(name) for name in self.thresholds}
        
    def record_performance(self, threshold_name: str, outcome: float):
        """
        Record performance feedback for a threshold.
        
        Args:
            threshold_name: Name of threshold used
            outcome: Outcome (positive = good, negative = bad)
        """
        try:
            self.performance_history.append({
                'threshold': threshold_name,
                'outcome': outcome,
                'volatility_regime': self.current_volatility_regime,
                'market_regime': self.current_market_regime,
                'timestamp': datetime.now()
            })
        
            # Adjust threshold based on feedback
            if threshold_name in self.thresholds:
                config = self.thresholds[threshold_name]
            
                # Simple feedback adjustment
                if outcome > 0:
                    # Good outcome - threshold was appropriate
                    pass
                else:
                    # Bad outcome - adjust threshold
                    # If we're losing, be more conservative (higher threshold)
                    adjustment = self.learning_rate * abs(outcome)
                    config.base_value = min(
                        config.max_value,
                        config.base_value * (1 + adjustment)
                    )
        except Exception as e:
            logger.error(f"Error in record_performance: {e}")
            raise
                
    def get_optimal_thresholds_for_regime(
        self,
        volatility_regime: VolatilityRegime,
        market_regime: MarketRegime
    ) -> Dict[str, float]:
        """
        Get optimal thresholds for a specific regime combination.
        
        Args:
            volatility_regime: Target volatility regime
            market_regime: Target market regime
            
        Returns:
            Dictionary of optimal threshold values
        """
        # Temporarily set regimes
        try:
            original_vol = self.current_volatility_regime
            original_market = self.current_market_regime
        
            self.current_volatility_regime = volatility_regime
            self.current_market_regime = market_regime
        
            thresholds = {
                name: self.get_threshold(name).adapted_value
                for name in self.thresholds
            }
        
            # Restore original regimes
            self.current_volatility_regime = original_vol
            self.current_market_regime = original_market
        
            return thresholds
        except Exception as e:
            logger.error(f"Error in get_optimal_thresholds_for_regime: {e}")
            raise
        
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'volatility_regime': self.current_volatility_regime.value,
            'market_regime': self.current_market_regime.value,
            'volatility_history_length': len(self.volatility_history),
            'performance_history_length': len(self.performance_history),
            'thresholds': {
                name: {
                    'base': config.base_value,
                    'adapted': self.get_threshold(name).adapted_value
                }
                for name, config in self.thresholds.items()
            }
        }


def create_adaptive_thresholds(config: Optional[Dict] = None) -> AdaptiveThresholds:
    """Factory function"""
    return AdaptiveThresholds(config)


if __name__ == "__main__":
    # Demo
    thresholds = create_adaptive_thresholds()
    
    print("=== Adaptive Thresholds Demo ===\n")
    
    # Simulate market data
    import random
    for i in range(100):
        vol = random.uniform(0.01, 0.05)
        trend = random.uniform(-1, 1)
        thresholds.update_market_data(vol, trend_strength=trend)
        
    print(f"Current Volatility Regime: {thresholds.current_volatility_regime.value}")
    print(f"Current Market Regime: {thresholds.current_market_regime.value}")
    
    print("\nAdapted Thresholds:")
    for name, adapted in thresholds.get_all_thresholds().items():
        print(f"  {name}: {adapted.base_value:.3f} -> {adapted.adapted_value:.3f}")
        
    print("\nThresholds for High Volatility + Trending:")
    high_vol_thresholds = thresholds.get_optimal_thresholds_for_regime(
        VolatilityRegime.HIGH,
        MarketRegime.TRENDING_UP
    )
    for name, value in high_vol_thresholds.items():
        print(f"  {name}: {value:.3f}")
