"""
Unified Observability Hub
=========================

Centralized monitoring, metrics aggregation, alerting, and system health tracking.
Provides a single pane of glass for all trading system observability.

Features:
- Real-time metrics collection and aggregation
- Multi-level alerting with escalation
- Component health monitoring
- Performance dashboards
- Anomaly detection
- Audit trail logging
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Set
from collections import deque
import threading
import logging
import time
import statistics
import hashlib
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked."""
    COUNTER = auto()      # Monotonically increasing (trades, orders)
    GAUGE = auto()        # Point-in-time value (PnL, position size)
    HISTOGRAM = auto()    # Distribution (latency, slippage)
    RATE = auto()         # Rate per second (orders/sec, fills/sec)
    TIMER = auto()        # Duration measurements


class MetricLevel(Enum):
    """Metric importance levels."""
    CRITICAL = auto()     # Must always be collected
    HIGH = auto()         # Important for operations
    MEDIUM = auto()       # Useful for analysis
    LOW = auto()          # Nice to have
    DEBUG = auto()        # Development only


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = auto()     # Immediate action required
    HIGH = auto()         # Action required soon
    MEDIUM = auto()       # Should investigate
    LOW = auto()          # Informational
    INFO = auto()         # FYI only


class SystemHealth(Enum):
    """Overall system health status."""
    HEALTHY = auto()      # All systems nominal
    DEGRADED = auto()     # Some issues, still operational
    IMPAIRED = auto()     # Significant issues
    CRITICAL = auto()     # Major problems
    DOWN = auto()         # System not operational


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime
    metric_type: MetricType
    level: MetricLevel = MetricLevel.MEDIUM
    tags: Dict[str, str] = field(default_factory=dict)
    component: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "type": self.metric_type.name,
            "level": self.level.name,
            "tags": self.tags,
            "component": self.component,
        }


@dataclass
class Alert:
    """System alert."""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    component: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.name,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "tags": self.tags,
        }


@dataclass
class ComponentStatus:
    """Status of a system component."""
    name: str
    health: SystemHealth
    last_heartbeat: datetime
    metrics_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    uptime_seconds: float = 0.0
    version: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_healthy(self) -> bool:
        return self.health in (SystemHealth.HEALTHY, SystemHealth.DEGRADED)
    
    @property
    def is_stale(self) -> bool:
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() > 60


@dataclass
class ObservabilityConfig:
    """Configuration for observability hub."""
    metrics_retention_hours: int = 24
    max_metrics_per_component: int = 10000
    alert_retention_hours: int = 168  # 1 week
    heartbeat_timeout_seconds: int = 60
    anomaly_detection_enabled: bool = True
    anomaly_std_threshold: float = 3.0
    rate_limit_per_second: int = 1000
    enable_audit_logging: bool = True
    dashboard_refresh_seconds: int = 5


class MetricAggregator:
    """Aggregates metrics over time windows."""
    
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._values: deque = deque()
        self._lock = threading.Lock()
    
    def add(self, value: float, timestamp: datetime) -> None:
        with self._lock:
            self._values.append((timestamp, value))
            self._cleanup()
    
    def _cleanup(self) -> None:
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        while self._values and self._values[0][0] < cutoff:
            self._values.popleft()
    
    def get_stats(self) -> Dict[str, float]:
        with self._lock:
            self._cleanup()
            if not self._values:
                return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0, "std": 0}
            
            values = [v[1] for v in self._values]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "sum": sum(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
            }


