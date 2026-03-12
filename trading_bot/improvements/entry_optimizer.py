"""
Entry Timing Optimization
=========================

Optimizes trade entry timing through:
1. Pullback detection for trend entries
2. Liquidity zone identification
3. Order flow confirmation
4. Avoid entering at resistance/support

Target: 10-20% better entry prices
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class EntryQuality(Enum):
    """Quality of entry opportunity"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    AVOID = "avoid"


class ZoneType(Enum):
    """Types of price zones"""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    DEMAND = "demand"
    SUPPLY = "supply"
    LIQUIDITY = "liquidity"


@dataclass
class PriceZone:
    """A significant price zone"""
    zone_type: ZoneType
    price_low: float
    price_high: float
    strength: float  # 0-1
    touches: int
    last_touch: Optional[datetime] = None
    
    @property
    def midpoint(self) -> float:
        return (self.price_low + self.price_high) / 2


@dataclass
class EntryOpportunity:
    """An entry opportunity analysis"""
    symbol: str
    direction: str
    current_price: float
    optimal_entry: float
    entry_quality: EntryQuality
    wait_for_pullback: bool
    pullback_target: Optional[float]
    nearby_zones: List[PriceZone]
    risk_reward: float
    reasons: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'current_price': self.current_price,
            'optimal_entry': self.optimal_entry,
            'entry_quality': self.entry_quality.value,
            'wait_for_pullback': self.wait_for_pullback,
            'pullback_target': self.pullback_target,
            'risk_reward': self.risk_reward,
            'reasons': self.reasons,
        }


