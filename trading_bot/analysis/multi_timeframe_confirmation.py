"""
Multi-Timeframe Confirmation System.

This module implements:
- Multi-timeframe trend alignment
- Timeframe confluence scoring
- Higher timeframe bias detection
- Entry timing optimization
- Multi-timeframe divergence detection
- Timeframe synchronization
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


class Timeframe(Enum):
    """Trading timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN = "1M"


class TrendDirection(Enum):
    """Trend direction."""
    STRONG_UP = "strong_up"
    UP = "up"
    NEUTRAL = "neutral"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


class AlignmentStatus(Enum):
    """Multi-timeframe alignment status."""
    FULLY_ALIGNED = "fully_aligned"
    MOSTLY_ALIGNED = "mostly_aligned"
    MIXED = "mixed"
    CONFLICTING = "conflicting"


class ConfirmationType(Enum):
    """Types of confirmation."""
    TREND = "trend"
    MOMENTUM = "momentum"
    STRUCTURE = "structure"
    VOLUME = "volume"
    PATTERN = "pattern"


@dataclass
class TimeframeAnalysis:
    """Analysis for a single timeframe."""
    timeframe: Timeframe
    trend: TrendDirection
    trend_strength: float  # 0-1
    momentum: float  # -1 to 1
    support: float
    resistance: float
    key_levels: List[float]
    bias: str  # 'bullish', 'bearish', 'neutral'
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConfluenceScore:
    """Confluence score across timeframes."""
    score: float  # 0-1
    alignment: AlignmentStatus
    confirming_timeframes: List[Timeframe]
    conflicting_timeframes: List[Timeframe]
    dominant_trend: TrendDirection
    entry_quality: float
    notes: List[str]


@dataclass
class MTFSignal:
    """Multi-timeframe trading signal."""
    direction: str  # 'long', 'short', 'none'
    strength: float  # 0-1
    confluence: ConfluenceScore
    entry_timeframe: Timeframe
    bias_timeframe: Timeframe
    optimal_entry_zone: Tuple[float, float]
    invalidation_level: float
    targets: List[float]
    timestamp: datetime = field(default_factory=datetime.now)


