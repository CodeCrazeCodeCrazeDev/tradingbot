"""
DeepChart Market Memory & Learned S/R Engine

Combines:
- Market Memory Decay Map (Concept 6)
- Learned Support/Resistance (Concept 12)
- Micro-Trend Vectors (Concept 8)

Tracks price levels with memory decay and learns reaction probabilities.

Math:
    strength = initial_strength × exp(-λ × time) × exp(-μ × volatility_change)
    reaction_prob = historical_reactions / total_tests
    
    micro_trend_direction = sign(EMA_short - EMA_long)
    micro_trend_magnitude = |EMA_short - EMA_long| / ATR

Performance Budget:
    - Update: O(N) where N = number of levels
    - Memory: O(max_levels)
    - Latency: <0.5ms per update
"""

import numpy as np
from collections import deque
from typing import List, Optional, Dict
import time
import logging

from .market_intelligence_core import (
    MarketMemoryLevel,
    LearnedSupportResistance,
    MicroTrendVector,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class MarketMemoryEngine:
    """
    Tracks price levels with memory decay.
    
    Levels weaken over time and volatility.
    Key insight: Old levels in low-vol environment may still be strong,
    but old levels after high-vol period are likely broken.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        try:
            self.config = config
            self._memory_levels: List[MarketMemoryLevel] = []
            self._price_history = deque(maxlen=500)
            self._volatility_history = deque(maxlen=100)
            self._bar_count = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, price: float, volume: float) -> List[MarketMemoryLevel]:
        """
        Update market memory levels.
        
        Args:
            price: Current price
            volume: Trade volume
            
        Returns:
            List of current memory levels
        """
        try:
            self._bar_count += 1
            self._price_history.append(price)
        
            # Calculate current volatility
            if len(self._price_history) >= 20:
                prices = np.array(self._price_history)
                vol = np.std(np.diff(prices[-20:]))
                self._volatility_history.append(vol)
        
            # Check for new significant levels
            self._detect_new_levels(price, volume)
        
            # Update existing levels
            self._update_levels(price)
        
            # Decay all levels
            self._decay_levels()
        
            # Prune weak levels
            self._prune_levels()
        
            return self._memory_levels
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _detect_new_levels(self, price: float, volume: float):
        """
        Detect new significant price levels.
        
        Looks for local extrema (swing highs/lows).
        """
        try:
            if len(self._price_history) < 20:
                return
        
            prices = np.array(self._price_history)
        
            # Detect local extrema (need at least 5 bars)
            if len(prices) >= 5:
                # Local high (resistance)
                if (prices[-3] > prices[-5] and prices[-3] > prices[-4] and
                    prices[-3] > prices[-2] and prices[-3] > prices[-1]):
                    self._add_level(prices[-3], volume, 'resistance')
            
                # Local low (support)
                if (prices[-3] < prices[-5] and prices[-3] < prices[-4] and
                    prices[-3] < prices[-2] and prices[-3] < prices[-1]):
                    self._add_level(prices[-3], volume, 'support')
        except Exception as e:
            logger.error(f"Error in _detect_new_levels: {e}")
            raise
    
    def _add_level(self, price: float, volume: float, level_type: str):
        """Add new memory level."""
        # Check if level already exists nearby
        try:
            for level in self._memory_levels:
                if abs(level.price - price) < price * 0.001:
                    # Reinforce existing level
                    level.reaction_count += 1
                    level.current_strength = min(1.0, level.current_strength + 0.1)
                    level.last_reaction_time = time.time()
                    return
        
            # Create new level
            current_vol = self._volatility_history[-1] if self._volatility_history else 0.01
        
            level = MarketMemoryLevel(
                price=price,
                initial_strength=min(1.0, volume / 1000),
                current_strength=min(1.0, volume / 1000),
                creation_time=time.time(),
                last_reaction_time=time.time(),
                reaction_count=1,
                reaction_probability=0.5,
                volatility_at_creation=current_vol,
                memory_half_life_bars=self.config.memory_decay_halflife,
                level_type=level_type,
                strength_decay=0.0
            )
        
            self._memory_levels.append(level)
        except Exception as e:
            logger.error(f"Error in _add_level: {e}")
            raise
    
    def _update_levels(self, price: float):
        """Update levels based on price interaction."""
        try:
            for level in self._memory_levels:
                distance = abs(price - level.price) / level.price
            
                # Price touched level
                if distance < 0.001:
                    level.reaction_count += 1
                    level.last_reaction_time = time.time()
                
                    # Update reaction probability (EMA)
                    alpha = 0.1
                    level.reaction_probability = alpha + (1 - alpha) * level.reaction_probability
        except Exception as e:
            logger.error(f"Error in _update_levels: {e}")
            raise
    
    def _decay_levels(self):
        """
        Apply decay to all levels.
        
        Decay = f(time, volatility_change)
        """
        try:
            current_vol = self._volatility_history[-1] if self._volatility_history else 0.01
        
            for level in self._memory_levels:
                # Time decay (exponential)
                time_factor = 0.5 ** (1 / level.memory_half_life_bars)
            
                # Volatility decay (more decay if vol increased since creation)
                vol_ratio = current_vol / (level.volatility_at_creation + 1e-8)
                vol_factor = 1.0 / (1 + max(0, vol_ratio - 1))
            
                # Apply decay
                level.current_strength *= time_factor * vol_factor
                level.strength_decay = 1 - level.current_strength / (level.initial_strength + 1e-8)
        except Exception as e:
            logger.error(f"Error in _decay_levels: {e}")
            raise
    
    def _prune_levels(self):
        """Remove weak levels."""
        try:
            self._memory_levels = [
                level for level in self._memory_levels
                if level.current_strength > 0.05
            ]
        
            # Keep only top N by strength
            if len(self._memory_levels) > self.config.max_memory_levels:
                self._memory_levels.sort(key=lambda x: x.current_strength, reverse=True)
                self._memory_levels = self._memory_levels[:self.config.max_memory_levels]
        except Exception as e:
            logger.error(f"Error in _prune_levels: {e}")
            raise
    
    def get_nearest_support(self, price: float) -> Optional[MarketMemoryLevel]:
        """Get nearest support level below price."""
        try:
            supports = [l for l in self._memory_levels 
                       if l.level_type == 'support' and l.price < price]
            if not supports:
                return None
            return max(supports, key=lambda x: x.price)
        except Exception as e:
            logger.error(f"Error in get_nearest_support: {e}")
            raise
    
    def get_nearest_resistance(self, price: float) -> Optional[MarketMemoryLevel]:
        """Get nearest resistance level above price."""
        try:
            resistances = [l for l in self._memory_levels 
                          if l.level_type == 'resistance' and l.price > price]
            if not resistances:
                return None
            return min(resistances, key=lambda x: x.price)
        except Exception as e:
            logger.error(f"Error in get_nearest_resistance: {e}")
            raise
    
    def reset(self):
        """Reset engine state."""
        try:
            self._memory_levels.clear()
            self._price_history.clear()
            self._volatility_history.clear()
            self._bar_count = 0
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


class LearnedSREngine:
    """
    ML-learned support/resistance with reaction probabilities.
    
    Unlike traditional S/R (fixed pivots), this learns actual
    reaction probability from historical data.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        try:
            self.config = config
            self._levels: List[LearnedSupportResistance] = []
            self._price_history = deque(maxlen=1000)
            self._reaction_history: Dict[float, List[bool]] = {}  # level -> [reacted, ...]
            self._bar_count = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, price: float, volume: float) -> List[LearnedSupportResistance]:
        """
        Update learned S/R levels.
        
        Args:
            price: Current price
            volume: Trade volume
            
        Returns:
            List of learned S/R levels
        """
        try:
            self._bar_count += 1
            self._price_history.append(price)
        
            if len(self._price_history) < 50:
                return []
        
            # Detect potential levels from volume profile
            self._detect_levels_from_volume()
        
            # Update reaction tracking
            self._track_reactions(price)
        
            # Update reaction probabilities
            self._update_probabilities()
        
            # Decay levels
            self._decay_levels()
        
            # Prune weak levels
            self._prune_levels()
        
            return self._levels
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _detect_levels_from_volume(self):
        """
        Detect S/R levels from volume profile.
        
        High volume nodes = potential S/R.
        """
        try:
            prices = np.array(self._price_history)
        
            # Create price bins
            price_min, price_max = np.min(prices), np.max(prices)
            if price_max - price_min < price_min * 0.001:
                return
        
            n_bins = 20
            bins = np.linspace(price_min, price_max, n_bins + 1)
        
            # Count price touches in each bin
            hist, _ = np.histogram(prices, bins=bins)
        
            # Find peaks (high volume nodes)
            for i in range(1, n_bins - 1):
                if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                    level_price = (bins[i] + bins[i+1]) / 2
                
                    # Check if level exists
                    exists = False
                    for level in self._levels:
                        if abs(level.price - level_price) < level_price * 0.002:
                            exists = True
                            break
                
                    if not exists:
                        # Determine type based on recent price action
                        recent_price = prices[-1]
                        level_type = 'support' if level_price < recent_price else 'resistance'
                    
                        self._levels.append(LearnedSupportResistance(
                            price=level_price,
                            level_type=level_type,
                            reaction_probability=0.5,
                            expected_reaction_magnitude=0.001,
                            confidence=0.3,
                            historical_reactions=0,
                            last_test_bars=0,
                            strength_decay=0.0
                        ))
                    
                        self._reaction_history[level_price] = []
        except Exception as e:
            logger.error(f"Error in _detect_levels_from_volume: {e}")
            raise
    
    def _track_reactions(self, price: float):
        """Track price reactions at each level."""
        try:
            for level in self._levels:
                distance = abs(price - level.price) / level.price
            
                # Price is testing level
                if distance < 0.002:
                    level.last_test_bars = 0
                
                    # Check if price reacted (bounced)
                    if len(self._price_history) >= 3:
                        prices = list(self._price_history)[-3:]
                    
                        # Approaching from below (support test)
                        if level.level_type == 'support':
                            reacted = prices[-1] > prices[-2]
                        else:  # Resistance test
                            reacted = prices[-1] < prices[-2]
                    
                        # Record reaction
                        if level.price in self._reaction_history:
                            self._reaction_history[level.price].append(reacted)
                            level.historical_reactions += 1
                else:
                    level.last_test_bars += 1
        except Exception as e:
            logger.error(f"Error in _track_reactions: {e}")
            raise
    
    def _update_probabilities(self):
        """Update reaction probabilities from historical data."""
        try:
            for level in self._levels:
                if level.price in self._reaction_history:
                    reactions = self._reaction_history[level.price]
                    if len(reactions) >= 3:
                        level.reaction_probability = np.mean(reactions)
                        level.confidence = min(1.0, len(reactions) / 10)
        except Exception as e:
            logger.error(f"Error in _update_probabilities: {e}")
            raise
    
    def _decay_levels(self):
        """Apply decay to levels."""
        try:
            decay_rate = 0.99
        
            for level in self._levels:
                # Decay confidence if not tested recently
                if level.last_test_bars > 50:
                    level.confidence *= decay_rate
            
                level.strength_decay = 1 - level.confidence
        except Exception as e:
            logger.error(f"Error in _decay_levels: {e}")
            raise
    
    def _prune_levels(self):
        """Remove weak levels."""
        try:
            self._levels = [l for l in self._levels if l.confidence > 0.1]
        
            # Keep only top N
            if len(self._levels) > self.config.max_memory_levels:
                self._levels.sort(key=lambda x: x.confidence, reverse=True)
                self._levels = self._levels[:self.config.max_memory_levels]
        except Exception as e:
            logger.error(f"Error in _prune_levels: {e}")
            raise
    
    def get_levels_in_range(self, price_low: float, price_high: float) -> List[LearnedSupportResistance]:
        """Get all levels in price range."""
        return [l for l in self._levels if price_low <= l.price <= price_high]
    
    def reset(self):
        """Reset engine state."""
        try:
            self._levels.clear()
            self._price_history.clear()
            self._reaction_history.clear()
            self._bar_count = 0
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


