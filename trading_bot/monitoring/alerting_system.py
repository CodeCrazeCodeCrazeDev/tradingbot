"""
from typing import List, Optional, Set
Comprehensive Alerting and Monitoring System
=============================================

Full monitoring infrastructure:
- Prometheus metrics (enhanced)
- Grafana dashboard configs
- PagerDuty integration
- Slack alerts
- SMS alerts
- Email reports
- Anomaly detection
- SLA monitoring
- Uptime tracking
- Performance benchmarks

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import json
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum, auto
from collections import defaultdict, deque
import threading
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert channels"""
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class SLAStatus(Enum):
    """SLA status"""
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    BREACHED = "breached"


@dataclass
class Alert:
    """Alert data"""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Routing
    channels: List[AlertChannel] = field(default_factory=list)
    
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


@dataclass
class SLADefinition:
    """SLA definition"""
    name: str
    metric: str
    target: float
    window_hours: int = 24
    
    # Thresholds
    warning_threshold: float = 0.95  # 95% of target
    critical_threshold: float = 0.90  # 90% of target
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'metric': self.metric,
            'target': self.target,
            'window_hours': self.window_hours,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold
        }


@dataclass
class SLAReport:
    """SLA report"""
    sla_name: str
    timestamp: datetime
    status: SLAStatus
    
    # Metrics
    current_value: float
    target_value: float
    achievement_pct: float
    
    # History
    values_in_window: List[float] = field(default_factory=list)
    breaches_in_window: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'sla_name': self.sla_name,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'achievement_pct': self.achievement_pct,
            'breaches_in_window': self.breaches_in_window
        }


@dataclass
class UptimeRecord:
    """Uptime record"""
    service: str
    timestamp: datetime
    is_up: bool
    response_time_ms: float = 0.0
    error: Optional[str] = None