class AlertManager:
    """Manages alerts and escalation."""
    
    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self._alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=10000)
        self._handlers: Dict[AlertSeverity, List[Callable]] = {s: [] for s in AlertSeverity}
        self._lock = threading.Lock()
        self._suppressed: Set[str] = set()
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: str,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Alert:
        alert_id = hashlib.sha256(
            f"{title}:{component}:{metric_name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow(),
            component=component,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
            tags=tags or {},
        )
        
        with self._lock:
            # Check suppression
            suppression_key = f"{title}:{component}"
            if suppression_key in self._suppressed:
                logger.debug(f"Alert suppressed: {title}")
                return alert
            
            self._alerts[alert_id] = alert
            self._alert_history.append(alert)
        
        # Trigger handlers
        self._trigger_handlers(alert)
        
        logger.warning(f"Alert created: [{severity.name}] {title} - {message}")
        return alert
    
    def acknowledge(self, alert_id: str, acknowledged_by: str) -> bool:
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].acknowledged = True
                self._alerts[alert_id].acknowledged_by = acknowledged_by
                self._alerts[alert_id].acknowledged_at = datetime.utcnow()
                return True
        return False
    
    def resolve(self, alert_id: str) -> bool:
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolved = True
                self._alerts[alert_id].resolved_at = datetime.utcnow()
                return True
        return False
    
    def suppress(self, title: str, component: str, duration_seconds: int = 3600) -> None:
        suppression_key = f"{title}:{component}"
        with self._lock:
            self._suppressed.add(suppression_key)
        
        # Auto-unsuppress after duration
        def unsuppress():
            time.sleep(duration_seconds)
            with self._lock:
                self._suppressed.discard(suppression_key)
        
        threading.Thread(target=unsuppress, daemon=True).start()
    
    def register_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]) -> None:
        self._handlers[severity].append(handler)
    
    def _trigger_handlers(self, alert: Alert) -> None:
        for handler in self._handlers[alert.severity]:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        with self._lock:
            alerts = [a for a in self._alerts.values() if not a.resolved]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_counts(self) -> Dict[str, int]:
        with self._lock:
            counts = {s.name: 0 for s in AlertSeverity}
            for alert in self._alerts.values():
                if not alert.resolved:
                    counts[alert.severity.name] += 1
            return counts


class AnomalyDetector:
    """Detects anomalies in metric streams."""
    
    def __init__(self, std_threshold: float = 3.0, min_samples: int = 30):
        self.std_threshold = std_threshold
        self.min_samples = min_samples
        self._baselines: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def check(self, metric_name: str, value: float) -> Optional[Dict[str, Any]]:
        with self._lock:
            if metric_name not in self._baselines:
                self._baselines[metric_name] = deque(maxlen=1000)
            
            baseline = self._baselines[metric_name]
            baseline.append(value)
            
            if len(baseline) < self.min_samples:
                return None
            
            values = list(baseline)
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0
            
            if std == 0:
                return None
            
            z_score = abs(value - mean) / std
            
            if z_score > self.std_threshold:
                return {
                    "metric_name": metric_name,
                    "value": value,
                    "mean": mean,
                    "std": std,
                    "z_score": z_score,
                    "threshold": self.std_threshold,
                }
        
        return None