class TimeframeAnalyzer:
    """
    Analyzes individual timeframes.
    """
    
    def __init__(
        self,
        ema_fast: int = 20,
        ema_slow: int = 50,
        ema_trend: int = 200,
        rsi_period: int = 14,
        atr_period: int = 14
    ):
        try:
            self.ema_fast = ema_fast
            self.ema_slow = ema_slow
            self.ema_trend = ema_trend
            self.rsi_period = rsi_period
            self.atr_period = atr_period
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate EMA."""
        return series.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / (loss + 1e-10)
            return 100 - (100 / (1 + rs))
        except Exception as e:
            logger.error(f"Error in calculate_rsi: {e}")
            raise
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
        
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
        
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Error in calculate_atr: {e}")
            raise
    
    def find_support_resistance(
        self,
        df: pd.DataFrame,
        lookback: int = 50
    ) -> Tuple[float, float]:
        """Find support and resistance levels."""
        try:
            recent = df.iloc[-lookback:]
        
            # Simple swing high/low detection
            highs = recent['high'].rolling(window=5, center=True).max()
            lows = recent['low'].rolling(window=5, center=True).min()
        
            resistance = recent['high'][recent['high'] == highs].max()
            support = recent['low'][recent['low'] == lows].min()
        
            return float(support), float(resistance)
        except Exception as e:
            logger.error(f"Error in find_support_resistance: {e}")
            raise
    
    def determine_trend(
        self,
        df: pd.DataFrame
    ) -> Tuple[TrendDirection, float]:
        """Determine trend direction and strength."""
        try:
            close = df['close']
        
            ema_fast = self.calculate_ema(close, self.ema_fast)
            ema_slow = self.calculate_ema(close, self.ema_slow)
            ema_trend = self.calculate_ema(close, self.ema_trend)
        
            current_price = close.iloc[-1]
            fast = ema_fast.iloc[-1]
            slow = ema_slow.iloc[-1]
            trend = ema_trend.iloc[-1]
        
            # Calculate trend strength
            if trend > 0:
                distance_from_trend = (current_price - trend) / trend
            else:
                distance_from_trend = 0
        
            # Determine direction
            if fast > slow > trend and current_price > fast:
                direction = TrendDirection.STRONG_UP
                strength = min(1.0, abs(distance_from_trend) * 10)
            elif fast > slow and current_price > trend:
                direction = TrendDirection.UP
                strength = min(0.7, abs(distance_from_trend) * 10)
            elif fast < slow < trend and current_price < fast:
                direction = TrendDirection.STRONG_DOWN
                strength = min(1.0, abs(distance_from_trend) * 10)
            elif fast < slow and current_price < trend:
                direction = TrendDirection.DOWN
                strength = min(0.7, abs(distance_from_trend) * 10)
            else:
                direction = TrendDirection.NEUTRAL
                strength = 0.3
        
            return direction, strength
        except Exception as e:
            logger.error(f"Error in determine_trend: {e}")
            raise
    
    def analyze(
        self,
        df: pd.DataFrame,
        timeframe: Timeframe
    ) -> TimeframeAnalysis:
        """Perform complete timeframe analysis."""
        try:
            close = df['close']
        
            # Trend analysis
            trend, trend_strength = self.determine_trend(df)
        
            # Momentum
            rsi = self.calculate_rsi(close, self.rsi_period)
            current_rsi = rsi.iloc[-1]
            momentum = (current_rsi - 50) / 50  # Normalize to -1 to 1
        
            # Support/Resistance
            support, resistance = self.find_support_resistance(df)
        
            # Key levels (EMAs)
            ema_fast = self.calculate_ema(close, self.ema_fast).iloc[-1]
            ema_slow = self.calculate_ema(close, self.ema_slow).iloc[-1]
            ema_trend = self.calculate_ema(close, self.ema_trend).iloc[-1]
            key_levels = sorted([ema_fast, ema_slow, ema_trend, support, resistance])
        
            # Determine bias
            if trend in [TrendDirection.STRONG_UP, TrendDirection.UP]:
                bias = 'bullish'
            elif trend in [TrendDirection.STRONG_DOWN, TrendDirection.DOWN]:
                bias = 'bearish'
            else:
                bias = 'neutral'
        
            # Confidence based on trend strength and momentum alignment
            if (trend in [TrendDirection.UP, TrendDirection.STRONG_UP] and momentum > 0) or \
               (trend in [TrendDirection.DOWN, TrendDirection.STRONG_DOWN] and momentum < 0):
                confidence = (trend_strength + abs(momentum)) / 2
            else:
                confidence = trend_strength * 0.5
        
            return TimeframeAnalysis(
                timeframe=timeframe,
                trend=trend,
                trend_strength=trend_strength,
                momentum=momentum,
                support=support,
                resistance=resistance,
                key_levels=key_levels,
                bias=bias,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class MultiTimeframeSystem:
    """
    Complete multi-timeframe confirmation system.
    """
    
    def __init__(
        self,
        timeframes: List[Timeframe] = None,
        min_confluence_score: float = 0.6,
        bias_timeframe: Timeframe = Timeframe.H4,
        entry_timeframe: Timeframe = Timeframe.M15
    ):
        try:
            self.timeframes = timeframes or [
                Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1
            ]
            self.min_confluence_score = min_confluence_score
            self.bias_timeframe = bias_timeframe
            self.entry_timeframe = entry_timeframe
        
            self.analyzer = TimeframeAnalyzer()
            self.analyses: Dict[Timeframe, TimeframeAnalysis] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def analyze_all_timeframes(
        self,
        data: Dict[Timeframe, pd.DataFrame]
    ) -> Dict[Timeframe, TimeframeAnalysis]:
        """Analyze all timeframes."""
        try:
            self.analyses = {}
        
            for tf in self.timeframes:
                if tf in data and len(data[tf]) > 0:
                    self.analyses[tf] = self.analyzer.analyze(data[tf], tf)
        
            return self.analyses
        except Exception as e:
            logger.error(f"Error in analyze_all_timeframes: {e}")
            raise
    
    def calculate_confluence(self) -> ConfluenceScore:
        """Calculate confluence score across timeframes."""
        try:
            if not self.analyses:
                return ConfluenceScore(
                    score=0,
                    alignment=AlignmentStatus.MIXED,
                    confirming_timeframes=[],
                    conflicting_timeframes=[],
                    dominant_trend=TrendDirection.NEUTRAL,
                    entry_quality=0,
                    notes=["No analyses available"]
                )
        
            # Count trend directions
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
        
            confirming = []
            conflicting = []
        
            # Get bias from higher timeframe
            bias_analysis = self.analyses.get(self.bias_timeframe)
            if bias_analysis:
                expected_bias = bias_analysis.bias
            else:
                expected_bias = 'neutral'
        
            for tf, analysis in self.analyses.items():
                if analysis.bias == 'bullish':
                    bullish_count += 1
                elif analysis.bias == 'bearish':
                    bearish_count += 1
                else:
                    neutral_count += 1
            
                # Check if confirming or conflicting with bias
                if analysis.bias == expected_bias or expected_bias == 'neutral':
                    confirming.append(tf)
                else:
                    conflicting.append(tf)
        
            total = len(self.analyses)
        
            # Determine dominant trend
            if bullish_count > bearish_count and bullish_count > neutral_count:
                dominant = TrendDirection.UP if bullish_count < total else TrendDirection.STRONG_UP
            elif bearish_count > bullish_count and bearish_count > neutral_count:
                dominant = TrendDirection.DOWN if bearish_count < total else TrendDirection.STRONG_DOWN
            else:
                dominant = TrendDirection.NEUTRAL
        
            # Calculate alignment
            max_aligned = max(bullish_count, bearish_count, neutral_count)
            alignment_ratio = max_aligned / total if total > 0 else 0
        
            if alignment_ratio >= 0.9:
                alignment = AlignmentStatus.FULLY_ALIGNED
            elif alignment_ratio >= 0.7:
                alignment = AlignmentStatus.MOSTLY_ALIGNED
            elif alignment_ratio >= 0.5:
                alignment = AlignmentStatus.MIXED
            else:
                alignment = AlignmentStatus.CONFLICTING
        
            # Calculate score
            score = alignment_ratio * 0.6 + (len(confirming) / total) * 0.4 if total > 0 else 0
        
            # Entry quality based on entry timeframe alignment
            entry_analysis = self.analyses.get(self.entry_timeframe)
            if entry_analysis and entry_analysis.bias == expected_bias:
                entry_quality = entry_analysis.confidence
            else:
                entry_quality = 0.3
        
            # Generate notes
            notes = []
            if alignment == AlignmentStatus.FULLY_ALIGNED:
                notes.append("All timeframes aligned - high probability setup")
            elif alignment == AlignmentStatus.CONFLICTING:
                notes.append("Timeframes conflicting - avoid trading")
        
            if len(conflicting) > 0:
                notes.append(f"Conflicting: {', '.join(tf.value for tf in conflicting)}")
        
            return ConfluenceScore(
                score=score,
                alignment=alignment,
                confirming_timeframes=confirming,
                conflicting_timeframes=conflicting,
                dominant_trend=dominant,
                entry_quality=entry_quality,
                notes=notes
            )
        except Exception as e:
            logger.error(f"Error in calculate_confluence: {e}")
            raise
    
    def get_entry_zone(
        self,
        direction: str
    ) -> Tuple[float, float]:
        """Get optimal entry zone based on MTF analysis."""
        try:
            entry_analysis = self.analyses.get(self.entry_timeframe)
        
            if not entry_analysis:
                return (0, 0)
        
            if direction == 'long':
                # Entry zone between support and current price
                zone_low = entry_analysis.support
                zone_high = entry_analysis.key_levels[1] if len(entry_analysis.key_levels) > 1 else entry_analysis.support * 1.01
            else:
                # Entry zone between current price and resistance
                zone_low = entry_analysis.key_levels[-2] if len(entry_analysis.key_levels) > 1 else entry_analysis.resistance * 0.99
                zone_high = entry_analysis.resistance
        
            return (zone_low, zone_high)
        except Exception as e:
            logger.error(f"Error in get_entry_zone: {e}")
            raise
    
    def get_invalidation_level(
        self,
        direction: str
    ) -> float:
        """Get invalidation level for the trade."""
        try:
            bias_analysis = self.analyses.get(self.bias_timeframe)
        
            if not bias_analysis:
                return 0
        
            if direction == 'long':
                return bias_analysis.support
            else:
                return bias_analysis.resistance
        except Exception as e:
            logger.error(f"Error in get_invalidation_level: {e}")
            raise
    
    def get_targets(
        self,
        direction: str
    ) -> List[float]:
        """Get profit targets based on MTF levels."""
        try:
            targets = []
        
            for tf in sorted(self.analyses.keys(), key=lambda x: list(Timeframe).index(x), reverse=True):
                analysis = self.analyses[tf]
            
                if direction == 'long':
                    if analysis.resistance not in targets:
                        targets.append(analysis.resistance)
                else:
                    if analysis.support not in targets:
                        targets.append(analysis.support)
        
            # Sort targets by distance
            if direction == 'long':
                targets.sort()
            else:
                targets.sort(reverse=True)
        
            return targets[:3]  # Return top 3 targets
        except Exception as e:
            logger.error(f"Error in get_targets: {e}")
            raise
    
    def generate_signal(
        self,
        data: Dict[Timeframe, pd.DataFrame]
    ) -> MTFSignal:
        """Generate multi-timeframe trading signal."""
        # Analyze all timeframes
        try:
            self.analyze_all_timeframes(data)
        
            # Calculate confluence
            confluence = self.calculate_confluence()
        
            # Determine direction
            if confluence.score < self.min_confluence_score:
                direction = 'none'
            elif confluence.dominant_trend in [TrendDirection.UP, TrendDirection.STRONG_UP]:
                direction = 'long'
            elif confluence.dominant_trend in [TrendDirection.DOWN, TrendDirection.STRONG_DOWN]:
                direction = 'short'
            else:
                direction = 'none'
        
            # Get entry zone
            entry_zone = self.get_entry_zone(direction) if direction != 'none' else (0, 0)
        
            # Get invalidation
            invalidation = self.get_invalidation_level(direction) if direction != 'none' else 0
        
            # Get targets
            targets = self.get_targets(direction) if direction != 'none' else []
        
            return MTFSignal(
                direction=direction,
                strength=confluence.score,
                confluence=confluence,
                entry_timeframe=self.entry_timeframe,
                bias_timeframe=self.bias_timeframe,
                optimal_entry_zone=entry_zone,
                invalidation_level=invalidation,
                targets=targets
            )
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def check_entry_timing(
        self,
        current_price: float,
        direction: str
    ) -> Tuple[bool, str]:
        """Check if current price is in optimal entry zone."""
        try:
            entry_zone = self.get_entry_zone(direction)
        
            if entry_zone == (0, 0):
                return False, "No entry zone defined"
        
            if direction == 'long':
                if entry_zone[0] <= current_price <= entry_zone[1]:
                    return True, f"Price in buy zone ({entry_zone[0]:.4f} - {entry_zone[1]:.4f})"
                elif current_price < entry_zone[0]:
                    return False, f"Price below buy zone, wait for {entry_zone[0]:.4f}"
                else:
                    return False, f"Price above buy zone, missed entry"
            else:
                if entry_zone[0] <= current_price <= entry_zone[1]:
                    return True, f"Price in sell zone ({entry_zone[0]:.4f} - {entry_zone[1]:.4f})"
                elif current_price > entry_zone[1]:
                    return False, f"Price above sell zone, wait for {entry_zone[1]:.4f}"
                else:
                    return False, f"Price below sell zone, missed entry"
        except Exception as e:
            logger.error(f"Error in check_entry_timing: {e}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of MTF analysis."""
        try:
            confluence = self.calculate_confluence()
        
            return {
                'timeframes_analyzed': len(self.analyses),
                'confluence_score': confluence.score,
                'alignment': confluence.alignment.value,
                'dominant_trend': confluence.dominant_trend.value,
                'confirming': [tf.value for tf in confluence.confirming_timeframes],
                'conflicting': [tf.value for tf in confluence.conflicting_timeframes],
                'entry_quality': confluence.entry_quality,
                'notes': confluence.notes,
                'analyses': {
                    tf.value: {
                        'trend': analysis.trend.value,
                        'bias': analysis.bias,
                        'confidence': analysis.confidence
                    }
                    for tf, analysis in self.analyses.items()
                }
            }
        except Exception as e:
            logger.error(f"Error in get_summary: {e}")
            raise


