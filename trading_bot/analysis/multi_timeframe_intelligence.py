import logging
logger = logging.getLogger(__name__)
"""Multi-Timeframe Intelligence System.

This module implements advanced multi-timeframe analysis capabilities
to align trading decisions across different timeframes for optimal entries and exits.
"""

import numpy as np
import pandas as pd
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
try:
    import talib
    TALIB_AVAILABLE = True
except Exception:
    TALIB_AVAILABLE = False
    talib = None
from loguru import logger
import numpy
import pandas


class TimeFrame(Enum):
    """Trading timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class TrendDirection(Enum):
    """Trend direction types."""
    UP = auto()
    DOWN = auto()
    SIDEWAYS = auto()


@dataclass
class TimeframeAnalysis:
    """Analysis result for a specific timeframe."""
    timeframe: TimeFrame
    trend: TrendDirection
    strength: float  # 0.0 to 1.0
    support_levels: List[float]
    resistance_levels: List[float]
    key_levels: List[float]
    indicators: Dict[str, float]
    timestamp: datetime


class MultiTimeframeIntelligence:
    """Advanced multi-timeframe analysis system.
    
    Features:
    - Trend alignment across timeframes
    - Support/resistance confluence detection
    - Entry/exit optimization based on multiple timeframes
    - Divergence detection between timeframes
    - Momentum alignment
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the multi-timeframe intelligence system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.timeframes = self.config.get('timeframes', [
            TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1
        ])
        self.primary_timeframe = self.config.get('primary_timeframe', TimeFrame.M15)
        self.analysis_cache = {}
        self.confluence_threshold = self.config.get('confluence_threshold', 0.05)
        logger.info("MultiTimeframeIntelligence initialized")
    
    def analyze_timeframe(self, data: pd.DataFrame, timeframe: TimeFrame) -> TimeframeAnalysis:
        """Analyze a specific timeframe.
        
        Args:
            data: DataFrame with OHLCV data for the timeframe
            timeframe: TimeFrame enum value
            
        Returns:
            TimeframeAnalysis object with analysis results
        """
        if len(data) < 50:
            logger.warning(f"Insufficient data for {timeframe.value} analysis")
            return self._default_analysis(timeframe)
        
        # Calculate indicators
        indicators = self._calculate_indicators(data)
        
        # Determine trend
        trend, strength = self._determine_trend(data, indicators)
        
        # Find support and resistance levels
        support_levels = self._find_support_levels(data)
        resistance_levels = self._find_resistance_levels(data)
        
        # Identify key levels (major S/R)
        key_levels = self._identify_key_levels(data, support_levels, resistance_levels)
        
        analysis = TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            strength=strength,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            key_levels=key_levels,
            indicators=indicators,
            timestamp=datetime.now()
        )
        
        # Cache the analysis
        self.analysis_cache[timeframe] = analysis
        
        return analysis
    
    def analyze_all_timeframes(self, data_dict: Dict[TimeFrame, pd.DataFrame]) -> Dict[TimeFrame, TimeframeAnalysis]:
        """Analyze all configured timeframes.
        
        Args:
            data_dict: Dictionary mapping TimeFrame to corresponding DataFrame
            
        Returns:
            Dictionary mapping TimeFrame to TimeframeAnalysis
        """
        results = {}
        
        for timeframe in self.timeframes:
            if timeframe in data_dict:
                results[timeframe] = self.analyze_timeframe(data_dict[timeframe], timeframe)
            else:
                logger.warning(f"No data provided for timeframe {timeframe.value}")
        
        return results
    
    def get_trend_alignment(self, analyses: Dict[TimeFrame, TimeframeAnalysis]) -> Dict[str, Any]:
        """Calculate trend alignment across timeframes.
        
        Args:
            analyses: Dictionary mapping TimeFrame to TimeframeAnalysis
            
        Returns:
            Dictionary with trend alignment metrics
        """
        if not analyses:
            return {'alignment': 0.0, 'direction': TrendDirection.SIDEWAYS}
        
        # Count trends in each direction
        up_count = sum(1 for a in analyses.values() if a.trend == TrendDirection.UP)
        down_count = sum(1 for a in analyses.values() if a.trend == TrendDirection.DOWN)
        sideways_count = sum(1 for a in analyses.values() if a.trend == TrendDirection.SIDEWAYS)
        
        total = len(analyses)
        
        # Calculate alignment percentage
        if up_count > down_count and up_count > sideways_count:
            alignment = up_count / total
            direction = TrendDirection.UP
        elif down_count > up_count and down_count > sideways_count:
            alignment = down_count / total
            direction = TrendDirection.DOWN
        else:
            alignment = sideways_count / total
            direction = TrendDirection.SIDEWAYS
        
        # Calculate weighted alignment (higher timeframes have more weight)
        weighted_alignment = 0.0
        total_weight = 0.0
        
        for tf, analysis in analyses.items():
            # Weight by timeframe (higher timeframes have more weight)
            weight = self._get_timeframe_weight(tf)
            total_weight += weight
            
            # Add to weighted alignment if aligned with overall direction
            if analysis.trend == direction:
                weighted_alignment += weight
        
        weighted_alignment = weighted_alignment / total_weight if total_weight > 0 else 0.0
        
        # Calculate strength across timeframes
        avg_strength = np.mean([a.strength for a in analyses.values()])
        
        return {
            'alignment': alignment,
            'weighted_alignment': weighted_alignment,
            'direction': direction,
            'strength': avg_strength,
            'up_count': up_count,
            'down_count': down_count,
            'sideways_count': sideways_count
        }
    
    def find_confluence_zones(self, analyses: Dict[TimeFrame, TimeframeAnalysis]) -> List[Dict[str, Any]]:
        """Find price zones with confluence across multiple timeframes.
        
        Args:
            analyses: Dictionary mapping TimeFrame to TimeframeAnalysis
            
        Returns:
            List of confluence zones with price levels and strength
        """
        if not analyses:
            return []
        
        # Collect all levels from all timeframes
        all_levels = []
        
        for tf, analysis in analyses.items():
            weight = self._get_timeframe_weight(tf)
            
            # Add support levels
            for level in analysis.support_levels:
                all_levels.append({
                    'price': level,
                    'type': 'support',
                    'timeframe': tf,
                    'weight': weight
                })
            
            # Add resistance levels
            for level in analysis.resistance_levels:
                all_levels.append({
                    'price': level,
                    'type': 'resistance',
                    'timeframe': tf,
                    'weight': weight
                })
            
            # Add key levels with higher weight
            for level in analysis.key_levels:
                all_levels.append({
                    'price': level,
                    'type': 'key',
                    'timeframe': tf,
                    'weight': weight * 2.0  # Key levels have double weight
                })
        
        # Find clusters of levels (confluence zones)
        confluence_zones = self._cluster_price_levels(all_levels)
        
        return confluence_zones
    
    def get_entry_quality(self, price: float, analyses: Dict[TimeFrame, TimeframeAnalysis]) -> Dict[str, Any]:
        """Evaluate the quality of a potential entry at the given price.
        
        Args:
            price: Current price
            analyses: Dictionary mapping TimeFrame to TimeframeAnalysis
            
        Returns:
            Dictionary with entry quality metrics
        """
        if not analyses:
            return {'quality': 0.0, 'confidence': 0.0}
        
        # Get trend alignment
        alignment = self.get_trend_alignment(analyses)
        
        # Find confluence zones
        confluence_zones = self.find_confluence_zones(analyses)
        
        # Check if price is near a confluence zone
        near_zone = None
        min_distance = float('inf')
        
        for zone in confluence_zones:
            distance = abs(price - zone['price']) / price
            if distance < min_distance:
                min_distance = distance
                near_zone = zone
        
        # Calculate entry quality
        quality = 0.0
        confidence = 0.0
        
        # Factor 1: Trend alignment
        quality += alignment['weighted_alignment'] * 0.4
        
        # Factor 2: Proximity to confluence zone
        if near_zone and min_distance < self.confluence_threshold:
            # Higher quality if entering at support in uptrend or resistance in downtrend
            if (alignment['direction'] == TrendDirection.UP and near_zone['type'] == 'support') or \
               (alignment['direction'] == TrendDirection.DOWN and near_zone['type'] == 'resistance'):
                quality += (1.0 - min_distance / self.confluence_threshold) * 0.4
                confidence += near_zone['strength'] * 0.5
        
        # Factor 3: Momentum alignment
        momentum_alignment = self._check_momentum_alignment(analyses, alignment['direction'])
        quality += momentum_alignment * 0.2
        confidence += momentum_alignment * 0.3
        
        # Calculate overall confidence
        confidence += alignment['weighted_alignment'] * 0.2
        confidence = min(1.0, confidence)
        
        return {
            'quality': min(1.0, quality),
            'confidence': confidence,
            'alignment': alignment,
            'nearest_zone': near_zone,
            'distance_to_zone': min_distance if near_zone else None,
            'momentum_alignment': momentum_alignment
        }
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators for timeframe analysis."""
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        
        indicators = {}
        
        if TALIB_AVAILABLE:
            # Trend indicators
            sma_20_arr = talib.SMA(close, timeperiod=20)
            sma_50_arr = talib.SMA(close, timeperiod=50)
            sma_200_arr = talib.SMA(close, timeperiod=200) if len(close) >= 200 else np.array([np.nan])
            
            indicators['sma_20'] = sma_20_arr[-1] if not np.isnan(sma_20_arr[-1]) else close[-1]
            indicators['sma_50'] = sma_50_arr[-1] if not np.isnan(sma_50_arr[-1]) else close[-1]
            indicators['sma_200'] = sma_200_arr[-1] if not np.isnan(sma_200_arr[-1]) else close[-1]
            
            # Momentum indicators
            rsi_arr = talib.RSI(close, timeperiod=14)
            macd_arr, macd_signal_arr, macd_hist_arr = talib.MACD(close)
            
            indicators['rsi'] = rsi_arr[-1] if not np.isnan(rsi_arr[-1]) else 50.0
            indicators['macd_hist'] = macd_hist_arr[-1] if not np.isnan(macd_hist_arr[-1]) else 0.0
            
            # Volatility indicators
            atr_arr = talib.ATR(high, low, close, timeperiod=14)
            indicators['atr'] = atr_arr[-1] if not np.isnan(atr_arr[-1]) else 0.0
            indicators['atr_percent'] = indicators['atr'] / close[-1] * 100 if close[-1] != 0 else 0.0
            
            # Trend strength
            adx_arr = talib.ADX(high, low, close, timeperiod=14)
            indicators['adx'] = adx_arr[-1] if not np.isnan(adx_arr[-1]) else 25.0
        else:
            # Pandas/numpy fallbacks
            close_series = pd.Series(close)
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            
            sma_20_arr = close_series.rolling(20).mean().values
            sma_50_arr = close_series.rolling(50).mean().values
            sma_200_arr = close_series.rolling(200).mean().values if len(close) >= 200 else np.array([np.nan])
            
            indicators['sma_20'] = sma_20_arr[-1] if not np.isnan(sma_20_arr[-1]) else close[-1]
            indicators['sma_50'] = sma_50_arr[-1] if not np.isnan(sma_50_arr[-1]) else close[-1]
            indicators['sma_200'] = sma_200_arr[-1] if not np.isnan(sma_200_arr[-1]) else close[-1]
            
            # RSI fallback
            delta = close_series.diff()
            gain = (delta.where(delta > 0, 0.0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0
            
            # MACD fallback
            ema12 = close_series.ewm(span=12, adjust=False).mean()
            ema26 = close_series.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            macd_hist = macd_line - macd_signal
            indicators['macd_hist'] = float(macd_hist.iloc[-1]) if not np.isnan(macd_hist.iloc[-1]) else 0.0
            
            # ATR fallback
            prev_close = close_series.shift(1)
            tr = pd.concat([
                (high_series - low_series).abs(),
                (high_series - prev_close).abs(),
                (low_series - prev_close).abs()
            ], axis=1).max(axis=1)
            atr_series = tr.rolling(14).mean()
            atr_val = float(atr_series.iloc[-1]) if not np.isnan(atr_series.iloc[-1]) else 0.0
            indicators['atr'] = atr_val
            indicators['atr_percent'] = (atr_val / close[-1] * 100) if close[-1] != 0 else 0.0
            
            # ADX fallback (simplified Wilder's DMI)
            up_move = high_series.diff()
            down_move = -low_series.diff()
            plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
            minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
            tr_fallback = tr  # from ATR calc above
            tr14 = tr_fallback.rolling(14).sum()
            plus_di = 100 * (plus_dm.rolling(14).sum() / tr14.replace(0, np.nan))
            minus_di = 100 * (minus_dm.rolling(14).sum() / tr14.replace(0, np.nan))
            dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0)
            adx_series = dx.rolling(14).mean()
            indicators['adx'] = float(adx_series.iloc[-1]) if not np.isnan(adx_series.iloc[-1]) else 25.0
        
        return indicators
    
    def _determine_trend(self, data: pd.DataFrame, indicators: Dict[str, float]) -> Tuple[TrendDirection, float]:
        """Determine trend direction and strength."""
        close = data['close'].values
        
        # Check moving averages
        sma_20 = indicators['sma_20']
        sma_50 = indicators['sma_50']
        sma_200 = indicators['sma_200']
        
        # Calculate price change
        price_change = (close[-1] / close[-20]) - 1 if len(close) >= 20 else 0
        
        # Check ADX for trend strength
        adx = indicators['adx']
        
        # Determine trend direction
        if close[-1] > sma_50 and sma_20 > sma_50 and price_change > 0:
            trend = TrendDirection.UP
            strength = min(1.0, (adx / 50) + abs(price_change) * 5)
        elif close[-1] < sma_50 and sma_20 < sma_50 and price_change < 0:
            trend = TrendDirection.DOWN
            strength = min(1.0, (adx / 50) + abs(price_change) * 5)
        else:
            trend = TrendDirection.SIDEWAYS
            strength = max(0.1, 1.0 - (adx / 25))
        
        return trend, strength
    
    def _find_support_levels(self, data: pd.DataFrame) -> List[float]:
        """Find support levels in the data."""
        low = data['low'].values
        support_levels = []
        
        # Simple swing low detection
        for i in range(2, len(low) - 2):
            if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
                support_levels.append(low[i])
        
        # Keep only the most recent levels
        support_levels = support_levels[-5:] if support_levels else []
        
        return support_levels
    
    def _find_resistance_levels(self, data: pd.DataFrame) -> List[float]:
        """Find resistance levels in the data."""
        high = data['high'].values
        resistance_levels = []
        
        # Simple swing high detection
        for i in range(2, len(high) - 2):
            if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
                resistance_levels.append(high[i])
        
        # Keep only the most recent levels
        resistance_levels = resistance_levels[-5:] if resistance_levels else []
        
        return resistance_levels
    
    def _identify_key_levels(self, data: pd.DataFrame, support_levels: List[float], 
                           resistance_levels: List[float]) -> List[float]:
        """Identify key price levels (major support/resistance)."""
        # Combine all levels
        all_levels = support_levels + resistance_levels
        
        # Find clusters of levels
        key_levels = []
        
        if not all_levels:
            return key_levels
        
        # Sort levels
        sorted_levels = sorted(all_levels)
        
        # Group nearby levels
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            # If level is close to the average of current cluster, add to cluster
            cluster_avg = sum(current_cluster) / len(current_cluster)
            if abs(level - cluster_avg) / cluster_avg < 0.01:  # 1% threshold
                current_cluster.append(level)
            else:
                # Add average of current cluster to key levels if it has multiple levels
                if len(current_cluster) >= 2:
                    key_levels.append(sum(current_cluster) / len(current_cluster))
                
                # Start new cluster
                current_cluster = [level]
        
        # Add last cluster if it has multiple levels
        if len(current_cluster) >= 2:
            key_levels.append(sum(current_cluster) / len(current_cluster))
        
        return key_levels
    
    def _cluster_price_levels(self, levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cluster price levels to find confluence zones."""
        if not levels:
            return []
        
        # Sort by price
        sorted_levels = sorted(levels, key=lambda x: x['price'])
        
        # Group nearby levels
        clusters = []
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            # If level is close to the average of current cluster, add to cluster
            cluster_avg = sum(l['price'] for l in current_cluster) / len(current_cluster)
            if abs(level['price'] - cluster_avg) / cluster_avg < self.confluence_threshold:
                current_cluster.append(level)
            else:
                # Process current cluster
                if len(current_cluster) >= 2:  # Only consider clusters with multiple levels
                    clusters.append(self._process_cluster(current_cluster))
                
                # Start new cluster
                current_cluster = [level]
        
        # Process last cluster
        if len(current_cluster) >= 2:
            clusters.append(self._process_cluster(current_cluster))
        
        # Sort clusters by strength
        return sorted(clusters, key=lambda x: x['strength'], reverse=True)
    
    def _process_cluster(self, cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a cluster of price levels to create a confluence zone."""
        # Calculate weighted average price
        total_weight = sum(level['weight'] for level in cluster)
        weighted_price = sum(level['price'] * level['weight'] for level in cluster) / total_weight
        
        # Determine zone type (support, resistance, or mixed)
        support_count = sum(1 for level in cluster if level['type'] == 'support')
        resistance_count = sum(1 for level in cluster if level['type'] == 'resistance')
        key_count = sum(1 for level in cluster if level['type'] == 'key')
        
        if support_count > resistance_count:
            zone_type = 'support'
        elif resistance_count > support_count:
            zone_type = 'resistance'
        else:
            zone_type = 'mixed'
        
        # Calculate strength based on number of levels, weights, and timeframe diversity
        timeframes = set(level['timeframe'] for level in cluster)
        timeframe_diversity = len(timeframes) / len(self.timeframes)
        
        # Strength factors
        level_count_factor = min(1.0, len(cluster) / 5)  # Cap at 5 levels
        weight_factor = min(1.0, total_weight / 5)
        key_factor = min(1.0, key_count / 2)  # Cap at 2 key levels
        
        strength = (level_count_factor * 0.4 + 
                   timeframe_diversity * 0.3 + 
                   weight_factor * 0.2 + 
                   key_factor * 0.1)
        
        return {
            'price': weighted_price,
            'type': zone_type,
            'strength': strength,
            'level_count': len(cluster),
            'timeframes': [tf.value for tf in timeframes],
            'timeframe_count': len(timeframes)
        }
    
    def _check_momentum_alignment(self, analyses: Dict[TimeFrame, TimeframeAnalysis], 
                                overall_direction: TrendDirection) -> float:
        """Check if momentum indicators align with the overall trend direction."""
        alignment_score = 0.0
        total_weight = 0.0
        
        for tf, analysis in analyses.items():
            weight = self._get_timeframe_weight(tf)
            total_weight += weight
            
            # Check RSI
            rsi = analysis.indicators.get('rsi', 50)
            if (overall_direction == TrendDirection.UP and rsi > 50) or \
               (overall_direction == TrendDirection.DOWN and rsi < 50):
                alignment_score += weight * 0.5
            
            # Check MACD histogram
            macd_hist = analysis.indicators.get('macd_hist', 0)
            if (overall_direction == TrendDirection.UP and macd_hist > 0) or \
               (overall_direction == TrendDirection.DOWN and macd_hist < 0):
                alignment_score += weight * 0.5
        
        return alignment_score / total_weight if total_weight > 0 else 0.0
    
    def _get_timeframe_weight(self, timeframe: TimeFrame) -> float:
        """Get weight for a timeframe (higher timeframes have more weight)."""
        weights = {
            TimeFrame.M1: 0.5,
            TimeFrame.M5: 0.8,
            TimeFrame.M15: 1.0,
            TimeFrame.M30: 1.2,
            TimeFrame.H1: 1.5,
            TimeFrame.H4: 2.0,
            TimeFrame.D1: 3.0,
            TimeFrame.W1: 4.0
        }
        
        return weights.get(timeframe, 1.0)
    
    def _default_analysis(self, timeframe: TimeFrame) -> TimeframeAnalysis:
        """Return default analysis when data is insufficient."""
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=TrendDirection.SIDEWAYS,
            strength=0.5,
            support_levels=[],
            resistance_levels=[],
            key_levels=[],
            indicators={},
            timestamp=datetime.now()
        )
