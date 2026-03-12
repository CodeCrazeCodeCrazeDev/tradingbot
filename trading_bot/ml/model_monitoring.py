"""
from typing import Any, Callable, List, Optional, Set, Tuple
ML Model Monitoring System

Production monitoring for ML models:
- Concept drift detection
- Performance degradation alerts
- Feature distribution monitoring
- Automatic retraining triggers
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque
import json

logger = logging.getLogger(__name__)

try:
    from scipy import stats
    from scipy.spatial.distance import jensenshannon
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available for statistical tests")

try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class DriftType(Enum):
    """Types of drift"""
    CONCEPT_DRIFT = "concept_drift"  # P(Y|X) changes
    DATA_DRIFT = "data_drift"  # P(X) changes
    LABEL_DRIFT = "label_drift"  # P(Y) changes
    PREDICTION_DRIFT = "prediction_drift"  # Model predictions change


class DriftSeverity(Enum):
    """Drift severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModelType(Enum):
    """Model types for appropriate metrics"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    RANKING = "ranking"


@dataclass
class DriftResult:
    """Result of drift detection"""
    drift_type: DriftType
    detected: bool
    severity: DriftSeverity
    score: float  # 0-1, higher = more drift
    p_value: Optional[float]
    threshold: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_name: str
    model_type: ModelType
    metrics: Dict[str, float]
    sample_size: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringAlert:
    """Monitoring alert"""
    alert_type: str
    model_name: str
    severity: str
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False


class StatisticalDriftDetector:
    """
    Statistical tests for drift detection.
    """
    
    @staticmethod
    def ks_test(reference: np.ndarray, current: np.ndarray) -> Tuple[float, float]:
        """
        Kolmogorov-Smirnov test for distribution comparison.
        
        Returns:
            (statistic, p_value)
        """
        if not SCIPY_AVAILABLE:
            return 0.0, 1.0
        
        statistic, p_value = stats.ks_2samp(reference, current)
        return statistic, p_value
    
    @staticmethod
    def chi_square_test(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> Tuple[float, float]:
        """
        Chi-square test for categorical/binned data.
        
        Returns:
            (statistic, p_value)
        """
        if not SCIPY_AVAILABLE:
            return 0.0, 1.0
        
        # Bin continuous data
        all_data = np.concatenate([reference, current])
        bin_edges = np.histogram_bin_edges(all_data, bins=bins)
        
        ref_hist, _ = np.histogram(reference, bins=bin_edges)
        cur_hist, _ = np.histogram(current, bins=bin_edges)
        
        # Add small value to avoid division by zero
        ref_hist = ref_hist + 1
        cur_hist = cur_hist + 1
        
        statistic, p_value = stats.chisquare(cur_hist, ref_hist)
        return statistic, p_value
    
    @staticmethod
    def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """
        Population Stability Index (PSI) for distribution shift.
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change
        
        Returns:
            PSI value
        """
        # Bin the data
        all_data = np.concatenate([reference, current])
        bin_edges = np.histogram_bin_edges(all_data, bins=bins)
        
        ref_hist, _ = np.histogram(reference, bins=bin_edges, density=True)
        cur_hist, _ = np.histogram(current, bins=bin_edges, density=True)
        
        # Add small value to avoid log(0)
        ref_hist = ref_hist + 1e-10
        cur_hist = cur_hist + 1e-10
        
        # Normalize
        ref_hist = ref_hist / ref_hist.sum()
        cur_hist = cur_hist / cur_hist.sum()
        
        # Calculate PSI
        psi = np.sum((cur_hist - ref_hist) * np.log(cur_hist / ref_hist))
        
        return psi
    
    @staticmethod
    def js_divergence(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """
        Jensen-Shannon divergence for distribution comparison.
        
        Returns:
            JS divergence (0 = identical, 1 = maximally different)
        """
        if not SCIPY_AVAILABLE:
            return 0.0
        
        # Bin the data
        all_data = np.concatenate([reference, current])
        bin_edges = np.histogram_bin_edges(all_data, bins=bins)
        
        ref_hist, _ = np.histogram(reference, bins=bin_edges, density=True)
        cur_hist, _ = np.histogram(current, bins=bin_edges, density=True)
        
        # Normalize
        ref_hist = ref_hist / ref_hist.sum()
        cur_hist = cur_hist / cur_hist.sum()
        
        return jensenshannon(ref_hist, cur_hist)


class FeatureMonitor:
    """
    Monitor feature distributions for data drift.
    """
    
    def __init__(
        self,
        reference_window: int = 1000,
        detection_window: int = 100,
        psi_threshold: float = 0.2,
        p_value_threshold: float = 0.05
    ):
        self.reference_window = reference_window
        self.detection_window = detection_window
        self.psi_threshold = psi_threshold
        self.p_value_threshold = p_value_threshold
        
        self.reference_data: Dict[str, deque] = {}
        self.current_data: Dict[str, deque] = {}
        self.drift_history: List[DriftResult] = []
    
    def add_sample(self, features: Dict[str, float]):
        """Add a feature sample"""
        for name, value in features.items():
            if name not in self.reference_data:
                self.reference_data[name] = deque(maxlen=self.reference_window)
                self.current_data[name] = deque(maxlen=self.detection_window)
            
            # Fill reference first, then current
            if len(self.reference_data[name]) < self.reference_window:
                self.reference_data[name].append(value)
            else:
                self.current_data[name].append(value)
    
    def check_drift(self, feature_name: Optional[str] = None) -> Dict[str, DriftResult]:
        """
        Check for drift in features.
        
        Args:
            feature_name: Specific feature to check, or None for all
        
        Returns:
            Dict of feature name to DriftResult
        """
        results = {}
        
        features_to_check = [feature_name] if feature_name else list(self.reference_data.keys())
        
        for name in features_to_check:
            if name not in self.reference_data or name not in self.current_data:
                continue
            
            ref = np.array(self.reference_data[name])
            cur = np.array(self.current_data[name])
            
            if len(ref) < 100 or len(cur) < 50:
                continue
            
            # Calculate PSI
            psi = StatisticalDriftDetector.psi(ref, cur)
            
            # KS test
            ks_stat, p_value = StatisticalDriftDetector.ks_test(ref, cur)
            
            # Determine severity
            if psi < 0.1 and p_value > self.p_value_threshold:
                severity = DriftSeverity.NONE
                detected = False
            elif psi < 0.2:
                severity = DriftSeverity.LOW
                detected = True
            elif psi < 0.3:
                severity = DriftSeverity.MEDIUM
                detected = True
            elif psi < 0.5:
                severity = DriftSeverity.HIGH
                detected = True
            else:
                severity = DriftSeverity.CRITICAL
                detected = True
            
            result = DriftResult(
                drift_type=DriftType.DATA_DRIFT,
                detected=detected,
                severity=severity,
                score=psi,
                p_value=p_value,
                threshold=self.psi_threshold,
                details={
                    'feature': name,
                    'ks_statistic': ks_stat,
                    'reference_mean': float(np.mean(ref)),
                    'current_mean': float(np.mean(cur)),
                    'reference_std': float(np.std(ref)),
                    'current_std': float(np.std(cur))
                }
            )
            
            results[name] = result
            
            if detected:
                self.drift_history.append(result)
        
        return results


class PerformanceMonitor:
    """
    Monitor model performance over time.
    """
    
    def __init__(
        self,
        model_name: str,
        model_type: ModelType,
        window_size: int = 100,
        degradation_threshold: float = 0.1
    ):
        self.model_name = model_name
        self.model_type = model_type
        self.window_size = window_size
        self.degradation_threshold = degradation_threshold
        
        self.predictions: deque = deque(maxlen=window_size)
        self.actuals: deque = deque(maxlen=window_size)
        self.performance_history: List[ModelPerformance] = []
        
        self.baseline_metrics: Optional[Dict[str, float]] = None
    
    def add_prediction(self, prediction: Any, actual: Any):
        """Add a prediction-actual pair"""
        self.predictions.append(prediction)
        self.actuals.append(actual)
    
    def set_baseline(self, metrics: Dict[str, float]):
        """Set baseline performance metrics"""
        self.baseline_metrics = metrics
        logger.info(f"Baseline set for {self.model_name}: {metrics}")
    
    def calculate_metrics(self) -> ModelPerformance:
        """Calculate current performance metrics"""
        if len(self.predictions) < 10:
            return None
        
        preds = np.array(list(self.predictions))
        acts = np.array(list(self.actuals))
        
        metrics = {}
        
        if self.model_type == ModelType.CLASSIFICATION:
            if SKLEARN_AVAILABLE:
                metrics['accuracy'] = accuracy_score(acts, preds)
                try:
                    metrics['precision'] = precision_score(acts, preds, average='weighted', zero_division=0)
                    metrics['recall'] = recall_score(acts, preds, average='weighted', zero_division=0)
                    metrics['f1'] = f1_score(acts, preds, average='weighted', zero_division=0)
                except Exception:
                    pass
            else:
                metrics['accuracy'] = np.mean(preds == acts)
        
        elif self.model_type == ModelType.REGRESSION:
            if SKLEARN_AVAILABLE:
                metrics['mse'] = mean_squared_error(acts, preds)
                metrics['mae'] = mean_absolute_error(acts, preds)
                metrics['r2'] = r2_score(acts, preds)
            else:
                metrics['mse'] = np.mean((preds - acts) ** 2)
                metrics['mae'] = np.mean(np.abs(preds - acts))
        
        performance = ModelPerformance(
            model_name=self.model_name,
            model_type=self.model_type,
            metrics=metrics,
            sample_size=len(preds),
            timestamp=datetime.now()
        )
        
        self.performance_history.append(performance)
        
        return performance
    
    def check_degradation(self) -> Optional[DriftResult]:
        """Check for performance degradation"""
        if not self.baseline_metrics:
            return None
        
        current = self.calculate_metrics()
        if not current:
            return None
        
        # Compare to baseline
        degradation_scores = []
        details = {}
        
        for metric_name, baseline_value in self.baseline_metrics.items():
            if metric_name not in current.metrics:
                continue
            
            current_value = current.metrics[metric_name]
            
            # For metrics where higher is better (accuracy, r2, etc.)
            if metric_name in ['accuracy', 'precision', 'recall', 'f1', 'r2']:
                degradation = (baseline_value - current_value) / baseline_value if baseline_value > 0 else 0
            # For metrics where lower is better (mse, mae, etc.)
            else:
                degradation = (current_value - baseline_value) / baseline_value if baseline_value > 0 else 0
            
            degradation_scores.append(degradation)
            details[f'{metric_name}_baseline'] = baseline_value
            details[f'{metric_name}_current'] = current_value
            details[f'{metric_name}_degradation'] = degradation
        
        if not degradation_scores:
            return None
        
        avg_degradation = np.mean(degradation_scores)
        
        # Determine severity
        if avg_degradation < 0.05:
            severity = DriftSeverity.NONE
            detected = False
        elif avg_degradation < 0.1:
            severity = DriftSeverity.LOW
            detected = True
        elif avg_degradation < 0.2:
            severity = DriftSeverity.MEDIUM
            detected = True
        elif avg_degradation < 0.3:
            severity = DriftSeverity.HIGH
            detected = True
        else:
            severity = DriftSeverity.CRITICAL
            detected = True
        
        return DriftResult(
            drift_type=DriftType.CONCEPT_DRIFT,
            detected=detected,
            severity=severity,
            score=avg_degradation,
            p_value=None,
            threshold=self.degradation_threshold,
            details=details
        )


class PredictionMonitor:
    """
    Monitor prediction distribution for prediction drift.
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.reference_predictions: deque = deque(maxlen=window_size)
        self.current_predictions: deque = deque(maxlen=window_size // 10)
    
    def add_prediction(self, prediction: float):
        """Add a prediction"""
        if len(self.reference_predictions) < self.window_size:
            self.reference_predictions.append(prediction)
        else:
            self.current_predictions.append(prediction)
    
    def check_drift(self) -> Optional[DriftResult]:
        """Check for prediction drift"""
        if len(self.reference_predictions) < 100 or len(self.current_predictions) < 50:
            return None
        
        ref = np.array(self.reference_predictions)
        cur = np.array(self.current_predictions)
        
        psi = StatisticalDriftDetector.psi(ref, cur)
        ks_stat, p_value = StatisticalDriftDetector.ks_test(ref, cur)
        
        detected = psi > 0.2 or p_value < 0.05
        
        if psi < 0.1:
            severity = DriftSeverity.NONE
        elif psi < 0.2:
            severity = DriftSeverity.LOW
        elif psi < 0.3:
            severity = DriftSeverity.MEDIUM
        else:
            severity = DriftSeverity.HIGH
        
        return DriftResult(
            drift_type=DriftType.PREDICTION_DRIFT,
            detected=detected,
            severity=severity,
            score=psi,
            p_value=p_value,
            threshold=0.2,
            details={
                'reference_mean': float(np.mean(ref)),
                'current_mean': float(np.mean(cur)),
                'ks_statistic': ks_stat
            }
        )


class ModelMonitoringSystem:
    """
    Complete model monitoring system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.feature_monitors: Dict[str, FeatureMonitor] = {}
        self.performance_monitors: Dict[str, PerformanceMonitor] = {}
        self.prediction_monitors: Dict[str, PredictionMonitor] = {}
        
        self.alerts: List[MonitoringAlert] = []
        self.alert_handlers: List[Callable] = []
        
        self.retraining_triggers: Dict[str, Callable] = {}
    
    def register_model(
        self,
        model_name: str,
        model_type: ModelType,
        baseline_metrics: Optional[Dict[str, float]] = None
    ):
        """Register a model for monitoring"""
        self.feature_monitors[model_name] = FeatureMonitor()
        self.performance_monitors[model_name] = PerformanceMonitor(
            model_name=model_name,
            model_type=model_type
        )
        self.prediction_monitors[model_name] = PredictionMonitor()
        
        if baseline_metrics:
            self.performance_monitors[model_name].set_baseline(baseline_metrics)
        
        logger.info(f"Registered model for monitoring: {model_name}")
    
    def log_prediction(
        self,
        model_name: str,
        features: Dict[str, float],
        prediction: Any,
        actual: Optional[Any] = None
    ):
        """Log a prediction for monitoring"""
        if model_name not in self.feature_monitors:
            logger.warning(f"Model {model_name} not registered")
            return
        
        # Log features
        self.feature_monitors[model_name].add_sample(features)
        
        # Log prediction
        if isinstance(prediction, (int, float)):
            self.prediction_monitors[model_name].add_prediction(float(prediction))
        
        # Log actual if available
        if actual is not None:
            self.performance_monitors[model_name].add_prediction(prediction, actual)
    
    def check_all_drift(self, model_name: str) -> Dict[str, Any]:
        """Run all drift checks for a model"""
        results = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat(),
            'feature_drift': {},
            'performance_drift': None,
            'prediction_drift': None,
            'alerts': []
        }
        
        # Feature drift
        if model_name in self.feature_monitors:
            feature_results = self.feature_monitors[model_name].check_drift()
            results['feature_drift'] = {
                name: {
                    'detected': r.detected,
                    'severity': r.severity.value,
                    'score': r.score
                }
                for name, r in feature_results.items()
            }
            
            # Alert on significant drift
            for name, r in feature_results.items():
                if r.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
                    self._fire_alert(
                        alert_type='feature_drift',
                        model_name=model_name,
                        severity=r.severity.value,
                        message=f"Feature '{name}' drift detected (PSI={r.score:.3f})",
                        metrics=r.details
                    )
        
        # Performance drift
        if model_name in self.performance_monitors:
            perf_result = self.performance_monitors[model_name].check_degradation()
            if perf_result:
                results['performance_drift'] = {
                    'detected': perf_result.detected,
                    'severity': perf_result.severity.value,
                    'score': perf_result.score,
                    'details': perf_result.details
                }
                
                if perf_result.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
                    self._fire_alert(
                        alert_type='performance_degradation',
                        model_name=model_name,
                        severity=perf_result.severity.value,
                        message=f"Performance degradation detected ({perf_result.score:.1%})",
                        metrics=perf_result.details
                    )
                    
                    # Trigger retraining if configured
                    if model_name in self.retraining_triggers:
                        logger.info(f"Triggering retraining for {model_name}")
                        self.retraining_triggers[model_name]()
        
        # Prediction drift
        if model_name in self.prediction_monitors:
            pred_result = self.prediction_monitors[model_name].check_drift()
            if pred_result:
                results['prediction_drift'] = {
                    'detected': pred_result.detected,
                    'severity': pred_result.severity.value,
                    'score': pred_result.score
                }
        
        return results
    
    def _fire_alert(
        self,
        alert_type: str,
        model_name: str,
        severity: str,
        message: str,
        metrics: Dict
    ):
        """Fire a monitoring alert"""
        alert = MonitoringAlert(
            alert_type=alert_type,
            model_name=model_name,
            severity=severity,
            message=message,
            metrics=metrics,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        logger.warning(f"MODEL ALERT [{severity}] {model_name}: {message}")
        
        # Call handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def set_retraining_trigger(self, model_name: str, trigger_func: Callable):
        """Set automatic retraining trigger"""
        self.retraining_triggers[model_name] = trigger_func
    
    def get_monitoring_report(self, model_name: str) -> Dict:
        """Get comprehensive monitoring report"""
        report = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Performance history
        if model_name in self.performance_monitors:
            pm = self.performance_monitors[model_name]
            if pm.performance_history:
                latest = pm.performance_history[-1]
                report['latest_performance'] = {
                    'metrics': latest.metrics,
                    'sample_size': latest.sample_size,
                    'timestamp': latest.timestamp.isoformat()
                }
                report['baseline'] = pm.baseline_metrics
        
        # Drift status
        report['drift_check'] = self.check_all_drift(model_name)
        
        # Recent alerts
        model_alerts = [a for a in self.alerts if a.model_name == model_name]
        report['recent_alerts'] = [
            {
                'type': a.alert_type,
                'severity': a.severity,
                'message': a.message,
                'timestamp': a.timestamp.isoformat()
            }
            for a in model_alerts[-10:]
        ]
        
        return report


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create monitoring system
    monitor = ModelMonitoringSystem()
    
    # Register model
    monitor.register_model(
        model_name="price_predictor",
        model_type=ModelType.REGRESSION,
        baseline_metrics={'mse': 0.001, 'mae': 0.02, 'r2': 0.85}
    )
    
    # Simulate predictions
    np.random.seed(42)
    
    # Reference period (stable)
    for i in range(500):
        features = {
            'feature1': np.random.normal(0, 1),
            'feature2': np.random.normal(5, 2)
        }
        prediction = np.random.normal(0, 0.1)
        actual = prediction + np.random.normal(0, 0.05)
        
        monitor.log_prediction("price_predictor", features, prediction, actual)
    
    # Drift period (distribution shift)
    for i in range(200):
        features = {
            'feature1': np.random.normal(2, 1.5),  # Shifted!
            'feature2': np.random.normal(5, 2)
        }
        prediction = np.random.normal(0.5, 0.2)  # Shifted!
        actual = prediction + np.random.normal(0, 0.1)
        
        monitor.log_prediction("price_predictor", features, prediction, actual)
    
    # Check drift
    results = monitor.check_all_drift("price_predictor")
    
    print("\n" + "="*60)
    logger.info("MODEL MONITORING REPORT")
    print("="*60)
    print(json.dumps(results, indent=2, default=str))
    print("="*60)
