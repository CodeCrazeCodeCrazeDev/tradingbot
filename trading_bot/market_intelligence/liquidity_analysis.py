import logging
logger = logging.getLogger(__name__)
"""Liquidity Analysis for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
import numpy
import pandas


class OrderBlockType(Enum):
    """Types of order blocks."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    MITIGATION = "mitigation"


class OrderBlockAnalysis:
    """Analyze order blocks and institutional order flow."""
    
    def __init__(self):
        try:
            self.order_blocks = []
            logger.info("Initialized OrderBlockAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_order_blocks(self, df: pd.DataFrame, 
                          min_body_size: float = 0.001,
                          volume_threshold: float = 1.5) -> List[Dict]:
        """Detect order blocks in price data.
        
        Args:
            df: DataFrame with OHLC and volume data
            min_body_size: Minimum candle body size for order block
            volume_threshold: Volume threshold for order block validation
            
        Returns:
            List of detected order blocks
        """
        try:
            order_blocks = []
        
            # Calculate candle metrics
            df['body_size'] = abs(df['close'] - df['open'])
            df['body_pct'] = df['body_size'] / df['close']
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            # Detect strong directional moves
            for i in range(2, len(df) - 2):
                current = df.iloc[i]
                prev = df.iloc[i-1]
                next_candle = df.iloc[i+1]
            
                # Check for strong bullish candle
                if (current['body_pct'] > min_body_size and
                    current['close'] > current['open'] and
                    current['volume_ratio'] > volume_threshold):
                
                    # Check if next candle moves away (creates imbalance)
                    if next_candle['low'] > current['high']:
                        order_blocks.append({
                            'timestamp': current.name,
                            'type': OrderBlockType.BULLISH,
                            'high': current['high'],
                            'low': current['low'],
                            'open': current['open'],
                            'close': current['close'],
                            'volume': current['volume'],
                            'body_size': current['body_size'],
                            'volume_ratio': current['volume_ratio'],
                            'mitigation_level': current['low'],  # Level to watch for mitigation
                            'is_mitigated': False
                        })
            
                # Check for strong bearish candle
                elif (current['body_pct'] > min_body_size and
                      current['close'] < current['open'] and
                      current['volume_ratio'] > volume_threshold):
                
                    # Check if next candle moves away
                    if next_candle['high'] < current['low']:
                        order_blocks.append({
                            'timestamp': current.name,
                            'type': OrderBlockType.BEARISH,
                            'high': current['high'],
                            'low': current['low'],
                            'open': current['open'],
                            'close': current['close'],
                            'volume': current['volume'],
                            'body_size': current['body_size'],
                            'volume_ratio': current['volume_ratio'],
                            'mitigation_level': current['high'],  # Level to watch for mitigation
                            'is_mitigated': False
                        })
        
            return order_blocks
        except Exception as e:
            logger.error(f"Error in detect_order_blocks: {e}")
            raise
    
    def check_order_block_mitigation(self, order_blocks: List[Dict], 
                                   df: pd.DataFrame) -> List[Dict]:
        """Check if order blocks have been mitigated.
        
        Args:
            order_blocks: List of order blocks to check
            df: DataFrame with current price data
            
        Returns:
            Updated list of order blocks with mitigation status
        """
        try:
            updated_blocks = []
        
            for block in order_blocks:
                block_copy = block.copy()
                block_timestamp = block['timestamp']
            
                # Get price data after the order block
                future_data = df[df.index > block_timestamp]
            
                if len(future_data) > 0:
                    if block['type'] == OrderBlockType.BULLISH:
                        # Bullish order block is mitigated when price returns to its low
                        mitigation_touches = future_data[future_data['low'] <= block['mitigation_level']]
                        if len(mitigation_touches) > 0:
                            block_copy['is_mitigated'] = True
                            block_copy['mitigation_timestamp'] = mitigation_touches.index[0]
                
                    elif block['type'] == OrderBlockType.BEARISH:
                        # Bearish order block is mitigated when price returns to its high
                        mitigation_touches = future_data[future_data['high'] >= block['mitigation_level']]
                        if len(mitigation_touches) > 0:
                            block_copy['is_mitigated'] = True
                            block_copy['mitigation_timestamp'] = mitigation_touches.index[0]
            
                updated_blocks.append(block_copy)
        
            return updated_blocks
        except Exception as e:
            logger.error(f"Error in check_order_block_mitigation: {e}")
            raise


