"""
Market Intent Decomposition Engine (MIDE) - Momentum Tracker

Tracks intent momentum, persistence, exhaustion, and stability.
Critical for understanding intent lifecycle and timing decisions.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Deque, Dict
from collections import deque

from .intent_decomposition_core import (
    IntentSimplex, IntentState, IntentPhase, IntentMomentum,
    IntentPersistence, IntentExhaustion, MIDEConfig, INTENT_NAMES,
    compute_stability_score
)


# =============================================================================
# DECAY FUNCTIONS
# =============================================================================

@dataclass
class DecayConfig:
    """Configuration for intent-specific decay."""
    decay_type: str  # 'exponential', 'linear', 'step', 'instant'
    half_life: float = 5.0  # For exponential
    decay_rate: float = 0.02  # For linear
    duration: int = 20  # For step
    instant_factor: float = 0.5  # For instant


INTENT_DECAY_CONFIGS = {
    'urgent': DecayConfig('exponential', half_life=5),
    'passive': DecayConfig('linear', decay_rate=0.02),
    'mechanical': DecayConfig('step', duration=20),
    'exploitative': DecayConfig('exponential', half_life=10),
    'noise': DecayConfig('instant', instant_factor=0.5),
}


def apply_decay(intent: str, strength: float, bars_elapsed: int) -> float:
    """
    Apply intent-specific decay function.
    
    Args:
        intent: Intent name
        strength: Current strength
        bars_elapsed: Bars since peak
    
    Returns:
        Decayed strength
    """
    config = INTENT_DECAY_CONFIGS.get(intent, DecayConfig('exponential'))
    
    if config.decay_type == 'exponential':
        return strength * np.exp(-0.693 * bars_elapsed / config.half_life)
    elif config.decay_type == 'linear':
        return max(0, strength - config.decay_rate * bars_elapsed)
    elif config.decay_type == 'step':
        return strength if bars_elapsed < config.duration else 0
    elif config.decay_type == 'instant':
        return strength * config.instant_factor
    else:
        return strength


# =============================================================================
# MOMENTUM TRACKER
# =============================================================================

class MomentumTracker:
    """
    Tracks momentum for each intent.
    
    Momentum = EMA of probability changes
    Positive momentum = intent strengthening
    Negative momentum = intent weakening
    """
    
    def __init__(self, beta: float = 0.9):
        self.beta = beta
        self.momentum = np.zeros(5, dtype=np.float32)
        self.max_momentum = np.ones(5, dtype=np.float32) * 0.1
        self._prev_simplex: Optional[np.ndarray] = None
    
    def update(self, simplex: IntentSimplex) -> IntentMomentum:
        """
        Update momentum with new simplex.
        
        Args:
            simplex: Current intent simplex
        
        Returns:
            Updated IntentMomentum
        """
        pi = simplex.to_array()
        
        if self._prev_simplex is not None:
            delta = pi - self._prev_simplex
            self.momentum = self.beta * self.momentum + (1 - self.beta) * delta
            self.max_momentum = np.maximum(self.max_momentum, np.abs(self.momentum))
        
        self._prev_simplex = pi.copy()
        
        return IntentMomentum(
            values=self.momentum.copy(),
            max_values=self.max_momentum.copy()
        )
    
    def get_direction(self, intent_idx: int) -> str:
        """Get momentum direction for intent."""
        if self.momentum[intent_idx] > 0.02:
            return 'strengthening'
        elif self.momentum[intent_idx] < -0.02:
            return 'weakening'
        else:
            return 'stable'
    
    def get_magnitude(self, intent_idx: int) -> float:
        """Get momentum magnitude for intent."""
        return float(np.abs(self.momentum[intent_idx]))
    
    def reset(self):
        """Reset tracker."""
        self.momentum = np.zeros(5, dtype=np.float32)
        self.max_momentum = np.ones(5, dtype=np.float32) * 0.1
        self._prev_simplex = None


# =============================================================================
# PERSISTENCE TRACKER
# =============================================================================

class PersistenceTracker:
    """
    Tracks persistence for each intent.
    
    Persistence = fraction of recent bars where intent exceeded threshold
    High persistence = sustained intent (institutional)
    Low persistence = transient intent (opportunistic/noise)
    """
    
    def __init__(self, lookback: int = 20, threshold: float = 0.3):
        self.lookback = lookback
        self.threshold = threshold
        self.history: Deque[np.ndarray] = deque(maxlen=lookback)
        self.persistence = np.zeros(5, dtype=np.float32)
    
    def update(self, simplex: IntentSimplex) -> IntentPersistence:
        """
        Update persistence with new simplex.
        
        Args:
            simplex: Current intent simplex
        
        Returns:
            Updated IntentPersistence
        """
        pi = simplex.to_array()
        self.history.append(pi)
        
        if len(self.history) >= self.lookback:
            history_array = np.array(list(self.history))
            self.persistence = np.mean(history_array > self.threshold, axis=0).astype(np.float32)
        
        return IntentPersistence(
            values=self.persistence.copy(),
            threshold=self.threshold,
            lookback=self.lookback
        )
    
    def get_persistence(self, intent_idx: int) -> float:
        """Get persistence for intent."""
        return float(self.persistence[intent_idx])
    
    def is_sustained(self, intent_idx: int, min_persistence: float = 0.7) -> bool:
        """Check if intent is sustained."""
        return self.persistence[intent_idx] >= min_persistence
    
    def reset(self):
        """Reset tracker."""
        self.history.clear()
        self.persistence = np.zeros(5, dtype=np.float32)


# =============================================================================
# EXHAUSTION TRACKER
# =============================================================================

class ExhaustionTracker:
    """
    Tracks exhaustion for each intent.
    
    Exhaustion = declining momentum after sustained presence
    High exhaustion = intent likely to fade
    Low exhaustion = intent has room to grow
    """
    
    def __init__(self):
        self.exhaustion = np.zeros(5, dtype=np.float32)
        self._peak_momentum = np.zeros(5, dtype=np.float32)
        self._bars_since_peak = np.zeros(5, dtype=np.int32)
    
    def update(self, momentum: IntentMomentum, 
               persistence: IntentPersistence) -> IntentExhaustion:
        """
        Update exhaustion based on momentum and persistence.
        
        Args:
            momentum: Current momentum state
            persistence: Current persistence state
        
        Returns:
            Updated IntentExhaustion
        """
        for i in range(5):
            # Track peak momentum
            if momentum.values[i] > self._peak_momentum[i]:
                self._peak_momentum[i] = momentum.values[i]
                self._bars_since_peak[i] = 0
            else:
                self._bars_since_peak[i] += 1
            
            # Calculate exhaustion
            if persistence.values[i] > 0.7 and momentum.values[i] < 0:
                # High persistence + declining momentum = exhaustion
                if momentum.max_values[i] > 0.01:
                    self.exhaustion[i] = 1.0 - (
                        momentum.values[i] / (-momentum.max_values[i] + 1e-8)
                    )
                    self.exhaustion[i] = np.clip(self.exhaustion[i], 0, 1)
            else:
                # Decay exhaustion
                self.exhaustion[i] *= 0.95
        
        return IntentExhaustion(values=self.exhaustion.copy())
    
    def get_exhaustion(self, intent_idx: int) -> float:
        """Get exhaustion for intent."""
        return float(self.exhaustion[intent_idx])
    
    def is_exhausted(self, intent_idx: int, threshold: float = 0.7) -> bool:
        """Check if intent is exhausted."""
        return self.exhaustion[intent_idx] >= threshold
    
    def reset(self):
        """Reset tracker."""
        self.exhaustion = np.zeros(5, dtype=np.float32)
        self._peak_momentum = np.zeros(5, dtype=np.float32)
        self._bars_since_peak = np.zeros(5, dtype=np.int32)


# =============================================================================
# STABILITY TRACKER
# =============================================================================

class StabilityTracker:
    """
    Tracks stability of intent distribution.
    
    High stability = confident, persistent, low momentum
    Low stability = uncertain, volatile, high momentum
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        self.config = config or MIDEConfig()
        self.history: Deque[np.ndarray] = deque(maxlen=10)
        self.stability_score = 0.5
    
    def update(self, simplex: IntentSimplex, 
               momentum: IntentMomentum) -> float:
        """
        Update stability score.
        
        Args:
            simplex: Current intent simplex
            momentum: Current momentum state
        
        Returns:
            Updated stability score
        """
        pi = simplex.to_array()
        self.history.append(pi)
        
        # Entropy component (lower entropy = more stable)
        entropy = simplex.entropy
        entropy_score = 1 - entropy
        
        # Momentum component (lower momentum = more stable)
        momentum_magnitude = np.linalg.norm(momentum.values)
        momentum_score = 1 / (1 + 10 * momentum_magnitude)
        
        # Consistency component (similar to recent history)
        if len(self.history) >= 5:
            recent = np.array(list(self.history)[-5:])
            variance = np.mean(np.var(recent, axis=0))
            consistency_score = 1 / (1 + 10 * variance)
        else:
            consistency_score = 0.5
        
        # Weighted combination
        self.stability_score = (
            self.config.stability_entropy_weight * entropy_score +
            self.config.stability_momentum_weight * momentum_score +
            self.config.stability_consistency_weight * consistency_score
        )
        
        return float(np.clip(self.stability_score, 0, 1))
    
    def reset(self):
        """Reset tracker."""
        self.history.clear()
        self.stability_score = 0.5


