import logging
logger = logging.getLogger(__name__)
"""
Advanced Order Block Mitigation Tracking System

This module provides sophisticated tracking and analysis of order block mitigation
patterns, including partial mitigation, re-entry opportunities, and institutional
behavior analysis.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading

import numpy as np
import pandas as pd
from loguru import logger

from .liquidity import OrderBlock, OrderBlockType
from .market_structure import TimeFrame
from ..performance.memory_optimization import RingBuffer
import numpy
import pandas


class MitigationType(Enum):
    """Types of order block mitigation."""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    OVERSHOOT = "overshoot"
    REJECTION = "rejection"


class MitigationStrength(Enum):
    """Strength of mitigation."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXTREME = "extreme"


class ReactionType(Enum):
    """Type of price reaction at order block."""
    BOUNCE = "bounce"
    ABSORPTION = "absorption"
    BREAKTHROUGH = "breakthrough"
    CONSOLIDATION = "consolidation"


@dataclass
class MitigationEvent:
    """Represents an order block mitigation event."""
    timestamp: float
    order_block: OrderBlock
    mitigation_type: MitigationType
    mitigation_strength: MitigationStrength
    entry_price: float
    exit_price: Optional[float] = None
    max_penetration: float = 0.0
    min_penetration: float = 0.0
    volume_at_mitigation: Optional[float] = None
    reaction_type: ReactionType = ReactionType.BOUNCE
    duration_bars: int = 0
    retest_count: int = 0
    success_probability: float = 0.0


@dataclass
class OrderBlockState:
    """Tracks the current state of an order block."""
    order_block: OrderBlock
    creation_time: float
    last_test_time: Optional[float] = None
    test_count: int = 0
    mitigation_events: List[MitigationEvent] = field(default_factory=list)
    current_mitigation: Optional[MitigationEvent] = None
    strength_score: float = 1.0
    reliability_score: float = 1.0
    is_active: bool = True
    invalidation_price: Optional[float] = None


