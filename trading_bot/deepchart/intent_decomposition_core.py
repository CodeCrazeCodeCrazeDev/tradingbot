"""
Market Intent Decomposition Engine (MIDE) - Core Data Structures

Causal market cognition layer that decomposes market moments into
probability-weighted mixtures of latent participant intents.

NON-NEGOTIABLE CONSTRAINTS:
- NO L3 order book data
- NO GPU infrastructure dependency
- CPU-first ML, ONNX-exportable
- <2ms inference latency per symbol
- Interpretable and stable under regime change
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Deque
from enum import Enum, auto
from collections import deque
import time


# =============================================================================
# ENUMS
# =============================================================================

import logging

logger = logging.getLogger(__name__)

class ParticipantIntent(Enum):
    """
    The 5 canonical latent intents (MANDATORY - no more, no less).
    """
    URGENT_DIRECTIONAL = 0      # Informed trader with time pressure
    PASSIVE_ACCUMULATION = 1    # Patient institutional flow
    MECHANICAL_FLOW = 2         # Algorithmic rebalancing, TWAP/VWAP
    EXPLOITATIVE = 3            # Market makers, stat-arb
    NOISE = 4                   # Retail, uninformed flow


class IntentPhase(Enum):
    """
    Lifecycle phase of an intent.
    """
    ABSENT = auto()         # Intent not present
    EMERGING = auto()       # New intent building
    BUILDING = auto()       # Intent strengthening
    SUSTAINED = auto()      # Established and continuing
    WEAKENING = auto()      # Intent losing strength
    EXHAUSTING = auto()     # Intent running out of steam
    FADING = auto()         # Intent about to disappear


class IntentTransition(Enum):
    """
    Types of intent transitions.
    """
    STABLE = auto()         # No change in dominant
    GRADUAL = auto()        # Slow transition
    ABRUPT = auto()         # Sudden change
    REVERSAL = auto()       # Opposite intent emerges


# =============================================================================
# PERFORMANCE BUDGET CONSTANTS
# =============================================================================

MAX_INFERENCE_LATENCY_MS = 2.0
MAX_RAM_PER_SYMBOL_KB = 200
MAX_STATE_HISTORY = 100
MAX_MODEL_SIZE_MB = 1.0
MAX_STALENESS_MS = 50
MIN_INTENT_PROBABILITY = 0.01
MAX_INTENT_PROBABILITY = 0.95
NOISE_FLOOR = 0.05


# =============================================================================
# INTENT NAMES AND COLORS
# =============================================================================

INTENT_NAMES = ['urgent', 'passive', 'mechanical', 'exploitative', 'noise']

INTENT_COLORS = {
    'urgent': (220, 50, 50, 255),       # Red
    'passive': (50, 100, 200, 255),     # Blue
    'mechanical': (128, 128, 128, 255), # Gray
    'exploitative': (230, 180, 50, 255),# Yellow
    'noise': (200, 200, 200, 128),      # Light gray, semi-transparent
}

INTENT_DESCRIPTIONS = {
    'urgent': 'Informed trader with time pressure executing aggressively',
    'passive': 'Patient institutional flow hiding in the tape',
    'mechanical': 'Algorithmic rebalancing, index tracking, TWAP/VWAP',
    'exploitative': 'Market makers, stat-arb, liquidity provision',
    'noise': 'Retail flow, random arrivals, uninformed speculation',
}


# =============================================================================
# TRANSITION MATRIX
# =============================================================================

# T[i,j] = P(intent_t = j | intent_{t-1} = i)
TRANSITION_MATRIX = np.array([
    # To:    Urgent  Passive  Mech.   Exploit. Noise
    [0.70,   0.10,    0.05,   0.05,    0.10],  # From: Urgent
    [0.10,   0.65,    0.10,   0.05,    0.10],  # From: Passive
    [0.05,   0.10,    0.70,   0.05,    0.10],  # From: Mechanical
    [0.10,   0.10,    0.05,   0.60,    0.15],  # From: Exploitative
    [0.10,   0.10,    0.15,   0.15,    0.50],  # From: Noise
], dtype=np.float32)


# =============================================================================
# DATA STRUCTURES - Observable Features
# =============================================================================

@dataclass
class ObservableFeatures:
    """
    The 12 observable features extracted from cheap data.
    All features are normalized to approximately [-3, 3] range.
    """
    # Price response per unit volume
    price_response_per_volume: float = 0.0  # ρ
    
    # Spread-crossing frequency
    spread_crossing_freq: float = 0.0  # f_cross
    
    # Reaction half-life after trade bursts
    reaction_half_life: float = 0.0  # τ_1/2
    
    # Volume entropy
    volume_entropy: float = 0.0  # H_v
    
    # Price curvature vs volume
    price_curvature: float = 0.0  # κ
    
    # Micro-friction persistence
    friction_persistence: float = 0.0  # φ
    
    # Execution efficiency vs volatility
    execution_efficiency: float = 0.0  # η
    
    # Trade arrival irregularity
    arrival_irregularity: float = 0.0  # ψ
    
    # Size clustering coefficient
    size_clustering: float = 0.0  # γ
    
    # Quote imbalance persistence
    imbalance_persistence: float = 0.0  # ω
    
    # Aggressor ratio asymmetry
    aggressor_asymmetry: float = 0.0  # α
    
    # Momentum decay rate
    momentum_decay_rate: float = 0.0  # λ_m
    
    # Metadata
    timestamp: float = 0.0
    is_valid: bool = True
    staleness_ms: float = 0.0
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input."""
        return np.array([
            self.price_response_per_volume,
            self.spread_crossing_freq,
            self.reaction_half_life,
            self.volume_entropy,
            self.price_curvature,
            self.friction_persistence,
            self.execution_efficiency,
            self.arrival_irregularity,
            self.size_clustering,
            self.imbalance_persistence,
            self.aggressor_asymmetry,
            self.momentum_decay_rate,
        ], dtype=np.float32)
    
    @staticmethod
    def from_array(arr: np.ndarray, timestamp: float = 0.0) -> 'ObservableFeatures':
        """Create from numpy array."""
        return ObservableFeatures(
            price_response_per_volume=float(arr[0]),
            spread_crossing_freq=float(arr[1]),
            reaction_half_life=float(arr[2]),
            volume_entropy=float(arr[3]),
            price_curvature=float(arr[4]),
            friction_persistence=float(arr[5]),
            execution_efficiency=float(arr[6]),
            arrival_irregularity=float(arr[7]),
            size_clustering=float(arr[8]),
            imbalance_persistence=float(arr[9]),
            aggressor_asymmetry=float(arr[10]),
            momentum_decay_rate=float(arr[11]),
            timestamp=timestamp,
        )


