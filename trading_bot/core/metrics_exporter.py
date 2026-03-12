"""
Metrics Export System
Prometheus-compatible metrics export for monitoring
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric type"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Metric definition"""
    name: str
    metric_type: MetricType
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: float = field(default_factory=time.time)


class MetricsRegistry:
    """
    Metrics Registry
    
    Collects and exports metrics in Prometheus format.
    Thread-safe metric collection.
    """
    
    def __init__(self, namespace: str = "trading_bot"):
        """
        Initialize metrics registry
        
        Args:
            namespace: Metric namespace prefix
        """
        try:
            self.namespace = namespace
            self._metrics: Dict[str, Metric] = {}
            self._counters: Dict[str, float] = defaultdict(float)
            self._gauges: Dict[str, float] = {}
            self._histograms: Dict[str, List[float]] = defaultdict(list)
            self._lock = threading.RLock()
        
            # Register default metrics
            self._register_default_metrics()
        
            logger.info(f"MetricsRegistry initialized with namespace: {namespace}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _register_default_metrics(self):
        """Register default trading bot metrics"""
        # Trading metrics
        try:
            self.register_counter(
                "trades_total",
                "Total number of trades executed",
                labels={"status": ""}
            )
            self.register_counter(
                "orders_total",
                "Total number of orders submitted",
                labels={"type": "", "status": ""}
            )
            self.register_gauge(
                "positions_open",
                "Number of currently open positions"
            )
            self.register_gauge(
                "account_equity",
                "Current account equity in USD"
            )
            self.register_gauge(
                "unrealized_pnl",
                "Unrealized profit/loss"
            )
            self.register_gauge(
                "realized_pnl_today",
                "Realized profit/loss today"
            )
            self.register_gauge(
                "drawdown_percent",
                "Current drawdown percentage"
            )
        
            # System metrics
            self.register_gauge(
                "system_health_score",
                "Overall system health score (0-100)"
            )
            self.register_counter(
                "errors_total",
                "Total number of errors",
                labels={"severity": ""}
            )
            self.register_gauge(
                "api_rate_limit_remaining",
                "Remaining API calls before rate limit",
                labels={"api": ""}
            )
        
            # Performance metrics
            self.register_histogram(
                "order_execution_seconds",
                "Order execution time in seconds"
            )
            self.register_histogram(
                "signal_generation_seconds",
                "Signal generation time in seconds"
            )
            self.register_gauge(
                "win_rate_percent",
                "Win rate percentage"
            )
            self.register_gauge(
                "profit_factor",
                "Profit factor (gross profit / gross loss)"
            )
        except Exception as e:
            logger.error(f"Error in _register_default_metrics: {e}")
            raise
    
    def register_counter(
        self,
        name: str,
        help_text: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Register a counter metric"""
        try:
            metric_name = self._format_name(name)
        
            with self._lock:
                self._metrics[metric_name] = Metric(
                    name=metric_name,
                    metric_type=MetricType.COUNTER,
                    help_text=help_text,
                    labels=labels or {}
                )
        except Exception as e:
            logger.error(f"Error in register_counter: {e}")
            raise
    
    def register_gauge(
        self,
        name: str,
        help_text: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Register a gauge metric"""
        try:
            metric_name = self._format_name(name)
        
            with self._lock:
                self._metrics[metric_name] = Metric(
                    name=metric_name,
                    metric_type=MetricType.GAUGE,
                    help_text=help_text,
                    labels=labels or {}
                )
        except Exception as e:
            logger.error(f"Error in register_gauge: {e}")
            raise
    
    def register_histogram(
        self,
        name: str,
        help_text: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Register a histogram metric"""
        try:
            metric_name = self._format_name(name)
        
            with self._lock:
                self._metrics[metric_name] = Metric(
                    name=metric_name,
                    metric_type=MetricType.HISTOGRAM,
                    help_text=help_text,
                    labels=labels or {}
                )
        except Exception as e:
            logger.error(f"Error in register_histogram: {e}")
            raise
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter"""
        try:
            metric_name = self._format_name(name)
            label_key = self._format_labels(labels or {})
            key = f"{metric_name}{label_key}"
        
            with self._lock:
                self._counters[key] += value
        except Exception as e:
            logger.error(f"Error in increment_counter: {e}")
            raise
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        try:
            metric_name = self._format_name(name)
            label_key = self._format_labels(labels or {})
            key = f"{metric_name}{label_key}"
        
            with self._lock:
                self._gauges[key] = value
        except Exception as e:
            logger.error(f"Error in set_gauge: {e}")
            raise
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add observation to histogram"""
        try:
            metric_name = self._format_name(name)
            label_key = self._format_labels(labels or {})
            key = f"{metric_name}{label_key}"
        
            with self._lock:
                self._histograms[key].append(value)
            
                # Keep only last 1000 observations
                if len(self._histograms[key]) > 1000:
                    self._histograms[key] = self._histograms[key][-1000:]
        except Exception as e:
            logger.error(f"Error in observe_histogram: {e}")
            raise
    
    def get_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format
        
        Returns:
            Metrics in Prometheus exposition format
        """
        try:
            lines = []
        
            with self._lock:
                # Export counters
                for key, value in self._counters.items():
                    metric_name = key.split('{')[0]
                    if metric_name in self._metrics:
                        metric = self._metrics[metric_name]
                        lines.append(f"# HELP {metric_name} {metric.help_text}")
                        lines.append(f"# TYPE {metric_name} counter")
                    lines.append(f"{key} {value}")
            
                # Export gauges
                for key, value in self._gauges.items():
                    metric_name = key.split('{')[0]
                    if metric_name in self._metrics:
                        metric = self._metrics[metric_name]
                        lines.append(f"# HELP {metric_name} {metric.help_text}")
                        lines.append(f"# TYPE {metric_name} gauge")
                    lines.append(f"{key} {value}")
            
                # Export histograms
                for key, observations in self._histograms.items():
                    if not observations:
                        continue
                
                    metric_name = key.split('{')[0]
                    if metric_name in self._metrics:
                        metric = self._metrics[metric_name]
                        lines.append(f"# HELP {metric_name} {metric.help_text}")
                        lines.append(f"# TYPE {metric_name} histogram")
                
                    # Calculate histogram buckets
                    sorted_obs = sorted(observations)
                    count = len(sorted_obs)
                    total = sum(sorted_obs)
                
                    # Standard buckets
                    buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                
                    for bucket in buckets:
                        bucket_count = sum(1 for v in sorted_obs if v <= bucket)
                        lines.append(f'{key.replace("}", f",le=\"{bucket}\"}}")} {bucket_count}')
                
                    lines.append(f'{key.replace("}", ",le=\"+Inf\"}}")} {count}')
                    lines.append(f"{key}_sum {total}")
                    lines.append(f"{key}_count {count}")
        
            return '\n'.join(lines) + '\n'
        except Exception as e:
            logger.error(f"Error in get_prometheus_format: {e}")
            raise
    
    def get_json_format(self) -> Dict[str, Any]:
        """
        Export metrics in JSON format
        
        Returns:
            Metrics as JSON dictionary
        """
        try:
            result = {
                'timestamp': datetime.now().isoformat(),
                'namespace': self.namespace,
                'counters': {},
                'gauges': {},
                'histograms': {}
            }
        
            with self._lock:
                result['counters'] = dict(self._counters)
                result['gauges'] = dict(self._gauges)
            
                # Calculate histogram statistics
                for key, observations in self._histograms.items():
                    if observations:
                        sorted_obs = sorted(observations)
                        count = len(sorted_obs)
                    
                        result['histograms'][key] = {
                            'count': count,
                            'sum': sum(sorted_obs),
                            'min': sorted_obs[0],
                            'max': sorted_obs[-1],
                            'mean': sum(sorted_obs) / count,
                            'p50': sorted_obs[int(count * 0.5)],
                            'p95': sorted_obs[int(count * 0.95)],
                            'p99': sorted_obs[int(count * 0.99)]
                        }
        
            return result
        except Exception as e:
            logger.error(f"Error in get_json_format: {e}")
            raise
    
    def _format_name(self, name: str) -> str:
        """Format metric name with namespace"""
        return f"{self.namespace}_{name}"
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for metric key"""
        try:
            if not labels:
                return ""
        
            label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
            return '{' + ','.join(label_pairs) + '}'
        except Exception as e:
            logger.error(f"Error in _format_labels: {e}")
            raise
    
    def reset_counters(self):
        """Reset all counters (useful for testing)"""
        try:
            with self._lock:
                self._counters.clear()
        except Exception as e:
            logger.error(f"Error in reset_counters: {e}")
            raise
    
    def get_metric_names(self) -> List[str]:
        """Get list of registered metric names"""
        try:
            with self._lock:
                return list(self._metrics.keys())
        except Exception as e:
            logger.error(f"Error in get_metric_names: {e}")
            raise


class MetricsCollector:
    """
    Metrics Collector
    
    High-level interface for collecting trading bot metrics.
    """
    
    def __init__(self, registry: Optional[MetricsRegistry] = None):
        """
        Initialize metrics collector
        
        Args:
            registry: Metrics registry (creates new if None)
        """
        try:
            self.registry = registry or MetricsRegistry()
            self.start_time = time.time()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade(self, status: str, pnl: float = 0.0):
        """Record a trade"""
        try:
            self.registry.increment_counter("trades_total", labels={"status": status})
        
            if status == "closed":
                if pnl > 0:
                    self.registry.increment_counter("winning_trades_total")
                else:
                    self.registry.increment_counter("losing_trades_total")
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def record_order(self, order_type: str, status: str):
        """Record an order"""
        try:
            self.registry.increment_counter(
                "orders_total",
                labels={"type": order_type, "status": status}
            )
        except Exception as e:
            logger.error(f"Error in record_order: {e}")
            raise
    
    def update_positions(self, count: int):
        """Update open positions count"""
        try:
            self.registry.set_gauge("positions_open", count)
        except Exception as e:
            logger.error(f"Error in update_positions: {e}")
            raise
    
    def update_account(
        self,
        equity: float,
        unrealized_pnl: float,
        realized_pnl_today: float,
        drawdown_percent: float
    ):
        """Update account metrics"""
        try:
            self.registry.set_gauge("account_equity", equity)
            self.registry.set_gauge("unrealized_pnl", unrealized_pnl)
            self.registry.set_gauge("realized_pnl_today", realized_pnl_today)
            self.registry.set_gauge("drawdown_percent", drawdown_percent)
        except Exception as e:
            logger.error(f"Error in update_account: {e}")
            raise
    
    def update_performance(self, win_rate: float, profit_factor: float):
        """Update performance metrics"""
        try:
            self.registry.set_gauge("win_rate_percent", win_rate)
            self.registry.set_gauge("profit_factor", profit_factor)
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise
    
    def record_execution_time(self, seconds: float):
        """Record order execution time"""
        try:
            self.registry.observe_histogram("order_execution_seconds", seconds)
        except Exception as e:
            logger.error(f"Error in record_execution_time: {e}")
            raise
    
    def record_signal_time(self, seconds: float):
        """Record signal generation time"""
        try:
            self.registry.observe_histogram("signal_generation_seconds", seconds)
        except Exception as e:
            logger.error(f"Error in record_signal_time: {e}")
            raise
    
    def record_error(self, severity: str = "error"):
        """Record an error"""
        try:
            self.registry.increment_counter("errors_total", labels={"severity": severity})
        except Exception as e:
            logger.error(f"Error in record_error: {e}")
            raise
    
    def update_health(self, score: float):
        """Update system health score (0-100)"""
        try:
            self.registry.set_gauge("system_health_score", score)
        except Exception as e:
            logger.error(f"Error in update_health: {e}")
            raise
    
    def update_rate_limit(self, api: str, remaining: int):
        """Update API rate limit remaining"""
        try:
            self.registry.set_gauge("api_rate_limit_remaining", remaining, labels={"api": api})
        except Exception as e:
            logger.error(f"Error in update_rate_limit: {e}")
            raise
    
    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time


# Singleton instances
_metrics_registry: Optional[MetricsRegistry] = None
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_registry() -> MetricsRegistry:
    """Get or create metrics registry singleton"""
    try:
        global _metrics_registry
    
        if _metrics_registry is None:
            _metrics_registry = MetricsRegistry()
    
        return _metrics_registry
    except Exception as e:
        logger.error(f"Error in get_metrics_registry: {e}")
        raise


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector singleton"""
    try:
        global _metrics_collector
    
        if _metrics_collector is None:
            _metrics_collector = MetricsCollector(get_metrics_registry())
    
        return _metrics_collector
    except Exception as e:
        logger.error(f"Error in get_metrics_collector: {e}")
        raise


def start_metrics_server(port: int = 9090):
    """
    Start HTTP server for metrics export
    
    Args:
        port: HTTP port to listen on
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                if self.path == '/metrics':
                    registry = get_metrics_registry()
                    metrics = registry.get_prometheus_format()
                
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; version=0.0.4')
                    self.end_headers()
                    self.wfile.write(metrics.encode())
            
                elif self.path == '/metrics/json':
                    registry = get_metrics_registry()
                    import json
                    metrics = json.dumps(registry.get_json_format(), indent=2)
                
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(metrics.encode())
            
                else:
                    self.send_response(404)
                    self.end_headers()
        
                # Suppress request logging
                pass
            except Exception as e:
                logger.error(f"Error in do_GET: {e}")
                raise
    
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    logger.info(f"Metrics server started on port {port}")
    logger.info(f"Prometheus metrics: http://localhost:{port}/metrics")
    logger.info(f"JSON metrics: http://localhost:{port}/metrics/json")
    
    # Run in separate thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    return server
