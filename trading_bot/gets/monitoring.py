"""
GETS Monitoring and Metrics Collection

Real-time metrics for system health, performance, and drift detection:
- Prometheus-compatible metrics export
- Drift detection (calibration, disagreement, feature drift)
- Alert system for critical thresholds
- Dashboard data endpoints
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import deque
import threading
import numpy as np

from .types import GETSSignal, GovernanceDecision

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_prometheus(self) -> str:
        """Convert to Prometheus format."""
        label_str = ",".join([f'{k}="{v}"' for k, v in self.labels.items()])
        if label_str:
            return f"{name}{{{label_str}}} {value} {int(self.timestamp.timestamp() * 1000)}"
        return f"{name} {value} {int(self.timestamp.timestamp() * 1000)}"


class MetricsCollector:
    """Central metrics collection for GETS."""
    
    def __init__(self, retention_seconds: int = 3600):
        self.retention_seconds = retention_seconds
        self._metrics: Dict[str, deque] = {}
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
    
    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record counter metric (monotonically increasing)."""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._counters:
                self._counters[key] = 0
            self._counters[key] += value
            
            self._add_metric_point(name, value, labels or {})
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record gauge metric (can go up or down)."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            
            self._add_metric_point(name, value, labels or {})
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record histogram metric (distribution of values)."""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            
            # Keep only recent values
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-5000:]
            
            self._add_metric_point(name, value, labels or {})
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key for metric."""
        if not labels:
            return name
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{name}{{{label_str}}}"
    
    def _add_metric_point(self, name: str, value: float, labels: Dict[str, str]):
        """Add metric point to history."""
        key = self._make_key(name, labels)
        
        if key not in self._metrics:
            self._metrics[key] = deque(maxlen=10000)
        
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels
        )
        self._metrics[key].append(point)
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get current counter value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get current gauge value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key, 0)
    
    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        with self._lock:
            key = self._make_key(name, labels)
            values = self._histograms.get(key, [])
            
            if not values:
                return {'count': 0, 'sum': 0, 'avg': 0, 'p50': 0, 'p95': 0, 'p99': 0}
            
            arr = np.array(values)
            return {
                'count': len(arr),
                'sum': float(np.sum(arr)),
                'avg': float(np.mean(arr)),
                'p50': float(np.percentile(arr, 50)),
                'p95': float(np.percentile(arr, 95)),
                'p99': float(np.percentile(arr, 99))
            }
    
    def get_prometheus_export(self) -> str:
        """Export all metrics in Prometheus format."""
        lines = []
        
        # Counters
        with self._lock:
            for key, value in self._counters.items():
                lines.append(f"# TYPE {key.split('{')[0]} counter")
                lines.append(f"{key} {value}")
            
            # Gauges
            for key, value in self._gauges.items():
                lines.append(f"# TYPE {key.split('{')[0]} gauge")
                lines.append(f"{key} {value}")
            
            # Histograms
            for key, values in self._histograms.items():
                base_name = key.split('{')[0]
                stats = self.get_histogram_stats(base_name)
                
                lines.append(f"# TYPE {base_name} histogram")
                lines.append(f"{base_name}_count {stats['count']}")
                lines.append(f"{base_name}_sum {stats['sum']}")
                lines.append(f"{base_name}_bucket{{le=\"0.005\"}} {sum(1 for v in values if v <= 0.005)}")
                lines.append(f"{base_name}_bucket{{le=\"0.01\"}} {sum(1 for v in values if v <= 0.01)}")
                lines.append(f"{base_name}_bucket{{le=\"0.025\"}} {sum(1 for v in values if v <= 0.025)}")
                lines.append(f"{base_name}_bucket{{le=\"+Inf\"}} {len(values)}")
        
        return "\n".join(lines)
    
    def get_time_series(self, name: str, labels: Dict[str, str] = None, 
                        since: Optional[datetime] = None) -> List[Dict]:
        """Get time series for a metric."""
        with self._lock:
            key = self._make_key(name, labels)
            points = self._metrics.get(key, deque())
            
            if since:
                points = [p for p in points if p.timestamp > since]
            
            return [
                {
                    'timestamp': p.timestamp.isoformat(),
                    'value': p.value,
                    'labels': p.labels
                }
                for p in points
            ]