class LiquidityPoolDetector:
    """Detect liquidity pools and zones."""
    
    def __init__(self):
        try:
            self.liquidity_pools = []
            logger.info("Initialized LiquidityPoolDetector")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_equal_highs_lows(self, df: pd.DataFrame, 
                              tolerance: float = 0.0005,
                              min_touches: int = 2) -> List[Dict]:
        """Detect equal highs and lows (potential liquidity pools).
        
        Args:
            df: DataFrame with OHLC data
            tolerance: Price tolerance for "equal" levels
            min_touches: Minimum number of touches to confirm level
            
        Returns:
            List of detected liquidity pools
        """
        try:
            liquidity_pools = []
        
            # Find swing highs and lows
            swing_highs = self._find_swing_points(df['high'], 'high')
            swing_lows = self._find_swing_points(df['low'], 'low')
        
            # Group similar levels for highs
            high_groups = self._group_similar_levels(swing_highs, tolerance)
            for group in high_groups:
                if len(group) >= min_touches:
                    avg_level = np.mean([point['price'] for point in group])
                    liquidity_pools.append({
                        'level': avg_level,
                        'type': 'resistance',
                        'touches': len(group),
                        'first_touch': min(point['timestamp'] for point in group),
                        'last_touch': max(point['timestamp'] for point in group),
                        'strength': len(group),
                        'touch_points': group
                    })
        
            # Group similar levels for lows
            low_groups = self._group_similar_levels(swing_lows, tolerance)
            for group in low_groups:
                if len(group) >= min_touches:
                    avg_level = np.mean([point['price'] for point in group])
                    liquidity_pools.append({
                        'level': avg_level,
                        'type': 'support',
                        'touches': len(group),
                        'first_touch': min(point['timestamp'] for point in group),
                        'last_touch': max(point['timestamp'] for point in group),
                        'strength': len(group),
                        'touch_points': group
                    })
        
            return liquidity_pools
        except Exception as e:
            logger.error(f"Error in detect_equal_highs_lows: {e}")
            raise
    
    def detect_liquidity_voids(self, df: pd.DataFrame, 
                             volume_threshold: float = 0.3) -> List[Dict]:
        """Detect liquidity voids (fair value gaps).
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume threshold for void detection
            
        Returns:
            List of detected liquidity voids
        """
        try:
            liquidity_voids = []
        
            # Calculate average volume
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            for i in range(1, len(df) - 1):
                prev_candle = df.iloc[i-1]
                current_candle = df.iloc[i]
                next_candle = df.iloc[i+1]
            
                # Bullish void: gap between previous high and next low
                if (current_candle['volume_ratio'] < volume_threshold and
                    prev_candle['high'] < next_candle['low']):
                
                    liquidity_voids.append({
                        'timestamp': current_candle.name,
                        'type': 'bullish_void',
                        'void_low': prev_candle['high'],
                        'void_high': next_candle['low'],
                        'void_size': next_candle['low'] - prev_candle['high'],
                        'volume': current_candle['volume'],
                        'volume_ratio': current_candle['volume_ratio'],
                        'is_filled': False
                    })
            
                # Bearish void: gap between previous low and next high
                elif (current_candle['volume_ratio'] < volume_threshold and
                      prev_candle['low'] > next_candle['high']):
                
                    liquidity_voids.append({
                        'timestamp': current_candle.name,
                        'type': 'bearish_void',
                        'void_high': prev_candle['low'],
                        'void_low': next_candle['high'],
                        'void_size': prev_candle['low'] - next_candle['high'],
                        'volume': current_candle['volume'],
                        'volume_ratio': current_candle['volume_ratio'],
                        'is_filled': False
                    })
        
            return liquidity_voids
        except Exception as e:
            logger.error(f"Error in detect_liquidity_voids: {e}")
            raise
    
    def _find_swing_points(self, series: pd.Series, point_type: str, 
                          window: int = 5) -> List[Dict]:
        """Find swing highs or lows in a price series."""
        try:
            swing_points = []
        
            for i in range(window, len(series) - window):
                if point_type == 'high':
                    # Check if current point is higher than surrounding points
                    is_swing = all(series.iloc[i] >= series.iloc[j] for j in range(i-window, i+window+1) if j != i)
                    if is_swing and series.iloc[i] == max(series.iloc[i-window:i+window+1]):
                        swing_points.append({
                            'timestamp': series.index[i],
                            'price': series.iloc[i],
                            'type': 'swing_high'
                        })
            
                elif point_type == 'low':
                    # Check if current point is lower than surrounding points
                    is_swing = all(series.iloc[i] <= series.iloc[j] for j in range(i-window, i+window+1) if j != i)
                    if is_swing and series.iloc[i] == min(series.iloc[i-window:i+window+1]):
                        swing_points.append({
                            'timestamp': series.index[i],
                            'price': series.iloc[i],
                            'type': 'swing_low'
                        })
        
            return swing_points
        except Exception as e:
            logger.error(f"Error in _find_swing_points: {e}")
            raise
    
    def _group_similar_levels(self, points: List[Dict], tolerance: float) -> List[List[Dict]]:
        """Group swing points with similar price levels."""
        try:
            if not points:
                return []
        
            # Sort points by price
            sorted_points = sorted(points, key=lambda x: x['price'])
            groups = []
            current_group = [sorted_points[0]]
        
            for i in range(1, len(sorted_points)):
                current_price = sorted_points[i]['price']
                group_avg = np.mean([p['price'] for p in current_group])
            
                if abs(current_price - group_avg) / group_avg <= tolerance:
                    current_group.append(sorted_points[i])
                else:
                    groups.append(current_group)
                    current_group = [sorted_points[i]]
        
            groups.append(current_group)
            return groups
        except Exception as e:
            logger.error(f"Error in _group_similar_levels: {e}")
            raise


