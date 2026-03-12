import logging
logger = logging.getLogger(__name__)
"""Market Manipulation and Price Action Analysis Module."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
from datetime import datetime, timedelta
import numpy
import pandas


class ManipulationType(Enum):
    """Types of market manipulation patterns."""
    STOP_HUNT = "stop_hunt"
    LIQUIDITY_GRAB = "liquidity_grab"
    FALSE_BREAKOUT = "false_breakout"
    WYCKOFF_SPRING = "wyckoff_spring"
    UPTHRUST = "upthrust"
    SHAKE_OUT = "shake_out"


class ManipulationPatterns:
    """Detect and analyze market manipulation patterns."""
    
    def __init__(self):
        try:
            self.manipulation_history = []
            logger.info("Initialized ManipulationPatterns")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_stop_hunts(self, df: pd.DataFrame, 
                         lookback_periods: int = 50) -> List[Dict]:
        """Detect stop hunting patterns."""
        try:
            stop_hunts = []
        
            if len(df) < lookback_periods:
                return stop_hunts
        
            # Find significant highs and lows
            highs = df['high'].rolling(10).max()
            lows = df['low'].rolling(10).min()
        
            for i in range(lookback_periods, len(df)):
                current_bar = df.iloc[i]
            
                # Check for stop hunt above resistance
                recent_high = highs.iloc[i-lookback_periods:i].max()
                if (current_bar['high'] > recent_high and 
                    current_bar['close'] < recent_high):
                
                    stop_hunts.append({
                        'timestamp': df.index[i],
                        'type': ManipulationType.STOP_HUNT,
                        'direction': 'bearish',
                        'level_breached': recent_high,
                        'close_price': current_bar['close'],
                        'volume': current_bar['volume'],
                        'manipulation_strength': self._calculate_manipulation_strength(
                            current_bar, recent_high, 'bearish'
                        )
                    })
            
                # Check for stop hunt below support
                recent_low = lows.iloc[i-lookback_periods:i].min()
                if (current_bar['low'] < recent_low and 
                    current_bar['close'] > recent_low):
                
                    stop_hunts.append({
                        'timestamp': df.index[i],
                        'type': ManipulationType.STOP_HUNT,
                        'direction': 'bullish',
                        'level_breached': recent_low,
                        'close_price': current_bar['close'],
                        'volume': current_bar['volume'],
                        'manipulation_strength': self._calculate_manipulation_strength(
                            current_bar, recent_low, 'bullish'
                        )
                    })
        
            return stop_hunts
        except Exception as e:
            logger.error(f"Error in detect_stop_hunts: {e}")
            raise
    
    def detect_liquidity_grabs(self, df: pd.DataFrame) -> List[Dict]:
        """Detect liquidity grab patterns."""
        try:
            liquidity_grabs = []
        
            # Calculate volume moving average
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(20).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_ma']
        
            # Look for high volume spikes with quick reversals
            for i in range(20, len(df_copy)):
                current = df_copy.iloc[i]
                previous = df_copy.iloc[i-1]
            
                # High volume condition
                if current['volume_ratio'] > 2.0:
                    # Check for quick reversal patterns
                    if self._is_liquidity_grab_pattern(df_copy.iloc[i-5:i+1]):
                        liquidity_grabs.append({
                            'timestamp': df_copy.index[i],
                            'type': ManipulationType.LIQUIDITY_GRAB,
                            'volume_spike': current['volume_ratio'],
                            'price_action': self._analyze_price_action(df_copy.iloc[i-5:i+1]),
                            'effectiveness': self._calculate_grab_effectiveness(df_copy, i)
                        })
        
            return liquidity_grabs
        except Exception as e:
            logger.error(f"Error in detect_liquidity_grabs: {e}")
            raise
    
    def _calculate_manipulation_strength(self, bar: pd.Series, 
                                       level: float, direction: str) -> float:
        """Calculate the strength of manipulation pattern."""
        try:
            if direction == 'bearish':
                wick_size = bar['high'] - bar['close']
                total_range = bar['high'] - bar['low']
            else:
                wick_size = bar['close'] - bar['low']
                total_range = bar['high'] - bar['low']
        
            if total_range == 0:
                return 0.0
        
            wick_ratio = wick_size / total_range
            return min(1.0, wick_ratio * 2)  # Normalize to 0-1
        except Exception as e:
            logger.error(f"Error in _calculate_manipulation_strength: {e}")
            raise
    
    def _is_liquidity_grab_pattern(self, window_df: pd.DataFrame) -> bool:
        """Check if price action represents liquidity grab."""
        try:
            if len(window_df) < 3:
                return False
        
            # Look for spike and reversal pattern
            max_high = window_df['high'].max()
            min_low = window_df['low'].min()
        
            # Check if we have a significant move followed by reversal
            price_range = max_high - min_low
            last_close = window_df['close'].iloc[-1]
        
            # Simple heuristic for liquidity grab
            return price_range > (last_close * 0.002)  # 0.2% range threshold
        except Exception as e:
            logger.error(f"Error in _is_liquidity_grab_pattern: {e}")
            raise
    
    def _analyze_price_action(self, window_df: pd.DataFrame) -> Dict:
        """Analyze price action characteristics."""
        return {
            'range': window_df['high'].max() - window_df['low'].min(),
            'direction': 'up' if window_df['close'].iloc[-1] > window_df['open'].iloc[0] else 'down',
            'volatility': window_df['close'].std()
        }
    
    def _calculate_grab_effectiveness(self, df: pd.DataFrame, index: int) -> float:
        """Calculate effectiveness of liquidity grab."""
        # Look ahead to see if price moved in expected direction
        try:
            if index + 5 >= len(df):
                return 0.5  # Unknown
        
            current_price = df['close'].iloc[index]
            future_price = df['close'].iloc[index + 5]
        
            return abs(future_price - current_price) / current_price
        except Exception as e:
            logger.error(f"Error in _calculate_grab_effectiveness: {e}")
            raise


class BreakerBlockIdentification:
    """Identify and analyze breaker blocks (mitigated order blocks)."""
    
    def __init__(self):
        try:
            self.breaker_blocks = []
            logger.info("Initialized BreakerBlockIdentification")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def identify_breaker_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """Identify breaker block formations."""
        try:
            breaker_blocks = []
        
            # First identify order blocks
            order_blocks = self._identify_order_blocks(df)
        
            # Then check which ones have been mitigated (become breakers)
            for block in order_blocks:
                mitigation_info = self._check_mitigation(df, block)
                if mitigation_info['is_mitigated']:
                    breaker_blocks.append({
                        **block,
                        'type': 'breaker_block',
                        'mitigation_info': mitigation_info,
                        'expected_reaction': self._predict_breaker_reaction(block)
                    })
        
            return breaker_blocks
        except Exception as e:
            logger.error(f"Error in identify_breaker_blocks: {e}")
            raise
    
    def _identify_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """Identify potential order blocks."""
        try:
            order_blocks = []
        
            # Look for strong moves followed by consolidation
            for i in range(20, len(df) - 10):
                # Check for strong bullish move
                if self._is_strong_move(df.iloc[i-5:i], 'bullish'):
                    block = {
                        'timestamp': df.index[i-1],
                        'type': 'bullish_order_block',
                        'high': df.iloc[i-1]['high'],
                        'low': df.iloc[i-1]['low'],
                        'formation_strength': self._calculate_block_strength(df.iloc[i-5:i])
                    }
                    order_blocks.append(block)
            
                # Check for strong bearish move
                elif self._is_strong_move(df.iloc[i-5:i], 'bearish'):
                    block = {
                        'timestamp': df.index[i-1],
                        'type': 'bearish_order_block',
                        'high': df.iloc[i-1]['high'],
                        'low': df.iloc[i-1]['low'],
                        'formation_strength': self._calculate_block_strength(df.iloc[i-5:i])
                    }
                    order_blocks.append(block)
        
            return order_blocks
        except Exception as e:
            logger.error(f"Error in _identify_order_blocks: {e}")
            raise
    
    def _is_strong_move(self, window_df: pd.DataFrame, direction: str) -> bool:
        """Check if price action represents strong directional move."""
        try:
            if len(window_df) < 3:
                return False
        
            start_price = window_df['open'].iloc[0]
            end_price = window_df['close'].iloc[-1]
        
            if direction == 'bullish':
                return (end_price - start_price) / start_price > 0.005  # 0.5% move
            else:
                return (start_price - end_price) / start_price > 0.005  # 0.5% move
        except Exception as e:
            logger.error(f"Error in _is_strong_move: {e}")
            raise
    
    def _calculate_block_strength(self, window_df: pd.DataFrame) -> float:
        """Calculate strength of order block formation."""
        try:
            price_change = abs(window_df['close'].iloc[-1] - window_df['open'].iloc[0])
            avg_volume = window_df['volume'].mean()
        
            # Simple strength calculation
            return min(1.0, (price_change / window_df['open'].iloc[0]) * 100)
        except Exception as e:
            logger.error(f"Error in _calculate_block_strength: {e}")
            raise
    
    def _check_mitigation(self, df: pd.DataFrame, block: Dict) -> Dict:
        """Check if order block has been mitigated."""
        try:
            block_timestamp = block['timestamp']
            block_high = block['high']
            block_low = block['low']
        
            # Look for price returning to block after formation
            future_data = df[df.index > block_timestamp]
        
            for timestamp, row in future_data.iterrows():
                # Check if price has returned to block zone
                if block_low <= row['low'] <= block_high or block_low <= row['high'] <= block_high:
                    return {
                        'is_mitigated': True,
                        'mitigation_timestamp': timestamp,
                        'mitigation_price': row['close']
                    }
        
            return {'is_mitigated': False}
        except Exception as e:
            logger.error(f"Error in _check_mitigation: {e}")
            raise
    
    def _predict_breaker_reaction(self, block: Dict) -> Dict:
        """Predict expected reaction from breaker block."""
        try:
            if block['type'] == 'bullish_order_block':
                return {
                    'expected_direction': 'bearish',
                    'confidence': 0.7,
                    'target_distance': 0.01  # 1% move expected
                }
            else:
                return {
                    'expected_direction': 'bullish',
                    'confidence': 0.7,
                    'target_distance': 0.01  # 1% move expected
                }
        except Exception as e:
            logger.error(f"Error in _predict_breaker_reaction: {e}")
            raise


class SmartMoneyOperations:
    """Analyze smart money operations and institutional footprints."""
    
    def __init__(self):
        try:
            self.operations_history = []
            logger.info("Initialized SmartMoneyOperations")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_smart_money_operations(self, df: pd.DataFrame) -> List[Dict]:
        """Detect smart money operations in price action."""
        try:
            operations = []
        
            # Detect accumulation/distribution phases
            accumulation_phases = self._detect_accumulation_phases(df)
            operations.extend(accumulation_phases)
        
            # Detect markup/markdown phases
            markup_phases = self._detect_markup_phases(df)
            operations.extend(markup_phases)
        
            # Detect distribution phases
            distribution_phases = self._detect_distribution_phases(df)
            operations.extend(distribution_phases)
        
            return operations
        except Exception as e:
            logger.error(f"Error in detect_smart_money_operations: {e}")
            raise
    
    def _detect_accumulation_phases(self, df: pd.DataFrame) -> List[Dict]:
        """Detect smart money accumulation phases."""
        try:
            accumulation_phases = []
        
            # Look for sideways price action with increasing volume
            window_size = 20
        
            for i in range(window_size, len(df) - window_size):
                window = df.iloc[i-window_size:i+window_size]
            
                # Check for sideways price action
                price_range = window['high'].max() - window['low'].min()
                avg_price = window['close'].mean()
            
                if price_range / avg_price < 0.02:  # Less than 2% range
                    # Check volume characteristics
                    volume_trend = self._analyze_volume_trend(window)
                
                    if volume_trend['increasing']:
                        accumulation_phases.append({
                            'timestamp': df.index[i],
                            'type': 'accumulation',
                            'duration': window_size * 2,
                            'price_range': price_range,
                            'volume_characteristics': volume_trend,
                            'confidence': self._calculate_phase_confidence(window, 'accumulation')
                        })
        
            return accumulation_phases
        except Exception as e:
            logger.error(f"Error in _detect_accumulation_phases: {e}")
            raise
    
    def _detect_markup_phases(self, df: pd.DataFrame) -> List[Dict]:
        """Detect markup phases (strong upward moves)."""
        try:
            markup_phases = []
        
            # Look for sustained upward moves with specific characteristics
            for i in range(10, len(df)):
                window = df.iloc[i-10:i]
            
                # Check for consistent upward movement
                if self._is_markup_phase(window):
                    markup_phases.append({
                        'timestamp': df.index[i],
                        'type': 'markup',
                        'price_change': (window['close'].iloc[-1] - window['open'].iloc[0]) / window['open'].iloc[0],
                        'volume_profile': self._analyze_volume_profile(window),
                        'strength': self._calculate_markup_strength(window)
                    })
        
            return markup_phases
        except Exception as e:
            logger.error(f"Error in _detect_markup_phases: {e}")
            raise
    
    def _detect_distribution_phases(self, df: pd.DataFrame) -> List[Dict]:
        """Detect distribution phases (smart money selling)."""
        try:
            distribution_phases = []
        
            # Similar to accumulation but with different volume characteristics
            window_size = 20
        
            for i in range(window_size, len(df) - window_size):
                window = df.iloc[i-window_size:i+window_size]
            
                # Check for sideways action at higher prices
                if self._is_distribution_pattern(window):
                    distribution_phases.append({
                        'timestamp': df.index[i],
                        'type': 'distribution',
                        'price_level': window['close'].mean(),
                        'volume_characteristics': self._analyze_volume_trend(window),
                        'distribution_strength': self._calculate_distribution_strength(window)
                    })
        
            return distribution_phases
        except Exception as e:
            logger.error(f"Error in _detect_distribution_phases: {e}")
            raise
    
    def _analyze_volume_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze volume trend characteristics."""
        try:
            volumes = df['volume'].values
        
            # Simple trend analysis
            first_half = volumes[:len(volumes)//2]
            second_half = volumes[len(volumes)//2:]
        
            return {
                'increasing': second_half.mean() > first_half.mean() * 1.1,
                'avg_volume': volumes.mean(),
                'volume_volatility': volumes.std()
            }
        except Exception as e:
            logger.error(f"Error in _analyze_volume_trend: {e}")
            raise
    
    def _is_markup_phase(self, window: pd.DataFrame) -> bool:
        """Check if window represents markup phase."""
        try:
            start_price = window['open'].iloc[0]
            end_price = window['close'].iloc[-1]
        
            # Must have significant upward movement
            return (end_price - start_price) / start_price > 0.01  # 1% minimum
        except Exception as e:
            logger.error(f"Error in _is_markup_phase: {e}")
            raise
    
    def _is_distribution_pattern(self, window: pd.DataFrame) -> bool:
        """Check if window represents distribution pattern."""
        # High prices with sideways action
        try:
            price_range = window['high'].max() - window['low'].min()
            avg_price = window['close'].mean()
        
            return (price_range / avg_price < 0.015 and  # Tight range
                    avg_price > window['close'].iloc[0] * 1.02)  # At elevated prices
        except Exception as e:
            logger.error(f"Error in _is_distribution_pattern: {e}")
            raise
    
    def _calculate_phase_confidence(self, window: pd.DataFrame, phase_type: str) -> float:
        """Calculate confidence in phase identification."""
        # Simple confidence calculation based on volume and price action
        try:
            volume_consistency = 1.0 - (window['volume'].std() / window['volume'].mean())
            return min(0.9, max(0.3, volume_consistency))
        except Exception as e:
            logger.error(f"Error in _calculate_phase_confidence: {e}")
            raise
    
    def _analyze_volume_profile(self, window: pd.DataFrame) -> Dict:
        """Analyze volume profile characteristics."""
        return {
            'total_volume': window['volume'].sum(),
            'avg_volume': window['volume'].mean(),
            'volume_distribution': 'even'  # Simplified
        }
    
    def _calculate_markup_strength(self, window: pd.DataFrame) -> float:
        """Calculate strength of markup phase."""
        try:
            price_change = (window['close'].iloc[-1] - window['open'].iloc[0]) / window['open'].iloc[0]
            return min(1.0, price_change * 50)  # Normalize
        except Exception as e:
            logger.error(f"Error in _calculate_markup_strength: {e}")
            raise
    
    def _calculate_distribution_strength(self, window: pd.DataFrame) -> float:
        """Calculate strength of distribution phase."""
        try:
            volume_increase = self._analyze_volume_trend(window)['increasing']
            return 0.8 if volume_increase else 0.4
        except Exception as e:
            logger.error(f"Error in _calculate_distribution_strength: {e}")
            raise


class InstitutionalFootprints:
    """Detect institutional trading footprints."""
    
    def __init__(self):
        try:
            self.footprints = []
            logger.info("Initialized InstitutionalFootprints")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_institutional_activity(self, df: pd.DataFrame) -> List[Dict]:
        """Detect signs of institutional trading activity."""
        try:
            footprints = []
        
            # Large volume spikes
            volume_spikes = self._detect_volume_spikes(df)
            footprints.extend(volume_spikes)
        
            # Iceberg order patterns
            iceberg_patterns = self._detect_iceberg_orders(df)
            footprints.extend(iceberg_patterns)
        
            # Block trading patterns
            block_trades = self._detect_block_trades(df)
            footprints.extend(block_trades)
        
            return footprints
        except Exception as e:
            logger.error(f"Error in detect_institutional_activity: {e}")
            raise
    
    def _detect_volume_spikes(self, df: pd.DataFrame) -> List[Dict]:
        """Detect unusual volume spikes."""
        try:
            volume_spikes = []
        
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(20).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_ma']
        
            # Find significant volume spikes
            spike_threshold = 3.0
        
            for i, (timestamp, row) in enumerate(df_copy.iterrows()):
                if row['volume_ratio'] > spike_threshold and not pd.isna(row['volume_ratio']):
                    volume_spikes.append({
                        'timestamp': timestamp,
                        'type': 'volume_spike',
                        'volume_ratio': row['volume_ratio'],
                        'price_impact': self._calculate_price_impact(df_copy, i),
                        'institutional_probability': min(0.9, row['volume_ratio'] / 10)
                    })
        
            return volume_spikes
        except Exception as e:
            logger.error(f"Error in _detect_volume_spikes: {e}")
            raise
    
    def _detect_iceberg_orders(self, df: pd.DataFrame) -> List[Dict]:
        """Detect iceberg order patterns."""
        # This would require order book data in practice
        # Simplified detection based on volume and price action
        try:
            iceberg_orders = []
        
            for i in range(10, len(df)):
                window = df.iloc[i-10:i]
            
                # Look for consistent volume with minimal price movement
                if self._is_iceberg_pattern(window):
                    iceberg_orders.append({
                        'timestamp': df.index[i],
                        'type': 'iceberg_order',
                        'estimated_size': window['volume'].sum(),
                        'price_stability': self._calculate_price_stability(window)
                    })
        
            return iceberg_orders
        except Exception as e:
            logger.error(f"Error in _detect_iceberg_orders: {e}")
            raise
    
    def _detect_block_trades(self, df: pd.DataFrame) -> List[Dict]:
        """Detect block trading patterns."""
        try:
            block_trades = []
        
            # Look for single bars with exceptionally high volume
            volume_threshold = df['volume'].quantile(0.95)
        
            for timestamp, row in df.iterrows():
                if row['volume'] > volume_threshold:
                    block_trades.append({
                        'timestamp': timestamp,
                        'type': 'block_trade',
                        'volume': row['volume'],
                        'price': row['close'],
                        'market_impact': abs(row['close'] - row['open']) / row['open']
                    })
        
            return block_trades
        except Exception as e:
            logger.error(f"Error in _detect_block_trades: {e}")
            raise
    
    def _calculate_price_impact(self, df: pd.DataFrame, index: int) -> float:
        """Calculate price impact of volume spike."""
        try:
            if index == 0:
                return 0.0
        
            current_price = df['close'].iloc[index]
            previous_price = df['close'].iloc[index-1]
        
            return abs(current_price - previous_price) / previous_price
        except Exception as e:
            logger.error(f"Error in _calculate_price_impact: {e}")
            raise
    
    def _is_iceberg_pattern(self, window: pd.DataFrame) -> bool:
        """Check if window shows iceberg order pattern."""
        # High volume with low price volatility
        try:
            avg_volume = window['volume'].mean()
            price_volatility = window['close'].std()
        
            volume_threshold = window['volume'].quantile(0.8)
        
            return (avg_volume > volume_threshold and 
                    price_volatility < window['close'].mean() * 0.001)
        except Exception as e:
            logger.error(f"Error in _is_iceberg_pattern: {e}")
            raise
    
    def _calculate_price_stability(self, window: pd.DataFrame) -> float:
        """Calculate price stability during potential iceberg execution."""
        try:
            price_range = window['high'].max() - window['low'].min()
            avg_price = window['close'].mean()
        
            return 1.0 - (price_range / avg_price) if avg_price > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_price_stability: {e}")
            raise


class TrappedTraderAnalysis:
    """Analyze trapped trader scenarios and potential reversals."""
    
    def __init__(self):
        try:
            self.trapped_scenarios = []
            logger.info("Initialized TrappedTraderAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def identify_trapped_traders(self, df: pd.DataFrame) -> List[Dict]:
        """Identify scenarios where traders might be trapped."""
        try:
            trapped_scenarios = []
        
            # False breakout scenarios
            false_breakouts = self._detect_false_breakouts(df)
            trapped_scenarios.extend(false_breakouts)
        
            # Stop hunt scenarios
            stop_hunts = self._detect_stop_hunt_scenarios(df)
            trapped_scenarios.extend(stop_hunts)
        
            # Liquidity trap scenarios
            liquidity_traps = self._detect_liquidity_traps(df)
            trapped_scenarios.extend(liquidity_traps)
        
            return trapped_scenarios
        except Exception as e:
            logger.error(f"Error in identify_trapped_traders: {e}")
            raise
    
    def _detect_false_breakouts(self, df: pd.DataFrame) -> List[Dict]:
        """Detect false breakout scenarios."""
        try:
            false_breakouts = []
        
            # Look for breakouts that quickly reverse
            for i in range(20, len(df) - 5):
                # Check for breakout above resistance
                resistance_level = df['high'].iloc[i-20:i].max()
            
                if (df['high'].iloc[i] > resistance_level and
                    df['close'].iloc[i+1:i+5].min() < resistance_level):
                
                    false_breakouts.append({
                        'timestamp': df.index[i],
                        'type': 'false_breakout_bearish',
                        'breakout_level': resistance_level,
                        'trapped_traders': 'long_positions',
                        'reversal_strength': self._calculate_reversal_strength(df, i, i+5)
                    })
            
                # Check for breakout below support
                support_level = df['low'].iloc[i-20:i].min()
            
                if (df['low'].iloc[i] < support_level and
                    df['close'].iloc[i+1:i+5].max() > support_level):
                
                    false_breakouts.append({
                        'timestamp': df.index[i],
                        'type': 'false_breakout_bullish',
                        'breakout_level': support_level,
                        'trapped_traders': 'short_positions',
                        'reversal_strength': self._calculate_reversal_strength(df, i, i+5)
                    })
        
            return false_breakouts
        except Exception as e:
            logger.error(f"Error in _detect_false_breakouts: {e}")
            raise
    
    def _detect_stop_hunt_scenarios(self, df: pd.DataFrame) -> List[Dict]:
        """Detect stop hunting scenarios that trap traders."""
        try:
            stop_hunts = []
        
            # Look for quick moves that reverse rapidly
            for i in range(5, len(df) - 5):
                current_bar = df.iloc[i]
            
                # Check for stop hunt pattern
                if self._is_stop_hunt_pattern(df, i):
                    stop_hunts.append({
                        'timestamp': df.index[i],
                        'type': 'stop_hunt',
                        'hunt_direction': self._determine_hunt_direction(df, i),
                        'trapped_volume': current_bar['volume'],
                        'recovery_speed': self._calculate_recovery_speed(df, i)
                    })
        
            return stop_hunts
        except Exception as e:
            logger.error(f"Error in _detect_stop_hunt_scenarios: {e}")
            raise
    
    def _detect_liquidity_traps(self, df: pd.DataFrame) -> List[Dict]:
        """Detect liquidity trap scenarios."""
        try:
            liquidity_traps = []
        
            # Look for areas where price gets trapped between levels
            for i in range(30, len(df) - 10):
                window = df.iloc[i-30:i]
            
                if self._is_liquidity_trap_pattern(window):
                    liquidity_traps.append({
                        'timestamp': df.index[i],
                        'type': 'liquidity_trap',
                        'trap_range': {
                            'high': window['high'].max(),
                            'low': window['low'].min()
                        },
                        'trap_duration': 30,
                        'breakout_probability': self._calculate_breakout_probability(window)
                    })
        
            return liquidity_traps
        except Exception as e:
            logger.error(f"Error in _detect_liquidity_traps: {e}")
            raise
    
    def _calculate_reversal_strength(self, df: pd.DataFrame, 
                                   start_idx: int, end_idx: int) -> float:
        """Calculate strength of price reversal."""
        try:
            if end_idx >= len(df):
                return 0.0
        
            breakout_price = df['close'].iloc[start_idx]
            reversal_price = df['close'].iloc[end_idx]
        
            return abs(reversal_price - breakout_price) / breakout_price
        except Exception as e:
            logger.error(f"Error in _calculate_reversal_strength: {e}")
            raise
    
    def _is_stop_hunt_pattern(self, df: pd.DataFrame, index: int) -> bool:
        """Check if pattern represents stop hunting."""
        try:
            if index < 5 or index >= len(df) - 5:
                return False
        
            current = df.iloc[index]
            before = df.iloc[index-5:index]
            after = df.iloc[index+1:index+6]
        
            # Look for spike and reversal pattern
            spike_up = current['high'] > before['high'].max() * 1.001
            reversal_down = after['close'].min() < current['close'] * 0.999
        
            spike_down = current['low'] < before['low'].min() * 0.999
            reversal_up = after['close'].max() > current['close'] * 1.001
        
            return (spike_up and reversal_down) or (spike_down and reversal_up)
        except Exception as e:
            logger.error(f"Error in _is_stop_hunt_pattern: {e}")
            raise
    
    def _determine_hunt_direction(self, df: pd.DataFrame, index: int) -> str:
        """Determine direction of stop hunt."""
        try:
            current = df.iloc[index]
            before_avg = df.iloc[index-5:index]['close'].mean()
        
            if current['high'] > before_avg * 1.001:
                return 'upward_hunt'
            elif current['low'] < before_avg * 0.999:
                return 'downward_hunt'
            else:
                return 'unknown'
        except Exception as e:
            logger.error(f"Error in _determine_hunt_direction: {e}")
            raise
    
    def _calculate_recovery_speed(self, df: pd.DataFrame, index: int) -> float:
        """Calculate speed of recovery after stop hunt."""
        try:
            if index >= len(df) - 5:
                return 0.0
        
            hunt_price = df['close'].iloc[index]
            recovery_price = df['close'].iloc[index+5]
        
            return abs(recovery_price - hunt_price) / hunt_price
        except Exception as e:
            logger.error(f"Error in _calculate_recovery_speed: {e}")
            raise
    
    def _is_liquidity_trap_pattern(self, window: pd.DataFrame) -> bool:
        """Check if pattern represents liquidity trap."""
        try:
            price_range = window['high'].max() - window['low'].min()
            avg_price = window['close'].mean()
        
            # Tight range indicates potential trap
            return price_range / avg_price < 0.02  # Less than 2% range
        except Exception as e:
            logger.error(f"Error in _is_liquidity_trap_pattern: {e}")
            raise
    
    def _calculate_breakout_probability(self, window: pd.DataFrame) -> float:
        """Calculate probability of breakout from trap."""
        # Simple heuristic based on volume and time
        try:
            volume_increase = window['volume'].iloc[-10:].mean() > window['volume'].iloc[:10].mean()
        
            return 0.7 if volume_increase else 0.3
        except Exception as e:
            logger.error(f"Error in _calculate_breakout_probability: {e}")
            raise
