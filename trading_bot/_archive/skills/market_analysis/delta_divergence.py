"""
Skill #6: Delta Divergence Detector
===================================

Detects divergences between volume delta and price movement.
Identifies potential reversals when price and delta disagree.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DivergenceType(Enum):
    """Type of divergence."""
    BULLISH_REGULAR = "bullish_regular"  # Price lower low, delta higher low
    BEARISH_REGULAR = "bearish_regular"  # Price higher high, delta lower high
    BULLISH_HIDDEN = "bullish_hidden"  # Price higher low, delta lower low
    BEARISH_HIDDEN = "bearish_hidden"  # Price lower high, delta higher high
    NONE = "none"


class DivergenceStrength(Enum):
    """Strength of divergence signal."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    EXTREME = 4


@dataclass
class DeltaBar:
    """Volume delta for a single bar."""
    timestamp: datetime
    delta: float  # Buy volume - Sell volume
    cumulative_delta: float
    buy_volume: float
    sell_volume: float
    total_volume: float
    delta_percentage: float  # Delta as % of total volume


@dataclass
class Divergence:
    """Detected divergence."""
    divergence_type: DivergenceType
    strength: DivergenceStrength
    start_timestamp: datetime
    end_timestamp: datetime
    price_start: float
    price_end: float
    delta_start: float
    delta_end: float
    bars_apart: int
    confidence: float
    trading_signal: str


@dataclass
class DeltaAnalysisResult:
    """Complete delta analysis result."""
    current_delta: DeltaBar
    cumulative_delta: float
    delta_trend: str  # 'accumulation', 'distribution', 'neutral'
    divergences: List[Divergence]
    active_divergence: Optional[Divergence]
    delta_momentum: float  # Rate of change of delta
    absorption_detected: bool
    exhaustion_detected: bool
    trading_recommendation: str
    confidence: float


