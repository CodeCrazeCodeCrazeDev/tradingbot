"""
DGS Monitoring and Dashboard System

Real-time monitoring, metrics collection, and dashboard API.
Provides health checks, performance metrics, and operational visibility.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum
import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """A single metric data point"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    

@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    last_check: datetime
    response_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    metric_name: str
    condition: str  # e.g., ">", "<", "=="
    threshold: float
    severity: str  # info, warning, critical
    duration_seconds: int  # How long condition must persist
    notification_channels: List[str]


class MetricsCollector:
    """
    Centralized metrics collection for DGS.
    
    Collects:
    - Decision throughput
    - Latency percentiles
    - Decision outcomes
    - Component health
    - Resource utilization
    """
    
    def __init__(self, retention_seconds: float = 3600):
        self.retention = retention_seconds
        self.metrics: deque = deque(maxlen=100000)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Metric dimensions
        self.dimensions = {
            'environment': 'production',
            'service': 'dgs'
        }
        
    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric"""
        
        self.counters[name] += value
        
        metric = Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=self.counters[name],
            timestamp=datetime.utcnow(),
            labels={**self.dimensions, **(labels or {})}
        )
        self.metrics.append(metric)
    
    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric"""
        
        self.gauges[name] = value
        
        metric = Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.utcnow(),
            labels={**self.dimensions, **(labels or {})}
        )
        self.metrics.append(metric)
    
    def record_timer(
        self,
        name: str,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer metric"""
        
        self.histograms[name].append(duration_ms)
        
        # Keep histograms bounded
        if len(self.histograms[name]) > 10000:
            self.histograms[name] = self.histograms[name][-5000:]
        
        metric = Metric(
            name=name,
            metric_type=MetricType.TIMER,
            value=duration_ms,
            timestamp=datetime.utcnow(),
            labels={**self.dimensions, **(labels or {})}
        )
        self.metrics.append(metric)
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric"""
        
        self.histograms[name].append(value)
        
        metric = Metric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            timestamp=datetime.utcnow(),
            labels={**self.dimensions, **(labels or {})}
        )
        self.metrics.append(metric)
    
    def get_counter(self, name: str) -> float:
        """Get current counter value"""
        return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        """Get current gauge value"""
        return self.gauges.get(name, 0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        
        values = self.histograms.get(name, [])
        
        if not values:
            return {'count': 0, 'min': 0, 'max': 0, 'mean': 0, 'p99': 0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            'count': n,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'mean': sum(sorted_values) / n,
            'p50': sorted_values[int(n * 0.5)],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[int(n * 0.99)] if n > 100 else sorted_values[-1]
        }
    
    def get_metrics_summary(
        self,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get metrics summary since a given time"""
        
        if since is None:
            since = datetime.utcnow() - timedelta(hours=1)
        
        # Filter metrics
        recent_metrics = [
            m for m in self.metrics
            if m.timestamp >= since
        ]
        
        # Group by name and type
        by_name = defaultdict(list)
        for m in recent_metrics:
            by_name[m.name].append(m.value)
        
        summary = {}
        for name, values in by_name.items():
            if values:
                summary[name] = {
                    'count': len(values),
                    'latest': values[-1],
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values)
                }
        
        return summary


class HealthMonitor:
    """
    Health monitoring for DGS components.
    """
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_history: Dict[str, deque] = {}
        self.check_interval_seconds = 60
        
    def register_component(
        self,
        name: str,
        check_func: Callable[[], HealthCheck]
    ) -> None:
        """Register a component for health monitoring"""
        
        self.health_checks[name] = check_func
        self.health_history[name] = deque(maxlen=100)
        logger.info(f"Registered health check for {name}")
    
    async def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                start = time.time()
                result = check_func()
                result.response_time_ms = (time.time() - start) * 1000
                result.last_check = datetime.utcnow()
                
                results[name] = result
                self.health_history[name].append(result)
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = HealthCheck(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(e)}",
                    last_check=datetime.utcnow(),
                    response_time_ms=0
                )
        
        return results
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health"""
        
        # Check latest health results
        statuses = []
        for history in self.health_history.values():
            if history:
                statuses.append(history[-1].status)
        
        if not statuses:
            return HealthStatus.UNKNOWN
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        
        overall = self.get_overall_health()
        
        components = []
        for name, history in self.health_history.items():
            if history:
                latest = history[-1]
                components.append({
                    'name': name,
                    'status': latest.status.value,
                    'message': latest.message,
                    'response_time_ms': latest.response_time_ms,
                    'last_check': latest.last_check.isoformat()
                })
        
        return {
            'overall_status': overall.value,
            'timestamp': datetime.utcnow().isoformat(),
            'components': components,
            'healthy_count': sum(1 for c in components if c['status'] == 'healthy'),
            'unhealthy_count': sum(1 for c in components if c['status'] == 'unhealthy')
        }


class AlertManager:
    """
    Alert management for DGS.
    """
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Dict] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_handlers: Dict[str, Callable] = {}
        
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule"""
        self.rules.append(rule)
    
    def register_notification_handler(
        self,
        channel: str,
        handler: Callable[[Dict], None]
    ) -> None:
        """Register a notification handler"""
        self.notification_handlers[channel] = handler
    
    def evaluate_rules(
        self,
        metrics_collector: MetricsCollector
    ) -> List[Dict]:
        """Evaluate all alert rules against current metrics"""
        
        triggered = []
        
        for rule in self.rules:
            # Get metric value
            if rule.metric_name in metrics_collector.gauges:
                value = metrics_collector.gauges[rule.metric_name]
            elif rule.metric_name in metrics_collector.counters:
                value = metrics_collector.counters[rule.metric_name]
            else:
                continue
            
            # Evaluate condition
            condition_met = self._evaluate_condition(
                value, rule.condition, rule.threshold
            )
            
            if condition_met:
                alert_key = f"{rule.name}:{rule.metric_name}"
                
                # Check if already alerting
                if alert_key not in self.active_alerts:
                    alert = {
                        'rule': rule.name,
                        'metric': rule.metric_name,
                        'value': value,
                        'threshold': rule.threshold,
                        'severity': rule.severity,
                        'triggered_at': datetime.utcnow().isoformat(),
                        'channels': rule.notification_channels
                    }
                    
                    self.active_alerts[alert_key] = alert
                    self.alert_history.append(alert)
                    triggered.append(alert)
                    
                    # Send notifications
                    self._send_notifications(alert)
            else:
                # Clear alert if condition no longer met
                alert_key = f"{rule.name}:{rule.metric_name}"
                if alert_key in self.active_alerts:
                    del self.active_alerts[alert_key]
        
        return triggered
    
    def _evaluate_condition(
        self,
        value: float,
        condition: str,
        threshold: float
    ) -> bool:
        """Evaluate alert condition"""
        
        if condition == '>':
            return value > threshold
        elif condition == '<':
            return value < threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return value == threshold
        
        return False
    
    def _send_notifications(self, alert: Dict) -> None:
        """Send alert notifications"""
        
        for channel in alert['channels']:
            handler = self.notification_handlers.get(channel)
            if handler:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {e}")


class DashboardAPI:
    """
    Dashboard API for DGS monitoring.
    Provides endpoints for real-time dashboard data.
    """
    
    def __init__(
        self,
        metrics: MetricsCollector,
        health: HealthMonitor,
        alerts: AlertManager
    ):
        self.metrics = metrics
        self.health = health
        self.alerts = alerts
        
    def get_overview(self) -> Dict[str, Any]:
        """Get dashboard overview"""
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'health': self.health.get_overall_health().value,
            'metrics': {
                'decisions_total': self.metrics.get_counter('decisions_total'),
                'decisions_approved': self.metrics.get_counter('decisions_approved'),
                'decisions_rejected': self.metrics.get_counter('decisions_rejected'),
                'avg_latency_ms': self.metrics.get_histogram_stats('decision_latency_ms')['mean']
            },
            'active_alerts': len(self.alerts.active_alerts),
            'system_status': 'operational' if self.health.get_overall_health() == HealthStatus.HEALTHY else 'degraded'
        }
    
    def get_decision_metrics(self) -> Dict[str, Any]:
        """Get decision-related metrics"""
        
        latency_stats = self.metrics.get_histogram_stats('decision_latency_ms')
        
        return {
            'throughput': {
                'decisions_per_minute': self.metrics.get_counter('decisions_total') / 60
            },
            'latency': latency_stats,
            'outcomes': {
                'approved': self.metrics.get_counter('decisions_approved'),
                'rejected': self.metrics.get_counter('decisions_rejected'),
                'resized': self.metrics.get_counter('decisions_resized'),
                'abstained': self.metrics.get_counter('decisions_abstained')
            },
            'quality': {
                'avg_confidence': self.metrics.get_gauge('avg_decision_confidence'),
                'avg_robustness': self.metrics.get_gauge('avg_decision_robustness')
            }
        }
    
    def get_component_status(self) -> List[Dict[str, Any]]:
        """Get status of all components"""
        
        status = []
        
        for name, history in self.health.health_history.items():
            if history:
                latest = history[-1]
                
                # Get recent metrics for this component
                component_metrics = self.metrics.get_metrics_summary(
                    since=datetime.utcnow() - timedelta(minutes=5)
                )
                
                status.append({
                    'name': name,
                    'health': latest.status.value,
                    'response_time_ms': latest.response_time_ms,
                    'last_check': latest.last_check.isoformat(),
                    'recent_metrics': component_metrics
                })
        
        return status
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk-related metrics"""
        
        return {
            'portfolio_var': self.metrics.get_gauge('portfolio_var_1d'),
            'concentration_risk': self.metrics.get_gauge('concentration_risk'),
            'correlation_risk': self.metrics.get_gauge('correlation_risk'),
            'stress_test_loss': self.metrics.get_gauge('max_stress_loss'),
            'safety_violations': self.metrics.get_counter('safety_violations_total')
        }
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        """Get active alerts, optionally filtered by severity"""
        
        alerts = list(self.alerts.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        return alerts
    
    def get_historical_metrics(
        self,
        metric_name: str,
        duration_minutes: int = 60
    ) -> List[Dict]:
        """Get historical data for a metric"""
        
        since = datetime.utcnow() - timedelta(minutes=duration_minutes)
        
        data = []
        for metric in self.metrics.metrics:
            if metric.name == metric_name and metric.timestamp >= since:
                data.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.value,
                    'labels': metric.labels
                })
        
        return data