# =============================================================================
# DATA STRUCTURES - Intent State
# =============================================================================

@dataclass
class IntentSimplex:
    """
    The 5-dimensional probability simplex representing intent mixture.
    """
    urgent: float = 0.2
    passive: float = 0.2
    mechanical: float = 0.2
    exploitative: float = 0.2
    noise: float = 0.2
    
    def __post_init__(self):
        """Ensure valid probability distribution."""
        try:
            self._normalize()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __post_init__: {e}")
            raise
    
    def _normalize(self):
        """Normalize to sum to 1 with constraints."""
        try:
            total = self.urgent + self.passive + self.mechanical + self.exploitative + self.noise
            if total > 0:
                self.urgent /= total
                self.passive /= total
                self.mechanical /= total
                self.exploitative /= total
                self.noise /= total
        
            # Apply floor and ceiling
            self.urgent = np.clip(self.urgent, MIN_INTENT_PROBABILITY, MAX_INTENT_PROBABILITY)
            self.passive = np.clip(self.passive, MIN_INTENT_PROBABILITY, MAX_INTENT_PROBABILITY)
            self.mechanical = np.clip(self.mechanical, MIN_INTENT_PROBABILITY, MAX_INTENT_PROBABILITY)
            self.exploitative = np.clip(self.exploitative, MIN_INTENT_PROBABILITY, MAX_INTENT_PROBABILITY)
            self.noise = max(self.noise, NOISE_FLOOR)  # Noise floor
        
            # Re-normalize after clipping
            total = self.urgent + self.passive + self.mechanical + self.exploitative + self.noise
            self.urgent /= total
            self.passive /= total
            self.mechanical /= total
            self.exploitative /= total
            self.noise /= total
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _normalize: {e}")
            raise
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([
            self.urgent, self.passive, self.mechanical, 
            self.exploitative, self.noise
        ], dtype=np.float32)
    
    @staticmethod
    def from_array(arr: np.ndarray) -> 'IntentSimplex':
        """Create from numpy array."""
        return IntentSimplex(
            urgent=float(arr[0]),
            passive=float(arr[1]),
            mechanical=float(arr[2]),
            exploitative=float(arr[3]),
            noise=float(arr[4]),
        )
    
    @property
    def dominant_intent(self) -> str:
        """Get the dominant intent name."""
        try:
            arr = self.to_array()
            return INTENT_NAMES[np.argmax(arr)]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in dominant_intent: {e}")
            raise
    
    @property
    def dominant_probability(self) -> float:
        """Get the probability of dominant intent."""
        return float(np.max(self.to_array()))
    
    @property
    def confidence(self) -> float:
        """Confidence = max - second_max."""
        try:
            arr = self.to_array()
            sorted_arr = np.sort(arr)[::-1]
            return float(sorted_arr[0] - sorted_arr[1])
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in confidence: {e}")
            raise
    
    @property
    def entropy(self) -> float:
        """Shannon entropy of the distribution."""
        try:
            arr = self.to_array()
            arr = np.clip(arr, 1e-10, 1.0)
            return float(-np.sum(arr * np.log(arr)) / np.log(5))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in entropy: {e}")
            raise