class SlackAlerter:
    """
    Slack alert integration
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
        logger.info("SlackAlerter initialized")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests not available for Slack")
            return False
        
        # Color based on severity
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff6600",
            AlertSeverity.CRITICAL: "#ff0000"
        }
        
        payload = {
            "attachments": [{
                "color": colors.get(alert.severity, "#808080"),
                "title": alert.title,
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value, "short": True},
                    {"title": "Source", "value": alert.source, "short": True},
                    {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ],
                "footer": "Elite Trading Bot",
                "ts": int(alert.timestamp.timestamp())
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")
            return False


class PagerDutyAlerter:
    """
    PagerDuty integration
    """
    
    def __init__(self, routing_key: str):
        self.routing_key = routing_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
        
        logger.info("PagerDutyAlerter initialized")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to PagerDuty"""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests not available for PagerDuty")
            return False
        
        # Map severity
        severity_map = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "critical"
        }
        
        payload = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "dedup_key": alert.alert_id,
            "payload": {
                "summary": alert.title,
                "severity": severity_map.get(alert.severity, "info"),
                "source": alert.source,
                "timestamp": alert.timestamp.isoformat(),
                "custom_details": {
                    "message": alert.message,
                    "tags": alert.tags,
                    **alert.metadata
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"PagerDuty alert failed: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert in PagerDuty"""
        if not REQUESTS_AVAILABLE:
            return False
        
        payload = {
            "routing_key": self.routing_key,
            "event_action": "resolve",
            "dedup_key": alert_id
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"PagerDuty resolve failed: {e}")
            return False


class EmailAlerter:
    """
    Email alert integration
    """
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        
        logger.info("EmailAlerter initialized")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # HTML content
            html = f"""
            <html>
            <body>
                <h2 style="color: {'red' if alert.severity == AlertSeverity.CRITICAL else 'orange'}">
                    {alert.title}
                </h2>
                <p><strong>Severity:</strong> {alert.severity.value}</p>
                <p><strong>Source:</strong> {alert.source}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{alert.message}</p>
                <hr>
                <p><small>Elite Trading Bot Alert System</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, self.to_emails, msg.as_string())
            
            return True
            
        except Exception as e:
            logger.error(f"Email alert failed: {e}")
            return False


class SMSAlerter:
    """
    SMS alert integration (via Twilio)
    """
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: List[str]
    ):
        self.from_number = from_number
        self.to_numbers = to_numbers
        
        if TWILIO_AVAILABLE:
            self.client = TwilioClient(account_sid, auth_token)
        else:
            self.client = None
            logger.warning("Twilio not available for SMS")
        
        logger.info("SMSAlerter initialized")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via SMS"""
        if not self.client:
            return False
        
        message = f"[{alert.severity.value.upper()}] {alert.title}: {alert.message[:100]}"
        
        success = True
        for to_number in self.to_numbers:
            try:
                self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
            except Exception as e:
                logger.error(f"SMS to {to_number} failed: {e}")
                success = False
        
        return success


class TelegramAlerter:
    """
    Telegram alert integration
    """
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        logger.info("TelegramAlerter initialized")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Telegram"""
        if not REQUESTS_AVAILABLE:
            return False
        
        # Emoji based on severity
        emojis = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        message = f"""
{emojis.get(alert.severity, '📢')} *{alert.title}*

*Severity:* {alert.severity.value}
*Source:* {alert.source}
*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{alert.message}
        """
        
        success = True
        for chat_id in self.chat_ids:
            try:
                response = requests.post(
                    self.api_url,
                    json={
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'Markdown'
                    },
                    timeout=10
                )
                if response.status_code != 200:
                    success = False
            except Exception as e:
                logger.error(f"Telegram alert failed: {e}")
                success = False
        
        return success


class DiscordAlerter:
    """
    Discord alert integration
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
        logger.info("DiscordAlerter initialized")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Discord"""
        if not REQUESTS_AVAILABLE:
            return False
        
        # Color based on severity
        colors = {
            AlertSeverity.INFO: 3447003,      # Blue
            AlertSeverity.WARNING: 16776960,   # Yellow
            AlertSeverity.ERROR: 16744448,     # Orange
            AlertSeverity.CRITICAL: 16711680   # Red
        }
        
        payload = {
            "embeds": [{
                "title": alert.title,
                "description": alert.message,
                "color": colors.get(alert.severity, 8421504),
                "fields": [
                    {"name": "Severity", "value": alert.severity.value, "inline": True},
                    {"name": "Source", "value": alert.source, "inline": True},
                    {"name": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
                ],
                "footer": {"text": "Elite Trading Bot"}
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Discord alert failed: {e}")
            return False


class AnomalyDetector:
    """
    Detects anomalies in metrics
    """
    
    def __init__(
        self,
        window_size: int = 100,
        z_threshold: float = 3.0
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        
        # Metric history
        self.history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        
        # Anomaly callbacks
        self.on_anomaly: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("AnomalyDetector initialized")
    
    def add_value(self, metric: str, value: float) -> Optional[Dict]:
        """Add a value and check for anomaly"""
        with self._lock:
            self.history[metric].append(value)
            
            if len(self.history[metric]) < self.window_size // 2:
                return None
            
            return self._check_anomaly(metric, value)
    
    def _check_anomaly(self, metric: str, value: float) -> Optional[Dict]:
        """Check if value is anomalous"""
        values = list(self.history[metric])
        
        mean = np.mean(values[:-1])  # Exclude current value
        std = np.std(values[:-1])
        
        if std == 0:
            return None
        
        z_score = abs(value - mean) / std
        
        if z_score > self.z_threshold:
            anomaly = {
                'metric': metric,
                'value': value,
                'mean': mean,
                'std': std,
                'z_score': z_score,
                'timestamp': datetime.now(),
                'direction': 'high' if value > mean else 'low'
            }
            
            # Fire callbacks
            for callback in self.on_anomaly:
                try:
                    callback(anomaly)
                except Exception as e:
                    logger.error(f"Anomaly callback error: {e}")
            
            return anomaly
        
        return None
    
    def get_statistics(self, metric: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        with self._lock:
            values = list(self.history.get(metric, []))
            
            if not values:
                return {}
            
            return {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }


class SLAMonitor:
    """
    Monitors SLA compliance
    """
    
    def __init__(self):
        # SLA definitions
        self.slas: Dict[str, SLADefinition] = {}
        
        # Metric history
        self.metric_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        
        # SLA reports
        self.reports: List[SLAReport] = []
        
        # Callbacks
        self.on_breach: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("SLAMonitor initialized")
    
    def define_sla(self, sla: SLADefinition):
        """Define an SLA"""
        with self._lock:
            self.slas[sla.name] = sla
            logger.info(f"SLA defined: {sla.name}")
    
    def record_metric(self, metric: str, value: float):
        """Record a metric value"""
        with self._lock:
            self.metric_history[metric].append({
                'value': value,
                'timestamp': datetime.now()
            })
    
    def check_sla(self, sla_name: str) -> Optional[SLAReport]:
        """Check SLA compliance"""
        with self._lock:
            sla = self.slas.get(sla_name)
            
            if not sla:
                return None
            
            # Get values in window
            cutoff = datetime.now() - timedelta(hours=sla.window_hours)
            values = [
                v['value'] for v in self.metric_history.get(sla.metric, [])
                if v['timestamp'] > cutoff
            ]
            
            if not values:
                return None
            
            current_value = np.mean(values)
            achievement_pct = (current_value / sla.target) * 100 if sla.target > 0 else 0
            
            # Determine status
            if achievement_pct >= 100:
                status = SLAStatus.HEALTHY
            elif achievement_pct >= sla.warning_threshold * 100:
                status = SLAStatus.AT_RISK
            else:
                status = SLAStatus.BREACHED
            
            # Count breaches
            breaches = sum(1 for v in values if v < sla.target * sla.critical_threshold)
            
            report = SLAReport(
                sla_name=sla_name,
                timestamp=datetime.now(),
                status=status,
                current_value=current_value,
                target_value=sla.target,
                achievement_pct=achievement_pct,
                values_in_window=values,
                breaches_in_window=breaches
            )
            
            self.reports.append(report)
            
            # Fire callbacks on breach
            if status == SLAStatus.BREACHED:
                for callback in self.on_breach:
                    try:
                        callback(report)
                    except Exception as e:
                        logger.error(f"SLA breach callback error: {e}")
            
            return report
    
    def check_all_slas(self) -> List[SLAReport]:
        """Check all SLAs"""
        reports = []
        
        for sla_name in self.slas:
            report = self.check_sla(sla_name)
            if report:
                reports.append(report)
        
        return reports
    
    def get_sla_summary(self) -> Dict[str, Any]:
        """Get SLA summary"""
        reports = self.check_all_slas()
        
        return {
            'total_slas': len(self.slas),
            'healthy': sum(1 for r in reports if r.status == SLAStatus.HEALTHY),
            'at_risk': sum(1 for r in reports if r.status == SLAStatus.AT_RISK),
            'breached': sum(1 for r in reports if r.status == SLAStatus.BREACHED),
            'reports': [r.to_dict() for r in reports]
        }


class UptimeTracker:
    """
    Tracks service uptime
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval = check_interval_seconds
        
        # Services to monitor
        self.services: Dict[str, Dict] = {}
        
        # Uptime records
        self.records: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        
        # Background task
        self._running = False
        self._task = None
        
        self._lock = threading.RLock()
        
        logger.info("UptimeTracker initialized")
    
    def add_service(
        self,
        name: str,
        url: str,
        timeout_seconds: float = 5.0
    ):
        """Add a service to monitor"""
        with self._lock:
            self.services[name] = {
                'url': url,
                'timeout': timeout_seconds
            }
    
    def remove_service(self, name: str):
        """Remove a service"""
        with self._lock:
            if name in self.services:
                del self.services[name]
    
    async def check_service(self, name: str) -> UptimeRecord:
        """Check a single service"""
        service = self.services.get(name)
        
        if not service or not REQUESTS_AVAILABLE:
            try:
                return UptimeRecord(
                    service=name,
                    timestamp=datetime.now(),
                    is_up=False,
                    error="Service not found or requests not available"
                )

                start = datetime.now()
                response = requests.get(
                    service['url'],
                    timeout=service['timeout']
                )
                response_time = (datetime.now() - start).total_seconds() * 1000

                is_up = response.status_code < 500

                record = UptimeRecord(
                    service=name,
                    timestamp=datetime.now(),
                    is_up=is_up,
                    response_time_ms=response_time,
                    error=None if is_up else f"Status code: {response.status_code}"
                )

            except Exception as e:
                record = UptimeRecord(
                    service=name,
                    timestamp=datetime.now(),
                    is_up=False,
                    error=str(e)
                )

        with self._lock:
            self.records[name].append(record)
        
        return record
    
    async def check_all_services(self) -> List[UptimeRecord]:
        """Check all services"""
        records = []
        
        for name in self.services:
            record = await self.check_service(name)
            records.append(record)
        
        return records
    
    def get_uptime_percentage(
        self,
        service: str,
        hours: int = 24
    ) -> float:
        """Get uptime percentage for a service"""
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours)
            records = [
                r for r in self.records.get(service, [])
                if r.timestamp > cutoff
            ]
            
            if not records:
                return 100.0
            
            up_count = sum(1 for r in records if r.is_up)
            return (up_count / len(records)) * 100
    
    def get_uptime_summary(self) -> Dict[str, Any]:
        """Get uptime summary"""
        summary = {
            'services': {},
            'overall_uptime': 0.0
        }
        
        uptimes = []
        for name in self.services:
            uptime = self.get_uptime_percentage(name)
            summary['services'][name] = {
                'uptime_24h': uptime,
                'uptime_7d': self.get_uptime_percentage(name, 168)
            }
            uptimes.append(uptime)
        
        if uptimes:
            summary['overall_uptime'] = np.mean(uptimes)
        
        return summary
    
    async def start(self):
        """Start uptime monitoring"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Uptime monitoring started")
    
    async def stop(self):
        """Stop uptime monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Uptime monitoring stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Uptime monitor error: {e}")
                await asyncio.sleep(5)


class PerformanceBenchmark:
    """
    Performance benchmarking
    """
    
    def __init__(self):
        # Benchmark results
        self.benchmarks: Dict[str, List[Dict]] = defaultdict(list)
        
        # Baselines
        self.baselines: Dict[str, float] = {}
        
        self._lock = threading.RLock()
        
        logger.info("PerformanceBenchmark initialized")
    
    def set_baseline(self, metric: str, value: float):
        """Set baseline for a metric"""
        with self._lock:
            self.baselines[metric] = value
    
    def record_benchmark(
        self,
        metric: str,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """Record a benchmark result"""
        with self._lock:
            self.benchmarks[metric].append({
                'value': value,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            })
    
    def get_benchmark_report(self, metric: str) -> Dict[str, Any]:
        """Get benchmark report for a metric"""
        with self._lock:
            results = self.benchmarks.get(metric, [])
            
            if not results:
                return {}
            
            values = [r['value'] for r in results]
            baseline = self.baselines.get(metric)
            
            report = {
                'metric': metric,
                'count': len(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'min': min(values),
                'max': max(values),
                'p50': np.percentile(values, 50),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99),
                'latest': values[-1]
            }
            
            if baseline:
                report['baseline'] = baseline
                report['vs_baseline_pct'] = ((np.mean(values) - baseline) / baseline) * 100
            
            return report
    
    def get_all_benchmarks(self) -> Dict[str, Dict]:
        """Get all benchmark reports"""
        return {
            metric: self.get_benchmark_report(metric)
            for metric in self.benchmarks
        }


class AlertingSystem:
    """
    Complete alerting system
    """
    
    def __init__(self):
        # Alert channels
        self.channels: Dict[AlertChannel, Any] = {}
        
        # Alert history
        self.alerts: deque = deque(maxlen=10000)
        
        # Alert routing rules
        self.routing_rules: List[Dict] = []
        
        # Components
        self.anomaly_detector = AnomalyDetector()
        self.sla_monitor = SLAMonitor()
        self.uptime_tracker = UptimeTracker()
        self.benchmark = PerformanceBenchmark()
        
        # Alert ID counter
        self._next_id = 1
        self._lock = threading.RLock()
        
        logger.info("AlertingSystem initialized")
    
    def _generate_id(self) -> str:
        with self._lock:
            alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return alert_id
    
    def configure_slack(self, webhook_url: str):
        """Configure Slack alerting"""
        self.channels[AlertChannel.SLACK] = SlackAlerter(webhook_url)
    
    def configure_pagerduty(self, routing_key: str):
        """Configure PagerDuty alerting"""
        self.channels[AlertChannel.PAGERDUTY] = PagerDutyAlerter(routing_key)
    
    def configure_email(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        """Configure email alerting"""
        self.channels[AlertChannel.EMAIL] = EmailAlerter(
            smtp_host, smtp_port, username, password, from_email, to_emails
        )
    
    def configure_sms(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: List[str]
    ):
        """Configure SMS alerting"""
        self.channels[AlertChannel.SMS] = SMSAlerter(
            account_sid, auth_token, from_number, to_numbers
        )
    
    def configure_telegram(self, bot_token: str, chat_ids: List[str]):
        """Configure Telegram alerting"""
        self.channels[AlertChannel.TELEGRAM] = TelegramAlerter(bot_token, chat_ids)
    
    def configure_discord(self, webhook_url: str):
        """Configure Discord alerting"""
        self.channels[AlertChannel.DISCORD] = DiscordAlerter(webhook_url)
    
    def add_routing_rule(
        self,
        severity: AlertSeverity,
        channels: List[AlertChannel],
        tags: Optional[List[str]] = None
    ):
        """Add alert routing rule"""
        self.routing_rules.append({
            'severity': severity,
            'channels': channels,
            'tags': tags or []
        })
    
    def _get_channels_for_alert(self, alert: Alert) -> List[AlertChannel]:
        """Get channels for an alert based on routing rules"""
        channels = set()
        
        for rule in self.routing_rules:
            if rule['severity'] == alert.severity:
                if not rule['tags'] or any(t in alert.tags for t in rule['tags']):
                    channels.update(rule['channels'])
        
        return list(channels)
    
    async def send_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Alert:
        """Send an alert"""
        alert = Alert(
            alert_id=self._generate_id(),
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Get channels
        alert.channels = self._get_channels_for_alert(alert)
        
        # Send to each channel
        for channel in alert.channels:
            alerter = self.channels.get(channel)
            if alerter:
                try:
                    await alerter.send_alert(alert)
                except Exception as e:
                    logger.error(f"Failed to send to {channel.value}: {e}")
        
        # Store alert
        with self._lock:
            self.alerts.append(alert)
        
        return alert
    
    def get_recent_alerts(self, count: int = 100) -> List[Dict]:
        """Get recent alerts"""
        with self._lock:
            return [a.to_dict() for a in list(self.alerts)[-count:]]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    return True
            return False


# Singleton instance
_alerting_system: Optional[AlertingSystem] = None


def get_alerting_system() -> AlertingSystem:
    global _alerting_system
    if _alerting_system is None:
        _alerting_system = AlertingSystem()
    return _alerting_system


# Export
__all__ = [
    'AlertingSystem',
    'SlackAlerter',
    'PagerDutyAlerter',
    'EmailAlerter',
    'SMSAlerter',
    'TelegramAlerter',
    'DiscordAlerter',
    'AnomalyDetector',
    'SLAMonitor',
    'UptimeTracker',
    'PerformanceBenchmark',
    'Alert',
    'AlertSeverity',
    'AlertChannel',
    'SLADefinition',
    'SLAReport',
    'SLAStatus',
    'UptimeRecord',
    'get_alerting_system'
]
