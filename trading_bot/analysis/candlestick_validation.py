"""
Candlestick Pattern Validation Module.

This module implements:
- Candlestick pattern detection
- Pattern validation and scoring
- Context-aware pattern analysis
- Pattern reliability metrics
- Historical pattern performance
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of candlestick patterns."""
    # Single candle patterns
    DOJI = "doji"
    HAMMER = "hammer"
    INVERTED_HAMMER = "inverted_hammer"
    HANGING_MAN = "hanging_man"
    SHOOTING_STAR = "shooting_star"
    MARUBOZU = "marubozu"
    SPINNING_TOP = "spinning_top"
    
    # Double candle patterns
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    HARAMI_BULLISH = "harami_bullish"
    HARAMI_BEARISH = "harami_bearish"
    PIERCING_LINE = "piercing_line"
    DARK_CLOUD_COVER = "dark_cloud_cover"
    TWEEZER_TOP = "tweezer_top"
    TWEEZER_BOTTOM = "tweezer_bottom"
    
    # Triple candle patterns
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"
    THREE_INSIDE_UP = "three_inside_up"
    THREE_INSIDE_DOWN = "three_inside_down"
    
    # Continuation patterns
    RISING_THREE = "rising_three"
    FALLING_THREE = "falling_three"


class PatternSignal(Enum):
    """Pattern signal direction."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PatternStrength(Enum):
    """Pattern strength levels."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"


@dataclass
class CandleMetrics:
    """Metrics for a single candle."""
    body_size: float
    upper_wick: float
    lower_wick: float
    total_range: float
    body_ratio: float  # Body / Total range
    is_bullish: bool
    is_doji: bool


@dataclass
class DetectedPattern:
    """A detected candlestick pattern."""
    pattern_type: PatternType
    signal: PatternSignal
    strength: PatternStrength
    start_index: int
    end_index: int
    confidence: float
    validation_score: float
    context_score: float
    price_at_detection: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PatternValidation:
    """Validation result for a pattern."""
    is_valid: bool
    validation_score: float  # 0-1
    context_score: float  # 0-1
    volume_confirmation: bool
    trend_alignment: bool
    support_resistance_proximity: bool
    reasons: List[str]


@dataclass
class PatternPerformance:
    """Historical performance of a pattern type."""
    pattern_type: PatternType
    total_occurrences: int
    success_rate: float
    avg_move_percent: float
    avg_time_to_target: int
    best_contexts: List[str]
    worst_contexts: List[str]


class CandleAnalyzer:
    """
    Analyzes individual candles.
    """
    
    def __init__(
        self,
        doji_threshold: float = 0.1,
        small_body_threshold: float = 0.3
    ):
        try:
            self.doji_threshold = doji_threshold
            self.small_body_threshold = small_body_threshold
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def analyze_candle(
        self,
        open_p: float,
        high: float,
        low: float,
        close: float
    ) -> CandleMetrics:
        """Analyze a single candle."""
        try:
            body_size = abs(close - open_p)
            upper_wick = high - max(open_p, close)
            lower_wick = min(open_p, close) - low
            total_range = high - low
        
            if total_range > 0:
                body_ratio = body_size / total_range
            else:
                body_ratio = 0
        
            is_bullish = close > open_p
            is_doji = body_ratio < self.doji_threshold
        
            return CandleMetrics(
                body_size=body_size,
                upper_wick=upper_wick,
                lower_wick=lower_wick,
                total_range=total_range,
                body_ratio=body_ratio,
                is_bullish=is_bullish,
                is_doji=is_doji
            )
        except Exception as e:
            logger.error(f"Error in analyze_candle: {e}")
            raise
    
    def is_hammer(self, metrics: CandleMetrics) -> bool:
        """Check if candle is a hammer."""
        try:
            if metrics.total_range == 0:
                return False
        
            lower_wick_ratio = metrics.lower_wick / metrics.total_range
            upper_wick_ratio = metrics.upper_wick / metrics.total_range
        
            return (
                lower_wick_ratio >= 0.6 and
                upper_wick_ratio <= 0.1 and
                metrics.body_ratio <= 0.3
            )
        except Exception as e:
            logger.error(f"Error in is_hammer: {e}")
            raise
    
    def is_shooting_star(self, metrics: CandleMetrics) -> bool:
        """Check if candle is a shooting star."""
        try:
            if metrics.total_range == 0:
                return False
        
            upper_wick_ratio = metrics.upper_wick / metrics.total_range
            lower_wick_ratio = metrics.lower_wick / metrics.total_range
        
            return (
                upper_wick_ratio >= 0.6 and
                lower_wick_ratio <= 0.1 and
                metrics.body_ratio <= 0.3
            )
        except Exception as e:
            logger.error(f"Error in is_shooting_star: {e}")
            raise
    
    def is_marubozu(self, metrics: CandleMetrics) -> bool:
        """Check if candle is a marubozu (no wicks)."""
        try:
            if metrics.total_range == 0:
                return False
        
            wick_ratio = (metrics.upper_wick + metrics.lower_wick) / metrics.total_range
            return wick_ratio <= 0.05 and metrics.body_ratio >= 0.9
        except Exception as e:
            logger.error(f"Error in is_marubozu: {e}")
            raise


