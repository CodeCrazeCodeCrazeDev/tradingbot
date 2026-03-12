"""
Elite Pattern Recognition Module - Proprietary algorithmic pattern recognition
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import logging
try:
    from scipy import signal
except ImportError:
    scipy = None
import numpy
import pandas

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Pattern type enumeration"""
    HARMONIC = "harmonic"
    CANDLESTICK = "candlestick"
    CHART = "chart"
    VOLUME = "volume"
    INSTITUTIONAL = "institutional"
    ORDERFLOW = "orderflow"


class ElitePatternRecognizer:
    """
    Proprietary algorithmic pattern recognition system implementing elite professional trading concepts
    """
    
    def __init__(self, min_pattern_quality: float = 0.7):
        """
        Initialize the Elite Pattern Recognizer
        
        Args:
            min_pattern_quality: Minimum quality threshold for pattern detection (0.0-1.0)
        """
        self.min_pattern_quality = min_pattern_quality
        logger.info(f"Initialized Elite Pattern Recognizer with {min_pattern_quality} quality threshold")
    
    def detect_patterns(self, data: pd.DataFrame, pattern_types: List[PatternType] = None) -> Dict:
        """
        Detect all supported patterns in the provided data
        
        Args:
            data: DataFrame with OHLCV data
            pattern_types: List of pattern types to detect, None for all
            
        Returns:
            Dictionary with detected patterns
        """
        if pattern_types is None:
            pattern_types = [pt for pt in PatternType]
        
        results = {}
        
        for pattern_type in pattern_types:
            if pattern_type == PatternType.HARMONIC:
                results['harmonic'] = self.detect_harmonic_patterns(data)
            elif pattern_type == PatternType.CANDLESTICK:
                results['candlestick'] = self.detect_candlestick_patterns(data)
            elif pattern_type == PatternType.CHART:
                results['chart'] = self.detect_chart_patterns(data)
            elif pattern_type == PatternType.VOLUME:
                results['volume'] = self.detect_volume_patterns(data)
            elif pattern_type == PatternType.INSTITUTIONAL:
                results['institutional'] = self.detect_institutional_patterns(data)
            elif pattern_type == PatternType.ORDERFLOW:
                results['orderflow'] = self.detect_orderflow_patterns(data)
        
        return results
    
    def detect_candlestick_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect candlestick patterns using custom implementation
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected candlestick patterns
        """
        patterns = []
        
        for i in range(1, len(data)):
            # Get current and previous candle data
            curr = data.iloc[i]
            prev = data.iloc[i-1]
            
            # Calculate candle properties
            curr_body = abs(curr['close'] - curr['open'])
            curr_upper_wick = curr['high'] - max(curr['open'], curr['close'])
            curr_lower_wick = min(curr['open'], curr['close']) - curr['low']
            
            prev_body = abs(prev['close'] - prev['open'])
            prev_upper_wick = prev['high'] - max(prev['open'], prev['close'])
            prev_lower_wick = min(prev['open'], prev['close']) - prev['low']
            
            # Check for bullish engulfing
            if (curr['open'] < prev['close'] and
                curr['close'] > prev['open'] and
                curr_body > prev_body and
                curr['close'] > curr['open']):
                patterns.append({
                    'type': 'candlestick',
                    'pattern': 'bullish_engulfing',
                    'index': i,
                    'strength': curr_body / prev_body,
                    'direction': 'bullish'
                })
            
            # Check for bearish engulfing
            elif (curr['open'] > prev['close'] and
                  curr['close'] < prev['open'] and
                  curr_body > prev_body and
                  curr['close'] < curr['open']):
                patterns.append({
                    'type': 'candlestick',
                    'pattern': 'bearish_engulfing',
                    'index': i,
                    'strength': curr_body / prev_body,
                    'direction': 'bearish'
                })
            
            # Check for hammer
            if (curr_lower_wick > 2 * curr_body and
                curr_upper_wick < 0.1 * curr_body and
                curr['close'] > curr['open']):
                patterns.append({
                    'type': 'candlestick',
                    'pattern': 'hammer',
                    'index': i,
                    'strength': curr_lower_wick / curr_body,
                    'direction': 'bullish'
                })
            
            # Check for shooting star
            if (curr_upper_wick > 2 * curr_body and
                curr_lower_wick < 0.1 * curr_body and
                curr['close'] < curr['open']):
                patterns.append({
                    'type': 'candlestick',
                    'pattern': 'shooting_star',
                    'index': i,
                    'strength': curr_upper_wick / curr_body,
                    'direction': 'bearish'
                })
            
            # Check for doji
            if curr_body < 0.1 * (curr['high'] - curr['low']):
                patterns.append({
                    'type': 'candlestick',
                    'pattern': 'doji',
                    'index': i,
                    'strength': 1 - (curr_body / (curr['high'] - curr['low'])),
                    'direction': 'neutral'
                })
        
        return patterns
    
    def detect_chart_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect chart patterns (Head and Shoulders, Double Top/Bottom, etc.)
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected chart patterns
        """
        patterns = []
        
        # Find potential head and shoulders patterns
        head_shoulders = self._find_head_and_shoulders(data)
        patterns.extend(head_shoulders)
        
        # Find potential double tops and bottoms
        double_patterns = self._find_double_patterns(data)
        patterns.extend(double_patterns)
        
        return patterns
    
    def detect_volume_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect volume-based patterns
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected volume patterns
        """
        patterns = []
        
        # Check for volume climax
        volume_climax = self._find_volume_climax(data)
        patterns.extend(volume_climax)
        
        return patterns
    
    def detect_institutional_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect institutional footprint patterns
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected institutional patterns
        """
        patterns = []
        
        # Check for stop hunts
        stop_hunts = self._find_stop_hunts(data)
        patterns.extend(stop_hunts)
        
        # Check for order blocks
        order_blocks = self._find_order_blocks(data)
        patterns.extend(order_blocks)
        
        # Check for fair value gaps
        fvgs = self._find_fair_value_gaps(data)
        patterns.extend(fvgs)
        
        return patterns
    
    def detect_harmonic_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect harmonic patterns (Gartley, Butterfly, Bat, etc.)
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected harmonic patterns
        """
        # Placeholder implementation
        return []
    
    def detect_orderflow_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect order flow patterns
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected order flow patterns
        """
        # Placeholder implementation
        return []
    
    def filter_patterns_by_quality(self, patterns: List[Dict], min_quality: float = None) -> List[Dict]:
        """
        Filter patterns by quality score
        
        Args:
            patterns: List of detected patterns
            min_quality: Minimum quality threshold, defaults to instance threshold
            
        Returns:
            Filtered list of patterns
        """
        if min_quality is None:
            min_quality = self.min_pattern_quality
        
        return [p for p in patterns if p.get('quality', 0) >= min_quality]
    
    def rank_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Rank patterns by quality and significance
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            List of patterns sorted by rank
        """
        if not patterns:
            return []
        
        # Calculate composite score for each pattern
        for pattern in patterns:
            quality = pattern.get('quality', 0.5)
            recency = pattern.get('recency', 0.5)  # More recent patterns are more relevant
            significance = pattern.get('significance', 0.5)
            
            # Composite score formula
            pattern['rank_score'] = (quality * 0.5) + (recency * 0.3) + (significance * 0.2)
        
        # Sort by rank score in descending order
        return sorted(patterns, key=lambda x: x.get('rank_score', 0), reverse=True)
    
    # Private helper methods
    
    def _find_price_pivots(self, data: pd.DataFrame, lookahead: int = 3) -> List[Dict]:
        """Find price pivots (swing highs and lows)"""
        highs = data['high'].values
        lows = data['low'].values
        
        # Find peaks (swing highs)
        peak_indices = signal.find_peaks(highs, distance=lookahead)[0]
        
        # Find valleys (swing lows)
        valley_indices = signal.find_peaks(-lows, distance=lookahead)[0]
        
        # Combine and sort by index
        pivots = []
        
        for idx in peak_indices:
            pivots.append({
                'index': idx,
                'price': highs[idx],
                'type': 'high',
                'timestamp': data.index[idx] if hasattr(data, 'index') else idx
            })
        
        for idx in valley_indices:
            pivots.append({
                'index': idx,
                'price': lows[idx],
                'type': 'low',
                'timestamp': data.index[idx] if hasattr(data, 'index') else idx
            })
        
        # Sort by index
        pivots.sort(key=lambda x: x['index'])
        
        return pivots
    
    def _find_head_and_shoulders(self, data: pd.DataFrame) -> List[Dict]:
        """Find head and shoulders patterns"""
        patterns = []
        
        # Find pivots
        pivots = self._find_price_pivots(data, lookahead=5)
        
        # Need at least 5 pivots for a head and shoulders
        if len(pivots) < 5:
            return patterns
        
        # Look for sequences of 5 pivots that could form head and shoulders
        for i in range(len(pivots) - 4):
            # Check if we have low-high-low-high-low sequence
            if (pivots[i]['type'] == 'low' and
                pivots[i+1]['type'] == 'high' and
                pivots[i+2]['type'] == 'low' and
                pivots[i+3]['type'] == 'high' and
                pivots[i+4]['type'] == 'low'):
                
                # Check if middle high is higher than other highs (head)
                if pivots[i+1]['price'] < pivots[i+3]['price'] > pivots[i+1]['price']:
                    
                    # Check if shoulders are roughly at same level
                    shoulder_diff = abs(pivots[i+1]['price'] - pivots[i+3]['price'])
                    shoulder_avg = (pivots[i+1]['price'] + pivots[i+3]['price']) / 2
                    if shoulder_diff / shoulder_avg < 0.1:  # Within 10% of each other
                        
                        # Check if neckline is roughly horizontal
                        neckline_diff = abs(pivots[i]['price'] - pivots[i+4]['price'])
                        neckline_avg = (pivots[i]['price'] + pivots[i+4]['price']) / 2
                        if neckline_diff / neckline_avg < 0.05:  # Within 5% of each other
                            
                            # We have a head and shoulders pattern
                            patterns.append({
                                'type': 'chart',
                                'pattern': 'head_and_shoulders',
                                'direction': 'bearish',
                                'start_index': pivots[i]['index'],
                                'end_index': pivots[i+4]['index'],
                                'neckline': neckline_avg,
                                'quality': 0.8,
                                'significance': 0.9
                            })
        
        # Look for inverse head and shoulders (similar logic, reversed)
        for i in range(len(pivots) - 4):
            if (pivots[i]['type'] == 'high' and
                pivots[i+1]['type'] == 'low' and
                pivots[i+2]['type'] == 'high' and
                pivots[i+3]['type'] == 'low' and
                pivots[i+4]['type'] == 'high'):
                
                if pivots[i+1]['price'] > pivots[i+3]['price'] < pivots[i+1]['price']:
                    shoulder_diff = abs(pivots[i+1]['price'] - pivots[i+3]['price'])
                    shoulder_avg = (pivots[i+1]['price'] + pivots[i+3]['price']) / 2
                    
                    if shoulder_diff / shoulder_avg < 0.1:
                        neckline_diff = abs(pivots[i]['price'] - pivots[i+4]['price'])
                        neckline_avg = (pivots[i]['price'] + pivots[i+4]['price']) / 2
                        
                        if neckline_diff / neckline_avg < 0.05:
                            patterns.append({
                                'type': 'chart',
                                'pattern': 'inverse_head_and_shoulders',
                                'direction': 'bullish',
                                'start_index': pivots[i]['index'],
                                'end_index': pivots[i+4]['index'],
                                'neckline': neckline_avg,
                                'quality': 0.8,
                                'significance': 0.9
                            })
        
        return patterns
    
    def _find_double_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Find double top and double bottom patterns"""
        patterns = []
        
        # Find pivots
        pivots = self._find_price_pivots(data, lookahead=5)
        
        # Need at least 3 pivots for a double top/bottom
        if len(pivots) < 3:
            return patterns
        
        # Look for double tops
        for i in range(len(pivots) - 2):
            # Check if we have high-low-high sequence
            if (pivots[i]['type'] == 'high' and
                pivots[i+1]['type'] == 'low' and
                pivots[i+2]['type'] == 'high'):
                
                # Check if tops are at similar levels
                top_diff = abs(pivots[i]['price'] - pivots[i+2]['price'])
                top_avg = (pivots[i]['price'] + pivots[i+2]['price']) / 2
                if top_diff / top_avg < 0.03:  # Within 3% of each other
                    
                    # We have a double top pattern
                    patterns.append({
                        'type': 'chart',
                        'pattern': 'double_top',
                        'direction': 'bearish',
                        'start_index': pivots[i]['index'],
                        'end_index': pivots[i+2]['index'],
                        'neckline': pivots[i+1]['price'],
                        'quality': 0.75,
                        'significance': 0.8
                    })
        
        # Look for double bottoms
        for i in range(len(pivots) - 2):
            # Check if we have low-high-low sequence
            if (pivots[i]['type'] == 'low' and
                pivots[i+1]['type'] == 'high' and
                pivots[i+2]['type'] == 'low'):
                
                # Check if bottoms are at similar levels
                bottom_diff = abs(pivots[i]['price'] - pivots[i+2]['price'])
                bottom_avg = (pivots[i]['price'] + pivots[i+2]['price']) / 2
                if bottom_diff / bottom_avg < 0.03:  # Within 3% of each other
                    
                    # We have a double bottom pattern
                    patterns.append({
                        'type': 'chart',
                        'pattern': 'double_bottom',
                        'direction': 'bullish',
                        'start_index': pivots[i]['index'],
                        'end_index': pivots[i+2]['index'],
                        'neckline': pivots[i+1]['price'],
                        'quality': 0.75,
                        'significance': 0.8
                    })
        
        return patterns
    
    def _find_volume_climax(self, data: pd.DataFrame) -> List[Dict]:
        """Find volume climax patterns"""
        patterns = []
        
        # Calculate average volume
        avg_volume = data['volume'].rolling(window=20).mean()
        
        # Look for volume spikes
        for i in range(20, len(data)):
            if data['volume'].iloc[i] > avg_volume.iloc[i] * 3:  # Volume 3x above average
                # Check if this is a price extreme
                is_high = data['high'].iloc[i] == data['high'].iloc[i-10:i+1].max()
                is_low = data['low'].iloc[i] == data['low'].iloc[i-10:i+1].min()
                
                if is_high or is_low:
                    direction = 'bearish' if is_high else 'bullish'
                    patterns.append({
                        'type': 'volume',
                        'pattern': 'volume_climax',
                        'direction': direction,
                        'index': i,
                        'volume': data['volume'].iloc[i],
                        'avg_volume': avg_volume.iloc[i],
                        'quality': 0.85,
                        'significance': 0.9
                    })
        
        return patterns
    
    def _find_stop_hunts(self, data: pd.DataFrame) -> List[Dict]:
        """Find stop hunt patterns"""
        patterns = []
        
        # Look for price spikes beyond support/resistance followed by reversal
        for i in range(5, len(data) - 1):
            # Calculate recent high and low
            recent_high = data['high'].iloc[i-5:i].max()
            recent_low = data['low'].iloc[i-5:i].min()
            
            # Check for upward stop hunt
            if (data['high'].iloc[i] > recent_high and
                data['close'].iloc[i] < recent_high and
                data['close'].iloc[i] < data['open'].iloc[i]):
                
                patterns.append({
                    'type': 'institutional',
                    'pattern': 'stop_hunt',
                    'direction': 'bearish',
                    'index': i,
                    'quality': 0.7,
                    'significance': 0.8
                })
            
            # Check for downward stop hunt
            if (data['low'].iloc[i] < recent_low and
                data['close'].iloc[i] > recent_low and
                data['close'].iloc[i] > data['open'].iloc[i]):
                
                patterns.append({
                    'type': 'institutional',
                    'pattern': 'stop_hunt',
                    'direction': 'bullish',
                    'index': i,
                    'quality': 0.7,
                    'significance': 0.8
                })
        
        return patterns
    
    def _find_order_blocks(self, data: pd.DataFrame) -> List[Dict]:
        """Find order block patterns"""
        patterns = []
        
        # Look for strong momentum candles followed by retracement
        for i in range(1, len(data) - 5):
            # Check for bullish order block
            if (data['close'].iloc[i] < data['open'].iloc[i] and  # Bearish candle
                data['close'].iloc[i+1] > data['open'].iloc[i+1] and  # Bullish candle
                data['close'].iloc[i+1] > data['close'].iloc[i] and  # Strong momentum
                (data['close'].iloc[i+1] - data['open'].iloc[i+1]) > 
                2 * abs(data['close'].iloc[i] - data['open'].iloc[i])):  # Momentum > 2x previous
                
                # Check if price retraces back to this candle
                for j in range(i+2, min(i+10, len(data))):
                    if data['low'].iloc[j] <= data['high'].iloc[i]:
                        patterns.append({
                            'type': 'institutional',
                            'pattern': 'bullish_order_block',
                            'direction': 'bullish',
                            'index': i,
                            'test_index': j,
                            'high': data['high'].iloc[i],
                            'low': data['low'].iloc[i],
                            'quality': 0.8,
                            'significance': 0.85
                        })
                        break
            
            # Check for bearish order block
            if (data['close'].iloc[i] > data['open'].iloc[i] and  # Bullish candle
                data['close'].iloc[i+1] < data['open'].iloc[i+1] and  # Bearish candle
                data['close'].iloc[i+1] < data['close'].iloc[i] and  # Strong momentum
                (data['open'].iloc[i+1] - data['close'].iloc[i+1]) > 
                2 * abs(data['close'].iloc[i] - data['open'].iloc[i])):  # Momentum > 2x previous
                
                # Check if price retraces back to this candle
                for j in range(i+2, min(i+10, len(data))):
                    if data['high'].iloc[j] >= data['low'].iloc[i]:
                        patterns.append({
                            'type': 'institutional',
                            'pattern': 'bearish_order_block',
                            'direction': 'bearish',
                            'index': i,
                            'test_index': j,
                            'high': data['high'].iloc[i],
                            'low': data['low'].iloc[i],
                            'quality': 0.8,
                            'significance': 0.85
                        })
                        break
        
        return patterns
    
    def _find_fair_value_gaps(self, data: pd.DataFrame) -> List[Dict]:
        """Find fair value gap patterns"""
        patterns = []
        
        # Look for gaps between candle bodies
        for i in range(1, len(data) - 1):
            # Check for bullish FVG
            if (data['low'].iloc[i+1] > data['high'].iloc[i-1]):
                gap_size = data['low'].iloc[i+1] - data['high'].iloc[i-1]
                avg_price = (data['close'].iloc[i-1] + data['close'].iloc[i+1]) / 2
                
                # Gap should be significant
                if gap_size / avg_price > 0.003:  # At least 0.3% gap
                    patterns.append({
                        'type': 'institutional',
                        'pattern': 'bullish_fvg',
                        'direction': 'bullish',
                        'index': i,
                        'high': data['high'].iloc[i-1],
                        'low': data['low'].iloc[i+1],
                        'gap_size': gap_size,
                        'quality': 0.75,
                        'significance': 0.8
                    })
            
            # Check for bearish FVG
            if (data['high'].iloc[i+1] < data['low'].iloc[i-1]):
                gap_size = data['low'].iloc[i-1] - data['high'].iloc[i+1]
                avg_price = (data['close'].iloc[i-1] + data['close'].iloc[i+1]) / 2
                
                # Gap should be significant
                if gap_size / avg_price > 0.003:  # At least 0.3% gap
                    patterns.append({
                        'type': 'institutional',
                        'pattern': 'bearish_fvg',
                        'direction': 'bearish',
                        'index': i,
                        'high': data['low'].iloc[i-1],
                        'low': data['high'].iloc[i+1],
                        'gap_size': gap_size,
                        'quality': 0.75,
                        'significance': 0.8
                    })
        
        return patterns
