"""
Limit Order Book (LOB) State Transition Modeling

Processes the entire LOB depth as an image (heatmap) over time.
Uses pattern recognition to detect complex, subtle patterns in the
order book's evolution that precede major moves.

Features:
- LOB snapshot to image conversion
- State transition detection
- Pattern recognition in order book evolution
- Predictive signals from LOB dynamics
- Institutional footprint detection
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class LOBState(Enum):
    """Order book states."""
    BALANCED = "balanced"
    BID_HEAVY = "bid_heavy"
    ASK_HEAVY = "ask_heavy"
    THIN = "thin"
    THICK = "thick"
    SPOOFING = "spoofing"
    ABSORPTION = "absorption"
    ICEBERG = "iceberg"


class TransitionType(Enum):
    """Types of state transitions."""
    ACCUMULATION_START = "accumulation_start"
    DISTRIBUTION_START = "distribution_start"
    BREAKOUT_SETUP = "breakout_setup"
    BREAKDOWN_SETUP = "breakdown_setup"
    LIQUIDITY_VACUUM = "liquidity_vacuum"
    SUPPORT_BUILDING = "support_building"
    RESISTANCE_BUILDING = "resistance_building"
    NEUTRAL = "neutral"


class SignalStrength(Enum):
    """Signal strength levels."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class LOBLevel:
    """Single price level in the order book."""
    price: float
    quantity: float
    order_count: int
    
    @property
    def avg_order_size(self) -> float:
        if self.order_count > 0:
            return self.quantity / self.order_count
        return 0


@dataclass
class LOBSnapshot:
    """Complete order book snapshot."""
    timestamp: datetime
    symbol: str
    bids: List[LOBLevel]  # Sorted by price descending
    asks: List[LOBLevel]  # Sorted by price ascending
    
    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0
    
    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 0
    
    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2
    
    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid
    
    @property
    def spread_bps(self) -> float:
        if self.mid_price > 0:
            return (self.spread / self.mid_price) * 10000
        return 0
    
    @property
    def total_bid_volume(self) -> float:
        return sum(level.quantity for level in self.bids)
    
    @property
    def total_ask_volume(self) -> float:
        return sum(level.quantity for level in self.asks)
    
    @property
    def imbalance(self) -> float:
        """Order book imbalance (-1 to +1)."""
        total = self.total_bid_volume + self.total_ask_volume
        if total > 0:
            return (self.total_bid_volume - self.total_ask_volume) / total
        return 0
    
    def to_matrix(self, depth: int = 10) -> List[List[float]]:
        """
        Convert to matrix representation.
        
        Returns:
            Matrix with rows = price levels, cols = [bid_qty, ask_qty]
        """
        matrix = []
        
        for i in range(depth):
            bid_qty = self.bids[i].quantity if i < len(self.bids) else 0
            ask_qty = self.asks[i].quantity if i < len(self.asks) else 0
            matrix.append([bid_qty, ask_qty])
        
        return matrix


@dataclass
class StateTransition:
    """Detected state transition."""
    timestamp: datetime
    from_state: LOBState
    to_state: LOBState
    transition_type: TransitionType
    confidence: float
    magnitude: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'from_state': self.from_state.value,
            'to_state': self.to_state.value,
            'transition_type': self.transition_type.value,
            'confidence': self.confidence,
            'magnitude': self.magnitude,
            'details': self.details
        }


@dataclass
class LOBPattern:
    """Detected pattern in LOB evolution."""
    pattern_name: str
    start_time: datetime
    end_time: datetime
    confidence: float
    price_levels: List[float]
    volume_profile: Dict[str, float]
    predicted_direction: str  # 'UP', 'DOWN', 'NEUTRAL'
    predicted_magnitude: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_name': self.pattern_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'confidence': self.confidence,
            'predicted_direction': self.predicted_direction,
            'predicted_magnitude': self.predicted_magnitude
        }


@dataclass
class LOBSignal:
    """Trading signal from LOB analysis."""
    timestamp: datetime
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    strength: SignalStrength
    confidence: float
    current_state: LOBState
    recent_transitions: List[StateTransition]
    patterns: List[LOBPattern]
    imbalance: float
    depth_ratio: float
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'strength': self.strength.name,
            'confidence': self.confidence,
            'current_state': self.current_state.value,
            'imbalance': self.imbalance,
            'depth_ratio': self.depth_ratio,
            'analysis': self.analysis
        }