class PatternDetector:
    """
    Detects candlestick patterns.
    """
    
    def __init__(self):
        try:
            self.candle_analyzer = CandleAnalyzer()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_single_patterns(
        self,
        df: pd.DataFrame,
        index: int
    ) -> List[PatternType]:
        """Detect single candle patterns."""
        try:
            patterns = []
        
            row = df.iloc[index]
            metrics = self.candle_analyzer.analyze_candle(
                row['open'], row['high'], row['low'], row['close']
            )
        
            # Doji
            if metrics.is_doji:
                patterns.append(PatternType.DOJI)
        
            # Hammer / Hanging Man
            if self.candle_analyzer.is_hammer(metrics):
                # Need context to determine if hammer or hanging man
                patterns.append(PatternType.HAMMER)
        
            # Shooting Star / Inverted Hammer
            if self.candle_analyzer.is_shooting_star(metrics):
                patterns.append(PatternType.SHOOTING_STAR)
        
            # Marubozu
            if self.candle_analyzer.is_marubozu(metrics):
                patterns.append(PatternType.MARUBOZU)
        
            # Spinning Top
            if 0.1 < metrics.body_ratio < 0.3:
                wick_balance = abs(metrics.upper_wick - metrics.lower_wick) / (metrics.total_range + 1e-10)
                if wick_balance < 0.3:
                    patterns.append(PatternType.SPINNING_TOP)
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_single_patterns: {e}")
            raise
    
    def detect_double_patterns(
        self,
        df: pd.DataFrame,
        index: int
    ) -> List[PatternType]:
        """Detect two-candle patterns."""
        try:
            if index < 1:
                return []
        
            patterns = []
        
            curr = df.iloc[index]
            prev = df.iloc[index - 1]
        
            curr_metrics = self.candle_analyzer.analyze_candle(
                curr['open'], curr['high'], curr['low'], curr['close']
            )
            prev_metrics = self.candle_analyzer.analyze_candle(
                prev['open'], prev['high'], prev['low'], prev['close']
            )
        
            # Bullish Engulfing
            if (not prev_metrics.is_bullish and curr_metrics.is_bullish and
                curr['open'] < prev['close'] and curr['close'] > prev['open'] and
                curr_metrics.body_size > prev_metrics.body_size):
                patterns.append(PatternType.ENGULFING_BULLISH)
        
            # Bearish Engulfing
            if (prev_metrics.is_bullish and not curr_metrics.is_bullish and
                curr['open'] > prev['close'] and curr['close'] < prev['open'] and
                curr_metrics.body_size > prev_metrics.body_size):
                patterns.append(PatternType.ENGULFING_BEARISH)
        
            # Bullish Harami
            if (not prev_metrics.is_bullish and curr_metrics.is_bullish and
                curr['open'] > prev['close'] and curr['close'] < prev['open'] and
                curr_metrics.body_size < prev_metrics.body_size * 0.5):
                patterns.append(PatternType.HARAMI_BULLISH)
        
            # Bearish Harami
            if (prev_metrics.is_bullish and not curr_metrics.is_bullish and
                curr['open'] < prev['close'] and curr['close'] > prev['open'] and
                curr_metrics.body_size < prev_metrics.body_size * 0.5):
                patterns.append(PatternType.HARAMI_BEARISH)
        
            # Piercing Line
            if (not prev_metrics.is_bullish and curr_metrics.is_bullish and
                curr['open'] < prev['low'] and
                curr['close'] > (prev['open'] + prev['close']) / 2 and
                curr['close'] < prev['open']):
                patterns.append(PatternType.PIERCING_LINE)
        
            # Dark Cloud Cover
            if (prev_metrics.is_bullish and not curr_metrics.is_bullish and
                curr['open'] > prev['high'] and
                curr['close'] < (prev['open'] + prev['close']) / 2 and
                curr['close'] > prev['open']):
                patterns.append(PatternType.DARK_CLOUD_COVER)
        
            # Tweezer Bottom
            if (abs(curr['low'] - prev['low']) / prev['low'] < 0.001 and
                not prev_metrics.is_bullish and curr_metrics.is_bullish):
                patterns.append(PatternType.TWEEZER_BOTTOM)
        
            # Tweezer Top
            if (abs(curr['high'] - prev['high']) / prev['high'] < 0.001 and
                prev_metrics.is_bullish and not curr_metrics.is_bullish):
                patterns.append(PatternType.TWEEZER_TOP)
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_double_patterns: {e}")
            raise
    
    def detect_triple_patterns(
        self,
        df: pd.DataFrame,
        index: int
    ) -> List[PatternType]:
        """Detect three-candle patterns."""
        try:
            if index < 2:
                return []
        
            patterns = []
        
            c1 = df.iloc[index - 2]
            c2 = df.iloc[index - 1]
            c3 = df.iloc[index]
        
            m1 = self.candle_analyzer.analyze_candle(c1['open'], c1['high'], c1['low'], c1['close'])
            m2 = self.candle_analyzer.analyze_candle(c2['open'], c2['high'], c2['low'], c2['close'])
            m3 = self.candle_analyzer.analyze_candle(c3['open'], c3['high'], c3['low'], c3['close'])
        
            # Morning Star
            if (not m1.is_bullish and m1.body_ratio > 0.5 and
                m2.body_ratio < 0.3 and
                m3.is_bullish and m3.body_ratio > 0.5 and
                c3['close'] > (c1['open'] + c1['close']) / 2):
                patterns.append(PatternType.MORNING_STAR)
        
            # Evening Star
            if (m1.is_bullish and m1.body_ratio > 0.5 and
                m2.body_ratio < 0.3 and
                not m3.is_bullish and m3.body_ratio > 0.5 and
                c3['close'] < (c1['open'] + c1['close']) / 2):
                patterns.append(PatternType.EVENING_STAR)
        
            # Three White Soldiers
            if (m1.is_bullish and m2.is_bullish and m3.is_bullish and
                c2['close'] > c1['close'] and c3['close'] > c2['close'] and
                c2['open'] > c1['open'] and c3['open'] > c2['open'] and
                m1.body_ratio > 0.5 and m2.body_ratio > 0.5 and m3.body_ratio > 0.5):
                patterns.append(PatternType.THREE_WHITE_SOLDIERS)
        
            # Three Black Crows
            if (not m1.is_bullish and not m2.is_bullish and not m3.is_bullish and
                c2['close'] < c1['close'] and c3['close'] < c2['close'] and
                c2['open'] < c1['open'] and c3['open'] < c2['open'] and
                m1.body_ratio > 0.5 and m2.body_ratio > 0.5 and m3.body_ratio > 0.5):
                patterns.append(PatternType.THREE_BLACK_CROWS)
        
            # Three Inside Up
            if (not m1.is_bullish and
                m2.is_bullish and c2['open'] > c1['close'] and c2['close'] < c1['open'] and
                m3.is_bullish and c3['close'] > c1['open']):
                patterns.append(PatternType.THREE_INSIDE_UP)
        
            # Three Inside Down
            if (m1.is_bullish and
                not m2.is_bullish and c2['open'] < c1['close'] and c2['close'] > c1['open'] and
                not m3.is_bullish and c3['close'] < c1['open']):
                patterns.append(PatternType.THREE_INSIDE_DOWN)
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_triple_patterns: {e}")
            raise
    
    def detect_all_patterns(
        self,
        df: pd.DataFrame,
        index: int
    ) -> List[PatternType]:
        """Detect all patterns at given index."""
        try:
            patterns = []
            patterns.extend(self.detect_single_patterns(df, index))
            patterns.extend(self.detect_double_patterns(df, index))
            patterns.extend(self.detect_triple_patterns(df, index))
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_all_patterns: {e}")
            raise


