"""
Skill #9: Cumulative Delta Tracker
==================================

Tracks running total of buying vs selling pressure.
Identifies divergences and trend confirmation.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DeltaTrend(Enum):
    """Cumulative delta trend."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class DeltaSignal(Enum):
    """Delta-based trading signal."""
    BULLISH_DIVERGENCE = "bullish_divergence"
    BEARISH_DIVERGENCE = "bearish_divergence"
    BULLISH_CONFIRMATION = "bullish_confirmation"
    BEARISH_CONFIRMATION = "bearish_confirmation"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    NEUTRAL = "neutral"


@dataclass
class DeltaPoint:
    """Single cumulative delta point."""
    timestamp: datetime
    bar_delta: float
    cumulative_delta: float
    price: float
    volume: float


@dataclass
class DeltaDivergence:
    """Detected delta divergence."""
    divergence_type: str
    start_time: datetime
    end_time: datetime
    price_direction: str
    delta_direction: str
    strength: float


@dataclass
class CumulativeDeltaResult:
    """Complete cumulative delta analysis."""
    current_delta: float
    cumulative_delta: float
    delta_trend: DeltaTrend
    delta_signal: DeltaSignal
    delta_history: List[DeltaPoint]
    divergences: List[DeltaDivergence]
    delta_momentum: float
    delta_acceleration: float
    support_levels: List[float]
    resistance_levels: List[float]
    trading_recommendation: str
    confidence: float


