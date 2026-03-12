"""
Automated Performance Monitoring System
========================================

Real-time monitoring of trading bot performance with:
- Latency tracking
- Resource utilization
- Trade performance metrics
- Alerting system
- Dashboard integration

Usage:
    from trading_bot.monitoring import PerformanceMonitor, start_monitoring
    
    # Start monitoring
    monitor = PerformanceMonitor()
    await monitor.start()
    
    # Record metrics
    monitor.record_trade(symbol='EURUSD', profit=100, duration=3600)
    monitor.record_latency('order_execution', 0.05)
    
    # Get report
    report = monitor.get_report()
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """Types of metrics tracked."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE = "resource"
    TRADE = "trade"
    CUSTOM = "custom"


@dataclass
class Alert:
    """Alert data structure."""
    level: AlertLevel
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceThresholds:
    """Performance thresholds for alerting."""
    # Latency thresholds (seconds)
    order_latency_warning: float = 0.5
    order_latency_critical: float = 1.0
    data_latency_warning: float = 0.1
    data_latency_critical: float = 0.5
    
    # Resource thresholds
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 70.0
    memory_critical: float = 90.0
    
    # Trade thresholds
    max_consecutive_losses: int = 5
    max_daily_loss_percent: float = 5.0
    max_drawdown_percent: float = 20.0
    
    # Error thresholds
    error_rate_warning: float = 0.01  # 1%
    error_rate_critical: float = 0.05  # 5%


class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self._metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.max_points)
            
            self._metrics[name].append(MetricPoint(
                name=name,
                value=value,
                tags=tags or {}
            ))
    
    def get_latest(self, name: str) -> Optional[float]:
        """Get the latest value for a metric."""
        with self._lock:
            if name in self._metrics and self._metrics[name]:
                return self._metrics[name][-1].value
        return None
    
    def get_average(self, name: str, window_seconds: int = 60) -> Optional[float]:
        """Get average value over a time window."""
        with self._lock:
            if name not in self._metrics:
                return None
            
            cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
            values = [p.value for p in self._metrics[name] if p.timestamp >= cutoff]
            
            if values:
                return sum(values) / len(values)
        return None
    
    def get_percentile(self, name: str, percentile: float, window_seconds: int = 60) -> Optional[float]:
        """Get percentile value over a time window."""
        with self._lock:
            if name not in self._metrics:
                return None
            
            cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
            values = sorted([p.value for p in self._metrics[name] if p.timestamp >= cutoff])
            
            if values:
                idx = int(len(values) * percentile / 100)
                return values[min(idx, len(values) - 1)]
        return None
    
    def get_count(self, name: str, window_seconds: int = 60) -> int:
        """Get count of metrics in a time window."""
        with self._lock:
            if name not in self._metrics:
                return 0
            
            cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
            return sum(1 for p in self._metrics[name] if p.timestamp >= cutoff)


class ResourceMonitor:
    """Monitors system resources."""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        return self.process.cpu_percent(interval=0.1)
    
    def get_memory_percent(self) -> float:
        """Get current memory usage percentage."""
        return self.process.memory_percent()
    
    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def get_thread_count(self) -> int:
        """Get current thread count."""
        return self.process.num_threads()
    
    def get_open_files(self) -> int:
        """Get number of open file handles."""
        try:
            return len(self.process.open_files())
        except Exception:
            return 0
    
    def get_connections(self) -> int:
        """Get number of network connections."""
        try:
            return len(self.process.connections())
        except Exception:
            return 0
    
    def get_all_metrics(self) -> Dict[str, float]:
        """Get all resource metrics."""
        return {
            'cpu_percent': self.get_cpu_percent(),
            'memory_percent': self.get_memory_percent(),
            'memory_mb': self.get_memory_mb(),
            'thread_count': self.get_thread_count(),
            'open_files': self.get_open_files(),
            'connections': self.get_connections()
        }