class SmartMoneyConceptsAnalyzer:
    """Analyze Smart Money Concepts (SMC) patterns."""
    
    def __init__(self):
        try:
            self.smc_patterns = {}
            logger.info("Initialized SmartMoneyConceptsAnalyzer")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_break_of_structure(self, df: pd.DataFrame, 
                                 lookback: int = 20) -> List[Dict]:
        """Detect Break of Structure (BOS) patterns.
        
        Args:
            df: DataFrame with OHLC data
            lookback: Lookback period for structure analysis
            
        Returns:
            List of BOS patterns
        """
        try:
            bos_patterns = []
        
            # Find swing highs and lows
            swing_highs = self._find_swing_points(df['high'], 'high', window=5)
            swing_lows = self._find_swing_points(df['low'], 'low', window=5)
        
            # Combine and sort by timestamp
            all_swings = swing_highs + swing_lows
            all_swings.sort(key=lambda x: x['timestamp'])
        
            # Analyze structure breaks
            for i in range(1, len(all_swings)):
                current_swing = all_swings[i]
                prev_swing = all_swings[i-1]
            
                # Bullish BOS: Higher high after lower low
                if (current_swing['type'] == 'swing_high' and 
                    prev_swing['type'] == 'swing_low'):
                
                    # Find previous high to compare
                    prev_highs = [s for s in all_swings[:i] if s['type'] == 'swing_high']
                    if prev_highs and current_swing['price'] > max(h['price'] for h in prev_highs[-3:]):
                        bos_patterns.append({
                            'timestamp': current_swing['timestamp'],
                            'type': 'bullish_bos',
                            'break_level': current_swing['price'],
                            'previous_high': max(h['price'] for h in prev_highs[-3:]),
                            'structure_break': True
                        })
            
                # Bearish BOS: Lower low after higher high
                elif (current_swing['type'] == 'swing_low' and 
                      prev_swing['type'] == 'swing_high'):
                
                    # Find previous low to compare
                    prev_lows = [s for s in all_swings[:i] if s['type'] == 'swing_low']
                    if prev_lows and current_swing['price'] < min(l['price'] for l in prev_lows[-3:]):
                        bos_patterns.append({
                            'timestamp': current_swing['timestamp'],
                            'type': 'bearish_bos',
                            'break_level': current_swing['price'],
                            'previous_low': min(l['price'] for l in prev_lows[-3:]),
                            'structure_break': True
                        })
        
            return bos_patterns
        except Exception as e:
            logger.error(f"Error in detect_break_of_structure: {e}")
            raise
    
    def detect_change_of_character(self, df: pd.DataFrame) -> List[Dict]:
        """Detect Change of Character (CHoCH) patterns.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of CHoCH patterns
        """
        try:
            choch_patterns = []
        
            # Calculate market structure
            df['ema_fast'] = df['close'].ewm(span=10).mean()
            df['ema_slow'] = df['close'].ewm(span=20).mean()
        
            # Determine trend direction
            df['trend'] = np.where(df['ema_fast'] > df['ema_slow'], 'bullish', 'bearish')
            df['trend_change'] = df['trend'] != df['trend'].shift(1)
        
            # Find significant trend changes
            for i, (timestamp, row) in enumerate(df.iterrows()):
                if row['trend_change'] and i > 20:  # Skip initial periods
                
                    # Look for confirmation in subsequent periods
                    confirmation_window = df.iloc[i:i+5]
                    if len(confirmation_window) >= 3:
                        trend_consistency = (confirmation_window['trend'] == row['trend']).sum()
                    
                        if trend_consistency >= 3:  # At least 3 confirmations
                            choch_patterns.append({
                                'timestamp': timestamp,
                                'new_trend': row['trend'],
                                'previous_trend': df.iloc[i-1]['trend'],
                                'confirmation_strength': trend_consistency,
                                'price_at_change': row['close']
                            })
        
            return choch_patterns
        except Exception as e:
            logger.error(f"Error in detect_change_of_character: {e}")
            raise
    
    def detect_premium_discount_zones(self, df: pd.DataFrame, 
                                    fib_levels: List[float] = None) -> Dict:
        """Detect premium and discount zones using Fibonacci levels.
        
        Args:
            df: DataFrame with OHLC data
            fib_levels: Fibonacci retracement levels to use
            
        Returns:
            Dictionary with premium and discount zones
        """
        try:
            if fib_levels is None:
                fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        
            # Find recent swing high and low
            recent_data = df.tail(100)  # Last 100 periods
            swing_high = recent_data['high'].max()
            swing_low = recent_data['low'].min()
        
            # Calculate Fibonacci levels
            fib_range = swing_high - swing_low
            fib_zones = {}
        
            for level in fib_levels:
                fib_price = swing_low + (fib_range * level)
                fib_zones[f'fib_{level}'] = fib_price
        
            # Define premium and discount zones
            premium_threshold = swing_low + (fib_range * 0.618)  # Above 61.8%
            discount_threshold = swing_low + (fib_range * 0.382)  # Below 38.2%
        
            current_price = df['close'].iloc[-1]
        
            if current_price > premium_threshold:
                current_zone = 'premium'
            elif current_price < discount_threshold:
                current_zone = 'discount'
            else:
                current_zone = 'equilibrium'
        
            return {
                'swing_high': swing_high,
                'swing_low': swing_low,
                'fib_levels': fib_zones,
                'premium_threshold': premium_threshold,
                'discount_threshold': discount_threshold,
                'current_price': current_price,
                'current_zone': current_zone
            }
        except Exception as e:
            logger.error(f"Error in detect_premium_discount_zones: {e}")
            raise
    
    def _find_swing_points(self, series: pd.Series, point_type: str, 
                          window: int = 5) -> List[Dict]:
        """Find swing highs or lows in a price series."""
        try:
            swing_points = []
        
            for i in range(window, len(series) - window):
                if point_type == 'high':
                    is_swing = all(series.iloc[i] >= series.iloc[j] for j in range(i-window, i+window+1) if j != i)
                    if is_swing and series.iloc[i] == max(series.iloc[i-window:i+window+1]):
                        swing_points.append({
                            'timestamp': series.index[i],
                            'price': series.iloc[i],
                            'type': 'swing_high'
                        })
            
                elif point_type == 'low':
                    is_swing = all(series.iloc[i] <= series.iloc[j] for j in range(i-window, i+window+1) if j != i)
                    if is_swing and series.iloc[i] == min(series.iloc[i-window:i+window+1]):
                        swing_points.append({
                            'timestamp': series.index[i],
                            'price': series.iloc[i],
                            'type': 'swing_low'
                        })
        
            return swing_points
        except Exception as e:
            logger.error(f"Error in _find_swing_points: {e}")
            raise
