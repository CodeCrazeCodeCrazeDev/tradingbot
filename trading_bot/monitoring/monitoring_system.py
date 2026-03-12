"""
Monitoring System - Unified interface for system monitoring

This module provides a centralized MonitoringSystem class that coordinates
all monitoring, alerting, and performance tracking operations.

Author: AlphaAlgo Trading System
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()


@dataclass
class Metric:
    """Represents a monitoring metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.name,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels
        }


@dataclass
class Alert:
    """Represents a monitoring alert"""
    alert_id: str
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'level': self.level.name,
            'message': self.message,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'acknowledged': self.acknowledged
        }


@dataclass
class MonitoringConfig:
    """Configuration for MonitoringSystem"""
    metrics_enabled: bool = True
    alerts_enabled: bool = True
    health_check_interval: int = 30
    metrics_retention_hours: int = 24
    alert_channels: List[str] = field(default_factory=lambda: ["log"])
    thresholds: Dict[str, float] = field(default_factory=dict)


class MonitoringSystem:
    """
    Unified Monitoring System for the trading platform.
    
    This class provides:
    - Metrics collection and aggregation
    - Alert management and routing
    - Health check monitoring
    - Performance tracking
    - System status reporting
    """
    
    def __init__(self, config: Optional[Union[MonitoringConfig, Dict[str, Any]]] = None):
        """
        Initialize the Monitoring System.
        
        Args:
            config: Configuration object or dictionary
        """
        if isinstance(config, dict):
            self.config = MonitoringConfig(**config)
        elif config is None:
            self.config = MonitoringConfig()
        else:
            self.config = config
        
        self.metrics: Dict[str, List[Metric]] = {}
        self.alerts: List[Alert] = []
        self.health_checks: Dict[str, Callable] = {}
        self.alert_handlers: Dict[str, Callable] = {}
        self._running = False
        self._start_time = datetime.now()
        
        # Default thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'latency_ms': 100.0,
            'error_rate': 0.05,
            **self.config.thresholds
        }
        
        logger.info("MonitoringSystem initialized")
    
    def start(self) -> None:
        """Start the monitoring system"""
        self._running = True
        self._start_time = datetime.now()
        logger.info("MonitoringSystem started")
    
    def stop(self) -> None:
        """Stop the monitoring system"""
        self._running = False
        logger.info("MonitoringSystem stopped")
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional labels
        """
        if not self.config.metrics_enabled:
            return
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(metric)
        
        # Check thresholds
        if name in self.thresholds:
            if value > self.thresholds[name]:
                self.create_alert(
                    level=AlertLevel.WARNING,
                    message=f"Metric {name} exceeded threshold: {value} > {self.thresholds[name]}",
                    source="threshold_monitor"
                )
        
        # Cleanup old metrics
        self._cleanup_old_metrics(name)
    
    def _cleanup_old_metrics(self, name: str) -> None:
        """Remove metrics older than retention period"""
        if name not in self.metrics:
            return
        
        cutoff = datetime.now()
        retention_seconds = self.config.metrics_retention_hours * 3600
        
        self.metrics[name] = [
            m for m in self.metrics[name]
            if (cutoff - m.timestamp).total_seconds() < retention_seconds
        ]
    
    def get_metric(self, name: str, last_n: int = 1) -> List[Metric]:
        """
        Get recent metric values.
        
        Args:
            name: Metric name
            last_n: Number of recent values to return
        
        Returns:
            List of recent metrics
        """
        if name not in self.metrics:
            return []
        return self.metrics[name][-last_n:]
    
    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Args:
            name: Metric name
        
        Returns:
            Dictionary with min, max, avg, count
        """
        if name not in self.metrics or not self.metrics[name]:
            return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
        
        values = [m.value for m in self.metrics[name]]
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
    
    def create_alert(
        self,
        level: AlertLevel,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            level: Alert severity level
            message: Alert message
            source: Source of the alert
            metadata: Additional metadata
        
        Returns:
            Created alert
        """
        if not self.config.alerts_enabled:
            return None
        
        alert = Alert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            level=level,
            message=message,
            source=source,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Route alert to handlers
        self._route_alert(alert)
        
        # Log alert
        log_level = {
            AlertLevel.DEBUG: logging.DEBUG,
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.INFO)
        
        logger.log(log_level, f"[{source}] {message}")
        
        return alert
    
    def _route_alert(self, alert: Alert) -> None:
        """Route alert to configured handlers"""
        for channel in self.config.alert_channels:
            if channel in self.alert_handlers:
                try:
                    self.alert_handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Error routing alert to {channel}: {e}")
    
    def register_alert_handler(self, channel: str, handler: Callable) -> None:
        """
        Register an alert handler.
        
        Args:
            channel: Channel name
            handler: Handler function
        """
        self.alert_handlers[channel] = handler
        logger.info(f"Registered alert handler: {channel}")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID to acknowledge
        
        Returns:
            True if acknowledged, False if not found
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            level: Filter by level
            acknowledged: Filter by acknowledged status
            limit: Maximum number of alerts to return
        
        Returns:
            List of alerts
        """
        alerts = self.alerts
        
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        return alerts[-limit:]
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check function.
        
        Args:
            name: Health check name
            check_func: Function that returns (healthy: bool, message: str)
        """
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def run_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all registered health checks.
        
        Returns:
            Dictionary of health check results
        """
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                start = time.time()
                healthy, message = check_func()
                duration = (time.time() - start) * 1000
                
                results[name] = {
                    'healthy': healthy,
                    'message': message,
                    'duration_ms': duration,
                    'timestamp': datetime.now().isoformat()
                }
                
                if not healthy:
                    self.create_alert(
                        level=AlertLevel.ERROR,
                        message=f"Health check failed: {name} - {message}",
                        source="health_monitor"
                    )
                    
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'message': str(e),
                    'duration_ms': 0,
                    'timestamp': datetime.now().isoformat()
                }
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            System status dictionary
        """
        health_results = self.run_health_checks()
        all_healthy = all(r['healthy'] for r in health_results.values()) if health_results else True
        
        unacked_alerts = len([a for a in self.alerts if not a.acknowledged])
        critical_alerts = len([a for a in self.alerts if a.level == AlertLevel.CRITICAL and not a.acknowledged])
        
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        return {
            'status': 'healthy' if all_healthy and critical_alerts == 0 else 'degraded',
            'running': self._running,
            'uptime_seconds': uptime,
            'health_checks': health_results,
            'metrics_count': sum(len(m) for m in self.metrics.values()),
            'alerts_total': len(self.alerts),
            'alerts_unacknowledged': unacked_alerts,
            'alerts_critical': critical_alerts,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            'running': self._running,
            'metrics_tracked': len(self.metrics),
            'total_alerts': len(self.alerts),
            'health_checks_registered': len(self.health_checks),
            'alert_handlers_registered': len(self.alert_handlers)
        }


# Factory function
def create_monitoring_system(config: Optional[Dict[str, Any]] = None) -> MonitoringSystem:
    """Create a configured MonitoringSystem instance"""
    return MonitoringSystem(config)


# Singleton instance
_monitoring_system: Optional[MonitoringSystem] = None


def get_monitoring_system() -> MonitoringSystem:
    """Get the global MonitoringSystem instance"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system
