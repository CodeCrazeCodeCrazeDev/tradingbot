import logging
logger = logging.getLogger(__name__)
"""Advanced Pattern Recognition for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import scipy.signal as signal
import numpy
import pandas


class MarketStructureAnalysis:
    """Analyze market structure patterns."""
    
    def __init__(self):
        try:
            self.structure_patterns = {}
            logger.info("Initialized MarketStructureAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_market_structure(self, df: pd.DataFrame, 
                              swing_window: int = 10) -> Dict:
        """Detect overall market structure.
        
        Args:
            df: DataFrame with OHLC data
            swing_window: Window for swing point detection
            
        Returns:
            Dictionary with market structure analysis
        """
        # Find swing points
        try:
            swing_highs = self._find_swing_highs(df['high'], swing_window)
            swing_lows = self._find_swing_lows(df['low'], swing_window)
        
            # Analyze trend structure
            trend_analysis = self._analyze_trend_structure(swing_highs, swing_lows)
        
            # Detect support and resistance levels
            support_resistance = self._detect_support_resistance(df, swing_highs, swing_lows)
        
            # Calculate structure strength
            structure_strength = self._calculate_structure_strength(swing_highs, swing_lows)
        
            return {
                'swing_highs': swing_highs,
                'swing_lows': swing_lows,
                'trend_analysis': trend_analysis,
                'support_resistance': support_resistance,
                'structure_strength': structure_strength,
                'current_structure': self._determine_current_structure(trend_analysis)
            }
        except Exception as e:
            logger.error(f"Error in detect_market_structure: {e}")
            raise
    
    def _find_swing_highs(self, high_series: pd.Series, window: int) -> List[Dict]:
        """Find swing high points."""
        try:
            peaks, _ = signal.find_peaks(high_series, distance=window)
            swing_highs = []
        
            for peak in peaks:
                swing_highs.append({
                    'timestamp': high_series.index[peak],
                    'price': high_series.iloc[peak],
                    'index': peak
                })
        
            return swing_highs
        except Exception as e:
            logger.error(f"Error in _find_swing_highs: {e}")
            raise
    
    def _find_swing_lows(self, low_series: pd.Series, window: int) -> List[Dict]:
        """Find swing low points."""
        # Invert series to find peaks (which are lows in original)
        try:
            inverted = -low_series
            peaks, _ = signal.find_peaks(inverted, distance=window)
            swing_lows = []
        
            for peak in peaks:
                swing_lows.append({
                    'timestamp': low_series.index[peak],
                    'price': low_series.iloc[peak],
                    'index': peak
                })
        
            return swing_lows
        except Exception as e:
            logger.error(f"Error in _find_swing_lows: {e}")
            raise
    
    def _analyze_trend_structure(self, swing_highs: List[Dict], 
                               swing_lows: List[Dict]) -> Dict:
        """Analyze trend structure from swing points."""
        try:
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return {'trend': 'insufficient_data'}
        
            # Analyze recent swing highs
            recent_highs = swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs
            recent_lows = swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
        
            # Check for higher highs and higher lows (uptrend)
            higher_highs = all(recent_highs[i]['price'] > recent_highs[i-1]['price'] 
                              for i in range(1, len(recent_highs)))
            higher_lows = all(recent_lows[i]['price'] > recent_lows[i-1]['price'] 
                             for i in range(1, len(recent_lows)))
        
            # Check for lower highs and lower lows (downtrend)
            lower_highs = all(recent_highs[i]['price'] < recent_highs[i-1]['price'] 
                             for i in range(1, len(recent_highs)))
            lower_lows = all(recent_lows[i]['price'] < recent_lows[i-1]['price'] 
                            for i in range(1, len(recent_lows)))
        
            if higher_highs and higher_lows:
                trend = 'uptrend'
            elif lower_highs and lower_lows:
                trend = 'downtrend'
            else:
                trend = 'sideways'
        
            return {
                'trend': trend,
                'higher_highs': higher_highs,
                'higher_lows': higher_lows,
                'lower_highs': lower_highs,
                'lower_lows': lower_lows,
                'recent_highs': recent_highs,
                'recent_lows': recent_lows
            }
        except Exception as e:
            logger.error(f"Error in _analyze_trend_structure: {e}")
            raise
    
    def _detect_support_resistance(self, df: pd.DataFrame, 
                                 swing_highs: List[Dict], 
                                 swing_lows: List[Dict]) -> Dict:
        """Detect support and resistance levels."""
        # Extract price levels
        try:
            resistance_levels = [swing['price'] for swing in swing_highs]
            support_levels = [swing['price'] for swing in swing_lows]
        
            # Cluster similar levels
            resistance_clusters = self._cluster_price_levels(resistance_levels)
            support_clusters = self._cluster_price_levels(support_levels)
        
            return {
                'resistance_levels': resistance_clusters,
                'support_levels': support_clusters,
                'key_resistance': max(resistance_levels) if resistance_levels else None,
                'key_support': min(support_levels) if support_levels else None
            }
        except Exception as e:
            logger.error(f"Error in _detect_support_resistance: {e}")
            raise
    
    def _cluster_price_levels(self, levels: List[float], 
                            tolerance: float = 0.001) -> List[Dict]:
        """Cluster similar price levels."""
        try:
            if not levels:
                return []
        
            levels_array = np.array(levels).reshape(-1, 1)
            scaler = MinMaxScaler()
            scaled_levels = scaler.fit_transform(levels_array)
        
            # Use KMeans clustering
            n_clusters = min(5, len(levels))  # Max 5 clusters
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(scaled_levels)
        
            # Group levels by cluster
            clustered_levels = []
            for cluster_id in range(n_clusters):
                cluster_levels = [levels[i] for i in range(len(levels)) if clusters[i] == cluster_id]
                if cluster_levels:
                    clustered_levels.append({
                        'level': np.mean(cluster_levels),
                        'count': len(cluster_levels),
                        'strength': len(cluster_levels),
                        'levels': cluster_levels
                    })
        
            return sorted(clustered_levels, key=lambda x: x['strength'], reverse=True)
        except Exception as e:
            logger.error(f"Error in _cluster_price_levels: {e}")
            raise
    
    def _calculate_structure_strength(self, swing_highs: List[Dict], 
                                    swing_lows: List[Dict]) -> float:
        """Calculate overall structure strength."""
        try:
            if not swing_highs or not swing_lows:
                return 0.0
        
            # Calculate based on number of swing points and their consistency
            total_swings = len(swing_highs) + len(swing_lows)
        
            # Bonus for consistent trend structure
            trend_consistency = 0
            if len(swing_highs) >= 2:
                high_trend = sum(1 for i in range(1, len(swing_highs)) 
                               if swing_highs[i]['price'] > swing_highs[i-1]['price'])
                trend_consistency += high_trend / (len(swing_highs) - 1)
        
            if len(swing_lows) >= 2:
                low_trend = sum(1 for i in range(1, len(swing_lows)) 
                              if swing_lows[i]['price'] > swing_lows[i-1]['price'])
                trend_consistency += low_trend / (len(swing_lows) - 1)
        
            return min(1.0, (total_swings / 10) * (trend_consistency / 2))
        except Exception as e:
            logger.error(f"Error in _calculate_structure_strength: {e}")
            raise
    
    def _determine_current_structure(self, trend_analysis: Dict) -> str:
        """Determine current market structure."""
        try:
            trend = trend_analysis.get('trend', 'unknown')
        
            if trend == 'uptrend':
                return 'bullish_structure'
            elif trend == 'downtrend':
                return 'bearish_structure'
            else:
                return 'neutral_structure'
        except Exception as e:
            logger.error(f"Error in _determine_current_structure: {e}")
            raise


class PremiumDiscountZones:
    """Identify premium and discount pricing zones."""
    
    def __init__(self):
        try:
            self.zones = {}
            logger.info("Initialized PremiumDiscountZones")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_fair_value_zones(self, df: pd.DataFrame, 
                                 lookback: int = 100) -> Dict:
        """Calculate fair value zones using statistical methods.
        
        Args:
            df: DataFrame with OHLC data
            lookback: Lookback period for calculation
            
        Returns:
            Dictionary with fair value zones
        """
        try:
            recent_data = df.tail(lookback)
        
            # Calculate VWAP (Volume Weighted Average Price)
            if 'volume' in df.columns:
                vwap = (recent_data['close'] * recent_data['volume']).sum() / recent_data['volume'].sum()
            else:
                vwap = recent_data['close'].mean()
        
            # Calculate standard deviations
            price_std = recent_data['close'].std()
        
            # Define zones
            premium_zone_start = vwap + (price_std * 0.5)
            premium_zone_end = vwap + (price_std * 2.0)
        
            discount_zone_start = vwap - (price_std * 2.0)
            discount_zone_end = vwap - (price_std * 0.5)
        
            current_price = df['close'].iloc[-1]
        
            # Determine current zone
            if current_price > premium_zone_start:
                current_zone = 'premium'
            elif current_price < discount_zone_end:
                current_zone = 'discount'
            else:
                current_zone = 'fair_value'
        
            return {
                'vwap': vwap,
                'fair_value_center': vwap,
                'premium_zone': {
                    'start': premium_zone_start,
                    'end': premium_zone_end
                },
                'discount_zone': {
                    'start': discount_zone_start,
                    'end': discount_zone_end
                },
                'current_price': current_price,
                'current_zone': current_zone,
                'distance_from_fair_value': abs(current_price - vwap) / vwap
            }
        except Exception as e:
            logger.error(f"Error in calculate_fair_value_zones: {e}")
            raise
    
    def detect_value_areas(self, df: pd.DataFrame, 
                          volume_profile_bins: int = 50) -> Dict:
        """Detect value areas using volume profile analysis.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_profile_bins: Number of bins for volume profile
            
        Returns:
            Dictionary with value area analysis
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for value area calculation")
                return {}
        
            # Create price bins
            price_min = df['low'].min()
            price_max = df['high'].max()
            price_bins = np.linspace(price_min, price_max, volume_profile_bins)
        
            # Calculate volume at each price level
            volume_profile = np.zeros(len(price_bins) - 1)
        
            for i, (_, row) in enumerate(df.iterrows()):
                # Distribute volume across the price range of each candle
                candle_range = row['high'] - row['low']
                if candle_range > 0:
                    for j in range(len(price_bins) - 1):
                        bin_low = price_bins[j]
                        bin_high = price_bins[j + 1]
                    
                        # Calculate overlap between candle range and price bin
                        overlap_low = max(bin_low, row['low'])
                        overlap_high = min(bin_high, row['high'])
                    
                        if overlap_high > overlap_low:
                            overlap_ratio = (overlap_high - overlap_low) / candle_range
                            volume_profile[j] += row['volume'] * overlap_ratio
        
            # Find Point of Control (POC) - highest volume price
            poc_index = np.argmax(volume_profile)
            poc_price = (price_bins[poc_index] + price_bins[poc_index + 1]) / 2
        
            # Calculate Value Area (70% of volume)
            total_volume = volume_profile.sum()
            target_volume = total_volume * 0.7
        
            # Find value area boundaries
            sorted_indices = np.argsort(volume_profile)[:-1]  # Descending order
            cumulative_volume = 0
            value_area_indices = []
        
            for idx in sorted_indices:
                cumulative_volume += volume_profile[idx]
                value_area_indices.append(idx)
                if cumulative_volume >= target_volume:
                    break
        
            value_area_low = price_bins[min(value_area_indices)]
            value_area_high = price_bins[max(value_area_indices) + 1]
        
            return {
                'poc_price': poc_price,
                'value_area_high': value_area_high,
                'value_area_low': value_area_low,
                'volume_profile': volume_profile,
                'price_bins': price_bins,
                'total_volume': total_volume
            }
        except Exception as e:
            logger.error(f"Error in detect_value_areas: {e}")
            raise


class ImbalanceAnalysis:
    """Analyze price imbalances and gaps."""
    
    def __init__(self):
        try:
            self.imbalances = []
            logger.info("Initialized ImbalanceAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_fair_value_gaps(self, df: pd.DataFrame, 
                             min_gap_size: float = 0.001) -> List[Dict]:
        """Detect Fair Value Gaps (FVG) in price data.
        
        Args:
            df: DataFrame with OHLC data
            min_gap_size: Minimum gap size as percentage of price
            
        Returns:
            List of detected fair value gaps
        """
        try:
            fair_value_gaps = []
        
            for i in range(1, len(df) - 1):
                prev_candle = df.iloc[i-1]
                current_candle = df.iloc[i]
                next_candle = df.iloc[i+1]
            
                # Bullish FVG: Previous high < Next low
                if prev_candle['high'] < next_candle['low']:
                    gap_size = (next_candle['low'] - prev_candle['high']) / current_candle['close']
                
                    if gap_size > min_gap_size:
                        fair_value_gaps.append({
                            'timestamp': current_candle.name,
                            'type': 'bullish_fvg',
                            'gap_low': prev_candle['high'],
                            'gap_high': next_candle['low'],
                            'gap_size': gap_size,
                            'current_price': current_candle['close'],
                            'is_filled': False
                        })
            
                # Bearish FVG: Previous low > Next high
                elif prev_candle['low'] > next_candle['high']:
                    gap_size = (prev_candle['low'] - next_candle['high']) / current_candle['close']
                
                    if gap_size > min_gap_size:
                        fair_value_gaps.append({
                            'timestamp': current_candle.name,
                            'type': 'bearish_fvg',
                            'gap_high': prev_candle['low'],
                            'gap_low': next_candle['high'],
                            'gap_size': gap_size,
                            'current_price': current_candle['close'],
                            'is_filled': False
                        })
        
            return fair_value_gaps
        except Exception as e:
            logger.error(f"Error in detect_fair_value_gaps: {e}")
            raise
    
    def detect_imbalance_zones(self, df: pd.DataFrame, 
                             volume_threshold: float = 0.5) -> List[Dict]:
        """Detect imbalance zones based on volume analysis.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume threshold for imbalance detection
            
        Returns:
            List of detected imbalance zones
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for imbalance detection")
                return []
        
            imbalance_zones = []
        
            # Calculate volume moving average
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(window=20).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_ma']
        
            # Find low volume areas
            low_volume_mask = df_copy['volume_ratio'] < volume_threshold
        
            # Group consecutive low volume periods
            imbalance_periods = []
            start_idx = None
        
            for i, is_low_volume in enumerate(low_volume_mask):
                if is_low_volume and start_idx is None:
                    start_idx = i
                elif not is_low_volume and start_idx is not None:
                    imbalance_periods.append((start_idx, i - 1))
                    start_idx = None
        
            # Handle case where data ends with low volume
            if start_idx is not None:
                imbalance_periods.append((start_idx, len(df_copy) - 1))
        
            # Create imbalance zone objects
            for start_idx, end_idx in imbalance_periods:
                if end_idx - start_idx >= 2:  # Minimum 3 periods
                    zone_data = df_copy.iloc[start_idx:end_idx+1]
                
                    imbalance_zones.append({
                        'start_timestamp': zone_data.index[0],
                        'end_timestamp': zone_data.index[-1],
                        'zone_high': zone_data['high'].max(),
                        'zone_low': zone_data['low'].min(),
                        'avg_volume_ratio': zone_data['volume_ratio'].mean(),
                        'duration': len(zone_data),
                        'zone_center': (zone_data['high'].max() + zone_data['low'].min()) / 2
                    })
        
            return imbalance_zones
        except Exception as e:
            logger.error(f"Error in detect_imbalance_zones: {e}")
            raise
    
    def check_gap_fills(self, fair_value_gaps: List[Dict], 
                       current_df: pd.DataFrame) -> List[Dict]:
        """Check if fair value gaps have been filled.
        
        Args:
            fair_value_gaps: List of FVGs to check
            current_df: Current price data
            
        Returns:
            Updated list of FVGs with fill status
        """
        try:
            updated_gaps = []
        
            for gap in fair_value_gaps:
                gap_copy = gap.copy()
                gap_timestamp = gap['timestamp']
            
                # Get price data after the gap
                future_data = current_df[current_df.index > gap_timestamp]
            
                if len(future_data) > 0:
                    if gap['type'] == 'bullish_fvg':
                        # Bullish FVG is filled when price returns to gap zone
                        fill_touches = future_data[
                            (future_data['low'] <= gap['gap_high']) & 
                            (future_data['low'] >= gap['gap_low'])
                        ]
                    
                        if len(fill_touches) > 0:
                            gap_copy['is_filled'] = True
                            gap_copy['fill_timestamp'] = fill_touches.index[0]
                            gap_copy['fill_price'] = fill_touches.iloc[0]['low']
                
                    elif gap['type'] == 'bearish_fvg':
                        # Bearish FVG is filled when price returns to gap zone
                        fill_touches = future_data[
                            (future_data['high'] >= gap['gap_low']) & 
                            (future_data['high'] <= gap['gap_high'])
                        ]
                    
                        if len(fill_touches) > 0:
                            gap_copy['is_filled'] = True
                            gap_copy['fill_timestamp'] = fill_touches.index[0]
                            gap_copy['fill_price'] = fill_touches.iloc[0]['high']
            
                updated_gaps.append(gap_copy)
        
            return updated_gaps
        except Exception as e:
            logger.error(f"Error in check_gap_fills: {e}")
            raise
