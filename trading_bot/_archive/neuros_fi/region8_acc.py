"""
NEUROS-FI Region 8: Anterior Cingulate Cortex - Conflict Detection and Uncertainty Management
==============================================================================================

Biological Basis:
The ACC monitors for response conflict — when multiple neural pathways generate
competing outputs, the ACC detects this conflict and signals the need for
additional cortical control. It also tracks error likelihood in uncertain
situations and adjusts cognitive control allocation accordingly.

High ACC activity = high uncertainty = recruit more processing resources.

Citations:
- Botvinick et al. (2001) - Conflict monitoring and cognitive control
- Shenhav et al. (2013) - The expected value of control
- Holroyd & Coles (2002) - The neural basis of human error processing
- Rushworth et al. (2004) - Action sets and decisions in the medial frontal cortex

Constitutional Version: 5.0
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts detected by the ACC."""
    
    MODEL_DISAGREEMENT = auto()    # Models predict different outcomes
    SIGNAL_CONFLICT = auto()       # Signals point in opposite directions
    STRATEGY_CONFLICT = auto()     # Strategies recommend conflicting actions
    REGIME_AMBIGUITY = auto()      # Unclear which regime we're in
    VALUE_CONFLICT = auto()        # Risk vs reward tradeoff unclear


class UncertaintySource(Enum):
    """Sources of uncertainty."""
    
    EPISTEMIC = auto()    # Model uncertainty (can be reduced with more data)
    ALEATORIC = auto()    # Inherent randomness (cannot be reduced)
    DISTRIBUTIONAL = auto()  # Out-of-distribution inputs


class ConflictSeverity(Enum):
    """Severity levels for detected conflicts."""
    
    NONE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ConflictSignal:
    """A detected conflict signal from the ACC."""
    
    signal_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    timestamp: datetime
    
    # Conflict details
    conflicting_sources: List[str]
    prediction_variance: float
    disagreement_magnitude: float
    
    # Recommended response
    additional_control_needed: float  # 0-1
    consensus_threshold_adjustment: float
    position_size_reduction: float
    
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UncertaintyEstimate:
    """Uncertainty estimate for a prediction or decision."""
    
    estimate_id: str
    timestamp: datetime
    target: str
    
    # Uncertainty components
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    total_uncertainty: float
    
    # Calibration
    confidence_interval: Tuple[float, float]
    calibration_score: float  # How well-calibrated are our uncertainties
    
    # Source
    source: UncertaintySource


@dataclass
class ErrorMonitoringResult:
    """Result of error monitoring for a prediction."""
    
    prediction_id: str
    timestamp: datetime
    signal_class: str
    
    # Error tracking
    predicted_value: float
    actual_value: float
    error: float
    error_rate_baseline: float
    error_rate_current: float
    
    # Spike detection
    is_error_spike: bool
    spike_magnitude: float


