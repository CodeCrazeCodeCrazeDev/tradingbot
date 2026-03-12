import logging
logger = logging.getLogger(__name__)
"""Liquidity Absorption Analysis for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
from datetime import datetime, timedelta
import numpy
import pandas


class AbsorptionType(Enum):
    """Types of liquidity absorption patterns."""
    BUYING_ABSORPTION = "buying_absorption"
    SELLING_ABSORPTION = "selling_absorption"
    NEUTRAL_ABSORPTION = "neutral_absorption"


class AbsorptionStrength(Enum):
    """Strength levels of absorption patterns."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXTREME = "extreme"


class AbsorptionPatterns:
    """Detect and analyze liquidity absorption patterns."""
    
    def __init__(self):
        try:
            self.absorption_history = []
            self.absorption_zones = {}
            logger.info("Initialized AbsorptionPatterns")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_absorption_patterns(self, df: pd.DataFrame, 
                                 volume_threshold: float = 2.0,
                                 price_stagnation_threshold: float = 0.002) -> List[Dict]:
        """Detect liquidity absorption patterns in market data.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume threshold for absorption detection
            price_stagnation_threshold: Price movement threshold for stagnation
            
        Returns:
            List of detected absorption patterns
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for absorption analysis")
                return []
        
            absorption_patterns = []
        
            # Calculate required metrics
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(20).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_ma']
            df_copy['price_change'] = df_copy['close'].pct_change()
            df_copy['price_range'] = (df_copy['high'] - df_copy['low']) / df_copy['close']
        
            # Sliding window analysis
            window_size = 5
        
            for i in range(window_size, len(df_copy)):
                window_data = df_copy.iloc[i-window_size:i+1]
            
                # Check for high volume with limited price movement
                avg_volume_ratio = window_data['volume_ratio'].mean()
                total_price_change = abs(window_data['price_change'].sum())
                avg_range = window_data['price_range'].mean()
            
                if (avg_volume_ratio > volume_threshold and 
                    total_price_change < price_stagnation_threshold):
                
                    # Determine absorption type
                    absorption_type = self._determine_absorption_type(window_data)
                    absorption_strength = self._calculate_absorption_strength(
                        avg_volume_ratio, total_price_change, avg_range
                    )
                
                    # Calculate absorption zone
                    absorption_zone = self._calculate_absorption_zone(window_data)
                
                    absorption_patterns.append({
                        'timestamp': window_data.index[-1],
                        'start_time': window_data.index[0],
                        'end_time': window_data.index[-1],
                        'type': absorption_type,
                        'strength': absorption_strength,
                        'volume_ratio': avg_volume_ratio,
                        'price_stagnation': total_price_change,
                        'absorption_zone': absorption_zone,
                        'duration': len(window_data),
                        'total_volume': window_data['volume'].sum()
                    })
        
            return absorption_patterns
        except Exception as e:
            logger.error(f"Error in detect_absorption_patterns: {e}")
            raise
    
    def analyze_absorption_effectiveness(self, absorption_patterns: List[Dict], 
                                      df: pd.DataFrame, 
                                      lookforward_periods: int = 20) -> List[Dict]:
        """Analyze the effectiveness of detected absorption patterns.
        
        Args:
            absorption_patterns: List of detected absorption patterns
            df: DataFrame with price data
            lookforward_periods: Periods to look ahead for effectiveness analysis
            
        Returns:
            List of absorption patterns with effectiveness analysis
        """
        try:
            analyzed_patterns = []
        
            for pattern in absorption_patterns:
                pattern_copy = pattern.copy()
                end_time = pattern['end_time']
            
                # Get future price data
                future_mask = df.index > end_time
                future_data = df[future_mask].head(lookforward_periods)
            
                if len(future_data) > 0:
                    effectiveness_analysis = self._calculate_effectiveness_metrics(
                        pattern, future_data
                    )
                    pattern_copy.update(effectiveness_analysis)
            
                analyzed_patterns.append(pattern_copy)
        
            return analyzed_patterns
        except Exception as e:
            logger.error(f"Error in analyze_absorption_effectiveness: {e}")
            raise
    
    def detect_iceberg_orders(self, df: pd.DataFrame, 
                            min_volume_ratio: float = 3.0,
                            max_price_impact: float = 0.001) -> List[Dict]:
        """Detect potential iceberg order patterns.
        
        Args:
            df: DataFrame with OHLC and volume data
            min_volume_ratio: Minimum volume ratio for iceberg detection
            max_price_impact: Maximum price impact for iceberg orders
            
        Returns:
            List of detected iceberg order patterns
        """
        try:
            if 'volume' not in df.columns:
                return []
        
            iceberg_patterns = []
        
            # Calculate metrics
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(10).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_ma']
            df_copy['price_impact'] = abs(df_copy['close'].pct_change())
        
            # Detect iceberg patterns
            for i, (timestamp, row) in enumerate(df_copy.iterrows()):
                if (row['volume_ratio'] > min_volume_ratio and 
                    row['price_impact'] < max_price_impact and
                    not pd.isna(row['volume_ratio'])):
                
                    # Analyze surrounding periods for confirmation
                    start_idx = max(0, i - 2)
                    end_idx = min(len(df_copy), i + 3)
                    surrounding_data = df_copy.iloc[start_idx:end_idx]
                
                    # Check for consistent pattern
                    consistent_high_volume = (surrounding_data['volume_ratio'] > min_volume_ratio * 0.7).sum()
                    consistent_low_impact = (surrounding_data['price_impact'] < max_price_impact * 2).sum()
                
                    if consistent_high_volume >= 3 and consistent_low_impact >= 3:
                        iceberg_patterns.append({
                            'timestamp': timestamp,
                            'volume': row['volume'],
                            'volume_ratio': row['volume_ratio'],
                            'price_impact': row['price_impact'],
                            'price': row['close'],
                            'confidence': min(consistent_high_volume, consistent_low_impact) / 5,
                            'pattern_type': 'iceberg_order'
                        })
        
            return iceberg_patterns
        except Exception as e:
            logger.error(f"Error in detect_iceberg_orders: {e}")
            raise
    
    def _determine_absorption_type(self, window_data: pd.DataFrame) -> AbsorptionType:
        """Determine the type of absorption pattern."""
        # Analyze price action within the window
        try:
            open_price = window_data['open'].iloc[0]
            close_price = window_data['close'].iloc[-1]
            high_price = window_data['high'].max()
            low_price = window_data['low'].min()
        
            # Calculate price position within range
            price_range = high_price - low_price
            if price_range == 0:
                return AbsorptionType.NEUTRAL_ABSORPTION
        
            close_position = (close_price - low_price) / price_range
        
            # Analyze volume distribution
            bullish_volume = 0
            bearish_volume = 0
        
            for _, row in window_data.iterrows():
                if row['close'] > row['open']:
                    bullish_volume += row['volume']
                elif row['close'] < row['open']:
                    bearish_volume += row['volume']
        
            total_volume = bullish_volume + bearish_volume
            if total_volume == 0:
                return AbsorptionType.NEUTRAL_ABSORPTION
        
            bullish_ratio = bullish_volume / total_volume
        
            # Determine absorption type
            if close_position > 0.6 and bullish_ratio > 0.6:
                return AbsorptionType.BUYING_ABSORPTION
            elif close_position < 0.4 and bullish_ratio < 0.4:
                return AbsorptionType.SELLING_ABSORPTION
            else:
                return AbsorptionType.NEUTRAL_ABSORPTION
        except Exception as e:
            logger.error(f"Error in _determine_absorption_type: {e}")
            raise
    
    def _calculate_absorption_strength(self, volume_ratio: float, 
                                     price_stagnation: float, 
                                     avg_range: float) -> AbsorptionStrength:
        """Calculate the strength of absorption pattern."""
        # Combine volume and price stagnation metrics
        try:
            strength_score = volume_ratio * (1 - price_stagnation) * (1 - avg_range)
        
            if strength_score > 4.0:
                return AbsorptionStrength.EXTREME
            elif strength_score > 3.0:
                return AbsorptionStrength.STRONG
            elif strength_score > 2.0:
                return AbsorptionStrength.MODERATE
            else:
                return AbsorptionStrength.WEAK
        except Exception as e:
            logger.error(f"Error in _calculate_absorption_strength: {e}")
            raise
    
    def _calculate_absorption_zone(self, window_data: pd.DataFrame) -> Dict:
        """Calculate the price zone where absorption occurred."""
        try:
            high_price = window_data['high'].max()
            low_price = window_data['low'].min()
            avg_price = window_data['close'].mean()
        
            # Calculate zone boundaries (±0.1% from average)
            zone_width = avg_price * 0.001
        
            return {
                'center': avg_price,
                'high': high_price,
                'low': low_price,
                'upper_boundary': avg_price + zone_width,
                'lower_boundary': avg_price - zone_width,
                'width': high_price - low_price
            }
        except Exception as e:
            logger.error(f"Error in _calculate_absorption_zone: {e}")
            raise
    
    def _calculate_effectiveness_metrics(self, pattern: Dict, 
                                       future_data: pd.DataFrame) -> Dict:
        """Calculate effectiveness metrics for absorption pattern."""
        try:
            absorption_zone = pattern['absorption_zone']
            absorption_type = pattern['type']
        
            # Price movement after absorption
            start_price = future_data['close'].iloc[0]
            end_price = future_data['close'].iloc[-1]
            max_price = future_data['high'].max()
            min_price = future_data['low'].min()
        
            price_change = (end_price - start_price) / start_price
            max_excursion_up = (max_price - start_price) / start_price
            max_excursion_down = (start_price - min_price) / start_price
        
            # Determine if absorption was effective
            if absorption_type == AbsorptionType.BUYING_ABSORPTION:
                # Expect upward movement after buying absorption
                effectiveness = price_change > 0.005  # 0.5% threshold
                direction_correct = price_change > 0
            elif absorption_type == AbsorptionType.SELLING_ABSORPTION:
                # Expect downward movement after selling absorption
                effectiveness = price_change < -0.005  # -0.5% threshold
                direction_correct = price_change < 0
            else:
                # Neutral absorption - expect continued consolidation
                effectiveness = abs(price_change) < 0.005
                direction_correct = True
        
            # Check if price returned to absorption zone
            zone_center = absorption_zone['center']
            zone_upper = absorption_zone['upper_boundary']
            zone_lower = absorption_zone['lower_boundary']
        
            returned_to_zone = any(
                zone_lower <= price <= zone_upper
                for price in future_data['close']
            )
        
            return {
                'effectiveness': effectiveness,
                'direction_correct': direction_correct,
                'price_change': price_change,
                'max_excursion_up': max_excursion_up,
                'max_excursion_down': max_excursion_down,
                'returned_to_zone': returned_to_zone,
                'follow_through_strength': abs(price_change)
            }
        except Exception as e:
            logger.error(f"Error in _calculate_effectiveness_metrics: {e}")
            raise


class AbsorptionConfirmation:
    """Methods for confirming absorption patterns."""
    
    def __init__(self):
        try:
            self.confirmation_methods = {}
            logger.info("Initialized AbsorptionConfirmation")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def confirm_with_order_flow(self, df: pd.DataFrame, 
                              absorption_pattern: Dict) -> Dict:
        """Confirm absorption using order flow analysis.
        
        Args:
            df: DataFrame with OHLC and volume data
            absorption_pattern: Detected absorption pattern
            
        Returns:
            Dictionary with order flow confirmation
        """
        try:
            if 'volume' not in df.columns:
                return {'confirmed': False, 'reason': 'No volume data available'}
        
            # Get data during absorption period
            start_time = absorption_pattern['start_time']
            end_time = absorption_pattern['end_time']
        
            absorption_data = df[(df.index >= start_time) & (df.index <= end_time)]
        
            if len(absorption_data) == 0:
                return {'confirmed': False, 'reason': 'No data in absorption period'}
        
            # Analyze order flow characteristics
            order_flow_analysis = self._analyze_order_flow_characteristics(absorption_data)
        
            # Confirmation criteria
            absorption_type = absorption_pattern['type']
        
            if absorption_type == AbsorptionType.BUYING_ABSORPTION:
                # Expect more buying pressure during absorption
                confirmed = (order_flow_analysis['buying_pressure'] > 
                            order_flow_analysis['selling_pressure'] * 1.2)
            elif absorption_type == AbsorptionType.SELLING_ABSORPTION:
                # Expect more selling pressure during absorption
                confirmed = (order_flow_analysis['selling_pressure'] > 
                            order_flow_analysis['buying_pressure'] * 1.2)
            else:
                # Neutral absorption - expect balanced flow
                ratio = (order_flow_analysis['buying_pressure'] / 
                        max(order_flow_analysis['selling_pressure'], 0.001))
                confirmed = 0.8 <= ratio <= 1.2
        
            return {
                'confirmed': confirmed,
                'order_flow_analysis': order_flow_analysis,
                'confirmation_strength': self._calculate_confirmation_strength(
                    order_flow_analysis, absorption_type
                )
            }
        except Exception as e:
            logger.error(f"Error in confirm_with_order_flow: {e}")
            raise
    
    def confirm_with_market_structure(self, df: pd.DataFrame, 
                                    absorption_pattern: Dict,
                                    lookback_periods: int = 50) -> Dict:
        """Confirm absorption using market structure analysis.
        
        Args:
            df: DataFrame with OHLC data
            absorption_pattern: Detected absorption pattern
            lookback_periods: Periods to look back for structure analysis
            
        Returns:
            Dictionary with structure confirmation
        """
        try:
            end_time = absorption_pattern['end_time']
        
            # Get historical data before absorption
            historical_data = df[df.index < end_time].tail(lookback_periods)
        
            if len(historical_data) < 20:
                return {'confirmed': False, 'reason': 'Insufficient historical data'}
        
            # Analyze market structure
            structure_analysis = self._analyze_market_structure_context(
                historical_data, absorption_pattern
            )
        
            # Confirmation based on structure context
            absorption_zone = absorption_pattern['absorption_zone']
        
            # Check if absorption occurred at key levels
            key_level_confirmation = self._check_key_level_alignment(
                structure_analysis, absorption_zone
            )
        
            return {
                'confirmed': key_level_confirmation['is_aligned'],
                'structure_analysis': structure_analysis,
                'key_level_alignment': key_level_confirmation,
                'structure_context': self._determine_structure_context(structure_analysis)
            }
        except Exception as e:
            logger.error(f"Error in confirm_with_market_structure: {e}")
            raise
    
    def confirm_with_time_analysis(self, absorption_pattern: Dict) -> Dict:
        """Confirm absorption using time-based analysis.
        
        Args:
            absorption_pattern: Detected absorption pattern
            
        Returns:
            Dictionary with time-based confirmation
        """
        try:
            start_time = absorption_pattern['start_time']
            end_time = absorption_pattern['end_time']
            duration = absorption_pattern['duration']
        
            # Convert to datetime if needed
            if isinstance(start_time, str):
                start_time = pd.to_datetime(start_time)
            if isinstance(end_time, str):
                end_time = pd.to_datetime(end_time)
        
            # Analyze timing characteristics
            hour_of_day = start_time.hour
            day_of_week = start_time.weekday()
        
            # Time-based confirmation criteria
            time_confirmations = []
        
            # Session timing
            if 8 <= hour_of_day <= 16:  # London session
                time_confirmations.append({
                    'factor': 'london_session',
                    'weight': 0.8,
                    'confirms': True
                })
            elif 13 <= hour_of_day <= 21:  # NY session
                time_confirmations.append({
                    'factor': 'ny_session',
                    'weight': 0.8,
                    'confirms': True
                })
            elif 13 <= hour_of_day <= 16:  # Overlap
                time_confirmations.append({
                    'factor': 'session_overlap',
                    'weight': 1.0,
                    'confirms': True
                })
        
            # Duration analysis
            if 3 <= duration <= 10:  # Optimal duration
                time_confirmations.append({
                    'factor': 'optimal_duration',
                    'weight': 0.6,
                    'confirms': True
                })
            elif duration > 15:  # Too long
                time_confirmations.append({
                    'factor': 'excessive_duration',
                    'weight': 0.4,
                    'confirms': False
                })
        
            # Calculate overall time confirmation
            total_weight = sum(conf['weight'] for conf in time_confirmations)
            confirming_weight = sum(
                conf['weight'] for conf in time_confirmations if conf['confirms']
            )
        
            time_confirmation_score = confirming_weight / max(total_weight, 0.1)
        
            return {
                'confirmed': time_confirmation_score > 0.6,
                'confirmation_score': time_confirmation_score,
                'time_factors': time_confirmations,
                'session_info': {
                    'hour': hour_of_day,
                    'day_of_week': day_of_week,
                    'duration': duration
                }
            }
        except Exception as e:
            logger.error(f"Error in confirm_with_time_analysis: {e}")
            raise
    
    def _analyze_order_flow_characteristics(self, df: pd.DataFrame) -> Dict:
        """Analyze order flow characteristics during absorption."""
        try:
            buying_volume = 0
            selling_volume = 0
        
            for _, row in df.iterrows():
                if row['close'] > row['open']:
                    buying_volume += row['volume']
                elif row['close'] < row['open']:
                    selling_volume += row['volume']
        
            total_volume = buying_volume + selling_volume
        
            if total_volume == 0:
                return {'buying_pressure': 0, 'selling_pressure': 0, 'imbalance': 0}
        
            buying_pressure = buying_volume / total_volume
            selling_pressure = selling_volume / total_volume
            imbalance = abs(buying_pressure - selling_pressure)
        
            return {
                'buying_pressure': buying_pressure,
                'selling_pressure': selling_pressure,
                'imbalance': imbalance,
                'total_volume': total_volume
            }
        except Exception as e:
            logger.error(f"Error in _analyze_order_flow_characteristics: {e}")
            raise
    
    def _calculate_confirmation_strength(self, order_flow: Dict, 
                                       absorption_type: AbsorptionType) -> float:
        """Calculate confirmation strength based on order flow."""
        try:
            if absorption_type == AbsorptionType.BUYING_ABSORPTION:
                return order_flow['buying_pressure'] - 0.5
            elif absorption_type == AbsorptionType.SELLING_ABSORPTION:
                return order_flow['selling_pressure'] - 0.5
            else:
                return 1.0 - order_flow['imbalance']  # Lower imbalance = higher confirmation
        except Exception as e:
            logger.error(f"Error in _calculate_confirmation_strength: {e}")
            raise
    
    def _analyze_market_structure_context(self, historical_data: pd.DataFrame, 
                                        absorption_pattern: Dict) -> Dict:
        """Analyze market structure context for absorption."""
        # Find recent swing highs and lows
        try:
            swing_highs = []
            swing_lows = []
        
            window = 5
            for i in range(window, len(historical_data) - window):
                # Check for swing high
                if (historical_data['high'].iloc[i] == 
                    historical_data['high'].iloc[i-window:i+window+1].max()):
                    swing_highs.append({
                        'price': historical_data['high'].iloc[i],
                        'timestamp': historical_data.index[i]
                    })
            
                # Check for swing low
                if (historical_data['low'].iloc[i] == 
                    historical_data['low'].iloc[i-window:i+window+1].min()):
                    swing_lows.append({
                        'price': historical_data['low'].iloc[i],
                        'timestamp': historical_data.index[i]
                    })
        
            return {
                'swing_highs': swing_highs[-5:],  # Last 5 swing highs
                'swing_lows': swing_lows[-5:],   # Last 5 swing lows
                'recent_high': historical_data['high'].max(),
                'recent_low': historical_data['low'].min(),
                'trend_direction': self._determine_trend_direction(historical_data)
            }
        except Exception as e:
            logger.error(f"Error in _analyze_market_structure_context: {e}")
            raise
    
    def _check_key_level_alignment(self, structure_analysis: Dict, 
                                 absorption_zone: Dict) -> Dict:
        """Check if absorption zone aligns with key structural levels."""
        try:
            zone_center = absorption_zone['center']
            zone_tolerance = absorption_zone['width'] * 0.5
        
            alignments = []
        
            # Check alignment with swing highs
            for swing_high in structure_analysis['swing_highs']:
                distance = abs(swing_high['price'] - zone_center)
                if distance <= zone_tolerance:
                    alignments.append({
                        'level_type': 'swing_high',
                        'level_price': swing_high['price'],
                        'distance': distance
                    })
        
            # Check alignment with swing lows
            for swing_low in structure_analysis['swing_lows']:
                distance = abs(swing_low['price'] - zone_center)
                if distance <= zone_tolerance:
                    alignments.append({
                        'level_type': 'swing_low',
                        'level_price': swing_low['price'],
                        'distance': distance
                    })
        
            return {
                'is_aligned': len(alignments) > 0,
                'alignments': alignments,
                'alignment_count': len(alignments)
            }
        except Exception as e:
            logger.error(f"Error in _check_key_level_alignment: {e}")
            raise
    
    def _determine_trend_direction(self, df: pd.DataFrame) -> str:
        """Determine trend direction from price data."""
        try:
            if len(df) < 20:
                return 'unknown'
        
            # Simple trend determination using moving averages
            short_ma = df['close'].rolling(10).mean().iloc[-1]
            long_ma = df['close'].rolling(20).mean().iloc[-1]
        
            if pd.isna(short_ma) or pd.isna(long_ma):
                return 'unknown'
        
            if short_ma > long_ma * 1.001:
                return 'bullish'
            elif short_ma < long_ma * 0.999:
                return 'bearish'
            else:
                return 'sideways'
        except Exception as e:
            logger.error(f"Error in _determine_trend_direction: {e}")
            raise
    
    def _determine_structure_context(self, structure_analysis: Dict) -> str:
        """Determine the structural context for absorption."""
        try:
            trend = structure_analysis['trend_direction']
            swing_highs = structure_analysis['swing_highs']
            swing_lows = structure_analysis['swing_lows']
        
            if trend == 'bullish' and len(swing_lows) > 0:
                return 'bullish_pullback_absorption'
            elif trend == 'bearish' and len(swing_highs) > 0:
                return 'bearish_pullback_absorption'
            elif trend == 'sideways':
                return 'range_bound_absorption'
            else:
                return 'trend_continuation_absorption'
        except Exception as e:
            logger.error(f"Error in _determine_structure_context: {e}")
            raise
