"""
Skill #1: Fractal Market Analysis
=================================

Detects self-similar patterns across multiple timeframes using fractal geometry.
Identifies fractal highs/lows, fractal dimensions, and multi-scale patterns.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FractalType(Enum):
    """Types of fractal patterns."""
    UP = "up"  # Fractal high (reversal down)
    DOWN = "down"  # Fractal low (reversal up)
    NEUTRAL = "neutral"


class FractalStrength(Enum):
    """Strength of fractal signal."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class FractalPoint:
    """Represents a detected fractal point."""
    timestamp: datetime
    price: float
    fractal_type: FractalType
    strength: FractalStrength
    timeframe: str
    bars_left: int = 2  # Bars to left of fractal
    bars_right: int = 2  # Bars to right of fractal
    confirmed: bool = False
    index: int = 0


@dataclass
class FractalDimension:
    """Fractal dimension measurement."""
    value: float  # 1.0 = trending, 1.5 = random, 2.0 = mean-reverting
    interpretation: str
    confidence: float
    sample_size: int


@dataclass
class MultiTimeframeFractal:
    """Fractal alignment across timeframes."""
    aligned_direction: Optional[str]  # 'bullish', 'bearish', None
    timeframes_aligned: List[str]
    alignment_score: float  # 0-1
    fractals: Dict[str, List[FractalPoint]]


@dataclass
class FractalAnalysisResult:
    """Complete fractal analysis result."""
    fractals: List[FractalPoint]
    fractal_dimension: FractalDimension
    multi_timeframe: MultiTimeframeFractal
    support_levels: List[float]
    resistance_levels: List[float]
    current_trend: str
    trend_strength: float
    next_likely_fractal: Optional[FractalType]
    trading_bias: str  # 'long', 'short', 'neutral'
    confidence: float