class ConflictDetection:
    """
    Conflict Detection System - monitors for response conflict.
    
    When multiple neural pathways generate competing outputs,
    the ACC detects this conflict and signals the need for
    additional cortical control.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Conflict thresholds
        self._variance_threshold = 2.0  # 2x historical average
        self._disagreement_threshold = 0.5  # 50% disagreement
        
        # Historical variance tracking
        self._variance_history: Dict[str, List[float]] = {}
        self._variance_window = 100
        
        # Conflict history
        self._conflicts: List[ConflictSignal] = []
    
    def detect_model_conflict(
        self,
        predictions: Dict[str, float],
        model_weights: Optional[Dict[str, float]] = None
    ) -> Optional[ConflictSignal]:
        """
        Detect conflict when models disagree significantly.
        
        Monitors variance of predictions across the Model Parliament.
        """
        with self._lock:
            if len(predictions) < 2:
                return None
            
            values = list(predictions.values())
            
            # Compute prediction variance
            variance = np.var(values)
            mean_pred = np.mean(values)
            std_pred = np.std(values)
            
            # Get historical average variance
            hist_key = "model_predictions"
            if hist_key not in self._variance_history:
                self._variance_history[hist_key] = []
            
            self._variance_history[hist_key].append(variance)
            if len(self._variance_history[hist_key]) > self._variance_window:
                self._variance_history[hist_key] = self._variance_history[hist_key][-self._variance_window:]
            
            historical_avg = np.mean(self._variance_history[hist_key][:-1]) if len(self._variance_history[hist_key]) > 1 else variance
            
            # Check if variance exceeds threshold
            if historical_avg > 0 and variance > self._variance_threshold * historical_avg:
                # Significant model disagreement
                severity = self._compute_severity(variance / max(historical_avg, 0.001))
                
                # Find most conflicting models
                conflicting = []
                for model, pred in predictions.items():
                    if abs(pred - mean_pred) > std_pred:
                        conflicting.append(model)
                
                signal = ConflictSignal(
                    signal_id=f"conflict_{int(time.time()*1000)}",
                    conflict_type=ConflictType.MODEL_DISAGREEMENT,
                    severity=severity,
                    timestamp=datetime.utcnow(),
                    conflicting_sources=conflicting,
                    prediction_variance=variance,
                    disagreement_magnitude=std_pred / max(abs(mean_pred), 0.001),
                    additional_control_needed=min(1.0, variance / (self._variance_threshold * historical_avg)),
                    consensus_threshold_adjustment=0.1 * severity.value,
                    position_size_reduction=0.1 * severity.value,
                    context={'predictions': predictions},
                )
                
                self._conflicts.append(signal)
                if len(self._conflicts) > 10000:
                    self._conflicts = self._conflicts[-5000:]
                
                return signal
            
            return None
    
    def detect_signal_conflict(
        self,
        signals: Dict[str, float]
    ) -> Optional[ConflictSignal]:
        """
        Detect conflict when signals point in opposite directions.
        """
        with self._lock:
            if len(signals) < 2:
                return None
            
            values = list(signals.values())
            
            # Check for sign disagreement
            positive = sum(1 for v in values if v > 0)
            negative = sum(1 for v in values if v < 0)
            
            total = len(values)
            disagreement = min(positive, negative) / total if total > 0 else 0
            
            if disagreement > self._disagreement_threshold:
                severity = self._compute_severity(disagreement / self._disagreement_threshold)
                
                conflicting = [
                    name for name, val in signals.items()
                    if (val > 0 and positive < negative) or (val < 0 and positive > negative)
                ]
                
                signal = ConflictSignal(
                    signal_id=f"conflict_{int(time.time()*1000)}",
                    conflict_type=ConflictType.SIGNAL_CONFLICT,
                    severity=severity,
                    timestamp=datetime.utcnow(),
                    conflicting_sources=conflicting,
                    prediction_variance=np.var(values),
                    disagreement_magnitude=disagreement,
                    additional_control_needed=disagreement,
                    consensus_threshold_adjustment=0.15 * severity.value,
                    position_size_reduction=0.15 * severity.value,
                    context={'signals': signals},
                )
                
                self._conflicts.append(signal)
                return signal
            
            return None
    
    def detect_regime_ambiguity(
        self,
        regime_probabilities: Dict[str, float]
    ) -> Optional[ConflictSignal]:
        """
        Detect ambiguity when regime classification is unclear.
        """
        with self._lock:
            if not regime_probabilities:
                return None
            
            probs = list(regime_probabilities.values())
            max_prob = max(probs)
            
            # Entropy-based ambiguity
            entropy = -sum(p * np.log(p + 1e-10) for p in probs if p > 0)
            max_entropy = np.log(len(probs))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            # High entropy = high ambiguity
            if normalized_entropy > 0.7 or max_prob < 0.4:
                severity = self._compute_severity(normalized_entropy / 0.7)
                
                signal = ConflictSignal(
                    signal_id=f"conflict_{int(time.time()*1000)}",
                    conflict_type=ConflictType.REGIME_AMBIGUITY,
                    severity=severity,
                    timestamp=datetime.utcnow(),
                    conflicting_sources=list(regime_probabilities.keys()),
                    prediction_variance=np.var(probs),
                    disagreement_magnitude=normalized_entropy,
                    additional_control_needed=normalized_entropy,
                    consensus_threshold_adjustment=0.2 * severity.value,
                    position_size_reduction=0.2 * severity.value,
                    context={'regime_probs': regime_probabilities, 'entropy': entropy},
                )
                
                self._conflicts.append(signal)
                return signal
            
            return None
    
    def _compute_severity(self, ratio: float) -> ConflictSeverity:
        """Compute conflict severity from ratio."""
        if ratio < 1.5:
            return ConflictSeverity.LOW
        elif ratio < 2.5:
            return ConflictSeverity.MODERATE
        elif ratio < 4.0:
            return ConflictSeverity.HIGH
        else:
            return ConflictSeverity.CRITICAL
    
    def get_recent_conflicts(self, limit: int = 100) -> List[ConflictSignal]:
        """Get recent conflict signals."""
        with self._lock:
            return self._conflicts[-limit:]
    
    def get_conflict_rate(self, window_minutes: int = 60) -> float:
        """Get conflict rate over recent window."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent = [c for c in self._conflicts if c.timestamp > cutoff]
            return len(recent) / max(window_minutes, 1)


