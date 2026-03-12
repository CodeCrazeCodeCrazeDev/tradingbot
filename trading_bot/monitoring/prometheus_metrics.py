"""
Prometheus metrics integration for real-time monitoring.
Tracks system performance, trading metrics, and health indicators.
"""

import logging
import time
from typing import Dict, Optional
from loguru import logger

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not installed. Install with: pip install prometheus-client")


class PrometheusMetrics:
    """Prometheus metrics collector for trading system."""
    
    def __init__(self, port: int = 8000):
        """
        Initialize Prometheus metrics.
        
        Args:
            port: Port for metrics HTTP server
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available - metrics disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.port = port
        
        # Trading metrics
        self.trades_total = Counter(
            'alphaalgo_trades_total',
            'Total number of trades executed',
            ['symbol', 'direction']
        )
        
        self.trade_pnl = Histogram(
            'alphaalgo_trade_pnl',
            'Trade profit/loss distribution',
            ['symbol'],
            buckets=[-1000, -500, -100, -50, 0, 50, 100, 500, 1000]
        )
        
        self.account_equity = Gauge(
            'alphaalgo_account_equity',
            'Current account equity'
        )
        
        self.open_positions = Gauge(
            'alphaalgo_open_positions',
            'Number of open positions',
            ['symbol']
        )
        
        # Performance metrics
        self.signal_latency = Histogram(
            'alphaalgo_signal_latency_seconds',
            'Time to generate trading signal',
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
        )
        
        self.model_inference_time = Histogram(
            'alphaalgo_model_inference_seconds',
            'Model inference time',
            ['model_type'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
        )
        
        self.indicator_calculation_time = Histogram(
            'alphaalgo_indicator_calc_seconds',
            'Indicator calculation time',
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
        )
        
        # Risk metrics
        self.portfolio_var = Gauge(
            'alphaalgo_portfolio_var',
            'Portfolio Value at Risk',
            ['confidence']
        )
        
        self.max_drawdown = Gauge(
            'alphaalgo_max_drawdown_pct',
            'Maximum drawdown percentage'
        )
        
        self.sharpe_ratio = Gauge(
            'alphaalgo_sharpe_ratio',
            'Current Sharpe ratio'
        )
        
        # System health
        self.validation_failures = Counter(
            'alphaalgo_validation_failures_total',
            'Number of trade validation failures',
            ['reason']
        )
        
        self.api_errors = Counter(
            'alphaalgo_api_errors_total',
            'API error count',
            ['api', 'error_type']
        )
        
        self.memory_usage = Gauge(
            'alphaalgo_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'alphaalgo_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        # Model metrics
        self.model_accuracy = Gauge(
            'alphaalgo_model_accuracy',
            'Model prediction accuracy',
            ['model_type']
        )
        
        self.online_learning_updates = Counter(
            'alphaalgo_online_learning_updates_total',
            'Number of online learning updates'
        )
        
        self.concept_drift_detected = Counter(
            'alphaalgo_concept_drift_total',
            'Number of concept drift detections'
        )
        
        logger.info(f"Prometheus metrics initialized on port {port}")
    
    def start_server(self):
        """Start Prometheus HTTP server."""
        if not self.enabled:
            return
        try:
        
            start_http_server(self.port)
            logger.success(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    def record_trade(self, symbol: str, direction: str, pnl: float):
        """Record trade execution."""
        if not self.enabled:
            return
        
        self.trades_total.labels(symbol=symbol, direction=direction).inc()
        self.trade_pnl.labels(symbol=symbol).observe(pnl)
    
    def update_account_equity(self, equity: float):
        """Update account equity."""
        if not self.enabled:
            return
        
        self.account_equity.set(equity)
    
    def update_open_positions(self, symbol: str, count: int):
        """Update open position count."""
        if not self.enabled:
            return
        
        self.open_positions.labels(symbol=symbol).set(count)
    
    def record_signal_latency(self, latency: float):
        """Record signal generation latency."""
        if not self.enabled:
            return
        
        self.signal_latency.observe(latency)
    
    def record_model_inference(self, model_type: str, duration: float):
        """Record model inference time."""
        if not self.enabled:
            return
        
        self.model_inference_time.labels(model_type=model_type).observe(duration)
    
    def record_indicator_calculation(self, duration: float):
        """Record indicator calculation time."""
        if not self.enabled:
            return
        
        self.indicator_calculation_time.observe(duration)
    
    def update_risk_metrics(self, var_95: float, var_99: float, 
                           max_dd: float, sharpe: float):
        """Update risk metrics."""
        if not self.enabled:
            return
        
        self.portfolio_var.labels(confidence='95').set(abs(var_95))
        self.portfolio_var.labels(confidence='99').set(abs(var_99))
        self.max_drawdown.set(max_dd)
        self.sharpe_ratio.set(sharpe)
    
    def record_validation_failure(self, reason: str):
        """Record validation failure."""
        if not self.enabled:
            return
        
        self.validation_failures.labels(reason=reason).inc()
    
    def record_api_error(self, api: str, error_type: str):
        """Record API error."""
        if not self.enabled:
            return
        
        self.api_errors.labels(api=api, error_type=error_type).inc()
    
    def update_system_resources(self, memory_bytes: int, cpu_percent: float):
        """Update system resource metrics."""
        if not self.enabled:
            return
        
        self.memory_usage.set(memory_bytes)
        self.cpu_usage.set(cpu_percent)
    
    def update_model_accuracy(self, model_type: str, accuracy: float):
        """Update model accuracy."""
        if not self.enabled:
            return
        
        self.model_accuracy.labels(model_type=model_type).set(accuracy)
    
    def record_online_learning_update(self):
        """Record online learning update."""
        if not self.enabled:
            return
        
        self.online_learning_updates.inc()
    
    def record_concept_drift(self):
        """Record concept drift detection."""
        if not self.enabled:
            return
        
        self.concept_drift_detected.inc()


class SystemMonitor:
    """System health and performance monitor."""
    
    def __init__(self, metrics: Optional[PrometheusMetrics] = None):
        self.metrics = metrics or PrometheusMetrics()
        self.start_time = None
        
    def start_monitoring(self):
        """Start monitoring system."""
        self.start_time = time.time()
        
        if self.metrics.enabled:
            self.metrics.start_server()
        
        logger.info("System monitoring started")
    
    def collect_system_metrics(self):
        """Collect and update system metrics."""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.update_system_resources(
                memory_bytes=memory.used,
                cpu_percent=psutil.cpu_percent(interval=1)
            )
            
        except ImportError:
            logger.warning("psutil not installed - system metrics unavailable")
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        if self.start_time is None:
            return 0
        
        return time.time() - self.start_time
