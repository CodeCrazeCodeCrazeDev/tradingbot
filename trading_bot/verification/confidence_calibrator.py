"""
Confidence Calibrator - Uncertainty Quantification and Calibration

Ensures that the bot's confidence levels are properly calibrated to match
actual historical accuracy. Prevents overconfidence and underconfidence.

CALIBRATION METHODS:
1. Platt Scaling - Logistic regression calibration
2. Isotonic Regression - Non-parametric calibration
3. Temperature Scaling - Simple scalar calibration
4. Bayesian Calibration - Prior-based adjustment
5. Historical Binning - Bucket-based calibration

Author: AlphaAlgo Team
Date: 2026-01-28
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class CalibrationMethod(Enum):
    """Calibration methods"""
    PLATT_SCALING = "platt_scaling"
    ISOTONIC = "isotonic"
    TEMPERATURE = "temperature"
    BAYESIAN = "bayesian"
    HISTORICAL_BINNING = "historical_binning"


class CalibrationStatus(Enum):
    """Calibration status"""
    WELL_CALIBRATED = "well_calibrated"
    OVERCONFIDENT = "overconfident"
    UNDERCONFIDENT = "underconfident"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class CalibrationResult:
    """Result of confidence calibration"""
    original_confidence: float
    calibrated_confidence: float
    calibration_method: CalibrationMethod
    calibration_status: CalibrationStatus
    calibration_error: float
    historical_accuracy_at_confidence: Optional[float]
    adjustment_factor: float
    uncertainty_bounds: Tuple[float, float]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_confidence': self.original_confidence,
            'calibrated_confidence': self.calibrated_confidence,
            'method': self.calibration_method.value,
            'status': self.calibration_status.value,
            'calibration_error': self.calibration_error,
            'historical_accuracy': self.historical_accuracy_at_confidence,
            'adjustment_factor': self.adjustment_factor,
            'uncertainty_lower': self.uncertainty_bounds[0],
            'uncertainty_upper': self.uncertainty_bounds[1],
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PredictionRecord:
    """Record of a prediction for calibration"""
    confidence: float
    was_correct: bool
    prediction_type: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConfidenceCalibrator:
    """
    Calibrates confidence levels to match historical accuracy.
    
    Implements multiple calibration methods and tracks prediction
    outcomes to continuously improve calibration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Calibration parameters
            self.min_samples = self.config.get('min_samples', 30)
            self.bucket_size = self.config.get('bucket_size', 0.1)
            self.temperature = self.config.get('temperature', 1.0)
            self.prior_strength = self.config.get('prior_strength', 0.3)
        
            # Prediction history
            self.prediction_history: List[PredictionRecord] = []
        
            # Calibration buckets
            self.calibration_buckets: Dict[float, List[bool]] = defaultdict(list)
        
            # Platt scaling parameters (learned)
            self.platt_a = 0.0
            self.platt_b = 1.0
        
            # Temperature (learned)
            self.learned_temperature = 1.0
        
            # Calibration history
            self.calibration_history: List[CalibrationResult] = []
        
            logger.info("ConfidenceCalibrator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_outcome(
        self,
        confidence: float,
        was_correct: bool,
        prediction_type: str = "general"
    ):
        """Record a prediction outcome for calibration"""
        try:
            record = PredictionRecord(
                confidence=confidence,
                was_correct=was_correct,
                prediction_type=prediction_type
            )
            self.prediction_history.append(record)
        
            # Update bucket
            bucket = round(confidence / self.bucket_size) * self.bucket_size
            self.calibration_buckets[bucket].append(was_correct)
        
            # Update calibration parameters periodically
            if len(self.prediction_history) % 50 == 0:
                self._update_calibration_parameters()
        except Exception as e:
            logger.error(f"Error in record_outcome: {e}")
            raise
    
    def calibrate(
        self,
        confidence: float,
        method: Optional[CalibrationMethod] = None,
        prediction_type: str = "general"
    ) -> CalibrationResult:
        """
        Calibrate a confidence value.
        
        Args:
            confidence: Original confidence value (0.0 to 1.0)
            method: Calibration method to use (auto-selected if None)
            prediction_type: Type of prediction for type-specific calibration
            
        Returns:
            CalibrationResult with calibrated confidence
        """
        # Validate input
        try:
            confidence = max(0.0, min(1.0, confidence))
        
            # Select method if not specified
            if method is None:
                method = self._select_best_method()
        
            # Get historical accuracy at this confidence level
            historical_accuracy = self._get_historical_accuracy(confidence)
        
            # Apply calibration
            if method == CalibrationMethod.PLATT_SCALING:
                calibrated = self._platt_calibrate(confidence)
            elif method == CalibrationMethod.ISOTONIC:
                calibrated = self._isotonic_calibrate(confidence)
            elif method == CalibrationMethod.TEMPERATURE:
                calibrated = self._temperature_calibrate(confidence)
            elif method == CalibrationMethod.BAYESIAN:
                calibrated = self._bayesian_calibrate(confidence, historical_accuracy)
            else:  # HISTORICAL_BINNING
                calibrated = self._binning_calibrate(confidence)
        
            # Calculate calibration error
            if historical_accuracy is not None:
                calibration_error = abs(confidence - historical_accuracy)
            else:
                calibration_error = 0.0
        
            # Determine calibration status
            status = self._determine_status(confidence, historical_accuracy)
        
            # Calculate adjustment factor
            adjustment_factor = calibrated / confidence if confidence > 0 else 1.0
        
            # Calculate uncertainty bounds
            uncertainty_bounds = self._calculate_uncertainty_bounds(calibrated)
        
            # Generate recommendations
            recommendations = self._generate_recommendations(status, calibration_error)
        
            result = CalibrationResult(
                original_confidence=confidence,
                calibrated_confidence=calibrated,
                calibration_method=method,
                calibration_status=status,
                calibration_error=calibration_error,
                historical_accuracy_at_confidence=historical_accuracy,
                adjustment_factor=adjustment_factor,
                uncertainty_bounds=uncertainty_bounds,
                recommendations=recommendations
            )
        
            self.calibration_history.append(result)
        
            return result
        except Exception as e:
            logger.error(f"Error in calibrate: {e}")
            raise
    
    def _platt_calibrate(self, confidence: float) -> float:
        """Apply Platt scaling calibration"""
        # Platt scaling: P(y=1|f) = 1 / (1 + exp(A*f + B))
        # where f is the original confidence
        try:
            logit = math.log(confidence / (1 - confidence + 1e-10) + 1e-10)
            scaled_logit = self.platt_a * logit + self.platt_b
            calibrated = 1 / (1 + math.exp(-scaled_logit))
            return max(0.01, min(0.99, calibrated))
        except Exception as e:
            logger.error(f"Error in _platt_calibrate: {e}")
            raise
    
    def _isotonic_calibrate(self, confidence: float) -> float:
        """Apply isotonic regression calibration"""
        # Simple piecewise linear interpolation based on buckets
        try:
            bucket = round(confidence / self.bucket_size) * self.bucket_size
        
            if bucket in self.calibration_buckets and len(self.calibration_buckets[bucket]) >= 5:
                accuracy = sum(self.calibration_buckets[bucket]) / len(self.calibration_buckets[bucket])
                return accuracy
        
            # Interpolate between nearest buckets
            lower_bucket = bucket - self.bucket_size
            upper_bucket = bucket + self.bucket_size
        
            lower_acc = None
            upper_acc = None
        
            if lower_bucket in self.calibration_buckets and len(self.calibration_buckets[lower_bucket]) >= 3:
                lower_acc = sum(self.calibration_buckets[lower_bucket]) / len(self.calibration_buckets[lower_bucket])
        
            if upper_bucket in self.calibration_buckets and len(self.calibration_buckets[upper_bucket]) >= 3:
                upper_acc = sum(self.calibration_buckets[upper_bucket]) / len(self.calibration_buckets[upper_bucket])
        
            if lower_acc is not None and upper_acc is not None:
                # Linear interpolation
                t = (confidence - lower_bucket) / self.bucket_size
                return lower_acc + t * (upper_acc - lower_acc)
            elif lower_acc is not None:
                return lower_acc
            elif upper_acc is not None:
                return upper_acc
        
            return confidence  # No calibration data available
        except Exception as e:
            logger.error(f"Error in _isotonic_calibrate: {e}")
            raise
    
    def _temperature_calibrate(self, confidence: float) -> float:
        """Apply temperature scaling calibration"""
        # Temperature scaling: softmax(logits / T)
        try:
            logit = math.log(confidence / (1 - confidence + 1e-10) + 1e-10)
            scaled_logit = logit / self.learned_temperature
            calibrated = 1 / (1 + math.exp(-scaled_logit))
            return max(0.01, min(0.99, calibrated))
        except Exception as e:
            logger.error(f"Error in _temperature_calibrate: {e}")
            raise
    
    def _bayesian_calibrate(
        self,
        confidence: float,
        historical_accuracy: Optional[float]
    ) -> float:
        """Apply Bayesian calibration with prior"""
        try:
            if historical_accuracy is None:
                return confidence
        
            # Bayesian update: posterior = prior * likelihood
            # Use historical accuracy as prior, confidence as likelihood
            prior = historical_accuracy
            likelihood = confidence
        
            # Weighted combination
            posterior = (
                self.prior_strength * prior + 
                (1 - self.prior_strength) * likelihood
            )
        
            return max(0.01, min(0.99, posterior))
        except Exception as e:
            logger.error(f"Error in _bayesian_calibrate: {e}")
            raise
    
    def _binning_calibrate(self, confidence: float) -> float:
        """Apply historical binning calibration"""
        try:
            bucket = round(confidence / self.bucket_size) * self.bucket_size
        
            if bucket in self.calibration_buckets and len(self.calibration_buckets[bucket]) >= self.min_samples:
                return sum(self.calibration_buckets[bucket]) / len(self.calibration_buckets[bucket])
        
            return confidence
        except Exception as e:
            logger.error(f"Error in _binning_calibrate: {e}")
            raise
    
    def _get_historical_accuracy(self, confidence: float) -> Optional[float]:
        """Get historical accuracy at a given confidence level"""
        try:
            bucket = round(confidence / self.bucket_size) * self.bucket_size
        
            if bucket in self.calibration_buckets and len(self.calibration_buckets[bucket]) >= 5:
                return sum(self.calibration_buckets[bucket]) / len(self.calibration_buckets[bucket])
        
            # Try nearby buckets
            for offset in [self.bucket_size, -self.bucket_size, 2*self.bucket_size, -2*self.bucket_size]:
                nearby = bucket + offset
                if nearby in self.calibration_buckets and len(self.calibration_buckets[nearby]) >= 5:
                    return sum(self.calibration_buckets[nearby]) / len(self.calibration_buckets[nearby])
        
            return None
        except Exception as e:
            logger.error(f"Error in _get_historical_accuracy: {e}")
            raise
    
    def _determine_status(
        self,
        confidence: float,
        historical_accuracy: Optional[float]
    ) -> CalibrationStatus:
        """Determine calibration status"""
        try:
            if historical_accuracy is None:
                return CalibrationStatus.INSUFFICIENT_DATA
        
            diff = confidence - historical_accuracy
        
            if abs(diff) < 0.1:
                return CalibrationStatus.WELL_CALIBRATED
            elif diff > 0:
                return CalibrationStatus.OVERCONFIDENT
            else:
                return CalibrationStatus.UNDERCONFIDENT
        except Exception as e:
            logger.error(f"Error in _determine_status: {e}")
            raise
    
    def _calculate_uncertainty_bounds(
        self,
        calibrated: float
    ) -> Tuple[float, float]:
        """Calculate uncertainty bounds for calibrated confidence"""
        # Use Wilson score interval for binomial proportion
        try:
            n = len(self.prediction_history)
        
            if n < 10:
                # Wide bounds with little data
                margin = 0.2
            else:
                # Wilson score interval approximation
                z = 1.96  # 95% confidence
                p = calibrated
                margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
        
            lower = max(0.0, calibrated - margin)
            upper = min(1.0, calibrated + margin)
        
            return (lower, upper)
        except Exception as e:
            logger.error(f"Error in _calculate_uncertainty_bounds: {e}")
            raise
    
    def _select_best_method(self) -> CalibrationMethod:
        """Select the best calibration method based on available data"""
        try:
            n = len(self.prediction_history)
        
            if n < 20:
                return CalibrationMethod.BAYESIAN
            elif n < 50:
                return CalibrationMethod.TEMPERATURE
            elif n < 100:
                return CalibrationMethod.HISTORICAL_BINNING
            else:
                return CalibrationMethod.ISOTONIC
        except Exception as e:
            logger.error(f"Error in _select_best_method: {e}")
            raise
    
    def _update_calibration_parameters(self):
        """Update calibration parameters based on history"""
        try:
            if len(self.prediction_history) < 30:
                return
        
            # Update temperature
            confidences = [r.confidence for r in self.prediction_history[-100:]]
            accuracies = [1.0 if r.was_correct else 0.0 for r in self.prediction_history[-100:]]
        
            avg_conf = statistics.mean(confidences)
            avg_acc = statistics.mean(accuracies)
        
            if avg_conf > 0 and avg_acc > 0:
                # Adjust temperature to match accuracy
                self.learned_temperature = avg_conf / avg_acc if avg_acc > 0 else 1.0
                self.learned_temperature = max(0.5, min(2.0, self.learned_temperature))
        
            logger.debug(f"Updated calibration: temperature={self.learned_temperature:.3f}")
        except Exception as e:
            logger.error(f"Error in _update_calibration_parameters: {e}")
            raise
    
    def _generate_recommendations(
        self,
        status: CalibrationStatus,
        calibration_error: float
    ) -> List[str]:
        """Generate recommendations based on calibration status"""
        try:
            recommendations = []
        
            if status == CalibrationStatus.OVERCONFIDENT:
                recommendations.append("Reduce confidence levels in predictions")
                recommendations.append("Consider wider stop-losses")
                recommendations.append("Use smaller position sizes")
                if calibration_error > 0.2:
                    recommendations.append("CRITICAL: Severely overconfident - halve position sizes")
        
            elif status == CalibrationStatus.UNDERCONFIDENT:
                recommendations.append("Predictions are more accurate than confidence suggests")
                recommendations.append("Consider increasing position sizes slightly")
        
            elif status == CalibrationStatus.INSUFFICIENT_DATA:
                recommendations.append("Collect more prediction outcomes for better calibration")
                recommendations.append("Use conservative position sizing until calibrated")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_recommendations: {e}")
            raise
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get calibration statistics"""
        try:
            if len(self.prediction_history) < 10:
                return {
                    'status': 'insufficient_data',
                    'samples': len(self.prediction_history)
                }
        
            confidences = [r.confidence for r in self.prediction_history]
            accuracies = [1.0 if r.was_correct else 0.0 for r in self.prediction_history]
        
            # Expected Calibration Error (ECE)
            ece = 0.0
            for bucket, outcomes in self.calibration_buckets.items():
                if len(outcomes) > 0:
                    bucket_acc = sum(outcomes) / len(outcomes)
                    bucket_conf = bucket
                    ece += len(outcomes) * abs(bucket_acc - bucket_conf)
            ece /= len(self.prediction_history) if self.prediction_history else 1
        
            return {
                'samples': len(self.prediction_history),
                'overall_accuracy': statistics.mean(accuracies),
                'avg_confidence': statistics.mean(confidences),
                'expected_calibration_error': ece,
                'learned_temperature': self.learned_temperature,
                'bucket_count': len(self.calibration_buckets),
                'calibration_status': 'well_calibrated' if ece < 0.1 else 'needs_calibration'
            }
        except Exception as e:
            logger.error(f"Error in get_calibration_stats: {e}")
            raise
    
    def get_reliability_diagram_data(self) -> Dict[str, List[float]]:
        """Get data for plotting a reliability diagram"""
        try:
            buckets = sorted(self.calibration_buckets.keys())
        
            bucket_centers = []
            bucket_accuracies = []
            bucket_counts = []
        
            for bucket in buckets:
                outcomes = self.calibration_buckets[bucket]
                if len(outcomes) >= 3:
                    bucket_centers.append(bucket)
                    bucket_accuracies.append(sum(outcomes) / len(outcomes))
                    bucket_counts.append(len(outcomes))
        
            return {
                'confidence_buckets': bucket_centers,
                'actual_accuracy': bucket_accuracies,
                'sample_counts': bucket_counts,
                'perfect_calibration': bucket_centers  # Diagonal line
            }
        except Exception as e:
            logger.error(f"Error in get_reliability_diagram_data: {e}")
            raise


def create_calibrator(config: Optional[Dict[str, Any]] = None) -> ConfidenceCalibrator:
    """Create a new confidence calibrator instance"""
    return ConfidenceCalibrator(config)


__all__ = [
    'ConfidenceCalibrator',
    'CalibrationResult',
    'CalibrationMethod',
    'CalibrationStatus',
    'PredictionRecord',
    'create_calibrator',
]
