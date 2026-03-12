"""
Prometheus Metrics Exporter for Trading Bot

Exports real-time trading metrics for Prometheus/Grafana monitoring.
"""

import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TradingMetricsExporter:
    """
    Export trading metrics to Prometheus
    
    Metrics:
    - Total trades
    - Win rate
    - PnL
    - Sharpe ratio
    - Drawdown
    - Latency
    - Error rate
    """
    
    def __init__(self, port: int = 9090):
        """
        Args:
            port: Port for Prometheus metrics endpoint
        """
        self.port = port
        self.metrics = {}
        
        try:
            from prometheus_client import Counter, Gauge, Histogram, start_http_server
            
            # Counters (monotonically increasing)
            self.total_trades = Counter('trading_total_trades', 'Total number of trades')
            self.winning_trades = Counter('trading_winning_trades', 'Number of winning trades')
            self.losing_trades = Counter('trading_losing_trades', 'Number of losing trades')
            self.errors = Counter('trading_errors_total', 'Total errors', ['error_type'])
            
            # Gauges (can go up or down)
            self.current_pnl = Gauge('trading_current_pnl', 'Current PnL in USD')
            self.current_equity = Gauge('trading_current_equity', 'Current account equity')
            self.open_positions = Gauge('trading_open_positions', 'Number of open positions')
            self.win_rate = Gauge('trading_win_rate', 'Win rate percentage')
            self.sharpe_ratio = Gauge('trading_sharpe_ratio', 'Sharpe ratio')
            self.max_drawdown = Gauge('trading_max_drawdown', 'Maximum drawdown percentage')
            self.current_drawdown = Gauge('trading_current_drawdown', 'Current drawdown percentage')
            
            # Histograms (distributions)
            self.trade_pnl = Histogram('trading_trade_pnl', 'Trade PnL distribution', 
                                       buckets=[-100, -50, -25, -10, 0, 10, 25, 50, 100, 200])
            self.trade_duration = Histogram('trading_trade_duration_seconds', 'Trade duration',
                                           buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800])
            self.latency = Histogram('trading_latency_ms', 'Order execution latency',
                                    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000])
            
            # Start HTTP server for Prometheus
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
            
            self.prometheus_available = True
            
        except ImportError:
            logger.warning("prometheus_client not installed. Metrics will be logged only.")
            self.prometheus_available = False
    
    def record_trade(
        self,
        pnl: float,
        duration_seconds: float,
        is_win: bool
    ):
        """Record a completed trade"""
        if self.prometheus_available:
            self.total_trades.inc()
            
            if is_win:
                self.winning_trades.inc()
            else:
                self.losing_trades.inc()
            
            self.trade_pnl.observe(pnl)
            self.trade_duration.observe(duration_seconds)
        
        logger.info(f"Trade recorded: PnL ${pnl:.2f}, Duration {duration_seconds:.0f}s, Win: {is_win}")
    
    def update_pnl(self, pnl: float):
        """Update current PnL"""
        if self.prometheus_available:
            self.current_pnl.set(pnl)
    
    def update_equity(self, equity: float):
        """Update current equity"""
        if self.prometheus_available:
            self.current_equity.set(equity)
    
    def update_positions(self, count: int):
        """Update number of open positions"""
        if self.prometheus_available:
            self.open_positions.set(count)
    
    def update_win_rate(self, win_rate: float):
        """Update win rate (0-100)"""
        if self.prometheus_available:
            self.win_rate.set(win_rate)
    
    def update_sharpe_ratio(self, sharpe: float):
        """Update Sharpe ratio"""
        if self.prometheus_available:
            self.sharpe_ratio.set(sharpe)
    
    def update_drawdown(self, current: float, maximum: float):
        """Update drawdown metrics"""
        if self.prometheus_available:
            self.current_drawdown.set(current)
            self.max_drawdown.set(maximum)
    
    def record_latency(self, latency_ms: float):
        """Record order execution latency"""
        if self.prometheus_available:
            self.latency.observe(latency_ms)
    
    def record_error(self, error_type: str):
        """Record an error"""
        if self.prometheus_available:
            self.errors.labels(error_type=error_type).inc()
        
        logger.error(f"Error recorded: {error_type}")


