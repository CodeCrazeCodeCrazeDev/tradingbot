"""
Failure Mode Detector
======================

Detect unseen failure modes BEFORE they cause losses.

PHILOSOPHY:
- Learn how decision-making BREAKS under uncertainty
- Detect failure modes FASTER than the market changes
- Predict when models will fail BEFORE they fail
- Identify regime changes before they invalidate strategies

DETECTION TYPES:
1. MODEL DEGRADATION - When model performance decays
2. ASSUMPTION VIOLATION - When model assumptions break
3. REGIME SHIFT - When market regime changes
4. DISTRIBUTION SHIFT - When data distribution changes
5. CORRELATION BREAKDOWN - When correlations change
6. LIQUIDITY EVAPORATION - When liquidity disappears
7. UNCERTAINTY EXPLOSION - When uncertainty becomes unbounded
"""

import logging
import threading
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class FailureModeType(Enum):
    """Types of failure modes"""
    MODEL_DEGRADATION = "model_degradation"
    ASSUMPTION_VIOLATION = "assumption_violation"
    REGIME_SHIFT = "regime_shift"
    DISTRIBUTION_SHIFT = "distribution_shift"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_EVAPORATION = "liquidity_evaporation"
    UNCERTAINTY_EXPLOSION = "uncertainty_explosion"
    EXECUTION_DEGRADATION = "execution_degradation"
    DATA_QUALITY = "data_quality"
    UNKNOWN = "unknown"


class DetectionSeverity(Enum):
    """Severity of detection"""
    INFO = "info"           # Informational
    WARNING = "warning"     # Needs attention
    CRITICAL = "critical"   # Immediate action required
    EMERGENCY = "emergency" # System should stop


class DetectionConfidence(Enum):
    """Confidence in detection"""
    LOW = "low"           # Possible but uncertain
    MEDIUM = "medium"     # Likely
    HIGH = "high"         # Very likely
    CERTAIN = "certain"   # Definite


@dataclass
class FailureModeDetection:
    """A detected failure mode"""
    detection_id: str
    failure_type: FailureModeType
    severity: DetectionSeverity
    confidence: DetectionConfidence
    
    # Description
    description: str
    mechanism: str          # How this failure mode works
    
    # Evidence
    evidence: List[str]
    metrics: Dict[str, float]
    
    # Timing
    detected_at: datetime = field(default_factory=datetime.now)
    estimated_impact_time: Optional[datetime] = None
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    
    # Metadata
    detector_name: str = ""
    false_positive_probability: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'detection_id': self.detection_id,
            'failure_type': self.failure_type.value,
            'severity': self.severity.value,
            'confidence': self.confidence.value,
            'description': self.description,
            'mechanism': self.mechanism,
            'evidence': self.evidence,
            'metrics': self.metrics,
            'detected_at': self.detected_at.isoformat(),
            'estimated_impact_time': self.estimated_impact_time.isoformat() if self.estimated_impact_time else None,
            'recommended_actions': self.recommended_actions,
            'detector_name': self.detector_name,
            'false_positive_probability': self.false_positive_probability
        }


class FailureModeDetectorBase(ABC):
    """Base class for failure mode detectors"""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.detection_count = 0
        self.false_positive_count = 0
    
    @abstractmethod
    def detect(
        self,
        current_state: Dict[str, Any],
        historical_states: List[Dict[str, Any]]
    ) -> List[FailureModeDetection]:
        """Detect failure modes"""
        pass
    
    def get_false_positive_rate(self) -> float:
        """Get false positive rate"""
        if self.detection_count == 0:
            return 0.0
        return self.false_positive_count / self.detection_count


