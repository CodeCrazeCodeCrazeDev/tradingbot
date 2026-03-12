"""
Liquidity Warfare System - Advanced Structural Liquidity Analysis

This module implements institutional-grade liquidity analysis including:
1. Structural Liquidity Radar with DTS/DBS detection
2. Equal highs/lows analyzer with time-decay weighting
3. Sweep hunter algorithm with spoofing detection
4. Liquidity trap avoidance and engineered liquidity pattern recognition
5. False breakout detector using order book momentum
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
try:
    from scipy import signal, stats
except ImportError:
    scipy = None
from scipy.signal import find_peaks
from sklearn.cluster import DBSCAN, KMeans
from datetime import datetime, timedelta
import warnings
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

class LiquidityType(Enum):
    """Types of liquidity zones"""
    BUY_SIDE = "buy_side"
    SELL_SIDE = "sell_side"
    EQUAL_HIGHS = "equal_highs"
    EQUAL_LOWS = "equal_lows"
    STOP_CLUSTER = "stop_cluster"
    ENGINEERED = "engineered"
    NATURAL = "natural"

class SweepType(Enum):
    """Types of liquidity sweeps"""
    STOP_HUNT = "stop_hunt"
    LIQUIDITY_GRAB = "liquidity_grab"
    FALSE_BREAKOUT = "false_breakout"
    ENGINEERED_SWEEP = "engineered_sweep"
    NATURAL_SWEEP = "natural_sweep"

class TrapType(Enum):
    """Types of liquidity traps"""
    BULL_TRAP = "bull_trap"
    BEAR_TRAP = "bear_trap"
    RANGE_TRAP = "range_trap"
    BREAKOUT_TRAP = "breakout_trap"
    REVERSAL_TRAP = "reversal_trap"

@dataclass
class LiquidityZone:
    """Liquidity zone data structure"""
    price: float
    strength: float
    zone_type: LiquidityType
    timestamp: datetime
    volume: float
    touches: int
    time_decay: float
    active: bool
    swept: bool
    engineered: bool

@dataclass
class LiquiditySweep:
    """Liquidity sweep event"""
    sweep_type: SweepType
    price: float
    timestamp: datetime
    volume: float
    speed: float
    retracement: float
    confirmation: bool
    target_zone: LiquidityZone
    spoofing_detected: bool

@dataclass
class LiquidityTrap:
    """Liquidity trap detection"""
    trap_type: TrapType
    entry_price: float
    trap_price: float
    timestamp: datetime
    strength: float
    volume_signature: float
    participants_trapped: int
    escape_probability: float

@dataclass
class StructuralLiquidityMap:
    """Complete structural liquidity mapping"""
    zones: List[LiquidityZone]
    sweeps: List[LiquiditySweep]
    traps: List[LiquidityTrap]
    dominant_flow: str
    liquidity_imbalance: float
    market_maker_activity: float
    retail_sentiment: str

class EqualHighsLowsDetector:
    """Advanced equal highs/lows detection with time-decay weighting"""
    
    def __init__(self, tolerance_pct: float = 0.1, min_touches: int = 2):
        self.tolerance_pct = tolerance_pct
        self.min_touches = min_touches
        self.detected_levels = []
        
    def detect_equal_levels(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Detect equal highs and lows with time-decay weighting
        
        Args:
            df: OHLCV data
            
        Returns:
            List of liquidity zones at equal levels
        """
        equal_zones = []
        
        # Detect equal highs
        equal_highs = self._find_equal_highs(df)
        equal_zones.extend(equal_highs)
        
        # Detect equal lows
        equal_lows = self._find_equal_lows(df)
        equal_zones.extend(equal_lows)
        
        # Apply time decay weighting
        self._apply_time_decay(equal_zones, df)
        
        # Filter by minimum touches and strength
        filtered_zones = [zone for zone in equal_zones 
                         if zone.touches >= self.min_touches and zone.strength > 0.3]
        
        return filtered_zones
    
    def _find_equal_highs(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """Find equal high levels"""
        equal_highs = []
        
        # Get swing highs
        swing_highs = self._get_swing_highs(df)
        
        if len(swing_highs) < 2:
            return equal_highs
        
        # Cluster swing highs by price
        prices = np.array([high[1] for high in swing_highs]).reshape(-1, 1)
        
        # Use DBSCAN for clustering
        price_range = prices.max() - prices.min()
        eps = price_range * (self.tolerance_pct / 100)
        
        clustering = DBSCAN(eps=eps, min_samples=self.min_touches).fit(prices)
        
        # Process each cluster
        for label in set(clustering.labels_):
            if label == -1:  # Noise
                continue
                
            cluster_indices = np.where(clustering.labels_ == label)[0]
            cluster_highs = [swing_highs[i] for i in cluster_indices]
            
            # Calculate zone properties
            zone_price = np.mean([high[1] for high in cluster_highs])
            touches = len(cluster_highs)
            
            # Calculate strength based on touches and volume
            total_volume = sum([self._get_volume_at_index(df, high[0]) for high in cluster_highs])
            avg_volume = df['volume'].mean() if 'volume' in df.columns else 1
            volume_strength = total_volume / (avg_volume * touches) if avg_volume > 0 else 1
            
            strength = min((touches / 5) + (volume_strength / 2), 1.0)
            
            # Get most recent timestamp
            latest_index = max([high[0] for high in cluster_highs])
            timestamp = pd.to_datetime(df.index[latest_index]) if hasattr(df.index[latest_index], 'to_pydatetime') else datetime.now()
            
            zone = LiquidityZone(
                price=zone_price,
                strength=strength,
                zone_type=LiquidityType.EQUAL_HIGHS,
                timestamp=timestamp,
                volume=total_volume,
                touches=touches,
                time_decay=1.0,  # Will be calculated later
                active=True,
                swept=False,
                engineered=self._detect_engineered_level(cluster_highs, df)
            )
            
            equal_highs.append(zone)
        
        return equal_highs
    
    def _find_equal_lows(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """Find equal low levels"""
        equal_lows = []
        
        # Get swing lows
        swing_lows = self._get_swing_lows(df)
        
        if len(swing_lows) < 2:
            return equal_lows
        
        # Cluster swing lows by price
        prices = np.array([low[1] for low in swing_lows]).reshape(-1, 1)
        
        # Use DBSCAN for clustering
        price_range = prices.max() - prices.min()
        eps = price_range * (self.tolerance_pct / 100)
        
        clustering = DBSCAN(eps=eps, min_samples=self.min_touches).fit(prices)
        
        # Process each cluster
        for label in set(clustering.labels_):
            if label == -1:  # Noise
                continue
                
            cluster_indices = np.where(clustering.labels_ == label)[0]
            cluster_lows = [swing_lows[i] for i in cluster_indices]
            
            # Calculate zone properties
            zone_price = np.mean([low[1] for low in cluster_lows])
            touches = len(cluster_lows)
            
            # Calculate strength
            total_volume = sum([self._get_volume_at_index(df, low[0]) for low in cluster_lows])
            avg_volume = df['volume'].mean() if 'volume' in df.columns else 1
            volume_strength = total_volume / (avg_volume * touches) if avg_volume > 0 else 1
            
            strength = min((touches / 5) + (volume_strength / 2), 1.0)
            
            # Get most recent timestamp
            latest_index = max([low[0] for low in cluster_lows])
            timestamp = pd.to_datetime(df.index[latest_index]) if hasattr(df.index[latest_index], 'to_pydatetime') else datetime.now()
            
            zone = LiquidityZone(
                price=zone_price,
                strength=strength,
                zone_type=LiquidityType.EQUAL_LOWS,
                timestamp=timestamp,
                volume=total_volume,
                touches=touches,
                time_decay=1.0,
                active=True,
                swept=False,
                engineered=self._detect_engineered_level(cluster_lows, df)
            )
            
            equal_lows.append(zone)
        
        return equal_lows
    
    def _get_swing_highs(self, df: pd.DataFrame, window: int = 5) -> List[Tuple[int, float]]:
        """Get swing high points"""
        highs = []
        
        for i in range(window, len(df) - window):
            current_high = df['high'].iloc[i]
            
            # Check if it's a swing high
            is_swing_high = True
            for j in range(i - window, i + window + 1):
                if j != i and df['high'].iloc[j] >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                highs.append((i, current_high))
        
        return highs
    
    def _get_swing_lows(self, df: pd.DataFrame, window: int = 5) -> List[Tuple[int, float]]:
        """Get swing low points"""
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df['low'].iloc[i]
            
            # Check if it's a swing low
            is_swing_low = True
            for j in range(i - window, i + window + 1):
                if j != i and df['low'].iloc[j] <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                lows.append((i, current_low))
        
        return lows
    
    def _get_volume_at_index(self, df: pd.DataFrame, index: int) -> float:
        """Get volume at specific index"""
        if 'volume' in df.columns:
            return df['volume'].iloc[index]
        return 1.0
    
    def _detect_engineered_level(self, cluster_points: List[Tuple[int, float]], df: pd.DataFrame) -> bool:
        """Detect if level appears engineered vs natural"""
        if len(cluster_points) < 3:
            return False
        
        # Check for suspicious patterns
        indices = [point[0] for point in cluster_points]
        prices = [point[1] for point in cluster_points]
        
        # Check for too-perfect price alignment
        price_std = np.std(prices)
        avg_price = np.mean(prices)
        price_precision = price_std / avg_price if avg_price > 0 else 0
        
        # Check for regular time intervals (algorithmic pattern)
        time_intervals = np.diff(indices)
        time_regularity = np.std(time_intervals) / np.mean(time_intervals) if np.mean(time_intervals) > 0 else 1
        
        # Engineered if too precise or too regular
        return price_precision < 0.0001 or time_regularity < 0.1
    
    def _apply_time_decay(self, zones: List[LiquidityZone], df: pd.DataFrame):
        """Apply time decay weighting to liquidity zones"""
        current_time = pd.to_datetime(df.index[-1]) if hasattr(df.index[-1], 'to_pydatetime') else datetime.now()
        
        for zone in zones:
            # Calculate time difference in hours
            time_diff = (current_time - zone.timestamp).total_seconds() / 3600
            
            # Exponential decay with half-life of 24 hours
            decay_factor = np.exp(-time_diff / 24)
            zone.time_decay = decay_factor
            
            # Adjust strength with time decay
            zone.strength *= decay_factor

class SweepHunterAlgorithm:
    """Advanced sweep detection with spoofing identification"""
    
    def __init__(self):
        self.sweep_history = []
        self.spoofing_patterns = []
        
    def detect_sweeps(self, df: pd.DataFrame, liquidity_zones: List[LiquidityZone]) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps with spoofing analysis
        
        Args:
            df: OHLCV data
            liquidity_zones: Known liquidity zones
            
        Returns:
            List of detected sweeps
        """
        sweeps = []
        
        for zone in liquidity_zones:
            if zone.swept:
                continue
                
            # Check for sweep of this zone
            sweep = self._check_zone_sweep(df, zone)
            if sweep:
                sweeps.append(sweep)
                zone.swept = True
        
        return sweeps
    
    def _check_zone_sweep(self, df: pd.DataFrame, zone: LiquidityZone) -> Optional[LiquiditySweep]:
        """Check if a specific zone has been swept"""
        zone_price = zone.price
        tolerance = zone_price * 0.001  # 0.1% tolerance
        
        # Look for price action that swept through the zone
        if zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]:
            # Look for upward sweep
            sweep_candles = df[df['high'] > zone_price + tolerance]
        else:
            # Look for downward sweep
            sweep_candles = df[df['low'] < zone_price - tolerance]
        
        if sweep_candles.empty:
            return None
        
        # Get the first sweep occurrence
        first_sweep_idx = sweep_candles.index[0]
        sweep_candle = sweep_candles.iloc[0]
        
        # Calculate sweep properties
        sweep_volume = sweep_candle['volume'] if 'volume' in df.columns else 0
        
        # Calculate sweep speed (price movement per bar)
        lookback = 5
        start_idx = max(0, df.index.get_loc(first_sweep_idx) - lookback)
        pre_sweep_data = df.iloc[start_idx:df.index.get_loc(first_sweep_idx)]
        
        if len(pre_sweep_data) > 0:
            price_change = abs(sweep_candle['close'] - pre_sweep_data['close'].iloc[0])
            time_bars = len(pre_sweep_data)
            speed = price_change / time_bars if time_bars > 0 else 0
        else:
            speed = 0
        
        # Calculate retracement after sweep
        lookforward = 10
        end_idx = min(len(df), df.index.get_loc(first_sweep_idx) + lookforward)
        post_sweep_data = df.iloc[df.index.get_loc(first_sweep_idx):end_idx]
        
        if len(post_sweep_data) > 1:
            if zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]:
                max_retracement = sweep_candle['high'] - post_sweep_data['low'].min()
                retracement = max_retracement / sweep_candle['high'] if sweep_candle['high'] > 0 else 0
            else:
                max_retracement = post_sweep_data['high'].max() - sweep_candle['low']
                retracement = max_retracement / sweep_candle['low'] if sweep_candle['low'] > 0 else 0
        else:
            retracement = 0
        
        # Detect spoofing
        spoofing_detected = self._detect_spoofing(df, first_sweep_idx, zone)
        
        # Classify sweep type
        sweep_type = self._classify_sweep_type(speed, retracement, spoofing_detected, zone)
        
        # Confirmation based on retracement and volume
        confirmation = retracement > 0.002 and sweep_volume > 0  # Significant retracement
        
        timestamp = pd.to_datetime(first_sweep_idx) if hasattr(first_sweep_idx, 'to_pydatetime') else datetime.now()
        
        return LiquiditySweep(
            sweep_type=sweep_type,
            price=zone_price,
            timestamp=timestamp,
            volume=sweep_volume,
            speed=speed,
            retracement=retracement,
            confirmation=confirmation,
            target_zone=zone,
            spoofing_detected=spoofing_detected
        )
    
    def _detect_spoofing(self, df: pd.DataFrame, sweep_idx: int, zone: LiquidityZone) -> bool:
        """Detect spoofing patterns around sweep"""
        # Look for suspicious volume patterns
        sweep_loc = df.index.get_loc(sweep_idx)
        
        # Check volume before sweep
        pre_sweep_window = 5
        start_idx = max(0, sweep_loc - pre_sweep_window)
        pre_sweep_data = df.iloc[start_idx:sweep_loc]
        
        if 'volume' not in df.columns or len(pre_sweep_data) == 0:
            return False
        
        # Calculate volume statistics
        avg_volume = df['volume'].rolling(20).mean().iloc[sweep_loc]
        sweep_volume = df['volume'].iloc[sweep_loc]
        pre_sweep_volume = pre_sweep_data['volume'].mean()
        
        # Spoofing indicators:
        # 1. Sudden volume spike during sweep
        volume_spike = sweep_volume > avg_volume * 3
        
        # 2. Low volume before sweep (accumulation)
        low_pre_volume = pre_sweep_volume < avg_volume * 0.5
        
        # 3. Quick reversal after sweep
        post_sweep_window = 3
        end_idx = min(len(df), sweep_loc + post_sweep_window)
        post_sweep_data = df.iloc[sweep_loc:end_idx]
        
        if len(post_sweep_data) > 1:
            sweep_price = zone.price
            if zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]:
                quick_reversal = post_sweep_data['close'].iloc[-1] < sweep_price
            else:
                quick_reversal = post_sweep_data['close'].iloc[-1] > sweep_price
        else:
            quick_reversal = False
        
        # Spoofing if multiple indicators present
        spoofing_score = sum([volume_spike, low_pre_volume, quick_reversal])
        return spoofing_score >= 2
    
    def _classify_sweep_type(self, speed: float, retracement: float, 
                           spoofing_detected: bool, zone: LiquidityZone) -> SweepType:
        """Classify the type of sweep"""
        if spoofing_detected:
            return SweepType.ENGINEERED_SWEEP
        
        # High speed + high retracement = stop hunt
        if speed > 0.001 and retracement > 0.005:
            return SweepType.STOP_HUNT
        
        # Moderate speed + moderate retracement = liquidity grab
        if speed > 0.0005 and retracement > 0.002:
            return SweepType.LIQUIDITY_GRAB
        
        # Low retracement = false breakout
        if retracement < 0.001:
            return SweepType.FALSE_BREAKOUT
        
        return SweepType.NATURAL_SWEEP

class LiquidityTrapDetector:
    """Advanced liquidity trap detection and avoidance"""
    
    def __init__(self):
        self.trap_history = []
        self.trap_patterns = {}
        
    def detect_traps(self, df: pd.DataFrame, sweeps: List[LiquiditySweep], 
                    zones: List[LiquidityZone]) -> List[LiquidityTrap]:
        """
        Detect various types of liquidity traps
        
        Args:
            df: OHLCV data
            sweeps: Recent liquidity sweeps
            zones: Active liquidity zones
            
        Returns:
            List of detected traps
        """
        traps = []
        
        # Detect bull traps
        bull_traps = self._detect_bull_traps(df, sweeps, zones)
        traps.extend(bull_traps)
        
        # Detect bear traps
        bear_traps = self._detect_bear_traps(df, sweeps, zones)
        traps.extend(bear_traps)
        
        # Detect range traps
        range_traps = self._detect_range_traps(df, zones)
        traps.extend(range_traps)
        
        # Detect breakout traps
        breakout_traps = self._detect_breakout_traps(df, sweeps)
        traps.extend(breakout_traps)
        
        return traps
    
    def _detect_bull_traps(self, df: pd.DataFrame, sweeps: List[LiquiditySweep], 
                          zones: List[LiquidityZone]) -> List[LiquidityTrap]:
        """Detect bull trap patterns"""
        bull_traps = []
        
        # Look for upward sweeps followed by sharp reversals
        upward_sweeps = [s for s in sweeps if s.sweep_type in [SweepType.STOP_HUNT, SweepType.LIQUIDITY_GRAB]
                        and s.target_zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]]
        
        for sweep in upward_sweeps:
            # Check for reversal after sweep
            if sweep.retracement > 0.005:  # Significant retracement
                # Calculate trap properties
                entry_price = sweep.price * 1.001  # Slightly above sweep level
                trap_price = sweep.price
                
                # Estimate participants trapped
                volume_factor = sweep.volume / df['volume'].mean() if 'volume' in df.columns and df['volume'].mean() > 0 else 1
                participants_trapped = int(volume_factor * 100)  # Rough estimate
                
                # Calculate escape probability
                escape_probability = self._calculate_escape_probability(df, sweep, TrapType.BULL_TRAP)
                
                trap = LiquidityTrap(
                    trap_type=TrapType.BULL_TRAP,
                    entry_price=entry_price,
                    trap_price=trap_price,
                    timestamp=sweep.timestamp,
                    strength=sweep.retracement,
                    volume_signature=sweep.volume,
                    participants_trapped=participants_trapped,
                    escape_probability=escape_probability
                )
                
                bull_traps.append(trap)
        
        return bull_traps
    
    def _detect_bear_traps(self, df: pd.DataFrame, sweeps: List[LiquiditySweep], 
                          zones: List[LiquidityZone]) -> List[LiquidityTrap]:
        """Detect bear trap patterns"""
        bear_traps = []
        
        # Look for downward sweeps followed by sharp reversals
        downward_sweeps = [s for s in sweeps if s.sweep_type in [SweepType.STOP_HUNT, SweepType.LIQUIDITY_GRAB]
                          and s.target_zone.zone_type in [LiquidityType.EQUAL_LOWS, LiquidityType.BUY_SIDE]]
        
        for sweep in downward_sweeps:
            if sweep.retracement > 0.005:
                entry_price = sweep.price * 0.999  # Slightly below sweep level
                trap_price = sweep.price
                
                volume_factor = sweep.volume / df['volume'].mean() if 'volume' in df.columns and df['volume'].mean() > 0 else 1
                participants_trapped = int(volume_factor * 100)
                
                escape_probability = self._calculate_escape_probability(df, sweep, TrapType.BEAR_TRAP)
                
                trap = LiquidityTrap(
                    trap_type=TrapType.BEAR_TRAP,
                    entry_price=entry_price,
                    trap_price=trap_price,
                    timestamp=sweep.timestamp,
                    strength=sweep.retracement,
                    volume_signature=sweep.volume,
                    participants_trapped=participants_trapped,
                    escape_probability=escape_probability
                )
                
                bear_traps.append(trap)
        
        return bear_traps
    
    def _detect_range_traps(self, df: pd.DataFrame, zones: List[LiquidityZone]) -> List[LiquidityTrap]:
        """Detect range-bound trap patterns"""
        range_traps = []
        
        # Find range boundaries
        if len(zones) < 2:
            return range_traps
        
        # Separate highs and lows
        high_zones = [z for z in zones if z.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]]
        low_zones = [z for z in zones if z.zone_type in [LiquidityType.EQUAL_LOWS, LiquidityType.BUY_SIDE]]
        
        if not high_zones or not low_zones:
            return range_traps
        
        # Find strongest range boundaries
        strongest_high = max(high_zones, key=lambda x: x.strength)
        strongest_low = max(low_zones, key=lambda x: x.strength)
        
        # Check if price is trapped in range
        current_price = df['close'].iloc[-1]
        range_size = strongest_high.price - strongest_low.price
        
        if strongest_low.price < current_price < strongest_high.price and range_size > 0:
            # Calculate trap strength based on range tightness and zone strength
            trap_strength = (strongest_high.strength + strongest_low.strength) / 2
            trap_strength *= (1 - range_size / current_price)  # Tighter range = stronger trap
            
            # Estimate escape probability
            escape_probability = self._calculate_range_escape_probability(df, strongest_high, strongest_low)
            
            trap = LiquidityTrap(
                trap_type=TrapType.RANGE_TRAP,
                entry_price=current_price,
                trap_price=(strongest_high.price + strongest_low.price) / 2,
                timestamp=datetime.now(),
                strength=trap_strength,
                volume_signature=df['volume'].iloc[-1] if 'volume' in df.columns else 0,
                participants_trapped=int(trap_strength * 200),
                escape_probability=escape_probability
            )
            
            range_traps.append(trap)
        
        return range_traps
    
    def _detect_breakout_traps(self, df: pd.DataFrame, sweeps: List[LiquiditySweep]) -> List[LiquidityTrap]:
        """Detect false breakout traps"""
        breakout_traps = []
        
        false_breakouts = [s for s in sweeps if s.sweep_type == SweepType.FALSE_BREAKOUT]
        
        for sweep in false_breakouts:
            # False breakout that immediately reverses
            if sweep.retracement > 0.003:  # Significant reversal
                trap = LiquidityTrap(
                    trap_type=TrapType.BREAKOUT_TRAP,
                    entry_price=sweep.price,
                    trap_price=sweep.price,
                    timestamp=sweep.timestamp,
                    strength=sweep.retracement,
                    volume_signature=sweep.volume,
                    participants_trapped=int(sweep.volume / 1000) if sweep.volume > 0 else 50,
                    escape_probability=0.3  # Low escape probability for false breakouts
                )
                
                breakout_traps.append(trap)
        
        return breakout_traps
    
    def _calculate_escape_probability(self, df: pd.DataFrame, sweep: LiquiditySweep, 
                                    trap_type: TrapType) -> float:
        """Calculate probability of escaping the trap"""
        # Base probability
        base_prob = 0.4
        
        # Adjust based on volume
        if 'volume' in df.columns:
            avg_volume = df['volume'].mean()
            if sweep.volume > avg_volume * 2:
                base_prob -= 0.1  # High volume makes escape harder
            elif sweep.volume < avg_volume * 0.5:
                base_prob += 0.1  # Low volume makes escape easier
        
        # Adjust based on retracement speed
        if sweep.speed > 0.001:
            base_prob -= 0.1  # Fast moves are harder to escape
        
        # Adjust based on spoofing
        if sweep.spoofing_detected:
            base_prob += 0.2  # Spoofed moves are more likely to reverse
        
        return max(0.1, min(0.9, base_prob))
    
    def _calculate_range_escape_probability(self, df: pd.DataFrame, 
                                          high_zone: LiquidityZone, low_zone: LiquidityZone) -> float:
        """Calculate probability of escaping range trap"""
        # Base probability
        base_prob = 0.5
        
        # Adjust based on zone strength
        avg_strength = (high_zone.strength + low_zone.strength) / 2
        base_prob -= avg_strength * 0.3  # Stronger zones = harder escape
        
        # Adjust based on time decay
        avg_decay = (high_zone.time_decay + low_zone.time_decay) / 2
        base_prob += (1 - avg_decay) * 0.2  # Older zones = easier escape
        
        # Adjust based on recent volatility
        recent_volatility = df['high'].rolling(10).max().iloc[-1] - df['low'].rolling(10).min().iloc[-1]
        avg_volatility = (df['high'] - df['low']).mean()
        
        if recent_volatility > avg_volatility * 1.5:
            base_prob += 0.2  # High volatility increases escape chance
        
        return max(0.1, min(0.9, base_prob))

class LiquidityWarfare:
    """Main radar system combining all liquidity analysis components"""
    
    def __init__(self):
        self.equal_detector = EqualHighsLowsDetector()
        self.sweep_hunter = SweepHunterAlgorithm()
        self.trap_detector = LiquidityTrapDetector()
        self.liquidity_history = []
        
    def scan_liquidity_landscape(self, df: pd.DataFrame) -> StructuralLiquidityMap:
        """
        Comprehensive liquidity landscape analysis
        
        Args:
            df: OHLCV data
            
        Returns:
            Complete structural liquidity map
        """
        # Detect liquidity zones
        zones = self.equal_detector.detect_equal_levels(df)
        
        # Add additional zone types
        additional_zones = self._detect_additional_zones(df)
        zones.extend(additional_zones)
        
        # Detect sweeps
        sweeps = self.sweep_hunter.detect_sweeps(df, zones)
        
        # Detect traps
        traps = self.trap_detector.detect_traps(df, sweeps, zones)
        
        # Analyze market maker activity
        mm_activity = self._analyze_market_maker_activity(df, sweeps, zones)
        
        # Determine dominant liquidity flow
        dominant_flow = self._determine_dominant_flow(sweeps, zones)
        
        # Calculate liquidity imbalance
        liquidity_imbalance = self._calculate_liquidity_imbalance(zones)
        
        # Assess retail sentiment
        retail_sentiment = self._assess_retail_sentiment(traps, sweeps)
        
        return StructuralLiquidityMap(
            zones=zones,
            sweeps=sweeps,
            traps=traps,
            dominant_flow=dominant_flow,
            liquidity_imbalance=liquidity_imbalance,
            market_maker_activity=mm_activity,
            retail_sentiment=retail_sentiment
        )
    
    def _detect_additional_zones(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """Detect additional types of liquidity zones"""
        additional_zones = []
        
        # Detect stop clusters using volume analysis
        if 'volume' in df.columns:
            stop_clusters = self._detect_stop_clusters(df)
            additional_zones.extend(stop_clusters)
        
        # Detect engineered levels
        engineered_levels = self._detect_engineered_levels(df)
        additional_zones.extend(engineered_levels)
        
        return additional_zones
    
    def _detect_stop_clusters(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """Detect stop loss clusters using volume analysis"""
        stop_clusters = []
        
        # Look for volume spikes at key levels
        volume_ma = df['volume'].rolling(20).mean()
        volume_spikes = df[df['volume'] > volume_ma * 2]
        
        if volume_spikes.empty:
            return stop_clusters
        
        # Cluster volume spikes by price
        spike_prices = []
        for idx in volume_spikes.index:
            spike_prices.append(df.loc[idx, 'high'])
            spike_prices.append(df.loc[idx, 'low'])
        
        if len(spike_prices) < 2:
            return stop_clusters
        
        # Use KMeans clustering
        prices_array = np.array(spike_prices).reshape(-1, 1)
        n_clusters = min(5, len(spike_prices) // 2)
        
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(prices_array)
            
            for i in range(n_clusters):
                cluster_prices = prices_array[clusters == i]
                if len(cluster_prices) >= 2:
                    zone_price = np.mean(cluster_prices)
                    zone_strength = len(cluster_prices) / len(spike_prices)
                    
                    zone = LiquidityZone(
                        price=zone_price,
                        strength=zone_strength,
                        zone_type=LiquidityType.STOP_CLUSTER,
                        timestamp=datetime.now(),
                        volume=volume_spikes['volume'].mean(),
                        touches=len(cluster_prices),
                        time_decay=1.0,
                        active=True,
                        swept=False,
                        engineered=False
                    )
                    
                    stop_clusters.append(zone)
        except Exception as e:
            logger.info(f"Stop cluster detection error: {e}")
        
        return stop_clusters
    
    def _detect_engineered_levels(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """Detect artificially engineered liquidity levels"""
        engineered_levels = []
        
        # Look for suspiciously round numbers
        current_price = df['close'].iloc[-1]
        
        # Check round numbers within 1% of current price
        price_range = current_price * 0.01
        
        # Generate round number candidates
        round_candidates = []
        
        # Major round numbers (00, 50)
        base = int(current_price)
        for offset in [-2, -1, 0, 1, 2]:
            round_candidates.append(base + offset)
            round_candidates.append(base + offset + 0.5)
        
        # Check which round numbers have been tested
        for candidate in round_candidates:
            if abs(candidate - current_price) > price_range:
                continue
            
            # Check if price has tested this level
            tolerance = candidate * 0.0005  # 0.05% tolerance
            tests_high = np.sum(np.abs(df['high'] - candidate) < tolerance)
            tests_low = np.sum(np.abs(df['low'] - candidate) < tolerance)
            total_tests = tests_high + tests_low
            
            if total_tests >= 2:
                zone = LiquidityZone(
                    price=candidate,
                    strength=min(total_tests / 5, 1.0),
                    zone_type=LiquidityType.ENGINEERED,
                    timestamp=datetime.now(),
                    volume=df['volume'].mean() if 'volume' in df.columns else 0,
                    touches=total_tests,
                    time_decay=1.0,
                    active=True,
                    swept=False,
                    engineered=True
                )
                
                engineered_levels.append(zone)
        
        return engineered_levels
    
    def _analyze_market_maker_activity(self, df: pd.DataFrame, sweeps: List[LiquiditySweep], 
                                     zones: List[LiquidityZone]) -> float:
        """Analyze market maker activity level"""
        mm_score = 0.0
        
        # Count engineered sweeps
        engineered_sweeps = len([s for s in sweeps if s.spoofing_detected])
        total_sweeps = len(sweeps)
        
        if total_sweeps > 0:
            mm_score += (engineered_sweeps / total_sweeps) * 0.4
        
        # Count engineered zones
        engineered_zones = len([z for z in zones if z.engineered])
        total_zones = len(zones)
        
        if total_zones > 0:
            mm_score += (engineered_zones / total_zones) * 0.3
        
        # Volume analysis
        if 'volume' in df.columns:
            recent_volume = df['volume'].rolling(10).mean().iloc[-1]
            avg_volume = df['volume'].mean()
            
            if recent_volume > avg_volume * 1.5:
                mm_score += 0.2  # High volume suggests MM activity
        
        # Price action analysis
        recent_range = df['high'].rolling(10).max().iloc[-1] - df['low'].rolling(10).min().iloc[-1]
        avg_range = (df['high'] - df['low']).mean()
        
        if recent_range < avg_range * 0.5:
            mm_score += 0.1  # Tight ranges suggest MM control
        
        return min(mm_score, 1.0)
    
    def _determine_dominant_flow(self, sweeps: List[LiquiditySweep], zones: List[LiquidityZone]) -> str:
        """Determine dominant liquidity flow direction"""
        if not sweeps:
            return "neutral"
        
        # Count sweep directions
        upward_sweeps = len([s for s in sweeps if s.target_zone.zone_type in 
                           [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]])
        downward_sweeps = len([s for s in sweeps if s.target_zone.zone_type in 
                             [LiquidityType.EQUAL_LOWS, LiquidityType.BUY_SIDE]])
        
        if upward_sweeps > downward_sweeps * 1.5:
            return "bullish_flow"
        elif downward_sweeps > upward_sweeps * 1.5:
            return "bearish_flow"
        else:
            return "balanced_flow"
    
    def _calculate_liquidity_imbalance(self, zones: List[LiquidityZone]) -> float:
        """Calculate liquidity imbalance between buy and sell side"""
        buy_side_strength = sum([z.strength for z in zones if z.zone_type in 
                               [LiquidityType.EQUAL_LOWS, LiquidityType.BUY_SIDE]])
        sell_side_strength = sum([z.strength for z in zones if z.zone_type in 
                                [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]])
        
        total_strength = buy_side_strength + sell_side_strength
        
        if total_strength == 0:
            return 0.0
        
        # Positive imbalance = more sell-side liquidity (bearish)
        # Negative imbalance = more buy-side liquidity (bullish)
        imbalance = (sell_side_strength - buy_side_strength) / total_strength
        
        return imbalance
    
    def _assess_retail_sentiment(self, traps: List[LiquidityTrap], sweeps: List[LiquiditySweep]) -> str:
        """Assess retail trader sentiment based on traps and sweeps"""
        if not traps and not sweeps:
            return "neutral"
        
        # Count trap types
        bull_traps = len([t for t in traps if t.trap_type == TrapType.BULL_TRAP])
        bear_traps = len([t for t in traps if t.trap_type == TrapType.BEAR_TRAP])
        
        # Count participants trapped
        total_trapped = sum([t.participants_trapped for t in traps])
        
        # Assess sentiment
        if bull_traps > bear_traps and total_trapped > 100:
            return "overly_bullish"  # Many bulls trapped
        elif bear_traps > bull_traps and total_trapped > 100:
            return "overly_bearish"  # Many bears trapped
        elif total_trapped > 200:
            return "confused"  # High trap activity
        else:
            return "cautious"
    
    def get_liquidity_signals(self, liquidity_map: StructuralLiquidityMap) -> Dict[str, Any]:
        """Generate trading signals from liquidity analysis"""
        signals = {
            'zone_signals': self._generate_zone_signals(liquidity_map.zones),
            'sweep_signals': self._generate_sweep_signals(liquidity_map.sweeps),
            'trap_signals': self._generate_trap_signals(liquidity_map.traps),
            'flow_signals': self._generate_flow_signals(liquidity_map),
            'overall_signal': self._generate_overall_liquidity_signal(liquidity_map)
        }
        
        return signals
    
    def _generate_zone_signals(self, zones: List[LiquidityZone]) -> Dict[str, Any]:
        """Generate signals from liquidity zones"""
        if not zones:
            return {'signal': 'neutral', 'strength': 0}
        
        # Find strongest active zones
        active_zones = [z for z in zones if z.active and not z.swept]
        
        if not active_zones:
            return {'signal': 'neutral', 'strength': 0}
        
        strongest_zone = max(active_zones, key=lambda x: x.strength * x.time_decay)
        
        # Generate signal based on zone type
        if strongest_zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SELL_SIDE]:
            signal = 'sell_at_resistance'
        elif strongest_zone.zone_type in [LiquidityType.EQUAL_LOWS, LiquidityType.BUY_SIDE]:
            signal = 'buy_at_support'
        else:
            signal = 'watch_level'
        
        return {
            'signal': signal,
            'strength': strongest_zone.strength,
            'price': strongest_zone.price,
            'zone_type': strongest_zone.zone_type.value,
            'engineered': strongest_zone.engineered
        }
    
    def _generate_sweep_signals(self, sweeps: List[LiquiditySweep]) -> Dict[str, Any]:
        """Generate signals from recent sweeps"""
        if not sweeps:
            return {'signal': 'neutral', 'strength': 0}
        
        recent_sweeps = sweeps[-5:]  # Last 5 sweeps
        
        # Count confirmed sweeps
        confirmed_sweeps = [s for s in recent_sweeps if s.confirmation]
        
        if not confirmed_sweeps:
            return {'signal': 'neutral', 'strength': 0}
        
        latest_sweep = confirmed_sweeps[-1]
        
        # Generate signal based on sweep type and retracement
        if latest_sweep.sweep_type == SweepType.STOP_HUNT and latest_sweep.retracement > 0.005:
            signal = 'fade_sweep'  # Trade against the sweep direction
        elif latest_sweep.sweep_type == SweepType.LIQUIDITY_GRAB:
            signal = 'follow_sweep'  # Trade with the sweep direction
        elif latest_sweep.spoofing_detected:
            signal = 'avoid_direction'  # Avoid trading in sweep direction
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'strength': latest_sweep.retracement,
            'sweep_type': latest_sweep.sweep_type.value,
            'spoofing': latest_sweep.spoofing_detected,
            'price': latest_sweep.price
        }
    
    def _generate_trap_signals(self, traps: List[LiquidityTrap]) -> Dict[str, Any]:
        """Generate signals from liquidity traps"""
        if not traps:
            return {'signal': 'neutral', 'strength': 0}
        
        active_traps = traps[-3:]  # Recent traps
        
        if not active_traps:
            return {'signal': 'neutral', 'strength': 0}
        
        strongest_trap = max(active_traps, key=lambda x: x.strength)
        
        # Generate avoidance signals
        if strongest_trap.trap_type == TrapType.BULL_TRAP:
            signal = 'avoid_long'
        elif strongest_trap.trap_type == TrapType.BEAR_TRAP:
            signal = 'avoid_short'
        elif strongest_trap.trap_type == TrapType.RANGE_TRAP:
            signal = 'avoid_breakout'
        else:
            signal = 'exercise_caution'
        
        return {
            'signal': signal,
            'strength': strongest_trap.strength,
            'trap_type': strongest_trap.trap_type.value,
            'escape_probability': strongest_trap.escape_probability,
            'participants_trapped': strongest_trap.participants_trapped
        }
    
    def _generate_flow_signals(self, liquidity_map: StructuralLiquidityMap) -> Dict[str, Any]:
        """Generate signals from liquidity flow analysis"""
        flow_direction = liquidity_map.dominant_flow
        imbalance = liquidity_map.liquidity_imbalance
        mm_activity = liquidity_map.market_maker_activity
        
        # Generate flow-based signals
        if flow_direction == "bullish_flow" and imbalance < -0.3:
            signal = 'bullish_flow'
        elif flow_direction == "bearish_flow" and imbalance > 0.3:
            signal = 'bearish_flow'
        elif mm_activity > 0.7:
            signal = 'mm_controlled'
        else:
            signal = 'neutral_flow'
        
        return {
            'signal': signal,
            'flow_direction': flow_direction,
            'imbalance': imbalance,
            'mm_activity': mm_activity,
            'retail_sentiment': liquidity_map.retail_sentiment
        }
    
    def _generate_overall_liquidity_signal(self, liquidity_map: StructuralLiquidityMap) -> Dict[str, Any]:
        """Generate overall liquidity-based signal"""
        # Combine all signal components
        zone_strength = max([z.strength for z in liquidity_map.zones], default=0)
        sweep_activity = len(liquidity_map.sweeps) / 10  # Normalize
        trap_risk = len(liquidity_map.traps) / 5  # Normalize
        mm_activity = liquidity_map.market_maker_activity
        
        # Calculate overall signal strength
        signal_strength = (zone_strength + sweep_activity - trap_risk + mm_activity) / 4
        signal_strength = max(0, min(1, signal_strength))
        
        # Determine signal direction
        if liquidity_map.liquidity_imbalance > 0.2:
            direction = 'bearish'
        elif liquidity_map.liquidity_imbalance < -0.2:
            direction = 'bullish'
        else:
            direction = 'neutral'
        
        # Assess signal quality
        if signal_strength > 0.7:
            quality = 'high'
        elif signal_strength > 0.4:
            quality = 'medium'
        else:
            quality = 'low'
        
        return {
            'direction': direction,
            'strength': signal_strength,
            'quality': quality,
            'confidence': signal_strength,
            'components': {
                'zone_strength': zone_strength,
                'sweep_activity': sweep_activity,
                'trap_risk': trap_risk,
                'mm_activity': mm_activity
            }
        }