class PatternValidator:
    """
    Validates detected patterns with context.
    """
    
    def __init__(
        self,
        volume_threshold: float = 1.2,
        trend_lookback: int = 20
    ):
        try:
            self.volume_threshold = volume_threshold
            self.trend_lookback = trend_lookback
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def get_pattern_signal(self, pattern_type: PatternType) -> PatternSignal:
        """Get the expected signal direction for a pattern."""
        try:
            bullish_patterns = [
                PatternType.HAMMER, PatternType.INVERTED_HAMMER,
                PatternType.ENGULFING_BULLISH, PatternType.HARAMI_BULLISH,
                PatternType.PIERCING_LINE, PatternType.TWEEZER_BOTTOM,
                PatternType.MORNING_STAR, PatternType.THREE_WHITE_SOLDIERS,
                PatternType.THREE_INSIDE_UP, PatternType.RISING_THREE
            ]
        
            bearish_patterns = [
                PatternType.HANGING_MAN, PatternType.SHOOTING_STAR,
                PatternType.ENGULFING_BEARISH, PatternType.HARAMI_BEARISH,
                PatternType.DARK_CLOUD_COVER, PatternType.TWEEZER_TOP,
                PatternType.EVENING_STAR, PatternType.THREE_BLACK_CROWS,
                PatternType.THREE_INSIDE_DOWN, PatternType.FALLING_THREE
            ]
        
            if pattern_type in bullish_patterns:
                return PatternSignal.BULLISH
            elif pattern_type in bearish_patterns:
                return PatternSignal.BEARISH
            else:
                return PatternSignal.NEUTRAL
        except Exception as e:
            logger.error(f"Error in get_pattern_signal: {e}")
            raise
    
    def check_volume_confirmation(
        self,
        df: pd.DataFrame,
        index: int
    ) -> bool:
        """Check if volume confirms the pattern."""
        try:
            if 'volume' not in df.columns or index < 5:
                return True  # Assume confirmed if no volume data
        
            current_volume = df.iloc[index]['volume']
            avg_volume = df.iloc[index-5:index]['volume'].mean()
        
            return current_volume > avg_volume * self.volume_threshold
        except Exception as e:
            logger.error(f"Error in check_volume_confirmation: {e}")
            raise
    
    def check_trend_alignment(
        self,
        df: pd.DataFrame,
        index: int,
        signal: PatternSignal
    ) -> bool:
        """Check if pattern aligns with trend for reversal patterns."""
        try:
            if index < self.trend_lookback:
                return True
        
            close = df['close']
            trend_start = close.iloc[index - self.trend_lookback]
            trend_end = close.iloc[index]
        
            is_uptrend = trend_end > trend_start
            is_downtrend = trend_end < trend_start
        
            # Bullish reversal patterns should appear in downtrends
            if signal == PatternSignal.BULLISH:
                return is_downtrend
            # Bearish reversal patterns should appear in uptrends
            elif signal == PatternSignal.BEARISH:
                return is_uptrend
        
            return True
        except Exception as e:
            logger.error(f"Error in check_trend_alignment: {e}")
            raise
    
    def check_support_resistance(
        self,
        df: pd.DataFrame,
        index: int,
        signal: PatternSignal,
        proximity_threshold: float = 0.02
    ) -> bool:
        """Check if pattern is near support/resistance."""
        try:
            if index < 50:
                return False
        
            close = df['close'].iloc[index]
            recent_highs = df['high'].iloc[index-50:index].nlargest(5)
            recent_lows = df['low'].iloc[index-50:index].nsmallest(5)
        
            near_resistance = any(abs(close - h) / h < proximity_threshold for h in recent_highs)
            near_support = any(abs(close - l) / l < proximity_threshold for l in recent_lows)
        
            if signal == PatternSignal.BULLISH:
                return near_support
            elif signal == PatternSignal.BEARISH:
                return near_resistance
        
            return False
        except Exception as e:
            logger.error(f"Error in check_support_resistance: {e}")
            raise
    
    def validate_pattern(
        self,
        df: pd.DataFrame,
        index: int,
        pattern_type: PatternType
    ) -> PatternValidation:
        """Validate a detected pattern."""
        try:
            signal = self.get_pattern_signal(pattern_type)
            reasons = []
        
            # Check volume
            volume_confirmed = self.check_volume_confirmation(df, index)
            if volume_confirmed:
                reasons.append("Volume confirms pattern")
            else:
                reasons.append("Low volume - weak confirmation")
        
            # Check trend alignment
            trend_aligned = self.check_trend_alignment(df, index, signal)
            if trend_aligned:
                reasons.append("Pattern aligned with prior trend")
            else:
                reasons.append("Pattern not aligned with trend")
        
            # Check S/R proximity
            sr_proximity = self.check_support_resistance(df, index, signal)
            if sr_proximity:
                reasons.append("Near key support/resistance level")
        
            # Calculate scores
            validation_score = (
                (0.4 if volume_confirmed else 0.1) +
                (0.4 if trend_aligned else 0.1) +
                (0.2 if sr_proximity else 0.0)
            )
        
            context_score = (
                (0.5 if trend_aligned else 0.2) +
                (0.3 if sr_proximity else 0.1) +
                (0.2 if volume_confirmed else 0.1)
            )
        
            is_valid = validation_score >= 0.5
        
            return PatternValidation(
                is_valid=is_valid,
                validation_score=validation_score,
                context_score=context_score,
                volume_confirmation=volume_confirmed,
                trend_alignment=trend_aligned,
                support_resistance_proximity=sr_proximity,
                reasons=reasons
            )
        except Exception as e:
            logger.error(f"Error in validate_pattern: {e}")
            raise


