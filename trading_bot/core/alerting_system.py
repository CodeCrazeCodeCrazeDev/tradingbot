"""
Alerting System
Multi-channel alert delivery (Slack, Email, Discord, Telegram)
"""

import asyncio
import logging
import smtplib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Alert message"""
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'message': self.message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ChannelConfig:
    """Channel configuration"""
    enabled: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


class AlertingSystem:
    """
    Multi-Channel Alerting System
    
    Sends alerts through multiple channels with rate limiting
    and severity-based routing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize alerting system
        
        Args:
            config: Channel configurations
        """
        self.config = config or {}
        
        # Channel configurations
        self.channels: Dict[AlertChannel, ChannelConfig] = {
            AlertChannel.EMAIL: ChannelConfig(
                enabled=self.config.get('email', {}).get('enabled', False),
                config=self.config.get('email', {})
            ),
            AlertChannel.SLACK: ChannelConfig(
                enabled=self.config.get('slack', {}).get('enabled', False),
                config=self.config.get('slack', {})
            ),
            AlertChannel.DISCORD: ChannelConfig(
                enabled=self.config.get('discord', {}).get('enabled', False),
                config=self.config.get('discord', {})
            ),
            AlertChannel.TELEGRAM: ChannelConfig(
                enabled=self.config.get('telegram', {}).get('enabled', False),
                config=self.config.get('telegram', {})
            ),
            AlertChannel.WEBHOOK: ChannelConfig(
                enabled=self.config.get('webhook', {}).get('enabled', False),
                config=self.config.get('webhook', {})
            )
        }
        
        # Rate limiting
        self.rate_limit_window = timedelta(minutes=5)
        self.max_alerts_per_window = 10
        self.alert_history: List[datetime] = []
        
        # Alert queue
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.processing = False
        
        # Statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': {s.value: 0 for s in AlertSeverity},
            'alerts_by_channel': {c.value: 0 for c in AlertChannel},
            'failed_deliveries': 0,
            'rate_limited': 0
        }
        
        logger.info("AlertingSystem initialized")
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        channels: Optional[List[AlertChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send alert through specified channels
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            channels: Target channels (all enabled if None)
            metadata: Additional metadata
        """
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            metadata=metadata or {}
        )
        
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning(f"Alert rate limited: {title}")
            self.stats['rate_limited'] += 1
            return
        
        self.stats['total_alerts'] += 1
        self.stats['alerts_by_severity'][severity.value] += 1
        
        # Determine target channels
        if channels is None:
            channels = [c for c, cfg in self.channels.items() if cfg.enabled]
        
        # Send to each channel
        for channel in channels:
            if not self.channels[channel].enabled:
                continue
            try:
            
                await self._send_to_channel(alert, channel)
                self.stats['alerts_by_channel'][channel.value] += 1
            except Exception as e:
                logger.error(f"Failed to send alert to {channel.value}: {e}")
                self.stats['failed_deliveries'] += 1
    
    async def _send_to_channel(self, alert: Alert, channel: AlertChannel):
        """Send alert to specific channel"""
        if channel == AlertChannel.EMAIL:
            await self._send_email(alert)
        elif channel == AlertChannel.SLACK:
            await self._send_slack(alert)
        elif channel == AlertChannel.DISCORD:
            await self._send_discord(alert)
        elif channel == AlertChannel.TELEGRAM:
            await self._send_telegram(alert)
        elif channel == AlertChannel.WEBHOOK:
            await self._send_webhook(alert)
    
    async def _send_email(self, alert: Alert):
        """Send email alert"""
        config = self.channels[AlertChannel.EMAIL].config
        
        smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        smtp_port = config.get('smtp_port', 587)
        username = config.get('username')
        password = config.get('password')
        from_addr = config.get('from_address', username)
        to_addrs = config.get('to_addresses', [])
        
        if not all([username, password, to_addrs]):
            logger.warning("Email configuration incomplete")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
{alert.title}

{alert.message}

