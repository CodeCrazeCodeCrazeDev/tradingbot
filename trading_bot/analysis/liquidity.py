from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from enum import Enum
"""Advanced Liquidity Analysis Module.

This module provides comprehensive liquidity analysis capabilities for the Elite Trading Bot:
    • Identification of equal highs & lows (potential double-tops / double-bottoms)
    • Detection of liquidity pools (buy-side above highs, sell-side below lows)
    • Tracking liquidity inducements and grabs with strength evaluation
    • Order block identification and classification
    • Fair value gap detection and analysis
    • Multi-timeframe liquidity mapping
    • Volume profile integration for enhanced liquidity analysis
    • Premium/discount zones identification

The implementation follows the Elite Trading Bot specification with advanced
liquidity concepts from institutional trading methodologies.
"""

import enum
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd  # type: ignore
from loguru import logger

from .market_structure import MarketStructureAnalyzer, SwingPoint, TimeFrame

# ---------------------------------------------------------------------------
# Enums and Constants
# ---------------------------------------------------------------------------


class LiquidityType(enum.Enum):
    """Types of liquidity in the market."""
    BUY = "buy"  # Buy-side liquidity above equal highs
    SELL = "sell"  # Sell-side liquidity below equal lows


class OrderBlockType(enum.Enum):
    """Types of order blocks in the market."""
    BULLISH = "bullish"  # Bullish order block (discount)
    BEARISH = "bearish"  # Bearish order block (premium)
    MIXED = "mixed"      # Mixed order block (both characteristics)


class FVGType(enum.Enum):
    """Types of fair value gaps."""
    BULLISH = "bullish"  # Bullish FVG (gap up)
    BEARISH = "bearish"  # Bearish FVG (gap down)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class LiquidityPool:
    """Represents an area where clustered stops/limit orders likely reside."""

    kind: LiquidityType  # Buy or sell side liquidity
    price: float  # Reference price (the equal-high low or high)
    swing_idxs: Tuple[int, ...]  # Indexes of the equal swings (can be more than 2)
    timeframe: TimeFrame = TimeFrame.M15
    strength: float = 1.0  # Relative strength of the liquidity pool (1.0 = normal)
    volume: Optional[float] = None  # Associated volume if available
    touched: bool = False  # Whether this pool has been touched/swept
    mitigated: bool = False  # Whether this pool has been fully mitigated
    created_at: Optional[pd.Timestamp] = None  # When this pool was formed


@dataclass(slots=True)
class LiquidityGrab:
    """Inducement/grab event when price sweeps a pool and reverses."""

    idx: int  # Bar index
    pool: LiquidityPool
    close_price: float
    strength: float = 1.0  # Strength of the grab (based on reversal magnitude)
    volume_delta: Optional[float] = None  # Volume change during the grab
    confirmed: bool = False  # Whether the grab has been confirmed by subsequent price action
    timeframe: TimeFrame = TimeFrame.M15
    correlated_grabs: List["LiquidityGrab"] = field(default_factory=list)  # Grabs on other timeframes


@dataclass(slots=True)
class OrderBlock:
    """Represents an institutional order block."""

    type: OrderBlockType  # Bullish, bearish, or mixed
    start_idx: int  # Starting bar index
    end_idx: int  # Ending bar index (usually start_idx + 1)
    high: float  # High price of the order block
    low: float  # Low price of the order block
    open: float  # Open price of the order block
    close: float  # Close price of the order block
    volume: Optional[float] = None  # Volume of the order block
    strength: float = 1.0  # Relative strength (based on subsequent move)
    timeframe: TimeFrame = TimeFrame.M15
    mitigated: bool = False  # Whether this order block has been mitigated
    mitigation_idx: Optional[int] = None  # Index when mitigation occurred
    created_at: Optional[pd.Timestamp] = None  # When this order block was formed


@dataclass(slots=True)
class FairValueGap:
    """Represents a fair value gap (FVG) in the market."""

    type: FVGType  # Bullish or bearish
    idx: int  # Bar index where the gap occurred
    high: float  # High price of the gap
    low: float  # Low price of the gap
    size: float  # Size of the gap in price units
    size_pct: float  # Size of the gap as percentage of price
    timeframe: TimeFrame = TimeFrame.M15
    filled: bool = False  # Whether this FVG has been filled
    fill_idx: Optional[int] = None  # Index when filling occurred
    strength: float = 1.0  # Relative strength of the FVG
    created_at: Optional[pd.Timestamp] = None  # When this FVG was formed


