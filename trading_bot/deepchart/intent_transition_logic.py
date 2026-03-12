"""
Market Intent Decomposition Engine (MIDE) - Transition Logic

Handles intent consistency constraints, transition smoothing,
and impossible state suppression based on market microstructure theory.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Deque
from collections import deque

from .intent_decomposition_core import (
    IntentSimplex, IntentState, IntentTransition, MIDEConfig,
    ObservableFeatures, TRANSITION_MATRIX, INTENT_NAMES,
    MIN_INTENT_PROBABILITY, NOISE_FLOOR,
    apply_impossible_state_rules, apply_transition_constraints,
    detect_transition_type
)

import logging
logger = logging.getLogger(__name__)



# =============================================================================
# TRANSITION CONSTRAINT RULES
# =============================================================================

@dataclass
class TransitionRule:
    """
    A single transition constraint rule.
    """
    from_intent: str
    to_intent: str
    max_probability: float
    description: str


# Disallowed or constrained transitions based on market microstructure
TRANSITION_RULES = [
    TransitionRule('urgent', 'passive', 0.15, 
                   'Urgent traders do not suddenly become passive'),
    TransitionRule('passive', 'urgent', 0.15,
                   'Passive accumulators do not suddenly become urgent'),
    TransitionRule('mechanical', 'exploitative', 0.10,
                   'Algorithmic flow does not become opportunistic'),
    TransitionRule('exploitative', 'passive', 0.15,
                   'Market makers do not become passive accumulators'),
]


# =============================================================================
# VOLATILITY REGIME DETECTOR
# =============================================================================

class VolatilityRegimeDetector:
    """
    Detects volatility regime for adaptive smoothing.
    """
    
    def __init__(self, lookback: int = 50):
        try:
            self.lookback = lookback
            self._returns: Deque[float] = deque(maxlen=lookback)
            self._vol_history: Deque[float] = deque(maxlen=20)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, price: float, prev_price: Optional[float]) -> str:
        """
        Update with new price and return regime.
        
        Returns:
            'high', 'medium', or 'low'
        """
        try:
            if prev_price is not None and prev_price > 0:
                ret = (price - prev_price) / prev_price
                self._returns.append(ret)
        
            if len(self._returns) < 10:
                return 'medium'
        
            # Compute current volatility
            current_vol = np.std(list(self._returns))
            self._vol_history.append(current_vol)
        
            if len(self._vol_history) < 5:
                return 'medium'
        
            # Compare to historical
            avg_vol = np.mean(list(self._vol_history))
        
            if current_vol > 1.5 * avg_vol:
                return 'high'
            elif current_vol < 0.5 * avg_vol:
                return 'low'
            else:
                return 'medium'
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


# =============================================================================
# INTENT SMOOTHER
# =============================================================================

class IntentSmoother:
    """
    Adaptive smoothing based on market conditions.
    
    High volatility → more responsive (fast EMA)
    Low volatility → more smooth (slow EMA)
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        try:
            self.config = config or MIDEConfig()
            self.ema_fast = 0.3   # Responsive
            self.ema_slow = 0.9   # Smooth
            self.ema_medium = 0.6
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def smooth(self, pi_new: np.ndarray, pi_prev: np.ndarray, 
               volatility_regime: str) -> np.ndarray:
        """
        Apply adaptive smoothing.
        
        Args:
            pi_new: New intent probabilities
            pi_prev: Previous intent probabilities
            volatility_regime: 'high', 'medium', or 'low'
        
        Returns:
            Smoothed probabilities
        """
        try:
            if volatility_regime == 'high':
                alpha = self.ema_fast
            elif volatility_regime == 'low':
                alpha = self.ema_slow
            else:
                alpha = self.ema_medium
        
            smoothed = alpha * pi_new + (1 - alpha) * pi_prev
        
            # Renormalize
            return smoothed / smoothed.sum()
        except Exception as e:
            logger.error(f"Error in smooth: {e}")
            raise


# =============================================================================
# IMPOSSIBLE STATE SUPPRESSOR
# =============================================================================