Severity: {alert.severity.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Metadata:
{json.dumps(alert.metadata, indent=2)}
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    async def _send_slack(self, alert: Alert):
        """Send Slack alert"""
        config = self.channels[AlertChannel.SLACK].config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Color based on severity
        colors = {
            AlertSeverity.INFO: '#36a64f',
            AlertSeverity.WARNING: '#ff9900',
            AlertSeverity.ERROR: '#ff0000',
            AlertSeverity.CRITICAL: '#8b0000'
        }
        
        payload = {
            'attachments': [{
                'color': colors.get(alert.severity, '#808080'),
                'title': alert.title,
                'text': alert.message,
                'fields': [
                    {'title': 'Severity', 'value': alert.severity.value, 'short': True},
                    {'title': 'Time', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
                ],
                'footer': 'Trading Bot Alert System',
                'ts': int(alert.timestamp.timestamp())
            }]
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Slack API returned {response.status}")
            
            logger.info(f"Slack alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            raise
    
    async def _send_discord(self, alert: Alert):
        """Send Discord alert"""
        config = self.channels[AlertChannel.DISCORD].config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return
        
        # Color based on severity
        colors = {
            AlertSeverity.INFO: 0x36a64f,
            AlertSeverity.WARNING: 0xff9900,
            AlertSeverity.ERROR: 0xff0000,
            AlertSeverity.CRITICAL: 0x8b0000
        }
        
        payload = {
            'embeds': [{
                'title': alert.title,
                'description': alert.message,
                'color': colors.get(alert.severity, 0x808080),
                'fields': [
                    {'name': 'Severity', 'value': alert.severity.value, 'inline': True},
                    {'name': 'Time', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'inline': True}
                ],
                'footer': {'text': 'Trading Bot Alert System'},
                'timestamp': alert.timestamp.isoformat()
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status not in [200, 204]:
                        raise Exception(f"Discord API returned {response.status}")
            
            logger.info(f"Discord alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            raise
    
    async def _send_telegram(self, alert: Alert):
        """Send Telegram alert"""
        config = self.channels[AlertChannel.TELEGRAM].config
        bot_token = config.get('bot_token')
        chat_id = config.get('chat_id')
        
        if not all([bot_token, chat_id]):
            logger.warning("Telegram configuration incomplete")
            return
        
        # Format message
        emoji = {
            AlertSeverity.INFO: 'ℹ️',
            AlertSeverity.WARNING: '⚠️',
            AlertSeverity.ERROR: '❌',
            AlertSeverity.CRITICAL: '🚨'
        }
        
        text = f"{emoji.get(alert.severity, '📢')} *{alert.title}*\n\n{alert.message}\n\n"
        text += f"_Severity: {alert.severity.value}_\n"
        text += f"_Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Telegram API returned {response.status}")
            
            logger.info(f"Telegram alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            raise
    
    async def _send_webhook(self, alert: Alert):
        """Send webhook alert"""
        config = self.channels[AlertChannel.WEBHOOK].config
        url = config.get('url')
        
        if not url:
            logger.warning("Webhook URL not configured")
            return
        
        payload = alert.to_dict()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status not in [200, 201, 202, 204]:
                        raise Exception(f"Webhook returned {response.status}")
            
            logger.info(f"Webhook alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            raise
    
    def _check_rate_limit(self) -> bool:
        """Check if alert is within rate limit"""
        now = datetime.now()
        cutoff = now - self.rate_limit_window
        
        # Remove old alerts
        self.alert_history = [t for t in self.alert_history if t > cutoff]
        
        # Check limit
        if len(self.alert_history) >= self.max_alerts_per_window:
            return False
        
        self.alert_history.append(now)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alerting statistics"""
        return self.stats.copy()
    
    async def send_test_alert(self, channel: AlertChannel):
        """Send test alert to verify configuration"""
        await self.send_alert(
            title="Test Alert",
            message="This is a test alert from the Trading Bot Alert System.",
            severity=AlertSeverity.INFO,
            channels=[channel],
            metadata={'test': True}
        )


# Singleton instance
_alerting_system: Optional[AlertingSystem] = None


def get_alerting_system(config: Optional[Dict[str, Any]] = None) -> AlertingSystem:
    """Get or create alerting system singleton"""
    global _alerting_system
    
    if _alerting_system is None:
        _alerting_system = AlertingSystem(config)
    
    return _alerting_system


async def send_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    channels: Optional[List[AlertChannel]] = None
):
    """Convenience function to send alert"""
    system = get_alerting_system()
    await system.send_alert(title, message, severity, channels)


async def send_critical_alert(title: str, message: str):
    """Send critical alert to all channels"""
    await send_alert(title, message, AlertSeverity.CRITICAL)


async def send_error_alert(title: str, message: str):
    """Send error alert"""
    await send_alert(title, message, AlertSeverity.ERROR)


async def send_warning_alert(title: str, message: str):
    """Send warning alert"""
    await send_alert(title, message, AlertSeverity.WARNING)