# =============================================================================
# INTENT PHASE DETECTOR
# =============================================================================

class IntentPhaseDetector:
    """
    Detects lifecycle phase for each intent.
    
    Phases:
    - ABSENT: Intent not present
    - EMERGING: New intent building
    - BUILDING: Intent strengthening
    - SUSTAINED: Established and continuing
    - WEAKENING: Intent losing strength
    - EXHAUSTING: Intent running out of steam
    - FADING: Intent about to disappear
    """
    
    def detect_phase(self, intent_idx: int,
                     momentum: IntentMomentum,
                     persistence: IntentPersistence,
                     exhaustion: IntentExhaustion) -> IntentPhase:
        """
        Detect phase for specific intent.
        
        Args:
            intent_idx: Index of intent (0-4)
            momentum: Current momentum state
            persistence: Current persistence state
            exhaustion: Current exhaustion state
        
        Returns:
            IntentPhase enum value
        """
        mom = momentum.values[intent_idx]
        pers = persistence.values[intent_idx]
        exh = exhaustion.values[intent_idx]
        
        if pers < 0.3:
            if mom > 0.05:
                return IntentPhase.EMERGING
            else:
                return IntentPhase.ABSENT
        elif pers < 0.7:
            if mom > 0:
                return IntentPhase.BUILDING
            else:
                return IntentPhase.WEAKENING
        else:  # pers >= 0.7
            if exh < 0.3:
                return IntentPhase.SUSTAINED
            elif exh < 0.7:
                return IntentPhase.EXHAUSTING
            else:
                return IntentPhase.FADING
    
    def detect_all_phases(self, momentum: IntentMomentum,
                          persistence: IntentPersistence,
                          exhaustion: IntentExhaustion) -> Dict[str, IntentPhase]:
        """
        Detect phases for all intents.
        
        Returns:
            Dict mapping intent name to phase
        """
        return {
            INTENT_NAMES[i]: self.detect_phase(i, momentum, persistence, exhaustion)
            for i in range(5)
        }


