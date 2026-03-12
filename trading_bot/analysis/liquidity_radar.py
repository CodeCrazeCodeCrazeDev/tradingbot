"""
Elite Trading Bot - Advanced Liquidity Radar

This module provides real-time liquidity detection and monitoring capabilities
for institutional-grade market analysis.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.signal import find_peaks, argrelextrema
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class LiquidityType(enum.Enum):
    """Types of liquidity zones."""
    BUY_SIDE = "buy_side"           # Above price liquidity
    SELL_SIDE = "sell_side"         # Below price liquidity
    INTERNAL = "internal"           # Within current range
    EXTERNAL = "external"           # Outside current range
    RESTING = "resting"             # Passive liquidity
    SWEPT = "swept"                 # Recently cleared liquidity


class LiquidityStrength(enum.Enum):
    """Strength levels of liquidity zones."""
    WEAK = "weak"                   # Minor liquidity
    MODERATE = "moderate"           # Moderate liquidity
    STRONG = "strong"               # Strong liquidity
    CRITICAL = "critical"           # Major liquidity zone


@dataclass
class LiquidityZone:
    """Represents a liquidity zone."""
    id: str
    zone_type: LiquidityType
    strength: LiquidityStrength
    price_level: float
    price_range: Tuple[float, float]  # (min, max)
    volume: float
    timestamp: datetime
    timeframe: str
    confidence: float = 0.0         # 0-1 confidence score
    touches: int = 0                # Number of times tested
    last_test: Optional[datetime] = None
    swept: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LiquidityProfile:
    """Complete liquidity profile for a market."""
    symbol: str
    timestamp: datetime
    current_price: float
    zones: List[LiquidityZone] = field(default_factory=list)
    buy_side_liquidity: float = 0.0
    sell_side_liquidity: float = 0.0
    net_liquidity: float = 0.0      # Buy - Sell
    liquidity_imbalance: float = 0.0  # Ratio of buy/sell
    nearest_buy_zone: Optional[LiquidityZone] = None
    nearest_sell_zone: Optional[LiquidityZone] = None


class LiquidityRadar:
    """
    Advanced liquidity detection and monitoring system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize liquidity radar.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Liquidity tracking
        self.liquidity_zones: Dict[str, List[LiquidityZone]] = {}
        self.liquidity_history: Dict[str, List[LiquidityProfile]] = {}
        
        logger.info("LiquidityRadar initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "lookback_periods": 100,        # Periods to analyze
            "min_volume_threshold": 1000,   # Minimum volume for zone
            "touch_sensitivity": 0.001,     # 0.1% price tolerance
            "zone_merge_distance": 0.002,   # 0.2% merge distance
            "confidence_threshold": 0.6,    # Minimum confidence
            "sweep_confirmation": 3,        # Bars to confirm sweep
            "strength_multipliers": {
                "weak": 1.0,
                "moderate": 2.0,
                "strong": 3.0,
                "critical": 5.0
            }
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def detect_liquidity_zones(self, 
                              ohlcv_data: pd.DataFrame,
                              symbol: str,
                              timeframe: str = "1H") -> LiquidityProfile:
        """
        Detect liquidity zones in market data.
        
        Args:
            ohlcv_data: OHLCV market data
            symbol: Trading symbol
            timeframe: Timeframe string
            
        Returns:
            LiquidityProfile with detected zones
        """
        if len(ohlcv_data) < self.config["lookback_periods"]:
            return LiquidityProfile(symbol, datetime.now(), ohlcv_data['close'].iloc[-1])
        
        current_price = ohlcv_data['close'].iloc[-1]
        zones = []
        
        # Detect equal highs/lows (classic liquidity zones)
        eq_high_zones = self._detect_equal_highs(ohlcv_data, timeframe)
        eq_low_zones = self._detect_equal_lows(ohlcv_data, timeframe)
        zones.extend(eq_high_zones)
        zones.extend(eq_low_zones)
        
        # Detect volume-based liquidity zones
        volume_zones = self._detect_volume_liquidity(ohlcv_data, timeframe)
        zones.extend(volume_zones)
        
        # Detect order block liquidity
        ob_zones = self._detect_order_block_liquidity(ohlcv_data, timeframe)
        zones.extend(ob_zones)
        
        # Detect fair value gap liquidity
        fvg_zones = self._detect_fvg_liquidity(ohlcv_data, timeframe)
        zones.extend(fvg_zones)
        
        # Merge nearby zones
        zones = self._merge_nearby_zones(zones)
        
        # Calculate zone strengths and confidence
        zones = self._calculate_zone_metrics(zones, ohlcv_data)
        
        # Filter by confidence threshold
        zones = [z for z in zones if z.confidence >= self.config["confidence_threshold"]]
        
        # Create liquidity profile
        profile = self._create_liquidity_profile(symbol, current_price, zones)
        
        # Store in history
        if symbol not in self.liquidity_history:
            self.liquidity_history[symbol] = []
        self.liquidity_history[symbol].append(profile)
        
        # Limit history size
        if len(self.liquidity_history[symbol]) > 1000:
            self.liquidity_history[symbol] = self.liquidity_history[symbol][-1000:]
        
        return profile
    
    def _detect_equal_highs(self, data: pd.DataFrame, timeframe: str) -> List[LiquidityZone]:
        """Detect equal highs liquidity zones."""
        zones = []
        highs = data['high'].values
        
        # Find local maxima
        peaks, _ = find_peaks(highs, distance=5, prominence=highs.std() * 0.5)
        
        if len(peaks) < 2:
            return zones
        
        # Group similar highs
        peak_prices = highs[peaks]
        tolerance = np.mean(peak_prices) * self.config["touch_sensitivity"]
        
        for i, peak_idx in enumerate(peaks):
            peak_price = highs[peak_idx]
            similar_peaks = []
            
            # Find peaks within tolerance
            for j, other_peak_idx in enumerate(peaks):
                if i != j:
                    other_price = highs[other_peak_idx]
                    if abs(peak_price - other_price) <= tolerance:
                        similar_peaks.append((other_peak_idx, other_price))
            
            # Create zone if multiple similar peaks
            if len(similar_peaks) >= 1:  # At least 2 total (original + similar)
                all_prices = [peak_price] + [p[1] for p in similar_peaks]
                min_price = min(all_prices)
                max_price = max(all_prices)
                avg_price = np.mean(all_prices)
                
                # Calculate volume at this level
                volume = data.loc[data.index[peak_idx], 'volume']
                
                zone = LiquidityZone(
                    id=f"eq_high_{uuid.uuid4().hex[:8]}",
                    zone_type=LiquidityType.BUY_SIDE,
                    strength=LiquidityStrength.MODERATE,
                    price_level=avg_price,
                    price_range=(min_price, max_price),
                    volume=volume,
                    timestamp=data.index[peak_idx],
                    timeframe=timeframe,
                    touches=len(similar_peaks) + 1,
                    metadata={"peak_indices": [peak_idx] + [p[0] for p in similar_peaks]}
                )
                zones.append(zone)
        
        return zones
    
    def _detect_equal_lows(self, data: pd.DataFrame, timeframe: str) -> List[LiquidityZone]:
        """Detect equal lows liquidity zones."""
        zones = []
        lows = data['low'].values
        
        # Find local minima
        troughs, _ = find_peaks(-lows, distance=5, prominence=lows.std() * 0.5)
        
        if len(troughs) < 2:
            return zones
        
        # Group similar lows
        trough_prices = lows[troughs]
        tolerance = np.mean(trough_prices) * self.config["touch_sensitivity"]
        
        for i, trough_idx in enumerate(troughs):
            trough_price = lows[trough_idx]
            similar_troughs = []
            
            # Find troughs within tolerance
            for j, other_trough_idx in enumerate(troughs):
                if i != j:
                    other_price = lows[other_trough_idx]
                    if abs(trough_price - other_price) <= tolerance:
                        similar_troughs.append((other_trough_idx, other_price))
            
            # Create zone if multiple similar troughs
            if len(similar_troughs) >= 1:
                all_prices = [trough_price] + [p[1] for p in similar_troughs]
                min_price = min(all_prices)
                max_price = max(all_prices)
                avg_price = np.mean(all_prices)
                
                # Calculate volume at this level
                volume = data.loc[data.index[trough_idx], 'volume']
                
                zone = LiquidityZone(
                    id=f"eq_low_{uuid.uuid4().hex[:8]}",
                    zone_type=LiquidityType.SELL_SIDE,
                    strength=LiquidityStrength.MODERATE,
                    price_level=avg_price,
                    price_range=(min_price, max_price),
                    volume=volume,
                    timestamp=data.index[trough_idx],
                    timeframe=timeframe,
                    touches=len(similar_troughs) + 1,
                    metadata={"trough_indices": [trough_idx] + [p[0] for p in similar_troughs]}
                )
                zones.append(zone)
        
        return zones
    
    def _detect_volume_liquidity(self, data: pd.DataFrame, timeframe: str) -> List[LiquidityZone]:
        """Detect volume-based liquidity zones."""
        zones = []
        
        # Find high volume areas
        volume_threshold = data['volume'].quantile(0.8)  # Top 20% volume
        high_vol_bars = data[data['volume'] >= volume_threshold]
        
        if len(high_vol_bars) == 0:
            return zones
        
        # Group consecutive high volume bars
        high_vol_indices = high_vol_bars.index
        groups = []
        current_group = [high_vol_indices[0]]
        
        for i in range(1, len(high_vol_indices)):
            prev_idx = high_vol_indices[i-1]
            curr_idx = high_vol_indices[i]
            
            # Check if consecutive (within reasonable gap)
            if data.index.get_loc(curr_idx) - data.index.get_loc(prev_idx) <= 3:
                current_group.append(curr_idx)
            else:
                if len(current_group) >= 2:
                    groups.append(current_group)
                current_group = [curr_idx]
        
        # Add last group
        if len(current_group) >= 2:
            groups.append(current_group)
        
        # Create zones from groups
        for group in groups:
            group_data = data.loc[group]
            
            # Calculate zone metrics
            min_price = group_data['low'].min()
            max_price = group_data['high'].max()
            avg_price = (group_data['high'] + group_data['low']).mean() / 2
            total_volume = group_data['volume'].sum()
            
            # Determine zone type based on price action
            if group_data['close'].iloc[-1] > group_data['open'].iloc[0]:
                zone_type = LiquidityType.BUY_SIDE
            else:
                zone_type = LiquidityType.SELL_SIDE
            
            zone = LiquidityZone(
                id=f"vol_liq_{uuid.uuid4().hex[:8]}",
                zone_type=zone_type,
                strength=LiquidityStrength.STRONG,
                price_level=avg_price,
                price_range=(min_price, max_price),
                volume=total_volume,
                timestamp=group_data.index[0],
                timeframe=timeframe,
                metadata={"bar_count": len(group), "avg_volume": total_volume / len(group)}
            )
            zones.append(zone)
        
        return zones
    
    def _detect_order_block_liquidity(self, data: pd.DataFrame, timeframe: str) -> List[LiquidityZone]:
        """Detect order block liquidity zones."""
        zones = []
        
        # Look for strong moves followed by consolidation
        returns = data['close'].pct_change()
        strong_move_threshold = returns.std() * 2
        
        strong_moves = returns[abs(returns) >= strong_move_threshold]
        
        for idx in strong_moves.index:
            try:
                bar_loc = data.index.get_loc(idx)
                
                # Skip if too close to edges
                if bar_loc < 5 or bar_loc >= len(data) - 5:
                    continue
                
                # Get the bar before the strong move (potential order block)
                ob_bar = data.iloc[bar_loc - 1]
                move_direction = 1 if returns.loc[idx] > 0 else -1
                
                # Define order block zone
                if move_direction > 0:  # Bullish move
                    zone_type = LiquidityType.BUY_SIDE
                    price_level = (ob_bar['high'] + ob_bar['low']) / 2
                    price_range = (ob_bar['low'], ob_bar['high'])
                else:  # Bearish move
                    zone_type = LiquidityType.SELL_SIDE
                    price_level = (ob_bar['high'] + ob_bar['low']) / 2
                    price_range = (ob_bar['low'], ob_bar['high'])
                
                zone = LiquidityZone(
                    id=f"ob_liq_{uuid.uuid4().hex[:8]}",
                    zone_type=zone_type,
                    strength=LiquidityStrength.STRONG,
                    price_level=price_level,
                    price_range=price_range,
                    volume=ob_bar['volume'],
                    timestamp=ob_bar.name,
                    timeframe=timeframe,
                    metadata={
                        "move_size": abs(returns.loc[idx]),
                        "move_direction": move_direction
                    }
                )
                zones.append(zone)
                
            except (KeyError, IndexError):
                continue
        
        return zones
    
    def _detect_fvg_liquidity(self, data: pd.DataFrame, timeframe: str) -> List[LiquidityZone]:
        """Detect Fair Value Gap liquidity zones."""
        zones = []
        
        # Look for gaps in price action
        for i in range(2, len(data)):
            prev_bar = data.iloc[i-2]
            curr_bar = data.iloc[i-1]
            next_bar = data.iloc[i]
            
            # Bullish FVG: gap between prev high and next low
            if prev_bar['high'] < next_bar['low']:
                gap_top = next_bar['low']
                gap_bottom = prev_bar['high']
                
                if gap_top > gap_bottom:  # Valid gap
                    zone = LiquidityZone(
                        id=f"fvg_bull_{uuid.uuid4().hex[:8]}",
                        zone_type=LiquidityType.BUY_SIDE,
                        strength=LiquidityStrength.MODERATE,
                        price_level=(gap_top + gap_bottom) / 2,
                        price_range=(gap_bottom, gap_top),
                        volume=curr_bar['volume'],
                        timestamp=curr_bar.name,
                        timeframe=timeframe,
                        metadata={"gap_size": gap_top - gap_bottom, "fvg_type": "bullish"}
                    )
                    zones.append(zone)
            
            # Bearish FVG: gap between prev low and next high
            elif prev_bar['low'] > next_bar['high']:
                gap_top = prev_bar['low']
                gap_bottom = next_bar['high']
                
                if gap_top > gap_bottom:  # Valid gap
                    zone = LiquidityZone(
                        id=f"fvg_bear_{uuid.uuid4().hex[:8]}",
                        zone_type=LiquidityType.SELL_SIDE,
                        strength=LiquidityStrength.MODERATE,
                        price_level=(gap_top + gap_bottom) / 2,
                        price_range=(gap_bottom, gap_top),
                        volume=curr_bar['volume'],
                        timestamp=curr_bar.name,
                        timeframe=timeframe,
                        metadata={"gap_size": gap_top - gap_bottom, "fvg_type": "bearish"}
                    )
                    zones.append(zone)
        
        return zones
    
    def _merge_nearby_zones(self, zones: List[LiquidityZone]) -> List[LiquidityZone]:
        """Merge zones that are close to each other."""
        if len(zones) <= 1:
            return zones
        
        merged_zones = []
        zones_to_merge = zones.copy()
        
        while zones_to_merge:
            current_zone = zones_to_merge.pop(0)
            merge_candidates = []
            
            # Find zones to merge with current zone
            i = 0
            while i < len(zones_to_merge):
                other_zone = zones_to_merge[i]
                
                # Check if zones are close enough to merge
                distance = abs(current_zone.price_level - other_zone.price_level)
                merge_threshold = current_zone.price_level * self.config["zone_merge_distance"]
                
                if distance <= merge_threshold and current_zone.zone_type == other_zone.zone_type:
                    merge_candidates.append(zones_to_merge.pop(i))
                else:
                    i += 1
            
            # Merge zones
            if merge_candidates:
                all_zones = [current_zone] + merge_candidates
                
                # Calculate merged zone properties
                all_prices = [z.price_level for z in all_zones]
                all_volumes = [z.volume for z in all_zones]
                all_ranges = [z.price_range for z in all_zones]
                
                merged_price = np.average(all_prices, weights=all_volumes)
                merged_volume = sum(all_volumes)
                merged_range = (min(r[0] for r in all_ranges), max(r[1] for r in all_ranges))
                merged_touches = sum(z.touches for z in all_zones)
                
                # Use strongest zone's properties as base
                strongest_zone = max(all_zones, key=lambda z: self.config["strength_multipliers"][z.strength.value])
                
                merged_zone = LiquidityZone(
                    id=f"merged_{uuid.uuid4().hex[:8]}",
                    zone_type=strongest_zone.zone_type,
                    strength=strongest_zone.strength,
                    price_level=merged_price,
                    price_range=merged_range,
                    volume=merged_volume,
                    timestamp=min(z.timestamp for z in all_zones),
                    timeframe=strongest_zone.timeframe,
                    touches=merged_touches,
                    metadata={"merged_from": len(all_zones), "original_ids": [z.id for z in all_zones]}
                )
                merged_zones.append(merged_zone)
            else:
                merged_zones.append(current_zone)
        
        return merged_zones
    
    def _calculate_zone_metrics(self, zones: List[LiquidityZone], data: pd.DataFrame) -> List[LiquidityZone]:
        """Calculate confidence and strength metrics for zones."""
        for zone in zones:
            # Base confidence from touches
            touch_confidence = min(zone.touches * 0.2, 0.6)
            
            # Volume confidence
            avg_volume = data['volume'].mean()
            volume_confidence = min(zone.volume / avg_volume * 0.2, 0.3)
            
            # Age confidence (newer zones are less reliable)
            days_old = (datetime.now() - zone.timestamp).days
            age_confidence = max(0.1, 0.4 - days_old * 0.01)
            
            # Range confidence (tighter ranges are more reliable)
            price_range = zone.price_range[1] - zone.price_range[0]
            range_pct = price_range / zone.price_level
            range_confidence = max(0.1, 0.3 - range_pct * 10)
            
            # Combine confidences
            zone.confidence = min(1.0, touch_confidence + volume_confidence + age_confidence + range_confidence)
            
            # Adjust strength based on confidence and volume
            if zone.confidence > 0.8 and zone.volume > avg_volume * 2:
                zone.strength = LiquidityStrength.CRITICAL
            elif zone.confidence > 0.7 and zone.volume > avg_volume * 1.5:
                zone.strength = LiquidityStrength.STRONG
            elif zone.confidence > 0.6:
                zone.strength = LiquidityStrength.MODERATE
            else:
                zone.strength = LiquidityStrength.WEAK
        
        return zones
    
    def _create_liquidity_profile(self, symbol: str, current_price: float, zones: List[LiquidityZone]) -> LiquidityProfile:
        """Create a complete liquidity profile."""
        # Separate buy-side and sell-side zones
        buy_zones = [z for z in zones if z.zone_type == LiquidityType.BUY_SIDE]
        sell_zones = [z for z in zones if z.zone_type == LiquidityType.SELL_SIDE]
        
        # Calculate total liquidity
        buy_side_liquidity = sum(z.volume * self.config["strength_multipliers"][z.strength.value] for z in buy_zones)
        sell_side_liquidity = sum(z.volume * self.config["strength_multipliers"][z.strength.value] for z in sell_zones)
        
        net_liquidity = buy_side_liquidity - sell_side_liquidity
        liquidity_imbalance = buy_side_liquidity / sell_side_liquidity if sell_side_liquidity > 0 else float('inf')
        
        # Find nearest zones
        buy_zones_above = [z for z in buy_zones if z.price_level > current_price]
        sell_zones_below = [z for z in sell_zones if z.price_level < current_price]
        
        nearest_buy_zone = min(buy_zones_above, key=lambda z: abs(z.price_level - current_price)) if buy_zones_above else None
        nearest_sell_zone = max(sell_zones_below, key=lambda z: abs(z.price_level - current_price)) if sell_zones_below else None
        
        return LiquidityProfile(
            symbol=symbol,
            timestamp=datetime.now(),
            current_price=current_price,
            zones=zones,
            buy_side_liquidity=buy_side_liquidity,
            sell_side_liquidity=sell_side_liquidity,
            net_liquidity=net_liquidity,
            liquidity_imbalance=liquidity_imbalance,
            nearest_buy_zone=nearest_buy_zone,
            nearest_sell_zone=nearest_sell_zone
        )
    
    def update_zone_status(self, symbol: str, current_price: float, volume: float = 0) -> List[LiquidityZone]:
        """Update zone status based on current price action."""
        if symbol not in self.liquidity_zones:
            return []
        
        updated_zones = []
        current_time = datetime.now()
        
        for zone in self.liquidity_zones[symbol]:
            # Check if zone was touched/swept
            price_in_zone = zone.price_range[0] <= current_price <= zone.price_range[1]
            
            if price_in_zone:
                zone.last_test = current_time
                zone.touches += 1
                
                # Check if zone was swept (price moved significantly through it)
                if not zone.swept:
                    if zone.zone_type == LiquidityType.BUY_SIDE and current_price < zone.price_range[0] * 0.999:
                        zone.swept = True
                        zone.zone_type = LiquidityType.SWEPT
                    elif zone.zone_type == LiquidityType.SELL_SIDE and current_price > zone.price_range[1] * 1.001:
                        zone.swept = True
                        zone.zone_type = LiquidityType.SWEPT
            
            updated_zones.append(zone)
        
        self.liquidity_zones[symbol] = updated_zones
        return updated_zones
    
    def get_liquidity_summary(self, symbol: str) -> Dict[str, Any]:
        """Get liquidity summary for a symbol."""
        if symbol not in self.liquidity_history or not self.liquidity_history[symbol]:
            return {"error": "No liquidity data available"}
        
        latest_profile = self.liquidity_history[symbol][-1]
        
        return {
            "symbol": symbol,
            "timestamp": latest_profile.timestamp,
            "current_price": latest_profile.current_price,
            "total_zones": len(latest_profile.zones),
            "buy_side_liquidity": latest_profile.buy_side_liquidity,
            "sell_side_liquidity": latest_profile.sell_side_liquidity,
            "net_liquidity": latest_profile.net_liquidity,
            "liquidity_imbalance": latest_profile.liquidity_imbalance,
            "nearest_buy_zone": {
                "price": latest_profile.nearest_buy_zone.price_level,
                "distance": latest_profile.nearest_buy_zone.price_level - latest_profile.current_price,
                "strength": latest_profile.nearest_buy_zone.strength.value
            } if latest_profile.nearest_buy_zone else None,
            "nearest_sell_zone": {
                "price": latest_profile.nearest_sell_zone.price_level,
                "distance": latest_profile.current_price - latest_profile.nearest_sell_zone.price_level,
                "strength": latest_profile.nearest_sell_zone.strength.value
            } if latest_profile.nearest_sell_zone else None,
            "zone_breakdown": {
                "critical": len([z for z in latest_profile.zones if z.strength == LiquidityStrength.CRITICAL]),
                "strong": len([z for z in latest_profile.zones if z.strength == LiquidityStrength.STRONG]),
                "moderate": len([z for z in latest_profile.zones if z.strength == LiquidityStrength.MODERATE]),
                "weak": len([z for z in latest_profile.zones if z.strength == LiquidityStrength.WEAK])
            }
        }
