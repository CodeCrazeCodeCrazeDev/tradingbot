"""
Skill #27: Concept Drift Detector
=================================

Detects when market dynamics change and models become stale,
triggering retraining or adaptation.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Type of concept drift."""
    SUDDEN = "sudden"
    GRADUAL = "gradual"
    INCREMENTAL = "incremental"
    RECURRING = "recurring"


class DriftSeverity(Enum):
    """Severity of detected drift."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftDetection:
    """Detected drift event."""
    drift_type: DriftType
    severity: DriftSeverity
    start_index: int
    confidence: float
    affected_features: List[str]


@dataclass
class ConceptDriftResult:
    """Concept drift detection result."""
    drift_detected: bool
    detections: List[DriftDetection]
    distribution_shift: float
    model_staleness: float
    retrain_recommended: bool
    trading_signal: str


class ConceptDriftDetector:
    """Concept drift detection for model monitoring."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.window_size = self.config.get('window_size', 50)
            self.threshold = self.config.get('threshold', 0.1)
            self.reference_distribution: Optional[np.ndarray] = None
            logger.info("ConceptDriftDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect(self, prices: np.ndarray, volumes: np.ndarray) -> ConceptDriftResult:
        """Detect concept drift in market data."""
        try:
            if len(prices) < self.window_size * 2:
                return self._create_empty_result()
        
            features = self._extract_features(prices, volumes)
        
            # Set reference if not set
            if self.reference_distribution is None:
                self.reference_distribution = features[:self.window_size]
        
            detections = []
        
            # Check for different drift types
            sudden = self._detect_sudden_drift(features)
            if sudden:
                detections.append(sudden)
        
            gradual = self._detect_gradual_drift(features)
            if gradual:
                detections.append(gradual)
        
            # Calculate distribution shift
            shift = self._calculate_distribution_shift(features)
        
            # Calculate model staleness
            staleness = self._calculate_staleness(features)
        
            drift_detected = len(detections) > 0 or shift > self.threshold
            retrain = staleness > 0.5 or any(d.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL] for d in detections)
        
            signal = self._generate_signal(drift_detected, detections, staleness)
        
            return ConceptDriftResult(
                drift_detected=drift_detected,
                detections=detections,
                distribution_shift=shift,
                model_staleness=staleness,
                retrain_recommended=retrain,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise
    
    def _extract_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features for drift detection."""
        try:
            returns = np.diff(prices) / prices[:-1]
            features = []
        
            for i in range(20, len(returns)):
                window = returns[i-20:i]
                features.append([
                    np.mean(window), np.std(window),
                    np.min(window), np.max(window),
                    np.median(window)
                ])
        
            return np.array(features)
        except Exception as e:
            logger.error(f"Error in _extract_features: {e}")
            raise
    
    def _detect_sudden_drift(self, features: np.ndarray) -> Optional[DriftDetection]:
        """Detect sudden concept drift."""
        try:
            if len(features) < self.window_size:
                return None
        
            recent = features[-self.window_size:]
            reference = self.reference_distribution
        
            # KS-like statistic
            diff = np.abs(np.mean(recent, axis=0) - np.mean(reference, axis=0))
            max_diff = np.max(diff)
        
            if max_diff > self.threshold * 2:
                return DriftDetection(
                    drift_type=DriftType.SUDDEN,
                    severity=DriftSeverity.HIGH if max_diff > self.threshold * 3 else DriftSeverity.MEDIUM,
                    start_index=len(features) - self.window_size,
                    confidence=min(0.95, max_diff / self.threshold),
                    affected_features=['mean', 'std', 'range']
                )
            return None
        except Exception as e:
            logger.error(f"Error in _detect_sudden_drift: {e}")
            raise
    
    def _detect_gradual_drift(self, features: np.ndarray) -> Optional[DriftDetection]:
        """Detect gradual concept drift."""
        try:
            if len(features) < self.window_size * 2:
                return None
        
            # Check trend in feature means
            means = np.mean(features, axis=1)
            x = np.arange(len(means))
            slope = np.polyfit(x, means, 1)[0]
        
            if abs(slope) > self.threshold / 100:
                return DriftDetection(
                    drift_type=DriftType.GRADUAL,
                    severity=DriftSeverity.MEDIUM,
                    start_index=0,
                    confidence=min(0.9, abs(slope) * 1000),
                    affected_features=['trend']
                )
            return None
        except Exception as e:
            logger.error(f"Error in _detect_gradual_drift: {e}")
            raise
    
    def _calculate_distribution_shift(self, features: np.ndarray) -> float:
        """Calculate distribution shift from reference."""
        try:
            if self.reference_distribution is None or len(features) < self.window_size:
                return 0.0
        
            recent = features[-self.window_size:]
            ref_mean = np.mean(self.reference_distribution, axis=0)
            recent_mean = np.mean(recent, axis=0)
        
            shift = np.linalg.norm(recent_mean - ref_mean)
            return float(shift)
        except Exception as e:
            logger.error(f"Error in _calculate_distribution_shift: {e}")
            raise
    
    def _calculate_staleness(self, features: np.ndarray) -> float:
        """Calculate model staleness score."""
        try:
            if self.reference_distribution is None:
                return 0.0
        
            # Compare variance
            ref_var = np.var(self.reference_distribution)
            recent_var = np.var(features[-self.window_size:])
        
            var_ratio = abs(recent_var - ref_var) / (ref_var + 1e-10)
            return min(1.0, var_ratio)
        except Exception as e:
            logger.error(f"Error in _calculate_staleness: {e}")
            raise
    
    def update_reference(self, prices: np.ndarray, volumes: np.ndarray):
        """Update reference distribution."""
        try:
            features = self._extract_features(prices, volumes)
            self.reference_distribution = features[-self.window_size:]
        except Exception as e:
            logger.error(f"Error in update_reference: {e}")
            raise
    
    def _generate_signal(
        self,
        drift_detected: bool,
        detections: List[DriftDetection],
        staleness: float
    ) -> str:
        """Generate trading signal."""
        try:
            if not drift_detected:
                return f"STABLE: No drift detected, staleness {staleness:.0%}"
        
            if any(d.severity == DriftSeverity.CRITICAL for d in detections):
                return "CRITICAL DRIFT: Stop trading, retrain model immediately"
            elif any(d.severity == DriftSeverity.HIGH for d in detections):
                return "HIGH DRIFT: Reduce position size, consider retraining"
        
            return f"DRIFT DETECTED: {len(detections)} events, staleness {staleness:.0%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> ConceptDriftResult:
        """Create empty result."""
        return ConceptDriftResult(
            drift_detected=False,
            detections=[],
            distribution_shift=0,
            model_staleness=0,
            retrain_recommended=False,
            trading_signal="Insufficient data"
        )