# =============================================================================
# UNIFIED MOMENTUM TRACKER
# =============================================================================

class IntentMomentumTracker:
    """
    Unified tracker for momentum, persistence, exhaustion, and stability.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        self.config = config or MIDEConfig()
        
        self.momentum_tracker = MomentumTracker(beta=config.momentum_beta if config else 0.9)
        self.persistence_tracker = PersistenceTracker(
            lookback=config.persistence_lookback if config else 20,
            threshold=config.persistence_threshold if config else 0.3
        )
        self.exhaustion_tracker = ExhaustionTracker()
        self.stability_tracker = StabilityTracker(config)
        self.phase_detector = IntentPhaseDetector()
        
        # State
        self._bars_in_state: int = 0
        self._prev_dominant: str = 'noise'
    
    def update(self, simplex: IntentSimplex) -> IntentState:
        """
        Update all trackers and return complete intent state.
        
        Args:
            simplex: Current intent simplex
        
        Returns:
            Complete IntentState
        """
        # Update trackers
        momentum = self.momentum_tracker.update(simplex)
        persistence = self.persistence_tracker.update(simplex)
        exhaustion = self.exhaustion_tracker.update(momentum, persistence)
        stability = self.stability_tracker.update(simplex, momentum)
        
        # Track bars in state
        current_dominant = simplex.dominant_intent
        if current_dominant == self._prev_dominant:
            self._bars_in_state += 1
        else:
            self._bars_in_state = 1
        self._prev_dominant = current_dominant
        
        # Create state
        state = IntentState(
            simplex=simplex,
            momentum=momentum,
            persistence=persistence,
            exhaustion=exhaustion,
            stability_score=stability,
            bars_in_state=self._bars_in_state,
            timestamp=0.0,  # Set by caller
        )
        
        return state
    
    def get_phase(self, intent: str) -> IntentPhase:
        """Get current phase for intent."""
        idx = INTENT_NAMES.index(intent)
        return self.phase_detector.detect_phase(
            idx,
            IntentMomentum(values=self.momentum_tracker.momentum.copy()),
            IntentPersistence(values=self.persistence_tracker.persistence.copy()),
            IntentExhaustion(values=self.exhaustion_tracker.exhaustion.copy())
        )
    
    def get_all_phases(self) -> Dict[str, IntentPhase]:
        """Get phases for all intents."""
        return self.phase_detector.detect_all_phases(
            IntentMomentum(values=self.momentum_tracker.momentum.copy()),
            IntentPersistence(values=self.persistence_tracker.persistence.copy()),
            IntentExhaustion(values=self.exhaustion_tracker.exhaustion.copy())
        )
    
    def get_decay_forecast(self, intent: str, bars_ahead: int = 10) -> List[float]:
        """
        Forecast intent strength decay over future bars.
        
        Args:
            intent: Intent name
            bars_ahead: Number of bars to forecast
        
        Returns:
            List of forecasted strengths
        """
        idx = INTENT_NAMES.index(intent)
        current_strength = self.persistence_tracker.persistence[idx]
        
        forecast = []
        for bars in range(bars_ahead):
            decayed = apply_decay(intent, current_strength, bars)
            forecast.append(decayed)
        
        return forecast
    
    def reset(self):
        """Reset all trackers."""
        self.momentum_tracker.reset()
        self.persistence_tracker.reset()
        self.exhaustion_tracker.reset()
        self.stability_tracker.reset()
        self._bars_in_state = 0
        self._prev_dominant = 'noise'


# =============================================================================
# INTENT LIFECYCLE ANALYZER
# =============================================================================

class IntentLifecycleAnalyzer:
    """
    Analyzes intent lifecycle for strategic decisions.
    """
    
    def __init__(self):
        self._lifecycle_history: Dict[str, List[Tuple[IntentPhase, int]]] = {
            name: [] for name in INTENT_NAMES
        }
    
    def record(self, phases: Dict[str, IntentPhase], bar_idx: int):
        """Record current phases."""
        for intent, phase in phases.items():
            history = self._lifecycle_history[intent]
            if not history or history[-1][0] != phase:
                history.append((phase, bar_idx))
            # Keep only recent history
            if len(history) > 100:
                self._lifecycle_history[intent] = history[-100:]
    
    def get_average_duration(self, intent: str, phase: IntentPhase) -> float:
        """Get average duration of phase for intent."""
        history = self._lifecycle_history[intent]
        
        durations = []
        for i in range(len(history) - 1):
            if history[i][0] == phase:
                duration = history[i + 1][1] - history[i][1]
                durations.append(duration)
        
        return float(np.mean(durations)) if durations else 0.0
    
    def get_transition_probability(self, intent: str, 
                                    from_phase: IntentPhase,
                                    to_phase: IntentPhase) -> float:
        """Get probability of phase transition for intent."""
        history = self._lifecycle_history[intent]
        
        transitions_from = 0
        transitions_to = 0
        
        for i in range(len(history) - 1):
            if history[i][0] == from_phase:
                transitions_from += 1
                if history[i + 1][0] == to_phase:
                    transitions_to += 1
        
        return transitions_to / transitions_from if transitions_from > 0 else 0.0
    
    def predict_next_phase(self, intent: str, 
                           current_phase: IntentPhase) -> Tuple[IntentPhase, float]:
        """
        Predict most likely next phase.
        
        Returns:
            Tuple of (predicted_phase, probability)
        """
        best_phase = IntentPhase.ABSENT
        best_prob = 0.0
        
        for phase in IntentPhase:
            prob = self.get_transition_probability(intent, current_phase, phase)
            if prob > best_prob:
                best_prob = prob
                best_phase = phase
        
        return best_phase, best_prob