class GETSMetrics:
    """GETS-specific metrics collection."""
    
    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or MetricsCollector()
    
    def record_signal(self, signal: GETSSignal, latency_ms: float):
        """Record signal generation metrics."""
        # Signal quality
        self.collector.record_gauge(
            'gets_signal_confidence',
            signal.confidence,
            {'symbol': signal.symbol, 'horizon': signal.horizon.name}
        )
        
        self.collector.record_gauge(
            'gets_signal_edge',
            signal.expected_edge,
            {'symbol': signal.symbol}
        )
        
        # Decision
        self.collector.record_counter(
            'gets_decisions_total',
            1,
            {'decision': signal.governance_decision.name}
        )
        
        # Abstention
        if signal.abstain_recommended:
            self.collector.record_counter(
                'gets_abstentions_total',
                1,
                {'reason': signal.abstain_reason or 'unknown'}
            )
        
        # Latency
        self.collector.record_histogram(
            'gets_signal_latency_ms',
            latency_ms
        )
        
        # Disagreement
        geom = signal.disagreement_geometry
        self.collector.record_gauge(
            'gets_disagreement_consensus',
            geom.forecast_consensus_score,
            {'symbol': signal.symbol}
        )
        
        self.collector.record_gauge(
            'gets_disagreement_entropy',
            geom.disagreement_entropy,
            {'symbol': signal.symbol}
        )
    
    def record_outcome(self, signal: GETSSignal, realized_return: float):
        """Record outcome for calibration tracking."""
        self.collector.record_counter('gets_outcomes_total', 1)
        
        # Prediction error
        pred_error = abs(signal.expected_edge - realized_return)
        self.collector.record_histogram('gets_prediction_error', pred_error)
        
        # Calibration: was predicted confidence accurate?
        # If confidence was high and return was positive: good
        # If confidence was high and return was negative: bad
        calibration = 1.0 if (signal.confidence > 0.7 and realized_return * signal.direction > 0) else 0.0
        self.collector.record_gauge('gets_calibration_score', calibration)
        
        # Regime-stratified
        if hasattr(signal.diagnosis_report, 'regime_label') and signal.diagnosis_report.regime_label:
            self.collector.record_histogram(
                'gets_return_by_regime',
                realized_return,
                {'regime': signal.diagnosis_report.regime_label.name}
            )
    
    def record_model_health(self, model_name: str, healthy: bool, latency_ms: float):
        """Record model health status."""
        self.collector.record_gauge(
            'gets_model_health',
            1.0 if healthy else 0.0,
            {'model': model_name}
        )
        
        self.collector.record_histogram(
            'gets_model_latency_ms',
            latency_ms,
            {'model': model_name}
        )


class DriftDetector:
    """
    Detect various forms of drift in GETS:
    - Calibration drift
    - Disagreement topology drift
    - Feature distribution drift
    - Performance drift
    """
    
    def __init__(
        self,
        calibration_threshold: float = 0.1,
        disagreement_threshold: float = 0.2,
        performance_threshold: float = 0.15,
        window_size: int = 100
    ):
        self.calibration_threshold = calibration_threshold
        self.disagreement_threshold = disagreement_threshold
        self.performance_threshold = performance_threshold
        self.window_size = window_size
        
        self._calibration_history: deque = deque(maxlen=window_size)
        self._disagreement_history: deque = deque(maxlen=window_size)
        self._performance_history: deque = deque(maxlen=window_size)
        self._drift_alerts: List[Dict] = []
    
    def update_calibration(self, predicted: float, realized: float, confidence: float):
        """Update calibration tracking."""
        # Brier score component
        accuracy = 1.0 if (predicted > 0 and realized > 0) or (predicted < 0 and realized < 0) else 0.0
        brier = (confidence - accuracy) ** 2
        
        self._calibration_history.append({
            'timestamp': datetime.now(),
            'predicted': predicted,
            'realized': realized,
            'confidence': confidence,
            'brier_score': brier
        })
    
    def update_disagreement(self, consensus_score: float, entropy: float):
        """Update disagreement topology tracking."""
        self._disagreement_history.append({
            'timestamp': datetime.now(),
            'consensus': consensus_score,
            'entropy': entropy
        })
    
    def update_performance(self, ic: float, sharpe: float):
        """Update performance tracking."""
        self._performance_history.append({
            'timestamp': datetime.now(),
            'ic': ic,
            'sharpe': sharpe
        })
    
    def detect_drift(self) -> List[Dict]:
        """Detect all forms of drift."""
        alerts = []
        
        # Calibration drift
        if len(self._calibration_history) >= self.window_size:
            recent = list(self._calibration_history)[-50:]
            older = list(self._calibration_history)[:50]
            
            recent_brier = np.mean([r['brier_score'] for r in recent])
            older_brier = np.mean([r['brier_score'] for r in older])
            
            if recent_brier > older_brier + self.calibration_threshold:
                alerts.append({
                    'type': 'CALIBRATION_DRIFT',
                    'severity': 'HIGH',
                    'message': f'Calibration degraded: {older_brier:.3f} -> {recent_brier:.3f}',
                    'timestamp': datetime.now()
                })
        
        # Disagreement drift
        if len(self._disagreement_history) >= self.window_size:
            recent = list(self._disagreement_history)[-50:]
            older = list(self._disagreement_history)[:50]
            
            recent_entropy = np.mean([r['entropy'] for r in recent])
            older_entropy = np.mean([r['entropy'] for r in older])
            
            if abs(recent_entropy - older_entropy) > self.disagreement_threshold:
                alerts.append({
                    'type': 'DISAGREEMENT_DRIFT',
                    'severity': 'MEDIUM',
                    'message': f'Disagreement pattern shifted: {older_entropy:.3f} -> {recent_entropy:.3f}',
                    'timestamp': datetime.now()
                })
        
        # Performance drift
        if len(self._performance_history) >= self.window_size:
            recent = list(self._performance_history)[-30:]
            older = list(self._performance_history)[30:60]
            
            if recent and older:
                recent_ic = np.mean([r['ic'] for r in recent])
                older_ic = np.mean([r['ic'] for r in older])
                
                if recent_ic < older_ic - self.performance_threshold:
                    alerts.append({
                        'type': 'PERFORMANCE_DRIFT',
                        'severity': 'CRITICAL',
                        'message': f'IC degraded: {older_ic:.3f} -> {recent_ic:.3f}',
                        'timestamp': datetime.now()
                    })
        
        self._drift_alerts.extend(alerts)
        return alerts
    
    def get_active_alerts(self, since_hours: int = 24) -> List[Dict]:
        """Get active drift alerts."""
        cutoff = datetime.now() - timedelta(hours=since_hours)
        return [a for a in self._drift_alerts if a['timestamp'] > cutoff]


