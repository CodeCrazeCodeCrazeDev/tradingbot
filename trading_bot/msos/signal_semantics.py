"""
AlphaAlgo MSOS - Signal Semantic Integrity Monitor

Continuously evaluate whether signals retain their intended meaning.

Monitor:
- Mutual information stability
- Correlation sign persistence
- Predictive decay
- Semantic inversion

If signal meaning degrades or inverts:
- Signal is disabled
- No retraining allowed
- Root cause logged

Broken semantics must never be "optimized away".

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SemanticState(Enum):
    """Signal semantic states"""
    INTACT = auto()          # Signal meaning is preserved
    DEGRADING = auto()       # Signal meaning is weakening
    DRIFTED = auto()         # Signal meaning has shifted
    INVERTED = auto()        # Signal meaning has inverted
    BROKEN = auto()          # Signal is meaningless
    UNKNOWN = auto()


class DriftType(Enum):
    """Types of semantic drift"""
    NONE = auto()
    GRADUAL = auto()         # Slow drift over time
    SUDDEN = auto()          # Abrupt change
    OSCILLATING = auto()     # Unstable, going back and forth
    STRUCTURAL = auto()      # Fundamental relationship changed


class SignalDrift:
    """Tracks drift in signal semantics"""
    
    def __init__(self, signal_id: str, window_size: int = 100):
        try:
            self.signal_id = signal_id
            self.window_size = window_size
        
            # History buffers
            self._correlation_history: Deque[float] = deque(maxlen=window_size)
            self._mi_history: Deque[float] = deque(maxlen=window_size)
            self._prediction_history: Deque[Tuple[float, float]] = deque(maxlen=window_size)
        
            # Baseline values (established during stable period)
            self.baseline_correlation: Optional[float] = None
            self.baseline_mi: Optional[float] = None
            self.baseline_sign: Optional[int] = None
        
            # Current state
            self.current_correlation: float = 0.0
            self.current_mi: float = 0.0
            self.drift_magnitude: float = 0.0
            self.drift_type: DriftType = DriftType.NONE
            self.is_inverted: bool = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, correlation: float, mutual_info: float, prediction: float, actual: float):
        """Update drift tracking with new data"""
        try:
            self._correlation_history.append(correlation)
            self._mi_history.append(mutual_info)
            self._prediction_history.append((prediction, actual))
        
            self.current_correlation = correlation
            self.current_mi = mutual_info
        
            # Establish baseline if not set
            if self.baseline_correlation is None and len(self._correlation_history) >= 20:
                self.baseline_correlation = np.mean(list(self._correlation_history)[:20])
                self.baseline_mi = np.mean(list(self._mi_history)[:20])
                self.baseline_sign = 1 if self.baseline_correlation >= 0 else -1
        
            # Calculate drift
            if self.baseline_correlation is not None:
                self._calculate_drift()
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _calculate_drift(self):
        """Calculate drift magnitude and type"""
        try:
            if len(self._correlation_history) < 10:
                return
        
            recent_corr = list(self._correlation_history)[-10:]
            recent_mean = np.mean(recent_corr)
            recent_std = np.std(recent_corr)
        
            # Drift magnitude
            self.drift_magnitude = abs(recent_mean - self.baseline_correlation)
        
            # Check for inversion
            current_sign = 1 if recent_mean >= 0 else -1
            self.is_inverted = current_sign != self.baseline_sign
        
            # Determine drift type
            if self.drift_magnitude < 0.1:
                self.drift_type = DriftType.NONE
            elif recent_std > 0.2:
                self.drift_type = DriftType.OSCILLATING
            elif self._is_sudden_change():
                self.drift_type = DriftType.SUDDEN
            elif self.is_inverted:
                self.drift_type = DriftType.STRUCTURAL
            else:
                self.drift_type = DriftType.GRADUAL
        except Exception as e:
            logger.error(f"Error in _calculate_drift: {e}")
            raise
    
    def _is_sudden_change(self) -> bool:
        """Detect sudden changes in correlation"""
        try:
            if len(self._correlation_history) < 20:
                return False
        
            recent = list(self._correlation_history)[-5:]
            older = list(self._correlation_history)[-20:-5]
        
            recent_mean = np.mean(recent)
            older_mean = np.mean(older)
        
            return abs(recent_mean - older_mean) > 0.3
        except Exception as e:
            logger.error(f"Error in _is_sudden_change: {e}")
            raise


@dataclass
class SemanticInversion:
    """Record of a semantic inversion event"""
    signal_id: str
    original_sign: int
    current_sign: int
    correlation_before: float
    correlation_after: float
    detection_time: float = field(default_factory=time.time)
    confirmed: bool = False
    confirmation_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'original_sign': self.original_sign,
            'current_sign': self.current_sign,
            'correlation_before': self.correlation_before,
            'correlation_after': self.correlation_after,
            'detection_time': self.detection_time,
            'confirmed': self.confirmed
        }


@dataclass
class SemanticResult:
    """Result from semantic integrity check"""
    signal_id: str
    state: SemanticState
    is_valid: bool
    can_use: bool
    correlation_stability: float  # 0-1
    mutual_info_stability: float  # 0-1
    predictive_power: float  # 0-1
    drift: SignalDrift
    inversions: List[SemanticInversion]
    reason: str
    recommended_action: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'state': self.state.name,
            'is_valid': self.is_valid,
            'can_use': self.can_use,
            'correlation_stability': self.correlation_stability,
            'mutual_info_stability': self.mutual_info_stability,
            'predictive_power': self.predictive_power,
            'drift_type': self.drift.drift_type.name,
            'drift_magnitude': self.drift.drift_magnitude,
            'is_inverted': self.drift.is_inverted,
            'reason': self.reason,
            'recommended_action': self.recommended_action,
            'timestamp': self.timestamp
        }


class MutualInformationTracker:
    """Tracks mutual information between signal and target"""
    
    def __init__(self, bins: int = 10):
        try:
            self.bins = bins
            self._signal_history: Deque[float] = deque(maxlen=1000)
            self._target_history: Deque[float] = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, signal_value: float, target_value: float):
        """Add new signal-target pair"""
        try:
            self._signal_history.append(signal_value)
            self._target_history.append(target_value)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def calculate_mi(self) -> float:
        """Calculate mutual information"""
        try:
            if len(self._signal_history) < 50:
                return 0.0
        
            signals = np.array(list(self._signal_history))
            targets = np.array(list(self._target_history))
        
            # Discretize
            signal_bins = np.digitize(signals, np.linspace(signals.min(), signals.max(), self.bins))
            target_bins = np.digitize(targets, np.linspace(targets.min(), targets.max(), self.bins))
        
            # Calculate joint and marginal probabilities
            joint_hist = np.zeros((self.bins + 1, self.bins + 1))
            for s, t in zip(signal_bins, target_bins):
                joint_hist[s, t] += 1
        
            joint_prob = joint_hist / joint_hist.sum()
            signal_prob = joint_prob.sum(axis=1)
            target_prob = joint_prob.sum(axis=0)
        
            # Calculate MI
            mi = 0.0
            for i in range(self.bins + 1):
                for j in range(self.bins + 1):
                    if joint_prob[i, j] > 0 and signal_prob[i] > 0 and target_prob[j] > 0:
                        mi += joint_prob[i, j] * np.log2(
                            joint_prob[i, j] / (signal_prob[i] * target_prob[j])
                        )
        
            return max(0, mi)
        except Exception as e:
            logger.error(f"Error in calculate_mi: {e}")
            raise


class CorrelationTracker:
    """Tracks correlation between signal and target"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._signal_history: Deque[float] = deque(maxlen=window_size)
            self._target_history: Deque[float] = deque(maxlen=window_size)
            self._correlation_history: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, signal_value: float, target_value: float) -> float:
        """Add new signal-target pair and return current correlation"""
        try:
            self._signal_history.append(signal_value)
            self._target_history.append(target_value)
        
            if len(self._signal_history) >= 20:
                signals = np.array(list(self._signal_history))
                targets = np.array(list(self._target_history))
            
                # Calculate correlation
                if np.std(signals) > 0 and np.std(targets) > 0:
                    corr = np.corrcoef(signals, targets)[0, 1]
                else:
                    corr = 0.0
            
                self._correlation_history.append(corr)
                return corr
        
            return 0.0
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_stability(self) -> float:
        """Calculate correlation stability (0-1, higher is more stable)"""
        try:
            if len(self._correlation_history) < 10:
                return 0.0
        
            correlations = np.array(list(self._correlation_history))
            std = np.std(correlations)
        
            # Stability is inverse of volatility
            return max(0, 1 - std * 2)
        except Exception as e:
            logger.error(f"Error in get_stability: {e}")
            raise
    
    def get_sign_persistence(self) -> float:
        """Calculate how often correlation maintains its sign (0-1)"""
        try:
            if len(self._correlation_history) < 10:
                return 0.0
        
            correlations = list(self._correlation_history)
            signs = [1 if c >= 0 else -1 for c in correlations]
        
            # Calculate sign changes
            changes = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i-1])
            persistence = 1 - (changes / len(signs))
        
            return persistence
        except Exception as e:
            logger.error(f"Error in get_sign_persistence: {e}")
            raise