class CandlestickPatternSystem:
    """
    Complete candlestick pattern detection and validation system.
    """
    
    def __init__(self):
        try:
            self.detector = PatternDetector()
            self.validator = PatternValidator()
            self.pattern_history: List[DetectedPattern] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def scan_for_patterns(
        self,
        df: pd.DataFrame,
        lookback: int = 5
    ) -> List[DetectedPattern]:
        """Scan recent candles for patterns."""
        try:
            detected = []
        
            start_idx = max(0, len(df) - lookback)
        
            for i in range(start_idx, len(df)):
                patterns = self.detector.detect_all_patterns(df, i)
            
                for pattern_type in patterns:
                    validation = self.validator.validate_pattern(df, i, pattern_type)
                    signal = self.validator.get_pattern_signal(pattern_type)
                
                    # Determine strength
                    if validation.validation_score >= 0.8:
                        strength = PatternStrength.VERY_STRONG
                    elif validation.validation_score >= 0.6:
                        strength = PatternStrength.STRONG
                    elif validation.validation_score >= 0.4:
                        strength = PatternStrength.MODERATE
                    elif validation.validation_score >= 0.2:
                        strength = PatternStrength.WEAK
                    else:
                        strength = PatternStrength.VERY_WEAK
                
                    detected_pattern = DetectedPattern(
                        pattern_type=pattern_type,
                        signal=signal,
                        strength=strength,
                        start_index=max(0, i - 2),
                        end_index=i,
                        confidence=validation.validation_score,
                        validation_score=validation.validation_score,
                        context_score=validation.context_score,
                        price_at_detection=df.iloc[i]['close']
                    )
                
                    detected.append(detected_pattern)
                    self.pattern_history.append(detected_pattern)
        
            return detected
        except Exception as e:
            logger.error(f"Error in scan_for_patterns: {e}")
            raise
    
    def get_trading_signal(
        self,
        df: pd.DataFrame,
        min_strength: PatternStrength = PatternStrength.MODERATE
    ) -> Optional[Dict[str, Any]]:
        """Get trading signal from detected patterns."""
        try:
            patterns = self.scan_for_patterns(df, lookback=3)
        
            # Filter by strength
            strength_order = [
                PatternStrength.VERY_STRONG,
                PatternStrength.STRONG,
                PatternStrength.MODERATE,
                PatternStrength.WEAK,
                PatternStrength.VERY_WEAK
            ]
            min_idx = strength_order.index(min_strength)
        
            valid_patterns = [
                p for p in patterns
                if strength_order.index(p.strength) <= min_idx
            ]
        
            if not valid_patterns:
                return None
        
            # Get strongest pattern
            best_pattern = max(valid_patterns, key=lambda p: p.validation_score)
        
            return {
                'pattern': best_pattern.pattern_type.value,
                'signal': best_pattern.signal.value,
                'strength': best_pattern.strength.value,
                'confidence': best_pattern.confidence,
                'price': best_pattern.price_at_detection,
                'validation_score': best_pattern.validation_score,
                'context_score': best_pattern.context_score
            }
        except Exception as e:
            logger.error(f"Error in get_trading_signal: {e}")
            raise