@dataclass
class IntentMomentum:
    """
    Momentum tracking for each intent.
    """
    values: np.ndarray = field(default_factory=lambda: np.zeros(5, dtype=np.float32))
    max_values: np.ndarray = field(default_factory=lambda: np.ones(5, dtype=np.float32) * 0.1)
    
    def update(self, pi_new: np.ndarray, pi_prev: np.ndarray, beta: float = 0.9):
        """Update momentum with EMA."""
        try:
            delta = pi_new - pi_prev
            self.values = beta * self.values + (1 - beta) * delta
            self.max_values = np.maximum(self.max_values, np.abs(self.values))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
    
    def get_direction(self, intent_idx: int) -> str:
        """Get momentum direction for intent."""
        try:
            if self.values[intent_idx] > 0.02:
                return 'strengthening'
            elif self.values[intent_idx] < -0.02:
                return 'weakening'
            else:
                return 'stable'
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_direction: {e}")
            raise


@dataclass
class IntentPersistence:
    """
    Persistence tracking for each intent.
    """
    values: np.ndarray = field(default_factory=lambda: np.zeros(5, dtype=np.float32))
    threshold: float = 0.3
    lookback: int = 20
    
    def update(self, history: Deque[np.ndarray]):
        """Update persistence from history."""
        try:
            if len(history) < self.lookback:
                return
        
            recent = np.array(list(history)[-self.lookback:])
            self.values = np.mean(recent > self.threshold, axis=0).astype(np.float32)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise


@dataclass
class IntentExhaustion:
    """
    Exhaustion tracking for each intent.
    """
    values: np.ndarray = field(default_factory=lambda: np.zeros(5, dtype=np.float32))
    
    def update(self, momentum: IntentMomentum, persistence: IntentPersistence):
        """Update exhaustion based on momentum and persistence."""
        try:
            for i in range(5):
                if persistence.values[i] > 0.7 and momentum.values[i] < 0:
                    # High persistence + declining momentum = exhaustion
                    self.values[i] = 1.0 - (momentum.values[i] / (-momentum.max_values[i] + 1e-8))
                    self.values[i] = np.clip(self.values[i], 0, 1)
                else:
                    # Decay exhaustion
                    self.values[i] *= 0.95
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise


@dataclass
class IntentState:
    """
    Complete intent state for strategy consumption.
    """
    # Core simplex
    simplex: IntentSimplex = field(default_factory=IntentSimplex)
    
    # Dynamics
    momentum: IntentMomentum = field(default_factory=IntentMomentum)
    persistence: IntentPersistence = field(default_factory=IntentPersistence)
    exhaustion: IntentExhaustion = field(default_factory=IntentExhaustion)
    
    # Meta
    stability_score: float = 0.5
    bars_in_state: int = 0
    timestamp: float = 0.0
    inference_latency_ms: float = 0.0
    
    # Previous state for transition detection
    prev_dominant: str = 'noise'
    transition_type: IntentTransition = IntentTransition.STABLE
    
    @property
    def dominant_intent(self) -> str:
        """Get dominant intent name."""
        return self.simplex.dominant_intent
    
    @property
    def dominant_probability(self) -> float:
        """Get dominant intent probability."""
        return self.simplex.dominant_probability
    
    @property
    def confidence(self) -> float:
        """Get confidence in dominant intent."""
        return self.simplex.confidence
    
    def is_actionable(self, threshold: float = 0.4) -> bool:
        """Check if intent is clear enough to act on."""
        return self.dominant_probability >= threshold and self.confidence >= 0.1
    
    def get_intent_phase(self, intent: str) -> IntentPhase:
        """Get lifecycle phase for specific intent."""
        try:
            idx = INTENT_NAMES.index(intent)
            mom = self.momentum.values[idx]
            pers = self.persistence.values[idx]
            exh = self.exhaustion.values[idx]
        
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
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_intent_phase: {e}")
            raise
    
    def get_color(self) -> Tuple[int, int, int, int]:
        """Get RGBA color for dominant intent."""
        return INTENT_COLORS[self.dominant_intent]
    
    def get_opacity(self) -> float:
        """Get opacity based on confidence."""
        return 0.3 + 0.7 * (0.6 * self.confidence + 0.4 * self.stability_score)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'simplex': self.simplex.to_array().tolist(),
            'dominant_intent': self.dominant_intent,
            'dominant_probability': self.dominant_probability,
            'confidence': self.confidence,
            'momentum': self.momentum.values.tolist(),
            'persistence': self.persistence.values.tolist(),
            'exhaustion': self.exhaustion.values.tolist(),
            'stability_score': self.stability_score,
            'bars_in_state': self.bars_in_state,
            'timestamp': self.timestamp,
            'inference_latency_ms': self.inference_latency_ms,
            'transition_type': self.transition_type.name,
        }


# =============================================================================
# DATA STRUCTURES - Configuration
# =============================================================================

@dataclass
class MIDEConfig:
    """
    Configuration for Market Intent Decomposition Engine.
    """
    # Feature extraction
    feature_window: int = 64          # Sequence length for model
    feature_update_freq: int = 1      # Update every N bars
    
    # Model settings
    use_tcn: bool = True
    use_gru: bool = True
    use_attention: bool = True
    hidden_dim: int = 32
    
    # Transition constraints
    transition_alpha_min: float = 0.3  # Minimum responsiveness
    transition_alpha_max: float = 0.7  # Maximum responsiveness
    
    # Smoothing
    momentum_beta: float = 0.9
    persistence_lookback: int = 20
    persistence_threshold: float = 0.3
    
    # Stability
    stability_entropy_weight: float = 0.4
    stability_momentum_weight: float = 0.3
    stability_consistency_weight: float = 0.3
    
    # Impossible state rules
    urgent_passive_max_sum: float = 0.6
    exploitative_spread_threshold: float = 1.5
    mechanical_cv_threshold: float = 0.3
    
    # Performance budget
    max_inference_ms: float = 2.0
    max_ram_kb: float = 200.0
    max_staleness_ms: float = 50.0
    
    # Calibration
    temperature: float = 1.0  # Softmax temperature


# =============================================================================
# DATA STRUCTURES - Visualization
# =============================================================================

@dataclass
class IntentRibbonSlice:
    """
    Single slice of the intent ribbon visualization.
    """
    bar_index: int
    probabilities: np.ndarray  # [5] array
    dominant: str
    confidence: float
    opacity: float
    momentum_direction: str  # 'up', 'down', 'stable'
    is_transition: bool
    
    def get_band_heights(self, total_height: int = 50) -> List[int]:
        """Get pixel heights for each band."""
        try:
            heights = (self.probabilities * total_height).astype(int)
            # Ensure they sum to total_height
            diff = total_height - heights.sum()
            heights[np.argmax(heights)] += diff
            return heights.tolist()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_band_heights: {e}")
            raise