class OrderBlockTracker:
    """
    Advanced order block mitigation tracking system.
    
    Provides comprehensive monitoring of order block behavior including:
    - Partial and full mitigation detection
    - Re-entry opportunity identification
    - Institutional behavior pattern analysis
    - Success probability calculation
    """
    
    def __init__(self, 
                 partial_threshold: float = 0.5,
                 full_threshold: float = 0.8,
                 overshoot_threshold: float = 1.2,
                 max_history: int = 1000,
                 enable_ml_scoring: bool = True):
        """
        Initialize the order block tracker.
        
        Args:
            partial_threshold: Threshold for partial mitigation (0-1)
            full_threshold: Threshold for full mitigation (0-1)
            overshoot_threshold: Threshold for overshoot detection (>1)
            max_history: Maximum number of historical events to keep
            enable_ml_scoring: Enable machine learning-based scoring
        """
        self.partial_threshold = partial_threshold
        self.full_threshold = full_threshold
        self.overshoot_threshold = overshoot_threshold
        self.max_history = max_history
        self.enable_ml_scoring = enable_ml_scoring
        
        # Tracking data structures
        self.tracked_blocks: Dict[str, Dict[TimeFrame, List[OrderBlockState]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.mitigation_history: deque = deque(maxlen=max_history)
        self.performance_stats = defaultdict(int)
        
        # Price buffers for analysis
        self.price_buffers: Dict[str, Dict[TimeFrame, RingBuffer]] = defaultdict(
            lambda: defaultdict(lambda: RingBuffer(200))
        )
        
        # Event callbacks
        self.event_callbacks: List[Callable[[str, MitigationEvent], None]] = []
        
        # Threading
        self.lock = threading.RLock()
        
        # ML model placeholder (would be trained on historical data)
        self.ml_model = None
        
    def register_order_block(self, symbol: str, timeframe: TimeFrame, 
                           order_block: OrderBlock) -> str:
        """
        Register a new order block for tracking.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            order_block: Order block to track
            
        Returns:
            Unique identifier for the tracked order block
        """
        with self.lock:
            block_id = f"{symbol}_{timeframe.name}_{order_block.start_idx}_{int(time.time())}"
            
            # Create order block state
            state = OrderBlockState(
                order_block=order_block,
                creation_time=time.time(),
                strength_score=order_block.strength,
                invalidation_price=self._calculate_invalidation_price(order_block)
            )
            
            # Add to tracking
            self.tracked_blocks[symbol][timeframe].append(state)
            
            # Update performance stats
            self.performance_stats['blocks_registered'] += 1
            
            logger.info(f"Registered order block {block_id} for tracking")
            return block_id
    
    def update_price(self, symbol: str, timeframe: TimeFrame, 
                    price: float, volume: Optional[float] = None,
                    timestamp: Optional[float] = None):
        """
        Update price data and check for mitigation events.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            price: Current price
            volume: Current volume
            timestamp: Price timestamp
        """
        with self.lock:
            # Update price buffer
            ts = int((timestamp or time.time()) * 1000)
            self.price_buffers[symbol][timeframe].append(price, ts)
            
            # Check all tracked blocks for this symbol/timeframe
            active_blocks = [
                state for state in self.tracked_blocks[symbol][timeframe]
                if state.is_active
            ]
            
            for block_state in active_blocks:
                self._check_mitigation(symbol, timeframe, block_state, price, volume)
    
    def update_candle(self, symbol: str, timeframe: TimeFrame, 
                     ohlcv: Dict[str, float]):
        """
        Update with full candle data for more accurate analysis.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            ohlcv: OHLCV candle data
        """
        with self.lock:
            # Extract candle data
            open_price = ohlcv.get('open', 0.0)
            high = ohlcv.get('high', 0.0)
            low = ohlcv.get('low', 0.0)
            close = ohlcv.get('close', 0.0)
            volume = ohlcv.get('volume', 0.0)
            timestamp = ohlcv.get('timestamp', time.time())
            
            # Update price buffer with close
            ts = int(timestamp * 1000)
            self.price_buffers[symbol][timeframe].append(close, ts)
            
            # Check all tracked blocks
            active_blocks = [
                state for state in self.tracked_blocks[symbol][timeframe]
                if state.is_active
            ]
            
            for block_state in active_blocks:
                self._check_candle_mitigation(symbol, timeframe, block_state, ohlcv)
    
    def _check_mitigation(self, symbol: str, timeframe: TimeFrame, 
                         block_state: OrderBlockState, price: float, 
                         volume: Optional[float] = None):
        """Check for mitigation events on a single price update."""
        ob = block_state.order_block
        
        # Check if price is testing the order block
        is_testing = False
        penetration = 0.0
        
        if ob.type == OrderBlockType.BULLISH:
            # Bullish OB - check for price coming back down into the block
            if ob.low <= price <= ob.high:
                is_testing = True
                penetration = (ob.high - price) / (ob.high - ob.low)
        elif ob.type == OrderBlockType.BEARISH:
            # Bearish OB - check for price coming back up into the block
            if ob.low <= price <= ob.high:
                is_testing = True
                penetration = (price - ob.low) / (ob.high - ob.low)
        
        if is_testing:
            block_state.last_test_time = time.time()
            block_state.test_count += 1
            
            # Determine mitigation type and strength
            mitigation_type = self._classify_mitigation_type(penetration)
            mitigation_strength = self._classify_mitigation_strength(penetration, volume)
            
            # Create or update mitigation event
            if block_state.current_mitigation is None:
                # New mitigation event
                event = MitigationEvent(
                    timestamp=time.time(),
                    order_block=ob,
                    mitigation_type=mitigation_type,
                    mitigation_strength=mitigation_strength,
                    entry_price=price,
                    volume_at_mitigation=volume,
                    max_penetration=penetration,
                    min_penetration=penetration
                )
                
                block_state.current_mitigation = event
                block_state.mitigation_events.append(event)
                
                # Calculate success probability
                event.success_probability = self._calculate_success_probability(block_state, event)
                
                # Emit event
                self._emit_mitigation_event(symbol, event)
                
            else:
                # Update existing mitigation event
                event = block_state.current_mitigation
                event.max_penetration = max(event.max_penetration, penetration)
                event.min_penetration = min(event.min_penetration, penetration)
                event.mitigation_type = mitigation_type
                event.mitigation_strength = mitigation_strength
                event.duration_bars += 1
        
        else:
            # Price moved away from order block
            if block_state.current_mitigation is not None:
                # Close current mitigation event
                event = block_state.current_mitigation
                event.exit_price = price
                event.reaction_type = self._classify_reaction_type(block_state, price)
                
                # Update block reliability based on reaction
                self._update_block_reliability(block_state, event)
                
                # Add to history
                self.mitigation_history.append(event)
                
                # Clear current mitigation
                block_state.current_mitigation = None
                
                # Check if block should be invalidated
                if self._should_invalidate_block(block_state, price):
                    block_state.is_active = False
                    self.performance_stats['blocks_invalidated'] += 1
    
    def _check_candle_mitigation(self, symbol: str, timeframe: TimeFrame,
                               block_state: OrderBlockState, ohlcv: Dict[str, float]):
        """Check for mitigation using full candle data."""
        ob = block_state.order_block
        high = ohlcv['high']
        low = ohlcv['low']
        close = ohlcv['close']
        volume = ohlcv.get('volume', 0.0)
        
        # Check if candle interacted with order block
        block_interaction = False
        max_penetration = 0.0
        
        if ob.type == OrderBlockType.BULLISH:
            # Check if candle low touched or penetrated the bullish OB
            if low <= ob.high:
                block_interaction = True
                if low < ob.low:
                    # Full penetration
                    max_penetration = 1.0 + (ob.low - low) / (ob.high - ob.low)
                else:
                    # Partial penetration
                    max_penetration = (ob.high - low) / (ob.high - ob.low)
        
        elif ob.type == OrderBlockType.BEARISH:
            # Check if candle high touched or penetrated the bearish OB
            if high >= ob.low:
                block_interaction = True
                if high > ob.high:
                    # Full penetration
                    max_penetration = 1.0 + (high - ob.high) / (ob.high - ob.low)
                else:
                    # Partial penetration
                    max_penetration = (high - ob.low) / (ob.high - ob.low)
        
        if block_interaction:
            # Process the interaction
            mitigation_type = self._classify_mitigation_type(max_penetration)
            mitigation_strength = self._classify_mitigation_strength(max_penetration, volume)
            reaction_type = self._classify_candle_reaction(ob, ohlcv)
            
            # Create mitigation event
            event = MitigationEvent(
                timestamp=time.time(),
                order_block=ob,
                mitigation_type=mitigation_type,
                mitigation_strength=mitigation_strength,
                entry_price=low if ob.type == OrderBlockType.BULLISH else high,
                exit_price=close,
                max_penetration=max_penetration,
                volume_at_mitigation=volume,
                reaction_type=reaction_type,
                duration_bars=1
            )
            
            # Calculate success probability
            event.success_probability = self._calculate_success_probability(block_state, event)
            
            # Add to block state
            block_state.mitigation_events.append(event)
            block_state.last_test_time = time.time()
            block_state.test_count += 1
            
            # Update reliability
            self._update_block_reliability(block_state, event)
            
            # Add to history
            self.mitigation_history.append(event)
            
            # Emit event
            self._emit_mitigation_event(symbol, event)
            
            # Check for invalidation
            if self._should_invalidate_block(block_state, close):
                block_state.is_active = False
                self.performance_stats['blocks_invalidated'] += 1
    
    def _classify_mitigation_type(self, penetration: float) -> MitigationType:
        """Classify the type of mitigation based on penetration depth."""
        if penetration < 0.1:
            return MitigationType.NONE
        elif penetration < self.partial_threshold:
            return MitigationType.PARTIAL
        elif penetration < self.full_threshold:
            return MitigationType.FULL
        elif penetration > self.overshoot_threshold:
            return MitigationType.OVERSHOOT
        else:
            return MitigationType.FULL
    
    def _classify_mitigation_strength(self, penetration: float, 
                                    volume: Optional[float] = None) -> MitigationStrength:
        """Classify the strength of mitigation."""
        base_strength = penetration
        
        # Adjust for volume if available
        if volume is not None and volume > 0:
            # Higher volume increases strength
            volume_factor = min(2.0, volume / 1000)  # Normalize volume
            base_strength *= volume_factor
        
        if base_strength < 0.3:
            return MitigationStrength.WEAK
        elif base_strength < 0.6:
            return MitigationStrength.MODERATE
        elif base_strength < 1.0:
            return MitigationStrength.STRONG
        else:
            return MitigationStrength.EXTREME
    
    def _classify_reaction_type(self, block_state: OrderBlockState, exit_price: float) -> ReactionType:
        """Classify the type of price reaction at the order block."""
        ob = block_state.order_block
        event = block_state.current_mitigation
        
        if event is None:
            return ReactionType.BOUNCE
        
        entry_price = event.entry_price
        price_move = abs(exit_price - entry_price)
        block_size = ob.high - ob.low
        
        if price_move < block_size * 0.2:
            return ReactionType.CONSOLIDATION
        elif price_move > block_size * 2.0:
            return ReactionType.BREAKTHROUGH
        elif event.max_penetration > 0.8:
            return ReactionType.ABSORPTION
        else:
            return ReactionType.BOUNCE
    
    def _classify_candle_reaction(self, ob: OrderBlock, ohlcv: Dict[str, float]) -> ReactionType:
        """Classify reaction type from candle data."""
        high = ohlcv['high']
        low = ohlcv['low']
        close = ohlcv['close']
        open_price = ohlcv['open']
        
        candle_size = high - low
        body_size = abs(close - open_price)
        block_size = ob.high - ob.low
        
        # Strong rejection if long wick and small body
        if body_size < candle_size * 0.3 and candle_size > block_size * 0.5:
            return ReactionType.BOUNCE
        
        # Breakthrough if large body through the block
        if body_size > block_size and candle_size > block_size * 1.5:
            return ReactionType.BREAKTHROUGH
        
        # Absorption if price spent time in block
        if candle_size < block_size * 0.5:
            return ReactionType.ABSORPTION
        
        return ReactionType.CONSOLIDATION
    
    def _calculate_success_probability(self, block_state: OrderBlockState, 
                                     event: MitigationEvent) -> float:
        """Calculate the probability of successful reaction at the order block."""
        base_probability = 0.5
        
        # Factor in block strength
        base_probability += (block_state.strength_score - 1.0) * 0.2
        
        # Factor in block reliability
        base_probability += (block_state.reliability_score - 1.0) * 0.15
        
        # Factor in mitigation type
        type_factors = {
            MitigationType.PARTIAL: 0.1,
            MitigationType.FULL: -0.05,
            MitigationType.OVERSHOOT: -0.2,
            MitigationType.REJECTION: 0.15
        }
        base_probability += type_factors.get(event.mitigation_type, 0.0)
        
        # Factor in test count (fewer tests = higher probability)
        if block_state.test_count > 0:
            base_probability -= min(0.2, block_state.test_count * 0.05)
        
        # Use ML model if available
        if self.enable_ml_scoring and self.ml_model is not None:
            ml_features = self._extract_ml_features(block_state, event)
            ml_probability = self.ml_model.predict_proba([ml_features])[0][1]
            base_probability = (base_probability + ml_probability) / 2
        
        return max(0.0, min(1.0, base_probability))
    
    def _extract_ml_features(self, block_state: OrderBlockState, 
                           event: MitigationEvent) -> List[float]:
        """Extract features for ML model."""
        ob = block_state.order_block
        
        features = [
            ob.strength,
            block_state.reliability_score,
            block_state.test_count,
            event.max_penetration,
            float(event.mitigation_type == MitigationType.PARTIAL),
            float(event.mitigation_type == MitigationType.FULL),
            float(event.reaction_type == ReactionType.BOUNCE),
            event.volume_at_mitigation or 0.0,
            time.time() - block_state.creation_time,  # Age of block
            len(block_state.mitigation_events)  # Number of previous events
        ]
        
        return features
    
    def _update_block_reliability(self, block_state: OrderBlockState, event: MitigationEvent):
        """Update the reliability score of an order block based on its performance."""
        # Positive factors
        if event.reaction_type == ReactionType.BOUNCE:
            block_state.reliability_score += 0.1
        elif event.reaction_type == ReactionType.ABSORPTION:
            block_state.reliability_score += 0.05
        
        # Negative factors
        if event.reaction_type == ReactionType.BREAKTHROUGH:
            block_state.reliability_score -= 0.15
        elif event.mitigation_type == MitigationType.OVERSHOOT:
            block_state.reliability_score -= 0.1
        
        # Clamp reliability score
        block_state.reliability_score = max(0.1, min(2.0, block_state.reliability_score))
    
    def _calculate_invalidation_price(self, ob: OrderBlock) -> float:
        """Calculate the price level at which the order block becomes invalid."""
        if ob.type == OrderBlockType.BULLISH:
            # Bullish OB invalidated if price closes significantly below the low
            return ob.low - (ob.high - ob.low) * 0.1
        else:
            # Bearish OB invalidated if price closes significantly above the high
            return ob.high + (ob.high - ob.low) * 0.1
    
    def _should_invalidate_block(self, block_state: OrderBlockState, current_price: float) -> bool:
        """Check if an order block should be invalidated."""
        if block_state.invalidation_price is None:
            return False
        
        ob = block_state.order_block
        
        if ob.type == OrderBlockType.BULLISH:
            return current_price < block_state.invalidation_price
        else:
            return current_price > block_state.invalidation_price
    
    def _emit_mitigation_event(self, symbol: str, event: MitigationEvent):
        """Emit a mitigation event to all registered callbacks."""
        try:
            for callback in self.event_callbacks:
                callback(symbol, event)
            
            self.performance_stats['events_emitted'] += 1
            
        except Exception as e:
            logger.error(f"Error emitting mitigation event: {e}")
    
    def add_event_callback(self, callback: Callable[[str, MitigationEvent], None]):
        """Add a callback for mitigation events."""
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[str, MitigationEvent], None]):
        """Remove a callback for mitigation events."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def get_active_blocks(self, symbol: str, timeframe: TimeFrame) -> List[OrderBlockState]:
        """Get all active order blocks for a symbol and timeframe."""
        with self.lock:
            return [
                state for state in self.tracked_blocks[symbol][timeframe]
                if state.is_active
            ]
    
    def get_block_statistics(self, symbol: str, timeframe: TimeFrame) -> Dict[str, Any]:
        """Get statistics for order blocks of a specific symbol and timeframe."""
        with self.lock:
            blocks = self.tracked_blocks[symbol][timeframe]
            
            if not blocks:
                return {}
            
            active_blocks = [b for b in blocks if b.is_active]
            total_events = sum(len(b.mitigation_events) for b in blocks)
            
            # Calculate success rates by reaction type
            reaction_stats = defaultdict(list)
            for block in blocks:
                for event in block.mitigation_events:
                    reaction_stats[event.reaction_type].append(event.success_probability)
            
            return {
                'total_blocks': len(blocks),
                'active_blocks': len(active_blocks),
                'total_mitigation_events': total_events,
                'avg_reliability_score': np.mean([b.reliability_score for b in blocks]),
                'avg_test_count': np.mean([b.test_count for b in blocks]),
                'reaction_type_stats': {
                    reaction.value: {
                        'count': len(probs),
                        'avg_success_probability': np.mean(probs) if probs else 0.0
                    }
                    for reaction, probs in reaction_stats.items()
                }
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return dict(self.performance_stats)
    
    def cleanup_old_blocks(self, max_age_hours: float = 24.0):
        """Clean up old inactive order blocks."""
        with self.lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            
            for symbol in self.tracked_blocks:
                for timeframe in self.tracked_blocks[symbol]:
                    blocks = self.tracked_blocks[symbol][timeframe]
                    
                    # Keep only recent or active blocks
                    filtered_blocks = []
                    for block in blocks:
                        age = current_time - block.creation_time
                        if block.is_active or age < max_age_seconds:
                            filtered_blocks.append(block)
                        else:
                            cleaned_count += 1
                    
                    self.tracked_blocks[symbol][timeframe] = filtered_blocks
            
            logger.info(f"Cleaned up {cleaned_count} old order blocks")
            return cleaned_count


# Utility functions
def create_order_block_tracker(enable_ml: bool = False) -> OrderBlockTracker:
    """Create an order block tracker with default settings."""
    return OrderBlockTracker(
        partial_threshold=0.5,
        full_threshold=0.8,
        overshoot_threshold=1.2,
        max_history=1000,
        enable_ml_scoring=enable_ml
    )


if __name__ == "__main__":
    # Example usage
    
    def mitigation_callback(symbol: str, event: MitigationEvent):
        print(f"Mitigation event for {symbol}: {event.mitigation_type.value} "
              f"at {event.entry_price:.5f} with {event.success_probability:.2%} success probability")
    
    # Create tracker
    tracker = create_order_block_tracker()
    tracker.add_event_callback(mitigation_callback)
    
    # Create sample order block
    ob = OrderBlock(
        type=OrderBlockType.BULLISH,
        start_idx=100,
        end_idx=100,
        high=1.1050,
        low=1.1030,
        open=1.1035,
        close=1.1045,
        strength=1.5,
        timeframe=TimeFrame.M15
    )
    
    # Register for tracking
    block_id = tracker.register_order_block('EURUSD', TimeFrame.M15, ob)
    
    # Simulate price updates
    prices = [1.1040, 1.1035, 1.1032, 1.1038, 1.1045, 1.1050, 1.1055]
    
    for price in prices:
        tracker.update_price('EURUSD', TimeFrame.M15, price, volume=500)
        time.sleep(0.1)
    
    # Get statistics
    stats = tracker.get_block_statistics('EURUSD', TimeFrame.M15)
    logger.info(f"Block statistics: {stats}")
    
    perf_stats = tracker.get_performance_stats()
    logger.info(f"Performance statistics: {perf_stats}")