# Convenience functions
def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Quick pattern detection."""
    try:
        system = CandlestickPatternSystem()
        patterns = system.scan_for_patterns(df)
    
        return [
            {
                'pattern': p.pattern_type.value,
                'signal': p.signal.value,
                'strength': p.strength.value,
                'confidence': p.confidence,
                'index': p.end_index
            }
            for p in patterns
        ]
    except Exception as e:
        logger.error(f"Error in detect_candlestick_patterns: {e}")
        raise


def validate_pattern(
    df: pd.DataFrame,
    pattern_name: str,
    index: int = -1
) -> Dict[str, Any]:
    """Validate a specific pattern."""
    try:
        if index == -1:
            index = len(df) - 1
    
        validator = PatternValidator()
        pattern_type = PatternType(pattern_name)
    
        validation = validator.validate_pattern(df, index, pattern_type)
    
        return {
            'is_valid': validation.is_valid,
            'validation_score': validation.validation_score,
            'context_score': validation.context_score,
            'volume_confirmed': validation.volume_confirmation,
            'trend_aligned': validation.trend_alignment,
            'near_sr': validation.support_resistance_proximity,
            'reasons': validation.reasons
        }
    except Exception as e:
        logger.error(f"Error in validate_pattern: {e}")
        raise


def get_pattern_signal(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Get trading signal from patterns."""
    try:
        system = CandlestickPatternSystem()
        return system.get_trading_signal(df)
    except Exception as e:
        logger.error(f"Error in get_pattern_signal: {e}")
        raise