class UnifiedObservabilityHub:
    """
    Centralized observability hub for the trading system.
    
    Provides:
    - Metrics collection and aggregation
    - Alerting with escalation
    - Component health monitoring
    - Anomaly detection
    - Audit logging
    """
    
    def __init__(self, config: Optional[ObservabilityConfig] = None):
        self.config = config or ObservabilityConfig()
        
        # Core components
        self._metrics: Dict[str, deque] = {}
        self._aggregators: Dict[str, MetricAggregator] = {}
        self._components: Dict[str, ComponentStatus] = {}
        self._alert_manager = AlertManager(self.config)
        self._anomaly_detector = AnomalyDetector(self.config.anomaly_std_threshold)
        
        # Thread safety
        self._lock = threading.Lock()
        self._rate_limiter: Dict[str, float] = {}
        
        # Audit log
        self._audit_log: deque = deque(maxlen=100000)
        
        # Start time
        self._start_time = datetime.utcnow()
        
        logger.info("UnifiedObservabilityHub initialized")
    
    # ==================== METRICS ====================
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        level: MetricLevel = MetricLevel.MEDIUM,
        component: str = "unknown",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric data point."""
        # Rate limiting
        if not self._check_rate_limit(component):
            return
        
        timestamp = datetime.utcnow()
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=timestamp,
            metric_type=metric_type,
            level=level,
            component=component,
            tags=tags or {},
        )
        
        with self._lock:
            # Store metric
            key = f"{component}:{name}"
            if key not in self._metrics:
                self._metrics[key] = deque(maxlen=self.config.max_metrics_per_component)
                self._aggregators[key] = MetricAggregator()
            
            self._metrics[key].append(point)
            self._aggregators[key].add(value, timestamp)
            
            # Update component
            if component not in self._components:
                self._components[component] = ComponentStatus(
                    name=component,
                    health=SystemHealth.HEALTHY,
                    last_heartbeat=timestamp,
                )
            self._components[component].metrics_count += 1
            self._components[component].last_heartbeat = timestamp
        
        # Anomaly detection
        if self.config.anomaly_detection_enabled:
            anomaly = self._anomaly_detector.check(key, value)
            if anomaly:
                self._alert_manager.create_alert(
                    title=f"Anomaly detected: {name}",
                    message=f"Value {value:.4f} is {anomaly['z_score']:.2f} std from mean",
                    severity=AlertSeverity.MEDIUM,
                    component=component,
                    metric_name=name,
                    metric_value=value,
                    threshold=anomaly["threshold"],
                )
    
    def record_counter(self, name: str, increment: float = 1.0, component: str = "unknown", tags: Optional[Dict[str, str]] = None) -> None:
        """Record a counter increment."""
        self.record_metric(name, increment, MetricType.COUNTER, MetricLevel.MEDIUM, component, tags)
    
    def record_gauge(self, name: str, value: float, component: str = "unknown", tags: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge value."""
        self.record_metric(name, value, MetricType.GAUGE, MetricLevel.MEDIUM, component, tags)
    
    def record_histogram(self, name: str, value: float, component: str = "unknown", tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value."""
        self.record_metric(name, value, MetricType.HISTOGRAM, MetricLevel.MEDIUM, component, tags)
    
    def record_timer(self, name: str, duration_ms: float, component: str = "unknown", tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer duration."""
        self.record_metric(name, duration_ms, MetricType.TIMER, MetricLevel.MEDIUM, component, tags)
    
    def get_metric_stats(self, component: str, name: str) -> Dict[str, float]:
        """Get aggregated stats for a metric."""
        key = f"{component}:{name}"
        with self._lock:
            if key in self._aggregators:
                return self._aggregators[key].get_stats()
        return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0, "std": 0}
    
    def get_metrics(self, component: Optional[str] = None, name: Optional[str] = None, since: Optional[datetime] = None) -> List[MetricPoint]:
        """Query metrics with filters."""
        with self._lock:
            results = []
            for key, points in self._metrics.items():
                comp, metric_name = key.split(":", 1)
                if component and comp != component:
                    continue
                if name and metric_name != name:
                    continue
                
                for point in points:
                    if since and point.timestamp < since:
                        continue
                    results.append(point)
            
            return sorted(results, key=lambda p: p.timestamp, reverse=True)
    
    # ==================== ALERTS ====================
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: str,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Alert:
        """Create a new alert."""
        alert = self._alert_manager.create_alert(
            title=title,
            message=message,
            severity=severity,
            component=component,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
            tags=tags,
        )
        
        # Update component health
        with self._lock:
            if component in self._components:
                if severity == AlertSeverity.CRITICAL:
                    self._components[component].health = SystemHealth.CRITICAL
                    self._components[component].error_count += 1
                elif severity == AlertSeverity.HIGH:
                    if self._components[component].health != SystemHealth.CRITICAL:
                        self._components[component].health = SystemHealth.IMPAIRED
                    self._components[component].error_count += 1
                elif severity == AlertSeverity.MEDIUM:
                    self._components[component].warning_count += 1
        
        # Audit log
        if self.config.enable_audit_logging:
            self._audit("ALERT_CREATED", {"alert": alert.to_dict()})
        
        return alert
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        result = self._alert_manager.acknowledge(alert_id, acknowledged_by)
        if result and self.config.enable_audit_logging:
            self._audit("ALERT_ACKNOWLEDGED", {"alert_id": alert_id, "by": acknowledged_by})
        return result
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        result = self._alert_manager.resolve(alert_id)
        if result and self.config.enable_audit_logging:
            self._audit("ALERT_RESOLVED", {"alert_id": alert_id})
        return result
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active (unresolved) alerts."""
        return self._alert_manager.get_active_alerts(severity)
    
    def get_alert_counts(self) -> Dict[str, int]:
        """Get counts of active alerts by severity."""
        return self._alert_manager.get_alert_counts()
    
    def register_alert_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]) -> None:
        """Register a handler for alerts of a specific severity."""
        self._alert_manager.register_handler(severity, handler)
    
    def suppress_alert(self, title: str, component: str, duration_seconds: int = 3600) -> None:
        """Suppress an alert for a duration."""
        self._alert_manager.suppress(title, component, duration_seconds)
    
    # ==================== COMPONENTS ====================
    
    def register_component(self, name: str, version: str = "unknown", metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a system component."""
        with self._lock:
            self._components[name] = ComponentStatus(
                name=name,
                health=SystemHealth.HEALTHY,
                last_heartbeat=datetime.utcnow(),
                version=version,
                metadata=metadata or {},
            )
        
        logger.info(f"Component registered: {name} v{version}")
    
    def heartbeat(self, component: str) -> None:
        """Record a heartbeat from a component."""
        with self._lock:
            if component in self._components:
                self._components[component].last_heartbeat = datetime.utcnow()
                # Reset health if was stale
                if self._components[component].health == SystemHealth.DOWN:
                    self._components[component].health = SystemHealth.HEALTHY
    
    def set_component_health(self, component: str, health: SystemHealth) -> None:
        """Manually set component health."""
        with self._lock:
            if component in self._components:
                self._components[component].health = health
    
    def get_component_status(self, component: str) -> Optional[ComponentStatus]:
        """Get status of a component."""
        with self._lock:
            return self._components.get(component)
    
    def get_all_components(self) -> List[ComponentStatus]:
        """Get status of all components."""
        with self._lock:
            # Update stale components
            now = datetime.utcnow()
            for comp in self._components.values():
                if comp.is_stale and comp.health != SystemHealth.DOWN:
                    comp.health = SystemHealth.DOWN
                comp.uptime_seconds = (now - self._start_time).total_seconds()
            
            return list(self._components.values())
    
    def get_system_health(self) -> SystemHealth:
        """Get overall system health."""
        components = self.get_all_components()
        if not components:
            return SystemHealth.HEALTHY
        
        healths = [c.health for c in components]
        
        if SystemHealth.DOWN in healths or SystemHealth.CRITICAL in healths:
            return SystemHealth.CRITICAL
        if SystemHealth.IMPAIRED in healths:
            return SystemHealth.IMPAIRED
        if SystemHealth.DEGRADED in healths:
            return SystemHealth.DEGRADED
        return SystemHealth.HEALTHY
    
    # ==================== DASHBOARD ====================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for observability dashboard."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": self.get_system_health().name,
            "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
            "components": [
                {
                    "name": c.name,
                    "health": c.health.name,
                    "last_heartbeat": c.last_heartbeat.isoformat(),
                    "metrics_count": c.metrics_count,
                    "error_count": c.error_count,
                    "warning_count": c.warning_count,
                    "is_stale": c.is_stale,
                }
                for c in self.get_all_components()
            ],
            "alerts": self.get_alert_counts(),
            "active_alerts": [a.to_dict() for a in self.get_active_alerts()[:10]],
            "metrics_summary": self._get_metrics_summary(),
        }
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self._lock:
            total_points = sum(len(m) for m in self._metrics.values())
            return {
                "total_metrics": len(self._metrics),
                "total_data_points": total_points,
                "components_count": len(self._components),
            }
    
    # ==================== AUDIT ====================
    
    def _audit(self, action: str, data: Dict[str, Any]) -> None:
        """Record an audit log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "data": data,
        }
        self._audit_log.append(entry)
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return list(self._audit_log)[-limit:]
    
    # ==================== UTILITIES ====================
    
    def _check_rate_limit(self, component: str) -> bool:
        """Check if component is within rate limit."""
        now = time.time()
        with self._lock:
            if component not in self._rate_limiter:
                self._rate_limiter[component] = now
                return True
            
            elapsed = now - self._rate_limiter[component]
            if elapsed < 1.0 / self.config.rate_limit_per_second:
                return False
            
            self._rate_limiter[component] = now
            return True
    
    def cleanup(self) -> None:
        """Cleanup old data."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.metrics_retention_hours)
        
        with self._lock:
            for key in list(self._metrics.keys()):
                # Remove old points
                while self._metrics[key] and self._metrics[key][0].timestamp < cutoff:
                    self._metrics[key].popleft()
                
                # Remove empty metrics
                if not self._metrics[key]:
                    del self._metrics[key]
                    if key in self._aggregators:
                        del self._aggregators[key]
        
        logger.debug("Observability cleanup completed")
    
    def export_metrics(self, format: str = "json") -> str:
        """Export all metrics."""
        metrics = self.get_metrics()
        if format == "json":
            return json.dumps([m.to_dict() for m in metrics], indent=2)
        return "\n".join(f"{m.name}={m.value}" for m in metrics)