class ImpossibleStateSuppressor:
    """
    Enforces market microstructure constraints on intent distribution.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        try:
            self.config = config or MIDEConfig()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def suppress(self, pi: np.ndarray, features: ObservableFeatures) -> np.ndarray:
        """
        Apply impossible state rules.
        
        Rules:
        1. Urgent + Passive cannot both exceed 0.4
        2. Exploitative requires spread > 1.5σ OR volume spike
        3. Noise floor minimum 0.05
        4. Mechanical requires regular intervals (CV < 0.3)
        
        Args:
            pi: Intent probabilities [5]
            features: Current observable features
        
        Returns:
            Constrained probabilities
        """
        try:
            pi = pi.copy()
        
            # Rule 1: Urgent + Passive conflict
            urgent_passive_sum = pi[0] + pi[1]
            if urgent_passive_sum > self.config.urgent_passive_max_sum:
                excess = urgent_passive_sum - self.config.urgent_passive_max_sum
                # Reduce both proportionally
                ratio = pi[0] / (pi[0] + pi[1] + 1e-8)
                pi[0] -= excess * ratio
                pi[1] -= excess * (1 - ratio)
                pi[4] += excess  # Add to noise
        
            # Rule 2: Exploitative conditions
            # High spread crossing freq suggests spread is wide enough
            # High arrival irregularity suggests volume spike
            spread_condition = features.spread_crossing_freq > 0.3
            volume_condition = features.arrival_irregularity > 1.0
        
            if not spread_condition and not volume_condition:
                # Exploitative unlikely without these conditions
                excess = max(0, pi[3] - 0.2)
                if excess > 0:
                    pi[3] -= excess
                    pi[4] += excess
        
            # Rule 3: Noise floor
            if pi[4] < NOISE_FLOOR:
                deficit = NOISE_FLOOR - pi[4]
                pi[4] = NOISE_FLOOR
                # Subtract from largest non-noise
                max_idx = np.argmax(pi[:4])
                pi[max_idx] = max(MIN_INTENT_PROBABILITY, pi[max_idx] - deficit)
        
            # Rule 4: Mechanical requires regular arrivals
            if features.arrival_irregularity > 0.5:
                # High irregularity = not mechanical
                excess = max(0, pi[2] - 0.15)
                if excess > 0:
                    pi[2] -= excess
                    pi[4] += excess
        
            # Ensure all positive
            pi = np.maximum(pi, MIN_INTENT_PROBABILITY)
        
            # Renormalize
            return pi / pi.sum()
        except Exception as e:
            logger.error(f"Error in suppress: {e}")
            raise


# =============================================================================
# TRANSITION CONSTRAINT ENFORCER
# =============================================================================

class TransitionConstraintEnforcer:
    """
    Enforces transition constraints using the transition matrix.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        try:
            self.config = config or MIDEConfig()
            self.transition_matrix = TRANSITION_MATRIX.copy()
        
            # Apply additional rules
            for rule in TRANSITION_RULES:
                from_idx = INTENT_NAMES.index(rule.from_intent)
                to_idx = INTENT_NAMES.index(rule.to_intent)
                self.transition_matrix[from_idx, to_idx] = min(
                    self.transition_matrix[from_idx, to_idx],
                    rule.max_probability
                )
        
            # Renormalize rows
            for i in range(5):
                self.transition_matrix[i] /= self.transition_matrix[i].sum()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def enforce(self, pi_new: np.ndarray, pi_prev: np.ndarray,
                confidence: float) -> np.ndarray:
        """
        Blend raw prediction with transition prior.
        
        Args:
            pi_new: New raw probabilities
            pi_prev: Previous probabilities
            confidence: Confidence in new prediction (0-1)
        
        Returns:
            Constrained probabilities
        """
        # Compute transition prior
        try:
            pi_prior = self.transition_matrix @ pi_prev
        
            # Adaptive blending based on confidence
            alpha = self.config.transition_alpha_min + (
                self.config.transition_alpha_max - self.config.transition_alpha_min
            ) * confidence
        
            # Blend
            pi_blended = alpha * pi_new + (1 - alpha) * pi_prior
        
            # Renormalize
            return pi_blended / pi_blended.sum()
        except Exception as e:
            logger.error(f"Error in enforce: {e}")
            raise
    
    def check_violation(self, pi_new: np.ndarray, pi_prev: np.ndarray) -> List[str]:
        """
        Check for transition rule violations.
        
        Returns:
            List of violation descriptions
        """
        try:
            violations = []
        
            for rule in TRANSITION_RULES:
                from_idx = INTENT_NAMES.index(rule.from_intent)
                to_idx = INTENT_NAMES.index(rule.to_intent)
            
                # Check if transitioning from high probability of from_intent
                # to high probability of to_intent
                if pi_prev[from_idx] > 0.4 and pi_new[to_idx] > rule.max_probability:
                    violations.append(
                        f"Violation: {rule.from_intent} -> {rule.to_intent} "
                        f"(prev={pi_prev[from_idx]:.2f}, new={pi_new[to_idx]:.2f}): "
                        f"{rule.description}"
                    )
        
            return violations
        except Exception as e:
            logger.error(f"Error in check_violation: {e}")
            raise


# =============================================================================
# UNIFIED TRANSITION LOGIC
# =============================================================================

