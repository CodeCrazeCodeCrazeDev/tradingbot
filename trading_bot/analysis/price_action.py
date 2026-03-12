from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""Price Action Analysis Module.

This module provides comprehensive candlestick pattern analysis, support/resistance detection,
chart pattern recognition, and real-time price behavior analysis with multi-timeframe confirmation.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
import numpy
import pandas


class PatternType(Enum):
    """Types of candlestick and chart patterns."""
    # Candlestick patterns
    DOJI = auto()
    HAMMER = auto()
    SHOOTING_STAR = auto()
    ENGULFING = auto()
    MORNING_STAR = auto()
    EVENING_STAR = auto()
    HARAMI = auto()
    PIERCING_LINE = auto()
    DARK_CLOUD_COVER = auto()
    
    # Chart patterns
    DOUBLE_TOP = auto()
    DOUBLE_BOTTOM = auto()
    HEAD_AND_SHOULDERS = auto()
    INVERSE_HEAD_AND_SHOULDERS = auto()
    TRIANGLE = auto()
    WEDGE = auto()
    CHANNEL = auto()
    FLAG = auto()
    PENNANT = auto()


class TrendDirection(Enum):
    """Trend direction classification."""
    UP = auto()
    DOWN = auto()
    SIDEWAYS = auto()


@dataclass
class SupportResistanceLevel:
    """Support or resistance price level with metadata."""
    price: float
    strength: float  # 0.0 to 1.0
    touches: int
    is_support: bool
    timeframe: str
    created_at: int  # timestamp
    last_test: int  # timestamp
    broken: bool = False


@dataclass
class PricePattern:
    """Detected price pattern with metadata."""
    pattern_type: PatternType
    start_idx: int
    end_idx: int
    strength: float  # 0.0 to 1.0
    confirmed: bool
    description: str


