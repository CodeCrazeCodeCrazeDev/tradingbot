"""
DeepChart Friction Engine - Market Micro-Friction Map

Computes market micro-friction map from L1 data.
Friction = resistance to price movement at each level.

High friction = price absorbed, low slippage
Low friction = price moves easily, potential slippage

Math:
    friction_i = (volume_absorbed_i / volume_total) × (1 - |price_change_i| / expected_change)
    absorption = Σ(volume × I(price_stayed_at_level))
    slippage_est = mean(|actual_fill - expected_fill|) at level

Performance Budget:
    - Update: O(1) per tick
    - Memory: O(N) where N = max_friction_points
    - Latency: <0.5ms per update
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional
import logging

from .market_intelligence_core import (
    MicroFrictionPoint,
    FrictionZone,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class MicroFrictionEngine:
    """
    Computes market micro-friction map from L1 data.
    
    Key insight: Price levels where volume is absorbed without price movement
    indicate hidden liquidity and low slippage zones.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        try:
            self.config = config
            self.friction_points: Dict[float, MicroFrictionPoint] = {}
            self._price_history = deque(maxlen=1000)
            self._volume_history = deque(maxlen=1000)
            self._trade_history = deque(maxlen=1000)
            self._bar_count = 0
            self._atr = 0.001  # Initial ATR estimate
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, price: float, volume: float, bid: float, ask: float,
               timestamp: float) -> List[MicroFrictionPoint]:
        """
        Update friction map with new data.
        
        Args:
            price: Current price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            timestamp: Unix timestamp
            
        Returns:
            List of current friction points
        """
        try:
            self._bar_count += 1
            self._price_history.append(price)
            self._volume_history.append(volume)
            self._trade_history.append({
                'price': price, 'volume': volume, 'bid': bid, 'ask': ask,
                'timestamp': timestamp, 'spread': ask - bid
            })
        
            # Update ATR
            self._update_atr()
        
            # Quantize price to levels
            price_level = self._quantize_price(price)
        
            # Update or create friction point
            if price_level in self.friction_points:
                self._update_friction_point(price_level, price, volume)
            else:
                self._create_friction_point(price_level, price, volume)
        
            # Decay all friction points
            self._decay_friction_points()
        
            # Prune old points
            self._prune_friction_points()
        
            return list(self.friction_points.values())
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _update_atr(self):
        """Update ATR estimate."""
        try:
            if len(self._price_history) >= 20:
                prices = np.array(self._price_history)
                self._atr = np.mean(np.abs(np.diff(prices[-20:]))) * 2
                if self._atr < 1e-8:
                    self._atr = prices[-1] * 0.001
        except Exception as e:
            logger.error(f"Error in _update_atr: {e}")
            raise
    
    def _quantize_price(self, price: float) -> float:
        """
        Quantize price to nearest level using ATR-based grid.
        
        This creates a dynamic grid that adapts to volatility.
        """
        try:
            if self._atr < 1e-8:
                return round(price, 4)
        
            return round(price / self._atr) * self._atr
        except Exception as e:
            logger.error(f"Error in _quantize_price: {e}")
            raise
    
    def _update_friction_point(self, level: float, price: float, volume: float):
        """Update existing friction point."""
        try:
            fp = self.friction_points[level]
        
            # Calculate absorption
            price_change = abs(price - level)
            expected_change = self._atr
            absorption = volume * max(0, 1 - price_change / (expected_change + 1e-8))
        
            # Update absorption strength (EMA)
            alpha = 0.1
            fp.absorption_strength = alpha * absorption + (1 - alpha) * fp.absorption_strength
        
            # Update friction coefficient
            fp.friction_coefficient = self._calculate_friction(fp)
        
            # Update touch info
            fp.touch_count += 1
            fp.last_touch_bars = 0
            fp.decay_factor = 1.0
        
            # Update slippage estimate
            fp.slippage_estimate_bps = self._estimate_slippage(level)
        
            # Update zone type
            fp.zone_type = self._classify_zone(fp)
        
            # Update confidence
            fp.confidence = min(1.0, fp.touch_count / 10)
        except Exception as e:
            logger.error(f"Error in _update_friction_point: {e}")
            raise
    
    def _create_friction_point(self, level: float, price: float, volume: float):
        """Create new friction point."""
        try:
            fp = MicroFrictionPoint(
                price_level=level,
                friction_coefficient=0.5,
                absorption_strength=volume,
                slippage_estimate_bps=self._estimate_slippage(level),
                zone_type=FrictionZone.NEUTRAL,
                confidence=0.1,
                decay_factor=1.0,
                last_touch_bars=0,
                touch_count=1
            )
            self.friction_points[level] = fp
        except Exception as e:
            logger.error(f"Error in _create_friction_point: {e}")
            raise
    
    def _calculate_friction(self, fp: MicroFrictionPoint) -> float:
        """
        Calculate friction coefficient.
        
        Friction = f(absorption, touch_frequency)
        High absorption + high frequency = high friction
        """
        # Normalize absorption by typical volume
        try:
            if len(self._volume_history) > 0:
                avg_vol = np.mean(self._volume_history)
                absorption_factor = min(1.0, fp.absorption_strength / (avg_vol * 10 + 1))
            else:
                absorption_factor = min(1.0, fp.absorption_strength / 1000)
        
            frequency_factor = min(1.0, fp.touch_count / 20)
        
            return 0.5 * absorption_factor + 0.5 * frequency_factor
        except Exception as e:
            logger.error(f"Error in _calculate_friction: {e}")
            raise
    
    def _estimate_slippage(self, level: float) -> float:
        """
        Estimate slippage at price level in basis points.
        
        Uses historical spread data near this level.
        """
        try:
            if len(self._trade_history) < 10:
                return 5.0  # Default 5 bps
        
            # Calculate average spread near this level
            spreads = []
            for trade in self._trade_history:
                if abs(trade['price'] - level) < self._atr:
                    spreads.append(trade['spread'])
        
            if not spreads:
                return 5.0
        
            avg_spread = np.mean(spreads)
            return (avg_spread / level) * 10000  # Convert to bps
        except Exception as e:
            logger.error(f"Error in _estimate_slippage: {e}")
            raise
    
    def _classify_zone(self, fp: MicroFrictionPoint) -> FrictionZone:
        """
        Classify friction zone type based on characteristics.
        
        ABSORPTION: High friction, high volume absorbed
        RESISTANCE: High friction, price rejected
        SLIPPAGE: Low friction, high slippage expected
        VACUUM: Very low friction, liquidity void
        """
        try:
            if fp.friction_coefficient > 0.7 and fp.absorption_strength > 500:
                return FrictionZone.ABSORPTION
            elif fp.friction_coefficient > 0.5:
                return FrictionZone.RESISTANCE
            elif fp.slippage_estimate_bps > 10:
                return FrictionZone.SLIPPAGE
            elif fp.friction_coefficient < 0.2:
                return FrictionZone.VACUUM
            return FrictionZone.NEUTRAL
        except Exception as e:
            logger.error(f"Error in _classify_zone: {e}")
            raise
    
    def _decay_friction_points(self):
        """Apply decay to all friction points."""
        try:
            decay_rate = 0.5 ** (1 / self.config.memory_decay_halflife)
        
            for fp in self.friction_points.values():
                fp.last_touch_bars += 1
                fp.decay_factor *= decay_rate
                fp.friction_coefficient *= fp.decay_factor
                fp.confidence *= decay_rate
        except Exception as e:
            logger.error(f"Error in _decay_friction_points: {e}")
            raise
    
    def _prune_friction_points(self):
        """Remove old/weak friction points."""
        try:
            to_remove = []
            for level, fp in self.friction_points.items():
                if fp.confidence < 0.01 or fp.last_touch_bars > 500:
                    to_remove.append(level)
        
            for level in to_remove:
                del self.friction_points[level]
        
            # Keep only top N by confidence
            if len(self.friction_points) > self.config.max_friction_points:
                sorted_points = sorted(
                    self.friction_points.items(),
                    key=lambda x: x[1].confidence,
                    reverse=True
                )
                self.friction_points = dict(sorted_points[:self.config.max_friction_points])
        except Exception as e:
            logger.error(f"Error in _prune_friction_points: {e}")
            raise
    
    def get_friction_at_price(self, price: float) -> float:
        """Get friction coefficient at specific price."""
        try:
            level = self._quantize_price(price)
            if level in self.friction_points:
                return self.friction_points[level].friction_coefficient
            return 0.5  # Default neutral friction
        except Exception as e:
            logger.error(f"Error in get_friction_at_price: {e}")
            raise
    
    def get_slippage_zones(self, threshold_bps: float = 10.0) -> List[MicroFrictionPoint]:
        """Get zones with high slippage risk."""
        return [fp for fp in self.friction_points.values() 
                if fp.slippage_estimate_bps > threshold_bps]
    
    def get_absorption_zones(self, threshold: float = 0.7) -> List[MicroFrictionPoint]:
        """Get zones with high absorption (hidden liquidity)."""
        return [fp for fp in self.friction_points.values()
                if fp.friction_coefficient > threshold and 
                fp.zone_type == FrictionZone.ABSORPTION]
    
    def get_vacuum_zones(self) -> List[MicroFrictionPoint]:
        """Get liquidity vacuum zones."""
        return [fp for fp in self.friction_points.values()
                if fp.zone_type == FrictionZone.VACUUM]
    
    def reset(self):
        """Reset engine state."""
        try:
            self.friction_points.clear()
            self._price_history.clear()
            self._volume_history.clear()
            self._trade_history.clear()
            self._bar_count = 0
            self._atr = 0.001
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