class MonitoringSystem:
    """
    Complete monitoring system combining metrics, health, and alerts.
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.health = HealthMonitor()
        self.alerts = AlertManager()
        self.dashboard = DashboardAPI(self.metrics, self.health, self.alerts)
        
        self._running = False
        self._monitor_task = None
        
    async def start(self) -> None:
        """Start monitoring system"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring system started")
    
    async def stop(self) -> None:
        """Stop monitoring system"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("Monitoring system stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        
        while self._running:
            try:
                # Run health checks
                await self.health.run_health_checks()
                
                # Evaluate alert rules
                self.alerts.evaluate_rules(self.metrics)
                
                # Record system metrics
                self._record_system_metrics()
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def _record_system_metrics(self) -> None:
        """Record system-level metrics"""
        
        # Memory usage (would use psutil in production)
        self.metrics.record_gauge('system_memory_usage', 0.5)
        
        # CPU usage
        self.metrics.record_gauge('system_cpu_usage', 0.3)
        
        # Queue depths
        self.metrics.record_gauge('decision_queue_depth', 0)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        
        return {
            'overview': self.dashboard.get_overview(),
            'decisions': self.dashboard.get_decision_metrics(),
            'components': self.dashboard.get_component_status(),
            'risk': self.dashboard.get_risk_metrics(),
            'alerts': self.dashboard.get_alerts()
        }