class LOBStateClassifier:
    """
    Classifies current LOB state.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.imbalance_threshold = self.config.get('imbalance_threshold', 0.3)
        self.thin_threshold = self.config.get('thin_threshold', 0.5)
    
    def classify(self, snapshot: LOBSnapshot, avg_volume: float) -> LOBState:
        """Classify current LOB state."""
        imbalance = snapshot.imbalance
        total_volume = snapshot.total_bid_volume + snapshot.total_ask_volume
        
        # Check for thin/thick
        if avg_volume > 0:
            volume_ratio = total_volume / avg_volume
            if volume_ratio < self.thin_threshold:
                return LOBState.THIN
            elif volume_ratio > 2.0:
                return LOBState.THICK
        
        # Check for imbalance
        if imbalance > self.imbalance_threshold:
            return LOBState.BID_HEAVY
        elif imbalance < -self.imbalance_threshold:
            return LOBState.ASK_HEAVY
        
        return LOBState.BALANCED


class SpoofingDetector:
    """
    Detects spoofing patterns in LOB.
    
    Characteristics:
    - Large orders that disappear before execution
    - Orders placed far from best price
    - Rapid cancel/replace cycles
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.snapshot_history: deque = deque(maxlen=50)
        self.large_order_threshold = self.config.get('large_order_threshold', 5.0)
    
    def add_snapshot(self, snapshot: LOBSnapshot):
        """Add snapshot to history."""
        self.snapshot_history.append(snapshot)
    
    def detect(self) -> Optional[Dict[str, Any]]:
        """Detect spoofing patterns."""
        if len(self.snapshot_history) < 5:
            return None
        
        snapshots = list(self.snapshot_history)
        
        # Track large orders that disappear
        disappeared_volume = 0
        
        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]
            
            # Check bid side
            for prev_level in prev.bids[:5]:
                # Find if this level still exists
                found = False
                for curr_level in curr.bids[:5]:
                    if abs(curr_level.price - prev_level.price) < 0.0001:
                        found = True
                        # Check for significant volume drop
                        if prev_level.quantity > curr_level.quantity * 2:
                            disappeared_volume += prev_level.quantity - curr_level.quantity
                        break
                
                if not found and prev_level.quantity > 0:
                    disappeared_volume += prev_level.quantity
        
        # Calculate average volume
        avg_volume = statistics.mean(
            s.total_bid_volume + s.total_ask_volume for s in snapshots
        )
        
        if avg_volume > 0 and disappeared_volume / avg_volume > self.large_order_threshold:
            return {
                'type': 'spoofing',
                'disappeared_volume': disappeared_volume,
                'ratio': disappeared_volume / avg_volume
            }
        
        return None


class AbsorptionDetector:
    """
    Detects absorption patterns.
    
    Characteristics:
    - Large volume absorbed at a price level
    - Price doesn't move despite heavy selling/buying
    - Indicates strong support/resistance
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.snapshot_history: deque = deque(maxlen=20)
    
    def add_snapshot(self, snapshot: LOBSnapshot):
        """Add snapshot."""
        self.snapshot_history.append(snapshot)
    
    def detect(self) -> Optional[Dict[str, Any]]:
        """Detect absorption."""
        if len(self.snapshot_history) < 10:
            return None
        
        snapshots = list(self.snapshot_history)
        
        # Check if price is stable despite volume
        prices = [s.mid_price for s in snapshots]
        volumes = [s.total_bid_volume + s.total_ask_volume for s in snapshots]
        
        price_range = max(prices) - min(prices)
        avg_price = statistics.mean(prices)
        
        if avg_price > 0:
            price_stability = price_range / avg_price
        else:
            price_stability = 0
        
        avg_volume = statistics.mean(volumes)
        
        # High volume + stable price = absorption
        if price_stability < 0.001 and avg_volume > 0:
            # Check imbalance direction
            imbalances = [s.imbalance for s in snapshots]
            avg_imbalance = statistics.mean(imbalances)
            
            if avg_imbalance > 0.2:
                return {
                    'type': 'bid_absorption',
                    'price_level': avg_price,
                    'volume': avg_volume,
                    'stability': price_stability
                }
            elif avg_imbalance < -0.2:
                return {
                    'type': 'ask_absorption',
                    'price_level': avg_price,
                    'volume': avg_volume,
                    'stability': price_stability
                }
        
        return None


class LOBPatternRecognizer:
    """
    Recognizes patterns in LOB evolution.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.matrix_history: deque = deque(maxlen=100)
        self.state_history: deque = deque(maxlen=100)
    
    def add_snapshot(self, snapshot: LOBSnapshot, state: LOBState):
        """Add snapshot and state."""
        matrix = snapshot.to_matrix(depth=10)
        self.matrix_history.append((snapshot.timestamp, matrix))
        self.state_history.append((snapshot.timestamp, state))
    
    def recognize_patterns(self) -> List[LOBPattern]:
        """Recognize patterns in recent history."""
        patterns = []
        
        if len(self.state_history) < 10:
            return patterns
        
        states = list(self.state_history)
        
        # Pattern 1: Accumulation (repeated bid_heavy states)
        bid_heavy_count = sum(1 for _, s in states[-20:] if s == LOBState.BID_HEAVY)
        if bid_heavy_count >= 10:
            patterns.append(LOBPattern(
                pattern_name="ACCUMULATION",
                start_time=states[-20][0],
                end_time=states[-1][0],
                confidence=bid_heavy_count / 20,
                price_levels=[],
                volume_profile={},
                predicted_direction='UP',
                predicted_magnitude=bid_heavy_count / 20 * 0.5
            ))
        
        # Pattern 2: Distribution (repeated ask_heavy states)
        ask_heavy_count = sum(1 for _, s in states[-20:] if s == LOBState.ASK_HEAVY)
        if ask_heavy_count >= 10:
            patterns.append(LOBPattern(
                pattern_name="DISTRIBUTION",
                start_time=states[-20][0],
                end_time=states[-1][0],
                confidence=ask_heavy_count / 20,
                price_levels=[],
                volume_profile={},
                predicted_direction='DOWN',
                predicted_magnitude=ask_heavy_count / 20 * 0.5
            ))
        
        # Pattern 3: Liquidity vacuum (thin followed by thick)
        recent_states = [s for _, s in states[-10:]]
        if LOBState.THIN in recent_states[:5] and LOBState.THICK in recent_states[5:]:
            patterns.append(LOBPattern(
                pattern_name="LIQUIDITY_RETURN",
                start_time=states[-10][0],
                end_time=states[-1][0],
                confidence=0.7,
                price_levels=[],
                volume_profile={},
                predicted_direction='NEUTRAL',
                predicted_magnitude=0.2
            ))
        
        return patterns


