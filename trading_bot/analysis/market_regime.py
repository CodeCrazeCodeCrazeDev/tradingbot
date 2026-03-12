"""
MARKET REGIME DETECTOR - PHASE 3 CORE
============================================================

Detects market regime to adapt strategy accordingly.

Features:
- Trend detection
- Range detection
- Volatility detection
- Regime classification
- Adaptive strategy selection

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional

import numpy as np
import numpy

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification."""
    STRONG_UPTREND = auto()
    WEAK_UPTREND = auto()
    RANGE_BOUND = auto()
    WEAK_DOWNTREND = auto()
    STRONG_DOWNTREND = auto()
    HIGHLY_VOLATILE = auto()


@dataclass
class RegimeMetrics:
    """Market regime metrics."""
    regime: MarketRegime
    trend_strength: float  # 0-1
    volatility: float  # 0-1
    range_width: float
    support: float
    resistance: float
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class MarketRegimeDetector:
    """Detects market regime for adaptive trading."""
    
    def __init__(self, lookback_period: int = 50):
        """
        Initialize market regime detector.
        
        Args:
            lookback_period: Number of candles to analyze
        """
        try:
            self.lookback_period = lookback_period
        
            # Price data storage
            self.highs = deque(maxlen=lookback_period)
            self.lows = deque(maxlen=lookback_period)
            self.closes = deque(maxlen=lookback_period)
            self.volumes = deque(maxlen=lookback_period)
        
            # Regime history
            self.regime_history: List[RegimeMetrics] = []
        
            logger.info(f"Market regime detector initialized (lookback: {lookback_period})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, high: float, low: float, close: float, volume: float = 0):
        """Update with new candle data."""
        try:
            self.highs.append(high)
            self.lows.append(low)
            self.closes.append(close)
            self.volumes.append(volume)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def detect_regime(self) -> Optional[RegimeMetrics]:
        """
        Detect current market regime.
        
        Returns:
            RegimeMetrics with regime classification
        """
        try:
            if len(self.closes) < self.lookback_period:
                return None
        
            # Calculate metrics
            trend_strength = self._calculate_trend_strength()
            volatility = self._calculate_volatility()
            support, resistance = self._calculate_support_resistance()
            range_width = resistance - support
        
            # Classify regime
            regime = self._classify_regime(trend_strength, volatility)
        
            metrics = RegimeMetrics(
                regime=regime,
                trend_strength=trend_strength,
                volatility=volatility,
                range_width=range_width,
                support=support,
                resistance=resistance
            )
        
            self.regime_history.append(metrics)
        
            # Keep only last 100
            if len(self.regime_history) > 100:
                self.regime_history.pop(0)
        
            return metrics
        except Exception as e:
            logger.error(f"Error in detect_regime: {e}")
            raise
    
    def _calculate_trend_strength(self) -> float:
        """Calculate trend strength (0-1)."""
        try:
            closes = list(self.closes)
        
            if len(closes) < 2:
                return 0
        
            # Calculate simple trend
            recent_close = closes[-1]
            old_close = closes[0]
        
            # Calculate slope
            slope = (recent_close - old_close) / old_close
        
            # Calculate volatility of closes
            close_std = np.std(closes)
            close_mean = np.mean(closes)
        
            if close_mean == 0:
                return 0
        
            # Trend strength = abs(slope) / volatility
            trend_strength = abs(slope) / (close_std / close_mean + 0.01)
        
            return min(1.0, trend_strength)
        except Exception as e:
            logger.error(f"Error in _calculate_trend_strength: {e}")
            raise
    
    def _calculate_volatility(self) -> float:
        """Calculate volatility (0-1)."""
        try:
            closes = list(self.closes)
        
            if len(closes) < 2:
                return 0
        
            # Calculate ATR-like measure
            tr_values = []
            for i in range(1, len(closes)):
                tr = max(
                    self.highs[i] - self.lows[i],
                    abs(self.highs[i] - closes[i-1]),
                    abs(self.lows[i] - closes[i-1])
                )
                tr_values.append(tr)
        
            atr = np.mean(tr_values)
            avg_price = np.mean(closes)
        
            if avg_price == 0:
                return 0
        
            # Volatility as percent of average price
            volatility = (atr / avg_price) * 100
        
            # Normalize to 0-1
            return min(1.0, volatility / 2.0)  # Assume 2% is high volatility
        except Exception as e:
            logger.error(f"Error in _calculate_volatility: {e}")
            raise
    
    def _calculate_support_resistance(self) -> tuple:
        """Calculate support and resistance levels."""
        try:
            highs = list(self.highs)
            lows = list(self.lows)
        
            # Support = lowest low
            support = min(lows)
        
            # Resistance = highest high
            resistance = max(highs)
        
            return support, resistance
        except Exception as e:
            logger.error(f"Error in _calculate_support_resistance: {e}")
            raise
    
    def _classify_regime(self, trend_strength: float, volatility: float) -> MarketRegime:
        """Classify market regime."""
        # High volatility regime
        try:
            if volatility > 0.7:
                return MarketRegime.HIGHLY_VOLATILE
        
            # Trend regimes
            if trend_strength > 0.6:
                # Determine direction from recent close
                recent_close = self.closes[-1]
                old_close = self.closes[0]
            
                if recent_close > old_close:
                    return MarketRegime.STRONG_UPTREND
                else:
                    return MarketRegime.STRONG_DOWNTREND
        
            elif trend_strength > 0.3:
                # Weak trend
                recent_close = self.closes[-1]
                old_close = self.closes[0]
            
                if recent_close > old_close:
                    return MarketRegime.WEAK_UPTREND
                else:
                    return MarketRegime.WEAK_DOWNTREND
        
            else:
                # Range bound
                return MarketRegime.RANGE_BOUND
        except Exception as e:
            logger.error(f"Error in _classify_regime: {e}")
            raise
    
    def get_strategy_recommendation(self) -> str:
        """Get strategy recommendation based on regime."""
        try:
            if not self.regime_history:
                return "No regime detected yet"
        
            metrics = self.regime_history[-1]
            regime = metrics.regime
        
            recommendations = {
                MarketRegime.STRONG_UPTREND: "Use trend-following strategy, buy dips",
                MarketRegime.WEAK_UPTREND: "Use conservative entries, watch for reversals",
                MarketRegime.RANGE_BOUND: "Use range trading, buy support/sell resistance",
                MarketRegime.WEAK_DOWNTREND: "Use conservative shorts, watch for reversals",
                MarketRegime.STRONG_DOWNTREND: "Use trend-following shorts, sell rallies",
                MarketRegime.HIGHLY_VOLATILE: "Reduce position size, use wider stops"
            }
        
            return recommendations.get(regime, "Unknown regime")
        except Exception as e:
            logger.error(f"Error in get_strategy_recommendation: {e}")
            raise
    
    def get_regime_status(self) -> str:
        """Get human-readable regime status."""
        try:
            if not self.regime_history:
                return "No regime data"
        
            metrics = self.regime_history[-1]
        
            status = "MARKET REGIME STATUS\n"
            status += "=" * 50 + "\n"
            status += f"Regime: {metrics.regime.name}\n"
            status += f"Trend Strength: {metrics.trend_strength:.2f}\n"
            status += f"Volatility: {metrics.volatility:.2f}\n"
            status += f"Support: {metrics.support:.5f}\n"
            status += f"Resistance: {metrics.resistance:.5f}\n"
            status += f"Range Width: {metrics.range_width:.5f}\n"
            status += "=" * 50 + "\n"
            status += f"Strategy: {self.get_strategy_recommendation()}\n"
        
            return status
        except Exception as e:
            logger.error(f"Error in get_regime_status: {e}")
            raise
    
    def reset(self):
        """Reset detector."""
        try:
            self.highs.clear()
            self.lows.clear()
            self.closes.clear()
            self.volumes.clear()
            self.regime_history.clear()
            logger.info("Market regime detector reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