class FractalAnalyzer:
    """
    Advanced Fractal Market Analysis System.
    
    Detects Williams fractals, calculates fractal dimensions,
    and identifies self-similar patterns across timeframes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.default_bars_left = self.config.get('bars_left', 2)
        self.default_bars_right = self.config.get('bars_right', 2)
        self.min_fractal_distance = self.config.get('min_fractal_distance', 5)
        self.fractal_history: Dict[str, List[FractalPoint]] = {}
        self.dimension_window = self.config.get('dimension_window', 100)
        
        # Timeframe hierarchy for multi-timeframe analysis
        self.timeframe_hierarchy = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
        
        logger.info("FractalAnalyzer initialized")
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        timestamps: List[datetime],
        timeframe: str = '1h'
    ) -> FractalAnalysisResult:
        """
        Perform complete fractal analysis.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            timestamps: List of timestamps
            timeframe: Timeframe of the data
            
        Returns:
            FractalAnalysisResult with all analysis
        """
        # Detect fractals
        fractals = self._detect_fractals(highs, lows, timestamps, timeframe)
        
        # Calculate fractal dimension
        fractal_dimension = self._calculate_fractal_dimension(closes)
        
        # Get support/resistance from fractals
        support_levels = self._get_support_levels(fractals, closes[-1])
        resistance_levels = self._get_resistance_levels(fractals, closes[-1])
        
        # Determine trend from fractals
        current_trend, trend_strength = self._determine_trend(fractals)
        
        # Predict next fractal
        next_likely_fractal = self._predict_next_fractal(fractals, closes)
        
        # Calculate trading bias
        trading_bias = self._calculate_trading_bias(
            fractals, fractal_dimension, current_trend
        )
        
        # Multi-timeframe placeholder (would need data from other timeframes)
        multi_timeframe = MultiTimeframeFractal(
            aligned_direction=None,
            timeframes_aligned=[timeframe],
            alignment_score=0.5,
            fractals={timeframe: fractals}
        )
        
        # Store fractals for history
        self.fractal_history[timeframe] = fractals
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(
            fractals, fractal_dimension, trend_strength
        )
        
        return FractalAnalysisResult(
            fractals=fractals,
            fractal_dimension=fractal_dimension,
            multi_timeframe=multi_timeframe,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            current_trend=current_trend,
            trend_strength=trend_strength,
            next_likely_fractal=next_likely_fractal,
            trading_bias=trading_bias,
            confidence=confidence
        )
    
    def _detect_fractals(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        timestamps: List[datetime],
        timeframe: str
    ) -> List[FractalPoint]:
        """Detect Williams fractals in price data."""
        fractals = []
        n = len(highs)
        bars_left = self.default_bars_left
        bars_right = self.default_bars_right
        
        for i in range(bars_left, n - bars_right):
            # Check for fractal high (up fractal)
            is_fractal_high = True
            for j in range(1, bars_left + 1):
                if highs[i] <= highs[i - j]:
                    is_fractal_high = False
                    break
            if is_fractal_high:
                for j in range(1, bars_right + 1):
                    if highs[i] <= highs[i + j]:
                        is_fractal_high = False
                        break
            
            if is_fractal_high:
                strength = self._calculate_fractal_strength(
                    highs, i, bars_left, bars_right, is_high=True
                )
                fractals.append(FractalPoint(
                    timestamp=timestamps[i],
                    price=highs[i],
                    fractal_type=FractalType.UP,
                    strength=strength,
                    timeframe=timeframe,
                    bars_left=bars_left,
                    bars_right=bars_right,
                    confirmed=True,
                    index=i
                ))
            
            # Check for fractal low (down fractal)
            is_fractal_low = True
            for j in range(1, bars_left + 1):
                if lows[i] >= lows[i - j]:
                    is_fractal_low = False
                    break
            if is_fractal_low:
                for j in range(1, bars_right + 1):
                    if lows[i] >= lows[i + j]:
                        is_fractal_low = False
                        break
            
            if is_fractal_low:
                strength = self._calculate_fractal_strength(
                    lows, i, bars_left, bars_right, is_high=False
                )
                fractals.append(FractalPoint(
                    timestamp=timestamps[i],
                    price=lows[i],
                    fractal_type=FractalType.DOWN,
                    strength=strength,
                    timeframe=timeframe,
                    bars_left=bars_left,
                    bars_right=bars_right,
                    confirmed=True,
                    index=i
                ))
        
        # Sort by timestamp
        fractals.sort(key=lambda x: x.timestamp)
        
        return fractals
    
    def _calculate_fractal_strength(
        self,
        prices: np.ndarray,
        index: int,
        bars_left: int,
        bars_right: int,
        is_high: bool
    ) -> FractalStrength:
        """Calculate the strength of a fractal point."""
        # Calculate how much the fractal stands out
        window = prices[max(0, index - bars_left * 2):min(len(prices), index + bars_right * 2 + 1)]
        
        if len(window) < 3:
            return FractalStrength.WEAK
        
        fractal_price = prices[index]
        
        if is_high:
            prominence = (fractal_price - np.mean(window)) / (np.std(window) + 1e-10)
        else:
            prominence = (np.mean(window) - fractal_price) / (np.std(window) + 1e-10)
        
        if prominence > 2.0:
            return FractalStrength.VERY_STRONG
        elif prominence > 1.5:
            return FractalStrength.STRONG
        elif prominence > 1.0:
            return FractalStrength.MODERATE
        else:
            return FractalStrength.WEAK
    
    def _calculate_fractal_dimension(self, closes: np.ndarray) -> FractalDimension:
        """
        Calculate fractal dimension using box-counting method.
        
        D ≈ 1.0: Trending market
        D ≈ 1.5: Random walk
        D ≈ 2.0: Mean-reverting market
        """
        if len(closes) < self.dimension_window:
            return FractalDimension(
                value=1.5,
                interpretation="Insufficient data",
                confidence=0.0,
                sample_size=len(closes)
            )
        
        # Use recent data
        data = closes[-self.dimension_window:]
        
        # Normalize data
        data_norm = (data - np.min(data)) / (np.max(data) - np.min(data) + 1e-10)
        
        # Box-counting method
        box_sizes = [2, 4, 8, 16, 32]
        box_counts = []
        
        for box_size in box_sizes:
            if box_size >= len(data_norm):
                continue
            
            count = 0
            for i in range(0, len(data_norm) - box_size, box_size):
                segment = data_norm[i:i + box_size]
                # Count boxes needed to cover the segment
                y_range = np.max(segment) - np.min(segment)
                boxes_needed = max(1, int(np.ceil(y_range * len(data_norm) / box_size)))
                count += boxes_needed
            
            if count > 0:
                box_counts.append((np.log(1 / box_size), np.log(count)))
        
        if len(box_counts) < 2:
            return FractalDimension(
                value=1.5,
                interpretation="Insufficient box counts",
                confidence=0.0,
                sample_size=len(closes)
            )
        
        # Linear regression to find dimension
        x = np.array([bc[0] for bc in box_counts])
        y = np.array([bc[1] for bc in box_counts])
        
        # Fit line
        slope, intercept = np.polyfit(x, y, 1)
        dimension = slope
        
        # Clamp to valid range
        dimension = max(1.0, min(2.0, dimension))
        
        # Calculate R-squared for confidence
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        
        # Interpret dimension
        if dimension < 1.3:
            interpretation = "Trending market - follow the trend"
        elif dimension < 1.7:
            interpretation = "Random walk - be cautious"
        else:
            interpretation = "Mean-reverting - fade extremes"
        
        return FractalDimension(
            value=dimension,
            interpretation=interpretation,
            confidence=max(0, r_squared),
            sample_size=len(data)
        )
    
    def _get_support_levels(
        self,
        fractals: List[FractalPoint],
        current_price: float
    ) -> List[float]:
        """Extract support levels from down fractals below current price."""
        supports = []
        
        for fractal in fractals:
            if fractal.fractal_type == FractalType.DOWN and fractal.price < current_price:
                supports.append(fractal.price)
        
        # Remove duplicates and sort descending (closest first)
        supports = list(set(supports))
        supports.sort(reverse=True)
        
        # Return top 5 support levels
        return supports[:5]
    
    def _get_resistance_levels(
        self,
        fractals: List[FractalPoint],
        current_price: float
    ) -> List[float]:
        """Extract resistance levels from up fractals above current price."""
        resistances = []
        
        for fractal in fractals:
            if fractal.fractal_type == FractalType.UP and fractal.price > current_price:
                resistances.append(fractal.price)
        
        # Remove duplicates and sort ascending (closest first)
        resistances = list(set(resistances))
        resistances.sort()
        
        # Return top 5 resistance levels
        return resistances[:5]
    
    def _determine_trend(
        self,
        fractals: List[FractalPoint]
    ) -> Tuple[str, float]:
        """Determine trend direction and strength from fractal sequence."""
        if len(fractals) < 4:
            return "neutral", 0.0
        
        # Get recent fractals
        recent = fractals[-10:]
        
        # Separate highs and lows
        highs = [f for f in recent if f.fractal_type == FractalType.UP]
        lows = [f for f in recent if f.fractal_type == FractalType.DOWN]
        
        if len(highs) < 2 or len(lows) < 2:
            return "neutral", 0.0
        
        # Check for higher highs and higher lows (uptrend)
        higher_highs = all(highs[i].price <= highs[i + 1].price for i in range(len(highs) - 1))
        higher_lows = all(lows[i].price <= lows[i + 1].price for i in range(len(lows) - 1))
        
        # Check for lower highs and lower lows (downtrend)
        lower_highs = all(highs[i].price >= highs[i + 1].price for i in range(len(highs) - 1))
        lower_lows = all(lows[i].price >= lows[i + 1].price for i in range(len(lows) - 1))
        
        if higher_highs and higher_lows:
            # Calculate trend strength
            high_diff = (highs[-1].price - highs[0].price) / highs[0].price
            low_diff = (lows[-1].price - lows[0].price) / lows[0].price
            strength = min(1.0, (abs(high_diff) + abs(low_diff)) * 10)
            return "uptrend", strength
        
        elif lower_highs and lower_lows:
            high_diff = (highs[0].price - highs[-1].price) / highs[0].price
            low_diff = (lows[0].price - lows[-1].price) / lows[0].price
            strength = min(1.0, (abs(high_diff) + abs(low_diff)) * 10)
            return "downtrend", strength
        
        else:
            return "ranging", 0.3
    
    def _predict_next_fractal(
        self,
        fractals: List[FractalPoint],
        closes: np.ndarray
    ) -> Optional[FractalType]:
        """Predict the most likely next fractal type."""
        if len(fractals) < 2:
            return None
        
        # Look at the pattern of recent fractals
        recent = fractals[-5:]
        
        # Count alternation
        alternating = 0
        for i in range(len(recent) - 1):
            if recent[i].fractal_type != recent[i + 1].fractal_type:
                alternating += 1
        
        last_fractal = recent[-1]
        
        # If highly alternating, predict opposite
        if alternating >= len(recent) - 2:
            if last_fractal.fractal_type == FractalType.UP:
                return FractalType.DOWN
            else:
                return FractalType.UP
        
        # Otherwise, look at price position
        current_price = closes[-1]
        avg_price = np.mean(closes[-20:])
        
        if current_price > avg_price * 1.02:
            return FractalType.UP  # Likely to form a high
        elif current_price < avg_price * 0.98:
            return FractalType.DOWN  # Likely to form a low
        
        return None
    
    def _calculate_trading_bias(
        self,
        fractals: List[FractalPoint],
        dimension: FractalDimension,
        trend: str
    ) -> str:
        """Calculate overall trading bias."""
        # Weight factors
        trend_weight = 0.5
        dimension_weight = 0.3
        fractal_weight = 0.2
        
        score = 0.0
        
        # Trend contribution
        if trend == "uptrend":
            score += trend_weight
        elif trend == "downtrend":
            score -= trend_weight
        
        # Dimension contribution (mean-reverting suggests fade, trending suggests follow)
        if dimension.value < 1.3:
            # Trending - go with trend
            if trend == "uptrend":
                score += dimension_weight
            elif trend == "downtrend":
                score -= dimension_weight
        elif dimension.value > 1.7:
            # Mean-reverting - fade trend
            if trend == "uptrend":
                score -= dimension_weight * 0.5
            elif trend == "downtrend":
                score += dimension_weight * 0.5
        
        # Recent fractal contribution
        if fractals:
            last_fractal = fractals[-1]
            if last_fractal.fractal_type == FractalType.DOWN:
                score += fractal_weight  # Potential bounce
            elif last_fractal.fractal_type == FractalType.UP:
                score -= fractal_weight  # Potential reversal
        
        # Convert score to bias
        if score > 0.2:
            return "long"
        elif score < -0.2:
            return "short"
        else:
            return "neutral"
    
    def _calculate_confidence(
        self,
        fractals: List[FractalPoint],
        dimension: FractalDimension,
        trend_strength: float
    ) -> float:
        """Calculate overall confidence in the analysis."""
        confidence = 0.5  # Base confidence
        
        # More fractals = more confidence
        if len(fractals) >= 10:
            confidence += 0.1
        elif len(fractals) >= 5:
            confidence += 0.05
        
        # Strong fractals = more confidence
        strong_fractals = sum(
            1 for f in fractals
            if f.strength in [FractalStrength.STRONG, FractalStrength.VERY_STRONG]
        )
        confidence += min(0.15, strong_fractals * 0.03)
        
        # Good dimension fit = more confidence
        confidence += dimension.confidence * 0.15
        
        # Strong trend = more confidence
        confidence += trend_strength * 0.1
        
        return min(1.0, confidence)
    
    def add_multi_timeframe_data(
        self,
        timeframe: str,
        fractals: List[FractalPoint]
    ):
        """Add fractal data from another timeframe for MTF analysis."""
        self.fractal_history[timeframe] = fractals
    
    def get_multi_timeframe_alignment(self) -> MultiTimeframeFractal:
        """Analyze fractal alignment across all stored timeframes."""
        if len(self.fractal_history) < 2:
            return MultiTimeframeFractal(
                aligned_direction=None,
                timeframes_aligned=[],
                alignment_score=0.0,
                fractals=self.fractal_history
            )
        
        bullish_count = 0
        bearish_count = 0
        aligned_timeframes = []
        
        for tf, fractals in self.fractal_history.items():
            if not fractals:
                continue
            
            # Get last fractal
            last = fractals[-1]
            
            if last.fractal_type == FractalType.DOWN:
                bullish_count += 1
                aligned_timeframes.append((tf, 'bullish'))
            elif last.fractal_type == FractalType.UP:
                bearish_count += 1
                aligned_timeframes.append((tf, 'bearish'))
        
        total = bullish_count + bearish_count
        if total == 0:
            return MultiTimeframeFractal(
                aligned_direction=None,
                timeframes_aligned=[],
                alignment_score=0.0,
                fractals=self.fractal_history
            )
        
        if bullish_count > bearish_count:
            direction = 'bullish'
            score = bullish_count / total
            aligned = [tf for tf, d in aligned_timeframes if d == 'bullish']
        else:
            direction = 'bearish'
            score = bearish_count / total
            aligned = [tf for tf, d in aligned_timeframes if d == 'bearish']
        
        return MultiTimeframeFractal(
            aligned_direction=direction,
            timeframes_aligned=aligned,
            alignment_score=score,
            fractals=self.fractal_history
        )