@dataclass
class IntentVisualization:
    """
    Complete visualization data for intent state.
    """
    ribbon_slices: List[IntentRibbonSlice] = field(default_factory=list)
    transition_markers: List[Tuple[int, str, str]] = field(default_factory=list)  # (bar, from, to)
    momentum_arrows: List[Tuple[int, str, float]] = field(default_factory=list)  # (bar, intent, magnitude)
    
    def to_json(self) -> Dict:
        """Convert to JSON-serializable format."""
        return {
            'ribbon': [
                {
                    'bar': s.bar_index,
                    'probs': s.probabilities.tolist(),
                    'dominant': s.dominant,
                    'confidence': s.confidence,
                    'opacity': s.opacity,
                }
                for s in self.ribbon_slices
            ],
            'transitions': [
                {'bar': t[0], 'from': t[1], 'to': t[2]}
                for t in self.transition_markers
            ],
            'momentum': [
                {'bar': m[0], 'intent': m[1], 'magnitude': m[2]}
                for m in self.momentum_arrows
            ],
            'colors': INTENT_COLORS,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def compute_stability_score(
    simplex: IntentSimplex,
    momentum: IntentMomentum,
    history: Deque[np.ndarray],
    config: MIDEConfig
) -> float:
    """
    Compute stability score for current intent state.
    
    High stability: Confident, persistent, low momentum
    Low stability: Uncertain, volatile, high momentum
    """
    # Entropy component (lower entropy = more stable)
    try:
        entropy_score = 1 - simplex.entropy
    
        # Momentum component (lower momentum = more stable)
        momentum_magnitude = np.linalg.norm(momentum.values)
        momentum_score = 1 / (1 + 10 * momentum_magnitude)
    
        # Consistency component (similar to recent history)
        if len(history) >= 5:
            recent = np.array(list(history)[-5:])
            variance = np.mean(np.var(recent, axis=0))
            consistency_score = 1 / (1 + 10 * variance)
        else:
            consistency_score = 0.5
    
        # Weighted combination
        stability = (
            config.stability_entropy_weight * entropy_score +
            config.stability_momentum_weight * momentum_score +
            config.stability_consistency_weight * consistency_score
        )
    
        return float(np.clip(stability, 0, 1))
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in compute_stability_score: {e}")
        raise


def detect_transition_type(
    current_dominant: str,
    prev_dominant: str,
    confidence_change: float
) -> IntentTransition:
    """
    Detect the type of intent transition.
    """
    try:
        if current_dominant == prev_dominant:
            return IntentTransition.STABLE
    
        # Check for reversal (opposite intents)
        opposites = {
            'urgent': 'passive',
            'passive': 'urgent',
            'mechanical': 'exploitative',
            'exploitative': 'mechanical',
        }
        if opposites.get(prev_dominant) == current_dominant:
            return IntentTransition.REVERSAL
    
        # Check for abrupt vs gradual
        if abs(confidence_change) > 0.3:
            return IntentTransition.ABRUPT
        else:
            return IntentTransition.GRADUAL
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in detect_transition_type: {e}")
        raise


def apply_impossible_state_rules(
    pi: np.ndarray,
    features: ObservableFeatures,
    config: MIDEConfig
) -> np.ndarray:
    """
    Enforce market microstructure constraints.
    """
    try:
        pi = pi.copy()
    
        # Rule 1: Urgent + Passive cannot both exceed threshold
        if pi[0] > 0.4 and pi[1] > 0.4:
            excess = (pi[0] + pi[1] - config.urgent_passive_max_sum) / 2
            if excess > 0:
                pi[0] -= excess
                pi[1] -= excess
                pi[4] += 2 * excess  # Redistribute to noise
    
        # Rule 2: Exploitative requires spread > threshold OR volume spike
        # (Using arrival_irregularity as proxy for volume spike)
        if features.spread_crossing_freq < 0.3 and features.arrival_irregularity < 1.0:
            excess = max(0, pi[3] - 0.2)
            if excess > 0:
                pi[3] -= excess
                pi[4] += excess
    
        # Rule 3: Noise floor minimum
        if pi[4] < NOISE_FLOOR:
            deficit = NOISE_FLOOR - pi[4]
            pi[4] = NOISE_FLOOR
            # Subtract from largest
            max_idx = np.argmax(pi[:4])
            pi[max_idx] -= deficit
    
        # Rule 4: Mechanical requires regular intervals (low CV)
        if features.arrival_irregularity > 0.5:
            excess = max(0, pi[2] - 0.15)
            if excess > 0:
                pi[2] -= excess
                pi[4] += excess
    
        # Ensure non-negative and renormalize
        pi = np.maximum(pi, MIN_INTENT_PROBABILITY)
        return pi / pi.sum()
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in apply_impossible_state_rules: {e}")
        raise


def apply_transition_constraints(
    pi_new: np.ndarray,
    pi_prev: np.ndarray,
    confidence: float,
    config: MIDEConfig
) -> np.ndarray:
    """
    Blend raw prediction with transition prior.
    """
    # Compute transition prior
    try:
        pi_prior = TRANSITION_MATRIX @ pi_prev
    
        # Adaptive blending based on confidence
        alpha = config.transition_alpha_min + (
            config.transition_alpha_max - config.transition_alpha_min
        ) * confidence
    
        # Blend
        pi_blended = alpha * pi_new + (1 - alpha) * pi_prior
    
        # Renormalize
        return pi_blended / pi_blended.sum()
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in apply_transition_constraints: {e}")
        raise
