"""
Signal Enhancement System
=========================

Improves signal accuracy through:
1. Multi-timeframe confirmation
2. Volume confirmation
3. Market structure validation
4. Trend strength filtering

Target: Increase win rate from ~55% to 65%+
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction classification"""
    STRONG_UP = "strong_up"
    UP = "up"
    NEUTRAL = "neutral"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1


@dataclass
class TimeframeAnalysis:
    """Analysis result for a single timeframe"""
    timeframe: str
    trend: TrendDirection
    strength: float  # 0-1
    ema_alignment: bool
    price_above_ema: bool
    momentum: float
    volume_trend: str  # 'increasing', 'decreasing', 'stable'


@dataclass
class SignalEnhancementResult:
    """Result of signal enhancement analysis"""
    original_signal: str
    enhanced_signal: str
    should_take: bool
    confidence: float
    reasons: List[str]
    timeframe_alignment: Dict[str, TrendDirection]
    volume_confirmed: bool
    structure_valid: bool
    trend_strength: float
    
    def to_dict(self) -> Dict:
        return {
            'original_signal': self.original_signal,
            'enhanced_signal': self.enhanced_signal,
            'should_take': self.should_take,
            'confidence': self.confidence,
            'reasons': self.reasons,
            'volume_confirmed': self.volume_confirmed,
            'structure_valid': self.structure_valid,
            'trend_strength': self.trend_strength,
        }


class MultiTimeframeAnalyzer:
    """
    Analyzes multiple timeframes for signal confirmation.
    
    PRINCIPLE: Only trade when multiple timeframes agree.
    """
    
    # Timeframe hierarchy (higher = more important)
    TIMEFRAMES = {
        'M1': 1,
        'M5': 2,
        'M15': 3,
        'M30': 4,
        'H1': 5,
        'H4': 6,
        'D1': 7,
        'W1': 8,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Timeframes to analyze (default: M15, H1, H4)
        self.analysis_timeframes = self.config.get('timeframes', ['M15', 'H1', 'H4'])
        
        # Minimum alignment required (default: all must agree)
        self.min_alignment = self.config.get('min_alignment', len(self.analysis_timeframes))
        
        # EMA periods for trend detection
        self.fast_ema = self.config.get('fast_ema', 20)
        self.slow_ema = self.config.get('slow_ema', 50)
        self.trend_ema = self.config.get('trend_ema', 200)
        
        logger.info(f"MultiTimeframeAnalyzer initialized: {self.analysis_timeframes}")
    
    def analyze_timeframe(
        self,
        prices: np.ndarray,
        timeframe: str
    ) -> TimeframeAnalysis:
        """Analyze a single timeframe"""
        if len(prices) < self.trend_ema:
            return TimeframeAnalysis(
                timeframe=timeframe,
                trend=TrendDirection.NEUTRAL,
                strength=0.0,
                ema_alignment=False,
                price_above_ema=False,
                momentum=0.0,
                volume_trend='stable'
            )
        
        # Calculate EMAs
        fast_ema = self._calculate_ema(prices, self.fast_ema)
        slow_ema = self._calculate_ema(prices, self.slow_ema)
        trend_ema = self._calculate_ema(prices, self.trend_ema)
        
        current_price = prices[-1]
        
        # Determine trend direction
        ema_alignment = fast_ema[-1] > slow_ema[-1] > trend_ema[-1]
        ema_alignment_down = fast_ema[-1] < slow_ema[-1] < trend_ema[-1]
        
        price_above_ema = current_price > trend_ema[-1]
        
        # Calculate momentum (rate of change)
        momentum = (prices[-1] - prices[-20]) / prices[-20] if len(prices) >= 20 else 0
        
        # Determine trend
        if ema_alignment and price_above_ema:
            if momentum > 0.02:
                trend = TrendDirection.STRONG_UP
                strength = min(1.0, abs(momentum) * 20)
            else:
                trend = TrendDirection.UP
                strength = 0.6
        elif ema_alignment_down and not price_above_ema:
            if momentum < -0.02:
                trend = TrendDirection.STRONG_DOWN
                strength = min(1.0, abs(momentum) * 20)
            else:
                trend = TrendDirection.DOWN
                strength = 0.6
        else:
            trend = TrendDirection.NEUTRAL
            strength = 0.3
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            strength=strength,
            ema_alignment=ema_alignment or ema_alignment_down,
            price_above_ema=price_above_ema,
            momentum=momentum,
            volume_trend='stable'  # Would need volume data
        )
    
    def check_alignment(
        self,
        signal: str,
        timeframe_data: Dict[str, np.ndarray]
    ) -> Tuple[bool, Dict[str, TrendDirection], float]:
        """
        Check if multiple timeframes align with the signal.
        
        Returns:
            Tuple of (is_aligned, timeframe_trends, alignment_score)
        """
        analyses = {}
        aligned_count = 0
        total_strength = 0.0
        
        for tf in self.analysis_timeframes:
            if tf in timeframe_data:
                analysis = self.analyze_timeframe(timeframe_data[tf], tf)
                analyses[tf] = analysis.trend
                
                # Check alignment with signal
                if signal == 'BUY':
                    if analysis.trend in [TrendDirection.UP, TrendDirection.STRONG_UP]:
                        aligned_count += 1
                        total_strength += analysis.strength
                elif signal == 'SELL':
                    if analysis.trend in [TrendDirection.DOWN, TrendDirection.STRONG_DOWN]:
                        aligned_count += 1
                        total_strength += analysis.strength
        
        is_aligned = aligned_count >= self.min_alignment
        alignment_score = total_strength / len(self.analysis_timeframes) if self.analysis_timeframes else 0
        
        return is_aligned, analyses, alignment_score
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices
        
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema


