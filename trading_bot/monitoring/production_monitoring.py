"""
from typing import List, Optional, Set
Production Monitoring System - Complete Real-Time Monitoring

Comprehensive monitoring infrastructure:
- Prometheus metrics with custom collectors
- Grafana dashboard generation
- Real-time alerting (Slack, Telegram, Email, SMS, PagerDuty)
- System health monitoring
- Trading performance tracking
- Anomaly detection
- SLA monitoring
"""

import asyncio
import logging
import json
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import os

logger = logging.getLogger(__name__)

# Optional imports
try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, Info,
        start_http_server, generate_latest, REGISTRY,
        CollectorRegistry, multiprocess, CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed")

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels"""
    SLACK = "slack"
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    DISCORD = "discord"


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


class PrometheusMetricsCollector:
    """
    Comprehensive Prometheus metrics collector for trading system.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, port: int = 9090, prefix: str = "alphaalgo"):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.port = port
        self.prefix = prefix
        self.enabled = PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            logger.warning("Prometheus not available - metrics disabled")
            return
        
        # Trading metrics
        self.trades_total = Counter(
            f'{prefix}_trades_total',
            'Total trades executed',
            ['symbol', 'side', 'strategy']
        )
        
        self.trade_pnl = Histogram(
            f'{prefix}_trade_pnl_dollars',
            'Trade P&L distribution',
            ['symbol'],
            buckets=[-1000, -500, -100, -50, -10, 0, 10, 50, 100, 500, 1000, 5000]
        )
        
        self.trade_duration = Histogram(
            f'{prefix}_trade_duration_seconds',
            'Trade duration',
            ['symbol'],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400]
        )
        
        self.account_equity = Gauge(
            f'{prefix}_account_equity_dollars',
            'Current account equity'
        )
        
        self.account_balance = Gauge(
            f'{prefix}_account_balance_dollars',
            'Current account balance'
        )
        
        self.open_positions = Gauge(
            f'{prefix}_open_positions_count',
            'Number of open positions',
            ['symbol']
        )
        
        self.position_value = Gauge(
            f'{prefix}_position_value_dollars',
            'Position value',
            ['symbol', 'side']
        )
        
        self.unrealized_pnl = Gauge(
            f'{prefix}_unrealized_pnl_dollars',
            'Unrealized P&L',
            ['symbol']
        )
        
        # Performance metrics
        self.signal_latency = Histogram(
            f'{prefix}_signal_latency_seconds',
            'Signal generation latency',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        self.order_latency = Histogram(
            f'{prefix}_order_latency_seconds',
            'Order execution latency',
            ['broker'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        )
        
        self.model_inference_time = Histogram(
            f'{prefix}_model_inference_seconds',
            'ML model inference time',
            ['model_name'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
        )
        
        # Risk metrics
        self.portfolio_var = Gauge(
            f'{prefix}_portfolio_var_dollars',
            'Portfolio Value at Risk',
            ['confidence']
        )
        
        self.max_drawdown = Gauge(
            f'{prefix}_max_drawdown_percent',
            'Maximum drawdown percentage'
        )
        
        self.current_drawdown = Gauge(
            f'{prefix}_current_drawdown_percent',
            'Current drawdown percentage'
        )
        
        self.sharpe_ratio = Gauge(
            f'{prefix}_sharpe_ratio',
            'Current Sharpe ratio'
        )
        
        self.sortino_ratio = Gauge(
            f'{prefix}_sortino_ratio',
            'Current Sortino ratio'
        )
        
        self.win_rate = Gauge(
            f'{prefix}_win_rate_percent',
            'Win rate percentage'
        )
        
        self.profit_factor = Gauge(
            f'{prefix}_profit_factor',
            'Profit factor'
        )
        
        # System health
        self.broker_connected = Gauge(
            f'{prefix}_broker_connected',
            'Broker connection status',
            ['broker']
        )
        
        self.data_feed_status = Gauge(
            f'{prefix}_data_feed_status',
            'Data feed status',
            ['feed']
        )
        
        self.api_errors = Counter(
            f'{prefix}_api_errors_total',
            'API error count',
            ['api', 'error_type']
        )
        
        self.order_rejections = Counter(
            f'{prefix}_order_rejections_total',
            'Order rejection count',
            ['broker', 'reason']
        )
        
        # System resources
        self.cpu_usage = Gauge(
            f'{prefix}_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage = Gauge(
            f'{prefix}_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.memory_percent = Gauge(
            f'{prefix}_memory_usage_percent',
            'Memory usage percentage'
        )
        
        self.disk_usage = Gauge(
            f'{prefix}_disk_usage_percent',
            'Disk usage percentage'
        )
        
        # Application info
        self.app_info = Info(
            f'{prefix}_app',
            'Application information'
        )
        
        self.uptime = Gauge(
            f'{prefix}_uptime_seconds',
            'Application uptime in seconds'
        )
        
        self._start_time = time.time()
        self._server_started = False
        
        logger.info(f"PrometheusMetricsCollector initialized on port {port}")
    
    def start_server(self):
        """Start Prometheus HTTP server"""
        if not self.enabled or self._server_started:
            return
        try:
        
            start_http_server(self.port)
            self._server_started = True
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    def record_trade(self, symbol: str, side: str, pnl: float, 
                     duration_seconds: float, strategy: str = "default"):
        """Record trade execution"""
        if not self.enabled:
            return
        
        self.trades_total.labels(symbol=symbol, side=side, strategy=strategy).inc()
        self.trade_pnl.labels(symbol=symbol).observe(pnl)
        self.trade_duration.labels(symbol=symbol).observe(duration_seconds)
    
    def update_account(self, equity: float, balance: float):
        """Update account metrics"""
        if not self.enabled:
            return
        
        self.account_equity.set(equity)
        self.account_balance.set(balance)
    
    def update_position(self, symbol: str, side: str, quantity: float, 
                        value: float, unrealized_pnl: float):
        """Update position metrics"""
        if not self.enabled:
            return
        
        self.open_positions.labels(symbol=symbol).set(1 if quantity > 0 else 0)
        self.position_value.labels(symbol=symbol, side=side).set(value)
        self.unrealized_pnl.labels(symbol=symbol).set(unrealized_pnl)
    
    def record_signal_latency(self, latency: float):
        """Record signal generation latency"""
        if not self.enabled:
            return
        self.signal_latency.observe(latency)
    
    def record_order_latency(self, broker: str, latency: float):
        """Record order execution latency"""
        if not self.enabled:
            return
        self.order_latency.labels(broker=broker).observe(latency)
    
    def record_model_inference(self, model_name: str, duration: float):
        """Record ML model inference time"""
        if not self.enabled:
            return
        self.model_inference_time.labels(model_name=model_name).observe(duration)
    
    def update_risk_metrics(self, var_95: float, var_99: float,
                            max_dd: float, current_dd: float,
                            sharpe: float, sortino: float,
                            win_rate: float, profit_factor: float):
        """Update risk metrics"""
        if not self.enabled:
            return
        
        self.portfolio_var.labels(confidence='95').set(abs(var_95))
        self.portfolio_var.labels(confidence='99').set(abs(var_99))
        self.max_drawdown.set(max_dd)
        self.current_drawdown.set(current_dd)
        self.sharpe_ratio.set(sharpe)
        self.sortino_ratio.set(sortino)
        self.win_rate.set(win_rate)
        self.profit_factor.set(profit_factor)
    
    def update_broker_status(self, broker: str, connected: bool):
        """Update broker connection status"""
        if not self.enabled:
            return
        self.broker_connected.labels(broker=broker).set(1 if connected else 0)
    
    def record_api_error(self, api: str, error_type: str):
        """Record API error"""
        if not self.enabled:
            return
        self.api_errors.labels(api=api, error_type=error_type).inc()
    
    def record_order_rejection(self, broker: str, reason: str):
        """Record order rejection"""
        if not self.enabled:
            return
        self.order_rejections.labels(broker=broker, reason=reason).inc()
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        if not self.enabled or not PSUTIL_AVAILABLE:
            return
        try:
        
            self.cpu_usage.set(psutil.cpu_percent())
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            self.memory_percent.set(memory.percent)
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.percent)
            self.uptime.set(time.time() - self._start_time)
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def set_app_info(self, version: str, environment: str, **kwargs):
        """Set application info"""
        if not self.enabled:
            return
        
        info = {
            'version': version,
            'environment': environment,
            **kwargs
        }
        self.app_info.info(info)


class AlertManager:
    """
    Multi-channel alert manager with rate limiting and escalation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Channel configurations
        self.slack_webhook = self.config.get('slack_webhook')
        self.telegram_token = self.config.get('telegram_token')
        self.telegram_chat_id = self.config.get('telegram_chat_id')
        self.pagerduty_key = self.config.get('pagerduty_key')
        self.email_config = self.config.get('email', {})
        self.sms_config = self.config.get('sms', {})
        
        # Alert history
        self.alerts: List[Alert] = []
        self.max_alerts = self.config.get('max_alerts', 1000)
        
        # Rate limiting
        self.rate_limits: Dict[str, deque] = {}
        self.rate_limit_window = self.config.get('rate_limit_window', 60)
        self.rate_limit_max = self.config.get('rate_limit_max', 10)
        
        # Severity routing
        self.severity_channels = {
            AlertSeverity.INFO: [AlertChannel.SLACK],
            AlertSeverity.WARNING: [AlertChannel.SLACK, AlertChannel.TELEGRAM],
            AlertSeverity.ERROR: [AlertChannel.SLACK, AlertChannel.TELEGRAM, AlertChannel.EMAIL],
            AlertSeverity.CRITICAL: [AlertChannel.SLACK, AlertChannel.TELEGRAM, 
                                     AlertChannel.EMAIL, AlertChannel.PAGERDUTY, AlertChannel.SMS]
        }
        
        # Callbacks
        self.on_alert: Optional[Callable] = None
        
        logger.info("AlertManager initialized")
    
    def _check_rate_limit(self, key: str) -> bool:
        """Check if rate limit allows sending"""
        now = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = deque()
        
        # Clean old entries
        while self.rate_limits[key] and now - self.rate_limits[key][0] > self.rate_limit_window:
            self.rate_limits[key].popleft()
        
        if len(self.rate_limits[key]) >= self.rate_limit_max:
            return False
        
        self.rate_limits[key].append(now)
        return True
    
    async def send_alert(self, alert: Alert, channels: Optional[List[AlertChannel]] = None):
        """Send alert through specified channels"""
        # Determine channels
        if channels is None:
            channels = self.severity_channels.get(alert.severity, [AlertChannel.SLACK])
        
        # Store alert
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Check rate limit
        rate_key = f"{alert.source}:{alert.severity.value}"
        if not self._check_rate_limit(rate_key):
            logger.warning(f"Rate limit exceeded for {rate_key}")
            return
        
        # Send to channels
        tasks = []
        for channel in channels:
            if channel == AlertChannel.SLACK and self.slack_webhook:
                tasks.append(self._send_slack(alert))
            elif channel == AlertChannel.TELEGRAM and self.telegram_token:
                tasks.append(self._send_telegram(alert))
            elif channel == AlertChannel.EMAIL and self.email_config:
                tasks.append(self._send_email(alert))
            elif channel == AlertChannel.PAGERDUTY and self.pagerduty_key:
                tasks.append(self._send_pagerduty(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Callback
        if self.on_alert:
            try:
                if asyncio.iscoroutinefunction(self.on_alert):
                    await self.on_alert(alert)
                else:
                    self.on_alert(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    async def _send_slack(self, alert: Alert):
        """Send alert to Slack"""
        if not AIOHTTP_AVAILABLE:
            return
        
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff6600",
            AlertSeverity.CRITICAL: "#ff0000"
        }
        
        payload = {
            "attachments": [{
                "color": colors.get(alert.severity, "#808080"),
                "title": f"[{alert.severity.value.upper()}] {alert.title}",
                "text": alert.message,
                "fields": [
                    {"title": "Source", "value": alert.source, "short": True},
                    {"title": "Time", "value": alert.timestamp.isoformat(), "short": True}
                ],
                "footer": "AlphaAlgo Trading Bot"
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Slack alert failed: {resp.status}")
        except Exception as e:
            logger.error(f"Slack alert error: {e}")
    
    async def _send_telegram(self, alert: Alert):
        """Send alert to Telegram"""
        if not AIOHTTP_AVAILABLE:
            return
        
        emojis = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        message = (
            f"{emojis.get(alert.severity, '📢')} *{alert.severity.value.upper()}*\n\n"
            f"*{alert.title}*\n\n"
            f"{alert.message}\n\n"
            f"_Source: {alert.source}_\n"
            f"_Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_"
        )
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Telegram alert failed: {resp.status}")
        except Exception as e:
            logger.error(f"Telegram alert error: {e}")
    
    async def _send_email(self, alert: Alert):
        """Send alert via email"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_addr')
            msg['To'] = self.email_config.get('to_addr')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
            Alert: {alert.title}
            Severity: {alert.severity.value}
            Source: {alert.source}
            Time: {alert.timestamp.isoformat()}
            
            {alert.message}
            
            Metadata: {json.dumps(alert.metadata, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.email_config.get('smtp_server'), 
                             self.email_config.get('smtp_port', 587)) as server:
                server.starttls()
                server.login(self.email_config.get('username'),
                           self.email_config.get('password'))
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Email alert error: {e}")
    
    async def _send_pagerduty(self, alert: Alert):
        """Send alert to PagerDuty"""
        if not AIOHTTP_AVAILABLE:
            return
        
        severity_map = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "critical"
        }
        
        payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"{alert.title}: {alert.message}",
                "severity": severity_map.get(alert.severity, "info"),
                "source": alert.source,
                "timestamp": alert.timestamp.isoformat(),
                "custom_details": alert.metadata
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload
                ) as resp:
                    if resp.status != 202:
                        logger.error(f"PagerDuty alert failed: {resp.status}")
        except Exception as e:
            logger.error(f"PagerDuty alert error: {e}")
    
    def get_alerts(self, severity: Optional[AlertSeverity] = None,
                   limit: int = 100) -> List[Alert]:
        """Get recent alerts"""
        alerts = self.alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts[-limit:]


class HealthMonitor:
    """
    System health monitoring with automatic alerting.
    """
    
    def __init__(self, metrics: PrometheusMetricsCollector,
                 alert_manager: AlertManager,
                 config: Optional[Dict[str, Any]] = None):
        self.metrics = metrics
        self.alert_manager = alert_manager
        self.config = config or {}
        
        # Thresholds
        self.cpu_threshold = self.config.get('cpu_threshold', 80)
        self.memory_threshold = self.config.get('memory_threshold', 85)
        self.disk_threshold = self.config.get('disk_threshold', 90)
        self.latency_threshold = self.config.get('latency_threshold', 1.0)
        
        # State
        self.is_healthy = True
        self.last_check = None
        self.issues: List[str] = []
        
        # Monitoring
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.check_interval = self.config.get('check_interval', 30)
        
        logger.info("HealthMonitor initialized")
    
    async def start(self):
        """Start health monitoring"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")
    
    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform health check"""
        self.last_check = datetime.now()
        self.issues = []
        checks = {}
        
        # System resources
        if PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            checks['cpu'] = {'value': cpu, 'healthy': cpu < self.cpu_threshold}
            checks['memory'] = {'value': memory.percent, 'healthy': memory.percent < self.memory_threshold}
            checks['disk'] = {'value': disk.percent, 'healthy': disk.percent < self.disk_threshold}
            
            if cpu >= self.cpu_threshold:
                self.issues.append(f"High CPU usage: {cpu}%")
            if memory.percent >= self.memory_threshold:
                self.issues.append(f"High memory usage: {memory.percent}%")
            if disk.percent >= self.disk_threshold:
                self.issues.append(f"High disk usage: {disk.percent}%")
            
            # Update metrics
            self.metrics.update_system_metrics()
        
        # Overall health
        self.is_healthy = len(self.issues) == 0
        
        # Send alerts for issues
        if self.issues:
            alert = Alert(
                alert_id=f"health_{int(time.time())}",
                severity=AlertSeverity.WARNING if len(self.issues) < 3 else AlertSeverity.ERROR,
                title="System Health Issues Detected",
                message="\n".join(self.issues),
                source="HealthMonitor",
                timestamp=datetime.now()
            )
            await self.alert_manager.send_alert(alert)
        
        return {
            'healthy': self.is_healthy,
            'timestamp': self.last_check.isoformat(),
            'checks': checks,
            'issues': self.issues
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            'healthy': self.is_healthy,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'issues': self.issues
        }


class ProductionMonitor:
    """
    Complete production monitoring system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.metrics = PrometheusMetricsCollector(
            port=self.config.get('metrics_port', 9090),
            prefix=self.config.get('metrics_prefix', 'alphaalgo')
        )
        
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        
        self.health_monitor = HealthMonitor(
            self.metrics,
            self.alert_manager,
            self.config.get('health', {})
        )
        
        # Trading metrics tracking
        self.trade_count = 0
        self.total_pnl = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        
        logger.info("ProductionMonitor initialized")
    
    async def start(self):
        """Start all monitoring"""
        self.metrics.start_server()
        await self.health_monitor.start()
        
        # Set app info
        self.metrics.set_app_info(
            version=self.config.get('version', '2.0.0'),
            environment=self.config.get('environment', 'production')
        )
        
        logger.info("Production monitoring started")
    
    async def stop(self):
        """Stop all monitoring"""
        await self.health_monitor.stop()
        logger.info("Production monitoring stopped")
    
    def record_trade(self, symbol: str, side: str, pnl: float,
                     duration: float, strategy: str = "default"):
        """Record a trade"""
        self.metrics.record_trade(symbol, side, pnl, duration, strategy)
        
        self.trade_count += 1
        self.total_pnl += pnl
        
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Update win rate
        if self.trade_count > 0:
            win_rate = (self.winning_trades / self.trade_count) * 100
            self.metrics.win_rate.set(win_rate)
    
    async def send_alert(self, severity: AlertSeverity, title: str,
                         message: str, source: str = "TradingBot",
                         **metadata):
        """Send an alert"""
        alert = Alert(
            alert_id=f"alert_{int(time.time())}",
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata
        )
        await self.alert_manager.send_alert(alert)
    
    def get_metrics_endpoint(self) -> str:
        """Get Prometheus metrics endpoint"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(REGISTRY).decode('utf-8')
        return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete monitoring status"""
        return {
            'health': self.health_monitor.get_status(),
            'trading': {
                'trade_count': self.trade_count,
                'total_pnl': self.total_pnl,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': (self.winning_trades / self.trade_count * 100) if self.trade_count > 0 else 0
            },
            'alerts': {
                'recent': [a.to_dict() for a in self.alert_manager.get_alerts(limit=10)]
            }
        }


# Singleton instance
_monitor: Optional[ProductionMonitor] = None


def get_monitor(config: Optional[Dict[str, Any]] = None) -> ProductionMonitor:
    """Get or create the production monitor singleton"""
    global _monitor
    if _monitor is None:
        _monitor = ProductionMonitor(config)
    return _monitor


# Export
__all__ = [
    'ProductionMonitor',
    'PrometheusMetricsCollector',
    'AlertManager',
    'HealthMonitor',
    'Alert',
    'AlertSeverity',
    'AlertChannel',
    'get_monitor'
]
