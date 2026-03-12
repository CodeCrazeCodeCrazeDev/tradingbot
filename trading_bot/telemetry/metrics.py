"""
AlphaAlgo Metrics - Performance & System Metrics

This module collects and exposes metrics for monitoring.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import time
import threading
from collections import defaultdict
from typing import Set

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class TradingMetrics:
    """Trading-specific metrics"""
    # Trade counts
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_pnl: float = 0.0
    
    # Performance
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    
    # Positions
    open_positions: int = 0
    total_exposure: float = 0.0
    
    # Orders
    orders_placed: int = 0
    orders_filled: int = 0
    orders_cancelled: int = 0
    orders_rejected: int = 0
    
    # Signals
    signals_generated: int = 0
    signals_executed: int = 0
    signals_rejected: int = 0
    
    # Risk
    daily_loss: float = 0.0
    risk_utilization: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trades': {
                'total': self.total_trades,
                'winning': self.winning_trades,
                'losing': self.losing_trades,
            },
            'pnl': {
                'profit': self.total_profit,
                'loss': self.total_loss,
                'net': self.net_pnl,
            },
            'performance': {
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'max_drawdown': self.max_drawdown,
                'current_drawdown': self.current_drawdown,
            },
            'positions': {
                'open': self.open_positions,
                'exposure': self.total_exposure,
            },
            'orders': {
                'placed': self.orders_placed,
                'filled': self.orders_filled,
                'cancelled': self.orders_cancelled,
                'rejected': self.orders_rejected,
            },
            'signals': {
                'generated': self.signals_generated,
                'executed': self.signals_executed,
                'rejected': self.signals_rejected,
            },
            'risk': {
                'daily_loss': self.daily_loss,
                'utilization': self.risk_utilization,
            },
        }


@dataclass
class SystemMetrics:
    """System-level metrics"""
    # Resource usage
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    
    # Latency
    data_latency_ms: float = 0.0
    signal_latency_ms: float = 0.0
    execution_latency_ms: float = 0.0
    
    # Throughput
    ticks_per_second: float = 0.0
    signals_per_minute: float = 0.0
    
    # Connections
    broker_connected: bool = False
    data_feed_connected: bool = False
    
    # Uptime
    uptime_seconds: float = 0.0
    
    # Errors
    error_count: int = 0
    warning_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resources': {
                'cpu_percent': self.cpu_percent,
                'memory_percent': self.memory_percent,
                'memory_mb': self.memory_mb,
            },
            'latency': {
                'data_ms': self.data_latency_ms,
                'signal_ms': self.signal_latency_ms,
                'execution_ms': self.execution_latency_ms,
            },
            'throughput': {
                'ticks_per_second': self.ticks_per_second,
                'signals_per_minute': self.signals_per_minute,
            },
            'connections': {
                'broker': self.broker_connected,
                'data_feed': self.data_feed_connected,
            },
            'uptime_seconds': self.uptime_seconds,
            'errors': {
                'error_count': self.error_count,
                'warning_count': self.warning_count,
            },
        }


class MetricsCollector:
    """
    Central metrics collector.
    
    Collects and aggregates metrics from all components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Metrics storage
        self._trading = TradingMetrics()
        self._system = SystemMetrics()
        
        # Counters
        self._counters: Dict[str, int] = defaultdict(int)
        
        # Gauges
        self._gauges: Dict[str, float] = defaultdict(float)
        
        # Histograms (store recent values)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._histogram_max_size = 1000
        
        # Timing
        self._start_time = datetime.now()
        self._last_update = datetime.now()
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info("MetricsCollector initialized")
    
    # =========================================================================
    # COUNTER OPERATIONS
    # =========================================================================
    
    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter"""
        with self._lock:
            self._counters[name] += value
    
    def get_counter(self, name: str) -> int:
        """Get counter value"""
        return self._counters.get(name, 0)
    
    # =========================================================================
    # GAUGE OPERATIONS
    # =========================================================================
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value"""
        with self._lock:
            self._gauges[name] = value
    
    def get_gauge(self, name: str) -> float:
        """Get gauge value"""
        return self._gauges.get(name, 0.0)
    
    # =========================================================================
    # HISTOGRAM OPERATIONS
    # =========================================================================
    
    def observe(self, name: str, value: float) -> None:
        """Add observation to histogram"""
        with self._lock:
            self._histograms[name].append(value)
            if len(self._histograms[name]) > self._histogram_max_size:
                self._histograms[name] = self._histograms[name][-self._histogram_max_size:]
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self._histograms.get(name, [])
        if not values:
            return {'count': 0, 'min': 0, 'max': 0, 'avg': 0, 'p50': 0, 'p95': 0, 'p99': 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            'count': count,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'avg': sum(sorted_values) / count,
            'p50': sorted_values[int(count * 0.5)],
            'p95': sorted_values[int(count * 0.95)] if count >= 20 else sorted_values[-1],
            'p99': sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1],
        }
    
    # =========================================================================
    # TRADING METRICS
    # =========================================================================
    
    def record_trade(self, is_winner: bool, pnl: float) -> None:
        """Record a completed trade"""
        with self._lock:
            self._trading.total_trades += 1
            if is_winner:
                self._trading.winning_trades += 1
                self._trading.total_profit += pnl
            else:
                self._trading.losing_trades += 1
                self._trading.total_loss += abs(pnl)
            
            self._trading.net_pnl = self._trading.total_profit - self._trading.total_loss
            
            if self._trading.total_trades > 0:
                self._trading.win_rate = self._trading.winning_trades / self._trading.total_trades
            
            if self._trading.total_loss > 0:
                self._trading.profit_factor = self._trading.total_profit / self._trading.total_loss
    
    def record_order(self, status: str) -> None:
        """Record an order event"""
        with self._lock:
            self._trading.orders_placed += 1
            if status == 'filled':
                self._trading.orders_filled += 1
            elif status == 'cancelled':
                self._trading.orders_cancelled += 1
            elif status == 'rejected':
                self._trading.orders_rejected += 1
    
    def record_signal(self, executed: bool) -> None:
        """Record a signal event"""
        with self._lock:
            self._trading.signals_generated += 1
            if executed:
                self._trading.signals_executed += 1
            else:
                self._trading.signals_rejected += 1
    
    def update_positions(self, count: int, exposure: float) -> None:
        """Update position metrics"""
        with self._lock:
            self._trading.open_positions = count
            self._trading.total_exposure = exposure
    
    def update_drawdown(self, current: float, maximum: float) -> None:
        """Update drawdown metrics"""
        with self._lock:
            self._trading.current_drawdown = current
            self._trading.max_drawdown = max(self._trading.max_drawdown, maximum)
    
    def update_risk(self, daily_loss: float, utilization: float) -> None:
        """Update risk metrics"""
        with self._lock:
            self._trading.daily_loss = daily_loss
            self._trading.risk_utilization = utilization
    
    # =========================================================================
    # SYSTEM METRICS
    # =========================================================================
    
    def update_system_resources(self, cpu: float, memory: float, memory_mb: float) -> None:
        """Update system resource metrics"""
        with self._lock:
            self._system.cpu_percent = cpu
            self._system.memory_percent = memory
            self._system.memory_mb = memory_mb
    
    def update_latency(self, data_ms: float = None, signal_ms: float = None, execution_ms: float = None) -> None:
        """Update latency metrics"""
        with self._lock:
            if data_ms is not None:
                self._system.data_latency_ms = data_ms
                self.observe('latency.data', data_ms)
            if signal_ms is not None:
                self._system.signal_latency_ms = signal_ms
                self.observe('latency.signal', signal_ms)
            if execution_ms is not None:
                self._system.execution_latency_ms = execution_ms
                self.observe('latency.execution', execution_ms)
    
    def update_connections(self, broker: bool = None, data_feed: bool = None) -> None:
        """Update connection status"""
        with self._lock:
            if broker is not None:
                self._system.broker_connected = broker
            if data_feed is not None:
                self._system.data_feed_connected = data_feed
    
    def record_error(self) -> None:
        """Record an error"""
        with self._lock:
            self._system.error_count += 1
    
    def record_warning(self) -> None:
        """Record a warning"""
        with self._lock:
            self._system.warning_count += 1
    
    # =========================================================================
    # GETTERS
    # =========================================================================
    
    def get_trading_metrics(self) -> Dict[str, Any]:
        """Get trading metrics"""
        return self._trading.to_dict()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        with self._lock:
            self._system.uptime_seconds = (datetime.now() - self._start_time).total_seconds()
        return self._system.to_dict()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'trading': self.get_trading_metrics(),
            'system': self.get_system_metrics(),
            'counters': dict(self._counters),
            'gauges': dict(self._gauges),
        }
    
    def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus format"""
        lines = []
        
        # Trading metrics
        lines.append(f"alphaalgo_trades_total {self._trading.total_trades}")
        lines.append(f"alphaalgo_trades_winning {self._trading.winning_trades}")
        lines.append(f"alphaalgo_trades_losing {self._trading.losing_trades}")
        lines.append(f"alphaalgo_pnl_net {self._trading.net_pnl}")
        lines.append(f"alphaalgo_win_rate {self._trading.win_rate}")
        lines.append(f"alphaalgo_profit_factor {self._trading.profit_factor}")
        lines.append(f"alphaalgo_drawdown_current {self._trading.current_drawdown}")
        lines.append(f"alphaalgo_drawdown_max {self._trading.max_drawdown}")
        lines.append(f"alphaalgo_positions_open {self._trading.open_positions}")
        lines.append(f"alphaalgo_exposure_total {self._trading.total_exposure}")
        
        # System metrics
        lines.append(f"alphaalgo_cpu_percent {self._system.cpu_percent}")
        lines.append(f"alphaalgo_memory_percent {self._system.memory_percent}")
        lines.append(f"alphaalgo_latency_data_ms {self._system.data_latency_ms}")
        lines.append(f"alphaalgo_latency_execution_ms {self._system.execution_latency_ms}")
        lines.append(f"alphaalgo_uptime_seconds {self._system.uptime_seconds}")
        lines.append(f"alphaalgo_errors_total {self._system.error_count}")
        
        # Custom counters
        for name, value in self._counters.items():
            safe_name = name.replace('.', '_').replace('-', '_')
            lines.append(f"alphaalgo_{safe_name} {value}")
        
        return "\n".join(lines)


# =============================================================================
# SINGLETON
# =============================================================================

_metrics_instance: Optional[MetricsCollector] = None


def get_metrics_collector(config: Optional[Dict[str, Any]] = None) -> MetricsCollector:
    """Get the singleton metrics collector"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector(config)
    return _metrics_instance


# =============================================================================
# TIMING DECORATOR
# =============================================================================

def timed(metric_name: str):
    """Decorator to time function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.time() - start) * 1000
                get_metrics_collector().observe(metric_name, elapsed_ms)
        return wrapper
    return decorator
