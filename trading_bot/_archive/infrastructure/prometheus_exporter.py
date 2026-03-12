"""
from typing import Optional, Set
Prometheus metrics exporter for trading system monitoring
"""

import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("Prometheus client not available. Install with: pip install prometheus-client")
    PROMETHEUS_AVAILABLE = False


class PrometheusExporter:
    """
    Export trading system metrics to Prometheus
    """
    
    def __init__(self, port: int = 8000, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus exporter
        
        Args:
            port: Port to expose metrics on
            registry: Custom registry (optional)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available - metrics will not be exported")
            self.enabled = False
            return
        
        self.enabled = True
        self.port = port
        self.registry = registry or CollectorRegistry()
        
        # Trading metrics
        self.trades_total = Counter(
            'trades_total',
            'Total number of trades executed',
            ['symbol', 'direction', 'status'],
            registry=self.registry
        )
        
        self.trade_pnl = Histogram(
            'trade_pnl',
            'Trade profit/loss distribution',
            ['symbol'],
            buckets=(-1000, -500, -100, -50, -10, 0, 10, 50, 100, 500, 1000),
            registry=self.registry
        )
        
        self.portfolio_value = Gauge(
            'portfolio_value',
            'Current portfolio value',
            registry=self.registry
        )
        
        self.portfolio_drawdown = Gauge(
            'portfolio_drawdown',
            'Current drawdown percentage',
            registry=self.registry
        )
        
        self.open_positions = Gauge(
            'open_positions',
            'Number of open positions',
            ['symbol'],
            registry=self.registry
        )
        
        # Model metrics
        self.model_latency = Histogram(
            'model_inference_latency_seconds',
            'Model inference latency',
            ['model_name'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
            registry=self.registry
        )
        
        self.model_predictions = Counter(
            'model_predictions_total',
            'Total model predictions',
            ['model_name', 'prediction'],
            registry=self.registry
        )
        
        self.model_confidence = Histogram(
            'model_confidence',
            'Model prediction confidence',
            ['model_name'],
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            registry=self.registry
        )
        
        # Risk metrics
        self.risk_limit_breaches = Counter(
            'risk_limit_breaches_total',
            'Risk limit breaches',
            ['limit_type'],
            registry=self.registry
        )
        
        self.current_risk_exposure = Gauge(
            'current_risk_exposure',
            'Current risk exposure percentage',
            registry=self.registry
        )
        
        # System metrics
        self.system_health = Gauge(
            'system_health_score',
            'Overall system health score (0-100)',
            registry=self.registry
        )
        
        self.data_staleness = Gauge(
            'data_staleness_seconds',
            'Data staleness in seconds',
            ['data_source'],
            registry=self.registry
        )
        
        self.circuit_breaker_status = Gauge(
            'circuit_breaker_status',
            'Circuit breaker status (0=closed, 1=open)',
            ['breaker_name'],
            registry=self.registry
        )
        
        # Execution metrics
        self.order_latency = Histogram(
            'order_execution_latency_seconds',
            'Order execution latency',
            ['order_type'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
            registry=self.registry
        )
        
        self.slippage = Histogram(
            'order_slippage_pips',
            'Order slippage in pips',
            ['symbol'],
            buckets=(0, 0.5, 1, 2, 5, 10, 20, 50),
            registry=self.registry
        )
        
        # Info metrics
        self.system_info = Info(
            'trading_system_info',
            'Trading system information',
            registry=self.registry
        )
        
        logger.info(f"Prometheus exporter initialized on port {port}")
    
    def start(self):
        """Start metrics HTTP server"""
        if not self.enabled:
            logger.warning("Prometheus not available - cannot start server")
            return
        try:
        
            start_http_server(self.port, registry=self.registry)
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    def record_trade(self, symbol: str, direction: str, status: str, pnl: float):
        """Record trade execution"""
        if not self.enabled:
            return
        
        self.trades_total.labels(symbol=symbol, direction=direction, status=status).inc()
        if status == 'closed':
            self.trade_pnl.labels(symbol=symbol).observe(pnl)
    
    def update_portfolio(self, value: float, drawdown: float):
        """Update portfolio metrics"""
        if not self.enabled:
            return
        
        self.portfolio_value.set(value)
        self.portfolio_drawdown.set(drawdown)
    
    def update_positions(self, symbol: str, count: int):
        """Update open positions count"""
        if not self.enabled:
            return
        
        self.open_positions.labels(symbol=symbol).set(count)
    
    def record_model_inference(self, model_name: str, latency: float, prediction: str, confidence: float):
        """Record model inference"""
        if not self.enabled:
            return
        
        self.model_latency.labels(model_name=model_name).observe(latency)
        self.model_predictions.labels(model_name=model_name, prediction=prediction).inc()
        self.model_confidence.labels(model_name=model_name).observe(confidence)
    
    def record_risk_breach(self, limit_type: str):
        """Record risk limit breach"""
        if not self.enabled:
            return
        
        self.risk_limit_breaches.labels(limit_type=limit_type).inc()
    
    def update_risk_exposure(self, exposure: float):
        """Update current risk exposure"""
        if not self.enabled:
            return
        
        self.current_risk_exposure.set(exposure)
    
    def update_system_health(self, score: float):
        """Update system health score"""
        if not self.enabled:
            return
        
        self.system_health.set(score)
    
    def update_data_staleness(self, source: str, staleness: float):
        """Update data staleness"""
        if not self.enabled:
            return
        
        self.data_staleness.labels(data_source=source).set(staleness)
    
    def update_circuit_breaker(self, name: str, is_open: bool):
        """Update circuit breaker status"""
        if not self.enabled:
            return
        
        self.circuit_breaker_status.labels(breaker_name=name).set(1 if is_open else 0)
    
    def record_order_execution(self, order_type: str, latency: float, symbol: str, slippage: float):
        """Record order execution metrics"""
        if not self.enabled:
            return
        
        self.order_latency.labels(order_type=order_type).observe(latency)
        self.slippage.labels(symbol=symbol).observe(slippage)
    
    def set_system_info(self, info: Dict[str, str]):
        """Set system information"""
        if not self.enabled:
            return
        
        self.system_info.info(info)


# Global exporter instance
_exporter: Optional[PrometheusExporter] = None


def get_exporter(port: int = 8000) -> PrometheusExporter:
    """Get or create global Prometheus exporter"""
    global _exporter
    
    if _exporter is None:
        _exporter = PrometheusExporter(port=port)
    
    return _exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if PROMETHEUS_AVAILABLE:
        # Test exporter
        exporter = PrometheusExporter(port=8000)
        exporter.start()
        
        # Set system info
        exporter.set_system_info({
            'version': '2.0.0',
            'environment': 'test',
            'strategy': 'alphaalgo'
        })
        
        # Simulate some metrics
        logger.info("Simulating metrics for 10 seconds...")
        for i in range(10):
            exporter.record_trade('EURUSD', 'BUY', 'closed', 10.5)
            exporter.update_portfolio(100000 + i * 100, 0.02)
            exporter.update_positions('EURUSD', i % 3)
            exporter.record_model_inference('tft', 0.05, 'BUY', 0.85)
            exporter.update_system_health(95.0)
            exporter.record_order_execution('MARKET', 0.02, 'EURUSD', 0.5)
            time.sleep(1)
        
        logger.info(f"\n✅ Metrics available at http://localhost:8000/metrics")
        logger.info("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nStopped")
    else:
        logger.info("❌ Prometheus client not available")