class UncertaintyManagement:
    """
    Uncertainty Management System - tracks and quantifies uncertainty.
    
    High ACC activity in a specific domain triggers increased allocation
    of exploration budget toward that domain.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Uncertainty tracking by domain
        self._uncertainty_by_domain: Dict[str, List[UncertaintyEstimate]] = {}
        
        # Calibration tracking
        self._calibration_history: List[Tuple[float, float, bool]] = []  # (predicted, actual, in_interval)
        
        # Exploration budget allocation
        self._exploration_budget: Dict[str, float] = {}
        self._total_exploration_budget = 1.0
    
    def estimate_uncertainty(
        self,
        predictions: List[float],
        domain: str,
        target: str
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty from ensemble predictions.
        
        Uses prediction variance as epistemic uncertainty proxy.
        """
        with self._lock:
            if not predictions:
                predictions = [0.0]
            
            mean_pred = np.mean(predictions)
            std_pred = np.std(predictions)
            
            # Epistemic uncertainty (model disagreement)
            epistemic = std_pred
            
            # Aleatoric uncertainty (estimated from historical residuals)
            # Simplified - in practice would use heteroscedastic models
            aleatoric = 0.01  # Base noise level
            
            # Total uncertainty
            total = np.sqrt(epistemic**2 + aleatoric**2)
            
            # Confidence interval (assuming Gaussian)
            ci_lower = mean_pred - 1.96 * total
            ci_upper = mean_pred + 1.96 * total
            
            # Determine source
            if epistemic > aleatoric * 2:
                source = UncertaintySource.EPISTEMIC
            else:
                source = UncertaintySource.ALEATORIC
            
            estimate = UncertaintyEstimate(
                estimate_id=f"unc_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                target=target,
                epistemic_uncertainty=epistemic,
                aleatoric_uncertainty=aleatoric,
                total_uncertainty=total,
                confidence_interval=(ci_lower, ci_upper),
                calibration_score=self._get_calibration_score(),
                source=source,
            )
            
            # Store by domain
            if domain not in self._uncertainty_by_domain:
                self._uncertainty_by_domain[domain] = []
            self._uncertainty_by_domain[domain].append(estimate)
            
            # Trim history
            if len(self._uncertainty_by_domain[domain]) > 1000:
                self._uncertainty_by_domain[domain] = self._uncertainty_by_domain[domain][-500:]
            
            # Update exploration budget
            self._update_exploration_budget(domain, total)
            
            return estimate
    
    def update_calibration(
        self,
        predicted: float,
        actual: float,
        confidence_interval: Tuple[float, float]
    ):
        """Update calibration tracking with actual outcome."""
        with self._lock:
            in_interval = confidence_interval[0] <= actual <= confidence_interval[1]
            self._calibration_history.append((predicted, actual, in_interval))
            
            if len(self._calibration_history) > 10000:
                self._calibration_history = self._calibration_history[-5000:]
    
    def _get_calibration_score(self) -> float:
        """Get calibration score (fraction of actuals in predicted intervals)."""
        with self._lock:
            if not self._calibration_history:
                return 0.95  # Prior
            
            recent = self._calibration_history[-100:]
            in_interval_count = sum(1 for _, _, in_int in recent if in_int)
            return in_interval_count / len(recent)
    
    def _update_exploration_budget(self, domain: str, uncertainty: float):
        """Update exploration budget allocation based on uncertainty."""
        with self._lock:
            # Higher uncertainty = more exploration budget
            self._exploration_budget[domain] = uncertainty
            
            # Normalize to sum to total budget
            total = sum(self._exploration_budget.values())
            if total > 0:
                for d in self._exploration_budget:
                    self._exploration_budget[d] = (
                        self._exploration_budget[d] / total * self._total_exploration_budget
                    )
    
    def get_exploration_budget(self, domain: str) -> float:
        """Get exploration budget for a domain."""
        with self._lock:
            return self._exploration_budget.get(domain, 0.1)
    
    def get_domain_uncertainty(self, domain: str) -> float:
        """Get average uncertainty for a domain."""
        with self._lock:
            if domain not in self._uncertainty_by_domain:
                return 0.5
            
            recent = self._uncertainty_by_domain[domain][-100:]
            if not recent:
                return 0.5
            
            return np.mean([e.total_uncertainty for e in recent])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get uncertainty management statistics."""
        with self._lock:
            return {
                'domains_tracked': len(self._uncertainty_by_domain),
                'calibration_score': self._get_calibration_score(),
                'exploration_budget': self._exploration_budget.copy(),
                'domain_uncertainties': {
                    d: self.get_domain_uncertainty(d)
                    for d in self._uncertainty_by_domain
                },
            }


class ErrorMonitoring:
    """
    Error Monitoring System - tracks error rates by signal class.
    
    When error rates in a specific signal class spike above baseline,
    the ACC signals the PFC to increase scrutiny of that signal class.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Error tracking by signal class
        self._errors_by_class: Dict[str, List[float]] = {}
        self._baseline_window = 100
        self._spike_threshold = 2.0  # 2x baseline
        
        # Monitoring results
        self._results: List[ErrorMonitoringResult] = []
        
        # PFC notification callbacks
        self._pfc_callbacks: List[Callable] = []
    
    def monitor_error(
        self,
        signal_class: str,
        predicted: float,
        actual: float,
        prediction_id: str = ""
    ) -> ErrorMonitoringResult:
        """
        Monitor error for a signal class.
        
        Detects error rate spikes and notifies PFC.
        """
        with self._lock:
            error = abs(actual - predicted)
            
            # Initialize class tracking
            if signal_class not in self._errors_by_class:
                self._errors_by_class[signal_class] = []
            
            # Get baseline error rate
            history = self._errors_by_class[signal_class]
            baseline = np.mean(history[-self._baseline_window:]) if history else error
            
            # Add current error
            self._errors_by_class[signal_class].append(error)
            if len(self._errors_by_class[signal_class]) > 10000:
                self._errors_by_class[signal_class] = self._errors_by_class[signal_class][-5000:]
            
            # Compute current error rate (recent window)
            recent = self._errors_by_class[signal_class][-20:]
            current_rate = np.mean(recent)
            
            # Detect spike
            is_spike = baseline > 0 and current_rate > self._spike_threshold * baseline
            spike_magnitude = current_rate / baseline if baseline > 0 else 1.0
            
            result = ErrorMonitoringResult(
                prediction_id=prediction_id or f"pred_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                signal_class=signal_class,
                predicted_value=predicted,
                actual_value=actual,
                error=error,
                error_rate_baseline=baseline,
                error_rate_current=current_rate,
                is_error_spike=is_spike,
                spike_magnitude=spike_magnitude,
            )
            
            self._results.append(result)
            if len(self._results) > 10000:
                self._results = self._results[-5000:]
            
            # Notify PFC if spike detected
            if is_spike:
                self._notify_pfc(result)
            
            return result
    
    def _notify_pfc(self, result: ErrorMonitoringResult):
        """Notify PFC of error spike."""
        logger.warning(
            f"ACC error spike detected: {result.signal_class} "
            f"(magnitude={result.spike_magnitude:.2f}x)"
        )
        
        for callback in self._pfc_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"PFC notification failed: {e}")
    
    def register_pfc_callback(self, callback: Callable[[ErrorMonitoringResult], None]):
        """Register callback for PFC notifications."""
        self._pfc_callbacks.append(callback)
    
    def get_error_rate(self, signal_class: str) -> float:
        """Get current error rate for a signal class."""
        with self._lock:
            if signal_class not in self._errors_by_class:
                return 0.0
            
            recent = self._errors_by_class[signal_class][-20:]
            return np.mean(recent) if recent else 0.0
    
    def get_spike_classes(self) -> List[str]:
        """Get signal classes currently experiencing error spikes."""
        with self._lock:
            spike_classes = []
            
            for signal_class, errors in self._errors_by_class.items():
                if len(errors) < 20:
                    continue
                
                baseline = np.mean(errors[-self._baseline_window:-20]) if len(errors) > self._baseline_window else np.mean(errors[:-20])
                current = np.mean(errors[-20:])
                
                if baseline > 0 and current > self._spike_threshold * baseline:
                    spike_classes.append(signal_class)
            
            return spike_classes
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error monitoring statistics."""
        with self._lock:
            return {
                'signal_classes_tracked': len(self._errors_by_class),
                'total_errors_monitored': len(self._results),
                'spike_classes': self.get_spike_classes(),
                'error_rates': {
                    cls: self.get_error_rate(cls)
                    for cls in self._errors_by_class
                },
            }


class CognitiveControlAllocation:
    """
    Cognitive Control Allocation - allocates processing resources based on conflict.
    
    High conflict/uncertainty = recruit more processing resources.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Control allocation by task
        self._allocations: Dict[str, float] = {}
        self._total_control = 1.0
        
        # Allocation history
        self._history: List[Dict[str, Any]] = []
    
    def allocate_control(
        self,
        task: str,
        conflict_level: float,
        uncertainty_level: float
    ) -> float:
        """
        Allocate cognitive control to a task based on conflict and uncertainty.
        
        Returns allocated control (0-1).
        """
        with self._lock:
            # Combined demand
            demand = 0.5 * conflict_level + 0.5 * uncertainty_level
            
            # Available control
            used = sum(self._allocations.values())
            available = self._total_control - used
            
            # Allocate
            allocation = min(demand, available)
            self._allocations[task] = allocation
            
            # Record
            self._history.append({
                'timestamp': datetime.utcnow(),
                'task': task,
                'conflict': conflict_level,
                'uncertainty': uncertainty_level,
                'allocation': allocation,
            })
            
            if len(self._history) > 10000:
                self._history = self._history[-5000:]
            
            return allocation
    
    def release_control(self, task: str):
        """Release control allocated to a task."""
        with self._lock:
            if task in self._allocations:
                del self._allocations[task]
    
    def get_available_control(self) -> float:
        """Get available cognitive control."""
        with self._lock:
            return self._total_control - sum(self._allocations.values())
    
    def get_allocation(self, task: str) -> float:
        """Get control allocated to a task."""
        with self._lock:
            return self._allocations.get(task, 0.0)


