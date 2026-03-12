"""
Skill #5: Market Profile Analyzer
=================================

Time-Price-Opportunity (TPO) analysis for understanding market structure.
Identifies value areas, POC, and market balance/imbalance.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MarketProfileType(Enum):
    """Type of market profile day."""
    NORMAL = "normal"  # 70% of days
    TREND = "trend"  # Strong directional move
    DOUBLE_DISTRIBUTION = "double_distribution"  # Two value areas
    NON_TREND = "non_trend"  # Narrow range
    NEUTRAL = "neutral"  # Balanced
    P_SHAPE = "p_shape"  # Short covering rally
    B_SHAPE = "b_shape"  # Long liquidation


class MarketState(Enum):
    """Current market state based on profile."""
    BALANCE = "balance"
    IMBALANCE_UP = "imbalance_up"
    IMBALANCE_DOWN = "imbalance_down"
    BREAKOUT = "breakout"
    ROTATION = "rotation"


@dataclass
class TPOLevel:
    """Time-Price-Opportunity at a price level."""
    price: float
    tpo_count: int
    tpo_letters: List[str]
    is_poc: bool = False
    is_value_area: bool = False


@dataclass
class ValueArea:
    """Value Area (70% of volume/TPO)."""
    high: float  # VAH
    low: float  # VAL
    poc: float  # Point of Control
    range_size: float
    value_area_percentage: float


@dataclass
class InitialBalance:
    """Initial Balance (first hour of trading)."""
    high: float
    low: float
    range_size: float
    extension_up: float  # IB high + range
    extension_down: float  # IB low - range


@dataclass
class SinglePrint:
    """Single print (low volume area)."""
    price_start: float
    price_end: float
    timestamp: datetime
    is_buying: bool


@dataclass
class MarketProfileResult:
    """Complete market profile analysis."""
    tpo_levels: List[TPOLevel]
    value_area: ValueArea
    initial_balance: InitialBalance
    profile_type: MarketProfileType
    market_state: MarketState
    single_prints: List[SinglePrint]
    poor_highs: List[float]
    poor_lows: List[float]
    excess_high: Optional[float]
    excess_low: Optional[float]
    open_type: str  # 'open_drive', 'open_test_drive', 'open_rejection_reverse', 'open_auction'
    trading_recommendation: str
    confidence: float


class MarketProfileAnalyzer:
    """
    Advanced Market Profile (TPO) Analysis System.
    
    Analyzes market structure using time-price-opportunity concepts.
    """
    
    TPO_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tick_size = self.config.get('tick_size', 0.0001)
        self.tpo_period_minutes = self.config.get('tpo_period_minutes', 30)
        self.value_area_percentage = self.config.get('value_area_percentage', 0.70)
        self.ib_periods = self.config.get('ib_periods', 2)  # First 2 periods = 1 hour
        
        logger.info("MarketProfileAnalyzer initialized")
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        timeframe_minutes: int = 30
    ) -> MarketProfileResult:
        """
        Perform complete market profile analysis.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            volumes: Array of volumes
            timestamps: List of timestamps
            timeframe_minutes: Minutes per bar
            
        Returns:
            MarketProfileResult with complete analysis
        """
        # Build TPO profile
        tpo_levels = self._build_tpo_profile(highs, lows, timestamps, timeframe_minutes)
        
        # Calculate value area
        value_area = self._calculate_value_area(tpo_levels)
        
        # Calculate initial balance
        initial_balance = self._calculate_initial_balance(
            highs, lows, timestamps, timeframe_minutes
        )
        
        # Identify profile type
        profile_type = self._identify_profile_type(
            tpo_levels, value_area, initial_balance, highs, lows
        )
        
        # Determine market state
        market_state = self._determine_market_state(
            closes[-1], value_area, initial_balance
        )
        
        # Find single prints
        single_prints = self._find_single_prints(tpo_levels)
        
        # Find poor highs/lows
        poor_highs = self._find_poor_highs(tpo_levels, highs)
        poor_lows = self._find_poor_lows(tpo_levels, lows)
        
        # Find excess
        excess_high = self._find_excess(tpo_levels, is_high=True)
        excess_low = self._find_excess(tpo_levels, is_high=False)
        
        # Determine open type
        open_type = self._determine_open_type(
            highs, lows, closes, value_area, initial_balance
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            closes[-1], value_area, initial_balance, market_state, profile_type
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            tpo_levels, value_area, profile_type
        )
        
        return MarketProfileResult(
            tpo_levels=tpo_levels,
            value_area=value_area,
            initial_balance=initial_balance,
            profile_type=profile_type,
            market_state=market_state,
            single_prints=single_prints,
            poor_highs=poor_highs,
            poor_lows=poor_lows,
            excess_high=excess_high,
            excess_low=excess_low,
            open_type=open_type,
            trading_recommendation=recommendation,
            confidence=confidence
        )
    
    def _build_tpo_profile(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        timestamps: List[datetime],
        timeframe_minutes: int
    ) -> List[TPOLevel]:
        """Build TPO profile from price data."""
        # Determine price levels
        price_min = np.min(lows)
        price_max = np.max(highs)
        
        # Calculate tick size based on price
        tick_size = self._calculate_tick_size(price_min)
        
        # Create price levels
        num_levels = int((price_max - price_min) / tick_size) + 1
        price_levels = {
            round(price_min + i * tick_size, 6): []
            for i in range(num_levels)
        }
        
        # Assign TPO letters to each period
        for i, (high, low) in enumerate(zip(highs, lows)):
            letter = self.TPO_LETTERS[i % len(self.TPO_LETTERS)]
            
            # Mark all price levels touched in this period
            for price in price_levels.keys():
                if low <= price <= high:
                    price_levels[price].append(letter)
        
        # Convert to TPOLevel objects
        tpo_levels = []
        for price, letters in sorted(price_levels.items()):
            if letters:  # Only include levels with TPOs
                tpo_levels.append(TPOLevel(
                    price=price,
                    tpo_count=len(letters),
                    tpo_letters=letters
                ))
        
        return tpo_levels
    
    def _calculate_tick_size(self, price: float) -> float:
        """Calculate appropriate tick size based on price."""
        if price < 1:
            return 0.0001
        elif price < 10:
            return 0.001
        elif price < 100:
            return 0.01
        elif price < 1000:
            return 0.1
        else:
            return 1.0
    
    def _calculate_value_area(self, tpo_levels: List[TPOLevel]) -> ValueArea:
        """Calculate Value Area (70% of TPOs)."""
        if not tpo_levels:
            return ValueArea(
                high=0, low=0, poc=0, range_size=0, value_area_percentage=0
            )
        
        # Find POC (Point of Control) - level with most TPOs
        poc_level = max(tpo_levels, key=lambda x: x.tpo_count)
        poc_level.is_poc = True
        poc = poc_level.price
        
        # Calculate total TPOs
        total_tpos = sum(level.tpo_count for level in tpo_levels)
        target_tpos = int(total_tpos * self.value_area_percentage)
        
        # Expand from POC to find value area
        poc_index = next(
            i for i, level in enumerate(tpo_levels)
            if level.price == poc
        )
        
        va_tpos = poc_level.tpo_count
        upper_index = poc_index
        lower_index = poc_index
        
        while va_tpos < target_tpos:
            # Check which direction to expand
            upper_tpos = 0
            lower_tpos = 0
            
            if upper_index + 1 < len(tpo_levels):
                upper_tpos = tpo_levels[upper_index + 1].tpo_count
            
            if lower_index - 1 >= 0:
                lower_tpos = tpo_levels[lower_index - 1].tpo_count
            
            if upper_tpos == 0 and lower_tpos == 0:
                break
            
            if upper_tpos >= lower_tpos:
                upper_index += 1
                va_tpos += upper_tpos
            else:
                lower_index -= 1
                va_tpos += lower_tpos
        
        # Mark value area levels
        for i in range(lower_index, upper_index + 1):
            tpo_levels[i].is_value_area = True
        
        vah = tpo_levels[upper_index].price
        val = tpo_levels[lower_index].price
        
        return ValueArea(
            high=vah,
            low=val,
            poc=poc,
            range_size=vah - val,
            value_area_percentage=va_tpos / total_tpos if total_tpos > 0 else 0
        )
    
    def _calculate_initial_balance(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        timestamps: List[datetime],
        timeframe_minutes: int
    ) -> InitialBalance:
        """Calculate Initial Balance (first hour of trading)."""
        # Number of periods in first hour
        periods_per_hour = 60 // timeframe_minutes
        ib_periods = min(periods_per_hour, len(highs))
        
        ib_high = np.max(highs[:ib_periods])
        ib_low = np.min(lows[:ib_periods])
        ib_range = ib_high - ib_low
        
        return InitialBalance(
            high=ib_high,
            low=ib_low,
            range_size=ib_range,
            extension_up=ib_high + ib_range,
            extension_down=ib_low - ib_range
        )
    
    def _identify_profile_type(
        self,
        tpo_levels: List[TPOLevel],
        value_area: ValueArea,
        initial_balance: InitialBalance,
        highs: np.ndarray,
        lows: np.ndarray
    ) -> MarketProfileType:
        """Identify the type of market profile day."""
        if not tpo_levels:
            return MarketProfileType.NORMAL
        
        day_range = np.max(highs) - np.min(lows)
        ib_range = initial_balance.range_size
        
        # Trend day: Range extends significantly beyond IB
        if day_range > ib_range * 2:
            return MarketProfileType.TREND
        
        # Check for double distribution
        tpo_counts = [level.tpo_count for level in tpo_levels]
        peaks = self._find_peaks(tpo_counts)
        if len(peaks) >= 2:
            return MarketProfileType.DOUBLE_DISTRIBUTION
        
        # Non-trend: Narrow range
        if day_range < ib_range * 1.2:
            return MarketProfileType.NON_TREND
        
        # P-shape: Short covering (fat top, thin bottom)
        upper_tpos = sum(
            level.tpo_count for level in tpo_levels
            if level.price > value_area.poc
        )
        lower_tpos = sum(
            level.tpo_count for level in tpo_levels
            if level.price < value_area.poc
        )
        
        if upper_tpos > lower_tpos * 1.5:
            return MarketProfileType.P_SHAPE
        
        # B-shape: Long liquidation (fat bottom, thin top)
        if lower_tpos > upper_tpos * 1.5:
            return MarketProfileType.B_SHAPE
        
        return MarketProfileType.NORMAL
    
    def _find_peaks(self, values: List[int]) -> List[int]:
        """Find peaks in a list of values."""
        peaks = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i - 1] and values[i] > values[i + 1]:
                peaks.append(i)
        return peaks
    
    def _determine_market_state(
        self,
        current_price: float,
        value_area: ValueArea,
        initial_balance: InitialBalance
    ) -> MarketState:
        """Determine current market state."""
        # Price relative to value area
        if value_area.low <= current_price <= value_area.high:
            return MarketState.BALANCE
        
        # Price above value area
        if current_price > value_area.high:
            if current_price > initial_balance.extension_up:
                return MarketState.BREAKOUT
            return MarketState.IMBALANCE_UP
        
        # Price below value area
        if current_price < value_area.low:
            if current_price < initial_balance.extension_down:
                return MarketState.BREAKOUT
            return MarketState.IMBALANCE_DOWN
        
        return MarketState.ROTATION
    
    def _find_single_prints(self, tpo_levels: List[TPOLevel]) -> List[SinglePrint]:
        """Find single print areas (low volume)."""
        single_prints = []
        
        i = 0
        while i < len(tpo_levels):
            if tpo_levels[i].tpo_count == 1:
                start_price = tpo_levels[i].price
                end_price = start_price
                
                # Find extent of single print area
                while i < len(tpo_levels) and tpo_levels[i].tpo_count <= 2:
                    end_price = tpo_levels[i].price
                    i += 1
                
                if end_price != start_price:
                    single_prints.append(SinglePrint(
                        price_start=start_price,
                        price_end=end_price,
                        timestamp=datetime.now(),
                        is_buying=end_price > start_price
                    ))
            else:
                i += 1
        
        return single_prints
    
    def _find_poor_highs(
        self,
        tpo_levels: List[TPOLevel],
        highs: np.ndarray
    ) -> List[float]:
        """Find poor highs (multiple TPOs at high)."""
        poor_highs = []
        
        if not tpo_levels:
            return poor_highs
        
        # Check top levels
        top_levels = tpo_levels[-3:] if len(tpo_levels) >= 3 else tpo_levels
        
        for level in top_levels:
            if level.tpo_count >= 3:  # Multiple TPOs = poor high
                poor_highs.append(level.price)
        
        return poor_highs
    
    def _find_poor_lows(
        self,
        tpo_levels: List[TPOLevel],
        lows: np.ndarray
    ) -> List[float]:
        """Find poor lows (multiple TPOs at low)."""
        poor_lows = []
        
        if not tpo_levels:
            return poor_lows
        
        # Check bottom levels
        bottom_levels = tpo_levels[:3] if len(tpo_levels) >= 3 else tpo_levels
        
        for level in bottom_levels:
            if level.tpo_count >= 3:  # Multiple TPOs = poor low
                poor_lows.append(level.price)
        
        return poor_lows
    
    def _find_excess(
        self,
        tpo_levels: List[TPOLevel],
        is_high: bool
    ) -> Optional[float]:
        """Find excess (single TPO at extreme)."""
        if not tpo_levels:
            return None
        
        if is_high:
            extreme_level = tpo_levels[-1]
        else:
            extreme_level = tpo_levels[0]
        
        if extreme_level.tpo_count == 1:
            return extreme_level.price
        
        return None
    
    def _determine_open_type(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        value_area: ValueArea,
        initial_balance: InitialBalance
    ) -> str:
        """Determine the type of market open."""
        if len(highs) < 2:
            return "unknown"
        
        open_price = closes[0]  # Assuming first close is near open
        
        # Open Drive: Opens and moves strongly in one direction
        if highs[0] == np.max(highs[:3]) or lows[0] == np.min(lows[:3]):
            return "open_drive"
        
        # Open Test Drive: Opens, tests one direction, then drives
        if (highs[1] > highs[0] and lows[1] > lows[0]) or \
           (highs[1] < highs[0] and lows[1] < lows[0]):
            return "open_test_drive"
        
        # Open Rejection Reverse: Opens, rejected, reverses
        if (highs[0] > highs[1] and closes[1] < closes[0]) or \
           (lows[0] < lows[1] and closes[1] > closes[0]):
            return "open_rejection_reverse"
        
        # Open Auction: Balanced open
        return "open_auction"
    
    def _generate_recommendation(
        self,
        current_price: float,
        value_area: ValueArea,
        initial_balance: InitialBalance,
        market_state: MarketState,
        profile_type: MarketProfileType
    ) -> str:
        """Generate trading recommendation."""
        recommendations = []
        
        # Based on market state
        if market_state == MarketState.BALANCE:
            recommendations.append(
                "RANGE: Price in value area. Fade extremes, buy VAL, sell VAH."
            )
        elif market_state == MarketState.IMBALANCE_UP:
            recommendations.append(
                "BULLISH: Price above value area. Look for pullbacks to VAH for longs."
            )
        elif market_state == MarketState.IMBALANCE_DOWN:
            recommendations.append(
                "BEARISH: Price below value area. Look for rallies to VAL for shorts."
            )
        elif market_state == MarketState.BREAKOUT:
            recommendations.append(
                "BREAKOUT: Strong move beyond IB extensions. Follow the trend."
            )
        
        # Based on profile type
        if profile_type == MarketProfileType.TREND:
            recommendations.append(
                "TREND DAY: Strong directional move. Don't fade, follow the trend."
            )
        elif profile_type == MarketProfileType.DOUBLE_DISTRIBUTION:
            recommendations.append(
                "DOUBLE DIST: Two value areas. Trade the gap between them."
            )
        elif profile_type == MarketProfileType.P_SHAPE:
            recommendations.append(
                "P-SHAPE: Short covering rally. Longs may be exhausted."
            )
        elif profile_type == MarketProfileType.B_SHAPE:
            recommendations.append(
                "B-SHAPE: Long liquidation. Shorts may be exhausted."
            )
        
        # Key levels
        recommendations.append(
            f"KEY LEVELS: POC={value_area.poc:.4f}, "
            f"VAH={value_area.high:.4f}, VAL={value_area.low:.4f}"
        )
        
        return " | ".join(recommendations)
    
    def _calculate_confidence(
        self,
        tpo_levels: List[TPOLevel],
        value_area: ValueArea,
        profile_type: MarketProfileType
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        # More TPO levels = more data = more confidence
        if len(tpo_levels) >= 20:
            confidence += 0.15
        elif len(tpo_levels) >= 10:
            confidence += 0.1
        
        # Clear value area = more confidence
        if value_area.value_area_percentage >= 0.65:
            confidence += 0.1
        
        # Clear profile type = more confidence
        if profile_type != MarketProfileType.NORMAL:
            confidence += 0.1
        
        return min(1.0, confidence)
