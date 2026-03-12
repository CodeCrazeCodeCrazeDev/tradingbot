"""
from enum import Enum
Elite Trading Bot - Wyckoff-ICT Fusion

This module provides a fusion of Wyckoff methodology and ICT (Inner Circle Trader) concepts
for identifying high-probability institutional entry points in the market.
"""

import enum
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


class EntryType(enum.Enum):
    """Types of entry triggers."""
    SPRING = "spring"                       # Wyckoff spring
    SECONDARY_TEST = "secondary_test"       # Wyckoff secondary test
    SIGN_OF_STRENGTH = "sign_of_strength"   # Wyckoff sign of strength
    LAST_POINT_OF_SUPPORT = "lps"           # Wyckoff last point of support
    UPTHRUST = "upthrust"                   # Wyckoff upthrust
    SECONDARY_TEST_DIST = "secondary_test_dist"  # Wyckoff secondary test (distribution)
    SIGN_OF_WEAKNESS = "sign_of_weakness"   # Wyckoff sign of weakness
    LAST_POINT_OF_SUPPLY = "lpsy"           # Wyckoff last point of supply
    BREAKER_BLOCK = "breaker_block"         # ICT breaker block
    ORDER_BLOCK_MITIGATION = "ob_mitigation"  # ICT order block mitigation
    FAIR_VALUE_GAP_FILL = "fvg_fill"        # ICT fair value gap fill
    LIQUIDITY_GRAB = "liquidity_grab"       # ICT liquidity grab
    OPTIMAL_TRADE_ENTRY = "ote"             # ICT optimal trade entry
    DISCOUNT_ENTRY = "discount"             # Entry at discount
    PREMIUM_ENTRY = "premium"               # Entry at premium
    CHANGE_OF_CHARACTER = "choch"           # Change of character
    BREAK_OF_STRUCTURE = "bos"              # Break of structure
    CUSTOM = "custom"                       # Custom entry type


class EntryConfirmation(enum.Enum):
    """Types of entry confirmations."""
    VOLUME_CONFIRMATION = "volume_confirmation"  # Confirmation with volume
    PRICE_ACTION = "price_action"           # Price action confirmation
    MOMENTUM_DIVERGENCE = "momentum_divergence"  # Momentum divergence
    ORDER_FLOW_ABSORPTION = "order_flow_absorption"  # Order flow absorption
    MARKET_STRUCTURE_SHIFT = "market_structure_shift"  # Market structure shift
    MULTI_TIMEFRAME_ALIGNMENT = "mtf_alignment"  # Multi-timeframe alignment
    INSTITUTIONAL_FOOTPRINT = "institutional_footprint"  # Institutional footprint
    LIQUIDITY_SWEEP = "liquidity_sweep"     # Liquidity sweep
    SMART_MONEY_DIVERGENCE = "smart_money_divergence"  # Smart money divergence
    CUSTOM = "custom"                       # Custom confirmation


class SchematicPattern(enum.Enum):
    """Wyckoff schematic patterns."""
    ACCUMULATION_SCHEMATIC_1 = "accumulation_1"  # Wyckoff accumulation schematic 1
    ACCUMULATION_SCHEMATIC_2 = "accumulation_2"  # Wyckoff accumulation schematic 2
    DISTRIBUTION_SCHEMATIC_1 = "distribution_1"  # Wyckoff distribution schematic 1
    DISTRIBUTION_SCHEMATIC_2 = "distribution_2"  # Wyckoff distribution schematic 2
    CUSTOM = "custom"                       # Custom schematic


class AccumulationPhase(enum.Enum):
    """Phases of Wyckoff accumulation."""
    PHASE_A = "phase_a"  # Selling climax, automatic rally, secondary test
    PHASE_B = "phase_b"  # Building cause, range-bound action
    PHASE_C = "phase_c"  # Spring or test of trading range
    PHASE_D = "phase_d"  # Sign of strength, backup, last point of support
    PHASE_E = "phase_e"  # Markup, breakout


class DistributionPhase(enum.Enum):
    """Phases of Wyckoff distribution."""
    PHASE_A = "phase_a"  # Preliminary supply, buying climax, automatic reaction
    PHASE_B = "phase_b"  # Secondary test, range-bound action
    PHASE_C = "phase_c"  # Upthrust or test of trading range
    PHASE_D = "phase_d"  # Sign of weakness, rally, last point of supply
    PHASE_E = "phase_e"  # Markdown, breakdown


@dataclass
class OrderBlock:
    """ICT order block structure."""
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    is_bullish: bool
    strength: float
    mitigated: bool = False
    mitigation_time: Optional[datetime] = None
    volume: Optional[float] = None
    delta: Optional[float] = None  # Volume delta (buying vs selling)
    imbalance: Optional[float] = None  # Order flow imbalance
    
    @property
    def midpoint(self) -> float:
        """Get midpoint of order block."""
        return (self.high + self.low) / 2
    
    @property
    def height(self) -> float:
        """Get height of order block."""
        return self.high - self.low
    
    @property
    def is_valid(self) -> bool:
        """Check if order block is still valid (not mitigated)."""
        return not self.mitigated


@dataclass
class FairValueGap:
    """ICT fair value gap structure."""
    time: datetime
    high: float
    low: float
    is_bullish: bool
    filled: bool = False
    fill_time: Optional[datetime] = None
    
    @property
    def gap_size(self) -> float:
        """Get size of fair value gap."""
        return self.high - self.low
    
    @property
    def is_valid(self) -> bool:
        """Check if fair value gap is still valid (not filled)."""
        return not self.filled