# Convenience functions
def check_mtf_alignment(
    data: Dict[str, pd.DataFrame],
    timeframes: List[str] = None
) -> Dict[str, Any]:
    """Quick MTF alignment check."""
    try:
        tf_map = {tf.value: tf for tf in Timeframe}
    
        # Convert string keys to Timeframe enum
        converted_data = {}
        for key, df in data.items():
            if key in tf_map:
                converted_data[tf_map[key]] = df
    
        tfs = [tf_map[t] for t in (timeframes or ['15m', '1h', '4h', '1d']) if t in tf_map]
    
        system = MultiTimeframeSystem(timeframes=tfs)
        signal = system.generate_signal(converted_data)
    
        return {
            'direction': signal.direction,
            'strength': signal.strength,
            'alignment': signal.confluence.alignment.value,
            'entry_zone': signal.optimal_entry_zone,
            'invalidation': signal.invalidation_level,
            'targets': signal.targets
        }
    except Exception as e:
        logger.error(f"Error in check_mtf_alignment: {e}")
        raise


def get_higher_timeframe_bias(
    htf_data: pd.DataFrame,
    timeframe: str = "4h"
) -> Tuple[str, float]:
    """Get bias from higher timeframe."""
    try:
        tf_map = {tf.value: tf for tf in Timeframe}
        tf = tf_map.get(timeframe, Timeframe.H4)
    
        analyzer = TimeframeAnalyzer()
        analysis = analyzer.analyze(htf_data, tf)
    
        return analysis.bias, analysis.confidence
    except Exception as e:
        logger.error(f"Error in get_higher_timeframe_bias: {e}")
        raise