class PriceActionAnalyzer:
    """Analyzes price action patterns and behavior."""
    
    def __init__(self, sensitivity: float = 0.5) -> None:
        """Initialize the analyzer with sensitivity parameter.
        
        Args:
            sensitivity: Detection sensitivity (0.0 to 1.0)
        """
        try:
            self.sensitivity = max(0.0, min(1.0, sensitivity))
            logger.debug("PriceActionAnalyzer initialized with sensitivity={}", sensitivity)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_candlesticks(self, df: pd.DataFrame) -> List[PricePattern]:
        """Analyze candlestick patterns in the dataframe.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected candlestick patterns
        """
        try:
            patterns = []
        
            # Ensure we have enough data
            if len(df) < 3:
                logger.warning("Not enough data for candlestick analysis")
                return patterns
        
            # Calculate basic candlestick properties
            df = df.copy()
            df['body_size'] = abs(df['close'] - df['open'])
            df['shadow_upper'] = df.apply(lambda x: x['high'] - max(x['open'], x['close']), axis=1)
            df['shadow_lower'] = df.apply(lambda x: min(x['open'], x['close']) - x['low'], axis=1)
            df['body_avg'] = df['body_size'].rolling(window=14).mean()
            df['is_bullish'] = df['close'] > df['open']
        
            # Detect Doji patterns
            doji_mask = (df['body_size'] / df['body_avg'] < 0.1) & \
                        ((df['shadow_upper'] > 0) | (df['shadow_lower'] > 0))
        
            for i in range(3, len(df)):
                # Skip first few rows for pattern detection that needs prior bars
                if doji_mask.iloc[i]:
                    patterns.append(PricePattern(
                        pattern_type=PatternType.DOJI,
                        start_idx=i,
                        end_idx=i,
                        strength=0.7,
                        confirmed=True,
                        description="Doji pattern indicating indecision"
                    ))
            
                # Detect Hammer pattern
                if (df['is_bullish'].iloc[i] and 
                    df['shadow_lower'].iloc[i] > 2 * df['body_size'].iloc[i] and
                    df['shadow_upper'].iloc[i] < 0.2 * df['body_size'].iloc[i]):
                    patterns.append(PricePattern(
                        pattern_type=PatternType.HAMMER,
                        start_idx=i,
                        end_idx=i,
                        strength=0.8,
                        confirmed=True,
                        description="Hammer pattern indicating potential reversal"
                    ))
            
                # Detect Shooting Star pattern
                if (not df['is_bullish'].iloc[i] and 
                    df['shadow_upper'].iloc[i] > 2 * df['body_size'].iloc[i] and
                    df['shadow_lower'].iloc[i] < 0.2 * df['body_size'].iloc[i]):
                    patterns.append(PricePattern(
                        pattern_type=PatternType.SHOOTING_STAR,
                        start_idx=i,
                        end_idx=i,
                        strength=0.8,
                        confirmed=True,
                        description="Shooting Star pattern indicating potential reversal"
                    ))
            
                # Detect Engulfing pattern
                if (i > 0 and
                    df['is_bullish'].iloc[i] != df['is_bullish'].iloc[i-1] and
                    df['body_size'].iloc[i] > df['body_size'].iloc[i-1] and
                    df['open'].iloc[i] <= df['close'].iloc[i-1] and
                    df['close'].iloc[i] >= df['open'].iloc[i-1]):
                    pattern_type = PatternType.ENGULFING
                    description = "Bullish Engulfing" if df['is_bullish'].iloc[i] else "Bearish Engulfing"
                    patterns.append(PricePattern(
                        pattern_type=pattern_type,
                        start_idx=i-1,
                        end_idx=i,
                        strength=0.85,
                        confirmed=True,
                        description=f"{description} pattern indicating potential reversal"
                    ))
        
            return patterns
        except Exception as e:
            logger.error(f"Error in analyze_candlesticks: {e}")
            raise
    
    def detect_support_resistance(self, df: pd.DataFrame, window_size: int = 10, 
                                 min_touches: int = 2) -> List[SupportResistanceLevel]:
        """Detect support and resistance levels.
        
        Args:
            df: DataFrame with OHLC data
            window_size: Window size for peak detection
            min_touches: Minimum number of touches to consider a valid level
            
        Returns:
            List of support and resistance levels
        """
        try:
            levels = []
        
            # Ensure we have enough data
            if len(df) < window_size * 2:
                logger.warning("Not enough data for support/resistance detection")
                return levels
        
            # Find local minima and maxima
            for i in range(window_size, len(df) - window_size):
                # Check if this is a local maximum
                if all(df['high'].iloc[i] >= df['high'].iloc[i-window_size:i]) and \
                   all(df['high'].iloc[i] >= df['high'].iloc[i+1:i+window_size+1]):
                    # Count touches
                    price_level = df['high'].iloc[i]
                    touches = self._count_level_touches(df, price_level, is_support=False)
                
                    if touches >= min_touches:
                        levels.append(SupportResistanceLevel(
                            price=price_level,
                            strength=min(0.5 + touches * 0.1, 1.0),
                            touches=touches,
                            is_support=False,
                            timeframe=self._infer_timeframe(df),
                            created_at=int(df['time'].iloc[i]),
                            last_test=int(df['time'].iloc[-1])
                        ))
            
                # Check if this is a local minimum
                if all(df['low'].iloc[i] <= df['low'].iloc[i-window_size:i]) and \
                   all(df['low'].iloc[i] <= df['low'].iloc[i+1:i+window_size+1]):
                    # Count touches
                    price_level = df['low'].iloc[i]
                    touches = self._count_level_touches(df, price_level, is_support=True)
                
                    if touches >= min_touches:
                        levels.append(SupportResistanceLevel(
                            price=price_level,
                            strength=min(0.5 + touches * 0.1, 1.0),
                            touches=touches,
                            is_support=True,
                            timeframe=self._infer_timeframe(df),
                            created_at=int(df['time'].iloc[i]),
                            last_test=int(df['time'].iloc[-1])
                        ))
        
            # Cluster similar levels
            return self._cluster_levels(levels)
        except Exception as e:
            logger.error(f"Error in detect_support_resistance: {e}")
            raise
    
    def detect_chart_patterns(self, df: pd.DataFrame) -> List[PricePattern]:
        """Detect chart patterns like double tops, head and shoulders, etc.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected chart patterns
        """
        try:
            patterns = []
        
            # Ensure we have enough data
            if len(df) < 30:
                logger.warning("Not enough data for chart pattern detection")
                return patterns
        
            # Detect double tops
            double_tops = self._detect_double_top(df)
            patterns.extend(double_tops)
        
            # Detect double bottoms
            double_bottoms = self._detect_double_bottom(df)
            patterns.extend(double_bottoms)
        
            # Detect head and shoulders
            head_shoulders = self._detect_head_and_shoulders(df)
            patterns.extend(head_shoulders)
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_chart_patterns: {e}")
            raise
    
    def analyze_trend(self, df: pd.DataFrame, window: int = 20) -> TrendDirection:
        """Analyze the current trend direction.
        
        Args:
            df: DataFrame with OHLC data
            window: Window size for trend analysis
            
        Returns:
            Trend direction enum
        """
        try:
            if len(df) < window:
                logger.warning("Not enough data for trend analysis")
                return TrendDirection.SIDEWAYS
        
            # Calculate simple moving average
            df = df.copy()
            df['sma'] = df['close'].rolling(window=window).mean()
        
            # Get the last valid SMA value
            last_sma = df['sma'].dropna().iloc[-1]
        
            # Calculate the slope of the SMA
            sma_values = df['sma'].dropna().values
            if len(sma_values) < 5:
                return TrendDirection.SIDEWAYS
            
            # Use the last 5 values to determine trend
            recent_sma = sma_values[-5:]
            slope = np.polyfit(range(len(recent_sma)), recent_sma, 1)[0]
        
            # Determine trend based on slope and price position
            last_close = df['close'].iloc[-1]
        
            if slope > 0 and last_close > last_sma:
                return TrendDirection.UP
            elif slope < 0 and last_close < last_sma:
                return TrendDirection.DOWN
            else:
                return TrendDirection.SIDEWAYS
        except Exception as e:
            logger.error(f"Error in analyze_trend: {e}")
            raise
    
    def multi_timeframe_confirmation(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Perform multi-timeframe confirmation analysis.
        
        Args:
            dataframes: Dictionary of dataframes for different timeframes
            
        Returns:
            Dictionary with multi-timeframe analysis results
        """
        try:
            results = {
                'aligned': False,
                'trend_agreement': 0.0,
                'support_resistance': [],
                'dominant_timeframe': None,
                'timeframes': {}
            }
        
            if not dataframes:
                logger.warning("No dataframes provided for multi-timeframe analysis")
                return results
        
            # Analyze each timeframe
            trends = {}
            for tf, df in dataframes.items():
                trend = self.analyze_trend(df)
                sr_levels = self.detect_support_resistance(df)
                patterns = self.analyze_candlesticks(df)
                chart_patterns = self.detect_chart_patterns(df)
            
                results['timeframes'][tf] = {
                    'trend': trend,
                    'support_resistance': sr_levels,
                    'candlestick_patterns': patterns,
                    'chart_patterns': chart_patterns
                }
                trends[tf] = trend
        
            # Check trend agreement
            if len(trends) > 1:
                # Count how many timeframes agree with the smallest timeframe
                smallest_tf = min(dataframes.keys())
                smallest_trend = trends[smallest_tf]
            
                agreement_count = sum(1 for t in trends.values() if t == smallest_trend)
                results['trend_agreement'] = agreement_count / len(trends)
                results['aligned'] = results['trend_agreement'] > 0.7
            
                # Find dominant timeframe (highest agreement with others)
                agreement_scores = {}
                for tf, trend in trends.items():
                    agreement_scores[tf] = sum(1 for t in trends.values() if t == trend)
            
                results['dominant_timeframe'] = max(agreement_scores, key=agreement_scores.get)
        
            # Combine support/resistance levels from all timeframes
            all_levels = []
            for tf_data in results['timeframes'].values():
                all_levels.extend(tf_data['support_resistance'])
        
            # Sort by strength and limit to top 10
            results['support_resistance'] = sorted(all_levels, key=lambda x: x.strength, reverse=True)[:10]
        
            return results
        except Exception as e:
            logger.error(f"Error in multi_timeframe_confirmation: {e}")
            raise
    
    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    
    def _count_level_touches(self, df: pd.DataFrame, level: float, is_support: bool, 
                           tolerance: float = 0.001) -> int:
        """Count how many times price has touched a level.
        
        Args:
            df: DataFrame with OHLC data
            level: Price level to check
            is_support: Whether this is a support level
            tolerance: Percentage tolerance for level matching
            
        Returns:
            Number of touches
        """
        try:
            tolerance_amount = level * tolerance
            touches = 0
        
            for i in range(len(df)):
                if is_support:
                    # For support, check if low price is within tolerance of level
                    if abs(df['low'].iloc[i] - level) <= tolerance_amount:
                        touches += 1
                else:
                    # For resistance, check if high price is within tolerance of level
                    if abs(df['high'].iloc[i] - level) <= tolerance_amount:
                        touches += 1
        
            return touches
        except Exception as e:
            logger.error(f"Error in _count_level_touches: {e}")
            raise
    
    def _cluster_levels(self, levels: List[SupportResistanceLevel], 
                      tolerance: float = 0.002) -> List[SupportResistanceLevel]:
        """Cluster similar price levels together.
        
        Args:
            levels: List of support/resistance levels
            tolerance: Percentage tolerance for clustering
            
        Returns:
            Clustered list of levels
        """
        try:
            if not levels:
                return []
        
            # Sort levels by price
            sorted_levels = sorted(levels, key=lambda x: x.price)
            clustered = []
            current_cluster = [sorted_levels[0]]
        
            for i in range(1, len(sorted_levels)):
                current_level = sorted_levels[i]
                prev_level = current_cluster[-1]
            
                # Check if current level is within tolerance of previous level
                if abs(current_level.price - prev_level.price) / prev_level.price <= tolerance:
                    # Add to current cluster
                    current_cluster.append(current_level)
                else:
                    # Create a new cluster
                    # First, merge the current cluster
                    if current_cluster:
                        merged = self._merge_cluster(current_cluster)
                        clustered.append(merged)
                
                    # Start a new cluster
                    current_cluster = [current_level]
        
            # Add the last cluster
            if current_cluster:
                merged = self._merge_cluster(current_cluster)
                clustered.append(merged)
        
            return clustered
        except Exception as e:
            logger.error(f"Error in _cluster_levels: {e}")
            raise
    
    def _merge_cluster(self, cluster: List[SupportResistanceLevel]) -> SupportResistanceLevel:
        """Merge a cluster of levels into a single level.
        
        Args:
            cluster: List of levels to merge
            
        Returns:
            Merged level
        """
        try:
            if not cluster:
                raise ValueError("Cannot merge empty cluster")
        
            if len(cluster) == 1:
                return cluster[0]
        
            # Calculate average price weighted by strength
            total_weight = sum(level.strength for level in cluster)
            avg_price = sum(level.price * level.strength for level in cluster) / total_weight
        
            # Sum touches
            total_touches = sum(level.touches for level in cluster)
        
            # Determine if support or resistance (majority vote)
            is_support = sum(1 for level in cluster if level.is_support) > len(cluster) / 2
        
            # Get the earliest creation timestamp
            created_at = min(level.created_at for level in cluster)
        
            # Get the latest test timestamp
            last_test = max(level.last_test for level in cluster)
        
            # Calculate combined strength (average + bonus for multiple levels)
            avg_strength = sum(level.strength for level in cluster) / len(cluster)
            combined_strength = min(avg_strength + 0.1 * (len(cluster) - 1), 1.0)
        
            # Determine if broken (any level is broken)
            broken = any(level.broken for level in cluster)
        
            # Use the most common timeframe
            timeframes = {}
            for level in cluster:
                timeframes[level.timeframe] = timeframes.get(level.timeframe, 0) + 1
            most_common_tf = max(timeframes, key=timeframes.get)
        
            return SupportResistanceLevel(
                price=avg_price,
                strength=combined_strength,
                touches=total_touches,
                is_support=is_support,
                timeframe=most_common_tf,
                created_at=created_at,
                last_test=last_test,
                broken=broken
            )
        except Exception as e:
            logger.error(f"Error in _merge_cluster: {e}")
            raise
    
    def _infer_timeframe(self, df: pd.DataFrame) -> str:
        """Infer the timeframe from the dataframe.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Timeframe string (M1, M5, M15, H1, etc.)
        """
        try:
            if len(df) < 2:
                return "Unknown"
        
            # Calculate average time difference between bars
            time_diffs = []
            for i in range(1, min(10, len(df))):
                time_diffs.append(df['time'].iloc[i] - df['time'].iloc[i-1])
        
            avg_diff = sum(time_diffs) / len(time_diffs)
        
            # Convert to minutes
            minutes = avg_diff / 60
        
            # Determine timeframe
            if minutes < 2:
                return "M1"
            elif minutes < 10:
                return "M5"
            elif minutes < 20:
                return "M15"
            elif minutes < 40:
                return "M30"
            elif minutes < 120:
                return "H1"
            elif minutes < 240:
                return "H4"
            else:
                return "D1"
        except Exception as e:
            logger.error(f"Error in _infer_timeframe: {e}")
            raise
    
    def _detect_double_top(self, df: pd.DataFrame) -> List[PricePattern]:
        """Detect double top patterns.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected double top patterns
        """
        try:
            patterns = []
        
            # Need at least 30 bars for reliable detection
            if len(df) < 30:
                return patterns
        
            # Find local maxima
            window = 5
            peaks = []
        
            for i in range(window, len(df) - window):
                if all(df['high'].iloc[i] >= df['high'].iloc[i-window:i]) and \
                   all(df['high'].iloc[i] >= df['high'].iloc[i+1:i+window+1]):
                    peaks.append((i, df['high'].iloc[i]))
        
            # Need at least 2 peaks
            if len(peaks) < 2:
                return patterns
        
            # Check for double tops
            for i in range(len(peaks) - 1):
                idx1, price1 = peaks[i]
            
                for j in range(i + 1, len(peaks)):
                    idx2, price2 = peaks[j]
                
                    # Check if peaks are similar in price
                    if abs(price1 - price2) / price1 <= 0.01:
                        # Check if there's a significant valley between peaks
                        if idx2 - idx1 >= 5:
                            valley_idx = df['low'].iloc[idx1:idx2].idxmin()
                            valley_price = df['low'].iloc[valley_idx]
                        
                            # Valley should be significantly lower
                            if (price1 - valley_price) / price1 >= 0.02:
                                patterns.append(PricePattern(
                                    pattern_type=PatternType.DOUBLE_TOP,
                                    start_idx=idx1,
                                    end_idx=idx2,
                                    strength=0.8,
                                    confirmed=True,
                                    description="Double Top pattern indicating potential reversal"
                                ))
                                # Only report one double top per peak
                                break
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_double_top: {e}")
            raise
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> List[PricePattern]:
        """Detect double bottom patterns.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected double bottom patterns
        """
        try:
            patterns = []
        
            # Need at least 30 bars for reliable detection
            if len(df) < 30:
                return patterns
        
            # Find local minima
            window = 5
            troughs = []
        
            for i in range(window, len(df) - window):
                if all(df['low'].iloc[i] <= df['low'].iloc[i-window:i]) and \
                   all(df['low'].iloc[i] <= df['low'].iloc[i+1:i+window+1]):
                    troughs.append((i, df['low'].iloc[i]))
        
            # Need at least 2 troughs
            if len(troughs) < 2:
                return patterns
        
            # Check for double bottoms
            for i in range(len(troughs) - 1):
                idx1, price1 = troughs[i]
            
                for j in range(i + 1, len(troughs)):
                    idx2, price2 = troughs[j]
                
                    # Check if troughs are similar in price
                    if abs(price1 - price2) / price1 <= 0.01:
                        # Check if there's a significant peak between troughs
                        if idx2 - idx1 >= 5:
                            peak_idx = df['high'].iloc[idx1:idx2].idxmax()
                            peak_price = df['high'].iloc[peak_idx]
                        
                            # Peak should be significantly higher
                            if (peak_price - price1) / price1 >= 0.02:
                                patterns.append(PricePattern(
                                    pattern_type=PatternType.DOUBLE_BOTTOM,
                                    start_idx=idx1,
                                    end_idx=idx2,
                                    strength=0.8,
                                    confirmed=True,
                                    description="Double Bottom pattern indicating potential reversal"
                                ))
                                # Only report one double bottom per trough
                                break
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_double_bottom: {e}")
            raise
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> List[PricePattern]:
        """Detect head and shoulders patterns.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected head and shoulders patterns
        """
        try:
            patterns = []
        
            # Need at least 50 bars for reliable detection
            if len(df) < 50:
                return patterns
        
            # Find local maxima
            window = 5
            peaks = []
        
            for i in range(window, len(df) - window):
                if all(df['high'].iloc[i] >= df['high'].iloc[i-window:i]) and \
                   all(df['high'].iloc[i] >= df['high'].iloc[i+1:i+window+1]):
                    peaks.append((i, df['high'].iloc[i]))
        
            # Need at least 3 peaks
            if len(peaks) < 3:
                return patterns
        
            # Check for head and shoulders pattern
            for i in range(len(peaks) - 2):
                left_idx, left_price = peaks[i]
            
                for j in range(i + 1, len(peaks) - 1):
                    head_idx, head_price = peaks[j]
                
                    # Head should be higher than left shoulder
                    if head_price <= left_price:
                        continue
                
                    for k in range(j + 1, len(peaks)):
                        right_idx, right_price = peaks[k]
                    
                        # Right shoulder should be similar to left shoulder
                        if abs(right_price - left_price) / left_price <= 0.05:
                            # Check if there are valleys between shoulders and head
                            left_valley_idx = df['low'].iloc[left_idx:head_idx].idxmin()
                            right_valley_idx = df['low'].iloc[head_idx:right_idx].idxmin()
                        
                            left_valley = df['low'].iloc[left_valley_idx]
                            right_valley = df['low'].iloc[right_valley_idx]
                        
                            # Valleys should be at similar levels (neckline)
                            if abs(left_valley - right_valley) / left_valley <= 0.02:
                                patterns.append(PricePattern(
                                    pattern_type=PatternType.HEAD_AND_SHOULDERS,
                                    start_idx=left_idx,
                                    end_idx=right_idx,
                                    strength=0.9,
                                    confirmed=True,
                                    description="Head and Shoulders pattern indicating potential reversal"
                                ))
                                # Only report one H&S per left shoulder
                                break
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_head_and_shoulders: {e}")
            raise
