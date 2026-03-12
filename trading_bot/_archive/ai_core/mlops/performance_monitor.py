"""
Performance Monitor for tracking ML model performance in production
"""

import logging
import time
from typing import Any, Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import numpy

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a model."""
    timestamp: str
    latency_ms: float
    throughput: float
    accuracy: Optional[float] = None
    error_rate: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0


@dataclass
class Alert:
    """Performance alert."""
    timestamp: str
    severity: str  # 'warning', 'critical'
    metric: str
    value: float
    threshold: float
    message: str


class PerformanceMonitor:
    """
    Monitor ML model performance in production.
    
    Features:
    - Real-time performance tracking
    - Latency and throughput monitoring
    - Accuracy drift detection
    - Resource usage tracking
    - Alerting on performance degradation
    """
    
    def __init__(
        self,
        model_id: str,
        window_size: int = 1000,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        self.model_id = model_id
        self.window_size = window_size
        self.metrics_history: deque = deque(maxlen=window_size)
        self.alerts: List[Alert] = []
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'latency_ms': 1000.0,  # 1 second
            'error_rate': 0.05,     # 5%
            'accuracy_drop': 0.10,  # 10% drop
            'memory_mb': 2000.0,    # 2GB
            'cpu_percent': 90.0     # 90%
        }
        
        self.baseline_accuracy: Optional[float] = None
        logger.info(f"PerformanceMonitor initialized for {model_id}")
    
    def record_prediction(
        self,
        latency_ms: float,
        is_correct: Optional[bool] = None,
        memory_mb: float = 0.0,
        cpu_percent: float = 0.0
    ):
        """
        Record a single prediction's performance.
        
        Args:
            latency_ms: Prediction latency in milliseconds
            is_correct: Whether prediction was correct (if known)
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage
        """
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            latency_ms=latency_ms,
            throughput=1000.0 / latency_ms if latency_ms > 0 else 0.0,
            accuracy=1.0 if is_correct else 0.0 if is_correct is not None else None,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent
        )
        
        self.metrics_history.append(metrics)
        self._check_alerts(metrics)
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check if any alerts should be triggered."""
        # Check latency
        if metrics.latency_ms > self.alert_thresholds['latency_ms']:
            self._create_alert(
                'critical',
                'latency_ms',
                metrics.latency_ms,
                self.alert_thresholds['latency_ms'],
                f"High latency detected: {metrics.latency_ms:.2f}ms"
            )
        
        # Check memory
        if metrics.memory_mb > self.alert_thresholds['memory_mb']:
            self._create_alert(
                'warning',
                'memory_mb',
                metrics.memory_mb,
                self.alert_thresholds['memory_mb'],
                f"High memory usage: {metrics.memory_mb:.2f}MB"
            )
        
        # Check CPU
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            self._create_alert(
                'warning',
                'cpu_percent',
                metrics.cpu_percent,
                self.alert_thresholds['cpu_percent'],
                f"High CPU usage: {metrics.cpu_percent:.2f}%"
            )
        
        # Check accuracy drift
        if metrics.accuracy is not None:
            if self.baseline_accuracy is None:
                self.baseline_accuracy = metrics.accuracy
            else:
                current_accuracy = self.get_recent_accuracy()
                if current_accuracy is not None:
                    accuracy_drop = self.baseline_accuracy - current_accuracy
                    if accuracy_drop > self.alert_thresholds['accuracy_drop']:
                        self._create_alert(
                            'critical',
                            'accuracy_drop',
                            accuracy_drop,
                            self.alert_thresholds['accuracy_drop'],
                            f"Accuracy drift detected: {accuracy_drop:.2%} drop"
                        )
    
    def _create_alert(
        self,
        severity: str,
        metric: str,
        value: float,
        threshold: float,
        message: str
    ):
        """Create a new alert."""
        alert = Alert(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            metric=metric,
            value=value,
            threshold=threshold,
            message=message
        )
        self.alerts.append(alert)
        logger.warning(f"[{severity.upper()}] {message}")
    
    def get_recent_accuracy(self, window: Optional[int] = None) -> Optional[float]:
        """Get recent accuracy over a window."""
        window = window or min(100, len(self.metrics_history))
        if not self.metrics_history:
            return None
        
        recent = list(self.metrics_history)[-window:]
        accuracies = [m.accuracy for m in recent if m.accuracy is not None]
        
        if not accuracies:
            return None
        
        return np.mean(accuracies)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.metrics_history:
            return {}
        
        metrics = list(self.metrics_history)
        latencies = [m.latency_ms for m in metrics]
        throughputs = [m.throughput for m in metrics]
        accuracies = [m.accuracy for m in metrics if m.accuracy is not None]
        
        stats = {
            'model_id': self.model_id,
            'total_predictions': len(metrics),
            'latency': {
                'mean': np.mean(latencies),
                'median': np.median(latencies),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'max': np.max(latencies)
            },
            'throughput': {
                'mean': np.mean(throughputs),
                'max': np.max(throughputs)
            }
        }
        
        if accuracies:
            stats['accuracy'] = {
                'current': accuracies[-1],
                'mean': np.mean(accuracies),
                'baseline': self.baseline_accuracy
            }
        
        stats['alerts'] = {
            'total': len(self.alerts),
            'critical': len([a for a in self.alerts if a.severity == 'critical']),
            'warning': len([a for a in self.alerts if a.severity == 'warning'])
        }
        
        return stats
    
    def get_recent_alerts(self, count: int = 10) -> List[Alert]:
        """Get recent alerts."""
        return self.alerts[-count:]
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()
        logger.info(f"Cleared alerts for {self.model_id}")
    
    def reset_baseline(self):
        """Reset the baseline accuracy."""
        self.baseline_accuracy = self.get_recent_accuracy()
        logger.info(f"Reset baseline accuracy to {self.baseline_accuracy:.4f}")