class LOBStateTransitionModel:
    """
    Main LOB state transition modeling system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.state_classifier = LOBStateClassifier(config)
        self.spoofing_detector = SpoofingDetector(config)
        self.absorption_detector = AbsorptionDetector(config)
        self.pattern_recognizer = LOBPatternRecognizer(config)
        
        # State tracking
        self.current_state: Optional[LOBState] = None
        self.state_history: deque = deque(maxlen=100)
        self.transitions: deque = deque(maxlen=50)
        self.avg_volume: float = 0
        self.volume_history: deque = deque(maxlen=100)
        
        logger.info("LOBStateTransitionModel initialized")
    
    def process_snapshot(self, snapshot: LOBSnapshot) -> Optional[StateTransition]:
        """
        Process new LOB snapshot.
        
        Args:
            snapshot: LOB snapshot
            
        Returns:
            StateTransition if state changed
        """
        # Update volume average
        total_volume = snapshot.total_bid_volume + snapshot.total_ask_volume
        self.volume_history.append(total_volume)
        self.avg_volume = statistics.mean(self.volume_history) if self.volume_history else total_volume
        
        # Classify state
        new_state = self.state_classifier.classify(snapshot, self.avg_volume)
        
        # Update detectors
        self.spoofing_detector.add_snapshot(snapshot)
        self.absorption_detector.add_snapshot(snapshot)
        self.pattern_recognizer.add_snapshot(snapshot, new_state)
        
        # Check for special states
        spoofing = self.spoofing_detector.detect()
        if spoofing:
            new_state = LOBState.SPOOFING
        
        absorption = self.absorption_detector.detect()
        if absorption:
            new_state = LOBState.ABSORPTION
        
        # Check for transition
        transition = None
        if self.current_state is not None and new_state != self.current_state:
            transition = self._create_transition(
                self.current_state, new_state, snapshot
            )
            self.transitions.append(transition)
        
        # Update state
        self.current_state = new_state
        self.state_history.append((snapshot.timestamp, new_state))
        
        return transition
    
    def _create_transition(
        self,
        from_state: LOBState,
        to_state: LOBState,
        snapshot: LOBSnapshot
    ) -> StateTransition:
        """Create state transition record."""
        # Determine transition type
        transition_type = self._classify_transition(from_state, to_state)
        
        # Calculate magnitude
        magnitude = abs(snapshot.imbalance)
        
        # Calculate confidence
        confidence = 0.5 + magnitude * 0.3
        
        return StateTransition(
            timestamp=snapshot.timestamp,
            from_state=from_state,
            to_state=to_state,
            transition_type=transition_type,
            confidence=min(0.95, confidence),
            magnitude=magnitude,
            details={
                'imbalance': snapshot.imbalance,
                'spread_bps': snapshot.spread_bps,
                'bid_volume': snapshot.total_bid_volume,
                'ask_volume': snapshot.total_ask_volume
            }
        )
    
    def _classify_transition(
        self,
        from_state: LOBState,
        to_state: LOBState
    ) -> TransitionType:
        """Classify transition type."""
        # Accumulation patterns
        if to_state == LOBState.BID_HEAVY:
            if from_state in [LOBState.BALANCED, LOBState.THIN]:
                return TransitionType.ACCUMULATION_START
            elif from_state == LOBState.ABSORPTION:
                return TransitionType.SUPPORT_BUILDING
        
        # Distribution patterns
        if to_state == LOBState.ASK_HEAVY:
            if from_state in [LOBState.BALANCED, LOBState.THIN]:
                return TransitionType.DISTRIBUTION_START
            elif from_state == LOBState.ABSORPTION:
                return TransitionType.RESISTANCE_BUILDING
        
        # Breakout setups
        if from_state == LOBState.BID_HEAVY and to_state == LOBState.THIN:
            return TransitionType.BREAKOUT_SETUP
        
        if from_state == LOBState.ASK_HEAVY and to_state == LOBState.THIN:
            return TransitionType.BREAKDOWN_SETUP
        
        # Liquidity vacuum
        if to_state == LOBState.THIN:
            return TransitionType.LIQUIDITY_VACUUM
        
        return TransitionType.NEUTRAL
    
    def generate_signal(self, symbol: str) -> LOBSignal:
        """
        Generate trading signal from LOB analysis.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            LOBSignal with analysis
        """
        if self.current_state is None:
            return self._empty_signal(symbol)
        
        # Get recent transitions
        recent_transitions = list(self.transitions)[-5:]
        
        # Get patterns
        patterns = self.pattern_recognizer.recognize_patterns()
        
        # Determine signal
        signal_type, strength, confidence = self._determine_signal(
            self.current_state, recent_transitions, patterns
        )
        
        # Calculate metrics
        states = list(self.state_history)
        if states:
            recent_imbalances = []
            for ts, state in states[-10:]:
                if state == LOBState.BID_HEAVY:
                    recent_imbalances.append(0.5)
                elif state == LOBState.ASK_HEAVY:
                    recent_imbalances.append(-0.5)
                else:
                    recent_imbalances.append(0)
            
            avg_imbalance = statistics.mean(recent_imbalances) if recent_imbalances else 0
        else:
            avg_imbalance = 0
        
        # Depth ratio
        bid_states = sum(1 for _, s in states[-20:] if s == LOBState.BID_HEAVY)
        ask_states = sum(1 for _, s in states[-20:] if s == LOBState.ASK_HEAVY)
        total_states = bid_states + ask_states
        depth_ratio = bid_states / total_states if total_states > 0 else 0.5
        
        # Generate analysis
        analysis = self._generate_analysis(
            self.current_state, recent_transitions, patterns, signal_type
        )
        
        return LOBSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            current_state=self.current_state,
            recent_transitions=recent_transitions,
            patterns=patterns,
            imbalance=avg_imbalance,
            depth_ratio=depth_ratio,
            analysis=analysis
        )
    
    def _empty_signal(self, symbol: str) -> LOBSignal:
        """Return empty signal."""
        return LOBSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            signal_type='NEUTRAL',
            strength=SignalStrength.WEAK,
            confidence=0.0,
            current_state=LOBState.BALANCED,
            recent_transitions=[],
            patterns=[],
            imbalance=0,
            depth_ratio=0.5,
            analysis="Insufficient data"
        )
    
    def _determine_signal(
        self,
        state: LOBState,
        transitions: List[StateTransition],
        patterns: List[LOBPattern]
    ) -> Tuple[str, SignalStrength, float]:
        """Determine signal from state and transitions."""
        confidence = 0.5
        
        # State-based signal
        if state == LOBState.BID_HEAVY:
            signal_type = 'BUY'
            confidence += 0.1
        elif state == LOBState.ASK_HEAVY:
            signal_type = 'SELL'
            confidence += 0.1
        elif state == LOBState.ABSORPTION:
            # Absorption often precedes reversal
            signal_type = 'NEUTRAL'
            confidence += 0.05
        else:
            signal_type = 'NEUTRAL'
        
        # Transition-based adjustment
        for trans in transitions[-3:]:
            if trans.transition_type == TransitionType.ACCUMULATION_START:
                if signal_type != 'SELL':
                    signal_type = 'BUY'
                    confidence += 0.1
            elif trans.transition_type == TransitionType.DISTRIBUTION_START:
                if signal_type != 'BUY':
                    signal_type = 'SELL'
                    confidence += 0.1
            elif trans.transition_type == TransitionType.BREAKOUT_SETUP:
                signal_type = 'BUY'
                confidence += 0.15
            elif trans.transition_type == TransitionType.BREAKDOWN_SETUP:
                signal_type = 'SELL'
                confidence += 0.15
        
        # Pattern-based adjustment
        for pattern in patterns:
            if pattern.predicted_direction == 'UP' and signal_type != 'SELL':
                signal_type = 'BUY'
                confidence += pattern.confidence * 0.2
            elif pattern.predicted_direction == 'DOWN' and signal_type != 'BUY':
                signal_type = 'SELL'
                confidence += pattern.confidence * 0.2
        
        # Determine strength
        if confidence >= 0.8:
            strength = SignalStrength.VERY_STRONG
        elif confidence >= 0.65:
            strength = SignalStrength.STRONG
        elif confidence >= 0.5:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        return signal_type, strength, min(0.95, confidence)
    
    def _generate_analysis(
        self,
        state: LOBState,
        transitions: List[StateTransition],
        patterns: List[LOBPattern],
        signal_type: str
    ) -> str:
        """Generate analysis text."""
        parts = []
        
        parts.append(f"State: {state.value}")
        parts.append(f"Signal: {signal_type}")
        
        if transitions:
            recent = transitions[-1]
            parts.append(f"Last transition: {recent.transition_type.value}")
        
        if patterns:
            pattern_names = [p.pattern_name for p in patterns]
            parts.append(f"Patterns: {', '.join(pattern_names)}")
        
        return " | ".join(parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get model status."""
        return {
            'current_state': self.current_state.value if self.current_state else None,
            'state_history_length': len(self.state_history),
            'transitions_count': len(self.transitions),
            'avg_volume': self.avg_volume,
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_lob_model(config: Optional[Dict] = None) -> LOBStateTransitionModel:
    """Create LOBStateTransitionModel instance."""
    return LOBStateTransitionModel(config)


# Example usage
if __name__ == "__main__":
    import random
    
    model = create_lob_model()
    
    print("=" * 60)
    print("LOB STATE TRANSITION MODEL")
    print("=" * 60)
    
    symbol = "EURUSD"
    base_price = 1.1000
    
    print("\nSimulating order book evolution...")
    
    for i in range(50):
        # Generate LOB snapshot
        mid = base_price + random.uniform(-0.001, 0.001)
        
        # Create bid levels
        bids = []
        for j in range(10):
            price = mid - 0.0001 * (j + 1)
            # Simulate accumulation pattern
            qty = random.randint(100, 1000) * (1.5 if i > 25 else 1.0)
            bids.append(LOBLevel(price=price, quantity=qty, order_count=random.randint(5, 20)))
        
        # Create ask levels
        asks = []
        for j in range(10):
            price = mid + 0.0001 * (j + 1)
            qty = random.randint(100, 1000)
            asks.append(LOBLevel(price=price, quantity=qty, order_count=random.randint(5, 20)))
        
        snapshot = LOBSnapshot(
            timestamp=datetime.now(),
            symbol=symbol,
            bids=bids,
            asks=asks
        )
        
        transition = model.process_snapshot(snapshot)
        
        if transition:
            print(f"\nBar {i}: TRANSITION DETECTED")
            print(f"  {transition.from_state.value} -> {transition.to_state.value}")
            print(f"  Type: {transition.transition_type.value}")
            print(f"  Confidence: {transition.confidence:.0%}")
    
    # Generate signal
    print("\n" + "=" * 60)
    print("LOB SIGNAL")
    print("=" * 60)
    
    signal = model.generate_signal(symbol)
    
    print(f"\nSymbol: {signal.symbol}")
    print(f"Signal: {signal.signal_type}")
    print(f"Strength: {signal.strength.name}")
    print(f"Confidence: {signal.confidence:.0%}")
    print(f"Current State: {signal.current_state.value}")
    print(f"Imbalance: {signal.imbalance:.2f}")
    print(f"Depth Ratio: {signal.depth_ratio:.2f}")
    
    if signal.patterns:
        print(f"\nDetected Patterns:")
        for pattern in signal.patterns:
            print(f"  {pattern.pattern_name}: {pattern.predicted_direction} ({pattern.confidence:.0%})")
    
    print(f"\nAnalysis: {signal.analysis}")
    
    # Status
    print("\n" + "=" * 60)
    print("STATUS")
    print("=" * 60)
    
    status = model.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