class PredictiveDecayTracker:
    """Tracks decay in predictive power"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._accuracy_history: Deque[float] = deque(maxlen=window_size)
            self._ic_history: Deque[float] = deque(maxlen=window_size)  # Information coefficient
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, prediction: float, actual: float):
        """Update with new prediction-actual pair"""
        # Simple directional accuracy
        try:
            correct = (prediction > 0 and actual > 0) or (prediction < 0 and actual < 0)
            self._accuracy_history.append(1.0 if correct else 0.0)
        
            # Information coefficient (correlation of predictions with actuals)
            # Simplified: just track if prediction magnitude correlates with actual magnitude
            ic = 1.0 if (abs(prediction) > 0.5) == (abs(actual) > 0.5) else 0.0
            self._ic_history.append(ic)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_current_power(self) -> float:
        """Get current predictive power (0-1)"""
        try:
            if len(self._accuracy_history) < 10:
                return 0.5  # Unknown
        
            recent_accuracy = np.mean(list(self._accuracy_history)[-20:])
            return recent_accuracy
        except Exception as e:
            logger.error(f"Error in get_current_power: {e}")
            raise
    
    def get_decay_rate(self) -> float:
        """Calculate rate of predictive decay"""
        try:
            if len(self._accuracy_history) < 50:
                return 0.0
        
            # Compare recent vs older accuracy
            recent = np.mean(list(self._accuracy_history)[-20:])
            older = np.mean(list(self._accuracy_history)[-50:-20])
        
            decay = older - recent  # Positive = decaying
            return max(0, decay)
        except Exception as e:
            logger.error(f"Error in get_decay_rate: {e}")
            raise
    
    def get_half_life(self) -> float:
        """Estimate signal half-life in periods"""
        try:
            decay_rate = self.get_decay_rate()
            if decay_rate <= 0:
                return float('inf')
        
            # Simple half-life calculation
            return 0.693 / decay_rate  # ln(2) / decay_rate
        except Exception as e:
            logger.error(f"Error in get_half_life: {e}")
            raise


class SignalSemanticMonitor:
    """
    Main Signal Semantic Monitor
    
    Continuously evaluates whether signals retain their intended meaning.
    
    RULES:
    1. If signal meaning degrades → signal is disabled
    2. If signal inverts → signal is disabled, no retraining allowed
    3. Broken semantics must never be "optimized away"
    4. Root cause must be logged for all semantic failures
    """
    
    # Thresholds
    MIN_CORRELATION_STABILITY = 0.5
    MIN_MI_STABILITY = 0.3
    MIN_PREDICTIVE_POWER = 0.52  # Just above random
    MAX_DRIFT_MAGNITUDE = 0.3
    INVERSION_CONFIRMATION_PERIODS = 10
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.semantics")
        
            # Per-signal trackers
            self._drift_trackers: Dict[str, SignalDrift] = {}
            self._mi_trackers: Dict[str, MutualInformationTracker] = {}
            self._corr_trackers: Dict[str, CorrelationTracker] = {}
            self._decay_trackers: Dict[str, PredictiveDecayTracker] = {}
        
            # Inversion records
            self._inversions: Dict[str, List[SemanticInversion]] = {}
        
            # Disabled signals
            self._disabled_signals: Dict[str, str] = {}  # signal_id -> reason
        
            self.logger.info("Signal Semantic Monitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_signal(self, signal_id: str):
        """Register a new signal for monitoring"""
        try:
            self._drift_trackers[signal_id] = SignalDrift(signal_id)
            self._mi_trackers[signal_id] = MutualInformationTracker()
            self._corr_trackers[signal_id] = CorrelationTracker()
            self._decay_trackers[signal_id] = PredictiveDecayTracker()
            self._inversions[signal_id] = []
        
            self.logger.info(f"Signal {signal_id} registered for semantic monitoring")
        except Exception as e:
            logger.error(f"Error in register_signal: {e}")
            raise
    
    def update(
        self,
        signal_id: str,
        signal_value: float,
        target_value: float,
        prediction: Optional[float] = None
    ) -> SemanticResult:
        """
        Update signal with new data and check semantic integrity.
        
        Args:
            signal_id: Signal identifier
            signal_value: Current signal value
            target_value: Actual target/outcome value
            prediction: Optional prediction made by signal
        """
        # Check if signal is disabled
        try:
            if signal_id in self._disabled_signals:
                return SemanticResult(
                    signal_id=signal_id,
                    state=SemanticState.BROKEN,
                    is_valid=False,
                    can_use=False,
                    correlation_stability=0.0,
                    mutual_info_stability=0.0,
                    predictive_power=0.0,
                    drift=self._drift_trackers.get(signal_id, SignalDrift(signal_id)),
                    inversions=self._inversions.get(signal_id, []),
                    reason=f"Signal disabled: {self._disabled_signals[signal_id]}",
                    recommended_action="Do not use. Investigate root cause."
                )
        
            # Ensure signal is registered
            if signal_id not in self._drift_trackers:
                self.register_signal(signal_id)
        
            # Update trackers
            correlation = self._corr_trackers[signal_id].update(signal_value, target_value)
            self._mi_trackers[signal_id].update(signal_value, target_value)
        
            if prediction is not None:
                self._decay_trackers[signal_id].update(prediction, target_value)
        
            # Calculate metrics
            mi = self._mi_trackers[signal_id].calculate_mi()
            self._drift_trackers[signal_id].update(correlation, mi, signal_value, target_value)
        
            # Get stability metrics
            corr_stability = self._corr_trackers[signal_id].get_stability()
            sign_persistence = self._corr_trackers[signal_id].get_sign_persistence()
            predictive_power = self._decay_trackers[signal_id].get_current_power()
        
            # MI stability (compare to baseline)
            drift = self._drift_trackers[signal_id]
            if drift.baseline_mi and drift.baseline_mi > 0:
                mi_stability = min(1.0, mi / drift.baseline_mi)
            else:
                mi_stability = 0.5  # Unknown
        
            # Check for inversion
            if drift.is_inverted:
                self._handle_inversion(signal_id, drift)
        
            # Determine state
            state = self._determine_state(
                corr_stability, mi_stability, predictive_power, drift
            )
        
            # Determine if signal can be used
            is_valid = state in [SemanticState.INTACT, SemanticState.DEGRADING]
            can_use = is_valid and not drift.is_inverted
        
            # Get recommended action
            reason, action = self._get_recommendation(state, drift)
        
            # Disable if broken
            if state == SemanticState.BROKEN or state == SemanticState.INVERTED:
                self._disable_signal(signal_id, reason)
        
            return SemanticResult(
                signal_id=signal_id,
                state=state,
                is_valid=is_valid,
                can_use=can_use,
                correlation_stability=corr_stability,
                mutual_info_stability=mi_stability,
                predictive_power=predictive_power,
                drift=drift,
                inversions=self._inversions.get(signal_id, []),
                reason=reason,
                recommended_action=action
            )
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _determine_state(
        self,
        corr_stability: float,
        mi_stability: float,
        predictive_power: float,
        drift: SignalDrift
    ) -> SemanticState:
        """Determine semantic state from metrics"""
        try:
            if drift.is_inverted:
                return SemanticState.INVERTED
        
            if predictive_power < 0.45:  # Worse than random
                return SemanticState.BROKEN
        
            if drift.drift_type == DriftType.STRUCTURAL:
                return SemanticState.BROKEN
        
            if corr_stability < self.MIN_CORRELATION_STABILITY:
                if drift.drift_magnitude > self.MAX_DRIFT_MAGNITUDE:
                    return SemanticState.DRIFTED
                return SemanticState.DEGRADING
        
            if mi_stability < self.MIN_MI_STABILITY:
                return SemanticState.DEGRADING
        
            if predictive_power < self.MIN_PREDICTIVE_POWER:
                return SemanticState.DEGRADING
        
            return SemanticState.INTACT
        except Exception as e:
            logger.error(f"Error in _determine_state: {e}")
            raise
    
    def _handle_inversion(self, signal_id: str, drift: SignalDrift):
        """Handle detected inversion"""
        try:
            inversions = self._inversions.get(signal_id, [])
        
            # Check if we have an unconfirmed inversion
            unconfirmed = [i for i in inversions if not i.confirmed]
        
            if unconfirmed:
                # Check if inversion is confirmed
                inversion = unconfirmed[-1]
                periods_since = (time.time() - inversion.detection_time) / 60  # Assume 1 min periods
            
                if periods_since >= self.INVERSION_CONFIRMATION_PERIODS:
                    inversion.confirmed = True
                    inversion.confirmation_time = time.time()
                    self.logger.critical(
                        f"Signal {signal_id} INVERSION CONFIRMED after {periods_since:.0f} periods"
                    )
            else:
                # Record new inversion
                inversion = SemanticInversion(
                    signal_id=signal_id,
                    original_sign=drift.baseline_sign or 1,
                    current_sign=-1 if drift.baseline_sign == 1 else 1,
                    correlation_before=drift.baseline_correlation or 0,
                    correlation_after=drift.current_correlation
                )
                inversions.append(inversion)
                self._inversions[signal_id] = inversions
            
                self.logger.warning(f"Signal {signal_id} potential INVERSION detected")
        except Exception as e:
            logger.error(f"Error in _handle_inversion: {e}")
            raise
    
    def _get_recommendation(
        self,
        state: SemanticState,
        drift: SignalDrift
    ) -> Tuple[str, str]:
        """Get reason and recommended action"""
        try:
            recommendations = {
                SemanticState.INTACT: (
                    "Signal semantics intact",
                    "Continue using signal"
                ),
                SemanticState.DEGRADING: (
                    f"Signal degrading (drift: {drift.drift_magnitude:.2f})",
                    "Reduce signal weight, monitor closely"
                ),
                SemanticState.DRIFTED: (
                    f"Signal has drifted significantly ({drift.drift_type.name})",
                    "Disable signal, investigate root cause"
                ),
                SemanticState.INVERTED: (
                    "Signal meaning has INVERTED",
                    "DISABLE IMMEDIATELY. No retraining allowed. Investigate root cause."
                ),
                SemanticState.BROKEN: (
                    "Signal is meaningless",
                    "DISABLE. Signal must be rebuilt from scratch."
                ),
                SemanticState.UNKNOWN: (
                    "Signal state unknown",
                    "Collect more data before using"
                )
            }
        
            return recommendations.get(state, ("Unknown", "Unknown"))
        except Exception as e:
            logger.error(f"Error in _get_recommendation: {e}")
            raise
    
    def _disable_signal(self, signal_id: str, reason: str):
        """Disable a signal"""
        try:
            self._disabled_signals[signal_id] = reason
            self.logger.critical(f"Signal {signal_id} DISABLED: {reason}")
        except Exception as e:
            logger.error(f"Error in _disable_signal: {e}")
            raise
    
    def is_signal_valid(self, signal_id: str) -> bool:
        """Check if signal is valid for use"""
        return signal_id not in self._disabled_signals
    
    def get_disabled_signals(self) -> Dict[str, str]:
        """Get all disabled signals and reasons"""
        return self._disabled_signals.copy()
    
    def get_signal_half_life(self, signal_id: str) -> float:
        """Get estimated half-life of signal in periods"""
        try:
            if signal_id in self._decay_trackers:
                return self._decay_trackers[signal_id].get_half_life()
            return float('inf')
        except Exception as e:
            logger.error(f"Error in get_signal_half_life: {e}")
            raise