class AnteriorCingulateCortex:
    """
    The complete Anterior Cingulate Cortex - conflict detection and uncertainty management.
    
    Implements:
    - Conflict detection (model, signal, regime)
    - Uncertainty estimation and tracking
    - Error monitoring with spike detection
    - Cognitive control allocation
    """
    
    def __init__(self):
        # Initialize components
        self.conflict_detection = ConflictDetection()
        self.uncertainty_management = UncertaintyManagement()
        self.error_monitoring = ErrorMonitoring()
        self.control_allocation = CognitiveControlAllocation()
        
        self._lock = threading.RLock()
        
        logger.info("Anterior Cingulate Cortex initialized - conflict and uncertainty monitoring active")
    
    def process_model_parliament(
        self,
        predictions: Dict[str, float],
        domain: str = "default"
    ) -> Dict[str, Any]:
        """
        Process Model Parliament predictions for conflict and uncertainty.
        
        Returns conflict signal and uncertainty estimate.
        """
        with self._lock:
            result = {
                'conflict': None,
                'uncertainty': None,
                'control_allocation': 0.0,
            }
            
            # Detect model conflict
            conflict = self.conflict_detection.detect_model_conflict(predictions)
            result['conflict'] = conflict
            
            # Estimate uncertainty
            uncertainty = self.uncertainty_management.estimate_uncertainty(
                list(predictions.values()),
                domain,
                "model_prediction"
            )
            result['uncertainty'] = uncertainty
            
            # Allocate control based on conflict and uncertainty
            conflict_level = conflict.severity.value / 4.0 if conflict else 0.0
            uncertainty_level = min(1.0, uncertainty.total_uncertainty * 10)
            
            allocation = self.control_allocation.allocate_control(
                f"parliament_{domain}",
                conflict_level,
                uncertainty_level
            )
            result['control_allocation'] = allocation
            
            return result
    
    def process_signals(
        self,
        signals: Dict[str, float]
    ) -> Optional[ConflictSignal]:
        """Process signals for conflict detection."""
        return self.conflict_detection.detect_signal_conflict(signals)
    
    def process_regime_classification(
        self,
        regime_probabilities: Dict[str, float]
    ) -> Optional[ConflictSignal]:
        """Process regime classification for ambiguity detection."""
        return self.conflict_detection.detect_regime_ambiguity(regime_probabilities)
    
    def monitor_prediction_error(
        self,
        signal_class: str,
        predicted: float,
        actual: float
    ) -> ErrorMonitoringResult:
        """Monitor a prediction error."""
        return self.error_monitoring.monitor_error(signal_class, predicted, actual)
    
    def get_exploration_budget(self, domain: str) -> float:
        """Get exploration budget for a domain (uncertainty-driven)."""
        return self.uncertainty_management.get_exploration_budget(domain)
    
    def get_conflict_level(self) -> float:
        """Get current overall conflict level."""
        recent = self.conflict_detection.get_recent_conflicts(10)
        if not recent:
            return 0.0
        
        return np.mean([c.severity.value / 4.0 for c in recent])
    
    def get_status(self) -> Dict[str, Any]:
        """Get ACC status."""
        return {
            'conflict_rate': self.conflict_detection.get_conflict_rate(),
            'conflict_level': self.get_conflict_level(),
            'uncertainty': self.uncertainty_management.get_statistics(),
            'error_monitoring': self.error_monitoring.get_statistics(),
            'available_control': self.control_allocation.get_available_control(),
        }