class CumulativeDeltaTracker:
    """
    Advanced Cumulative Delta Tracking System.
    
    Monitors buying vs selling pressure over time.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.lookback = self.config.get('lookback', 50)
            self.divergence_threshold = self.config.get('divergence_threshold', 0.05)
            self.delta_history: List[DeltaPoint] = []
            self.cumulative_delta = 0.0
        
            logger.info("CumulativeDeltaTracker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        high: float,
        low: float,
        close: float,
        volume: float,
        timestamp: datetime,
        buy_volume: Optional[float] = None,
        sell_volume: Optional[float] = None
    ) -> CumulativeDeltaResult:
        """
        Update with new bar data.
        
        Args:
            high, low, close: Price data
            volume: Total volume
            timestamp: Bar timestamp
            buy_volume: Optional buy volume
            sell_volume: Optional sell volume
            
        Returns:
            CumulativeDeltaResult with analysis
        """
        # Calculate delta
        try:
            if buy_volume is not None and sell_volume is not None:
                bar_delta = buy_volume - sell_volume
            else:
                bar_delta = self._estimate_delta(high, low, close, volume)
        
            # Update cumulative
            self.cumulative_delta += bar_delta
        
            # Add to history
            self.delta_history.append(DeltaPoint(
                timestamp=timestamp,
                bar_delta=bar_delta,
                cumulative_delta=self.cumulative_delta,
                price=close,
                volume=volume
            ))
        
            # Trim history
            if len(self.delta_history) > self.lookback * 2:
                self.delta_history = self.delta_history[-self.lookback * 2:]
        
            return self.analyze()
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def analyze(self) -> CumulativeDeltaResult:
        """Perform complete analysis on current data."""
        try:
            if len(self.delta_history) < 5:
                return self._create_empty_result()
        
            # Current values
            current_delta = self.delta_history[-1].bar_delta
            cumulative = self.cumulative_delta
        
            # Determine trend
            delta_trend = self._determine_trend()
        
            # Determine signal
            delta_signal = self._determine_signal()
        
            # Find divergences
            divergences = self._find_divergences()
        
            # Calculate momentum
            momentum = self._calculate_momentum()
        
            # Calculate acceleration
            acceleration = self._calculate_acceleration()
        
            # Find support/resistance from delta
            support, resistance = self._find_delta_levels()
        
            # Generate recommendation
            recommendation = self._generate_recommendation(
                delta_trend, delta_signal, divergences, momentum
            )
        
            # Calculate confidence
            confidence = self._calculate_confidence(
                delta_trend, divergences, momentum
            )
        
            return CumulativeDeltaResult(
                current_delta=current_delta,
                cumulative_delta=cumulative,
                delta_trend=delta_trend,
                delta_signal=delta_signal,
                delta_history=self.delta_history[-self.lookback:],
                divergences=divergences,
                delta_momentum=momentum,
                delta_acceleration=acceleration,
                support_levels=support,
                resistance_levels=resistance,
                trading_recommendation=recommendation,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _estimate_delta(
        self,
        high: float,
        low: float,
        close: float,
        volume: float
    ) -> float:
        """Estimate delta from OHLC data."""
        try:
            bar_range = high - low
        
            if bar_range > 0:
                # Position of close within bar
                close_position = (close - low) / bar_range
                # Delta estimate: positive if close near high
                delta = volume * (close_position * 2 - 1)
            else:
                delta = 0
        
            return delta
        except Exception as e:
            logger.error(f"Error in _estimate_delta: {e}")
            raise
    
    def _determine_trend(self) -> DeltaTrend:
        """Determine cumulative delta trend."""
        try:
            if len(self.delta_history) < 10:
                return DeltaTrend.NEUTRAL
        
            recent = self.delta_history[-10:]
        
            # Calculate slope of cumulative delta
            cum_deltas = [p.cumulative_delta for p in recent]
            x = np.arange(len(cum_deltas))
            slope = np.polyfit(x, cum_deltas, 1)[0]
        
            # Normalize by average volume
            avg_volume = np.mean([p.volume for p in recent])
            normalized_slope = slope / (avg_volume + 1e-10)
        
            if normalized_slope > 0.5:
                return DeltaTrend.STRONG_BULLISH
            elif normalized_slope > 0.1:
                return DeltaTrend.BULLISH
            elif normalized_slope < -0.5:
                return DeltaTrend.STRONG_BEARISH
            elif normalized_slope < -0.1:
                return DeltaTrend.BEARISH
            else:
                return DeltaTrend.NEUTRAL
        except Exception as e:
            logger.error(f"Error in _determine_trend: {e}")
            raise
    
    def _determine_signal(self) -> DeltaSignal:
        """Determine trading signal from delta."""
        try:
            if len(self.delta_history) < 10:
                return DeltaSignal.NEUTRAL
        
            recent = self.delta_history[-10:]
        
            # Price trend
            prices = [p.price for p in recent]
            price_change = (prices[-1] - prices[0]) / prices[0]
        
            # Delta trend
            cum_deltas = [p.cumulative_delta for p in recent]
            delta_change = cum_deltas[-1] - cum_deltas[0]
            avg_volume = np.mean([p.volume for p in recent])
            normalized_delta_change = delta_change / (avg_volume * len(recent) + 1e-10)
        
            # Check for divergence
            if price_change < -self.divergence_threshold and normalized_delta_change > 0.1:
                return DeltaSignal.BULLISH_DIVERGENCE
            elif price_change > self.divergence_threshold and normalized_delta_change < -0.1:
                return DeltaSignal.BEARISH_DIVERGENCE
        
            # Check for confirmation
            if price_change > self.divergence_threshold and normalized_delta_change > 0.1:
                return DeltaSignal.BULLISH_CONFIRMATION
            elif price_change < -self.divergence_threshold and normalized_delta_change < -0.1:
                return DeltaSignal.BEARISH_CONFIRMATION
        
            # Check for accumulation/distribution
            if normalized_delta_change > 0.2 and abs(price_change) < self.divergence_threshold:
                return DeltaSignal.ACCUMULATION
            elif normalized_delta_change < -0.2 and abs(price_change) < self.divergence_threshold:
                return DeltaSignal.DISTRIBUTION
        
            return DeltaSignal.NEUTRAL
        except Exception as e:
            logger.error(f"Error in _determine_signal: {e}")
            raise
    
    def _find_divergences(self) -> List[DeltaDivergence]:
        """Find price-delta divergences."""
        try:
            divergences = []
        
            if len(self.delta_history) < 20:
                return divergences
        
            # Find swing points in price
            prices = [p.price for p in self.delta_history]
            cum_deltas = [p.cumulative_delta for p in self.delta_history]
        
            price_lows = self._find_swing_lows(prices)
            price_highs = self._find_swing_highs(prices)
        
            # Check for bullish divergence (lower price low, higher delta low)
            for i in range(len(price_lows) - 1):
                idx1, idx2 = price_lows[i], price_lows[-1]
            
                if prices[idx2] < prices[idx1]:  # Lower price low
                    if cum_deltas[idx2] > cum_deltas[idx1]:  # Higher delta low
                        divergences.append(DeltaDivergence(
                            divergence_type="bullish",
                            start_time=self.delta_history[idx1].timestamp,
                            end_time=self.delta_history[idx2].timestamp,
                            price_direction="down",
                            delta_direction="up",
                            strength=abs(cum_deltas[idx2] - cum_deltas[idx1])
                        ))
        
            # Check for bearish divergence (higher price high, lower delta high)
            for i in range(len(price_highs) - 1):
                idx1, idx2 = price_highs[i], price_highs[-1]
            
                if prices[idx2] > prices[idx1]:  # Higher price high
                    if cum_deltas[idx2] < cum_deltas[idx1]:  # Lower delta high
                        divergences.append(DeltaDivergence(
                            divergence_type="bearish",
                            start_time=self.delta_history[idx1].timestamp,
                            end_time=self.delta_history[idx2].timestamp,
                            price_direction="up",
                            delta_direction="down",
                            strength=abs(cum_deltas[idx2] - cum_deltas[idx1])
                        ))
        
            return divergences
        except Exception as e:
            logger.error(f"Error in _find_divergences: {e}")
            raise
    
    def _find_swing_lows(self, data: List[float], lookback: int = 3) -> List[int]:
        """Find swing low indices."""
        try:
            lows = []
            for i in range(lookback, len(data) - lookback):
                is_low = all(data[i] <= data[i - j] for j in range(1, lookback + 1))
                is_low = is_low and all(data[i] <= data[i + j] for j in range(1, lookback + 1))
                if is_low:
                    lows.append(i)
            return lows
        except Exception as e:
            logger.error(f"Error in _find_swing_lows: {e}")
            raise
    
    def _find_swing_highs(self, data: List[float], lookback: int = 3) -> List[int]:
        """Find swing high indices."""
        try:
            highs = []
            for i in range(lookback, len(data) - lookback):
                is_high = all(data[i] >= data[i - j] for j in range(1, lookback + 1))
                is_high = is_high and all(data[i] >= data[i + j] for j in range(1, lookback + 1))
                if is_high:
                    highs.append(i)
            return highs
        except Exception as e:
            logger.error(f"Error in _find_swing_highs: {e}")
            raise
    
    def _calculate_momentum(self) -> float:
        """Calculate delta momentum (rate of change)."""
        try:
            if len(self.delta_history) < 5:
                return 0.0
        
            recent = self.delta_history[-5:]
            deltas = [p.bar_delta for p in recent]
        
            # Momentum = current vs average
            current = deltas[-1]
            avg = np.mean(deltas[:-1])
        
            if avg == 0:
                return 0.0
        
            return (current - avg) / abs(avg)
        except Exception as e:
            logger.error(f"Error in _calculate_momentum: {e}")
            raise
    
    def _calculate_acceleration(self) -> float:
        """Calculate delta acceleration (change in momentum)."""
        try:
            if len(self.delta_history) < 10:
                return 0.0
        
            # Calculate momentum at two points
            recent = self.delta_history[-5:]
            older = self.delta_history[-10:-5]
        
            recent_deltas = [p.bar_delta for p in recent]
            older_deltas = [p.bar_delta for p in older]
        
            recent_momentum = np.mean(recent_deltas)
            older_momentum = np.mean(older_deltas)
        
            if older_momentum == 0:
                return 0.0
        
            return (recent_momentum - older_momentum) / abs(older_momentum)
        except Exception as e:
            logger.error(f"Error in _calculate_acceleration: {e}")
            raise
    
    def _find_delta_levels(self) -> Tuple[List[float], List[float]]:
        """Find support/resistance from delta extremes."""
        try:
            if len(self.delta_history) < 10:
                return [], []
        
            support = []
            resistance = []
        
            # Find prices where delta made significant lows (support)
            cum_deltas = [p.cumulative_delta for p in self.delta_history]
            prices = [p.price for p in self.delta_history]
        
            delta_lows = self._find_swing_lows(cum_deltas)
            delta_highs = self._find_swing_highs(cum_deltas)
        
            for idx in delta_lows:
                support.append(prices[idx])
        
            for idx in delta_highs:
                resistance.append(prices[idx])
        
            return support[-3:], resistance[-3:]
        except Exception as e:
            logger.error(f"Error in _find_delta_levels: {e}")
            raise
    
    def _generate_recommendation(
        self,
        trend: DeltaTrend,
        signal: DeltaSignal,
        divergences: List[DeltaDivergence],
        momentum: float
    ) -> str:
        """Generate trading recommendation."""
        try:
            recommendations = []
        
            # Trend-based
            if trend == DeltaTrend.STRONG_BULLISH:
                recommendations.append("STRONG BUYING: Heavy accumulation in progress")
            elif trend == DeltaTrend.STRONG_BEARISH:
                recommendations.append("STRONG SELLING: Heavy distribution in progress")
            elif trend == DeltaTrend.BULLISH:
                recommendations.append("BUYING: Moderate accumulation")
            elif trend == DeltaTrend.BEARISH:
                recommendations.append("SELLING: Moderate distribution")
        
            # Signal-based
            if signal == DeltaSignal.BULLISH_DIVERGENCE:
                recommendations.append("BULLISH DIVERGENCE: Price down, delta up - reversal likely")
            elif signal == DeltaSignal.BEARISH_DIVERGENCE:
                recommendations.append("BEARISH DIVERGENCE: Price up, delta down - reversal likely")
            elif signal == DeltaSignal.BULLISH_CONFIRMATION:
                recommendations.append("BULLISH CONFIRMATION: Price and delta aligned up")
            elif signal == DeltaSignal.BEARISH_CONFIRMATION:
                recommendations.append("BEARISH CONFIRMATION: Price and delta aligned down")
            elif signal == DeltaSignal.ACCUMULATION:
                recommendations.append("ACCUMULATION: Smart money buying")
            elif signal == DeltaSignal.DISTRIBUTION:
                recommendations.append("DISTRIBUTION: Smart money selling")
        
            # Momentum-based
            if momentum > 0.5:
                recommendations.append("MOMENTUM: Accelerating buying")
            elif momentum < -0.5:
                recommendations.append("MOMENTUM: Accelerating selling")
        
            return " | ".join(recommendations) if recommendations else "NEUTRAL: No clear delta signal"
        except Exception as e:
            logger.error(f"Error in _generate_recommendation: {e}")
            raise
    
    def _calculate_confidence(
        self,
        trend: DeltaTrend,
        divergences: List[DeltaDivergence],
        momentum: float
    ) -> float:
        """Calculate confidence in the analysis."""
        try:
            confidence = 0.5
        
            # Strong trend adds confidence
            if trend in [DeltaTrend.STRONG_BULLISH, DeltaTrend.STRONG_BEARISH]:
                confidence += 0.2
            elif trend in [DeltaTrend.BULLISH, DeltaTrend.BEARISH]:
                confidence += 0.1
        
            # Divergences add confidence
            if divergences:
                confidence += 0.15
        
            # Strong momentum adds confidence
            if abs(momentum) > 0.5:
                confidence += 0.1
        
            return min(1.0, confidence)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _create_empty_result(self) -> CumulativeDeltaResult:
        """Create empty result for insufficient data."""
        return CumulativeDeltaResult(
            current_delta=0,
            cumulative_delta=0,
            delta_trend=DeltaTrend.NEUTRAL,
            delta_signal=DeltaSignal.NEUTRAL,
            delta_history=[],
            divergences=[],
            delta_momentum=0,
            delta_acceleration=0,
            support_levels=[],
            resistance_levels=[],
            trading_recommendation="Insufficient data",
            confidence=0
        )
    
    def reset(self):
        """Reset the tracker."""
        try:
            self.delta_history = []
            self.cumulative_delta = 0.0
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
