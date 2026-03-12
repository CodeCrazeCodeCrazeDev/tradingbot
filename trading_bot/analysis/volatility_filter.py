"""
VOLATILITY FILTER MODULE - P0 CRITICAL FIX
============================================================

Implements volatility filtering to adjust position sizes based on market volatility.

Features:
- ATR (Average True Range) calculation
- Volatility regime detection
- Dynamic position size adjustment
- Volatility alerts

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional

import numpy as np
from loguru import logger
import numpy


class VolatilityRegime(Enum):
    """Volatility regime classification."""
    LOW = auto()        # < 50% of average
    NORMAL = auto()     # 50-150% of average
    HIGH = auto()       # 150-200% of average
    EXTREME = auto()    # > 200% of average


@dataclass
class VolatilityMetrics:
    """Volatility metrics."""
    current_atr: float
    average_atr: float
    atr_multiplier: float
    volatility_regime: VolatilityRegime
    position_size_multiplier: float
    timestamp: datetime


class VolatilityFilter:
    """Filters trades based on volatility conditions."""
    
    def __init__(self, atr_period: int = 14, lookback_period: int = 100):
        """
        Initialize volatility filter.
        
        Args:
            atr_period: Period for ATR calculation (default 14)
            lookback_period: Number of candles to track (default 100)
        """
        try:
            self.atr_period = atr_period
            self.lookback_period = lookback_period
        
            self.highs = deque(maxlen=atr_period)
            self.lows = deque(maxlen=atr_period)
            self.closes = deque(maxlen=atr_period)
            self.atr_values = deque(maxlen=lookback_period)
            self.metrics_history = deque(maxlen=lookback_period)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, high: float, low: float, close: float):
        """
        Update with new candle data.
        
        Args:
            high: Candle high
            low: Candle low
            close: Candle close
        """
        try:
            self.highs.append(high)
            self.lows.append(low)
            self.closes.append(close)
        
            if len(self.closes) >= self.atr_period:
                atr = self._calculate_atr()
                self.atr_values.append(atr)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _calculate_atr(self) -> float:
        """Calculate Average True Range."""
        try:
            tr_values = []
        
            for i in range(len(self.closes)):
                if i == 0:
                    tr = self.highs[i] - self.lows[i]
                else:
                    tr = max(
                        self.highs[i] - self.lows[i],
                        abs(self.highs[i] - self.closes[i-1]),
                        abs(self.lows[i] - self.closes[i-1])
                    )
                tr_values.append(tr)
        
            return np.mean(tr_values[-self.atr_period:]) if tr_values else 0
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
    
    def get_current_atr(self) -> float:
        """Get current ATR."""
        try:
            if not self.atr_values:
                return 0
            return self.atr_values[-1]
        except Exception as e:
            logger.error(f"Error in get_current_atr: {e}")
            raise
    
    def get_average_atr(self) -> float:
        """Get average ATR."""
        try:
            if not self.atr_values:
                return 0
            return np.mean(list(self.atr_values))
        except Exception as e:
            logger.error(f"Error in get_average_atr: {e}")
            raise
    
    def get_volatility_regime(self) -> VolatilityRegime:
        """Determine current volatility regime."""
        try:
            if not self.atr_values:
                return VolatilityRegime.NORMAL
        
            current_atr = self.atr_values[-1]
            avg_atr = np.mean(list(self.atr_values))
        
            if avg_atr == 0:
                return VolatilityRegime.NORMAL
        
            multiplier = current_atr / avg_atr
        
            if multiplier < 0.5:
                return VolatilityRegime.LOW
            elif multiplier < 1.5:
                return VolatilityRegime.NORMAL
            elif multiplier < 2.0:
                return VolatilityRegime.HIGH
            else:
                return VolatilityRegime.EXTREME
        except Exception as e:
            logger.error(f"Error in get_volatility_regime: {e}")
            raise
    
    def get_position_size_multiplier(self) -> float:
        """
        Get position size multiplier based on volatility.
        
        Returns:
            1.5 for LOW volatility (can increase size)
            1.0 for NORMAL volatility
            0.75 for HIGH volatility
            0.5 for EXTREME volatility
        """
        try:
            regime = self.get_volatility_regime()
        
            multipliers = {
                VolatilityRegime.LOW: 1.5,
                VolatilityRegime.NORMAL: 1.0,
                VolatilityRegime.HIGH: 0.75,
                VolatilityRegime.EXTREME: 0.5
            }
        
            return multipliers.get(regime, 1.0)
        except Exception as e:
            logger.error(f"Error in get_position_size_multiplier: {e}")
            raise
    
    def is_volatility_acceptable(self, max_atr_multiplier: float = 2.0) -> bool:
        """
        Check if volatility is within acceptable range.
        
        Args:
            max_atr_multiplier: Maximum allowed ATR multiplier
            
        Returns:
            True if volatility acceptable, False otherwise
        """
        try:
            if not self.atr_values:
                return True
        
            current_atr = self.atr_values[-1]
            avg_atr = np.mean(list(self.atr_values))
        
            if avg_atr == 0:
                return True
        
            multiplier = current_atr / avg_atr
            return multiplier <= max_atr_multiplier
        except Exception as e:
            logger.error(f"Error in is_volatility_acceptable: {e}")
            raise
    
    def get_metrics(self) -> VolatilityMetrics:
        """Get current volatility metrics."""
        try:
            current_atr = self.get_current_atr()
            average_atr = self.get_average_atr()
        
            if average_atr == 0:
                atr_multiplier = 1.0
            else:
                atr_multiplier = current_atr / average_atr
        
            regime = self.get_volatility_regime()
            multiplier = self.get_position_size_multiplier()
        
            metrics = VolatilityMetrics(
                current_atr=current_atr,
                average_atr=average_atr,
                atr_multiplier=atr_multiplier,
                volatility_regime=regime,
                position_size_multiplier=multiplier,
                timestamp=datetime.now()
            )
        
            self.metrics_history.append(metrics)
            return metrics
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            raise
    
    def get_volatility_status(self) -> str:
        """Get human-readable volatility status."""
        try:
            metrics = self.get_metrics()
        
            regime_map = {
                VolatilityRegime.LOW: "🟢 LOW",
                VolatilityRegime.NORMAL: "🟢 NORMAL",
                VolatilityRegime.HIGH: "🟡 HIGH",
                VolatilityRegime.EXTREME: "🔴 EXTREME"
            }
        
            return f"""
    VOLATILITY STATUS
    {'=' * 50}
    Regime: {regime_map[metrics.volatility_regime]}
    Current ATR: {metrics.current_atr:.5f}
    Average ATR: {metrics.average_atr:.5f}
    Multiplier: {metrics.atr_multiplier:.2f}x
    Position Size Multiplier: {metrics.position_size_multiplier:.2f}x
    {'=' * 50}
    """
        except Exception as e:
            logger.error(f"Error in get_volatility_status: {e}")
            raise
    
    def get_history(self) -> List[VolatilityMetrics]:
        """Get volatility history."""
        return list(self.metrics_history)
    
    def reset(self):
        """Reset all data."""
        try:
            self.highs.clear()
            self.lows.clear()
            self.closes.clear()
            self.atr_values.clear()
            self.metrics_history.clear()
            logger.info("Volatility filter reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