class MicroTrendVectorEngine:
    """
    Computes micro-trend as vector field.
    
    Each point has direction, magnitude, acceleration, divergence, curl.
    This replaces traditional indicator lines with a richer representation.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        try:
            self.config = config
            self._price_history = deque(maxlen=200)
            self._vectors: List[MicroTrendVector] = []
            self._bar_count = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, price: float) -> List[MicroTrendVector]:
        """
        Update micro-trend vectors.
        
        Args:
            price: Current price
            
        Returns:
            List of micro-trend vectors
        """
        try:
            self._bar_count += 1
            self._price_history.append(price)
        
            if len(self._price_history) < self.config.micro_trend_window:
                return []
        
            prices = np.array(self._price_history)
        
            # Calculate EMAs at different scales
            ema_short = self._ema(prices, 5)
            ema_medium = self._ema(prices, 20)
            ema_long = self._ema(prices, 50) if len(prices) >= 50 else ema_medium
        
            # ATR for normalization
            atr = np.mean(np.abs(np.diff(prices[-20:]))) if len(prices) >= 20 else 1.0
            if atr < 1e-8:
                atr = price * 0.001
        
            # Direction [-1, 1]
            direction = np.sign(ema_short - ema_medium)
        
            # Magnitude [0, 1] (normalized by ATR)
            magnitude = min(1.0, abs(ema_short - ema_medium) / (atr + 1e-8))
        
            # Acceleration (rate of change of momentum)
            if len(self._vectors) > 0:
                prev_momentum = self._vectors[-1].direction * self._vectors[-1].magnitude
                curr_momentum = direction * magnitude
                acceleration = curr_momentum - prev_momentum
            else:
                acceleration = 0.0
        
            # Divergence from macro trend
            macro_direction = np.sign(ema_short - ema_long)
            divergence = float(direction - macro_direction)
        
            # Curl (trend reversal indicator)
            if len(self._vectors) >= 2:
                curl = self._vectors[-1].direction - self._vectors[-2].direction
            else:
                curl = 0.0
        
            # Confidence based on consistency
            confidence = self._calculate_confidence(prices)
        
            vector = MicroTrendVector(
                price=price,
                time_index=self._bar_count,
                direction=float(direction),
                magnitude=float(magnitude),
                acceleration=float(acceleration),
                divergence=divergence,
                curl=float(curl),
                confidence=confidence
            )
        
            self._vectors.append(vector)
        
            # Keep only recent vectors
            if len(self._vectors) > 100:
                self._vectors = self._vectors[-100:]
        
            return self._vectors
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA."""
        try:
            if len(prices) < period:
                return prices[-1]
        
            alpha = 2 / (period + 1)
            ema = prices[-period]
        
            for p in prices[-period+1:]:
                ema = alpha * p + (1 - alpha) * ema
        
            return ema
        except Exception as e:
            logger.error(f"Error in _ema: {e}")
            raise
    
    def _calculate_confidence(self, prices: np.ndarray) -> float:
        """
        Calculate confidence based on trend consistency.
        
        Consistent direction = high confidence.
        """
        try:
            if len(prices) < 10:
                return 0.3
        
            # Check direction consistency
            changes = np.diff(prices[-10:])
            positive = np.sum(changes > 0)
            negative = np.sum(changes < 0)
        
            # More consistent = higher confidence
            consistency = abs(positive - negative) / len(changes)
        
            return min(1.0, 0.3 + consistency * 0.7)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def get_current_trend(self) -> Optional[MicroTrendVector]:
        """Get most recent trend vector."""
        return self._vectors[-1] if self._vectors else None
    
    def get_trend_strength(self) -> float:
        """Get overall trend strength."""
        try:
            if not self._vectors:
                return 0.0
        
            # Average magnitude of recent vectors
            recent = self._vectors[-10:] if len(self._vectors) >= 10 else self._vectors
            return np.mean([v.magnitude for v in recent])
        except Exception as e:
            logger.error(f"Error in get_trend_strength: {e}")
            raise
    
    def reset(self):
        """Reset engine state."""
        try:
            self._price_history.clear()
            self._vectors.clear()
            self._bar_count = 0
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