class TradeTracker:
    """Tracks trade performance metrics."""
    
    def __init__(self):
        self.trades: List[Dict[str, Any]] = []
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.consecutive_losses: int = 0
        self.max_drawdown: float = 0.0
        self.peak_equity: float = 0.0
        self._lock = threading.Lock()
    
    def record_trade(
        self,
        symbol: str,
        direction: str,
        profit: float,
        pips: float = 0.0,
        duration_seconds: float = 0.0,
        entry_price: float = 0.0,
        exit_price: float = 0.0
    ):
        """Record a completed trade."""
        with self._lock:
            trade = {
                'timestamp': datetime.utcnow(),
                'symbol': symbol,
                'direction': direction,
                'profit': profit,
                'pips': pips,
                'duration': duration_seconds,
                'entry_price': entry_price,
                'exit_price': exit_price
            }
            self.trades.append(trade)
            
            # Update PnL
            self.daily_pnl += profit
            self.total_pnl += profit
            
            # Track consecutive losses
            if profit < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            
            # Update drawdown
            if self.total_pnl > self.peak_equity:
                self.peak_equity = self.total_pnl
            
            current_drawdown = (self.peak_equity - self.total_pnl) / max(self.peak_equity, 1)
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
    
    def get_win_rate(self, window_trades: int = 100) -> float:
        """Get win rate for recent trades."""
        with self._lock:
            recent = self.trades[-window_trades:] if self.trades else []
            if not recent:
                return 0.0
            
            wins = sum(1 for t in recent if t['profit'] > 0)
            return wins / len(recent)
    
    def get_profit_factor(self, window_trades: int = 100) -> float:
        """Get profit factor for recent trades."""
        with self._lock:
            recent = self.trades[-window_trades:] if self.trades else []
            if not recent:
                return 0.0
            
            gross_profit = sum(t['profit'] for t in recent if t['profit'] > 0)
            gross_loss = abs(sum(t['profit'] for t in recent if t['profit'] < 0))
            
            if gross_loss == 0:
                return float('inf') if gross_profit > 0 else 0.0
            
            return gross_profit / gross_loss
    
    def get_average_trade(self, window_trades: int = 100) -> float:
        """Get average trade profit."""
        with self._lock:
            recent = self.trades[-window_trades:] if self.trades else []
            if not recent:
                return 0.0
            
            return sum(t['profit'] for t in recent) / len(recent)
    
    def reset_daily(self):
        """Reset daily metrics."""
        with self._lock:
            self.daily_pnl = 0.0


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self, max_alerts: int = 1000):
        self.alerts: deque = deque(maxlen=max_alerts)
        self.handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
    
    def add_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler."""
        self.handlers.append(handler)
    
    def trigger(self, level: AlertLevel, message: str, metric: str, value: float, threshold: float):
        """Trigger an alert."""
        alert = Alert(
            level=level,
            message=message,
            metric=metric,
            value=value,
            threshold=threshold
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        # Log alert
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.error,
            AlertLevel.EMERGENCY: logger.critical
        }.get(level, logger.warning)
        
        log_method(f"ALERT [{level.value}]: {message} (metric={metric}, value={value}, threshold={threshold})")
    
    def get_recent(self, count: int = 10, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get recent alerts."""
        with self._lock:
            alerts = list(self.alerts)
            if level:
                alerts = [a for a in alerts if a.level == level]
            return alerts[-count:]
    
    def acknowledge(self, alert: Alert):
        """Acknowledge an alert."""
        alert.acknowledged = True