class PullbackDetector:
    """
    Detects pullbacks for optimal trend entries.
    
    PRINCIPLE: Enter trends on pullbacks, not at extensions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # EMA periods for pullback detection
            self.fast_ema = self.config.get('fast_ema', 20)
            self.slow_ema = self.config.get('slow_ema', 50)
        
            # Pullback depth thresholds (as % of recent move)
            self.min_pullback = self.config.get('min_pullback', 0.382)  # 38.2% Fib
            self.max_pullback = self.config.get('max_pullback', 0.618)  # 61.8% Fib
        
            logger.info("PullbackDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_pullback(
        self,
        direction: str,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> Tuple[bool, Optional[float], str]:
        """
        Detect if price is in a pullback zone.
        
        Args:
            direction: 'BUY' or 'SELL'
            highs: High prices
            lows: Low prices
            closes: Close prices
        
        Returns:
            Tuple of (is_pullback, pullback_target, reason)
        """
        try:
            if len(closes) < 50:
                return False, None, "Insufficient data"
        
            # Calculate EMAs
            fast_ema = self._calculate_ema(closes, self.fast_ema)
            slow_ema = self._calculate_ema(closes, self.slow_ema)
        
            current_price = closes[-1]
        
            if direction == 'BUY':
                # For buy: look for pullback in uptrend
                if fast_ema[-1] <= slow_ema[-1]:
                    return False, None, "Not in uptrend"
            
                # Find recent swing high and low
                recent_high = max(highs[-20:])
                recent_low = min(lows[-30:-10]) if len(lows) > 30 else min(lows[-20:])
            
                move_size = recent_high - recent_low
            
                # Calculate Fibonacci levels
                fib_382 = recent_high - (move_size * 0.382)
                fib_500 = recent_high - (move_size * 0.500)
                fib_618 = recent_high - (move_size * 0.618)
            
                # Check if price is in pullback zone
                if fib_618 <= current_price <= fib_382:
                    pullback_depth = (recent_high - current_price) / move_size
                    return True, fib_500, f"Pullback at {pullback_depth:.1%} (ideal zone)"
                elif current_price > fib_382:
                    return False, fib_382, f"Wait for pullback to {fib_382:.5f}"
                else:
                    return False, None, "Pullback too deep"
        
            else:  # SELL
                # For sell: look for pullback in downtrend
                if fast_ema[-1] >= slow_ema[-1]:
                    return False, None, "Not in downtrend"
            
                # Find recent swing high and low
                recent_low = min(lows[-20:])
                recent_high = max(highs[-30:-10]) if len(highs) > 30 else max(highs[-20:])
            
                move_size = recent_high - recent_low
            
                # Calculate Fibonacci levels
                fib_382 = recent_low + (move_size * 0.382)
                fib_500 = recent_low + (move_size * 0.500)
                fib_618 = recent_low + (move_size * 0.618)
            
                # Check if price is in pullback zone
                if fib_382 <= current_price <= fib_618:
                    pullback_depth = (current_price - recent_low) / move_size
                    return True, fib_500, f"Pullback at {pullback_depth:.1%} (ideal zone)"
                elif current_price < fib_382:
                    return False, fib_382, f"Wait for pullback to {fib_382:.5f}"
                else:
                    return False, None, "Pullback too deep"
        except Exception as e:
            logger.error(f"Error in detect_pullback: {e}")
            raise
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        try:
            multiplier = 2 / (period + 1)
            ema = np.zeros(len(prices))
            ema[0] = prices[0]
        
            for i in range(1, len(prices)):
                ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
            return ema
        except Exception as e:
            logger.error(f"Error in _calculate_ema: {e}")
            raise


class LiquidityZoneFinder:
    """
    Identifies liquidity zones for optimal entries.
    
    PRINCIPLE: Enter where liquidity provides better fills.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Zone detection parameters
            self.lookback = self.config.get('lookback', 100)
            self.min_touches = self.config.get('min_touches', 2)
            self.zone_tolerance = self.config.get('zone_tolerance', 0.001)  # 0.1%
        
            logger.info("LiquidityZoneFinder initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def find_zones(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> List[PriceZone]:
        """
        Find significant price zones.
        
        Returns:
            List of PriceZone objects
        """
        try:
            if len(closes) < self.lookback:
                return []
        
            zones = []
        
            # Find swing highs (resistance/supply)
            swing_highs = self._find_swing_points(highs, is_high=True)
        
            # Find swing lows (support/demand)
            swing_lows = self._find_swing_points(lows, is_high=False)
        
            # Cluster swing highs into zones
            for cluster in self._cluster_levels(swing_highs):
                zone = PriceZone(
                    zone_type=ZoneType.RESISTANCE,
                    price_low=min(cluster) * (1 - self.zone_tolerance),
                    price_high=max(cluster) * (1 + self.zone_tolerance),
                    strength=min(1.0, len(cluster) / 5),
                    touches=len(cluster)
                )
                zones.append(zone)
        
            # Cluster swing lows into zones
            for cluster in self._cluster_levels(swing_lows):
                zone = PriceZone(
                    zone_type=ZoneType.SUPPORT,
                    price_low=min(cluster) * (1 - self.zone_tolerance),
                    price_high=max(cluster) * (1 + self.zone_tolerance),
                    strength=min(1.0, len(cluster) / 5),
                    touches=len(cluster)
                )
                zones.append(zone)
        
            return zones
        except Exception as e:
            logger.error(f"Error in find_zones: {e}")
            raise
    
    def _find_swing_points(
        self,
        prices: np.ndarray,
        is_high: bool,
        lookback: int = 5
    ) -> List[float]:
        """Find swing high or low points"""
        try:
            swings = []
        
            for i in range(lookback, len(prices) - lookback):
                if is_high:
                    if prices[i] == max(prices[i-lookback:i+lookback+1]):
                        swings.append(prices[i])
                else:
                    if prices[i] == min(prices[i-lookback:i+lookback+1]):
                        swings.append(prices[i])
        
            return swings
        except Exception as e:
            logger.error(f"Error in _find_swing_points: {e}")
            raise
    
    def _cluster_levels(
        self,
        levels: List[float],
        tolerance: float = 0.002
    ) -> List[List[float]]:
        """Cluster nearby price levels"""
        try:
            if not levels:
                return []
        
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
        
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                    current_cluster.append(level)
                else:
                    if len(current_cluster) >= self.min_touches:
                        clusters.append(current_cluster)
                    current_cluster = [level]
        
            if len(current_cluster) >= self.min_touches:
                clusters.append(current_cluster)
        
            return clusters
        except Exception as e:
            logger.error(f"Error in _cluster_levels: {e}")
            raise
    
    def get_nearby_zones(
        self,
        current_price: float,
        zones: List[PriceZone],
        distance_pct: float = 0.01
    ) -> List[PriceZone]:
        """Get zones near current price"""
        try:
            nearby = []
        
            for zone in zones:
                zone_distance = min(
                    abs(current_price - zone.price_low),
                    abs(current_price - zone.price_high)
                ) / current_price
            
                if zone_distance <= distance_pct:
                    nearby.append(zone)
        
            return nearby
        except Exception as e:
            logger.error(f"Error in get_nearby_zones: {e}")
            raise


class EntryOptimizer:
    """
    Master entry optimization system.
    
    Combines pullback detection, zone analysis, and timing.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.pullback = PullbackDetector(self.config.get('pullback', {}))
            self.zones = LiquidityZoneFinder(self.config.get('zones', {}))
        
            # Entry quality thresholds
            self.excellent_rr = self.config.get('excellent_rr', 3.0)
            self.good_rr = self.config.get('good_rr', 2.0)
            self.min_rr = self.config.get('min_rr', 1.5)
        
            logger.info("EntryOptimizer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_entry(
        self,
        symbol: str,
        direction: str,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        stop_loss: float,
        take_profit: float
    ) -> EntryOpportunity:
        """
        Analyze entry opportunity quality.
        
        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            highs: High prices
            lows: Low prices
            closes: Close prices
            stop_loss: Proposed stop loss
            take_profit: Proposed take profit
        
        Returns:
            EntryOpportunity with analysis
        """
        try:
            current_price = closes[-1]
            reasons = []
        
            # 1. Check pullback status
            is_pullback, pullback_target, pullback_reason = self.pullback.detect_pullback(
                direction, highs, lows, closes
            )
            reasons.append(pullback_reason)
        
            # 2. Find nearby zones
            price_zones = self.zones.find_zones(highs, lows, closes)
            nearby = self.zones.get_nearby_zones(current_price, price_zones)
        
            # 3. Check if entering at bad level
            entering_at_resistance = False
            entering_at_support = False
        
            for zone in nearby:
                if zone.zone_type == ZoneType.RESISTANCE:
                    if direction == 'BUY' and zone.price_low <= current_price <= zone.price_high:
                        entering_at_resistance = True
                        reasons.append(f"Warning: Entering BUY at resistance ({zone.midpoint:.5f})")
                elif zone.zone_type == ZoneType.SUPPORT:
                    if direction == 'SELL' and zone.price_low <= current_price <= zone.price_high:
                        entering_at_support = True
                        reasons.append(f"Warning: Entering SELL at support ({zone.midpoint:.5f})")
        
            # 4. Calculate risk/reward
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = reward / risk if risk > 0 else 0
        
            # 5. Determine optimal entry
            if is_pullback:
                optimal_entry = pullback_target or current_price
            else:
                optimal_entry = current_price
        
            # 6. Determine entry quality
            if risk_reward >= self.excellent_rr and is_pullback and not entering_at_resistance:
                quality = EntryQuality.EXCELLENT
            elif risk_reward >= self.good_rr and (is_pullback or not entering_at_resistance):
                quality = EntryQuality.GOOD
            elif risk_reward >= self.min_rr:
                quality = EntryQuality.ACCEPTABLE
            elif entering_at_resistance or entering_at_support:
                quality = EntryQuality.AVOID
                reasons.append("Avoid: Poor entry location")
            else:
                quality = EntryQuality.POOR
        
            # 7. Determine if should wait
            wait_for_pullback = not is_pullback and quality != EntryQuality.EXCELLENT
        
            if wait_for_pullback:
                reasons.append("Recommendation: Wait for pullback")
        
            return EntryOpportunity(
                symbol=symbol,
                direction=direction,
                current_price=current_price,
                optimal_entry=optimal_entry,
                entry_quality=quality,
                wait_for_pullback=wait_for_pullback,
                pullback_target=pullback_target,
                nearby_zones=nearby,
                risk_reward=risk_reward,
                reasons=reasons
            )
        except Exception as e:
            logger.error(f"Error in analyze_entry: {e}")
            raise
    
    def should_enter_now(
        self,
        opportunity: EntryOpportunity
    ) -> Tuple[bool, str]:
        """
        Determine if should enter trade now.
        
        Returns:
            Tuple of (should_enter, reason)
        """
        try:
            if opportunity.entry_quality == EntryQuality.AVOID:
                return False, "Entry quality too poor"
        
            if opportunity.entry_quality == EntryQuality.EXCELLENT:
                return True, "Excellent entry opportunity"
        
            if opportunity.wait_for_pullback:
                return False, f"Wait for pullback to {opportunity.pullback_target:.5f}"
        
            if opportunity.entry_quality in [EntryQuality.GOOD, EntryQuality.ACCEPTABLE]:
                return True, f"Entry quality: {opportunity.entry_quality.value}"
        
            return False, "Entry conditions not met"
        except Exception as e:
            logger.error(f"Error in should_enter_now: {e}")
            raise
    
    def get_improved_entry(
        self,
        direction: str,
        current_price: float,
        atr: float
    ) -> Tuple[float, float]:
        """
        Get improved entry price using limit order.
        
        Returns:
            Tuple of (limit_price, timeout_seconds)
        """
        # Place limit order slightly better than current price
        try:
            improvement = atr * 0.2  # 20% of ATR
        
            if direction == 'BUY':
                limit_price = current_price - improvement
            else:
                limit_price = current_price + improvement
        
            # Timeout for limit order (5 minutes)
            timeout = 300
        
            return limit_price, timeout
        except Exception as e:
            logger.error(f"Error in get_improved_entry: {e}")
            raise
