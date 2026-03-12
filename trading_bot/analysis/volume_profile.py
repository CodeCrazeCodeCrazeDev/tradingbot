"""Advanced Volume Profile Analysis Module.

Implements institutional-grade volume profile analysis including:
- VPOC (Volume Point of Control) - Price level with highest traded volume
- VAH (Value Area High) - Upper boundary of 70% volume concentration
- VAL (Value Area Low) - Lower boundary of 70% volume concentration
- Volume Nodes (HVN/LVN) - High/Low Volume Nodes identification
- Volume Profile Fixed Range - Analysis over specific price ranges
- Time-segmented VWAP - Session-based VWAP calculations
- Multi-day VWAP analysis - Extended VWAP tracking
- TPO (Time Price Opportunity) profiles
- Market Profile integration

This module enables identification of institutional accumulation zones
and high-probability reversal areas based on volume distribution.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class VolumeNodeType(enum.Enum):
    """Types of volume nodes in the profile."""
    HVN = "high_volume_node"  # High Volume Node - support/resistance
    LVN = "low_volume_node"   # Low Volume Node - fast price movement area
    NEUTRAL = "neutral"       # Normal volume distribution


class ProfileType(enum.Enum):
    """Types of volume profiles."""
    SESSION = "session"       # Single session profile
    COMPOSITE = "composite"   # Multi-session composite
    FIXED_RANGE = "fixed_range"  # User-defined range
    VISIBLE_RANGE = "visible_range"  # Visible chart range


@dataclass
class VolumeNode:
    """Represents a volume node in the profile."""
    price_level: float
    volume: float
    node_type: VolumeNodeType
    relative_volume: float  # Volume relative to average (1.0 = average)
    price_range: Tuple[float, float]  # (low, high) of the price bin
    
    
@dataclass
class ValueArea:
    """Represents the Value Area (70% of volume)."""
    vah: float  # Value Area High
    val: float  # Value Area Low
    vpoc: float  # Volume Point of Control
    value_area_volume: float  # Total volume in value area
    total_volume: float  # Total profile volume
    value_area_percent: float = 70.0  # Percentage of volume in VA


@dataclass
class VolumeProfile:
    """Complete volume profile for a given range."""
    profile_type: ProfileType
    start_time: datetime
    end_time: datetime
    price_levels: List[float]
    volume_at_price: Dict[float, float]
    value_area: ValueArea
    volume_nodes: List[VolumeNode]
    hvn_levels: List[float]  # High Volume Node price levels
    lvn_levels: List[float]  # Low Volume Node price levels
    total_volume: float
    num_bins: int
    bin_size: float
    
    
@dataclass
class TPOProfile:
    """Time Price Opportunity profile (Market Profile)."""
    price_levels: List[float]
    tpo_count: Dict[float, int]  # TPO count at each price
    poc: float  # Point of Control
    initial_balance_high: float
    initial_balance_low: float
    value_area: ValueArea
    single_prints: List[float]  # Single print levels (potential support/resistance)
    poor_highs: List[float]  # Poor high formations
    poor_lows: List[float]  # Poor low formations
    excess_high: Optional[float]  # Excess at high
    excess_low: Optional[float]  # Excess at low


@dataclass
class VWAPBand:
    """VWAP with standard deviation bands."""
    vwap: float
    upper_band_1: float  # +1 std dev
    lower_band_1: float  # -1 std dev
    upper_band_2: float  # +2 std dev
    lower_band_2: float  # -2 std dev
    upper_band_3: float  # +3 std dev
    lower_band_3: float  # -3 std dev
    cumulative_volume: float
    timestamp: datetime


class VolumeProfileAnalyzer:
    """Advanced Volume Profile Analysis Engine.
    
    Provides institutional-grade volume profile analysis for identifying
    key support/resistance levels, accumulation zones, and high-probability
    reversal areas.
    """
    
    def __init__(
        self,
        num_bins: int = 100,
        value_area_percent: float = 70.0,
        hvn_threshold: float = 1.5,
        lvn_threshold: float = 0.5,
        session_hours: int = 24
    ):
        """Initialize Volume Profile Analyzer.
        
        Args:
            num_bins: Number of price bins for the profile
            value_area_percent: Percentage of volume for value area (default 70%)
            hvn_threshold: Threshold for High Volume Node (relative to average)
            lvn_threshold: Threshold for Low Volume Node (relative to average)
            session_hours: Hours per session for session profiles
        """
        try:
            self.num_bins = num_bins
            self.value_area_percent = value_area_percent
            self.hvn_threshold = hvn_threshold
            self.lvn_threshold = lvn_threshold
            self.session_hours = session_hours
        
            # Cache for profiles
            self._profile_cache: Dict[str, VolumeProfile] = {}
            self._vwap_cache: Dict[str, List[VWAPBand]] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_volume_profile(
        self,
        df: pd.DataFrame,
        start_idx: Optional[int] = None,
        end_idx: Optional[int] = None,
        profile_type: ProfileType = ProfileType.SESSION
    ) -> VolumeProfile:
        """Calculate volume profile for the given data range.
        
        Args:
            df: DataFrame with OHLCV data
            start_idx: Starting index (None = beginning)
            end_idx: Ending index (None = end)
            profile_type: Type of profile to calculate
            
        Returns:
            VolumeProfile with complete analysis
        """
        # Slice data
        try:
            if start_idx is None:
                start_idx = 0
            if end_idx is None:
                end_idx = len(df)
            
            data = df.iloc[start_idx:end_idx].copy()
        
            if len(data) < 2:
                logger.warning("Insufficient data for volume profile")
                return self._empty_profile(profile_type)
            
            # Get price range
            price_high = data['high'].max()
            price_low = data['low'].min()
            price_range = price_high - price_low
        
            if price_range <= 0:
                logger.warning("Invalid price range for volume profile")
                return self._empty_profile(profile_type)
            
            # Calculate bin size
            bin_size = price_range / self.num_bins
        
            # Create price levels
            price_levels = [price_low + (i * bin_size) for i in range(self.num_bins + 1)]
        
            # Calculate volume at each price level
            volume_at_price = self._distribute_volume(data, price_levels, bin_size)
        
            # Calculate value area
            value_area = self._calculate_value_area(volume_at_price, price_levels)
        
            # Identify volume nodes
            volume_nodes = self._identify_volume_nodes(volume_at_price, price_levels)
        
            # Extract HVN and LVN levels
            hvn_levels = [node.price_level for node in volume_nodes if node.node_type == VolumeNodeType.HVN]
            lvn_levels = [node.price_level for node in volume_nodes if node.node_type == VolumeNodeType.LVN]
        
            # Get timestamps
            start_time = data.index[0] if isinstance(data.index, pd.DatetimeIndex) else datetime.now()
            end_time = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else datetime.now()
        
            return VolumeProfile(
                profile_type=profile_type,
                start_time=start_time,
                end_time=end_time,
                price_levels=price_levels,
                volume_at_price=volume_at_price,
                value_area=value_area,
                volume_nodes=volume_nodes,
                hvn_levels=hvn_levels,
                lvn_levels=lvn_levels,
                total_volume=sum(volume_at_price.values()),
                num_bins=self.num_bins,
                bin_size=bin_size
            )
        except Exception as e:
            logger.error(f"Error in calculate_volume_profile: {e}")
            raise
        
    def _distribute_volume(
        self,
        data: pd.DataFrame,
        price_levels: List[float],
        bin_size: float
    ) -> Dict[float, float]:
        """Distribute volume across price levels using TPO-style distribution.
        
        For each bar, volume is distributed proportionally across the price
        range covered by that bar.
        """
        try:
            volume_at_price = {level: 0.0 for level in price_levels[:-1]}
        
            for _, row in data.iterrows():
                bar_high = row['high']
                bar_low = row['low']
                bar_volume = row.get('volume', 1.0)
            
                if pd.isna(bar_volume) or bar_volume <= 0:
                    bar_volume = 1.0
                
                # Find bins that this bar touches
                bar_range = bar_high - bar_low
                if bar_range <= 0:
                    bar_range = bin_size
                
                for level in price_levels[:-1]:
                    level_high = level + bin_size
                
                    # Check if bar overlaps with this level
                    if bar_low <= level_high and bar_high >= level:
                        # Calculate overlap
                        overlap_low = max(bar_low, level)
                        overlap_high = min(bar_high, level_high)
                        overlap = overlap_high - overlap_low
                    
                        # Distribute volume proportionally
                        volume_portion = (overlap / bar_range) * bar_volume
                        volume_at_price[level] += volume_portion
                    
            return volume_at_price
        except Exception as e:
            logger.error(f"Error in _distribute_volume: {e}")
            raise
        
    def _calculate_value_area(
        self,
        volume_at_price: Dict[float, float],
        price_levels: List[float]
    ) -> ValueArea:
        """Calculate Value Area (VAH, VAL, VPOC).
        
        The Value Area contains 70% of the total volume, centered around
        the Point of Control (highest volume price level).
        """
        try:
            total_volume = sum(volume_at_price.values())
        
            if total_volume <= 0:
                return ValueArea(
                    vah=price_levels[-1],
                    val=price_levels[0],
                    vpoc=price_levels[len(price_levels) // 2],
                    value_area_volume=0,
                    total_volume=0,
                    value_area_percent=self.value_area_percent
                )
            
            # Find VPOC (Volume Point of Control)
            vpoc_level = max(volume_at_price.keys(), key=lambda x: volume_at_price[x])
        
            # Calculate Value Area using the standard algorithm
            target_volume = total_volume * (self.value_area_percent / 100.0)
        
            # Start from VPOC and expand outward
            sorted_levels = sorted(price_levels[:-1])
            vpoc_idx = sorted_levels.index(vpoc_level)
        
            va_volume = volume_at_price[vpoc_level]
            va_low_idx = vpoc_idx
            va_high_idx = vpoc_idx
        
            while va_volume < target_volume:
                # Check volume above and below
                vol_above = 0.0
                vol_below = 0.0
            
                if va_high_idx < len(sorted_levels) - 1:
                    vol_above = volume_at_price.get(sorted_levels[va_high_idx + 1], 0)
                if va_low_idx > 0:
                    vol_below = volume_at_price.get(sorted_levels[va_low_idx - 1], 0)
                
                # Expand in direction of higher volume
                if vol_above >= vol_below and va_high_idx < len(sorted_levels) - 1:
                    va_high_idx += 1
                    va_volume += vol_above
                elif va_low_idx > 0:
                    va_low_idx -= 1
                    va_volume += vol_below
                else:
                    break
                
            return ValueArea(
                vah=sorted_levels[va_high_idx] + (sorted_levels[1] - sorted_levels[0]),  # Add bin size
                val=sorted_levels[va_low_idx],
                vpoc=vpoc_level,
                value_area_volume=va_volume,
                total_volume=total_volume,
                value_area_percent=self.value_area_percent
            )
        except Exception as e:
            logger.error(f"Error in _calculate_value_area: {e}")
            raise
        
    def _identify_volume_nodes(
        self,
        volume_at_price: Dict[float, float],
        price_levels: List[float]
    ) -> List[VolumeNode]:
        """Identify High Volume Nodes (HVN) and Low Volume Nodes (LVN)."""
        try:
            volumes = list(volume_at_price.values())
        
            if not volumes or sum(volumes) == 0:
                return []
            
            avg_volume = np.mean(volumes)
            bin_size = price_levels[1] - price_levels[0] if len(price_levels) > 1 else 0
        
            nodes = []
            for level in price_levels[:-1]:
                vol = volume_at_price.get(level, 0)
                relative_vol = vol / avg_volume if avg_volume > 0 else 0
            
                if relative_vol >= self.hvn_threshold:
                    node_type = VolumeNodeType.HVN
                elif relative_vol <= self.lvn_threshold:
                    node_type = VolumeNodeType.LVN
                else:
                    node_type = VolumeNodeType.NEUTRAL
                
                nodes.append(VolumeNode(
                    price_level=level,
                    volume=vol,
                    node_type=node_type,
                    relative_volume=relative_vol,
                    price_range=(level, level + bin_size)
                ))
            
            return nodes
        except Exception as e:
            logger.error(f"Error in _identify_volume_nodes: {e}")
            raise
        
    def calculate_vwap(
        self,
        df: pd.DataFrame,
        anchor: Optional[datetime] = None,
        include_bands: bool = True
    ) -> List[VWAPBand]:
        """Calculate VWAP with standard deviation bands.
        
        Args:
            df: DataFrame with OHLCV data
            anchor: Anchor point for VWAP calculation (None = session start)
            include_bands: Whether to calculate standard deviation bands
            
        Returns:
            List of VWAPBand objects for each bar
        """
        try:
            if len(df) < 1:
                return []
            
            vwap_bands = []
        
            # Calculate typical price
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            volume = df['volume'].fillna(1)
        
            # Cumulative calculations
            cumulative_tp_vol = (typical_price * volume).cumsum()
            cumulative_vol = volume.cumsum()
        
            vwap = cumulative_tp_vol / cumulative_vol
        
            if include_bands:
                # Calculate standard deviation bands
                squared_diff = ((typical_price - vwap) ** 2 * volume).cumsum()
                variance = squared_diff / cumulative_vol
                std_dev = np.sqrt(variance)
            
                for i in range(len(df)):
                    timestamp = df.index[i] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
                
                    vwap_bands.append(VWAPBand(
                        vwap=float(vwap.iloc[i]),
                        upper_band_1=float(vwap.iloc[i] + std_dev.iloc[i]),
                        lower_band_1=float(vwap.iloc[i] - std_dev.iloc[i]),
                        upper_band_2=float(vwap.iloc[i] + 2 * std_dev.iloc[i]),
                        lower_band_2=float(vwap.iloc[i] - 2 * std_dev.iloc[i]),
                        upper_band_3=float(vwap.iloc[i] + 3 * std_dev.iloc[i]),
                        lower_band_3=float(vwap.iloc[i] - 3 * std_dev.iloc[i]),
                        cumulative_volume=float(cumulative_vol.iloc[i]),
                        timestamp=timestamp
                    ))
            else:
                for i in range(len(df)):
                    timestamp = df.index[i] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
                    vwap_val = float(vwap.iloc[i])
                
                    vwap_bands.append(VWAPBand(
                        vwap=vwap_val,
                        upper_band_1=vwap_val,
                        lower_band_1=vwap_val,
                        upper_band_2=vwap_val,
                        lower_band_2=vwap_val,
                        upper_band_3=vwap_val,
                        lower_band_3=vwap_val,
                        cumulative_volume=float(cumulative_vol.iloc[i]),
                        timestamp=timestamp
                    ))
                
            return vwap_bands
        except Exception as e:
            logger.error(f"Error in calculate_vwap: {e}")
            raise
        
    def calculate_multi_day_vwap(
        self,
        df: pd.DataFrame,
        days: int = 5
    ) -> Dict[int, List[VWAPBand]]:
        """Calculate VWAP for multiple days.
        
        Args:
            df: DataFrame with OHLCV data
            days: Number of days to calculate
            
        Returns:
            Dictionary mapping day number to VWAP bands
        """
        try:
            multi_day_vwap = {}
        
            if not isinstance(df.index, pd.DatetimeIndex):
                logger.warning("DataFrame index must be DatetimeIndex for multi-day VWAP")
                return multi_day_vwap
            
            # Group by date
            df['date'] = df.index.date
        
            for day_num, (date, day_data) in enumerate(df.groupby('date')):
                if day_num >= days:
                    break
                multi_day_vwap[day_num] = self.calculate_vwap(day_data.drop(columns=['date']))
            
            return multi_day_vwap
        except Exception as e:
            logger.error(f"Error in calculate_multi_day_vwap: {e}")
            raise
        
    def calculate_session_vwap(
        self,
        df: pd.DataFrame,
        session_start_hour: int = 9,
        session_end_hour: int = 16
    ) -> List[VWAPBand]:
        """Calculate session-specific VWAP (e.g., regular trading hours only).
        
        Args:
            df: DataFrame with OHLCV data
            session_start_hour: Session start hour (24-hour format)
            session_end_hour: Session end hour (24-hour format)
            
        Returns:
            List of VWAPBand objects for session hours
        """
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                return self.calculate_vwap(df)
            
            # Filter to session hours
            session_mask = (df.index.hour >= session_start_hour) & (df.index.hour < session_end_hour)
            session_data = df[session_mask]
        
            if len(session_data) == 0:
                return []
            
            return self.calculate_vwap(session_data)
        except Exception as e:
            logger.error(f"Error in calculate_session_vwap: {e}")
            raise
        
    def calculate_tpo_profile(
        self,
        df: pd.DataFrame,
        tpo_period_minutes: int = 30,
        initial_balance_periods: int = 2
    ) -> TPOProfile:
        """Calculate Time Price Opportunity (Market Profile).
        
        Args:
            df: DataFrame with OHLCV data
            tpo_period_minutes: Minutes per TPO period (default 30)
            initial_balance_periods: Number of periods for Initial Balance
            
        Returns:
            TPOProfile with complete market profile analysis
        """
        try:
            if len(df) < 2:
                return self._empty_tpo_profile()
            
            # Get price range
            price_high = df['high'].max()
            price_low = df['low'].min()
        
            # Create price levels (tick-based)
            tick_size = (price_high - price_low) / self.num_bins
            price_levels = [price_low + (i * tick_size) for i in range(self.num_bins + 1)]
        
            # Count TPOs at each price level
            tpo_count = {level: 0 for level in price_levels[:-1]}
        
            for _, row in df.iterrows():
                bar_high = row['high']
                bar_low = row['low']
            
                for level in price_levels[:-1]:
                    level_high = level + tick_size
                    if bar_low <= level_high and bar_high >= level:
                        tpo_count[level] += 1
                    
            # Find POC
            poc = max(tpo_count.keys(), key=lambda x: tpo_count[x])
        
            # Calculate Initial Balance
            ib_data = df.iloc[:initial_balance_periods] if len(df) >= initial_balance_periods else df
            ib_high = ib_data['high'].max()
            ib_low = ib_data['low'].min()
        
            # Calculate Value Area
            total_tpos = sum(tpo_count.values())
            target_tpos = total_tpos * 0.70
        
            sorted_levels = sorted(price_levels[:-1])
            poc_idx = sorted_levels.index(poc)
        
            va_tpos = tpo_count[poc]
            va_low_idx = poc_idx
            va_high_idx = poc_idx
        
            while va_tpos < target_tpos and (va_low_idx > 0 or va_high_idx < len(sorted_levels) - 1):
                tpos_above = tpo_count.get(sorted_levels[va_high_idx + 1], 0) if va_high_idx < len(sorted_levels) - 1 else 0
                tpos_below = tpo_count.get(sorted_levels[va_low_idx - 1], 0) if va_low_idx > 0 else 0
            
                if tpos_above >= tpos_below and va_high_idx < len(sorted_levels) - 1:
                    va_high_idx += 1
                    va_tpos += tpos_above
                elif va_low_idx > 0:
                    va_low_idx -= 1
                    va_tpos += tpos_below
                else:
                    break
                
            value_area = ValueArea(
                vah=sorted_levels[va_high_idx] + tick_size,
                val=sorted_levels[va_low_idx],
                vpoc=poc,
                value_area_volume=va_tpos,
                total_volume=total_tpos,
                value_area_percent=70.0
            )
        
            # Identify single prints (levels with only 1 TPO)
            single_prints = [level for level, count in tpo_count.items() if count == 1]
        
            # Identify poor highs/lows (multiple TPOs at extremes)
            poor_highs = []
            poor_lows = []
        
            # Check top 5% of range for poor highs
            high_threshold = price_low + (price_high - price_low) * 0.95
            for level in sorted_levels:
                if level >= high_threshold and tpo_count[level] >= 2:
                    poor_highs.append(level)
                
            # Check bottom 5% of range for poor lows
            low_threshold = price_low + (price_high - price_low) * 0.05
            for level in sorted_levels:
                if level <= low_threshold and tpo_count[level] >= 2:
                    poor_lows.append(level)
                
            # Check for excess (single TPO at extreme with gap)
            excess_high = None
            excess_low = None
        
            if sorted_levels and tpo_count[sorted_levels[-1]] == 1:
                excess_high = sorted_levels[-1]
            if sorted_levels and tpo_count[sorted_levels[0]] == 1:
                excess_low = sorted_levels[0]
            
            return TPOProfile(
                price_levels=price_levels,
                tpo_count=tpo_count,
                poc=poc,
                initial_balance_high=ib_high,
                initial_balance_low=ib_low,
                value_area=value_area,
                single_prints=single_prints,
                poor_highs=poor_highs,
                poor_lows=poor_lows,
                excess_high=excess_high,
                excess_low=excess_low
            )
        except Exception as e:
            logger.error(f"Error in calculate_tpo_profile: {e}")
            raise
        
    def get_support_resistance_levels(
        self,
        profile: VolumeProfile,
        num_levels: int = 5
    ) -> Dict[str, List[float]]:
        """Extract key support and resistance levels from volume profile.
        
        Args:
            profile: VolumeProfile to analyze
            num_levels: Number of levels to return
            
        Returns:
            Dictionary with 'support' and 'resistance' levels
        """
        # HVN levels act as support/resistance
        try:
            hvn_sorted = sorted(profile.hvn_levels)
        
            # Current price approximation (use VPOC as reference)
            current_price = profile.value_area.vpoc
        
            support_levels = [level for level in hvn_sorted if level < current_price]
            resistance_levels = [level for level in hvn_sorted if level > current_price]
        
            # Add VAL and VAH
            if profile.value_area.val not in support_levels:
                support_levels.append(profile.value_area.val)
            if profile.value_area.vah not in resistance_levels:
                resistance_levels.append(profile.value_area.vah)
            
            # Sort and limit
            support_levels = sorted(support_levels, reverse=True)[:num_levels]
            resistance_levels = sorted(resistance_levels)[:num_levels]
        
            return {
                'support': support_levels,
                'resistance': resistance_levels,
                'vpoc': profile.value_area.vpoc,
                'vah': profile.value_area.vah,
                'val': profile.value_area.val
            }
        except Exception as e:
            logger.error(f"Error in get_support_resistance_levels: {e}")
            raise
        
    def identify_naked_vpoc(
        self,
        profiles: List[VolumeProfile],
        current_price: float
    ) -> List[float]:
        """Identify naked (untested) VPOCs from previous sessions.
        
        Naked VPOCs are strong magnets for price and often act as
        support/resistance levels.
        
        Args:
            profiles: List of historical volume profiles
            current_price: Current market price
            
        Returns:
            List of naked VPOC levels
        """
        try:
            naked_vpocs = []
        
            for profile in profiles:
                vpoc = profile.value_area.vpoc
            
                # Check if VPOC has been tested
                # A VPOC is considered tested if price has traded through it
                is_naked = True
            
                for other_profile in profiles:
                    if other_profile.start_time > profile.end_time:
                        # Check if subsequent profile traded through this VPOC
                        if other_profile.value_area.val <= vpoc <= other_profile.value_area.vah:
                            is_naked = False
                            break
                        
                if is_naked:
                    naked_vpocs.append(vpoc)
                
            return naked_vpocs
        except Exception as e:
            logger.error(f"Error in identify_naked_vpoc: {e}")
            raise
        
    def calculate_volume_delta(
        self,
        df: pd.DataFrame
    ) -> pd.Series:
        """Calculate cumulative volume delta (buying vs selling pressure).
        
        Approximates delta using price action within each bar.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Series with cumulative volume delta
        """
        # Approximate delta: if close > open, more buying; if close < open, more selling
        try:
            delta = df.apply(
                lambda row: row['volume'] * (
                    (row['close'] - row['open']) / (row['high'] - row['low'])
                    if row['high'] != row['low'] else 0
                ),
                axis=1
            )
        
            return delta.cumsum()
        except Exception as e:
            logger.error(f"Error in calculate_volume_delta: {e}")
            raise
        
    def _empty_profile(self, profile_type: ProfileType) -> VolumeProfile:
        """Create an empty volume profile."""
        return VolumeProfile(
            profile_type=profile_type,
            start_time=datetime.now(),
            end_time=datetime.now(),
            price_levels=[],
            volume_at_price={},
            value_area=ValueArea(
                vah=0, val=0, vpoc=0,
                value_area_volume=0, total_volume=0
            ),
            volume_nodes=[],
            hvn_levels=[],
            lvn_levels=[],
            total_volume=0,
            num_bins=self.num_bins,
            bin_size=0
        )
        
    def _empty_tpo_profile(self) -> TPOProfile:
        """Create an empty TPO profile."""
        return TPOProfile(
            price_levels=[],
            tpo_count={},
            poc=0,
            initial_balance_high=0,
            initial_balance_low=0,
            value_area=ValueArea(
                vah=0, val=0, vpoc=0,
                value_area_volume=0, total_volume=0
            ),
            single_prints=[],
            poor_highs=[],
            poor_lows=[],
            excess_high=None,
            excess_low=None
        )


# Convenience functions for quick analysis
def get_vpoc(df: pd.DataFrame, num_bins: int = 100) -> float:
    """Quick function to get VPOC from data."""
    try:
        analyzer = VolumeProfileAnalyzer(num_bins=num_bins)
        profile = analyzer.calculate_volume_profile(df)
        return profile.value_area.vpoc
    except Exception as e:
        logger.error(f"Error in get_vpoc: {e}")
        raise


def get_value_area(df: pd.DataFrame, num_bins: int = 100) -> Tuple[float, float, float]:
    """Quick function to get VAH, VAL, VPOC from data."""
    try:
        analyzer = VolumeProfileAnalyzer(num_bins=num_bins)
        profile = analyzer.calculate_volume_profile(df)
        return (
            profile.value_area.vah,
            profile.value_area.val,
            profile.value_area.vpoc
        )
    except Exception as e:
        logger.error(f"Error in get_value_area: {e}")
        raise


def get_hvn_levels(df: pd.DataFrame, num_bins: int = 100) -> List[float]:
    """Quick function to get High Volume Node levels."""
    try:
        analyzer = VolumeProfileAnalyzer(num_bins=num_bins)
        profile = analyzer.calculate_volume_profile(df)
        return profile.hvn_levels
    except Exception as e:
        logger.error(f"Error in get_hvn_levels: {e}")
        raise


def get_lvn_levels(df: pd.DataFrame, num_bins: int = 100) -> List[float]:
    """Quick function to get Low Volume Node levels."""
    try:
        analyzer = VolumeProfileAnalyzer(num_bins=num_bins)
        profile = analyzer.calculate_volume_profile(df)
        return profile.lvn_levels
    except Exception as e:
        logger.error(f"Error in get_lvn_levels: {e}")
        raise