class PerformanceMonitor:
    """
    Main performance monitoring system.
    
    Provides real-time monitoring of:
    - Latency metrics
    - Resource utilization
    - Trade performance
    - Error rates
    - Custom metrics
    """
    
    def __init__(
        self,
        thresholds: Optional[PerformanceThresholds] = None,
        check_interval: float = 5.0,
        persist_path: Optional[str] = None
    ):
        self.thresholds = thresholds or PerformanceThresholds()
        self.check_interval = check_interval
        self.persist_path = Path(persist_path) if persist_path else None
        
        # Components
        self.metrics = MetricsCollector()
        self.resources = ResourceMonitor()
        self.trades = TradeTracker()
        self.alerts = AlertManager()
        
        # State
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time = datetime.utcnow()
        
        # Error tracking
        self._error_count = 0
        self._request_count = 0
    
    async def start(self):
        """Start the monitoring loop."""
        if self._running:
            return
        
        self._running = True
        self._start_time = datetime.utcnow()
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")
    
    async def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self.persist_path:
            self._persist_metrics()
        
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_metrics()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    async def _check_metrics(self):
        """Check all metrics and trigger alerts if needed."""
        # Resource metrics
        resources = self.resources.get_all_metrics()
        
        for name, value in resources.items():
            self.metrics.record(f"resource.{name}", value)
        
        # Check CPU
        if resources['cpu_percent'] >= self.thresholds.cpu_critical:
            self.alerts.trigger(
                AlertLevel.CRITICAL,
                f"CPU usage critical: {resources['cpu_percent']:.1f}%",
                "cpu_percent",
                resources['cpu_percent'],
                self.thresholds.cpu_critical
            )
        elif resources['cpu_percent'] >= self.thresholds.cpu_warning:
            self.alerts.trigger(
                AlertLevel.WARNING,
                f"CPU usage high: {resources['cpu_percent']:.1f}%",
                "cpu_percent",
                resources['cpu_percent'],
                self.thresholds.cpu_warning
            )
        
        # Check memory
        if resources['memory_percent'] >= self.thresholds.memory_critical:
            self.alerts.trigger(
                AlertLevel.CRITICAL,
                f"Memory usage critical: {resources['memory_percent']:.1f}%",
                "memory_percent",
                resources['memory_percent'],
                self.thresholds.memory_critical
            )
        elif resources['memory_percent'] >= self.thresholds.memory_warning:
            self.alerts.trigger(
                AlertLevel.WARNING,
                f"Memory usage high: {resources['memory_percent']:.1f}%",
                "memory_percent",
                resources['memory_percent'],
                self.thresholds.memory_warning
            )
        
        # Check consecutive losses
        if self.trades.consecutive_losses >= self.thresholds.max_consecutive_losses:
            self.alerts.trigger(
                AlertLevel.CRITICAL,
                f"Consecutive losses: {self.trades.consecutive_losses}",
                "consecutive_losses",
                self.trades.consecutive_losses,
                self.thresholds.max_consecutive_losses
            )
        
        # Check drawdown
        if self.trades.max_drawdown * 100 >= self.thresholds.max_drawdown_percent:
            self.alerts.trigger(
                AlertLevel.EMERGENCY,
                f"Max drawdown exceeded: {self.trades.max_drawdown * 100:.1f}%",
                "max_drawdown",
                self.trades.max_drawdown * 100,
                self.thresholds.max_drawdown_percent
            )
        
        # Check error rate
        if self._request_count > 0:
            error_rate = self._error_count / self._request_count
            self.metrics.record("error_rate", error_rate)
            
            if error_rate >= self.thresholds.error_rate_critical:
                self.alerts.trigger(
                    AlertLevel.CRITICAL,
                    f"Error rate critical: {error_rate * 100:.2f}%",
                    "error_rate",
                    error_rate,
                    self.thresholds.error_rate_critical
                )
    
    def record_latency(self, operation: str, latency_seconds: float):
        """Record operation latency."""
        self.metrics.record(f"latency.{operation}", latency_seconds)
        
        # Check thresholds
        if 'order' in operation.lower():
            if latency_seconds >= self.thresholds.order_latency_critical:
                self.alerts.trigger(
                    AlertLevel.CRITICAL,
                    f"Order latency critical: {latency_seconds * 1000:.0f}ms",
                    f"latency.{operation}",
                    latency_seconds,
                    self.thresholds.order_latency_critical
                )
            elif latency_seconds >= self.thresholds.order_latency_warning:
                self.alerts.trigger(
                    AlertLevel.WARNING,
                    f"Order latency high: {latency_seconds * 1000:.0f}ms",
                    f"latency.{operation}",
                    latency_seconds,
                    self.thresholds.order_latency_warning
                )
    
    def record_trade(
        self,
        symbol: str,
        direction: str,
        profit: float,
        pips: float = 0.0,
        duration_seconds: float = 0.0
    ):
        """Record a completed trade."""
        self.trades.record_trade(
            symbol=symbol,
            direction=direction,
            profit=profit,
            pips=pips,
            duration_seconds=duration_seconds
        )
        
        self.metrics.record("trade.profit", profit, {'symbol': symbol})
        self.metrics.record("trade.pips", pips, {'symbol': symbol})
    
    def record_error(self, error_type: str = "general"):
        """Record an error occurrence."""
        self._error_count += 1
        self.metrics.record(f"error.{error_type}", 1)
    
    def record_request(self):
        """Record a request (for error rate calculation)."""
        self._request_count += 1
    
    def record_custom(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric."""
        self.metrics.record(f"custom.{name}", value, tags)
    
    def get_report(self) -> Dict[str, Any]:
        """Get a comprehensive performance report."""
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime,
            'resources': self.resources.get_all_metrics(),
            'trade_metrics': {
                'total_trades': len(self.trades.trades),
                'total_pnl': self.trades.total_pnl,
                'daily_pnl': self.trades.daily_pnl,
                'win_rate': self.trades.get_win_rate(),
                'profit_factor': self.trades.get_profit_factor(),
                'average_trade': self.trades.get_average_trade(),
                'consecutive_losses': self.trades.consecutive_losses,
                'max_drawdown': self.trades.max_drawdown
            },
            'latency': {
                'order_avg_ms': (self.metrics.get_average('latency.order_execution') or 0) * 1000,
                'order_p99_ms': (self.metrics.get_percentile('latency.order_execution', 99) or 0) * 1000,
                'data_avg_ms': (self.metrics.get_average('latency.data_fetch') or 0) * 1000
            },
            'errors': {
                'total_errors': self._error_count,
                'total_requests': self._request_count,
                'error_rate': self._error_count / max(self._request_count, 1)
            },
            'alerts': {
                'total': len(self.alerts.alerts),
                'recent': [
                    {
                        'level': a.level.value,
                        'message': a.message,
                        'timestamp': a.timestamp.isoformat()
                    }
                    for a in self.alerts.get_recent(5)
                ]
            }
        }
    
    def _persist_metrics(self):
        """Persist metrics to disk."""
        if not self.persist_path:
            return
        try:
        
            self.persist_path.mkdir(parents=True, exist_ok=True)
            report_file = self.persist_path / f"metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(self.get_report(), f, indent=2, default=str)
            
            logger.info(f"Metrics persisted to {report_file}")
        except Exception as e:
            logger.error(f"Failed to persist metrics: {e}")


# Singleton instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


async def start_monitoring(
    thresholds: Optional[PerformanceThresholds] = None,
    check_interval: float = 5.0
) -> PerformanceMonitor:
    """Start the global performance monitor."""
    global _monitor
    _monitor = PerformanceMonitor(thresholds=thresholds, check_interval=check_interval)
    await _monitor.start()
    return _monitor


__all__ = [
    'PerformanceMonitor',
    'PerformanceThresholds',
    'AlertLevel',
    'Alert',
    'MetricType',
    'get_monitor',
    'start_monitoring',
]
