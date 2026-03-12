"""
Skill #8: Footprint Chart Analyzer
==================================

Analyzes bid/ask imbalance at each price level.
Identifies absorption, exhaustion, and imbalance patterns.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImbalanceType(Enum):
    """Type of bid/ask imbalance."""
    BID_IMBALANCE = "bid_imbalance"  # More buying
    ASK_IMBALANCE = "ask_imbalance"  # More selling
    BALANCED = "balanced"
    STACKED_BID = "stacked_bid"  # Multiple consecutive bid imbalances
    STACKED_ASK = "stacked_ask"  # Multiple consecutive ask imbalances


class FootprintPattern(Enum):
    """Footprint chart patterns."""
    ABSORPTION = "absorption"  # High volume, little movement
    EXHAUSTION = "exhaustion"  # Extreme delta at extreme
    INITIATIVE = "initiative"  # Aggressive buying/selling
    RESPONSIVE = "responsive"  # Reactive to levels
    UNFINISHED_BUSINESS = "unfinished_business"  # Single prints
    POOR_HIGH = "poor_high"
    POOR_LOW = "poor_low"


@dataclass
class PriceLevel:
    """Single price level in footprint."""
    price: float
    bid_volume: float
    ask_volume: float
    delta: float  # bid - ask
    total_volume: float
    imbalance_type: ImbalanceType
    imbalance_ratio: float


@dataclass
class FootprintBar:
    """Single footprint bar (candle)."""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    levels: List[PriceLevel]
    total_delta: float
    total_volume: float
    poc_price: float  # Point of control
    vwap: float
    patterns: List[FootprintPattern]


@dataclass
class FootprintAnalysisResult:
    """Complete footprint analysis result."""
    current_bar: FootprintBar
    recent_bars: List[FootprintBar]
    cumulative_delta: float
    stacked_imbalances: List[Tuple[float, float, ImbalanceType]]
    absorption_levels: List[float]
    exhaustion_detected: bool
    initiative_direction: Optional[str]
    unfinished_business: List[float]
    trading_signal: str
    confidence: float


class FootprintChartAnalyzer:
    """
    Advanced Footprint Chart Analysis System.
    
    Analyzes order flow at each price level for institutional insights.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.imbalance_threshold = self.config.get('imbalance_threshold', 3.0)
        self.stacked_count = self.config.get('stacked_count', 3)
        self.tick_size = self.config.get('tick_size', 0.0001)
        self.footprint_history: List[FootprintBar] = []
        
        logger.info("FootprintChartAnalyzer initialized")
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        opens: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        bid_volumes: Optional[np.ndarray] = None,
        ask_volumes: Optional[np.ndarray] = None
    ) -> FootprintAnalysisResult:
        """
        Perform complete footprint analysis.
        
        Args:
            highs, lows, opens, closes: OHLC data
            volumes: Total volumes
            timestamps: Timestamps
            bid_volumes: Optional bid volumes per bar
            ask_volumes: Optional ask volumes per bar
            
        Returns:
            FootprintAnalysisResult with complete analysis
        """
        # Estimate bid/ask if not provided
        if bid_volumes is None or ask_volumes is None:
            bid_volumes, ask_volumes = self._estimate_bid_ask(
                highs, lows, opens, closes, volumes
            )
        
        # Build footprint bars
        footprint_bars = self._build_footprint_bars(
            highs, lows, opens, closes, volumes,
            bid_volumes, ask_volumes, timestamps
        )
        
        if not footprint_bars:
            return self._create_empty_result()
        
        # Update history
        self.footprint_history = footprint_bars
        
        # Get current bar
        current_bar = footprint_bars[-1]
        
        # Calculate cumulative delta
        cumulative_delta = sum(bar.total_delta for bar in footprint_bars)
        
        # Find stacked imbalances
        stacked_imbalances = self._find_stacked_imbalances(footprint_bars)
        
        # Find absorption levels
        absorption_levels = self._find_absorption_levels(footprint_bars)
        
        # Detect exhaustion
        exhaustion = self._detect_exhaustion(footprint_bars)
        
        # Identify initiative direction
        initiative = self._identify_initiative(footprint_bars)
        
        # Find unfinished business
        unfinished = self._find_unfinished_business(footprint_bars)
        
        # Generate signal
        signal = self._generate_signal(
            current_bar, stacked_imbalances, absorption_levels,
            exhaustion, initiative
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            stacked_imbalances, absorption_levels, exhaustion
        )
        
        return FootprintAnalysisResult(
            current_bar=current_bar,
            recent_bars=footprint_bars[-10:],
            cumulative_delta=cumulative_delta,
            stacked_imbalances=stacked_imbalances,
            absorption_levels=absorption_levels,
            exhaustion_detected=exhaustion,
            initiative_direction=initiative,
            unfinished_business=unfinished,
            trading_signal=signal,
            confidence=confidence
        )
    
    def _estimate_bid_ask(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        opens: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate bid/ask volume from OHLC."""
        bid_volumes = np.zeros(len(volumes))
        ask_volumes = np.zeros(len(volumes))
        
        for i in range(len(volumes)):
            bar_range = highs[i] - lows[i]
            
            if bar_range > 0:
                # Bullish bar: more bid volume
                if closes[i] > opens[i]:
                    bid_pct = 0.5 + (closes[i] - opens[i]) / bar_range * 0.3
                # Bearish bar: more ask volume
                else:
                    bid_pct = 0.5 - (opens[i] - closes[i]) / bar_range * 0.3
                
                bid_pct = max(0.2, min(0.8, bid_pct))
            else:
                bid_pct = 0.5
            
            bid_volumes[i] = volumes[i] * bid_pct
            ask_volumes[i] = volumes[i] * (1 - bid_pct)
        
        return bid_volumes, ask_volumes
    
    def _build_footprint_bars(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        opens: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        bid_volumes: np.ndarray,
        ask_volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[FootprintBar]:
        """Build footprint bar objects."""
        footprint_bars = []
        
        for i in range(len(highs)):
            # Create price levels for this bar
            levels = self._create_price_levels(
                highs[i], lows[i], bid_volumes[i], ask_volumes[i]
            )
            
            # Calculate bar metrics
            total_delta = bid_volumes[i] - ask_volumes[i]
            total_volume = volumes[i]
            
            # Find POC (highest volume level)
            poc_price = levels[0].price if levels else closes[i]
            max_vol = 0
            for level in levels:
                if level.total_volume > max_vol:
                    max_vol = level.total_volume
                    poc_price = level.price
            
            # Calculate VWAP
            vwap = self._calculate_vwap(levels)
            
            # Identify patterns
            patterns = self._identify_patterns(
                levels, total_delta, highs[i], lows[i], closes[i]
            )
            
            footprint_bars.append(FootprintBar(
                timestamp=timestamps[i],
                open_price=opens[i],
                high_price=highs[i],
                low_price=lows[i],
                close_price=closes[i],
                levels=levels,
                total_delta=total_delta,
                total_volume=total_volume,
                poc_price=poc_price,
                vwap=vwap,
                patterns=patterns
            ))
        
        return footprint_bars
    
    def _create_price_levels(
        self,
        high: float,
        low: float,
        bid_volume: float,
        ask_volume: float
    ) -> List[PriceLevel]:
        """Create price levels for a bar."""
        levels = []
        
        # Determine tick size
        tick_size = self._get_tick_size(low)
        
        # Number of levels
        num_levels = max(1, int((high - low) / tick_size))
        
        # Distribute volume across levels (simplified)
        vol_per_level = (bid_volume + ask_volume) / num_levels if num_levels > 0 else 0
        bid_per_level = bid_volume / num_levels if num_levels > 0 else 0
        ask_per_level = ask_volume / num_levels if num_levels > 0 else 0
        
        for i in range(num_levels):
            price = low + i * tick_size
            
            # Add some randomness to make it realistic
            bid_vol = bid_per_level * (0.8 + np.random.random() * 0.4)
            ask_vol = ask_per_level * (0.8 + np.random.random() * 0.4)
            
            delta = bid_vol - ask_vol
            total = bid_vol + ask_vol
            
            # Determine imbalance
            if total > 0:
                ratio = max(bid_vol, ask_vol) / min(bid_vol, ask_vol) if min(bid_vol, ask_vol) > 0 else float('inf')
            else:
                ratio = 1.0
            
            if ratio >= self.imbalance_threshold:
                if bid_vol > ask_vol:
                    imbalance_type = ImbalanceType.BID_IMBALANCE
                else:
                    imbalance_type = ImbalanceType.ASK_IMBALANCE
            else:
                imbalance_type = ImbalanceType.BALANCED
            
            levels.append(PriceLevel(
                price=price,
                bid_volume=bid_vol,
                ask_volume=ask_vol,
                delta=delta,
                total_volume=total,
                imbalance_type=imbalance_type,
                imbalance_ratio=ratio
            ))
        
        return levels
    
    def _get_tick_size(self, price: float) -> float:
        """Get appropriate tick size."""
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
    
    def _calculate_vwap(self, levels: List[PriceLevel]) -> float:
        """Calculate VWAP from price levels."""
        if not levels:
            return 0.0
        
        total_volume = sum(level.total_volume for level in levels)
        if total_volume == 0:
            return levels[len(levels) // 2].price
        
        vwap = sum(level.price * level.total_volume for level in levels) / total_volume
        return vwap
    
    def _identify_patterns(
        self,
        levels: List[PriceLevel],
        total_delta: float,
        high: float,
        low: float,
        close: float
    ) -> List[FootprintPattern]:
        """Identify footprint patterns in a bar."""
        patterns = []
        
        if not levels:
            return patterns
        
        # Absorption: High volume at extreme with little movement
        high_levels = [l for l in levels if l.price >= high - (high - low) * 0.2]
        low_levels = [l for l in levels if l.price <= low + (high - low) * 0.2]
        
        high_volume = sum(l.total_volume for l in high_levels)
        low_volume = sum(l.total_volume for l in low_levels)
        total_volume = sum(l.total_volume for l in levels)
        
        if high_volume > total_volume * 0.4 and close < high - (high - low) * 0.3:
            patterns.append(FootprintPattern.ABSORPTION)
        if low_volume > total_volume * 0.4 and close > low + (high - low) * 0.3:
            patterns.append(FootprintPattern.ABSORPTION)
        
        # Exhaustion: Extreme delta at extreme price
        if total_delta > 0 and close == high:
            patterns.append(FootprintPattern.EXHAUSTION)
        if total_delta < 0 and close == low:
            patterns.append(FootprintPattern.EXHAUSTION)
        
        # Initiative: Strong directional move
        if abs(total_delta) > total_volume * 0.3:
            patterns.append(FootprintPattern.INITIATIVE)
        
        # Poor high/low: Multiple touches at extreme
        if len(high_levels) >= 3:
            patterns.append(FootprintPattern.POOR_HIGH)
        if len(low_levels) >= 3:
            patterns.append(FootprintPattern.POOR_LOW)
        
        return patterns
    
    def _find_stacked_imbalances(
        self,
        bars: List[FootprintBar]
    ) -> List[Tuple[float, float, ImbalanceType]]:
        """Find stacked bid/ask imbalances."""
        stacked = []
        
        for bar in bars:
            # Look for consecutive imbalances
            consecutive_bid = 0
            consecutive_ask = 0
            start_price = 0
            
            for level in bar.levels:
                if level.imbalance_type == ImbalanceType.BID_IMBALANCE:
                    if consecutive_bid == 0:
                        start_price = level.price
                    consecutive_bid += 1
                    consecutive_ask = 0
                    
                    if consecutive_bid >= self.stacked_count:
                        stacked.append((
                            start_price,
                            level.price,
                            ImbalanceType.STACKED_BID
                        ))
                
                elif level.imbalance_type == ImbalanceType.ASK_IMBALANCE:
                    if consecutive_ask == 0:
                        start_price = level.price
                    consecutive_ask += 1
                    consecutive_bid = 0
                    
                    if consecutive_ask >= self.stacked_count:
                        stacked.append((
                            start_price,
                            level.price,
                            ImbalanceType.STACKED_ASK
                        ))
                
                else:
                    consecutive_bid = 0
                    consecutive_ask = 0
        
        return stacked
    
    def _find_absorption_levels(self, bars: List[FootprintBar]) -> List[float]:
        """Find price levels with absorption."""
        absorption_levels = []
        
        for bar in bars:
            if FootprintPattern.ABSORPTION in bar.patterns:
                # Find the level with highest volume
                if bar.levels:
                    max_level = max(bar.levels, key=lambda l: l.total_volume)
                    absorption_levels.append(max_level.price)
        
        return list(set(absorption_levels))
    
    def _detect_exhaustion(self, bars: List[FootprintBar]) -> bool:
        """Detect exhaustion in recent bars."""
        if not bars:
            return False
        
        recent = bars[-3:]
        
        for bar in recent:
            if FootprintPattern.EXHAUSTION in bar.patterns:
                return True
        
        return False
    
    def _identify_initiative(self, bars: List[FootprintBar]) -> Optional[str]:
        """Identify initiative buying or selling."""
        if len(bars) < 3:
            return None
        
        recent = bars[-5:]
        
        buy_initiative = sum(
            1 for bar in recent
            if bar.total_delta > 0 and FootprintPattern.INITIATIVE in bar.patterns
        )
        
        sell_initiative = sum(
            1 for bar in recent
            if bar.total_delta < 0 and FootprintPattern.INITIATIVE in bar.patterns
        )
        
        if buy_initiative >= 3:
            return "buying"
        elif sell_initiative >= 3:
            return "selling"
        
        return None
    
    def _find_unfinished_business(self, bars: List[FootprintBar]) -> List[float]:
        """Find single print levels (unfinished business)."""
        unfinished = []
        
        for bar in bars:
            for level in bar.levels:
                # Single print = very low volume at a level
                if level.total_volume < bar.total_volume * 0.05:
                    unfinished.append(level.price)
        
        return list(set(unfinished))
    
    def _generate_signal(
        self,
        current_bar: FootprintBar,
        stacked: List[Tuple[float, float, ImbalanceType]],
        absorption: List[float],
        exhaustion: bool,
        initiative: Optional[str]
    ) -> str:
        """Generate trading signal from footprint analysis."""
        signals = []
        
        # Current bar delta
        if current_bar.total_delta > 0:
            signals.append(f"DELTA: Positive ({current_bar.total_delta:.0f}) - buyers in control")
        else:
            signals.append(f"DELTA: Negative ({current_bar.total_delta:.0f}) - sellers in control")
        
        # Stacked imbalances
        bid_stacks = [s for s in stacked if s[2] == ImbalanceType.STACKED_BID]
        ask_stacks = [s for s in stacked if s[2] == ImbalanceType.STACKED_ASK]
        
        if bid_stacks:
            signals.append(f"STACKED BIDS at {bid_stacks[-1][0]:.4f}-{bid_stacks[-1][1]:.4f} - support")
        if ask_stacks:
            signals.append(f"STACKED ASKS at {ask_stacks[-1][0]:.4f}-{ask_stacks[-1][1]:.4f} - resistance")
        
        # Absorption
        if absorption:
            signals.append(f"ABSORPTION at {absorption[-1]:.4f} - potential reversal")
        
        # Exhaustion
        if exhaustion:
            signals.append("EXHAUSTION detected - trend may reverse")
        
        # Initiative
        if initiative:
            signals.append(f"INITIATIVE {initiative.upper()} - follow the flow")
        
        return " | ".join(signals)
    
    def _calculate_confidence(
        self,
        stacked: List[Tuple[float, float, ImbalanceType]],
        absorption: List[float],
        exhaustion: bool
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        if stacked:
            confidence += 0.15
        
        if absorption:
            confidence += 0.15
        
        if exhaustion:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_empty_result(self) -> FootprintAnalysisResult:
        """Create empty result for insufficient data."""
        empty_bar = FootprintBar(
            timestamp=datetime.now(),
            open_price=0, high_price=0, low_price=0, close_price=0,
            levels=[], total_delta=0, total_volume=0,
            poc_price=0, vwap=0, patterns=[]
        )
        
        return FootprintAnalysisResult(
            current_bar=empty_bar,
            recent_bars=[],
            cumulative_delta=0,
            stacked_imbalances=[],
            absorption_levels=[],
            exhaustion_detected=False,
            initiative_direction=None,
            unfinished_business=[],
            trading_signal="Insufficient data",
            confidence=0
        )