@dataclass
class LiquidityVoid:
    """Liquidity void structure."""
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    volume_profile: Optional[Dict[float, float]] = None  # Price level -> volume
    
    @property
    def height(self) -> float:
        """Get height of liquidity void."""
        return self.high - self.low


@dataclass
class EntryTrigger:
    """Entry trigger identified by the system."""
    id: str
    symbol: str
    timestamp: datetime
    entry_type: EntryType
    price: float
    direction: str  # "long" or "short"
    timeframe: str
    confidence: float  # 0.0 to 1.0
    confirmations: List[EntryConfirmation] = field(default_factory=list)
    wyckoff_phase: Optional[Union[AccumulationPhase, DistributionPhase]] = None
    schematic: Optional[SchematicPattern] = None
    order_blocks: List[OrderBlock] = field(default_factory=list)
    fair_value_gaps: List[FairValueGap] = field(default_factory=list)
    liquidity_voids: List[LiquidityVoid] = field(default_factory=list)
    volume_confirmation: bool = False
    multi_timeframe_aligned: bool = False
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward: Optional[float] = None
    notes: str = ""
    
    @property
    def is_valid(self) -> bool:
        """Check if entry trigger is valid based on confirmations."""
        # Must have at least one confirmation
        if not self.confirmations:
            return False
            
        # Must have minimum confidence
        if self.confidence < 0.5:
            return False
            
        return True