class GrafanaDashboardConfig:
    """
    Generate Grafana dashboard configuration
    
    Creates JSON config for importing into Grafana
    """
    
    @staticmethod
    def generate_dashboard() -> Dict:
        """Generate Grafana dashboard JSON"""
        return {
            "dashboard": {
                "title": "Trading Bot Metrics",
                "panels": [
                    {
                        "title": "Current PnL",
                        "type": "stat",
                        "targets": [{
                            "expr": "trading_current_pnl"
                        }]
                    },
                    {
                        "title": "Win Rate",
                        "type": "gauge",
                        "targets": [{
                            "expr": "trading_win_rate"
                        }]
                    },
                    {
                        "title": "Sharpe Ratio",
                        "type": "stat",
                        "targets": [{
                            "expr": "trading_sharpe_ratio"
                        }]
                    },
                    {
                        "title": "Total Trades",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(trading_total_trades[5m])"
                        }]
                    },
                    {
                        "title": "Trade PnL Distribution",
                        "type": "heatmap",
                        "targets": [{
                            "expr": "trading_trade_pnl"
                        }]
                    },
                    {
                        "title": "Execution Latency",
                        "type": "graph",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, trading_latency_ms)"
                        }]
                    },
                    {
                        "title": "Drawdown",
                        "type": "graph",
                        "targets": [
                            {"expr": "trading_current_drawdown", "legendFormat": "Current"},
                            {"expr": "trading_max_drawdown", "legendFormat": "Maximum"}
                        ]
                    },
                    {
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(trading_errors_total[5m])"
                        }]
                    }
                ]
            }
        }
    
    @staticmethod
    def save_dashboard(filename: str = "grafana_dashboard.json"):
        """Save dashboard config to file"""
        import json
        
        config = GrafanaDashboardConfig.generate_dashboard()
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Grafana dashboard config saved to {filename}")


class AlertManager:
    """
    Alert manager for critical events
    
    Sends alerts when thresholds are exceeded
    """
    
    def __init__(
        self,
        max_drawdown_threshold: float = 10.0,
        min_win_rate_threshold: float = 45.0,
        max_latency_threshold: float = 500.0
    ):
        self.max_drawdown_threshold = max_drawdown_threshold
        self.min_win_rate_threshold = min_win_rate_threshold
        self.max_latency_threshold = max_latency_threshold
        
        self.alerts_sent = []
    
    def check_drawdown(self, current_drawdown: float):
        """Check if drawdown exceeds threshold"""
        if current_drawdown > self.max_drawdown_threshold:
            self._send_alert(
                'CRITICAL',
                f"Drawdown {current_drawdown:.1f}% exceeds threshold {self.max_drawdown_threshold:.1f}%"
            )
    
    def check_win_rate(self, win_rate: float):
        """Check if win rate below threshold"""
        if win_rate < self.min_win_rate_threshold:
            self._send_alert(
                'WARNING',
                f"Win rate {win_rate:.1f}% below threshold {self.min_win_rate_threshold:.1f}%"
            )
    
    def check_latency(self, latency_ms: float):
        """Check if latency exceeds threshold"""
        if latency_ms > self.max_latency_threshold:
            self._send_alert(
                'WARNING',
                f"Latency {latency_ms:.0f}ms exceeds threshold {self.max_latency_threshold:.0f}ms"
            )
    
    def _send_alert(self, level: str, message: str):
        """Send alert (placeholder for actual implementation)"""
        alert = {
            'timestamp': time.time(),
            'level': level,
            'message': message
        }
        
        self.alerts_sent.append(alert)
        
        logger.warning(f"ALERT [{level}]: {message}")
        
        # In production, send to Slack, email, SMS, etc.


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    logger.info("PROMETHEUS MONITORING DEMO")
    print("="*60)
    
    # Create exporter
    logger.info("\nInitializing metrics exporter...")
    exporter = TradingMetricsExporter(port=9090)
    
    # Simulate some trades
    logger.info("\nSimulating trades...")
    import random
    
    for i in range(10):
        pnl = random.uniform(-50, 100)
        duration = random.uniform(300, 3600)
        is_win = pnl > 0
        
        exporter.record_trade(pnl, duration, is_win)
        time.sleep(0.1)
    
    # Update metrics
    logger.info("\nUpdating metrics...")
    exporter.update_pnl(250.50)
    exporter.update_equity(10250.50)
    exporter.update_positions(3)
    exporter.update_win_rate(65.0)
    exporter.update_sharpe_ratio(1.85)
    exporter.update_drawdown(2.5, 8.3)
    
    # Record latency
    for _ in range(5):
        exporter.record_latency(random.uniform(10, 100))
    
    # Generate Grafana dashboard
    logger.info("\nGenerating Grafana dashboard config...")
    GrafanaDashboardConfig.save_dashboard()
    
    # Test alerts
    logger.info("\nTesting alert manager...")
    alert_mgr = AlertManager()
    alert_mgr.check_drawdown(12.0)  # Should trigger alert
    alert_mgr.check_win_rate(40.0)  # Should trigger alert
    alert_mgr.check_latency(600.0)  # Should trigger alert
    
    logger.info(f"\nAlerts sent: {len(alert_mgr.alerts_sent)}")
    
    print("\n" + "="*60)
    logger.info("MONITORING SYSTEM READY!")
    print("="*60)
    logger.info(f"Metrics available at: http://localhost:9090/metrics")
    logger.info("Import grafana_dashboard.json into Grafana")
    print("="*60)