class DeltaDivergenceDetector:
    """
    Advanced Delta Divergence Detection System.
    
    Analyzes volume delta to detect divergences with price.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lookback = self.config.get('lookback', 20)
        self.divergence_threshold = self.config.get('divergence_threshold', 0.1)
        self.cumulative_delta = 0.0
        self.delta_history: List[DeltaBar] = []
        
        logger.info("DeltaDivergenceDetector initialized")
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        buy_volumes: Optional[np.ndarray] = None,
        sell_volumes: Optional[np.ndarray] = None
    ) -> DeltaAnalysisResult:
        """
        Perform complete delta divergence analysis.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            volumes: Array of total volumes
            timestamps: List of timestamps
            buy_volumes: Optional array of buy volumes
            sell_volumes: Optional array of sell volumes
            
        Returns:
            DeltaAnalysisResult with complete analysis
        """
        # Calculate delta if not provided
        if buy_volumes is None or sell_volumes is None:
            buy_volumes, sell_volumes = self._estimate_buy_sell_volume(
                highs, lows, closes, volumes
            )
        
        # Build delta bars
        delta_bars = self._build_delta_bars(
            buy_volumes, sell_volumes, volumes, timestamps
        )
        
        if not delta_bars:
            return self._create_empty_result()
        
        # Update history
        self.delta_history = delta_bars
        
        # Get current delta
        current_delta = delta_bars[-1]
        
        # Calculate cumulative delta
        cumulative_delta = sum(bar.delta for bar in delta_bars)
        
        # Determine delta trend
        delta_trend = self._determine_delta_trend(delta_bars)
        
        # Detect divergences
        divergences = self._detect_divergences(closes, delta_bars, timestamps)
        
        # Find active divergence
        active_divergence = self._find_active_divergence(divergences, closes[-1])
        
        # Calculate delta momentum
        delta_momentum = self._calculate_delta_momentum(delta_bars)
        
        # Detect absorption
        absorption_detected = self._detect_absorption(
            closes, volumes, delta_bars
        )
        
        # Detect exhaustion
        exhaustion_detected = self._detect_exhaustion(
            closes, volumes, delta_bars
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            active_divergence, delta_trend, absorption_detected, exhaustion_detected
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            divergences, delta_trend, absorption_detected
        )
        
        return DeltaAnalysisResult(
            current_delta=current_delta,
            cumulative_delta=cumulative_delta,
            delta_trend=delta_trend,
            divergences=divergences,
            active_divergence=active_divergence,
            delta_momentum=delta_momentum,
            absorption_detected=absorption_detected,
            exhaustion_detected=exhaustion_detected,
            trading_recommendation=recommendation,
            confidence=confidence
        )
    
    def _estimate_buy_sell_volume(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate buy/sell volume using price position within bar.
        
        Uses the assumption that if close is near high, more buying occurred.
        """
        buy_volumes = np.zeros(len(volumes))
        sell_volumes = np.zeros(len(volumes))
        
        for i in range(len(volumes)):
            bar_range = highs[i] - lows[i]
            
            if bar_range > 0:
                # Position of close within the bar (0 = low, 1 = high)
                close_position = (closes[i] - lows[i]) / bar_range
                
                # Estimate buy/sell split
                buy_volumes[i] = volumes[i] * close_position
                sell_volumes[i] = volumes[i] * (1 - close_position)
            else:
                # Doji - split evenly
                buy_volumes[i] = volumes[i] / 2
                sell_volumes[i] = volumes[i] / 2
        
        return buy_volumes, sell_volumes
    
    def _build_delta_bars(
        self,
        buy_volumes: np.ndarray,
        sell_volumes: np.ndarray,
        total_volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[DeltaBar]:
        """Build delta bar objects."""
        delta_bars = []
        cumulative = 0.0
        
        for i in range(len(buy_volumes)):
            delta = buy_volumes[i] - sell_volumes[i]
            cumulative += delta
            
            total = total_volumes[i]
            delta_pct = (delta / total * 100) if total > 0 else 0
            
            delta_bars.append(DeltaBar(
                timestamp=timestamps[i],
                delta=delta,
                cumulative_delta=cumulative,
                buy_volume=buy_volumes[i],
                sell_volume=sell_volumes[i],
                total_volume=total,
                delta_percentage=delta_pct
            ))
        
        return delta_bars
    
    def _determine_delta_trend(self, delta_bars: List[DeltaBar]) -> str:
        """Determine overall delta trend."""
        if len(delta_bars) < 5:
            return "neutral"
        
        recent = delta_bars[-10:]
        
        # Calculate trend of cumulative delta
        cum_deltas = [bar.cumulative_delta for bar in recent]
        
        # Simple linear regression slope
        x = np.arange(len(cum_deltas))
        slope = np.polyfit(x, cum_deltas, 1)[0]
        
        # Normalize by average volume
        avg_volume = np.mean([bar.total_volume for bar in recent])
        normalized_slope = slope / (avg_volume + 1e-10)
        
        if normalized_slope > 0.1:
            return "accumulation"
        elif normalized_slope < -0.1:
            return "distribution"
        else:
            return "neutral"
    
    def _detect_divergences(
        self,
        closes: np.ndarray,
        delta_bars: List[DeltaBar],
        timestamps: List[datetime]
    ) -> List[Divergence]:
        """Detect divergences between price and delta."""
        divergences = []
        
        if len(closes) < self.lookback:
            return divergences
        
        # Find swing highs and lows in price
        price_highs = self._find_swing_points(closes, is_high=True)
        price_lows = self._find_swing_points(closes, is_high=False)
        
        # Find swing highs and lows in cumulative delta
        cum_deltas = np.array([bar.cumulative_delta for bar in delta_bars])
        delta_highs = self._find_swing_points(cum_deltas, is_high=True)
        delta_lows = self._find_swing_points(cum_deltas, is_high=False)
        
        # Check for bullish regular divergence (price lower low, delta higher low)
        for i in range(len(price_lows) - 1):
            for j in range(i + 1, len(price_lows)):
                idx1, idx2 = price_lows[i], price_lows[j]
                
                if closes[idx2] < closes[idx1]:  # Price made lower low
                    # Find corresponding delta lows
                    delta_idx1 = self._find_nearest_swing(delta_lows, idx1)
                    delta_idx2 = self._find_nearest_swing(delta_lows, idx2)
                    
                    if delta_idx1 is not None and delta_idx2 is not None:
                        if cum_deltas[delta_idx2] > cum_deltas[delta_idx1]:
                            # Bullish divergence!
                            strength = self._calculate_divergence_strength(
                                closes[idx1], closes[idx2],
                                cum_deltas[delta_idx1], cum_deltas[delta_idx2]
                            )
                            
                            divergences.append(Divergence(
                                divergence_type=DivergenceType.BULLISH_REGULAR,
                                strength=strength,
                                start_timestamp=timestamps[idx1],
                                end_timestamp=timestamps[idx2],
                                price_start=closes[idx1],
                                price_end=closes[idx2],
                                delta_start=cum_deltas[delta_idx1],
                                delta_end=cum_deltas[delta_idx2],
                                bars_apart=idx2 - idx1,
                                confidence=0.7,
                                trading_signal="BUY: Bullish divergence detected"
                            ))
        
        # Check for bearish regular divergence (price higher high, delta lower high)
        for i in range(len(price_highs) - 1):
            for j in range(i + 1, len(price_highs)):
                idx1, idx2 = price_highs[i], price_highs[j]
                
                if closes[idx2] > closes[idx1]:  # Price made higher high
                    delta_idx1 = self._find_nearest_swing(delta_highs, idx1)
                    delta_idx2 = self._find_nearest_swing(delta_highs, idx2)
                    
                    if delta_idx1 is not None and delta_idx2 is not None:
                        if cum_deltas[delta_idx2] < cum_deltas[delta_idx1]:
                            # Bearish divergence!
                            strength = self._calculate_divergence_strength(
                                closes[idx1], closes[idx2],
                                cum_deltas[delta_idx1], cum_deltas[delta_idx2]
                            )
                            
                            divergences.append(Divergence(
                                divergence_type=DivergenceType.BEARISH_REGULAR,
                                strength=strength,
                                start_timestamp=timestamps[idx1],
                                end_timestamp=timestamps[idx2],
                                price_start=closes[idx1],
                                price_end=closes[idx2],
                                delta_start=cum_deltas[delta_idx1],
                                delta_end=cum_deltas[delta_idx2],
                                bars_apart=idx2 - idx1,
                                confidence=0.7,
                                trading_signal="SELL: Bearish divergence detected"
                            ))
        
        return divergences
    
    def _find_swing_points(
        self,
        data: np.ndarray,
        is_high: bool,
        lookback: int = 5
    ) -> List[int]:
        """Find swing high or low points."""
        swings = []
        
        for i in range(lookback, len(data) - lookback):
            if is_high:
                is_swing = all(data[i] >= data[i - j] for j in range(1, lookback + 1))
                is_swing = is_swing and all(data[i] >= data[i + j] for j in range(1, lookback + 1))
            else:
                is_swing = all(data[i] <= data[i - j] for j in range(1, lookback + 1))
                is_swing = is_swing and all(data[i] <= data[i + j] for j in range(1, lookback + 1))
            
            if is_swing:
                swings.append(i)
        
        return swings
    
    def _find_nearest_swing(
        self,
        swings: List[int],
        target_idx: int,
        tolerance: int = 3
    ) -> Optional[int]:
        """Find nearest swing point to target index."""
        for swing in swings:
            if abs(swing - target_idx) <= tolerance:
                return swing
        return None
    
    def _calculate_divergence_strength(
        self,
        price1: float,
        price2: float,
        delta1: float,
        delta2: float
    ) -> DivergenceStrength:
        """Calculate strength of divergence."""
        price_change = abs(price2 - price1) / price1
        delta_change = abs(delta2 - delta1) / (abs(delta1) + 1e-10)
        
        # Combined divergence magnitude
        magnitude = price_change + delta_change
        
        if magnitude > 0.3:
            return DivergenceStrength.EXTREME
        elif magnitude > 0.2:
            return DivergenceStrength.STRONG
        elif magnitude > 0.1:
            return DivergenceStrength.MODERATE
        else:
            return DivergenceStrength.WEAK
    
    def _find_active_divergence(
        self,
        divergences: List[Divergence],
        current_price: float
    ) -> Optional[Divergence]:
        """Find the most recent active divergence."""
        if not divergences:
            return None
        
        # Return most recent divergence
        return divergences[-1]
    
    def _calculate_delta_momentum(self, delta_bars: List[DeltaBar]) -> float:
        """Calculate rate of change of delta."""
        if len(delta_bars) < 5:
            return 0.0
        
        recent = delta_bars[-5:]
        deltas = [bar.delta for bar in recent]
        
        # Simple momentum: current vs average
        current = deltas[-1]
        avg = np.mean(deltas[:-1])
        
        if avg == 0:
            return 0.0
        
        return (current - avg) / abs(avg)
    
    def _detect_absorption(
        self,
        closes: np.ndarray,
        volumes: np.ndarray,
        delta_bars: List[DeltaBar]
    ) -> bool:
        """
        Detect absorption (high volume with little price movement).
        
        Absorption suggests strong hands absorbing selling/buying pressure.
        """
        if len(closes) < 5:
            return False
        
        recent_closes = closes[-5:]
        recent_volumes = volumes[-5:]
        recent_deltas = [bar.delta for bar in delta_bars[-5:]]
        
        # Price range
        price_range = np.max(recent_closes) - np.min(recent_closes)
        avg_price = np.mean(recent_closes)
        price_range_pct = price_range / avg_price
        
        # Volume is high
        avg_volume = np.mean(volumes)
        recent_avg_volume = np.mean(recent_volumes)
        volume_ratio = recent_avg_volume / (avg_volume + 1e-10)
        
        # Delta is mixed (buyers and sellers fighting)
        delta_sum = abs(sum(recent_deltas))
        delta_total = sum(abs(d) for d in recent_deltas)
        delta_ratio = delta_sum / (delta_total + 1e-10)
        
        # Absorption: high volume, low price movement, mixed delta
        return volume_ratio > 1.5 and price_range_pct < 0.01 and delta_ratio < 0.3
    
    def _detect_exhaustion(
        self,
        closes: np.ndarray,
        volumes: np.ndarray,
        delta_bars: List[DeltaBar]
    ) -> bool:
        """
        Detect exhaustion (extreme delta with price stalling).
        
        Exhaustion suggests the trend is running out of steam.
        """
        if len(closes) < 5:
            return False
        
        recent_closes = closes[-5:]
        recent_deltas = [bar.delta for bar in delta_bars[-5:]]
        
        # Check for extreme delta
        avg_delta = np.mean([abs(bar.delta) for bar in delta_bars])
        recent_delta = abs(recent_deltas[-1])
        
        is_extreme_delta = recent_delta > avg_delta * 2
        
        # Check for price stalling
        price_change = abs(recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        is_stalling = price_change < 0.005  # Less than 0.5% move
        
        return is_extreme_delta and is_stalling
    
    def _generate_recommendation(
        self,
        active_divergence: Optional[Divergence],
        delta_trend: str,
        absorption: bool,
        exhaustion: bool
    ) -> str:
        """Generate trading recommendation."""
        recommendations = []
        
        if active_divergence:
            recommendations.append(active_divergence.trading_signal)
        
        if delta_trend == "accumulation":
            recommendations.append("DELTA: Accumulation in progress - bullish bias")
        elif delta_trend == "distribution":
            recommendations.append("DELTA: Distribution in progress - bearish bias")
        
        if absorption:
            recommendations.append("ABSORPTION: Strong hands absorbing pressure - reversal likely")
        
        if exhaustion:
            recommendations.append("EXHAUSTION: Trend losing momentum - prepare for reversal")
        
        if not recommendations:
            recommendations.append("NEUTRAL: No significant delta signals")
        
        return " | ".join(recommendations)
    
    def _calculate_confidence(
        self,
        divergences: List[Divergence],
        delta_trend: str,
        absorption: bool
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        if divergences:
            confidence += 0.2
            # Strong divergence adds more confidence
            if any(d.strength in [DivergenceStrength.STRONG, DivergenceStrength.EXTREME] 
                   for d in divergences):
                confidence += 0.1
        
        if delta_trend != "neutral":
            confidence += 0.1
        
        if absorption:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_empty_result(self) -> DeltaAnalysisResult:
        """Create empty result for insufficient data."""
        return DeltaAnalysisResult(
            current_delta=DeltaBar(
                timestamp=datetime.now(),
                delta=0, cumulative_delta=0,
                buy_volume=0, sell_volume=0,
                total_volume=0, delta_percentage=0
            ),
            cumulative_delta=0,
            delta_trend="neutral",
            divergences=[],
            active_divergence=None,
            delta_momentum=0,
            absorption_detected=False,
            exhaustion_detected=False,
            trading_recommendation="Insufficient data",
            confidence=0
        )