class WyckoffICTFusion:
    """
    Fusion of Wyckoff methodology and ICT concepts for identifying
    high-probability institutional entry points.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Wyckoff-ICT fusion.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Detected structures
        self.order_blocks: Dict[str, List[OrderBlock]] = {}  # symbol -> order blocks
        self.fair_value_gaps: Dict[str, List[FairValueGap]] = {}  # symbol -> FVGs
        self.liquidity_voids: Dict[str, List[LiquidityVoid]] = {}  # symbol -> voids
        
        # Wyckoff analysis
        self.current_phase: Dict[str, Union[AccumulationPhase, DistributionPhase]] = {}  # symbol -> phase
        self.current_schematic: Dict[str, SchematicPattern] = {}  # symbol -> schematic
        
        # Entry triggers
        self.entry_triggers: Dict[str, List[EntryTrigger]] = {}  # symbol -> triggers
        
        logger.info("WyckoffICTFusion initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "spring_threshold": 0.3,  # % below trading range for spring
            "upthrust_threshold": 0.3,  # % above trading range for upthrust
            "volume_confirmation_threshold": 1.5,  # Volume multiple for confirmation
            "min_order_block_strength": 0.6,  # Minimum strength for valid order block
            "min_fair_value_gap_size": 0.001,  # Minimum size for valid FVG (% of price)
            "timeframes": ["1h", "4h", "1d"],  # Timeframes to analyze
            "primary_timeframe": "4h",  # Primary timeframe for analysis
            "confirmation_timeframes": ["1h", "1d"],  # Timeframes for confirmation
            "min_confirmations": 2,  # Minimum number of confirmations for valid entry
            "enable_wyckoff": True,  # Enable Wyckoff analysis
            "enable_ict": True,  # Enable ICT concepts
            "enable_multi_timeframe": True,  # Enable multi-timeframe analysis
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze_market_structure(self, 
                               symbol: str, 
                               data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze market structure using Wyckoff and ICT concepts.
        
        Args:
            symbol: Symbol to analyze
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            "symbol": symbol,
            "timestamp": datetime.now(),
            "order_blocks": [],
            "fair_value_gaps": [],
            "liquidity_voids": [],
            "wyckoff_phase": None,
            "schematic": None,
            "entry_triggers": []
        }
        
        # Check if we have data for primary timeframe
        primary_tf = self.config["primary_timeframe"]
        if primary_tf not in data or data[primary_tf].empty:
            logger.warning(f"No data for primary timeframe {primary_tf}")
            return results
        
        # Analyze each timeframe
        for timeframe, df in data.items():
            if df.empty:
                continue
                
            # Detect ICT structures
            if self.config["enable_ict"]:
                order_blocks = self._detect_order_blocks(df, timeframe)
                fair_value_gaps = self._detect_fair_value_gaps(df, timeframe)
                liquidity_voids = self._detect_liquidity_voids(df, timeframe)
                
                # Store structures
                if timeframe == primary_tf:
                    results["order_blocks"] = order_blocks
                    results["fair_value_gaps"] = fair_value_gaps
                    results["liquidity_voids"] = liquidity_voids
                    
                    # Update internal state
                    self.order_blocks[symbol] = order_blocks
                    self.fair_value_gaps[symbol] = fair_value_gaps
                    self.liquidity_voids[symbol] = liquidity_voids
            
            # Detect Wyckoff phases
            if self.config["enable_wyckoff"] and timeframe == primary_tf:
                phase, schematic = self._detect_wyckoff_phase(df)
                results["wyckoff_phase"] = phase
                results["schematic"] = schematic
                
                # Update internal state
                if phase:
                    self.current_phase[symbol] = phase
                if schematic:
                    self.current_schematic[symbol] = schematic
        
        # Generate entry triggers
        if self.config["enable_wyckoff"] and self.config["enable_ict"]:
            entry_triggers = self._generate_entry_triggers(symbol, data)
            results["entry_triggers"] = entry_triggers
            
            # Update internal state
            self.entry_triggers[symbol] = entry_triggers
        
        return results
    
    def _detect_order_blocks(self, 
                           df: pd.DataFrame, 
                           timeframe: str) -> List[OrderBlock]:
        """
        Detect ICT order blocks in price data.
        
        Args:
            df: OHLCV DataFrame
            timeframe: Timeframe of data
            
        Returns:
            List of detected order blocks
        """
        order_blocks = []
        
        # Need at least 10 candles
        if len(df) < 10:
            return order_blocks
        
        # Calculate candle body size and wick size
        df = df.copy()
        df['body_size'] = abs(df['close'] - df['open'])
        df['body_top'] = df[['open', 'close']].max(axis=1)
        df['body_bottom'] = df[['open', 'close']].min(axis=1)
        df['is_bullish'] = df['close'] > df['open']
        df['is_bearish'] = df['close'] < df['open']
        
        # Calculate volume metrics if available
        if 'volume' in df.columns:
            # Calculate average volume
            avg_volume = df['volume'].rolling(window=10).mean()
            df['rel_volume'] = df['volume'] / avg_volume
            
            # Calculate delta if we have enough data
            if 'bid_volume' in df.columns and 'ask_volume' in df.columns:
                df['delta'] = df['ask_volume'] - df['bid_volume']
                df['delta_ratio'] = df['delta'] / df['volume']
            else:
                # Estimate delta based on price action
                df['delta'] = df['body_size'] * df['volume'] * df['is_bullish'].map({True: 1, False: -1})
                df['delta_ratio'] = df['is_bullish'].map({True: 0.6, False: -0.6})  # Rough estimate
        
        # Look for potential order blocks
        for i in range(3, len(df) - 1):
            # Bullish order block (bearish candle followed by strong move up)
            if (df.iloc[i]['is_bearish'] and 
                df.iloc[i+1]['is_bullish'] and 
                df.iloc[i+1]['close'] > df.iloc[i]['body_top']):
                
                # Calculate strength based on subsequent move
                subsequent_move = (df.iloc[i+1]['close'] - df.iloc[i]['close']) / df.iloc[i]['close']
                strength = min(1.0, subsequent_move * 20)  # Scale to 0-1
                
                # Check if strong enough
                if strength >= self.config["min_order_block_strength"]:
                    ob = OrderBlock(
                        start_time=df.index[i],
                        end_time=df.index[i],
                        high=df.iloc[i]['body_top'],
                        low=df.iloc[i]['body_bottom'],
                        is_bullish=True,
                        strength=strength,
                        volume=df.iloc[i]['volume'] if 'volume' in df.columns else None,
                        delta=df.iloc[i]['delta'] if 'delta' in df.columns else None
                    )
                    order_blocks.append(ob)
            
            # Bearish order block (bullish candle followed by strong move down)
            if (df.iloc[i]['is_bullish'] and 
                df.iloc[i+1]['is_bearish'] and 
                df.iloc[i+1]['close'] < df.iloc[i]['body_bottom']):
                
                # Calculate strength based on subsequent move
                subsequent_move = (df.iloc[i]['close'] - df.iloc[i+1]['close']) / df.iloc[i]['close']
                strength = min(1.0, subsequent_move * 20)  # Scale to 0-1
                
                # Check if strong enough
                if strength >= self.config["min_order_block_strength"]:
                    ob = OrderBlock(
                        start_time=df.index[i],
                        end_time=df.index[i],
                        high=df.iloc[i]['body_top'],
                        low=df.iloc[i]['body_bottom'],
                        is_bullish=False,
                        strength=strength,
                        volume=df.iloc[i]['volume'] if 'volume' in df.columns else None,
                        delta=df.iloc[i]['delta'] if 'delta' in df.columns else None
                    )
                    order_blocks.append(ob)
        
        # Check for mitigation
        latest_price = df.iloc[-1]['close']
        for ob in order_blocks:
            if ob.is_bullish and latest_price <= ob.low:
                ob.mitigated = True
                ob.mitigation_time = df.index[-1]
            elif not ob.is_bullish and latest_price >= ob.high:
                ob.mitigated = True
                ob.mitigation_time = df.index[-1]
        
        # Sort by time (newest first)
        order_blocks.sort(key=lambda x: x.start_time, reverse=True)
        
        return order_blocks
    
    def _detect_fair_value_gaps(self, 
                              df: pd.DataFrame, 
                              timeframe: str) -> List[FairValueGap]:
        """
        Detect ICT fair value gaps in price data.
        
        Args:
            df: OHLCV DataFrame
            timeframe: Timeframe of data
            
        Returns:
            List of detected fair value gaps
        """
        fair_value_gaps = []
        
        # Need at least 3 candles
        if len(df) < 3:
            return fair_value_gaps
        
        # Calculate minimum gap size
        avg_price = df['close'].mean()
        min_gap_size = avg_price * self.config["min_fair_value_gap_size"]
        
        # Look for gaps
        for i in range(1, len(df) - 1):
            # Bullish FVG (gap up)
            if df.iloc[i]['low'] > df.iloc[i-1]['high']:
                gap_size = df.iloc[i]['low'] - df.iloc[i-1]['high']
                
                # Check if gap is large enough
                if gap_size >= min_gap_size:
                    fvg = FairValueGap(
                        time=df.index[i],
                        high=df.iloc[i]['low'],
                        low=df.iloc[i-1]['high'],
                        is_bullish=True
                    )
                    fair_value_gaps.append(fvg)
            
            # Bearish FVG (gap down)
            if df.iloc[i]['high'] < df.iloc[i-1]['low']:
                gap_size = df.iloc[i-1]['low'] - df.iloc[i]['high']
                
                # Check if gap is large enough
                if gap_size >= min_gap_size:
                    fvg = FairValueGap(
                        time=df.index[i],
                        high=df.iloc[i-1]['low'],
                        low=df.iloc[i]['high'],
                        is_bullish=False
                    )
                    fair_value_gaps.append(fvg)
        
        # Check for filled gaps
        for fvg in fair_value_gaps:
            # Check if price has entered the gap
            for i in range(1, len(df)):
                candle_time = df.index[i]
                
                # Only check candles after the gap formed
                if candle_time <= fvg.time:
                    continue
                
                # Check if candle filled the gap
                if (df.iloc[i]['low'] <= fvg.high and df.iloc[i]['high'] >= fvg.low):
                    fvg.filled = True
                    fvg.fill_time = candle_time
                    break
        
        # Sort by time (newest first)
        fair_value_gaps.sort(key=lambda x: x.time, reverse=True)
        
        return fair_value_gaps
    
    def _detect_liquidity_voids(self, 
                              df: pd.DataFrame, 
                              timeframe: str) -> List[LiquidityVoid]:
        """
        Detect liquidity voids in price data.
        
        Args:
            df: OHLCV DataFrame
            timeframe: Timeframe of data
            
        Returns:
            List of detected liquidity voids
        """
        liquidity_voids = []
        
        # Need at least 50 candles for meaningful analysis
        if len(df) < 50:
            return liquidity_voids
        
        # Create price bins for volume profile
        price_range = df['high'].max() - df['low'].min()
        bin_size = price_range / 100  # 100 bins
        
        # Create volume profile if volume data is available
        if 'volume' in df.columns:
            # Create bins
            bins = np.arange(df['low'].min(), df['high'].max() + bin_size, bin_size)
            
            # Initialize volume profile
            volume_profile = {bin_mid: 0 for bin_mid in (bins[:-1] + bins[1:]) / 2}
            
            # Distribute volume across price range of each candle
            for i in range(len(df)):
                candle_low = df.iloc[i]['low']
                candle_high = df.iloc[i]['high']
                candle_volume = df.iloc[i]['volume']
                
                # Find bins that overlap with this candle
                overlap_bins = [b for b in bins[:-1] if b >= candle_low and b <= candle_high]
                
                if overlap_bins:
                    # Distribute volume equally across overlapping bins
                    volume_per_bin = candle_volume / len(overlap_bins)
                    
                    for bin_low in overlap_bins:
                        bin_mid = bin_low + bin_size / 2
                        volume_profile[bin_mid] += volume_per_bin
            
            # Convert to array for easier analysis
            bin_mids = np.array(list(volume_profile.keys()))
            bin_volumes = np.array(list(volume_profile.values()))
            
            # Find low volume areas (potential liquidity voids)
            avg_volume = np.mean(bin_volumes[bin_volumes > 0])
            low_volume_threshold = avg_volume * 0.2  # 20% of average volume
            
            # Find consecutive low volume bins
            low_volume_bins = bin_volumes < low_volume_threshold
            
            # Find runs of low volume bins
            from itertools import groupby
            from operator import itemgetter
            
            for k, g in groupby(enumerate(low_volume_bins), key=itemgetter(1)):
                if k:  # If low volume
                    group = list(g)
                    start_idx = group[0][0]
                    end_idx = group[-1][0]
                    
                    # Only consider voids of at least 3 bins
                    if end_idx - start_idx >= 3:
                        void_low = bin_mids[start_idx]
                        void_high = bin_mids[end_idx] + bin_size
                        
                        # Find approximate time range
                        # (when price was above void_high and then below void_low or vice versa)
                        crossings = []
                        for i in range(1, len(df)):
                            if ((df.iloc[i-1]['low'] > void_high and df.iloc[i]['low'] < void_low) or
                                (df.iloc[i-1]['high'] < void_low and df.iloc[i]['high'] > void_high)):
                                crossings.append(i)
                        
                        if len(crossings) >= 2:
                            start_time = df.index[crossings[0]]
                            end_time = df.index[crossings[-1]]
                            
                            # Create volume profile for this void
                            void_profile = {
                                bin_mids[i]: bin_volumes[i] 
                                for i in range(start_idx, end_idx + 1)
                            }
                            
                            void = LiquidityVoid(
                                start_time=start_time,
                                end_time=end_time,
                                high=void_high,
                                low=void_low,
                                volume_profile=void_profile
                            )
                            liquidity_voids.append(void)
        
        # Sort by size (largest first)
        liquidity_voids.sort(key=lambda x: x.height, reverse=True)
        
        return liquidity_voids
    
    def _detect_wyckoff_phase(self, 
                            df: pd.DataFrame) -> Tuple[Optional[Union[AccumulationPhase, DistributionPhase]], 
                                                     Optional[SchematicPattern]]:
        """
        Detect current Wyckoff phase and schematic.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Tuple of (phase, schematic) or (None, None) if not detected
        """
        # Need at least 50 candles for meaningful analysis
        if len(df) < 50:
            return None, None
        
        # Calculate key metrics
        df = df.copy()
        
        # Calculate price swings
        df['swing_high'] = df['high'].rolling(window=5, center=True).max() == df['high']
        df['swing_low'] = df['low'].rolling(window=5, center=True).min() == df['low']
        
        # Calculate volume metrics if available
        if 'volume' in df.columns:
            df['vol_ma'] = df['volume'].rolling(window=20).mean()
            df['rel_volume'] = df['volume'] / df['vol_ma']
        
        # Identify potential phases
        
        # Check for accumulation
        # Phase A: Selling climax, automatic rally, secondary test
        selling_climax = False
        automatic_rally = False
        secondary_test = False
        
        # Look for selling climax (sharp down move on high volume)
        for i in range(20, len(df) - 20):
            if (df.iloc[i]['swing_low'] and 
                'rel_volume' in df.columns and 
                df.iloc[i]['rel_volume'] > 1.5):
                
                # Check for price decline before
                price_decline = (df.iloc[i-10:i]['close'].iloc[0] - df.iloc[i]['close']) / df.iloc[i-10:i]['close'].iloc[0]
                
                if price_decline > 0.05:  # 5% decline
                    selling_climax = True
                    sc_idx = i
                    
                    # Look for automatic rally after selling climax
                    for j in range(i+1, min(i+10, len(df))):
                        if df.iloc[j]['close'] > df.iloc[i]['close'] * 1.02:  # 2% rally
                            automatic_rally = True
                            ar_idx = j
                            
                            # Look for secondary test
                            for k in range(j+1, min(j+15, len(df))):
                                if df.iloc[k]['low'] <= df.iloc[i]['low'] * 1.01:  # Test of SC low
                                    secondary_test = True
                                    st_idx = k
                                    break
                            
                            break
                    
                    break
        
        # Check for distribution
        # Phase A: Preliminary supply, buying climax, automatic reaction
        preliminary_supply = False
        buying_climax = False
        automatic_reaction = False
        
        # Look for buying climax (sharp up move on high volume)
        for i in range(20, len(df) - 20):
            if (df.iloc[i]['swing_high'] and 
                'rel_volume' in df.columns and 
                df.iloc[i]['rel_volume'] > 1.5):
                
                # Check for price advance before
                price_advance = (df.iloc[i]['close'] - df.iloc[i-10:i]['close'].iloc[0]) / df.iloc[i-10:i]['close'].iloc[0]
                
                if price_advance > 0.05:  # 5% advance
                    buying_climax = True
                    bc_idx = i
                    
                    # Look for automatic reaction after buying climax
                    for j in range(i+1, min(i+10, len(df))):
                        if df.iloc[j]['close'] < df.iloc[i]['close'] * 0.98:  # 2% reaction
                            automatic_reaction = True
                            ar_idx = j
                            break
                    
                    # Look for preliminary supply before buying climax
                    for j in range(max(0, i-15), i):
                        if (df.iloc[j]['swing_high'] and 
                            'rel_volume' in df.columns and 
                            df.iloc[j]['rel_volume'] > 1.2):
                            preliminary_supply = True
                            ps_idx = j
                            break
                    
                    break
        
        # Determine phase and schematic
        if selling_climax and automatic_rally:
            if secondary_test:
                # Look for spring (Phase C)
                spring_found = False
                for i in range(st_idx + 1, len(df)):
                    if df.iloc[i]['low'] < df.iloc[sc_idx]['low']:
                        spring_found = True
                        spring_idx = i
                        break
                
                if spring_found:
                    # Look for sign of strength (Phase D)
                    sos_found = False
                    for i in range(spring_idx + 1, len(df)):
                        if df.iloc[i]['close'] > df.iloc[ar_idx]['high']:
                            sos_found = True
                            sos_idx = i
                            break
                    
                    if sos_found:
                        # Phase D or E
                        # Look for last point of support
                        lps_found = False
                        for i in range(sos_idx + 1, len(df)):
                            if (df.iloc[i]['swing_low'] and 
                                df.iloc[i]['low'] > df.iloc[spring_idx]['low']):
                                lps_found = True
                                lps_idx = i
                                break
                        
                        if lps_found:
                            # Check if we've broken out
                            if df.iloc[-1]['close'] > df.iloc[sos_idx]['high']:
                                return AccumulationPhase.PHASE_E, SchematicPattern.ACCUMULATION_SCHEMATIC_1
                            else:
                                return AccumulationPhase.PHASE_D, SchematicPattern.ACCUMULATION_SCHEMATIC_1
                    else:
                        return AccumulationPhase.PHASE_C, SchematicPattern.ACCUMULATION_SCHEMATIC_1
                else:
                    return AccumulationPhase.PHASE_B, SchematicPattern.ACCUMULATION_SCHEMATIC_1
            else:
                return AccumulationPhase.PHASE_A, SchematicPattern.ACCUMULATION_SCHEMATIC_1
                
        elif buying_climax and automatic_reaction:
            if preliminary_supply:
                # Look for upthrust (Phase C)
                upthrust_found = False
                for i in range(ar_idx + 1, len(df)):
                    if df.iloc[i]['high'] > df.iloc[bc_idx]['high']:
                        upthrust_found = True
                        upthrust_idx = i
                        break
                
                if upthrust_found:
                    # Look for sign of weakness (Phase D)
                    sow_found = False
                    for i in range(upthrust_idx + 1, len(df)):
                        if df.iloc[i]['close'] < df.iloc[ar_idx]['low']:
                            sow_found = True
                            sow_idx = i
                            break
                    
                    if sow_found:
                        # Phase D or E
                        # Look for last point of supply
                        lpsy_found = False
                        for i in range(sow_idx + 1, len(df)):
                            if (df.iloc[i]['swing_high'] and 
                                df.iloc[i]['high'] < df.iloc[upthrust_idx]['high']):
                                lpsy_found = True
                                lpsy_idx = i
                                break
                        
                        if lpsy_found:
                            # Check if we've broken down
                            if df.iloc[-1]['close'] < df.iloc[sow_idx]['low']:
                                return DistributionPhase.PHASE_E, SchematicPattern.DISTRIBUTION_SCHEMATIC_1
                            else:
                                return DistributionPhase.PHASE_D, SchematicPattern.DISTRIBUTION_SCHEMATIC_1
                    else:
                        return DistributionPhase.PHASE_C, SchematicPattern.DISTRIBUTION_SCHEMATIC_1
                else:
                    return DistributionPhase.PHASE_B, SchematicPattern.DISTRIBUTION_SCHEMATIC_1
            else:
                return DistributionPhase.PHASE_A, SchematicPattern.DISTRIBUTION_SCHEMATIC_1
        
        return None, None
    
    def _generate_entry_triggers(self, 
                               symbol: str, 
                               data: Dict[str, pd.DataFrame]) -> List[EntryTrigger]:
        """
        Generate entry triggers based on Wyckoff and ICT analysis.
        
        Args:
            symbol: Symbol to analyze
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            List of entry triggers
        """
        entry_triggers = []
        
        # Get current phase and structures
        current_phase = self.current_phase.get(symbol)
        order_blocks = self.order_blocks.get(symbol, [])
        fair_value_gaps = self.fair_value_gaps.get(symbol, [])
        
        # Get primary timeframe data
        primary_tf = self.config["primary_timeframe"]
        if primary_tf not in data or data[primary_tf].empty:
            return entry_triggers
        
        df = data[primary_tf]
        current_price = df.iloc[-1]['close']
        
        # Generate Wyckoff entry triggers
        if self.config["enable_wyckoff"] and current_phase:
            # Accumulation phase entries
            if isinstance(current_phase, AccumulationPhase):
                # Spring entry (Phase C)
                if current_phase == AccumulationPhase.PHASE_C:
                    # Look for spring pattern
                    for i in range(len(df) - 20, len(df)):
                        if df.iloc[i]['swing_low']:
                            # Check if this is a spring (new low followed by quick reversal)
                            is_spring = False
                            for j in range(max(0, i-20), i):
                                if df.iloc[i]['low'] < df.iloc[j]['low']:
                                    is_spring = True
                                    break
                            
                            if is_spring and i < len(df) - 1 and df.iloc[i+1]['close'] > df.iloc[i]['close']:
                                # Confirm with volume if available
                                volume_confirmation = False
                                if 'volume' in df.columns:
                                    volume_confirmation = df.iloc[i+1]['volume'] > df.iloc[i-5:i]['volume'].mean() * 1.2
                                
                                # Create entry trigger
                                trigger = EntryTrigger(
                                    id=f"spring_{symbol}_{int(datetime.now().timestamp())}",
                                    symbol=symbol,
                                    timestamp=df.index[i],
                                    entry_type=EntryType.SPRING,
                                    price=df.iloc[i]['low'],
                                    direction="long",
                                    timeframe=primary_tf,
                                    confidence=0.7,
                                    confirmations=[EntryConfirmation.PRICE_ACTION],
                                    wyckoff_phase=AccumulationPhase.PHASE_C,
                                    volume_confirmation=volume_confirmation,
                                    stop_loss=df.iloc[i]['low'] * 0.99,  # 1% below spring low
                                    notes="Wyckoff spring pattern detected"
                                )
                                
                                # Add volume confirmation if available
                                if volume_confirmation:
                                    trigger.confirmations.append(EntryConfirmation.VOLUME_CONFIRMATION)
                                
                                entry_triggers.append(trigger)
                
                # Last Point of Support entry (Phase D)
                elif current_phase == AccumulationPhase.PHASE_D:
                    # Look for LPS pattern
                    for i in range(len(df) - 15, len(df)):
                        if df.iloc[i]['swing_low']:
                            # Check if this is a higher low
                            higher_low = True
                            for j in range(max(0, i-20), i):
                                if df.iloc[j]['swing_low'] and df.iloc[i]['low'] <= df.iloc[j]['low']:
                                    higher_low = False
                                    break
                            
                            if higher_low and i < len(df) - 1 and df.iloc[i+1]['close'] > df.iloc[i]['close']:
                                # Confirm with volume if available
                                volume_confirmation = False
                                if 'volume' in df.columns:
                                    volume_confirmation = df.iloc[i+1]['volume'] > df.iloc[i-5:i]['volume'].mean()
                                
                                # Create entry trigger
                                trigger = EntryTrigger(
                                    id=f"lps_{symbol}_{int(datetime.now().timestamp())}",
                                    symbol=symbol,
                                    timestamp=df.index[i],
                                    entry_type=EntryType.LAST_POINT_OF_SUPPORT,
                                    price=df.iloc[i]['low'],
                                    direction="long",
                                    timeframe=primary_tf,
                                    confidence=0.8,
                                    confirmations=[EntryConfirmation.PRICE_ACTION],
                                    wyckoff_phase=AccumulationPhase.PHASE_D,
                                    volume_confirmation=volume_confirmation,
                                    stop_loss=df.iloc[i]['low'] * 0.99,  # 1% below LPS low
                                    notes="Wyckoff Last Point of Support detected"
                                )
                                
                                # Add volume confirmation if available
                                if volume_confirmation:
                                    trigger.confirmations.append(EntryConfirmation.VOLUME_CONFIRMATION)
                                
                                entry_triggers.append(trigger)
            
            # Distribution phase entries
            elif isinstance(current_phase, DistributionPhase):
                # Upthrust entry (Phase C)
                if current_phase == DistributionPhase.PHASE_C:
                    # Look for upthrust pattern
                    for i in range(len(df) - 20, len(df)):
                        if df.iloc[i]['swing_high']:
                            # Check if this is an upthrust (new high followed by quick reversal)
                            is_upthrust = False
                            for j in range(max(0, i-20), i):
                                if df.iloc[i]['high'] > df.iloc[j]['high']:
                                    is_upthrust = True
                                    break
                            
                            if is_upthrust and i < len(df) - 1 and df.iloc[i+1]['close'] < df.iloc[i]['close']:
                                # Confirm with volume if available
                                volume_confirmation = False
                                if 'volume' in df.columns:
                                    volume_confirmation = df.iloc[i+1]['volume'] > df.iloc[i-5:i]['volume'].mean() * 1.2
                                
                                # Create entry trigger
                                trigger = EntryTrigger(
                                    id=f"upthrust_{symbol}_{int(datetime.now().timestamp())}",
                                    symbol=symbol,
                                    timestamp=df.index[i],
                                    entry_type=EntryType.UPTHRUST,
                                    price=df.iloc[i]['high'],
                                    direction="short",
                                    timeframe=primary_tf,
                                    confidence=0.7,
                                    confirmations=[EntryConfirmation.PRICE_ACTION],
                                    wyckoff_phase=DistributionPhase.PHASE_C,
                                    volume_confirmation=volume_confirmation,
                                    stop_loss=df.iloc[i]['high'] * 1.01,  # 1% above upthrust high
                                    notes="Wyckoff upthrust pattern detected"
                                )
                                
                                # Add volume confirmation if available
                                if volume_confirmation:
                                    trigger.confirmations.append(EntryConfirmation.VOLUME_CONFIRMATION)
                                
                                entry_triggers.append(trigger)
                
                # Last Point of Supply entry (Phase D)
                elif current_phase == DistributionPhase.PHASE_D:
                    # Look for LPSY pattern
                    for i in range(len(df) - 15, len(df)):
                        if df.iloc[i]['swing_high']:
                            # Check if this is a lower high
                            lower_high = True
                            for j in range(max(0, i-20), i):
                                if df.iloc[j]['swing_high'] and df.iloc[i]['high'] >= df.iloc[j]['high']:
                                    lower_high = False
                                    break
                            
                            if lower_high and i < len(df) - 1 and df.iloc[i+1]['close'] < df.iloc[i]['close']:
                                # Confirm with volume if available
                                volume_confirmation = False
                                if 'volume' in df.columns:
                                    volume_confirmation = df.iloc[i+1]['volume'] > df.iloc[i-5:i]['volume'].mean()
                                
                                # Create entry trigger
                                trigger = EntryTrigger(
                                    id=f"lpsy_{symbol}_{int(datetime.now().timestamp())}",
                                    symbol=symbol,
                                    timestamp=df.index[i],
                                    entry_type=EntryType.LAST_POINT_OF_SUPPLY,
                                    price=df.iloc[i]['high'],
                                    direction="short",
                                    timeframe=primary_tf,
                                    confidence=0.8,
                                    confirmations=[EntryConfirmation.PRICE_ACTION],
                                    wyckoff_phase=DistributionPhase.PHASE_D,
                                    volume_confirmation=volume_confirmation,
                                    stop_loss=df.iloc[i]['high'] * 1.01,  # 1% above LPSY high
                                    notes="Wyckoff Last Point of Supply detected"
                                )
                                
                                # Add volume confirmation if available
                                if volume_confirmation:
                                    trigger.confirmations.append(EntryConfirmation.VOLUME_CONFIRMATION)
                                
                                entry_triggers.append(trigger)
        
        # Generate ICT entry triggers
        if self.config["enable_ict"]:
            # Order block mitigation entries
            for ob in order_blocks:
                # Skip mitigated order blocks
                if ob.mitigated:
                    continue
                
                # Check if price is approaching the order block
                approaching = False
                if ob.is_bullish:
                    # For bullish OB, price should be approaching from above
                    approaching = current_price < ob.high * 1.02
                else:
                    # For bearish OB, price should be approaching from below
                    approaching = current_price > ob.low * 0.98
                
                if approaching:
                    # Create entry trigger
                    direction = "long" if ob.is_bullish else "short"
                    price = ob.midpoint
                    stop_loss = ob.low * 0.99 if ob.is_bullish else ob.high * 1.01
                    
                    trigger = EntryTrigger(
                        id=f"ob_{symbol}_{int(datetime.now().timestamp())}",
                        symbol=symbol,
                        timestamp=datetime.now(),
                        entry_type=EntryType.ORDER_BLOCK_MITIGATION,
                        price=price,
                        direction=direction,
                        timeframe=primary_tf,
                        confidence=min(0.9, ob.strength + 0.2),
                        confirmations=[EntryConfirmation.PRICE_ACTION],
                        order_blocks=[ob],
                        stop_loss=stop_loss,
                        notes=f"ICT {direction} order block mitigation"
                    )
                    
                    # Add volume confirmation if available
                    if ob.volume is not None and ob.volume > 0:
                        avg_volume = df['volume'].tail(20).mean()
                        if ob.volume > avg_volume:
                            trigger.confirmations.append(EntryConfirmation.VOLUME_CONFIRMATION)
                            trigger.volume_confirmation = True
                    
                    entry_triggers.append(trigger)
            
            # Fair value gap fill entries
            for fvg in fair_value_gaps:
                # Skip filled gaps
                if fvg.filled:
                    continue
                
                # Check if price is approaching the FVG
                approaching = False
                if fvg.is_bullish:
                    # For bullish FVG, price should be approaching from below
                    approaching = current_price > fvg.low * 0.98
                else:
                    # For bearish FVG, price should be approaching from above
                    approaching = current_price < fvg.high * 1.02
                
                if approaching:
                    # Create entry trigger
                    direction = "long" if fvg.is_bullish else "short"
                    price = fvg.low if fvg.is_bullish else fvg.high
                    stop_loss = fvg.low * 0.99 if fvg.is_bullish else fvg.high * 1.01
                    
                    trigger = EntryTrigger(
                        id=f"fvg_{symbol}_{int(datetime.now().timestamp())}",
                        symbol=symbol,
                        timestamp=datetime.now(),
                        entry_type=EntryType.FAIR_VALUE_GAP_FILL,
                        price=price,
                        direction=direction,
                        timeframe=primary_tf,
                        confidence=0.7,
                        confirmations=[EntryConfirmation.PRICE_ACTION],
                        fair_value_gaps=[fvg],
                        stop_loss=stop_loss,
                        notes=f"ICT {direction} fair value gap fill"
                    )
                    
                    entry_triggers.append(trigger)
        
        # Add multi-timeframe confirmation
        if self.config["enable_multi_timeframe"]:
            for trigger in entry_triggers:
                mtf_aligned = self._check_multi_timeframe_alignment(
                    symbol, trigger.direction, data
                )
                
                if mtf_aligned:
                    trigger.confirmations.append(EntryConfirmation.MULTI_TIMEFRAME_ALIGNMENT)
                    trigger.multi_timeframe_aligned = True
                    trigger.confidence = min(1.0, trigger.confidence + 0.1)
        
        # Filter by minimum confirmations
        min_confirmations = self.config["min_confirmations"]
        entry_triggers = [
            trigger for trigger in entry_triggers 
            if len(trigger.confirmations) >= min_confirmations
        ]
        
        # Sort by confidence (highest first)
        entry_triggers.sort(key=lambda x: x.confidence, reverse=True)
        
        return entry_triggers
    
    def _check_multi_timeframe_alignment(self, 
                                       symbol: str, 
                                       direction: str, 
                                       data: Dict[str, pd.DataFrame]) -> bool:
        """
        Check if multiple timeframes are aligned with the trade direction.
        
        Args:
            symbol: Symbol to check
            direction: Trade direction ("long" or "short")
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            True if timeframes are aligned, False otherwise
        """
        # Get confirmation timeframes
        confirmation_tfs = self.config["confirmation_timeframes"]
        
        # Count aligned timeframes
        aligned_count = 0
        
        for tf in confirmation_tfs:
            if tf not in data or data[tf].empty:
                continue
                
            df = data[tf]
            
            # Calculate trend direction
            df['sma20'] = df['close'].rolling(window=20).mean()
            df['sma50'] = df['close'].rolling(window=50).mean()
            
            # Check trend alignment
            if direction == "long":
                if df.iloc[-1]['close'] > df.iloc[-1]['sma20'] > df.iloc[-1]['sma50']:
                    aligned_count += 1
            else:  # short
                if df.iloc[-1]['close'] < df.iloc[-1]['sma20'] < df.iloc[-1]['sma50']:
                    aligned_count += 1
        
        # Consider aligned if majority of timeframes are aligned
        return aligned_count >= len(confirmation_tfs) / 2
    
    def get_active_entry_triggers(self, symbol: str) -> List[EntryTrigger]:
        """
        Get active entry triggers for a symbol.
        
        Args:
            symbol: Symbol to get triggers for
            
        Returns:
            List of active entry triggers
        """
        return self.entry_triggers.get(symbol, [])
    
    def get_current_phase(self, symbol: str) -> Optional[Union[AccumulationPhase, DistributionPhase]]:
        """
        Get current Wyckoff phase for a symbol.
        
        Args:
            symbol: Symbol to get phase for
            
        Returns:
            Current phase or None if not detected
        """
        return self.current_phase.get(symbol)
    
    def get_active_order_blocks(self, symbol: str) -> List[OrderBlock]:
        """
        Get active (non-mitigated) order blocks for a symbol.
        
        Args:
            symbol: Symbol to get order blocks for
            
        Returns:
            List of active order blocks
        """
        all_obs = self.order_blocks.get(symbol, [])
        return [ob for ob in all_obs if not ob.mitigated]
    
    def get_unfilled_fair_value_gaps(self, symbol: str) -> List[FairValueGap]:
        """
        Get unfilled fair value gaps for a symbol.
        
        Args:
            symbol: Symbol to get FVGs for
            
        Returns:
            List of unfilled fair value gaps
        """
        all_fvgs = self.fair_value_gaps.get(symbol, [])
        return [fvg for fvg in all_fvgs if not fvg.filled]
