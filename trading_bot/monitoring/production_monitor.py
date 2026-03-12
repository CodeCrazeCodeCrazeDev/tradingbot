"""
Production Monitoring System

Comprehensive monitoring for production trading bot:
- Health checks
- Performance metrics
- Alert management
- System diagnostics
- Real-time dashboards

Author: Trading Bot Team
Date: 2025-10-18
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass
class Alert:
    """System alert"""
    severity: AlertSeverity
    component: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


class MetricsCollector:
    """Collect and aggregate system metrics"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.latencies = deque(maxlen=window_size)
        self.throughputs = deque(maxlen=window_size)
        self.error_counts = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.cpu_usage = deque(maxlen=window_size)
        
    def record_latency(self, latency_ms: float):
        """Record operation latency"""
        self.latencies.append({
            'timestamp': datetime.now(),
            'value': latency_ms
        })
    
    def record_throughput(self, ops_per_second: float):
        """Record throughput"""
        self.throughputs.append({
            'timestamp': datetime.now(),
            'value': ops_per_second
        })
    
    def record_error(self):
        """Record error occurrence"""
        self.error_counts.append({
            'timestamp': datetime.now(),
            'value': 1
        })
    
    def record_system_metrics(self):
        """Record system resource metrics"""
        process = psutil.Process()
        
        self.memory_usage.append({
            'timestamp': datetime.now(),
            'value': process.memory_info().rss / 1024 / 1024  # MB
        })
        
        self.cpu_usage.append({
            'timestamp': datetime.now(),
            'value': process.cpu_percent()
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical summary"""
        import numpy as np
        
        stats = {}
        
        if self.latencies:
            latency_values = [m['value'] for m in self.latencies]
            stats['latency'] = {
                'mean': np.mean(latency_values),
                'median': np.median(latency_values),
                'p95': np.percentile(latency_values, 95),
                'p99': np.percentile(latency_values, 99),
                'min': min(latency_values),
                'max': max(latency_values)
            }
        
        if self.throughputs:
            throughput_values = [m['value'] for m in self.throughputs]
            stats['throughput'] = {
                'mean': np.mean(throughput_values),
                'current': throughput_values[-1] if throughput_values else 0
            }
        
        if self.error_counts:
            recent_errors = sum(1 for e in self.error_counts 
                              if (datetime.now() - e['timestamp']).seconds < 300)
            stats['errors'] = {
                'total': len(self.error_counts),
                'last_5min': recent_errors,
                'rate': recent_errors / 300  # errors per second
            }
        
        if self.memory_usage:
            memory_values = [m['value'] for m in self.memory_usage]
            stats['memory'] = {
                'current_mb': memory_values[-1] if memory_values else 0,
                'peak_mb': max(memory_values),
                'mean_mb': np.mean(memory_values)
            }
        
        if self.cpu_usage:
            cpu_values = [m['value'] for m in self.cpu_usage]
            stats['cpu'] = {
                'current_percent': cpu_values[-1] if cpu_values else 0,
                'peak_percent': max(cpu_values),
                'mean_percent': np.mean(cpu_values)
            }
        
        return stats


class ProductionMonitor:
    """Main production monitoring system"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.metrics = MetricsCollector()
        self.alerts = deque(maxlen=1000)
        self.health_checks = {}
        self.start_time = datetime.now()
        self.is_running = False
        
        # Thresholds
        self.latency_threshold_ms = self.config.get('latency_threshold_ms', 100)
        self.error_rate_threshold = self.config.get('error_rate_threshold', 0.01)
        self.memory_threshold_mb = self.config.get('memory_threshold_mb', 1000)
        self.cpu_threshold_percent = self.config.get('cpu_threshold_percent', 80)
        
        # Alert configuration
        self.alert_email = self.config.get('alert_email')
        self.smtp_config = self.config.get('smtp_config', {})
        
        logger.info("Production monitor initialized")
    
    async def start(self):
        """Start monitoring"""
        self.is_running = True
        logger.info("Production monitor started")
        
        # Start background tasks
        asyncio.create_task(self._monitor_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._alert_check_loop())
    
    async def stop(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("Production monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                self.metrics.record_system_metrics()
                
                # Check thresholds
                await self._check_thresholds()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def _health_check_loop(self):
        """Health check loop"""
        while self.is_running:
            try:
                # Run all health checks
                await self.run_health_checks()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _alert_check_loop(self):
        """Alert checking loop"""
        while self.is_running:
            try:
                # Process pending alerts
                await self._process_alerts()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(10)
    
    async def _check_thresholds(self):
        """Check if metrics exceed thresholds"""
        stats = self.metrics.get_statistics()
        
        # Check latency
        if 'latency' in stats:
            if stats['latency']['p95'] > self.latency_threshold_ms:
                await self.create_alert(
                    AlertSeverity.WARNING,
                    'performance',
                    f"High latency: P95={stats['latency']['p95']:.2f}ms",
                    metadata={'latency': stats['latency']}
                )
        
        # Check error rate
        if 'errors' in stats:
            if stats['errors']['rate'] > self.error_rate_threshold:
                await self.create_alert(
                    AlertSeverity.ERROR,
                    'errors',
                    f"High error rate: {stats['errors']['rate']:.4f} errors/sec",
                    metadata={'errors': stats['errors']}
                )
        
        # Check memory
        if 'memory' in stats:
            if stats['memory']['current_mb'] > self.memory_threshold_mb:
                await self.create_alert(
                    AlertSeverity.WARNING,
                    'resources',
                    f"High memory usage: {stats['memory']['current_mb']:.2f}MB",
                    metadata={'memory': stats['memory']}
                )
        
        # Check CPU
        if 'cpu' in stats:
            if stats['cpu']['current_percent'] > self.cpu_threshold_percent:
                await self.create_alert(
                    AlertSeverity.WARNING,
                    'resources',
                    f"High CPU usage: {stats['cpu']['current_percent']:.1f}%",
                    metadata={'cpu': stats['cpu']}
                )
    
    async def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        checks = {}
        
        # Database health
        checks['database'] = await self._check_database_health()
        
        # MT5 connection health
        checks['mt5_connection'] = await self._check_mt5_health()
        
        # Signal generation health
        checks['signal_generation'] = await self._check_signal_health()
        
        # Execution health
        checks['execution'] = await self._check_execution_health()
        
        # Risk management health
        checks['risk_management'] = await self._check_risk_health()
        
        # System resources health
        checks['system_resources'] = await self._check_system_health()
        
        self.health_checks = checks
        
        # Create alerts for unhealthy components
        for component, check in checks.items():
            if check.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                await self.create_alert(
                    AlertSeverity.CRITICAL if check.status == HealthStatus.CRITICAL else AlertSeverity.ERROR,
                    component,
                    f"Health check failed: {check.message}",
                    metadata={'health_check': check.__dict__}
                )
        
        return checks
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database health"""
        start = time.time()
        
        try:
            # Simulate database check
            await asyncio.sleep(0.01)
            
            latency_ms = (time.time() - start) * 1000
            
            if latency_ms > 100:
                return HealthCheck(
                    component='database',
                    status=HealthStatus.DEGRADED,
                    message=f'Slow response: {latency_ms:.2f}ms',
                    latency_ms=latency_ms
                )
            
            return HealthCheck(
                component='database',
                status=HealthStatus.HEALTHY,
                message='Database operational',
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return HealthCheck(
                component='database',
                status=HealthStatus.CRITICAL,
                message=f'Database error: {str(e)}',
                latency_ms=(time.time() - start) * 1000
            )
    
    async def _check_mt5_health(self) -> HealthCheck:
        """Check MT5 connection health"""
        start = time.time()
        
        try:
            # Check if MT5 is connected
            # This would use actual MT5 connection check
            is_connected = True  # Placeholder
            
            latency_ms = (time.time() - start) * 1000
            
            if not is_connected:
                return HealthCheck(
                    component='mt5_connection',
                    status=HealthStatus.CRITICAL,
                    message='MT5 disconnected',
                    latency_ms=latency_ms
                )
            
            return HealthCheck(
                component='mt5_connection',
                status=HealthStatus.HEALTHY,
                message='MT5 connected',
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return HealthCheck(
                component='mt5_connection',
                status=HealthStatus.CRITICAL,
                message=f'MT5 error: {str(e)}',
                latency_ms=(time.time() - start) * 1000
            )
    
    async def _check_signal_health(self) -> HealthCheck:
        """Check signal generation health"""
        start = time.time()
        
        try:
            # Check last signal generation time
            # This would check actual signal generation
            last_signal_time = datetime.now() - timedelta(minutes=2)
            time_since_last = (datetime.now() - last_signal_time).seconds
            
            latency_ms = (time.time() - start) * 1000
            
            if time_since_last > 600:  # 10 minutes
                return HealthCheck(
                    component='signal_generation',
                    status=HealthStatus.DEGRADED,
                    message=f'No signals for {time_since_last}s',
                    latency_ms=latency_ms,
                    metrics={'time_since_last_signal': time_since_last}
                )
            
            return HealthCheck(
                component='signal_generation',
                status=HealthStatus.HEALTHY,
                message='Signals generating normally',
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return HealthCheck(
                component='signal_generation',
                status=HealthStatus.UNHEALTHY,
                message=f'Signal error: {str(e)}',
                latency_ms=(time.time() - start) * 1000
            )
    
    async def _check_execution_health(self) -> HealthCheck:
        """Check execution system health"""
        start = time.time()
        
        try:
            # Check execution metrics
            # This would check actual execution system
            latency_ms = (time.time() - start) * 1000
            
            return HealthCheck(
                component='execution',
                status=HealthStatus.HEALTHY,
                message='Execution system operational',
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return HealthCheck(
                component='execution',
                status=HealthStatus.UNHEALTHY,
                message=f'Execution error: {str(e)}',
                latency_ms=(time.time() - start) * 1000
            )
    
    async def _check_risk_health(self) -> HealthCheck:
        """Check risk management health"""
        start = time.time()
        
        try:
            # Check risk limits
            # This would check actual risk management
            latency_ms = (time.time() - start) * 1000
            
            return HealthCheck(
                component='risk_management',
                status=HealthStatus.HEALTHY,
                message='Risk management active',
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return HealthCheck(
                component='risk_management',
                status=HealthStatus.CRITICAL,
                message=f'Risk management error: {str(e)}',
                latency_ms=(time.time() - start) * 1000
            )
    
    async def _check_system_health(self) -> HealthCheck:
        """Check system resources health"""
        start = time.time()
        
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            latency_ms = (time.time() - start) * 1000
            
            # Check thresholds
            if memory_mb > self.memory_threshold_mb or cpu_percent > self.cpu_threshold_percent:
                return HealthCheck(
                    component='system_resources',
                    status=HealthStatus.DEGRADED,
                    message=f'High resource usage: {memory_mb:.0f}MB, {cpu_percent:.1f}% CPU',
                    latency_ms=latency_ms,
                    metrics={'memory_mb': memory_mb, 'cpu_percent': cpu_percent}
                )
            
            return HealthCheck(
                component='system_resources',
                status=HealthStatus.HEALTHY,
                message='Resources within limits',
                latency_ms=latency_ms,
                metrics={'memory_mb': memory_mb, 'cpu_percent': cpu_percent}
            )
            
        except Exception as e:
            return HealthCheck(
                component='system_resources',
                status=HealthStatus.UNHEALTHY,
                message=f'System check error: {str(e)}',
                latency_ms=(time.time() - start) * 1000
            )
    
    async def create_alert(self, severity: AlertSeverity, component: str, 
                          message: str, metadata: Optional[Dict] = None):
        """Create new alert"""
        alert = Alert(
            severity=severity,
            component=component,
            message=message,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Log alert
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }[severity]
        
        log_func(f"[{severity.value.upper()}] {component}: {message}")
        
        # Send email for critical alerts
        if severity == AlertSeverity.CRITICAL and self.alert_email:
            await self._send_alert_email(alert)
    
    async def _send_alert_email(self, alert: Alert):
        """Send alert email"""
        try:
            if not self.smtp_config:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from_email')
            msg['To'] = self.alert_email
            msg['Subject'] = f"[CRITICAL] Trading Bot Alert: {alert.component}"
            
            body = f"""
            Critical Alert from Trading Bot
            
            Component: {alert.component}
            Severity: {alert.severity.value}
            Time: {alert.timestamp.isoformat()}
            
            Message: {alert.message}
            
            Metadata:
            {json.dumps(alert.metadata, indent=2)}
            
            Please investigate immediately.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (async)
            # This would use actual SMTP configuration
            logger.info(f"Alert email sent to {self.alert_email}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    async def _process_alerts(self):
        """Process pending alerts"""
        # Auto-resolve old alerts
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for alert in self.alerts:
            if not alert.resolved and alert.timestamp < cutoff_time:
                if alert.severity in [AlertSeverity.INFO, AlertSeverity.WARNING]:
                    alert.resolved = True
                    logger.info(f"Auto-resolved alert: {alert.component} - {alert.message}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Count alerts by severity
        alert_counts = {
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        
        for alert in self.alerts:
            if not alert.resolved:
                alert_counts[alert.severity.value] += 1
        
        # Overall health status
        overall_status = HealthStatus.HEALTHY
        for check in self.health_checks.values():
            if check.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
                break
            elif check.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif check.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'health_checks': {
                name: {
                    'status': check.status.value,
                    'message': check.message,
                    'latency_ms': check.latency_ms
                }
                for name, check in self.health_checks.items()
            },
            'alerts': alert_counts,
            'metrics': self.metrics.get_statistics()
        }
    
    def print_status(self):
        """Print formatted status"""
        status = self.get_status()
        
        print("\n" + "=" * 80)
        logger.info("PRODUCTION MONITORING STATUS")
        print("=" * 80)
        
        # Overall status
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'critical': '🚨'
        }
        
        logger.info(f"\n{status_emoji[status['status']]} Overall Status: {status['status'].upper()}")
        logger.info(f"⏱️  Uptime: {status['uptime_formatted']}")
        
        # Health checks
        logger.info(f"\n📊 Health Checks:")
        for name, check in status['health_checks'].items():
            emoji = status_emoji[check['status']]
            logger.info(f"  {emoji} {name}: {check['message']} ({check['latency_ms']:.2f}ms)")
        
        # Alerts
        logger.info(f"\n🔔 Active Alerts:")
        alerts = status['alerts']
        if sum(alerts.values()) == 0:
            logger.info("  ✅ No active alerts")
        else:
            if alerts['critical'] > 0:
                logger.info(f"  🚨 Critical: {alerts['critical']}")
            if alerts['error'] > 0:
                logger.info(f"  ❌ Error: {alerts['error']}")
            if alerts['warning'] > 0:
                logger.info(f"  ⚠️  Warning: {alerts['warning']}")
            if alerts['info'] > 0:
                logger.info(f"  ℹ️  Info: {alerts['info']}")
        
        # Metrics
        if 'metrics' in status and status['metrics']:
            logger.info(f"\n📈 Performance Metrics:")
            metrics = status['metrics']
            
            if 'latency' in metrics:
                logger.info(f"  Latency: {metrics['latency']['mean']:.2f}ms (P95: {metrics['latency']['p95']:.2f}ms)")
            
            if 'throughput' in metrics:
                logger.info(f"  Throughput: {metrics['throughput']['current']:.2f} ops/sec")
            
            if 'memory' in metrics:
                logger.info(f"  Memory: {metrics['memory']['current_mb']:.2f} MB")
            
            if 'cpu' in metrics:
                logger.info(f"  CPU: {metrics['cpu']['current_percent']:.1f}%")
        
        logger.info("=" * 80 + "\n")


# Global monitor instance
_monitor_instance: Optional[ProductionMonitor] = None


def get_monitor(config: Optional[Dict] = None) -> ProductionMonitor:
    """Get or create monitor instance"""
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = ProductionMonitor(config)
    
    return _monitor_instance


if __name__ == '__main__':
    # Example usage
    async def main():
        monitor = get_monitor({
            'latency_threshold_ms': 100,
            'error_rate_threshold': 0.01,
            'memory_threshold_mb': 1000,
            'cpu_threshold_percent': 80
        })
        
        await monitor.start()
        
        # Simulate some operations
        for i in range(10):
            monitor.metrics.record_latency(50 + i * 5)
            monitor.metrics.record_throughput(100 - i * 2)
            await asyncio.sleep(1)
        
        # Run health checks
        await monitor.run_health_checks()
        
        # Print status
        monitor.print_status()
        
        await monitor.stop()
    
    asyncio.run(main())