@dataclass(slots=True)
class VolumeProfile:
    """Volume profile for a price range."""

    price_levels: np.ndarray  # Array of price levels
    volumes: np.ndarray  # Volume at each price level
    poc: float  # Point of control (price level with highest volume)
    value_area_high: float  # Upper boundary of the value area
    value_area_low: float  # Lower boundary of the value area
    value_area_pct: float = 0.68  # Percentage of volume in value area (default 68%)
    timeframe: TimeFrame = TimeFrame.M15


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class LiquidityAnalyzer:
    """Advanced liquidity analysis for institutional trading concepts."""

    def __init__(self, 
                 *,
                 swing_len: int = 3, 
                 tolerance_pct: float = 0.02,
                 volume_weight: float = 0.4,
                 default_timeframe: TimeFrame = TimeFrame.M15,
                 multi_timeframe: bool = True,
                 fvg_min_size_pct: float = 0.1,
                 value_area_pct: float = 0.68) -> None:
        """Initialize the liquidity analyzer.
        
        Args:
            swing_len: Length of swings to detect
            tolerance_pct: Percentage tolerance for equal highs/lows
            volume_weight: Weight of volume in strength calculations (0-1)
            default_timeframe: Default timeframe for analysis
            multi_timeframe: Whether to perform multi-timeframe analysis
            fvg_min_size_pct: Minimum size of FVG as percentage of price
            value_area_pct: Percentage of volume in value area (default 68%)
        """
        self.msa = MarketStructureAnalyzer(swing_len=swing_len, 
                                          default_timeframe=default_timeframe,
                                          volume_weight=volume_weight,
                                          multi_timeframe=multi_timeframe)
        self.tolerance_pct = tolerance_pct
        self.volume_weight = volume_weight
        self.default_timeframe = default_timeframe
        self.multi_timeframe = multi_timeframe
        self.fvg_min_size_pct = fvg_min_size_pct
        self.value_area_pct = value_area_pct
        
        # Cache for multi-timeframe analysis
        self._timeframe_data: Dict[TimeFrame, Dict] = {}
        self._liquidity_pools: Dict[TimeFrame, Tuple[List[LiquidityPool], List[LiquidityPool]]] = {}
        self._order_blocks: Dict[TimeFrame, List[OrderBlock]] = {}
        self._fvgs: Dict[TimeFrame, List[FairValueGap]] = {}
        self._volume_profiles: Dict[TimeFrame, VolumeProfile] = {}

    # ------------------------------------------------------------------
    # Equal Highs / Lows - Liquidity Pools
    # ------------------------------------------------------------------

    def find_equal_highs_lows(
        self, data: pd.DataFrame, timeframe: TimeFrame = None
    ) -> Tuple[List[LiquidityPool], List[LiquidityPool]]:
        """Return lists of buy-side & sell-side liquidity pools with strength evaluation.
        
        Args:
            data: OHLCV DataFrame
            timeframe: Timeframe for analysis (uses default if None)
            
        Returns:
            Tuple of (buy_pools, sell_pools)
        """
        if timeframe is None:
            timeframe = self.default_timeframe
            
        highs, lows = self.msa.find_swings(data)
        buy_pools: list[LiquidityPool] = []  # above equal highs
        sell_pools: list[LiquidityPool] = []  # below equal lows
        
        # Get timestamps if available
        timestamps = data.index if isinstance(data.index, pd.DatetimeIndex) else None

        # Equal highs - now supports clusters of more than 2 points
        high_clusters = self._cluster_swing_points(highs)
        for cluster in high_clusters:
            if len(cluster) >= 2:  # Need at least 2 points for a liquidity pool
                price_avg = sum(sp.price for sp in cluster) / len(cluster)
                idxs = tuple(sp.idx for sp in cluster)
                
                # Calculate strength based on number of points and volume
                strength = min(2.0, 0.75 + 0.25 * len(cluster))  # Base strength from number of points
                
                # Add volume component if available
                volume = None
                if hasattr(cluster[0], 'volume') and all(hasattr(sp, 'volume') for sp in cluster):
                    volume = sum(sp.volume for sp in cluster if sp.volume is not None)
                    if volume is not None and volume > 0:
                        vol_strength = min(1.5, volume / (data['volume'].mean() * len(cluster)))
                        strength = (1 - self.volume_weight) * strength + self.volume_weight * vol_strength
                
                # Create timestamp if available
                created_at = timestamps[max(idxs)] if timestamps is not None else None
                
                buy_pools.append(
                    LiquidityPool(
                        LiquidityType.BUY, 
                        price_avg, 
                        idxs, 
                        timeframe=timeframe,
                        strength=strength,
                        volume=volume,
                        created_at=created_at
                    )
                )

        # Equal lows
        low_clusters = self._cluster_swing_points(lows)
        for cluster in low_clusters:
            if len(cluster) >= 2:  # Need at least 2 points for a liquidity pool
                price_avg = sum(sp.price for sp in cluster) / len(cluster)
                idxs = tuple(sp.idx for sp in cluster)
                
                # Calculate strength based on number of points and volume
                strength = min(2.0, 0.75 + 0.25 * len(cluster))  # Base strength from number of points
                
                # Add volume component if available
                volume = None
                if hasattr(cluster[0], 'volume') and all(hasattr(sp, 'volume') for sp in cluster):
                    volume = sum(sp.volume for sp in cluster if sp.volume is not None)
                    if volume is not None and volume > 0:
                        vol_strength = min(1.5, volume / (data['volume'].mean() * len(cluster)))
                        strength = (1 - self.volume_weight) * strength + self.volume_weight * vol_strength
                
                # Create timestamp if available
                created_at = timestamps[max(idxs)] if timestamps is not None else None
                
                sell_pools.append(
                    LiquidityPool(
                        LiquidityType.SELL, 
                        price_avg, 
                        idxs, 
                        timeframe=timeframe,
                        strength=strength,
                        volume=volume,
                        created_at=created_at
                    )
                )

        # Deduplicate by price
        buy_pools = self._dedup_pools(buy_pools)
        sell_pools = self._dedup_pools(sell_pools)
        
        # Cache results for multi-timeframe analysis
        self._liquidity_pools[timeframe] = (buy_pools, sell_pools)
        
        return buy_pools, sell_pools

    def _cluster_swing_points(self, swing_points: List[SwingPoint]) -> List[List[SwingPoint]]:
        """Group swing points into clusters based on price similarity."""
        if not swing_points:
            return []
            
        # Sort by price
        sorted_points = sorted(swing_points, key=lambda sp: sp.price)
        
        clusters: List[List[SwingPoint]] = [[sorted_points[0]]]
        
        for sp in sorted_points[1:]:
            last_cluster = clusters[-1]
            last_price = last_cluster[-1].price
            
            # Calculate tolerance based on price
            tol = last_price * self.tolerance_pct / 100
            
            if abs(sp.price - last_price) <= tol:
                # Add to existing cluster
                last_cluster.append(sp)
            else:
                # Start new cluster
                clusters.append([sp])
                
        return clusters

    # ------------------------------------------------------------------
    # Liquidity Grabs with Strength Evaluation
    # ------------------------------------------------------------------

    def detect_grabs(
        self, data: pd.DataFrame, pools: Sequence[LiquidityPool], timeframe: TimeFrame = None
    ) -> List[LiquidityGrab]:
        """Detect liquidity grabs with strength evaluation.
        
        Args:
            data: OHLCV DataFrame
            pools: Sequence of liquidity pools to check
            timeframe: Timeframe for analysis (uses default if None)
            
        Returns:
            List of liquidity grabs
        """
        if timeframe is None:
            timeframe = self.default_timeframe
            
        grabs: list[LiquidityGrab] = []
        timestamps = data.index if isinstance(data.index, pd.DatetimeIndex) else None
        
        for pool in pools:
            # Skip pools that have already been touched
            if pool.touched:
                continue
                
            for idx in range(max(pool.swing_idxs) + 1, len(data)):
                bar = data.iloc[idx]
                prev_bar = data.iloc[idx-1] if idx > 0 else None
                
                # Calculate volume delta if volume data is available
                volume_delta = None
                if 'volume' in data.columns and prev_bar is not None:
                    volume_delta = bar.volume - prev_bar.volume
                
                if pool.kind == LiquidityType.BUY and bar.high > pool.price:
                    # Price swept above equal highs
                    pool.touched = True
                    
                    # Check if close below price → reversal
                    if bar.close < pool.price:
                        # Calculate strength based on reversal magnitude and volume
                        strength = 1.0
                        
                        # Stronger if reversal is larger
                        price_range = bar.high - bar.low
                        if price_range > 0:
                            reversal_pct = (bar.high - bar.close) / price_range
                            strength = min(2.0, 0.5 + reversal_pct * 1.5)
                        
                        # Add volume component if available
                        if volume_delta is not None and volume_delta > 0:
                            vol_strength = min(1.5, volume_delta / data['volume'].mean())
                            strength = (1 - self.volume_weight) * strength + self.volume_weight * vol_strength
                        
                        # Create grab with strength evaluation
                        grab = LiquidityGrab(
                            idx, 
                            pool, 
                            bar.close,
                            strength=strength,
                            volume_delta=volume_delta,
                            timeframe=timeframe
                        )
                        
                        # Check if grab is confirmed by subsequent price action
                        if idx + 1 < len(data) and data.iloc[idx+1].close < bar.close:
                            grab.confirmed = True
                            
                        grabs.append(grab)
                        break
                        
                elif pool.kind == LiquidityType.SELL and bar.low < pool.price:
                    # Price swept below equal lows
                    pool.touched = True
                    
                    # Check if close above price → reversal
                    if bar.close > pool.price:
                        # Calculate strength based on reversal magnitude and volume
                        strength = 1.0
                        
                        # Stronger if reversal is larger
                        price_range = bar.high - bar.low
                        if price_range > 0:
                            reversal_pct = (bar.close - bar.low) / price_range
                            strength = min(2.0, 0.5 + reversal_pct * 1.5)
                        
                        # Add volume component if available
                        if volume_delta is not None and volume_delta > 0:
                            vol_strength = min(1.5, volume_delta / data['volume'].mean())
                            strength = (1 - self.volume_weight) * strength + self.volume_weight * vol_strength
                        
                        # Create grab with strength evaluation
                        grab = LiquidityGrab(
                            idx, 
                            pool, 
                            bar.close,
                            strength=strength,
                            volume_delta=volume_delta,
                            timeframe=timeframe
                        )
                        
                        # Check if grab is confirmed by subsequent price action
                        if idx + 1 < len(data) and data.iloc[idx+1].close > bar.close:
                            grab.confirmed = True
                            
                        grabs.append(grab)
                        break
        
        # Mark pools as mitigated if price continues in reversal direction
        for grab in grabs:
            idx = grab.idx
            if idx + 3 < len(data):  # Check if we have enough bars after the grab
                if grab.pool.kind == LiquidityType.BUY:
                    # For buy-side liquidity, check if price continues lower
                    if all(data.iloc[i].close < grab.close_price for i in range(idx+1, idx+4)):
                        grab.pool.mitigated = True
                else:  # SELL
                    # For sell-side liquidity, check if price continues higher
                    if all(data.iloc[i].close > grab.close_price for i in range(idx+1, idx+4)):
                        grab.pool.mitigated = True
        
        return grabs


    # ------------------------------------------------------------------
    # Order Block Detection
    # ------------------------------------------------------------------

    def detect_order_blocks(
        self, data: pd.DataFrame, timeframe: TimeFrame = None
    ) -> List[OrderBlock]:
        """Detect institutional order blocks.
        
        Order blocks are areas where significant orders were placed that led to
        a strong directional move. These are key areas for potential reversals.
        
        Args:
            data: OHLCV DataFrame
            timeframe: Timeframe for analysis (uses default if None)
            
        Returns:
            List of order blocks
        """
        if timeframe is None:
            timeframe = self.default_timeframe
            
        order_blocks: List[OrderBlock] = []
        timestamps = data.index if isinstance(data.index, pd.DatetimeIndex) else None
        
        # Need at least 20 bars for meaningful analysis
        if len(data) < 20:
            return order_blocks
            
        # Look for strong directional moves
        for i in range(3, len(data) - 1):
            # Current bar and previous bars
            curr = data.iloc[i]
            prev1 = data.iloc[i-1]
            prev2 = data.iloc[i-2]
            prev3 = data.iloc[i-3]
            
            # Next bar to confirm the move
            next_bar = data.iloc[i+1] if i+1 < len(data) else None
            
            # Check for bullish order block (discount)
            # Look for a strong bearish move followed by a strong bullish move
            if (
                # Previous bearish move
                prev3.close > prev3.open > prev2.close and
                prev2.close > prev2.open > prev1.close and
                # Current strong bullish move
                curr.open < curr.close and
                curr.close > prev1.high and
                # Confirmed by next bar
                next_bar is not None and
                next_bar.low > curr.low
            ):
                # The order block is the last bearish candle before the bullish move
                ob = OrderBlock(
                    type=OrderBlockType.BULLISH,
                    start_idx=i-1,
                    end_idx=i-1,
                    high=prev1.high,
                    low=prev1.low,
                    open=prev1.open,
                    close=prev1.close,
                    volume=prev1.volume if 'volume' in data.columns else None,
                    timeframe=timeframe,
                    created_at=timestamps[i-1] if timestamps is not None else None
                )
                
                # Calculate strength based on the subsequent move
                move_size = curr.close - curr.open
                avg_move = data['close'].diff().abs().rolling(10).mean().iloc[i] or 0.0001
                ob.strength = min(2.0, 0.75 + (move_size / avg_move) * 0.25)
                
                # Add volume component if available
                if 'volume' in data.columns and ob.volume is not None:
                    vol_ratio = ob.volume / data['volume'].rolling(10).mean().iloc[i-1]
                    ob.strength = (1 - self.volume_weight) * ob.strength + self.volume_weight * min(1.5, vol_ratio)
                
                order_blocks.append(ob)
                
            # Check for bearish order block (premium)
            # Look for a strong bullish move followed by a strong bearish move
            elif (
                # Previous bullish move
                prev3.close < prev3.open < prev2.close and
                prev2.close < prev2.open < prev1.close and
                # Current strong bearish move
                curr.open > curr.close and
                curr.close < prev1.low and
                # Confirmed by next bar
                next_bar is not None and
                next_bar.high < curr.high
            ):
                # The order block is the last bullish candle before the bearish move
                ob = OrderBlock(
                    type=OrderBlockType.BEARISH,
                    start_idx=i-1,
                    end_idx=i-1,
                    high=prev1.high,
                    low=prev1.low,
                    open=prev1.open,
                    close=prev1.close,
                    volume=prev1.volume if 'volume' in data.columns else None,
                    timeframe=timeframe,
                    created_at=timestamps[i-1] if timestamps is not None else None
                )
                
                # Calculate strength based on the subsequent move
                move_size = curr.open - curr.close
                avg_move = data['close'].diff().abs().rolling(10).mean().iloc[i] or 0.0001
                ob.strength = min(2.0, 0.75 + (move_size / avg_move) * 0.25)
                
                # Add volume component if available
                if 'volume' in data.columns and ob.volume is not None:
                    vol_ratio = ob.volume / data['volume'].rolling(10).mean().iloc[i-1]
                    ob.strength = (1 - self.volume_weight) * ob.strength + self.volume_weight * min(1.5, vol_ratio)
                
                order_blocks.append(ob)
        
        # Cache results for multi-timeframe analysis
        self._order_blocks[timeframe] = order_blocks
        
        return order_blocks

    def check_order_block_mitigation(
        self, data: pd.DataFrame, order_blocks: List[OrderBlock]
    ) -> None:
        """Check if order blocks have been mitigated by price action.
        
        Args:
            data: OHLCV DataFrame
            order_blocks: List of order blocks to check
        """
        for ob in order_blocks:
            if ob.mitigated:
                continue
                
            # Check bars after the order block
            for i in range(ob.end_idx + 1, len(data)):
                bar = data.iloc[i]
                
                if ob.type == OrderBlockType.BULLISH:
                    # Bullish OB is mitigated when price trades back into it
                    if bar.low <= ob.high and bar.low >= ob.low:
                        ob.mitigated = True
                        ob.mitigation_idx = i
                        break
                else:  # BEARISH
                    # Bearish OB is mitigated when price trades back into it
                    if bar.high >= ob.low and bar.high <= ob.high:
                        ob.mitigated = True
                        ob.mitigation_idx = i
                        break

    # ------------------------------------------------------------------
    # Fair Value Gap Detection
    # ------------------------------------------------------------------

    def detect_fair_value_gaps(
        self, data: pd.DataFrame, timeframe: TimeFrame = None
    ) -> List[FairValueGap]:
        """Detect fair value gaps (FVGs) in the market.
        
        FVGs occur when price jumps, leaving an imbalance that often gets filled later.
        
        Args:
            data: OHLCV DataFrame
            timeframe: Timeframe for analysis (uses default if None)
            
        Returns:
            List of fair value gaps
        """
        if timeframe is None:
            timeframe = self.default_timeframe
            
        fvgs: List[FairValueGap] = []
        timestamps = data.index if isinstance(data.index, pd.DatetimeIndex) else None
        
        # Need at least 3 bars
        if len(data) < 3:
            return fvgs
            
        # Look for gaps between candles
        for i in range(1, len(data) - 1):
            prev_bar = data.iloc[i-1]
            curr_bar = data.iloc[i]
            next_bar = data.iloc[i+1]
            
            # Bullish FVG (gap up)
            if prev_bar.high < next_bar.low:
                gap_size = next_bar.low - prev_bar.high
                gap_pct = gap_size / prev_bar.close * 100
                
                # Only consider significant gaps
                if gap_pct >= self.fvg_min_size_pct:
                    fvg = FairValueGap(
                        type=FVGType.BULLISH,
                        idx=i,
                        high=next_bar.low,
                        low=prev_bar.high,
                        size=gap_size,
                        size_pct=gap_pct,
                        timeframe=timeframe,
                        created_at=timestamps[i] if timestamps is not None else None
                    )
                    
                    # Calculate strength based on gap size and volume
                    fvg.strength = min(2.0, 0.75 + gap_pct / 2)
                    
                    # Add volume component if available
                    if 'volume' in data.columns:
                        vol_ratio = curr_bar.volume / data['volume'].rolling(10).mean().iloc[i]
                        fvg.strength = (1 - self.volume_weight) * fvg.strength + self.volume_weight * min(1.5, vol_ratio)
                    
                    fvgs.append(fvg)
                    
            # Bearish FVG (gap down)
            elif prev_bar.low > next_bar.high:
                gap_size = prev_bar.low - next_bar.high
                gap_pct = gap_size / prev_bar.close * 100
                
                # Only consider significant gaps
                if gap_pct >= self.fvg_min_size_pct:
                    fvg = FairValueGap(
                        type=FVGType.BEARISH,
                        idx=i,
                        high=prev_bar.low,
                        low=next_bar.high,
                        size=gap_size,
                        size_pct=gap_pct,
                        timeframe=timeframe,
                        created_at=timestamps[i] if timestamps is not None else None
                    )
                    
                    # Calculate strength based on gap size and volume
                    fvg.strength = min(2.0, 0.75 + gap_pct / 2)
                    
                    # Add volume component if available
                    if 'volume' in data.columns:
                        vol_ratio = curr_bar.volume / data['volume'].rolling(10).mean().iloc[i]
                        fvg.strength = (1 - self.volume_weight) * fvg.strength + self.volume_weight * min(1.5, vol_ratio)
                    
                    fvgs.append(fvg)
        
        # Cache results for multi-timeframe analysis
        self._fvgs[timeframe] = fvgs
        
        return fvgs

    def check_fvg_filling(
        self, data: pd.DataFrame, fvgs: List[FairValueGap]
    ) -> None:
        """Check if fair value gaps have been filled by price action.
        
        Args:
            data: OHLCV DataFrame
            fvgs: List of fair value gaps to check
        """
        for fvg in fvgs:
            if fvg.filled:
                continue
                
            # Check bars after the FVG
            for i in range(fvg.idx + 1, len(data)):
                bar = data.iloc[i]
                
                if fvg.type == FVGType.BULLISH:
                    # Bullish FVG is filled when price trades back down into the gap
                    if bar.low <= fvg.high and bar.low >= fvg.low:
                        fvg.filled = True
                        fvg.fill_idx = i
                        break
                else:  # BEARISH
                    # Bearish FVG is filled when price trades back up into the gap
                    if bar.high >= fvg.low and bar.high <= fvg.high:
                        fvg.filled = True
                        fvg.fill_idx = i
                        break

    # ------------------------------------------------------------------
    # Volume Profile Analysis
    # ------------------------------------------------------------------

    def create_volume_profile(
        self, data: pd.DataFrame, num_bins: int = 20, timeframe: TimeFrame = None
    ) -> VolumeProfile:
        """Create a volume profile for the given price range.
        
        Args:
            data: OHLCV DataFrame with 'volume' column
            num_bins: Number of price bins to use
            timeframe: Timeframe for analysis (uses default if None)
            
        Returns:
            VolumeProfile object
        """
        if timeframe is None:
            timeframe = self.default_timeframe
            
        if 'volume' not in data.columns:
            raise ValueError("Volume data required for volume profile analysis")
            
        # Create price bins
        price_min = data['low'].min()
        price_max = data['high'].max()
        price_range = price_max - price_min
        bin_size = price_range / num_bins
        
        # Create price levels
        price_levels = np.linspace(price_min, price_max, num_bins)
        volumes = np.zeros(num_bins)
        
        # Distribute volume across price levels
        for i in range(len(data)):
            bar = data.iloc[i]
            bar_range = bar.high - bar.low
            
            if bar_range <= 0:
                continue
                
            # Distribute volume proportionally across price range of the bar
            for j in range(num_bins):
                level = price_levels[j]
                if bar.low <= level <= bar.high:
                    # Weight by proximity to center of the bar
                    weight = 1 - abs(level - (bar.low + bar.high) / 2) / (bar_range / 2)
                    volumes[j] += bar.volume * weight
        
        # Find point of control (price level with highest volume)
        poc_idx = np.argmax(volumes)
        poc = price_levels[poc_idx]
        
        # Calculate value area (68% of volume by default)
        total_volume = np.sum(volumes)
        target_volume = total_volume * self.value_area_pct
        
        # Start from POC and expand outward
        left = right = poc_idx
        cumulative_volume = volumes[poc_idx]
        
        while cumulative_volume < target_volume and (left > 0 or right < num_bins - 1):
            # Expand to the side with higher volume
            left_vol = volumes[left - 1] if left > 0 else 0
            right_vol = volumes[right + 1] if right < num_bins - 1 else 0
            
            if left_vol > right_vol and left > 0:
                left -= 1
                cumulative_volume += volumes[left]
            elif right < num_bins - 1:
                right += 1
                cumulative_volume += volumes[right]
            else:
                break
        
        value_area_low = price_levels[left]
        value_area_high = price_levels[right]
        
        profile = VolumeProfile(
            price_levels=price_levels,
            volumes=volumes,
            poc=poc,
            value_area_high=value_area_high,
            value_area_low=value_area_low,
            value_area_pct=self.value_area_pct,
            timeframe=timeframe
        )
        
        # Cache results for multi-timeframe analysis
        self._volume_profiles[timeframe] = profile
        
        return profile

    # ------------------------------------------------------------------
    # Multi-Timeframe Analysis
    # ------------------------------------------------------------------

    def analyze_multi_timeframe(
        self, data_dict: Dict[TimeFrame, pd.DataFrame]
    ) -> Dict[str, Dict[TimeFrame, List]]:
        """Perform multi-timeframe analysis on all provided timeframes.
        
        Args:
            data_dict: Dictionary mapping timeframes to their respective DataFrames
            
        Returns:
            Dictionary of analysis results by type and timeframe
        """
        if not self.multi_timeframe:
            logger.warning("Multi-timeframe analysis is disabled. Enable with multi_timeframe=True")
            return {}
            
        # Store data for later reference
        self._timeframe_data = data_dict
        
        # Analyze each timeframe
        for tf, data in data_dict.items():
            # Find liquidity pools
            self.find_equal_highs_lows(data, timeframe=tf)
            
            # Detect order blocks
            self.detect_order_blocks(data, timeframe=tf)
            
            # Detect fair value gaps
            self.detect_fair_value_gaps(data, timeframe=tf)
            
            # Create volume profile if volume data is available
            if 'volume' in data.columns:
                try:
                    self.create_volume_profile(data, timeframe=tf)
                except Exception as e:
                    logger.warning(f"Failed to create volume profile for {tf}: {e}")
        
        # Correlate findings across timeframes
        self._correlate_liquidity_pools()
        self._correlate_order_blocks()
        self._correlate_fvgs()
        
        # Return all analysis results
        return {
            "liquidity_pools": self._liquidity_pools,
            "order_blocks": self._order_blocks,
            "fvgs": self._fvgs,
            "volume_profiles": self._volume_profiles
        }

    def _correlate_liquidity_pools(self) -> None:
        """Correlate liquidity pools across timeframes to enhance strength."""
        if len(self._liquidity_pools) <= 1:
            return
            
        # Sort timeframes from smallest to largest
        timeframes = sorted(self._liquidity_pools.keys(), 
                           key=lambda tf: TimeFrame[tf.name].value if isinstance(tf, TimeFrame) else 0)
        
        # For each larger timeframe, check if its pools are confirmed by smaller timeframes
        for i in range(1, len(timeframes)):
            larger_tf = timeframes[i]
            buy_pools, sell_pools = self._liquidity_pools[larger_tf]
            
            # Check each larger timeframe pool against smaller timeframe pools
            for pool in buy_pools + sell_pools:
                for j in range(i):
                    smaller_tf = timeframes[j]
                    smaller_buy_pools, smaller_sell_pools = self._liquidity_pools[smaller_tf]
                    
                    # Check against pools of the same kind
                    smaller_pools = smaller_buy_pools if pool.kind == LiquidityType.BUY else smaller_sell_pools
                    
                    # Find confirming pools within tolerance
                    confirming_pools = []
                    for sp in smaller_pools:
                        # If prices are within tolerance, consider it a confirmation
                        if abs(sp.price - pool.price) / pool.price < self.tolerance_pct / 100:
                            confirming_pools.append(sp)
                    
                    # Enhance strength based on confirmations
                    if confirming_pools:
                        # More confirmations = stronger
                        confirmation_boost = min(0.5, 0.1 * len(confirming_pools))
                        pool.strength = min(2.0, pool.strength + confirmation_boost)

    def _correlate_order_blocks(self) -> None:
        """Correlate order blocks across timeframes to enhance strength."""
        if len(self._order_blocks) <= 1:
            return
            
        # Sort timeframes from smallest to largest
        timeframes = sorted(self._order_blocks.keys(), 
                           key=lambda tf: TimeFrame[tf.name].value if isinstance(tf, TimeFrame) else 0)
        
        # For each larger timeframe, check if its order blocks are confirmed by smaller timeframes
        for i in range(1, len(timeframes)):
            larger_tf = timeframes[i]
            larger_obs = self._order_blocks[larger_tf]
            
            # Check each larger timeframe order block against smaller timeframe order blocks
            for ob in larger_obs:
                for j in range(i):
                    smaller_tf = timeframes[j]
                    smaller_obs = self._order_blocks[smaller_tf]
                    
                    # Find confirming order blocks of the same type
                    confirming_obs = []
                    for sob in smaller_obs:
                        if sob.type == ob.type:
                            # Check if price ranges overlap
                            if (sob.low <= ob.high and sob.high >= ob.low):
                                confirming_obs.append(sob)
                    
                    # Enhance strength based on confirmations
                    if confirming_obs:
                        # More confirmations = stronger
                        confirmation_boost = min(0.5, 0.1 * len(confirming_obs))
                        ob.strength = min(2.0, ob.strength + confirmation_boost)

    def _correlate_fvgs(self) -> None:
        """Correlate fair value gaps across timeframes to enhance strength."""
        if len(self._fvgs) <= 1:
            return
            
        # Sort timeframes from smallest to largest
        timeframes = sorted(self._fvgs.keys(), 
                           key=lambda tf: TimeFrame[tf.name].value if isinstance(tf, TimeFrame) else 0)
        
        # For each larger timeframe, check if its FVGs are confirmed by smaller timeframes
        for i in range(1, len(timeframes)):
            larger_tf = timeframes[i]
            larger_fvgs = self._fvgs[larger_tf]
            
            # Check each larger timeframe FVG against smaller timeframe FVGs
            for fvg in larger_fvgs:
                for j in range(i):
                    smaller_tf = timeframes[j]
                    smaller_fvgs = self._fvgs[smaller_tf]
                    
                    # Find confirming FVGs of the same type
                    confirming_fvgs = []
                    for sfvg in smaller_fvgs:
                        if sfvg.type == fvg.type:
                            # Check if price ranges overlap
                            if (sfvg.low <= fvg.high and sfvg.high >= fvg.low):
                                confirming_fvgs.append(sfvg)
                    
                    # Enhance strength based on confirmations
                    if confirming_fvgs:
                        # More confirmations = stronger
                        confirmation_boost = min(0.5, 0.1 * len(confirming_fvgs))
                        fvg.strength = min(2.0, fvg.strength + confirmation_boost)

    # ------------------------------------------------------------------
    # Premium/Discount Zone Identification
    # ------------------------------------------------------------------

    def identify_premium_discount_zones(
        self, data: pd.DataFrame, timeframe: TimeFrame = None
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Identify premium and discount zones based on liquidity and order blocks.
        
        Premium zones are areas where price is likely to reverse downward.
        Discount zones are areas where price is likely to reverse upward.
        
        Args:
            data: OHLCV DataFrame
            timeframe: Timeframe for analysis (uses default if None)
            
        Returns:
            Tuple of (premium_zones, discount_zones) as lists of (high, low) tuples
        """
        if timeframe is None:
            timeframe = self.default_timeframe
            
        # Get liquidity pools and order blocks for this timeframe
        buy_pools, sell_pools = self._liquidity_pools.get(timeframe, ([], []))
        order_blocks = self._order_blocks.get(timeframe, [])
        
        premium_zones: List[Tuple[float, float]] = []
        discount_zones: List[Tuple[float, float]] = []
        
        # Premium zones from sell-side liquidity and bearish order blocks
        for pool in sell_pools:
            if pool.strength >= 1.2 and not pool.mitigated:
                # Create zone around the pool price
                zone_size = data['close'].iloc[-1] * 0.002  # 0.2% of current price
                premium_zones.append((pool.price + zone_size, pool.price - zone_size))
        
        for ob in order_blocks:
            if ob.type == OrderBlockType.BEARISH and ob.strength >= 1.2 and not ob.mitigated:
                premium_zones.append((ob.high, ob.low))
        
        # Discount zones from buy-side liquidity and bullish order blocks
        for pool in buy_pools:
            if pool.strength >= 1.2 and not pool.mitigated:
                # Create zone around the pool price
                zone_size = data['close'].iloc[-1] * 0.002  # 0.2% of current price
                discount_zones.append((pool.price + zone_size, pool.price - zone_size))
        
        for ob in order_blocks:
            if ob.type == OrderBlockType.BULLISH and ob.strength >= 1.2 and not ob.mitigated:
                discount_zones.append((ob.high, ob.low))
        
        # Merge overlapping zones
        premium_zones = self._merge_overlapping_zones(premium_zones)
        discount_zones = self._merge_overlapping_zones(discount_zones)
        
        return premium_zones, discount_zones

    def _merge_overlapping_zones(self, zones: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Merge overlapping price zones."""
        if not zones:
            return []
            
        # Sort by lower bound
        sorted_zones = sorted(zones, key=lambda z: z[1])
        
        merged: List[Tuple[float, float]] = [sorted_zones[0]]
        
        for high, low in sorted_zones[1:]:
            prev_high, prev_low = merged[-1]
            
            # Check if zones overlap
            if low <= prev_high:
                # Merge zones
                merged[-1] = (max(high, prev_high), min(low, prev_low))
            else:
                # Add as separate zone
                merged.append((high, low))
                
        return merged

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _dedup_pools(self, pools: List[LiquidityPool]) -> List[LiquidityPool]:
        """Merge pools within 0.1 pip distance to avoid duplicates."""
        merged: list[LiquidityPool] = []
        for p in sorted(pools, key=lambda x: x.price):
            if not merged or abs(p.price - merged[-1].price) > 0.00001:
                merged.append(p)
        return merged


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # Create sample data
    import pandas as pd
    
    # Generate sample OHLCV data
    np.random.seed(42)
    n = 100
    dates = pd.date_range('2023-01-01', periods=n, freq='15min')
    
    # Create a trending price series with some volatility
    close = np.cumsum(np.random.normal(0, 1, n)) + 100
    # Add some mean reversion
    close = close * 0.99 + 100 * 0.01
    
    # Create OHLCV data
    high = close + np.random.uniform(0, 2, n)
    low = close - np.random.uniform(0, 2, n)
    open_price = low + np.random.uniform(0, high - low, n)
    volume = np.random.uniform(100, 1000, n)
    
    # Create DataFrame
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    # Create smaller timeframe data
    df_m5 = df.copy()
    df_m5.index = pd.date_range('2023-01-01', periods=n*3, freq='5min')[:n]
    
    # Create larger timeframe data
    df_h1 = df.iloc[:4].copy()
    
    # Create analyzer
    analyzer = LiquidityAnalyzer(multi_timeframe=True)
    
    # Test multi-timeframe analysis
    results = analyzer.analyze_multi_timeframe({
        TimeFrame.M5: df_m5,
        TimeFrame.M15: df,
        TimeFrame.H1: df_h1
    })
    
    # Print results
    logger.info("\nMulti-timeframe Liquidity Analysis Results:")
    for tf_name, tf_data in results.items():
        logger.info(f"\n{tf_name}:")
        for timeframe, items in tf_data.items():
            if isinstance(items, tuple):
                buy_pools, sell_pools = items
                logger.info(f"  {timeframe}: {len(buy_pools)} buy pools, {len(sell_pools)} sell pools")
            elif isinstance(items, list):
                logger.info(f"  {timeframe}: {len(items)} items")
            else:
                logger.info(f"  {timeframe}: {type(items)}")
    
    # Test premium/discount zones
    premium, discount = analyzer.identify_premium_discount_zones(df)
    print("\nPremium zones:", premium)
    print("Discount zones:", discount)
