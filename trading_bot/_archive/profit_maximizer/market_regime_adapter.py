"""
Market Regime Adapter
=====================

Adapts trading strategy based on detected market regime.
This is critical for maximizing profits - different regimes need different approaches.

REGIMES:
- TRENDING: Wide targets, trail stops, ride the trend
- RANGING: Tight targets, quick exits, fade extremes
- VOLATILE: Reduce size, wider stops, fewer trades
- QUIET: Skip or reduce size, wait for action
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    BREAKOUT = "breakout"


@dataclass
class RegimeAnalysis:
    """Market regime analysis result"""
    regime: MarketRegime
    confidence: float
    trend_strength: float
    volatility_percentile: float
    range_bound_score: float
    recommended_strategy: str
    size_adjustment: float
    target_adjustment: float
    stop_adjustment: float


class MarketRegimeAdapter:
    """
    Detects market regime and adapts trading parameters accordingly.
    
    This is how professional traders adapt to changing conditions.
    """
    
    def __init__(self):
        self.regime_history = []
        logger.info("Market Regime Adapter initialized")
    
    def analyze_regime(self, market_data: pd.DataFrame) -> RegimeAnalysis:
        """
        Analyze current market regime
        
        Args:
            market_data: OHLCV DataFrame
        
        Returns:
            RegimeAnalysis with regime and adaptations
        """
        close = market_data['close'].values
        high = market_data['high'].values
        low = market_data['low'].values
        
        # Calculate metrics
        trend_strength = self._calculate_trend_strength(close)
        volatility_pct = self._calculate_volatility_percentile(close)
        range_score = self._calculate_range_score(high, low, close)
        
        # Determine regime
        regime, confidence = self._classify_regime(
            trend_strength, volatility_pct, range_score
        )
        
        # Get adaptations
        strategy, size_adj, target_adj, stop_adj = self._get_adaptations(regime)
        
        analysis = RegimeAnalysis(
            regime=regime,
            confidence=confidence,
            trend_strength=trend_strength,
            volatility_percentile=volatility_pct,
            range_bound_score=range_score,
            recommended_strategy=strategy,
            size_adjustment=size_adj,
            target_adjustment=target_adj,
            stop_adjustment=stop_adj
        )
        
        self.regime_history.append(analysis)
        
        return analysis
    
    def _calculate_trend_strength(self, close: np.ndarray) -> float:
        """Calculate trend strength using ADX-like method"""
        if len(close) < 20:
            return 0.0
        
        # Simple trend strength: distance from 20 EMA as % of price
        ema_20 = self._ema(close, 20)
        deviation = (close[-1] - ema_20[-1]) / close[-1]
        
        # Also check EMA slope
        ema_slope = (ema_20[-1] - ema_20[-5]) / ema_20[-5] if len(ema_20) >= 5 else 0
        
        # Combine
        strength = abs(deviation) * 10 + abs(ema_slope) * 100
        
        return min(1.0, strength)
    
    def _calculate_volatility_percentile(self, close: np.ndarray) -> float:
        """Calculate current volatility percentile"""
        if len(close) < 50:
            return 50.0
        
        returns = np.diff(close) / close[:-1]
        
        # Current volatility (last 10 bars)
        current_vol = np.std(returns[-10:])
        
        # Historical volatility windows
        vol_windows = [np.std(returns[i:i+10]) for i in range(0, len(returns)-10, 5)]
        
        if not vol_windows:
            return 50.0
        
        # Percentile
        percentile = sum(1 for v in vol_windows if v < current_vol) / len(vol_windows) * 100
        
        return percentile
    
    def _calculate_range_score(self, high: np.ndarray, low: np.ndarray, 
                               close: np.ndarray) -> float:
        """Calculate how range-bound the market is"""
        if len(close) < 20:
            return 0.5
        
        # Recent range
        recent_high = np.max(high[-20:])
        recent_low = np.min(low[-20:])
        range_size = (recent_high - recent_low) / close[-1]
        
        # How many times price touched range boundaries
        touches = 0
        for i in range(-20, 0):
            if high[i] >= recent_high * 0.99:
                touches += 1
            if low[i] <= recent_low * 1.01:
                touches += 1
        
        # Range score: small range + many touches = range-bound
        if range_size < 0.02 and touches >= 4:
            return 0.9
        elif range_size < 0.03 and touches >= 2:
            return 0.7
        elif range_size < 0.05:
            return 0.5
        else:
            return 0.2
    
    def _classify_regime(self, trend: float, vol_pct: float, 
                        range_score: float) -> Tuple[MarketRegime, float]:
        """Classify market regime"""
        
        # High volatility overrides
        if vol_pct > 85:
            return MarketRegime.VOLATILE, 0.8
        
        # Very quiet
        if vol_pct < 15:
            return MarketRegime.QUIET, 0.7
        
        # Strong trend
        if trend > 0.6:
            if trend > 0:
                return MarketRegime.TRENDING_UP, min(0.9, trend)
            else:
                return MarketRegime.TRENDING_DOWN, min(0.9, abs(trend))
        
        # Range-bound
        if range_score > 0.7:
            return MarketRegime.RANGING, range_score
        
        # Breakout potential
        if vol_pct > 60 and range_score > 0.5:
            return MarketRegime.BREAKOUT, 0.6
        
        # Default to ranging
        return MarketRegime.RANGING, 0.5
    
    def _get_adaptations(self, regime: MarketRegime) -> Tuple[str, float, float, float]:
        """Get strategy adaptations for regime"""
        
        adaptations = {
            MarketRegime.TRENDING_UP: (
                "Trend following - buy dips, trail stops, wide targets",
                1.0,   # Normal size
                1.5,   # Extended targets
                1.2    # Wider stops
            ),
            MarketRegime.TRENDING_DOWN: (
                "Trend following - sell rallies, trail stops, wide targets",
                1.0,
                1.5,
                1.2
            ),
            MarketRegime.RANGING: (
                "Mean reversion - fade extremes, tight targets, quick exits",
                0.8,   # Reduced size
                0.7,   # Tighter targets
                0.8    # Tighter stops
            ),
            MarketRegime.VOLATILE: (
                "Defensive - reduce size, wider stops, fewer trades",
                0.5,   # Half size
                1.0,   # Normal targets
                1.5    # Much wider stops
            ),
            MarketRegime.QUIET: (
                "Wait mode - skip or minimal size, wait for volatility",
                0.25,  # Quarter size
                0.8,   # Tighter targets
                0.8    # Tighter stops
            ),
            MarketRegime.BREAKOUT: (
                "Breakout mode - wait for confirmation, then full size",
                1.0,
                2.0,   # Extended targets for breakout
                1.0
            ),
        }
        
        return adaptations.get(regime, ("Default", 1.0, 1.0, 1.0))
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data, dtype=float)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema
