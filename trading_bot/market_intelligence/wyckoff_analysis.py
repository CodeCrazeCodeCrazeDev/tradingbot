import logging
logger = logging.getLogger(__name__)
"""Wyckoff Market Analysis for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
import numpy
import pandas


class WyckoffPhase(Enum):
    """Wyckoff market phases."""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class WyckoffAccumulationDetector:
    """Detect Wyckoff accumulation patterns."""
    
    def __init__(self):
        try:
            self.accumulation_zones = []
            logger.info("Initialized WyckoffAccumulationDetector")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_accumulation_phase(self, df: pd.DataFrame, 
                                volume_threshold: float = 1.5,
                                price_range_threshold: float = 0.02) -> List[Dict]:
        """Detect accumulation phases in price data.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume increase threshold for accumulation
            price_range_threshold: Maximum price range during accumulation
            
        Returns:
            List of detected accumulation phases
        """
        try:
            accumulation_phases = []
        
            # Calculate volume moving average
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            # Calculate price range
            df['price_range'] = (df['high'] - df['low']) / df['close']
            df['range_ma'] = df['price_range'].rolling(window=20).mean()
        
            # Detect potential accumulation periods
            accumulation_mask = (
                (df['volume_ratio'] > volume_threshold) &
                (df['price_range'] < df['range_ma'] * (1 + price_range_threshold))
            )
        
            # Group consecutive accumulation periods
            accumulation_periods = self._group_consecutive_periods(df, accumulation_mask)
        
            for start_idx, end_idx in accumulation_periods:
                if end_idx - start_idx >= 5:  # Minimum 5 periods for accumulation
                    phase_data = df.iloc[start_idx:end_idx+1]
                
                    accumulation_phases.append({
                        'start_time': phase_data.index[0],
                        'end_time': phase_data.index[-1],
                        'duration': len(phase_data),
                        'avg_volume_ratio': phase_data['volume_ratio'].mean(),
                        'price_low': phase_data['low'].min(),
                        'price_high': phase_data['high'].max(),
                        'price_range': (phase_data['high'].max() - phase_data['low'].min()) / phase_data['close'].mean(),
                        'total_volume': phase_data['volume'].sum(),
                        'phase': WyckoffPhase.ACCUMULATION
                    })
        
            return accumulation_phases
        except Exception as e:
            logger.error(f"Error in detect_accumulation_phase: {e}")
            raise
    
    def detect_spring_action(self, df: pd.DataFrame, 
                           accumulation_zones: List[Dict]) -> List[Dict]:
        """Detect spring actions (false breakdowns) in accumulation zones.
        
        Args:
            df: DataFrame with OHLC data
            accumulation_zones: List of detected accumulation zones
            
        Returns:
            List of spring actions
        """
        try:
            spring_actions = []
        
            for zone in accumulation_zones:
                zone_low = zone['price_low']
                zone_end = zone['end_time']
            
                # Look for price action after accumulation zone
                post_zone_data = df[df.index > zone_end].head(20)  # Look 20 periods ahead
            
                for i, (timestamp, row) in enumerate(post_zone_data.iterrows()):
                    # Check for breakdown below accumulation low
                    if row['low'] < zone_low:
                        # Check for quick recovery (spring action)
                        recovery_data = post_zone_data.iloc[i:i+5]  # Next 5 periods
                    
                        if len(recovery_data) > 0 and recovery_data['close'].iloc[-1] > zone_low:
                            spring_actions.append({
                                'timestamp': timestamp,
                                'accumulation_zone': zone,
                                'spring_low': row['low'],
                                'zone_low': zone_low,
                                'breakdown_amount': zone_low - row['low'],
                                'recovery_close': recovery_data['close'].iloc[-1],
                                'volume': row['volume']
                            })
                            break
        
            return spring_actions
        except Exception as e:
            logger.error(f"Error in detect_spring_action: {e}")
            raise
    
    def _group_consecutive_periods(self, df: pd.DataFrame, mask: pd.Series) -> List[Tuple[int, int]]:
        """Group consecutive True values in a boolean mask."""
        try:
            groups = []
            start_idx = None
        
            for i, value in enumerate(mask):
                if value and start_idx is None:
                    start_idx = i
                elif not value and start_idx is not None:
                    groups.append((start_idx, i - 1))
                    start_idx = None
        
            # Handle case where mask ends with True
            if start_idx is not None:
                groups.append((start_idx, len(mask) - 1))
        
            return groups
        except Exception as e:
            logger.error(f"Error in _group_consecutive_periods: {e}")
            raise


class WyckoffDistributionAnalyzer:
    """Analyze Wyckoff distribution patterns."""
    
    def __init__(self):
        try:
            self.distribution_zones = []
            logger.info("Initialized WyckoffDistributionAnalyzer")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_distribution_phase(self, df: pd.DataFrame,
                                volume_threshold: float = 1.5,
                                price_level_threshold: float = 0.98) -> List[Dict]:
        """Detect distribution phases in price data.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume increase threshold
            price_level_threshold: Price level maintenance threshold
            
        Returns:
            List of detected distribution phases
        """
        try:
            distribution_phases = []
        
            # Calculate rolling highs and volume metrics
            df['rolling_high'] = df['high'].rolling(window=20).max()
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            # Detect potential distribution periods
            # High volume near recent highs with limited upward progress
            distribution_mask = (
                (df['volume_ratio'] > volume_threshold) &
                (df['high'] >= df['rolling_high'] * price_level_threshold) &
                (df['close'] < df['high'])  # Inability to close at highs
            )
        
            # Group consecutive distribution periods
            distribution_periods = self._group_consecutive_periods(df, distribution_mask)
        
            for start_idx, end_idx in distribution_periods:
                if end_idx - start_idx >= 5:  # Minimum 5 periods
                    phase_data = df.iloc[start_idx:end_idx+1]
                
                    distribution_phases.append({
                        'start_time': phase_data.index[0],
                        'end_time': phase_data.index[-1],
                        'duration': len(phase_data),
                        'avg_volume_ratio': phase_data['volume_ratio'].mean(),
                        'price_high': phase_data['high'].max(),
                        'price_low': phase_data['low'].min(),
                        'avg_close': phase_data['close'].mean(),
                        'total_volume': phase_data['volume'].sum(),
                        'phase': WyckoffPhase.DISTRIBUTION
                    })
        
            return distribution_phases
        except Exception as e:
            logger.error(f"Error in detect_distribution_phase: {e}")
            raise
    
    def detect_upthrust_action(self, df: pd.DataFrame,
                             distribution_zones: List[Dict]) -> List[Dict]:
        """Detect upthrust actions (false breakouts) in distribution zones.
        
        Args:
            df: DataFrame with OHLC data
            distribution_zones: List of detected distribution zones
            
        Returns:
            List of upthrust actions
        """
        try:
            upthrust_actions = []
        
            for zone in distribution_zones:
                zone_high = zone['price_high']
                zone_end = zone['end_time']
            
                # Look for price action after distribution zone
                post_zone_data = df[df.index > zone_end].head(20)
            
                for i, (timestamp, row) in enumerate(post_zone_data.iterrows()):
                    # Check for breakout above distribution high
                    if row['high'] > zone_high:
                        # Check for quick reversal (upthrust action)
                        reversal_data = post_zone_data.iloc[i:i+5]
                    
                        if len(reversal_data) > 0 and reversal_data['close'].iloc[-1] < zone_high:
                            upthrust_actions.append({
                                'timestamp': timestamp,
                                'distribution_zone': zone,
                                'upthrust_high': row['high'],
                                'zone_high': zone_high,
                                'breakout_amount': row['high'] - zone_high,
                                'reversal_close': reversal_data['close'].iloc[-1],
                                'volume': row['volume']
                            })
                            break
        
            return upthrust_actions
        except Exception as e:
            logger.error(f"Error in detect_upthrust_action: {e}")
            raise
    
    def _group_consecutive_periods(self, df: pd.DataFrame, mask: pd.Series) -> List[Tuple[int, int]]:
        """Group consecutive True values in a boolean mask."""
        try:
            groups = []
            start_idx = None
        
            for i, value in enumerate(mask):
                if value and start_idx is None:
                    start_idx = i
                elif not value and start_idx is not None:
                    groups.append((start_idx, i - 1))
                    start_idx = None
        
            if start_idx is not None:
                groups.append((start_idx, len(mask) - 1))
        
            return groups
        except Exception as e:
            logger.error(f"Error in _group_consecutive_periods: {e}")
            raise


class VolumeAnalysis:
    """Advanced volume analysis for Wyckoff methodology."""
    
    def __init__(self):
        try:
            self.volume_patterns = {}
            logger.info("Initialized VolumeAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_volume_spread_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform Volume Spread Analysis (VSA).
        
        Args:
            df: DataFrame with OHLC and volume data
            
        Returns:
            DataFrame with VSA indicators
        """
        try:
            vsa_df = df.copy()
        
            # Calculate spread (range)
            vsa_df['spread'] = vsa_df['high'] - vsa_df['low']
            vsa_df['spread_ma'] = vsa_df['spread'].rolling(window=20).mean()
        
            # Calculate volume metrics
            vsa_df['volume_ma'] = vsa_df['volume'].rolling(window=20).mean()
            vsa_df['volume_ratio'] = vsa_df['volume'] / vsa_df['volume_ma']
        
            # Calculate close position within the range
            vsa_df['close_position'] = (vsa_df['close'] - vsa_df['low']) / vsa_df['spread']
        
            # VSA signals
            vsa_df['high_volume'] = vsa_df['volume_ratio'] > 1.5
            vsa_df['low_volume'] = vsa_df['volume_ratio'] < 0.7
            vsa_df['wide_spread'] = vsa_df['spread'] > vsa_df['spread_ma'] * 1.5
            vsa_df['narrow_spread'] = vsa_df['spread'] < vsa_df['spread_ma'] * 0.7
        
            # Specific VSA patterns
            vsa_df['climax_volume'] = (
                vsa_df['high_volume'] & 
                vsa_df['wide_spread'] & 
                (vsa_df['close_position'] < 0.3)  # Close in lower 30% of range
            )
        
            vsa_df['professional_money'] = (
                vsa_df['high_volume'] & 
                vsa_df['narrow_spread'] & 
                (vsa_df['close_position'] > 0.7)  # Close in upper 30% of range
            )
        
            vsa_df['weak_demand'] = (
                vsa_df['low_volume'] & 
                vsa_df['wide_spread'] & 
                (vsa_df['close_position'] < 0.5)
            )
        
            return vsa_df
        except Exception as e:
            logger.error(f"Error in analyze_volume_spread_analysis: {e}")
            raise
    
    def detect_volume_climax(self, df: pd.DataFrame, 
                           volume_threshold: float = 3.0,
                           lookback: int = 20) -> List[Dict]:
        """Detect volume climax events.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume threshold as multiple of average
            lookback: Lookback period for volume average
            
        Returns:
            List of volume climax events
        """
        try:
            climax_events = []
        
            # Calculate volume moving average
            df['volume_ma'] = df['volume'].rolling(window=lookback).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            # Calculate price change
            df['price_change'] = df['close'].pct_change()
        
            for i, (timestamp, row) in enumerate(df.iterrows()):
                if i >= lookback and row['volume_ratio'] > volume_threshold:
                    # Determine climax type based on price action
                    if row['price_change'] > 0.02:  # Strong upward move
                        climax_type = 'buying_climax'
                    elif row['price_change'] < -0.02:  # Strong downward move
                        climax_type = 'selling_climax'
                    else:
                        climax_type = 'neutral_climax'
                
                    climax_events.append({
                        'timestamp': timestamp,
                        'climax_type': climax_type,
                        'volume': row['volume'],
                        'volume_ratio': row['volume_ratio'],
                        'price_change': row['price_change'],
                        'close': row['close'],
                        'spread': row['high'] - row['low']
                    })
        
            return climax_events
        except Exception as e:
            logger.error(f"Error in detect_volume_climax: {e}")
            raise
    
    def analyze_effort_vs_result(self, df: pd.DataFrame, 
                               window: int = 10) -> pd.DataFrame:
        """Analyze effort (volume) vs result (price movement).
        
        Args:
            df: DataFrame with OHLC and volume data
            window: Window for analysis
            
        Returns:
            DataFrame with effort vs result analysis
        """
        try:
            analysis_df = df.copy()
        
            # Calculate rolling metrics
            analysis_df['volume_sum'] = df['volume'].rolling(window=window).sum()
            analysis_df['price_change'] = df['close'].pct_change(periods=window)
            analysis_df['spread_sum'] = (df['high'] - df['low']).rolling(window=window).sum()
        
            # Normalize metrics
            analysis_df['effort_normalized'] = (
                analysis_df['volume_sum'] / analysis_df['volume_sum'].rolling(window=50).mean()
            )
            analysis_df['result_normalized'] = (
                abs(analysis_df['price_change']) / abs(analysis_df['price_change']).rolling(window=50).mean()
            )
        
            # Calculate effort vs result ratio
            analysis_df['effort_result_ratio'] = (
                analysis_df['effort_normalized'] / analysis_df['result_normalized']
            )
        
            # Identify divergences
            analysis_df['high_effort_low_result'] = (
                (analysis_df['effort_normalized'] > 1.5) & 
                (analysis_df['result_normalized'] < 0.7)
            )
        
            analysis_df['low_effort_high_result'] = (
                (analysis_df['effort_normalized'] < 0.7) & 
                (analysis_df['result_normalized'] > 1.5)
            )
        
            return analysis_df
        except Exception as e:
            logger.error(f"Error in analyze_effort_vs_result: {e}")
            raise
    
    def detect_stopping_volume(self, df: pd.DataFrame,
                             volume_threshold: float = 2.0,
                             reversal_threshold: float = 0.01) -> List[Dict]:
        """Detect stopping volume patterns.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume threshold for stopping volume
            reversal_threshold: Price reversal threshold
            
        Returns:
            List of stopping volume events
        """
        try:
            stopping_volume_events = []
        
            # Calculate volume metrics
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            # Calculate price metrics
            df['price_change'] = df['close'].pct_change()
            df['next_price_change'] = df['price_change'].shift(-1)
        
            for i, (timestamp, row) in enumerate(df.iterrows()):
                if (i < len(df) - 1 and 
                    row['volume_ratio'] > volume_threshold and
                    not pd.isna(row['next_price_change'])):
                
                    # Check for price reversal after high volume
                    current_direction = 1 if row['price_change'] > 0 else -1
                    next_direction = 1 if row['next_price_change'] > 0 else -1
                
                    # Stopping volume occurs when high volume is followed by reversal
                    if (current_direction != next_direction and 
                        abs(row['next_price_change']) > reversal_threshold):
                    
                        stopping_volume_events.append({
                            'timestamp': timestamp,
                            'volume': row['volume'],
                            'volume_ratio': row['volume_ratio'],
                            'price_change': row['price_change'],
                            'next_price_change': row['next_price_change'],
                            'reversal_strength': abs(row['next_price_change']),
                            'direction': 'up_to_down' if current_direction > 0 else 'down_to_up'
                        })
        
            return stopping_volume_events
        except Exception as e:
            logger.error(f"Error in detect_stopping_volume: {e}")
            raise