class IntentTransitionLogic:
    """
    Unified transition logic combining all constraints.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        try:
            self.config = config or MIDEConfig()
        
            self.volatility_detector = VolatilityRegimeDetector()
            self.smoother = IntentSmoother(config)
            self.suppressor = ImpossibleStateSuppressor(config)
            self.constraint_enforcer = TransitionConstraintEnforcer(config)
        
            # State
            self._prev_simplex: Optional[np.ndarray] = None
            self._prev_dominant: str = 'noise'
            self._prev_price: Optional[float] = None
            self._bars_in_state: int = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process(self, raw_simplex: IntentSimplex, 
                features: ObservableFeatures,
                price: float) -> Tuple[IntentSimplex, IntentTransition, int]:
        """
        Process raw intent simplex through all constraints.
        
        Args:
            raw_simplex: Raw output from inference engine
            features: Current observable features
            price: Current price (for volatility detection)
        
        Returns:
            Tuple of (constrained_simplex, transition_type, bars_in_state)
        """
        try:
            pi_new = raw_simplex.to_array()
        
            # Update volatility regime
            vol_regime = self.volatility_detector.update(price, self._prev_price)
            self._prev_price = price
        
            # Initialize previous if needed
            if self._prev_simplex is None:
                self._prev_simplex = np.array([0.2, 0.2, 0.2, 0.2, 0.2], dtype=np.float32)
        
            # Step 1: Apply transition constraints
            confidence = float(np.max(pi_new) - np.partition(pi_new, -2)[-2])
            pi_constrained = self.constraint_enforcer.enforce(
                pi_new, self._prev_simplex, confidence
            )
        
            # Step 2: Apply impossible state suppression
            pi_suppressed = self.suppressor.suppress(pi_constrained, features)
        
            # Step 3: Apply adaptive smoothing
            pi_smoothed = self.smoother.smooth(
                pi_suppressed, self._prev_simplex, vol_regime
            )
        
            # Detect transition
            current_dominant = INTENT_NAMES[np.argmax(pi_smoothed)]
            confidence_change = float(np.max(pi_smoothed) - np.max(self._prev_simplex))
        
            transition_type = detect_transition_type(
                current_dominant, self._prev_dominant, confidence_change
            )
        
            # Update bars in state
            if current_dominant == self._prev_dominant:
                self._bars_in_state += 1
            else:
                self._bars_in_state = 1
        
            # Update state
            self._prev_simplex = pi_smoothed.copy()
            self._prev_dominant = current_dominant
        
            # Create output simplex
            output_simplex = IntentSimplex.from_array(pi_smoothed)
        
            return output_simplex, transition_type, self._bars_in_state
        except Exception as e:
            logger.error(f"Error in process: {e}")
            raise
    
    def get_transition_probability(self, from_intent: str, to_intent: str) -> float:
        """
        Get transition probability between intents.
        """
        try:
            from_idx = INTENT_NAMES.index(from_intent)
            to_idx = INTENT_NAMES.index(to_intent)
            return float(self.constraint_enforcer.transition_matrix[from_idx, to_idx])
        except Exception as e:
            logger.error(f"Error in get_transition_probability: {e}")
            raise
    
    def reset(self):
        """Reset state."""
        try:
            self._prev_simplex = None
            self._prev_dominant = 'noise'
            self._prev_price = None
            self._bars_in_state = 0
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


# =============================================================================
# TRANSITION VALIDATOR
# =============================================================================

class TransitionValidator:
    """
    Validates intent transitions for debugging and monitoring.
    """
    
    def __init__(self):
        try:
            self._history: Deque[Tuple[str, float]] = deque(maxlen=100)
            self._violations: List[str] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, simplex: IntentSimplex, 
                 prev_simplex: Optional[IntentSimplex]) -> List[str]:
        """
        Validate transition and return any warnings.
        """
        try:
            warnings = []
        
            if prev_simplex is None:
                return warnings
        
            pi_new = simplex.to_array()
            pi_prev = prev_simplex.to_array()
        
            # Check for sudden large changes
            max_change = np.max(np.abs(pi_new - pi_prev))
            if max_change > 0.4:
                warnings.append(f"Large intent change detected: {max_change:.2f}")
        
            # Check for impossible transitions
            enforcer = TransitionConstraintEnforcer()
            violations = enforcer.check_violation(pi_new, pi_prev)
            warnings.extend(violations)
        
            # Check for degenerate states
            if simplex.entropy > 0.95:
                warnings.append("Near-uniform distribution (high uncertainty)")
        
            # Check for stuck state
            self._history.append((simplex.dominant_intent, simplex.dominant_probability))
            if len(self._history) >= 50:
                recent_dominants = [h[0] for h in list(self._history)[-50:]]
                if len(set(recent_dominants)) == 1:
                    warnings.append(f"Stuck in {recent_dominants[0]} for 50+ bars")
        
            self._violations.extend(warnings)
            return warnings
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    @property
    def recent_violations(self) -> List[str]:
        """Get recent violations."""
        return self._violations[-10:]