class ModelDegradationDetector(FailureModeDetectorBase):
    """Detects when model performance is degrading"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("ModelDegradationDetector", config)
        self.performance_window = deque(maxlen=100)
        self.baseline_performance: Optional[float] = None
        self.degradation_threshold = config.get('degradation_threshold', 0.2) if config else 0.2
    
    def detect(
        self,
        current_state: Dict[str, Any],
        historical_states: List[Dict[str, Any]]
    ) -> List[FailureModeDetection]:
        detections = []
        
        # Get current performance metrics
        current_accuracy = current_state.get('model_accuracy', 0.0)
        current_sharpe = current_state.get('sharpe_ratio', 0.0)
        current_hit_rate = current_state.get('hit_rate', 0.0)
        
        # Update performance window
        self.performance_window.append({
            'accuracy': current_accuracy,
            'sharpe': current_sharpe,
            'hit_rate': current_hit_rate,
            'timestamp': datetime.now()
        })
        
        # Set baseline if not set
        if self.baseline_performance is None and len(self.performance_window) >= 20:
            self.baseline_performance = np.mean([p['accuracy'] for p in list(self.performance_window)[:20]])
        
        # Check for degradation
        if self.baseline_performance and len(self.performance_window) >= 10:
            recent_performance = np.mean([p['accuracy'] for p in list(self.performance_window)[-10:]])
            degradation = (self.baseline_performance - recent_performance) / max(self.baseline_performance, 0.01)
            
            if degradation > self.degradation_threshold:
                import hashlib
                detection_id = hashlib.md5(
                    f"model_degradation_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
                
                severity = DetectionSeverity.WARNING
                if degradation > 0.4:
                    severity = DetectionSeverity.CRITICAL
                if degradation > 0.6:
                    severity = DetectionSeverity.EMERGENCY
                
                detection = FailureModeDetection(
                    detection_id=detection_id,
                    failure_type=FailureModeType.MODEL_DEGRADATION,
                    severity=severity,
                    confidence=DetectionConfidence.HIGH if degradation > 0.3 else DetectionConfidence.MEDIUM,
                    description=f"Model performance degraded by {degradation:.1%}",
                    mechanism="Model predictions becoming less accurate over time",
                    evidence=[
                        f"Baseline accuracy: {self.baseline_performance:.2%}",
                        f"Recent accuracy: {recent_performance:.2%}",
                        f"Degradation: {degradation:.1%}"
                    ],
                    metrics={
                        'baseline_accuracy': self.baseline_performance,
                        'recent_accuracy': recent_performance,
                        'degradation': degradation
                    },
                    recommended_actions=[
                        "Review model assumptions",
                        "Check for regime change",
                        "Consider model retraining",
                        "Reduce position sizes"
                    ],
                    detector_name=self.name
                )
                
                detections.append(detection)
                self.detection_count += 1
        
        return detections


class RegimeShiftDetector(FailureModeDetectorBase):
    """Detects regime shifts in market behavior"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("RegimeShiftDetector", config)
        self.volatility_window = deque(maxlen=100)
        self.correlation_window = deque(maxlen=50)
        self.regime_history: List[str] = []
    
    def detect(
        self,
        current_state: Dict[str, Any],
        historical_states: List[Dict[str, Any]]
    ) -> List[FailureModeDetection]:
        detections = []
        
        # Get current regime indicators
        current_volatility = current_state.get('volatility', 0.0)
        current_correlation = current_state.get('correlation', 0.0)
        current_regime = current_state.get('regime', 'unknown')
        
        # Update windows
        self.volatility_window.append(current_volatility)
        self.correlation_window.append(current_correlation)
        
        # Check for volatility regime shift
        if len(self.volatility_window) >= 20:
            recent_vol = np.mean(list(self.volatility_window)[-10:])
            baseline_vol = np.mean(list(self.volatility_window)[:10])
            
            vol_change = abs(recent_vol - baseline_vol) / max(baseline_vol, 0.001)
            
            if vol_change > 0.5:  # 50% change in volatility
                import hashlib
                detection_id = hashlib.md5(
                    f"regime_shift_vol_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
                
                detection = FailureModeDetection(
                    detection_id=detection_id,
                    failure_type=FailureModeType.REGIME_SHIFT,
                    severity=DetectionSeverity.WARNING if vol_change < 1.0 else DetectionSeverity.CRITICAL,
                    confidence=DetectionConfidence.HIGH,
                    description=f"Volatility regime shift detected: {vol_change:.0%} change",
                    mechanism="Market volatility structure has changed significantly",
                    evidence=[
                        f"Baseline volatility: {baseline_vol:.4f}",
                        f"Recent volatility: {recent_vol:.4f}",
                        f"Change: {vol_change:.0%}"
                    ],
                    metrics={
                        'baseline_volatility': baseline_vol,
                        'recent_volatility': recent_vol,
                        'volatility_change': vol_change
                    },
                    recommended_actions=[
                        "Review volatility-dependent strategies",
                        "Adjust position sizing",
                        "Update risk parameters",
                        "Consider pausing trading"
                    ],
                    detector_name=self.name
                )
                
                detections.append(detection)
                self.detection_count += 1
        
        # Check for correlation breakdown
        if len(self.correlation_window) >= 20:
            recent_corr = np.mean(list(self.correlation_window)[-10:])
            baseline_corr = np.mean(list(self.correlation_window)[:10])
            
            corr_change = abs(recent_corr - baseline_corr)
            
            if corr_change > 0.3:  # Significant correlation change
                import hashlib
                detection_id = hashlib.md5(
                    f"correlation_breakdown_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
                
                detection = FailureModeDetection(
                    detection_id=detection_id,
                    failure_type=FailureModeType.CORRELATION_BREAKDOWN,
                    severity=DetectionSeverity.WARNING,
                    confidence=DetectionConfidence.MEDIUM,
                    description=f"Correlation structure changed by {corr_change:.2f}",
                    mechanism="Asset correlations have shifted, invalidating hedges",
                    evidence=[
                        f"Baseline correlation: {baseline_corr:.2f}",
                        f"Recent correlation: {recent_corr:.2f}",
                        f"Change: {corr_change:.2f}"
                    ],
                    metrics={
                        'baseline_correlation': baseline_corr,
                        'recent_correlation': recent_corr,
                        'correlation_change': corr_change
                    },
                    recommended_actions=[
                        "Review correlation-dependent strategies",
                        "Check hedge effectiveness",
                        "Update correlation matrix"
                    ],
                    detector_name=self.name
                )
                
                detections.append(detection)
                self.detection_count += 1
        
        return detections


class UncertaintyExplosionDetector(FailureModeDetectorBase):
    """Detects when uncertainty becomes unbounded"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("UncertaintyExplosionDetector", config)
        self.uncertainty_window = deque(maxlen=50)
        self.max_acceptable_uncertainty = config.get('max_uncertainty', 0.5) if config else 0.5
    
    def detect(
        self,
        current_state: Dict[str, Any],
        historical_states: List[Dict[str, Any]]
    ) -> List[FailureModeDetection]:
        detections = []
        
        # Get uncertainty metrics
        prediction_uncertainty = current_state.get('prediction_uncertainty', 0.0)
        model_disagreement = current_state.get('model_disagreement', 0.0)
        confidence_spread = current_state.get('confidence_spread', 0.0)
        
        # Composite uncertainty
        uncertainty = (prediction_uncertainty + model_disagreement + confidence_spread) / 3
        self.uncertainty_window.append(uncertainty)
        
        # Check for uncertainty explosion
        if len(self.uncertainty_window) >= 10:
            recent_uncertainty = np.mean(list(self.uncertainty_window)[-5:])
            baseline_uncertainty = np.mean(list(self.uncertainty_window)[:5])
            
            uncertainty_growth = recent_uncertainty / max(baseline_uncertainty, 0.01)
            
            if recent_uncertainty > self.max_acceptable_uncertainty or uncertainty_growth > 2.0:
                import hashlib
                detection_id = hashlib.md5(
                    f"uncertainty_explosion_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
                
                severity = DetectionSeverity.WARNING
                if recent_uncertainty > 0.7 or uncertainty_growth > 3.0:
                    severity = DetectionSeverity.CRITICAL
                if recent_uncertainty > 0.9 or uncertainty_growth > 5.0:
                    severity = DetectionSeverity.EMERGENCY
                
                detection = FailureModeDetection(
                    detection_id=detection_id,
                    failure_type=FailureModeType.UNCERTAINTY_EXPLOSION,
                    severity=severity,
                    confidence=DetectionConfidence.HIGH,
                    description=f"Uncertainty exploded: {recent_uncertainty:.2f} (growth: {uncertainty_growth:.1f}x)",
                    mechanism="Model uncertainty has grown beyond acceptable bounds",
                    evidence=[
                        f"Current uncertainty: {recent_uncertainty:.2f}",
                        f"Baseline uncertainty: {baseline_uncertainty:.2f}",
                        f"Growth factor: {uncertainty_growth:.1f}x",
                        f"Threshold: {self.max_acceptable_uncertainty:.2f}"
                    ],
                    metrics={
                        'current_uncertainty': recent_uncertainty,
                        'baseline_uncertainty': baseline_uncertainty,
                        'uncertainty_growth': uncertainty_growth
                    },
                    recommended_actions=[
                        "STOP trading immediately",
                        "Wait for uncertainty to stabilize",
                        "Review what caused uncertainty spike",
                        "Consider market is unpredictable"
                    ],
                    detector_name=self.name
                )
                
                detections.append(detection)
                self.detection_count += 1
        
        return detections


class LiquidityEvaporationDetector(FailureModeDetectorBase):
    """Detects when liquidity is evaporating"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("LiquidityEvaporationDetector", config)
        self.liquidity_window = deque(maxlen=50)
        self.spread_window = deque(maxlen=50)
    
    def detect(
        self,
        current_state: Dict[str, Any],
        historical_states: List[Dict[str, Any]]
    ) -> List[FailureModeDetection]:
        detections = []
        
        # Get liquidity metrics
        bid_depth = current_state.get('bid_depth', 1.0)
        ask_depth = current_state.get('ask_depth', 1.0)
        spread = current_state.get('spread', 0.0)
        volume = current_state.get('volume', 1.0)
        
        # Composite liquidity score
        liquidity_score = (bid_depth + ask_depth) / 2 * volume
        self.liquidity_window.append(liquidity_score)
        self.spread_window.append(spread)
        
        # Check for liquidity evaporation
        if len(self.liquidity_window) >= 10:
            recent_liquidity = np.mean(list(self.liquidity_window)[-5:])
            baseline_liquidity = np.mean(list(self.liquidity_window)[:5])
            
            liquidity_drop = 1 - (recent_liquidity / max(baseline_liquidity, 0.01))
            
            recent_spread = np.mean(list(self.spread_window)[-5:])
            baseline_spread = np.mean(list(self.spread_window)[:5])
            spread_increase = recent_spread / max(baseline_spread, 0.0001) - 1
            
            if liquidity_drop > 0.5 or spread_increase > 1.0:
                import hashlib
                detection_id = hashlib.md5(
                    f"liquidity_evaporation_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
                
                severity = DetectionSeverity.WARNING
                if liquidity_drop > 0.7 or spread_increase > 2.0:
                    severity = DetectionSeverity.CRITICAL
                if liquidity_drop > 0.9 or spread_increase > 5.0:
                    severity = DetectionSeverity.EMERGENCY
                
                detection = FailureModeDetection(
                    detection_id=detection_id,
                    failure_type=FailureModeType.LIQUIDITY_EVAPORATION,
                    severity=severity,
                    confidence=DetectionConfidence.HIGH,
                    description=f"Liquidity dropped {liquidity_drop:.0%}, spread up {spread_increase:.0%}",
                    mechanism="Market makers withdrawing, execution will be poor",
                    evidence=[
                        f"Liquidity drop: {liquidity_drop:.0%}",
                        f"Spread increase: {spread_increase:.0%}",
                        f"Current bid depth: {bid_depth:.2f}",
                        f"Current ask depth: {ask_depth:.2f}"
                    ],
                    metrics={
                        'liquidity_drop': liquidity_drop,
                        'spread_increase': spread_increase,
                        'bid_depth': bid_depth,
                        'ask_depth': ask_depth
                    },
                    recommended_actions=[
                        "Avoid new positions",
                        "Reduce position sizes",
                        "Use limit orders only",
                        "Widen stop losses to avoid slippage"
                    ],
                    detector_name=self.name
                )
                
                detections.append(detection)
                self.detection_count += 1
        
        return detections


class AssumptionViolationDetector(FailureModeDetectorBase):
    """Detects when model assumptions are violated"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("AssumptionViolationDetector", config)
        self.assumptions: Dict[str, Dict] = {}
        self._initialize_assumptions()
    
    def _initialize_assumptions(self):
        """Initialize common model assumptions"""
        self.assumptions = {
            'stationarity': {
                'description': 'Data distribution is stationary',
                'check': self._check_stationarity
            },
            'normality': {
                'description': 'Returns are approximately normal',
                'check': self._check_normality
            },
            'independence': {
                'description': 'Observations are independent',
                'check': self._check_independence
            },
            'homoscedasticity': {
                'description': 'Variance is constant',
                'check': self._check_homoscedasticity
            }
        }
    
    def _check_stationarity(self, data: List[float]) -> Tuple[bool, float]:
        """Check if data is stationary"""
        if len(data) < 20:
            return True, 0.0
        
        # Simple check: compare mean and variance of halves
        half = len(data) // 2
        mean1, mean2 = np.mean(data[:half]), np.mean(data[half:])
        var1, var2 = np.var(data[:half]), np.var(data[half:])
        
        mean_change = abs(mean1 - mean2) / max(abs(mean1), 0.001)
        var_change = abs(var1 - var2) / max(var1, 0.001)
        
        violation_score = (mean_change + var_change) / 2
        return violation_score < 0.3, violation_score
    
    def _check_normality(self, data: List[float]) -> Tuple[bool, float]:
        """Check if data is approximately normal"""
        if len(data) < 20:
            return True, 0.0
        
        # Simple check: skewness and kurtosis
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return True, 0.0
        
        normalized = [(x - mean) / std for x in data]
        skewness = np.mean([x**3 for x in normalized])
        kurtosis = np.mean([x**4 for x in normalized]) - 3
        
        violation_score = (abs(skewness) + abs(kurtosis) / 3) / 2
        return violation_score < 0.5, violation_score
    
    def _check_independence(self, data: List[float]) -> Tuple[bool, float]:
        """Check if observations are independent"""
        if len(data) < 20:
            return True, 0.0
        
        # Simple autocorrelation check
        mean = np.mean(data)
        var = np.var(data)
        if var == 0:
            return True, 0.0
        
        autocorr = np.mean([(data[i] - mean) * (data[i-1] - mean) for i in range(1, len(data))]) / var
        
        violation_score = abs(autocorr)
        return violation_score < 0.3, violation_score
    
    def _check_homoscedasticity(self, data: List[float]) -> Tuple[bool, float]:
        """Check if variance is constant"""
        if len(data) < 20:
            return True, 0.0
        
        # Check variance in windows
        window_size = len(data) // 4
        variances = []
        for i in range(4):
            start = i * window_size
            end = start + window_size
            variances.append(np.var(data[start:end]))
        
        max_var = max(variances)
        min_var = min(variances)
        
        if min_var == 0:
            return False, 1.0
        
        violation_score = (max_var / min_var - 1) / 2
        return violation_score < 0.5, min(violation_score, 1.0)
    
    def detect(
        self,
        current_state: Dict[str, Any],
        historical_states: List[Dict[str, Any]]
    ) -> List[FailureModeDetection]:
        detections = []
        
        # Get data for assumption checking
        returns = current_state.get('returns', [])
        if not returns or len(returns) < 20:
            return detections
        
        # Check each assumption
        violations = []
        for assumption_name, assumption_info in self.assumptions.items():
            is_valid, violation_score = assumption_info['check'](returns)
            
            if not is_valid:
                violations.append({
                    'name': assumption_name,
                    'description': assumption_info['description'],
                    'violation_score': violation_score
                })
        
        # Create detection if violations found
        if violations:
            import hashlib
            detection_id = hashlib.md5(
                f"assumption_violation_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            max_violation = max(v['violation_score'] for v in violations)
            
            severity = DetectionSeverity.INFO
            if max_violation > 0.5:
                severity = DetectionSeverity.WARNING
            if max_violation > 0.7:
                severity = DetectionSeverity.CRITICAL
            
            detection = FailureModeDetection(
                detection_id=detection_id,
                failure_type=FailureModeType.ASSUMPTION_VIOLATION,
                severity=severity,
                confidence=DetectionConfidence.MEDIUM,
                description=f"{len(violations)} model assumptions violated",
                mechanism="Model assumptions no longer hold, predictions unreliable",
                evidence=[
                    f"{v['name']}: {v['description']} (score: {v['violation_score']:.2f})"
                    for v in violations
                ],
                metrics={
                    v['name']: v['violation_score'] for v in violations
                },
                recommended_actions=[
                    "Review model assumptions",
                    "Consider non-parametric methods",
                    "Reduce model confidence",
                    "Use robust estimation"
                ],
                detector_name=self.name
            )
            
            detections.append(detection)
            self.detection_count += 1
        
        return detections


class FailureModeDetector:
    """
    Main failure mode detection system.
    
    CORE PRINCIPLE:
    Detect failure modes FASTER than the market changes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Initialize detectors
        self.detectors: List[FailureModeDetectorBase] = [
            ModelDegradationDetector(config),
            RegimeShiftDetector(config),
            UncertaintyExplosionDetector(config),
            LiquidityEvaporationDetector(config),
            AssumptionViolationDetector(config)
        ]
        
        # Detection history
        self.detection_history: List[FailureModeDetection] = []
        self.active_detections: Dict[str, FailureModeDetection] = {}
        
        # State history
        self.state_history: List[Dict[str, Any]] = []
        self.max_history = config.get('max_history', 1000) if config else 1000
        
        # Statistics
        self.total_detections = 0
        self.detections_by_type: Dict[str, int] = {}
        
        # Callbacks
        self.on_detection_callbacks: List[Callable] = []
        
        logger.info("FailureModeDetector initialized with %d detectors", len(self.detectors))
    
    def update(self, current_state: Dict[str, Any]) -> List[FailureModeDetection]:
        """
        Update with current state and detect failure modes.
        
        Args:
            current_state: Current system/market state
            
        Returns:
            List of detected failure modes
        """
        with self.lock:
            # Store state
            self.state_history.append({
                **current_state,
                'timestamp': datetime.now()
            })
            
            # Trim history
            if len(self.state_history) > self.max_history:
                self.state_history = self.state_history[-self.max_history:]
            
            # Run all detectors
            all_detections = []
            
            for detector in self.detectors:
                try:
                    detections = detector.detect(current_state, self.state_history)
                    all_detections.extend(detections)
                except Exception as e:
                    logger.error("Detector %s failed: %s", detector.name, e)
            
            # Process detections
            for detection in all_detections:
                self._process_detection(detection)
            
            return all_detections
    
    def _process_detection(self, detection: FailureModeDetection):
        """Process a new detection"""
        # Store in history
        self.detection_history.append(detection)
        
        # Update active detections
        self.active_detections[detection.detection_id] = detection
        
        # Update statistics
        self.total_detections += 1
        failure_type = detection.failure_type.value
        self.detections_by_type[failure_type] = self.detections_by_type.get(failure_type, 0) + 1
        
        # Log
        logger.warning(
            "FAILURE MODE DETECTED [%s/%s]: %s",
            detection.severity.value.upper(),
            detection.failure_type.value,
            detection.description
        )
        
        # Call callbacks
        for callback in self.on_detection_callbacks:
            try:
                callback(detection)
            except Exception as e:
                logger.error("Detection callback failed: %s", e)
    
    def on_detection(self, callback: Callable[[FailureModeDetection], None]):
        """Register callback for detections"""
        self.on_detection_callbacks.append(callback)
    
    def get_active_detections(
        self,
        severity: Optional[DetectionSeverity] = None,
        failure_type: Optional[FailureModeType] = None
    ) -> List[FailureModeDetection]:
        """Get active detections with optional filtering"""
        with self.lock:
            detections = list(self.active_detections.values())
            
            if severity:
                detections = [d for d in detections if d.severity == severity]
            
            if failure_type:
                detections = [d for d in detections if d.failure_type == failure_type]
            
            return detections
    
    def clear_detection(self, detection_id: str):
        """Clear a detection (mark as resolved)"""
        with self.lock:
            if detection_id in self.active_detections:
                del self.active_detections[detection_id]
    
    def get_risk_level(self) -> Tuple[str, float]:
        """
        Get overall risk level based on active detections.
        
        Returns:
            Tuple of (risk_level, risk_score)
        """
        with self.lock:
            if not self.active_detections:
                return "low", 0.0
            
            # Calculate risk score
            severity_weights = {
                DetectionSeverity.INFO: 0.1,
                DetectionSeverity.WARNING: 0.3,
                DetectionSeverity.CRITICAL: 0.6,
                DetectionSeverity.EMERGENCY: 1.0
            }
            
            total_score = sum(
                severity_weights.get(d.severity, 0.1)
                for d in self.active_detections.values()
            )
            
            # Normalize
            risk_score = min(1.0, total_score / 3)
            
            # Determine level
            if risk_score < 0.2:
                risk_level = "low"
            elif risk_score < 0.4:
                risk_level = "moderate"
            elif risk_score < 0.6:
                risk_level = "elevated"
            elif risk_score < 0.8:
                risk_level = "high"
            else:
                risk_level = "critical"
            
            return risk_level, risk_score
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics"""
        with self.lock:
            return {
                'total_detections': self.total_detections,
                'active_detections': len(self.active_detections),
                'detections_by_type': self.detections_by_type,
                'detector_stats': {
                    d.name: {
                        'detection_count': d.detection_count,
                        'false_positive_rate': d.get_false_positive_rate()
                    }
                    for d in self.detectors
                },
                'risk_level': self.get_risk_level()[0],
                'risk_score': self.get_risk_level()[1]
            }