class AlertManager:
    """Manage and route alerts from GETS."""
    
    def __init__(self):
        self._handlers: List[Callable[[Dict], None]] = []
        self._alert_history: deque = deque(maxlen=1000)
        self._lock = threading.RLock()
    
    def register_handler(self, handler: Callable[[Dict], None]):
        """Register alert handler."""
        self._handlers.append(handler)
    
    def send_alert(self, alert: Dict):
        """Send alert to all handlers."""
        with self._lock:
            self._alert_history.append(alert)
        
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def get_alert_history(self, severity: Optional[str] = None) -> List[Dict]:
        """Get alert history."""
        with self._lock:
            alerts = list(self._alert_history)
        
        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]
        
        return alerts


class HealthCheck:
    """System health monitoring."""
    
    def __init__(self, gets_instance=None):
        self.gets = gets_instance
        self._last_check: Optional[datetime] = None
        self._health_status: Dict[str, Any] = {}
    
    def check_health(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'overall': 'HEALTHY',
            'components': {}
        }
        
        if not self.gets:
            status['overall'] = 'UNKNOWN'
            return status
        
        # Check GETS layers
        status['components']['layer1'] = self._check_layer1()
        status['components']['layer2'] = self._check_layer2()
        status['components']['layer3'] = self._check_layer3()
        status['components']['layer5'] = self._check_layer5()
        
        # Determine overall status
        if any(c['status'] == 'CRITICAL' for c in status['components'].values()):
            status['overall'] = 'CRITICAL'
        elif any(c['status'] == 'WARNING' for c in status['components'].values()):
            status['overall'] = 'WARNING'
        
        self._last_check = datetime.now()
        self._health_status = status
        
        return status
    
    def _check_layer1(self) -> Dict:
        """Check Layer 1 health."""
        if not self.gets.layer1_perception:
            return {'status': 'CRITICAL', 'message': 'Layer 1 not initialized'}
        
        # Check model availability
        available_models = self.gets.layer1_perception.get_available_models()
        if not available_models:
            return {'status': 'WARNING', 'message': 'No foundation models available'}
        
        return {
            'status': 'HEALTHY',
            'available_models': len(available_models),
            'models': [m.value for m in available_models]
        }
    
    def _check_layer2(self) -> Dict:
        """Check Layer 2 health."""
        if not self.gets.layer2_representation:
            return {'status': 'CRITICAL', 'message': 'Layer 2 not initialized'}
        
        return {
            'status': 'HEALTHY',
            'heads_initialized': True
        }
    
    def _check_layer3(self) -> Dict:
        """Check Layer 3 health."""
        if not self.gets.layer3_diagnosis:
            return {'status': 'CRITICAL', 'message': 'Layer 3 not initialized'}
        
        return {
            'status': 'HEALTHY',
            'disagreement_engine_active': True
        }
    
    def _check_layer5(self) -> Dict:
        """Check Layer 5 health."""
        if not self.gets.layer5_governance:
            return {'status': 'CRITICAL', 'message': 'Layer 5 not initialized'}
        
        audit_status = self.gets.layer5_governance.get_audit_status()
        
        return {
            'status': 'HEALTHY',
            'audit_chain_valid': audit_status.get('chain_valid', False),
            'total_promotions': audit_status.get('total_records', 0)
        }


def create_monitoring_system(gets_instance=None) -> tuple:
    """
    Factory function to create complete monitoring system.
    
    Returns:
        (MetricsCollector, GETSMetrics, DriftDetector, AlertManager, HealthCheck)
    """
    collector = MetricsCollector()
    gets_metrics = GETSMetrics(collector)
    drift = DriftDetector()
    alerts = AlertManager()
    health = HealthCheck(gets_instance)
    
    return collector, gets_metrics, drift, alerts, health