class VolumeConfirmation:
    """
    Confirms signals with volume analysis.
    
    PRINCIPLE: Strong moves should be accompanied by strong volume.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Volume threshold (default: 1.2x average)
        self.volume_threshold = self.config.get('volume_threshold', 1.2)
        
        # Lookback period for average volume
        self.lookback = self.config.get('lookback', 20)
        
        logger.info(f"VolumeConfirmation initialized: threshold={self.volume_threshold}x")
    
    def confirm(
        self,
        signal: str,
        current_volume: float,
        volume_history: np.ndarray
    ) -> Tuple[bool, str]:
        """
        Check if volume confirms the signal.
        
        Returns:
            Tuple of (is_confirmed, reason)
        """
        if len(volume_history) < self.lookback:
            return True, "Insufficient volume history"
        
        avg_volume = np.mean(volume_history[-self.lookback:])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        if volume_ratio >= self.volume_threshold:
            return True, f"Volume confirmed ({volume_ratio:.2f}x average)"
        elif volume_ratio >= 1.0:
            return True, f"Volume acceptable ({volume_ratio:.2f}x average)"
        else:
            return False, f"Low volume ({volume_ratio:.2f}x average) - signal weak"
    
    def get_volume_trend(self, volume_history: np.ndarray) -> str:
        """Determine if volume is increasing, decreasing, or stable"""
        if len(volume_history) < 10:
            return 'stable'
        
        recent = np.mean(volume_history[-5:])
        older = np.mean(volume_history[-10:-5])
        
        if recent > older * 1.2:
            return 'increasing'
        elif recent < older * 0.8:
            return 'decreasing'
        return 'stable'


class MarketStructureValidator:
    """
    Validates market structure for signal quality.
    
    Checks:
    - Higher highs / Lower lows
    - Support/Resistance levels
    - Trend structure integrity
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Swing detection parameters
        self.swing_lookback = self.config.get('swing_lookback', 5)
        
        logger.info("MarketStructureValidator initialized")
    
    def validate(
        self,
        signal: str,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> Tuple[bool, str, float]:
        """
        Validate market structure supports the signal.
        
        Returns:
            Tuple of (is_valid, reason, structure_score)
        """
        if len(closes) < 50:
            return True, "Insufficient data for structure analysis", 0.5
        
        # Find swing highs and lows
        swing_highs = self._find_swing_highs(highs)
        swing_lows = self._find_swing_lows(lows)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return True, "Insufficient swings for analysis", 0.5
        
        # Check structure
        if signal == 'BUY':
            # For buy: want higher lows (uptrend structure)
            recent_lows = swing_lows[-3:]
            if len(recent_lows) >= 2:
                higher_lows = all(recent_lows[i] > recent_lows[i-1] * 0.998 
                                  for i in range(1, len(recent_lows)))
                if higher_lows:
                    return True, "Uptrend structure confirmed (higher lows)", 0.8
                else:
                    return False, "No higher lows - weak uptrend structure", 0.3
        
        elif signal == 'SELL':
            # For sell: want lower highs (downtrend structure)
            recent_highs = swing_highs[-3:]
            if len(recent_highs) >= 2:
                lower_highs = all(recent_highs[i] < recent_highs[i-1] * 1.002 
                                  for i in range(1, len(recent_highs)))
                if lower_highs:
                    return True, "Downtrend structure confirmed (lower highs)", 0.8
                else:
                    return False, "No lower highs - weak downtrend structure", 0.3
        
        return True, "Structure neutral", 0.5
    
    def _find_swing_highs(self, highs: np.ndarray) -> List[float]:
        """Find swing high points"""
        swings = []
        for i in range(self.swing_lookback, len(highs) - self.swing_lookback):
            if highs[i] == max(highs[i-self.swing_lookback:i+self.swing_lookback+1]):
                swings.append(highs[i])
        return swings
    
    def _find_swing_lows(self, lows: np.ndarray) -> List[float]:
        """Find swing low points"""
        swings = []
        for i in range(self.swing_lookback, len(lows) - self.swing_lookback):
            if lows[i] == min(lows[i-self.swing_lookback:i+self.swing_lookback+1]):
                swings.append(lows[i])
        return swings


class SignalEnhancer:
    """
    Master signal enhancement system.
    
    Combines all enhancement techniques to improve signal quality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.mtf_analyzer = MultiTimeframeAnalyzer(self.config.get('mtf', {}))
        self.volume_confirm = VolumeConfirmation(self.config.get('volume', {}))
        self.structure_validator = MarketStructureValidator(self.config.get('structure', {}))
        
        # Enhancement thresholds
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.require_volume = self.config.get('require_volume', True)
        self.require_structure = self.config.get('require_structure', True)
        
        logger.info("SignalEnhancer initialized - All enhancement systems active")
    
    def enhance_signal(
        self,
        signal: str,
        symbol: str,
        timeframe_data: Dict[str, np.ndarray],
        volume_data: Optional[np.ndarray] = None,
        current_volume: Optional[float] = None,
        ohlc_data: Optional[Dict[str, np.ndarray]] = None
    ) -> SignalEnhancementResult:
        """
        Enhance and validate a trading signal.
        
        Args:
            signal: Original signal ('BUY', 'SELL', 'HOLD')
            symbol: Trading symbol
            timeframe_data: Dict of timeframe -> price array
            volume_data: Historical volume array
            current_volume: Current bar volume
            ohlc_data: Dict with 'high', 'low', 'close' arrays
        
        Returns:
            SignalEnhancementResult with enhanced signal and analysis
        """
        reasons = []
        confidence = 0.5
        
        # 1. Multi-timeframe analysis
        is_aligned, tf_trends, alignment_score = self.mtf_analyzer.check_alignment(
            signal, timeframe_data
        )
        
        if is_aligned:
            reasons.append(f"Multi-timeframe aligned ({alignment_score:.2f})")
            confidence += 0.2
        else:
            reasons.append("Multi-timeframe NOT aligned")
            confidence -= 0.2
        
        # 2. Volume confirmation
        volume_confirmed = True
        if volume_data is not None and current_volume is not None:
            volume_confirmed, vol_reason = self.volume_confirm.confirm(
                signal, current_volume, volume_data
            )
            reasons.append(vol_reason)
            if volume_confirmed:
                confidence += 0.1
            else:
                confidence -= 0.15
        
        # 3. Market structure validation
        structure_valid = True
        structure_score = 0.5
        if ohlc_data is not None:
            structure_valid, struct_reason, structure_score = self.structure_validator.validate(
                signal,
                ohlc_data.get('high', np.array([])),
                ohlc_data.get('low', np.array([])),
                ohlc_data.get('close', np.array([]))
            )
            reasons.append(struct_reason)
            confidence += (structure_score - 0.5) * 0.4
        
        # Calculate final confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # Determine if signal should be taken
        should_take = (
            confidence >= self.min_confidence and
            is_aligned and
            (not self.require_volume or volume_confirmed) and
            (not self.require_structure or structure_valid)
        )
        
        # Determine enhanced signal
        if should_take:
            enhanced_signal = signal
        else:
            enhanced_signal = 'HOLD'
            reasons.append(f"Signal filtered (confidence: {confidence:.2f})")
        
        return SignalEnhancementResult(
            original_signal=signal,
            enhanced_signal=enhanced_signal,
            should_take=should_take,
            confidence=confidence,
            reasons=reasons,
            timeframe_alignment=tf_trends,
            volume_confirmed=volume_confirmed,
            structure_valid=structure_valid,
            trend_strength=alignment_score
        )
    
    def get_trend_strength(
        self,
        timeframe_data: Dict[str, np.ndarray]
    ) -> Tuple[TrendDirection, float]:
        """Get overall trend direction and strength"""
        if not timeframe_data:
            return TrendDirection.NEUTRAL, 0.0
        
        # Use highest timeframe available
        for tf in ['H4', 'H1', 'M30', 'M15']:
            if tf in timeframe_data:
                analysis = self.mtf_analyzer.analyze_timeframe(timeframe_data[tf], tf)
                return analysis.trend, analysis.strength
        
        return TrendDirection.NEUTRAL, 0.0
