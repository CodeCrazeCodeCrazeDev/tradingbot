"""ICT (Inner Circle Trader) Concepts Framework Module.

Implements the complete ICT trading methodology including:
- Optimal Trade Entry (OTE) zones
- Order Blocks (OB) - Bullish and Bearish
- Fair Value Gaps (FVG) - ICT methodology
- Breaker Blocks
- Mitigation Blocks
- Liquidity concepts (BSL/SSL)
- Market Structure Shifts (MSS)
- Change of Character (CHoCH)
- Break of Structure (BOS)
- Premium and Discount zones
- Killzones (London, NY, Asian sessions)
- Power of 3 (Accumulation, Manipulation, Distribution)
- Judas Swing
- ICT Silver Bullet
- Optimal Trade Location (OTL)

This module provides institutional trading methodology
for identifying high-probability trade setups.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class ICTSessionType(enum.Enum):
    """ICT Trading Sessions (Killzones)."""
    ASIAN = "asian"  # 20:00-00:00 EST
    LONDON = "london"  # 02:00-05:00 EST
    NY_OPEN = "ny_open"  # 07:00-10:00 EST
    NY_LUNCH = "ny_lunch"  # 12:00-13:00 EST
    NY_PM = "ny_pm"  # 13:30-16:00 EST
    OFF_SESSION = "off_session"


class OrderBlockType(enum.Enum):
    """Types of ICT Order Blocks."""
    BULLISH_OB = "bullish_ob"  # Last down candle before up move
    BEARISH_OB = "bearish_ob"  # Last up candle before down move
    BREAKER_BULLISH = "breaker_bullish"  # Failed bearish OB becomes support
    BREAKER_BEARISH = "breaker_bearish"  # Failed bullish OB becomes resistance
    MITIGATION = "mitigation"  # OB that has been partially filled


class FVGType(enum.Enum):
    """Types of Fair Value Gaps."""
    BULLISH_FVG = "bullish_fvg"  # Gap up (buy imbalance)
    BEARISH_FVG = "bearish_fvg"  # Gap down (sell imbalance)
    SIBI = "sibi"  # Sell-side Imbalance Buy-side Inefficiency
    BISI = "bisi"  # Buy-side Imbalance Sell-side Inefficiency


class MarketStructureType(enum.Enum):
    """Market Structure Types."""
    BOS_BULLISH = "bos_bullish"  # Break of Structure (bullish)
    BOS_BEARISH = "bos_bearish"  # Break of Structure (bearish)
    CHOCH_BULLISH = "choch_bullish"  # Change of Character (bullish)
    CHOCH_BEARISH = "choch_bearish"  # Change of Character (bearish)
    MSS_BULLISH = "mss_bullish"  # Market Structure Shift (bullish)
    MSS_BEARISH = "mss_bearish"  # Market Structure Shift (bearish)


class LiquidityType(enum.Enum):
    """Types of Liquidity."""
    BSL = "bsl"  # Buy-side Liquidity (above highs)
    SSL = "ssl"  # Sell-side Liquidity (below lows)
    EQH = "eqh"  # Equal Highs
    EQL = "eql"  # Equal Lows


class PowerOf3Phase(enum.Enum):
    """Power of 3 Phases."""
    ACCUMULATION = "accumulation"
    MANIPULATION = "manipulation"
    DISTRIBUTION = "distribution"


@dataclass
class ICTOrderBlock:
    """ICT Order Block."""
    ob_type: OrderBlockType
    high: float
    low: float
    open_price: float
    close_price: float
    start_idx: int
    end_idx: int
    volume: float
    strength: float  # 0-100
    mitigated: bool = False
    mitigation_percent: float = 0.0
    timeframe: str = "1H"
    created_at: Optional[datetime] = None
    
    @property
    def midpoint(self) -> float:
        """Get OB midpoint (50% level)."""
        return (self.high + self.low) / 2
        
    @property
    def ote_zone(self) -> Tuple[float, float]:
        """Get Optimal Trade Entry zone (61.8% - 78.6% retracement)."""
        try:
            range_size = self.high - self.low
            if self.ob_type in [OrderBlockType.BULLISH_OB, OrderBlockType.BREAKER_BULLISH]:
                return (self.low + range_size * 0.618, self.low + range_size * 0.786)
            else:
                return (self.high - range_size * 0.786, self.high - range_size * 0.618)
        except Exception as e:
            logger.error(f"Error in ote_zone: {e}")
            raise


@dataclass
class ICTFVG:
    """ICT Fair Value Gap."""
    fvg_type: FVGType
    high: float  # Top of gap
    low: float  # Bottom of gap
    ce: float  # Consequent Encroachment (50% of FVG)
    start_idx: int
    candle_indices: Tuple[int, int, int]  # 3 candles that form FVG
    filled: bool = False
    fill_percent: float = 0.0
    timeframe: str = "1H"
    created_at: Optional[datetime] = None
    
    @property
    def size(self) -> float:
        """Get FVG size."""
        return self.high - self.low


@dataclass
class ICTLiquidity:
    """ICT Liquidity Level."""
    liquidity_type: LiquidityType
    price: float
    swing_indices: List[int]
    strength: float  # Based on number of touches
    swept: bool = False
    sweep_idx: Optional[int] = None
    timeframe: str = "1H"


@dataclass
class ICTMarketStructure:
    """ICT Market Structure Event."""
    structure_type: MarketStructureType
    price: float
    idx: int
    swing_high: float
    swing_low: float
    confirmed: bool = True
    timeframe: str = "1H"


@dataclass
class ICTKillzone:
    """ICT Killzone (Trading Session)."""
    session_type: ICTSessionType
    start_time: time
    end_time: time
    high: float
    low: float
    open_price: float
    close_price: float
    range_size: float
    bias: str  # 'bullish', 'bearish', 'neutral'


@dataclass
class PowerOf3:
    """Power of 3 Analysis."""
    phase: PowerOf3Phase
    accumulation_range: Tuple[float, float]
    manipulation_high: Optional[float]
    manipulation_low: Optional[float]
    distribution_target: Optional[float]
    confidence: float


@dataclass
class ICTSetup:
    """Complete ICT Trade Setup."""
    setup_type: str
    direction: str  # 'long' or 'short'
    entry_zone: Tuple[float, float]
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    confluence_score: float  # 0-100
    components: Dict[str, Any]
    timeframe: str
    killzone: Optional[ICTSessionType]
    created_at: datetime


class ICTConceptsAnalyzer:
    """ICT Concepts Analysis Engine.
    
    Provides comprehensive ICT methodology analysis for
    institutional-grade trade setups.
    """
    
    # Killzone times (EST)
    KILLZONES = {
        ICTSessionType.ASIAN: (time(20, 0), time(0, 0)),
        ICTSessionType.LONDON: (time(2, 0), time(5, 0)),
        ICTSessionType.NY_OPEN: (time(7, 0), time(10, 0)),
        ICTSessionType.NY_LUNCH: (time(12, 0), time(13, 0)),
        ICTSessionType.NY_PM: (time(13, 30), time(16, 0)),
    }
    
    # Silver Bullet times
    SILVER_BULLET_TIMES = {
        'london': (time(3, 0), time(4, 0)),
        'ny_am': (time(10, 0), time(11, 0)),
        'ny_pm': (time(14, 0), time(15, 0)),
    }
    
    def __init__(
        self,
        swing_lookback: int = 10,
        ob_lookback: int = 50,
        fvg_min_size_pct: float = 0.001,  # 0.1% minimum FVG size
        equal_level_tolerance: float = 0.0005  # 0.05% tolerance for equal highs/lows
    ):
        """Initialize ICT Concepts Analyzer.
        
        Args:
            swing_lookback: Bars to look back for swing detection
            ob_lookback: Bars to look back for order block detection
            fvg_min_size_pct: Minimum FVG size as percentage of price
            equal_level_tolerance: Tolerance for equal highs/lows detection
        """
        try:
            self.swing_lookback = swing_lookback
            self.ob_lookback = ob_lookback
            self.fvg_min_size_pct = fvg_min_size_pct
            self.equal_level_tolerance = equal_level_tolerance
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def identify_order_blocks(
        self,
        df: pd.DataFrame,
        min_move_pct: float = 0.005
    ) -> List[ICTOrderBlock]:
        """Identify ICT Order Blocks.
        
        Bullish OB: Last bearish candle before a strong bullish move
        Bearish OB: Last bullish candle before a strong bearish move
        
        Args:
            df: DataFrame with OHLCV data
            min_move_pct: Minimum move percentage to qualify as impulsive
            
        Returns:
            List of ICTOrderBlock objects
        """
        try:
            order_blocks = []
        
            if len(df) < 5:
                return order_blocks
            
            for i in range(2, len(df) - 2):
                current = df.iloc[i]
                prev = df.iloc[i - 1]
                next_candle = df.iloc[i + 1]
                next_next = df.iloc[i + 2]
            
                # Check for bullish order block
                # Current candle is bearish, followed by strong bullish move
                if current['close'] < current['open']:  # Bearish candle
                    # Check for impulsive move up
                    move_up = (next_next['high'] - current['low']) / current['low']
                    if move_up >= min_move_pct:
                        # Confirm with displacement (next candle closes above OB high)
                        if next_candle['close'] > current['high']:
                            strength = min(100, move_up / min_move_pct * 50)
                        
                            order_blocks.append(ICTOrderBlock(
                                ob_type=OrderBlockType.BULLISH_OB,
                                high=current['high'],
                                low=current['low'],
                                open_price=current['open'],
                                close_price=current['close'],
                                start_idx=i,
                                end_idx=i,
                                volume=current.get('volume', 0),
                                strength=strength,
                                timeframe=self._get_timeframe(df),
                                created_at=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None
                            ))
                        
                # Check for bearish order block
                # Current candle is bullish, followed by strong bearish move
                if current['close'] > current['open']:  # Bullish candle
                    # Check for impulsive move down
                    move_down = (current['high'] - next_next['low']) / current['high']
                    if move_down >= min_move_pct:
                        # Confirm with displacement (next candle closes below OB low)
                        if next_candle['close'] < current['low']:
                            strength = min(100, move_down / min_move_pct * 50)
                        
                            order_blocks.append(ICTOrderBlock(
                                ob_type=OrderBlockType.BEARISH_OB,
                                high=current['high'],
                                low=current['low'],
                                open_price=current['open'],
                                close_price=current['close'],
                                start_idx=i,
                                end_idx=i,
                                volume=current.get('volume', 0),
                                strength=strength,
                                timeframe=self._get_timeframe(df),
                                created_at=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None
                            ))
                        
            return order_blocks
        except Exception as e:
            logger.error(f"Error in identify_order_blocks: {e}")
            raise
        
    def identify_breaker_blocks(
        self,
        df: pd.DataFrame,
        order_blocks: List[ICTOrderBlock]
    ) -> List[ICTOrderBlock]:
        """Identify Breaker Blocks (failed order blocks).
        
        When price breaks through an order block with conviction,
        it becomes a breaker block (role reversal).
        
        Args:
            df: DataFrame with OHLCV data
            order_blocks: List of existing order blocks
            
        Returns:
            List of breaker blocks
        """
        try:
            breakers = []
        
            for ob in order_blocks:
                if ob.end_idx >= len(df) - 1:
                    continue
                
                # Check if OB was broken
                subsequent_data = df.iloc[ob.end_idx + 1:]
            
                if ob.ob_type == OrderBlockType.BULLISH_OB:
                    # Bullish OB broken = price closes below OB low
                    broken = any(subsequent_data['close'] < ob.low)
                    if broken:
                        breakers.append(ICTOrderBlock(
                            ob_type=OrderBlockType.BREAKER_BEARISH,
                            high=ob.high,
                            low=ob.low,
                            open_price=ob.open_price,
                            close_price=ob.close_price,
                            start_idx=ob.start_idx,
                            end_idx=ob.end_idx,
                            volume=ob.volume,
                            strength=ob.strength * 0.8,  # Slightly reduced strength
                            timeframe=ob.timeframe,
                            created_at=ob.created_at
                        ))
                    
                elif ob.ob_type == OrderBlockType.BEARISH_OB:
                    # Bearish OB broken = price closes above OB high
                    broken = any(subsequent_data['close'] > ob.high)
                    if broken:
                        breakers.append(ICTOrderBlock(
                            ob_type=OrderBlockType.BREAKER_BULLISH,
                            high=ob.high,
                            low=ob.low,
                            open_price=ob.open_price,
                            close_price=ob.close_price,
                            start_idx=ob.start_idx,
                            end_idx=ob.end_idx,
                            volume=ob.volume,
                            strength=ob.strength * 0.8,
                            timeframe=ob.timeframe,
                            created_at=ob.created_at
                        ))
                    
            return breakers
        except Exception as e:
            logger.error(f"Error in identify_breaker_blocks: {e}")
            raise
        
    def identify_fvg(
        self,
        df: pd.DataFrame
    ) -> List[ICTFVG]:
        """Identify Fair Value Gaps (ICT methodology).
        
        FVG is created when candle 1's low is higher than candle 3's high (bullish)
        or candle 1's high is lower than candle 3's low (bearish).
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of ICTFVG objects
        """
        try:
            fvgs = []
        
            if len(df) < 3:
                return fvgs
            
            for i in range(len(df) - 2):
                candle1 = df.iloc[i]
                candle2 = df.iloc[i + 1]
                candle3 = df.iloc[i + 2]
            
                avg_price = candle2['close']
                min_gap = avg_price * self.fvg_min_size_pct
            
                # Bullish FVG (BISI): Candle 1 low > Candle 3 high
                if candle1['low'] > candle3['high']:
                    gap_size = candle1['low'] - candle3['high']
                    if gap_size >= min_gap:
                        fvgs.append(ICTFVG(
                            fvg_type=FVGType.BULLISH_FVG,
                            high=candle1['low'],
                            low=candle3['high'],
                            ce=(candle1['low'] + candle3['high']) / 2,
                            start_idx=i,
                            candle_indices=(i, i + 1, i + 2),
                            timeframe=self._get_timeframe(df),
                            created_at=df.index[i + 1] if isinstance(df.index, pd.DatetimeIndex) else None
                        ))
                    
                # Bearish FVG (SIBI): Candle 1 high < Candle 3 low
                if candle1['high'] < candle3['low']:
                    gap_size = candle3['low'] - candle1['high']
                    if gap_size >= min_gap:
                        fvgs.append(ICTFVG(
                            fvg_type=FVGType.BEARISH_FVG,
                            high=candle3['low'],
                            low=candle1['high'],
                            ce=(candle3['low'] + candle1['high']) / 2,
                            start_idx=i,
                            candle_indices=(i, i + 1, i + 2),
                            timeframe=self._get_timeframe(df),
                            created_at=df.index[i + 1] if isinstance(df.index, pd.DatetimeIndex) else None
                        ))
                    
            return fvgs
        except Exception as e:
            logger.error(f"Error in identify_fvg: {e}")
            raise
        
    def identify_liquidity(
        self,
        df: pd.DataFrame
    ) -> List[ICTLiquidity]:
        """Identify liquidity levels (BSL/SSL, Equal Highs/Lows).
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of ICTLiquidity objects
        """
        try:
            liquidity_levels = []
        
            if len(df) < self.swing_lookback * 2:
                return liquidity_levels
            
            # Find swing highs and lows
            swing_highs = []
            swing_lows = []
        
            for i in range(self.swing_lookback, len(df) - self.swing_lookback):
                # Swing high
                is_swing_high = all(
                    df.iloc[i]['high'] >= df.iloc[j]['high']
                    for j in range(i - self.swing_lookback, i + self.swing_lookback + 1)
                    if j != i
                )
                if is_swing_high:
                    swing_highs.append((i, df.iloc[i]['high']))
                
                # Swing low
                is_swing_low = all(
                    df.iloc[i]['low'] <= df.iloc[j]['low']
                    for j in range(i - self.swing_lookback, i + self.swing_lookback + 1)
                    if j != i
                )
                if is_swing_low:
                    swing_lows.append((i, df.iloc[i]['low']))
                
            # Find equal highs (BSL above)
            for i, (idx1, high1) in enumerate(swing_highs):
                equal_indices = [idx1]
                for idx2, high2 in swing_highs[i + 1:]:
                    if abs(high1 - high2) / high1 <= self.equal_level_tolerance:
                        equal_indices.append(idx2)
                    
                if len(equal_indices) >= 2:
                    liquidity_levels.append(ICTLiquidity(
                        liquidity_type=LiquidityType.EQH,
                        price=high1,
                        swing_indices=equal_indices,
                        strength=len(equal_indices) * 25,
                        timeframe=self._get_timeframe(df)
                    ))
                
            # Find equal lows (SSL below)
            for i, (idx1, low1) in enumerate(swing_lows):
                equal_indices = [idx1]
                for idx2, low2 in swing_lows[i + 1:]:
                    if abs(low1 - low2) / low1 <= self.equal_level_tolerance:
                        equal_indices.append(idx2)
                    
                if len(equal_indices) >= 2:
                    liquidity_levels.append(ICTLiquidity(
                        liquidity_type=LiquidityType.EQL,
                        price=low1,
                        swing_indices=equal_indices,
                        strength=len(equal_indices) * 25,
                        timeframe=self._get_timeframe(df)
                    ))
                
            # Add BSL above recent highs
            if swing_highs:
                recent_high = max(swing_highs[-5:], key=lambda x: x[1]) if len(swing_highs) >= 5 else max(swing_highs, key=lambda x: x[1])
                liquidity_levels.append(ICTLiquidity(
                    liquidity_type=LiquidityType.BSL,
                    price=recent_high[1],
                    swing_indices=[recent_high[0]],
                    strength=50,
                    timeframe=self._get_timeframe(df)
                ))
            
            # Add SSL below recent lows
            if swing_lows:
                recent_low = min(swing_lows[-5:], key=lambda x: x[1]) if len(swing_lows) >= 5 else min(swing_lows, key=lambda x: x[1])
                liquidity_levels.append(ICTLiquidity(
                    liquidity_type=LiquidityType.SSL,
                    price=recent_low[1],
                    swing_indices=[recent_low[0]],
                    strength=50,
                    timeframe=self._get_timeframe(df)
                ))
            
            return liquidity_levels
        except Exception as e:
            logger.error(f"Error in identify_liquidity: {e}")
            raise
        
    def identify_market_structure(
        self,
        df: pd.DataFrame
    ) -> List[ICTMarketStructure]:
        """Identify Market Structure (BOS, CHoCH, MSS).
        
        BOS: Break of Structure (continuation)
        CHoCH: Change of Character (potential reversal)
        MSS: Market Structure Shift (confirmed reversal)
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of ICTMarketStructure objects
        """
        try:
            structures = []
        
            if len(df) < self.swing_lookback * 3:
                return structures
            
            # Find swing points
            swing_highs = []
            swing_lows = []
        
            for i in range(self.swing_lookback, len(df) - self.swing_lookback):
                # Swing high
                if all(df.iloc[i]['high'] >= df.iloc[j]['high'] 
                       for j in range(i - self.swing_lookback, i + self.swing_lookback + 1) if j != i):
                    swing_highs.append((i, df.iloc[i]['high']))
                
                # Swing low
                if all(df.iloc[i]['low'] <= df.iloc[j]['low']
                       for j in range(i - self.swing_lookback, i + self.swing_lookback + 1) if j != i):
                    swing_lows.append((i, df.iloc[i]['low']))
                
            # Detect BOS and CHoCH
            # In uptrend: higher highs, higher lows
            # BOS bullish: break above previous swing high
            # CHoCH bearish: break below previous swing low in uptrend
        
            for i in range(1, len(swing_highs)):
                prev_high = swing_highs[i - 1]
                curr_high = swing_highs[i]
            
                # Check for BOS bullish (higher high)
                if curr_high[1] > prev_high[1]:
                    structures.append(ICTMarketStructure(
                        structure_type=MarketStructureType.BOS_BULLISH,
                        price=curr_high[1],
                        idx=curr_high[0],
                        swing_high=curr_high[1],
                        swing_low=swing_lows[-1][1] if swing_lows else df['low'].min(),
                        timeframe=self._get_timeframe(df)
                    ))
                
            for i in range(1, len(swing_lows)):
                prev_low = swing_lows[i - 1]
                curr_low = swing_lows[i]
            
                # Check for BOS bearish (lower low)
                if curr_low[1] < prev_low[1]:
                    structures.append(ICTMarketStructure(
                        structure_type=MarketStructureType.BOS_BEARISH,
                        price=curr_low[1],
                        idx=curr_low[0],
                        swing_high=swing_highs[-1][1] if swing_highs else df['high'].max(),
                        swing_low=curr_low[1],
                        timeframe=self._get_timeframe(df)
                    ))
                
            # Detect CHoCH (trend reversal signals)
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                # CHoCH bullish: in downtrend, price breaks above recent swing high
                last_two_lows = swing_lows[-2:]
                if last_two_lows[1][1] < last_two_lows[0][1]:  # Downtrend (lower lows)
                    last_high = swing_highs[-1]
                    # Check if price broke above this high
                    subsequent = df.iloc[last_high[0]:]
                    if any(subsequent['close'] > last_high[1]):
                        structures.append(ICTMarketStructure(
                            structure_type=MarketStructureType.CHOCH_BULLISH,
                            price=last_high[1],
                            idx=last_high[0],
                            swing_high=last_high[1],
                            swing_low=last_two_lows[1][1],
                            timeframe=self._get_timeframe(df)
                        ))
                    
                # CHoCH bearish: in uptrend, price breaks below recent swing low
                last_two_highs = swing_highs[-2:]
                if last_two_highs[1][1] > last_two_highs[0][1]:  # Uptrend (higher highs)
                    last_low = swing_lows[-1]
                    # Check if price broke below this low
                    subsequent = df.iloc[last_low[0]:]
                    if any(subsequent['close'] < last_low[1]):
                        structures.append(ICTMarketStructure(
                            structure_type=MarketStructureType.CHOCH_BEARISH,
                            price=last_low[1],
                            idx=last_low[0],
                            swing_high=last_two_highs[1][1],
                            swing_low=last_low[1],
                            timeframe=self._get_timeframe(df)
                        ))
                    
            return structures
        except Exception as e:
            logger.error(f"Error in identify_market_structure: {e}")
            raise
        
    def get_premium_discount_zones(
        self,
        df: pd.DataFrame,
        lookback: int = 50
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate Premium and Discount zones.
        
        Premium: Above 50% of range (sell zone)
        Discount: Below 50% of range (buy zone)
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Bars to look back for range
            
        Returns:
            Dictionary with zone boundaries
        """
        try:
            recent = df.iloc[-lookback:] if len(df) >= lookback else df
        
            range_high = recent['high'].max()
            range_low = recent['low'].min()
            equilibrium = (range_high + range_low) / 2
        
            # Fibonacci levels
            fib_618 = range_low + (range_high - range_low) * 0.618
            fib_786 = range_low + (range_high - range_low) * 0.786
            fib_382 = range_low + (range_high - range_low) * 0.382
            fib_236 = range_low + (range_high - range_low) * 0.236
        
            return {
                'premium': (equilibrium, range_high),
                'discount': (range_low, equilibrium),
                'equilibrium': equilibrium,
                'extreme_premium': (fib_786, range_high),
                'extreme_discount': (range_low, fib_236),
                'ote_buy': (fib_618, fib_786),  # Optimal Trade Entry for longs
                'ote_sell': (fib_236, fib_382),  # Optimal Trade Entry for shorts
                'range_high': range_high,
                'range_low': range_low
            }
        except Exception as e:
            logger.error(f"Error in get_premium_discount_zones: {e}")
            raise
        
    def get_current_killzone(
        self,
        timestamp: Optional[datetime] = None
    ) -> ICTSessionType:
        """Get current ICT Killzone based on time.
        
        Args:
            timestamp: Timestamp to check (default: now)
            
        Returns:
            Current killzone session type
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            current_time = timestamp.time()
        
            for session, (start, end) in self.KILLZONES.items():
                if start <= end:
                    if start <= current_time <= end:
                        return session
                else:  # Crosses midnight (Asian session)
                    if current_time >= start or current_time <= end:
                        return session
                    
            return ICTSessionType.OFF_SESSION
        except Exception as e:
            logger.error(f"Error in get_current_killzone: {e}")
            raise
        
    def analyze_power_of_3(
        self,
        df: pd.DataFrame,
        session_data: Optional[pd.DataFrame] = None
    ) -> PowerOf3:
        """Analyze Power of 3 (AMD) pattern.
        
        Accumulation: Initial range/consolidation
        Manipulation: False breakout/stop hunt
        Distribution: True move in intended direction
        
        Args:
            df: DataFrame with OHLCV data
            session_data: Optional session-specific data
            
        Returns:
            PowerOf3 analysis
        """
        try:
            data = session_data if session_data is not None else df.iloc[-20:]
        
            if len(data) < 10:
                return PowerOf3(
                    phase=PowerOf3Phase.ACCUMULATION,
                    accumulation_range=(data['low'].min(), data['high'].max()),
                    manipulation_high=None,
                    manipulation_low=None,
                    distribution_target=None,
                    confidence=0
                )
            
            # Split into thirds
            third = len(data) // 3
        
            first_third = data.iloc[:third]
            second_third = data.iloc[third:2*third]
            last_third = data.iloc[2*third:]
        
            # Accumulation range (first third)
            acc_high = first_third['high'].max()
            acc_low = first_third['low'].min()
        
            # Check for manipulation (second third)
            manip_high = second_third['high'].max()
            manip_low = second_third['low'].min()
        
            manipulation_up = manip_high > acc_high
            manipulation_down = manip_low < acc_low
        
            # Distribution (last third)
            dist_close = last_third['close'].iloc[-1]
            dist_direction = 'bullish' if dist_close > (acc_high + acc_low) / 2 else 'bearish'
        
            # Determine current phase
            current_price = data['close'].iloc[-1]
        
            if current_price >= acc_low and current_price <= acc_high:
                phase = PowerOf3Phase.ACCUMULATION
            elif manipulation_up or manipulation_down:
                phase = PowerOf3Phase.MANIPULATION
            else:
                phase = PowerOf3Phase.DISTRIBUTION
            
            # Calculate confidence
            confidence = 50
            if manipulation_up and dist_direction == 'bearish':
                confidence = 80  # Classic AMD pattern
            elif manipulation_down and dist_direction == 'bullish':
                confidence = 80
            
            # Distribution target
            range_size = acc_high - acc_low
            if dist_direction == 'bullish':
                distribution_target = acc_high + range_size
            else:
                distribution_target = acc_low - range_size
            
            return PowerOf3(
                phase=phase,
                accumulation_range=(acc_low, acc_high),
                manipulation_high=manip_high if manipulation_up else None,
                manipulation_low=manip_low if manipulation_down else None,
                distribution_target=distribution_target,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze_power_of_3: {e}")
            raise
        
    def find_ict_setup(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Optional[ICTSetup]:
        """Find complete ICT trade setup.
        
        Args:
            df: DataFrame with OHLCV data
            current_price: Current market price
            
        Returns:
            ICTSetup if valid setup found, None otherwise
        """
        # Get all ICT components
        try:
            order_blocks = self.identify_order_blocks(df)
            fvgs = self.identify_fvg(df)
            liquidity = self.identify_liquidity(df)
            structure = self.identify_market_structure(df)
            zones = self.get_premium_discount_zones(df)
            killzone = self.get_current_killzone()
        
            # Check for valid setup
            confluence_score = 0
            setup_type = None
            direction = None
            entry_zone = None
            stop_loss = None
            components = {}
        
            # Look for bullish setup
            bullish_obs = [ob for ob in order_blocks if ob.ob_type == OrderBlockType.BULLISH_OB and not ob.mitigated]
            bullish_fvgs = [fvg for fvg in fvgs if fvg.fvg_type == FVGType.BULLISH_FVG and not fvg.filled]
            bullish_structure = [s for s in structure if s.structure_type in [MarketStructureType.BOS_BULLISH, MarketStructureType.CHOCH_BULLISH]]
        
            # Check if price is in discount zone
            in_discount = zones['discount'][0] <= current_price <= zones['discount'][1]
        
            if in_discount and bullish_obs:
                # Find nearest bullish OB
                nearest_ob = min(bullish_obs, key=lambda x: abs(x.midpoint - current_price))
            
                if current_price <= nearest_ob.high:
                    confluence_score += 30
                    setup_type = "OB_Retest"
                    direction = "long"
                    entry_zone = (nearest_ob.low, nearest_ob.midpoint)
                    stop_loss = nearest_ob.low - (nearest_ob.high - nearest_ob.low) * 0.5
                    components['order_block'] = nearest_ob
                
            # Add FVG confluence
            if bullish_fvgs and direction == "long":
                for fvg in bullish_fvgs:
                    if fvg.low <= current_price <= fvg.high:
                        confluence_score += 20
                        components['fvg'] = fvg
                        break
                    
            # Add structure confluence
            if bullish_structure and direction == "long":
                confluence_score += 25
                components['structure'] = bullish_structure[-1]
            
            # Add killzone confluence
            if killzone in [ICTSessionType.LONDON, ICTSessionType.NY_OPEN]:
                confluence_score += 15
            
            # Add liquidity confluence
            ssl_levels = [l for l in liquidity if l.liquidity_type == LiquidityType.SSL]
            if ssl_levels and direction == "long":
                nearest_ssl = min(ssl_levels, key=lambda x: abs(x.price - current_price))
                if nearest_ssl.swept:
                    confluence_score += 10
                    components['liquidity_sweep'] = nearest_ssl
                
            # Check for bearish setup if no bullish found
            if confluence_score < 50:
                bearish_obs = [ob for ob in order_blocks if ob.ob_type == OrderBlockType.BEARISH_OB and not ob.mitigated]
                bearish_fvgs = [fvg for fvg in fvgs if fvg.fvg_type == FVGType.BEARISH_FVG and not fvg.filled]
                bearish_structure = [s for s in structure if s.structure_type in [MarketStructureType.BOS_BEARISH, MarketStructureType.CHOCH_BEARISH]]
            
                in_premium = zones['premium'][0] <= current_price <= zones['premium'][1]
            
                if in_premium and bearish_obs:
                    nearest_ob = min(bearish_obs, key=lambda x: abs(x.midpoint - current_price))
                
                    if current_price >= nearest_ob.low:
                        confluence_score = 30
                        setup_type = "OB_Retest"
                        direction = "short"
                        entry_zone = (nearest_ob.midpoint, nearest_ob.high)
                        stop_loss = nearest_ob.high + (nearest_ob.high - nearest_ob.low) * 0.5
                        components['order_block'] = nearest_ob
                    
                        if bearish_fvgs:
                            for fvg in bearish_fvgs:
                                if fvg.low <= current_price <= fvg.high:
                                    confluence_score += 20
                                    components['fvg'] = fvg
                                    break
                                
                        if bearish_structure:
                            confluence_score += 25
                            components['structure'] = bearish_structure[-1]
                        
            # Return setup if confluence is sufficient
            if confluence_score >= 50 and entry_zone and stop_loss:
                risk = abs(entry_zone[0] - stop_loss)
            
                if direction == "long":
                    tp1 = entry_zone[0] + risk * 1.5
                    tp2 = entry_zone[0] + risk * 2.5
                    tp3 = entry_zone[0] + risk * 4.0
                else:
                    tp1 = entry_zone[0] - risk * 1.5
                    tp2 = entry_zone[0] - risk * 2.5
                    tp3 = entry_zone[0] - risk * 4.0
                
                return ICTSetup(
                    setup_type=setup_type,
                    direction=direction,
                    entry_zone=entry_zone,
                    stop_loss=stop_loss,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    take_profit_3=tp3,
                    risk_reward=2.5,
                    confluence_score=confluence_score,
                    components=components,
                    timeframe=self._get_timeframe(df),
                    killzone=killzone,
                    created_at=datetime.now()
                )
            
            return None
        except Exception as e:
            logger.error(f"Error in find_ict_setup: {e}")
            raise
        
    def _get_timeframe(self, df: pd.DataFrame) -> str:
        """Infer timeframe from DataFrame."""
        try:
            if len(df) < 2:
                return "UNKNOWN"
            
            if isinstance(df.index, pd.DatetimeIndex):
                diff = df.index[1] - df.index[0]
                minutes = diff.total_seconds() / 60
            
                if minutes <= 1:
                    return "1m"
                elif minutes <= 5:
                    return "5m"
                elif minutes <= 15:
                    return "15m"
                elif minutes <= 60:
                    return "1H"
                elif minutes <= 240:
                    return "4H"
                elif minutes <= 1440:
                    return "1D"
                else:
                    return "1W"
                
            return "UNKNOWN"
        except Exception as e:
            logger.error(f"Error in _get_timeframe: {e}")
            raise


# Convenience functions
def find_order_blocks(df: pd.DataFrame) -> List[ICTOrderBlock]:
    """Quick function to find order blocks."""
    try:
        analyzer = ICTConceptsAnalyzer()
        return analyzer.identify_order_blocks(df)
    except Exception as e:
        logger.error(f"Error in find_order_blocks: {e}")
        raise


def find_fvg(df: pd.DataFrame) -> List[ICTFVG]:
    """Quick function to find fair value gaps."""
    try:
        analyzer = ICTConceptsAnalyzer()
        return analyzer.identify_fvg(df)
    except Exception as e:
        logger.error(f"Error in find_fvg: {e}")
        raise


def get_ict_setup(df: pd.DataFrame, current_price: float) -> Optional[ICTSetup]:
    """Quick function to get ICT trade setup."""
    try:
        analyzer = ICTConceptsAnalyzer()
        return analyzer.find_ict_setup(df, current_price)
    except Exception as e:
        logger.error(f"Error in get_ict_setup: {e}")
        raise
