"""
Real-Time Alert System for Critical Trading Opportunities
Notifications via multiple channels (email, SMS, webhook, desktop)
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from collections import deque
import os

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Important opportunity
    MEDIUM = "medium"  # Standard alert
    LOW = "low"  # Informational
    INFO = "info"  # General information

class AlertType(Enum):
    """Types of alerts"""
    OPPORTUNITY = "opportunity"  # Trading opportunity detected
    EXECUTION = "execution"  # Trade executed
    RISK = "risk"  # Risk warning
    PERFORMANCE = "performance"  # Performance milestone
    SYSTEM = "system"  # System status
    ERROR = "error"  # Error condition

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    timestamp: datetime
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    symbol: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    channels: List[str] = None
    metadata: Dict[str, Any] = None

class AlertSystem:
    """
    Comprehensive alert system with multiple notification channels
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Alert queue
        self.alert_queue = asyncio.Queue()
        self.alert_history = deque(maxlen=1000)
        
        # Alert filters
        self.min_severity = AlertSeverity[config.get('min_severity', 'MEDIUM')]
        self.alert_cooldown = config.get('cooldown_seconds', 60)
        self.last_alert_times = {}
        
        # Notification channels
        self.channels = {}
        self._initialize_channels()
        
        # Alert rules
        self.alert_rules = []
        self._load_alert_rules()
        
        # Database manager
        self.db_manager = None
        
        # Start alert processor
        self.processor_task = None
        
    def _initialize_channels(self):
        """Initialize notification channels"""
        # Email channel
        if 'email' in self.config:
            self.channels['email'] = EmailChannel(self.config['email'])
        
        # SMS channel (Twilio)
        if 'sms' in self.config:
            self.channels['sms'] = SMSChannel(self.config['sms'])
        
        # Webhook channel
        if 'webhook' in self.config:
            self.channels['webhook'] = WebhookChannel(self.config['webhook'])
        
        # Desktop notifications
        if self.config.get('desktop_notifications', True):
            self.channels['desktop'] = DesktopChannel()
        
        # Telegram channel
        if 'telegram' in self.config:
            self.channels['telegram'] = TelegramChannel(self.config['telegram'])
        
        # Discord channel
        if 'discord' in self.config:
            self.channels['discord'] = DiscordChannel(self.config['discord'])
        
        logger.info(f"Initialized {len(self.channels)} notification channels")
    
    def _load_alert_rules(self):
        """Load alert rules from configuration"""
        rules = self.config.get('alert_rules', [])
        
        # Default rules
        default_rules = [
            {
                'name': 'High Confidence Opportunity',
                'condition': lambda data: data.get('confidence', 0) > 0.8,
                'severity': AlertSeverity.HIGH,
                'channels': ['email', 'desktop', 'telegram']
            },
            {
                'name': 'Large P&L',
                'condition': lambda data: abs(data.get('pnl', 0)) > 1000,
                'severity': AlertSeverity.HIGH,
                'channels': ['email', 'sms']
            },
            {
                'name': 'Risk Limit Breach',
                'condition': lambda data: data.get('risk_breach', False),
                'severity': AlertSeverity.CRITICAL,
                'channels': ['all']
            },
            {
                'name': 'System Error',
                'condition': lambda data: data.get('error_level', '') == 'critical',
                'severity': AlertSeverity.CRITICAL,
                'channels': ['all']
            }
        ]
        
        self.alert_rules.extend(default_rules)
        self.alert_rules.extend(rules)
    
    async def start(self):
        """Start the alert system"""
        self.processor_task = asyncio.create_task(self._process_alerts())
        logger.info("Alert system started")
    
    async def stop(self):
        """Stop the alert system"""
        if self.processor_task:
            self.processor_task.cancel()
        logger.info("Alert system stopped")
    
    async def send_alert(self, alert: Alert):
        """Send an alert"""
        # Check severity filter
        if alert.severity.value < self.min_severity.value:
            return
        
        # Check cooldown
        if not self._check_cooldown(alert):
            return
        
        # Add to queue
        await self.alert_queue.put(alert)
        
        # Save to history
        self.alert_history.append(alert)
        
        # Save to database if available
        if self.db_manager:
            await self.db_manager.save_alert({
                'alert_id': alert.alert_id,
                'timestamp': alert.timestamp,
                'type': alert.type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'metadata': alert.metadata
            })
    
    async def create_opportunity_alert(self, opportunity: Dict):
        """Create alert for trading opportunity"""
        # Check alert rules
        severity = self._determine_severity(opportunity)
        channels = self._determine_channels(opportunity, severity)
        
        alert = Alert(
            alert_id=f"OPP_{opportunity.get('opportunity_id', datetime.now().timestamp())}",
            timestamp=datetime.now(),
            type=AlertType.OPPORTUNITY,
            severity=severity,
            title=f"Trading Opportunity: {opportunity.get('type', 'Unknown')}",
            message=self._format_opportunity_message(opportunity),
            symbol=opportunity.get('symbol'),
            data=opportunity,
            channels=channels
        )
        
        await self.send_alert(alert)
    
    async def create_execution_alert(self, trade: Dict):
        """Create alert for trade execution"""
        alert = Alert(
            alert_id=f"EXEC_{trade.get('trade_id', datetime.now().timestamp())}",
            timestamp=datetime.now(),
            type=AlertType.EXECUTION,
            severity=AlertSeverity.MEDIUM,
            title=f"Trade Executed: {trade.get('symbol', 'Unknown')}",
            message=self._format_execution_message(trade),
            symbol=trade.get('symbol'),
            data=trade,
            channels=['desktop', 'telegram']
        )
        
        await self.send_alert(alert)
    
    async def create_risk_alert(self, risk_data: Dict):
        """Create alert for risk warning"""
        severity = AlertSeverity.CRITICAL if risk_data.get('critical', False) else AlertSeverity.HIGH
        
        alert = Alert(
            alert_id=f"RISK_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            type=AlertType.RISK,
            severity=severity,
            title="⚠️ Risk Warning",
            message=self._format_risk_message(risk_data),
            data=risk_data,
            channels=['all']
        )
        
        await self.send_alert(alert)
    
    async def create_performance_alert(self, metrics: Dict):
        """Create alert for performance milestone"""
        alert = Alert(
            alert_id=f"PERF_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            type=AlertType.PERFORMANCE,
            severity=AlertSeverity.INFO,
            title="📈 Performance Update",
            message=self._format_performance_message(metrics),
            data=metrics,
            channels=['email', 'desktop']
        )
        
        await self.send_alert(alert)
    
    async def create_system_alert(self, system_data: Dict):
        """Create alert for system status"""
        severity = AlertSeverity[system_data.get('severity', 'MEDIUM').upper()]
        
        alert = Alert(
            alert_id=f"SYS_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            type=AlertType.SYSTEM,
            severity=severity,
            title="System Status",
            message=system_data.get('message', 'System status update'),
            data=system_data,
            channels=['desktop']
        )
        
        await self.send_alert(alert)
    
    async def _process_alerts(self):
        """Process alerts from queue"""
        while True:
            try:
                alert = await self.alert_queue.get()
                
                # Determine channels
                channels = alert.channels or self._get_default_channels(alert.severity)
                
                # Send to each channel
                tasks = []
                for channel_name in channels:
                    if channel_name == 'all':
                        # Send to all channels
                        for name, channel in self.channels.items():
                            tasks.append(channel.send(alert))
                    elif channel_name in self.channels:
                        tasks.append(self.channels[channel_name].send(alert))
                
                # Send in parallel
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                logger.info(f"Alert sent: {alert.title}")
                
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
    
    def _check_cooldown(self, alert: Alert) -> bool:
        """Check if alert passes cooldown period"""
        key = f"{alert.type.value}_{alert.symbol or 'global'}"
        
        if key in self.last_alert_times:
            time_since_last = (datetime.now() - self.last_alert_times[key]).seconds
            if time_since_last < self.alert_cooldown:
                return False
        
        self.last_alert_times[key] = datetime.now()
        return True
    
    def _determine_severity(self, data: Dict) -> AlertSeverity:
        """Determine alert severity based on data"""
        # Check rules
        for rule in self.alert_rules:
            if 'condition' in rule and rule['condition'](data):
                return rule.get('severity', AlertSeverity.MEDIUM)
        
        # Default based on confidence
        confidence = data.get('confidence', 0.5)
        if confidence > 0.9:
            return AlertSeverity.HIGH
        elif confidence > 0.7:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _determine_channels(self, data: Dict, severity: AlertSeverity) -> List[str]:
        """Determine which channels to use"""
        # Check rules
        for rule in self.alert_rules:
            if 'condition' in rule and rule['condition'](data):
                return rule.get('channels', self._get_default_channels(severity))
        
        return self._get_default_channels(severity)
    
    def _get_default_channels(self, severity: AlertSeverity) -> List[str]:
        """Get default channels based on severity"""
        if severity == AlertSeverity.CRITICAL:
            return ['all']
        elif severity == AlertSeverity.HIGH:
            return ['email', 'desktop', 'telegram']
        elif severity == AlertSeverity.MEDIUM:
            return ['desktop', 'telegram']
        else:
            return ['desktop']
    
    def _format_opportunity_message(self, opportunity: Dict) -> str:
        """Format opportunity alert message"""
        return f"""
🎯 Trading Opportunity Detected

Type: {opportunity.get('type', 'Unknown')}
Symbol: {opportunity.get('symbol', 'N/A')}
Confidence: {opportunity.get('confidence', 0):.1%}
Expected Return: {opportunity.get('expected_return', 0):.2%}
Risk Score: {opportunity.get('risk', 0):.2f}

Action: {opportunity.get('action', 'Review opportunity')}
        """.strip()
    
    def _format_execution_message(self, trade: Dict) -> str:
        """Format execution alert message"""
        return f"""
✅ Trade Executed

Symbol: {trade.get('symbol', 'N/A')}
Side: {trade.get('side', 'Unknown')}
Quantity: {trade.get('quantity', 0)}
Price: {trade.get('price', 0)}
Status: {trade.get('status', 'Unknown')}
        """.strip()
    
    def _format_risk_message(self, risk_data: Dict) -> str:
        """Format risk alert message"""
        return f"""
⚠️ Risk Alert

Type: {risk_data.get('risk_type', 'Unknown')}
Level: {risk_data.get('level', 'Unknown')}
Message: {risk_data.get('message', 'Risk limit approached')}

Current VaR: {risk_data.get('var', 0):.2%}
Max Drawdown: {risk_data.get('max_drawdown', 0):.2%}

Action Required: {risk_data.get('action', 'Review positions')}
        """.strip()
    
    def _format_performance_message(self, metrics: Dict) -> str:
        """Format performance alert message"""
        return f"""
📊 Performance Update

Win Rate: {metrics.get('win_rate', 0):.1%}
Total P&L: ${metrics.get('total_pnl', 0):,.2f}
Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
Active Positions: {metrics.get('active_positions', 0)}

Daily Return: {metrics.get('daily_return', 0):.2%}
Weekly Return: {metrics.get('weekly_return', 0):.2%}
        """.strip()


class EmailChannel:
    """Email notification channel"""
    
    def __init__(self, config: Dict):
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('sender_email')
        self.sender_password = config.get('sender_password')
        self.recipient_emails = config.get('recipient_emails', [])
    
    async def send(self, alert: Alert):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"{alert.message}\n\nTimestamp: {alert.timestamp}"
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")


class SMSChannel:
    """SMS notification channel using Twilio"""
    
    def __init__(self, config: Dict):
        self.account_sid = config.get('account_sid')
        self.auth_token = config.get('auth_token')
        self.from_number = config.get('from_number')
        self.to_numbers = config.get('to_numbers', [])
    
    async def send(self, alert: Alert):
        """Send SMS alert"""
        try:
            # Import Twilio client
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # Short message for SMS
            message = f"{alert.title[:50]}\n{alert.message[:100]}"
            
            for to_number in self.to_numbers:
                client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
            
            logger.info(f"SMS alert sent: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")


class WebhookChannel:
    """Webhook notification channel"""
    
    def __init__(self, config: Dict):
        self.webhook_url = config.get('url')
        self.headers = config.get('headers', {})
    
    async def send(self, alert: Alert):
        """Send webhook alert"""
        try:
            payload = {
                'alert_id': alert.alert_id,
                'timestamp': alert.timestamp.isoformat(),
                'type': alert.type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'symbol': alert.symbol,
                'data': alert.data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent: {alert.title}")
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


class DesktopChannel:
    """Desktop notification channel"""
    
    async def send(self, alert: Alert):
        """Send desktop notification"""
        try:
            # Use plyer for cross-platform notifications
            from plyer import notification
            
            notification.notify(
                title=f"[{alert.severity.value.upper()}] {alert.title}",
                message=alert.message[:256],  # Limit message length
                timeout=10
            )
            
            logger.info(f"Desktop alert sent: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send desktop alert: {e}")


class TelegramChannel:
    """Telegram notification channel"""
    
    def __init__(self, config: Dict):
        self.bot_token = config.get('bot_token')
        self.chat_ids = config.get('chat_ids', [])
    
    async def send(self, alert: Alert):
        """Send Telegram alert"""
        try:
            # Format message with Markdown
            message = f"""*[{alert.severity.value.upper()}] {alert.title}*

{alert.message}

_Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_""".strip()
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            async with aiohttp.ClientSession() as session:
                for chat_id in self.chat_ids:
                    payload = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'Markdown'
                    }
                    
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            logger.info(f"Telegram alert sent to {chat_id}")
                        else:
                            logger.error(f"Telegram send failed: {await response.text()}")
                            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")


class DiscordChannel:
    """Discord notification channel"""
    
    def __init__(self, config: Dict):
        self.webhook_url = config.get('webhook_url')
    
    async def send(self, alert: Alert):
        """Send Discord alert"""
        try:
            # Create Discord embed
            embed = {
                'title': alert.title,
                'description': alert.message,
                'color': self._get_color(alert.severity),
                'timestamp': alert.timestamp.isoformat(),
                'fields': []
            }
            
            if alert.symbol:
                embed['fields'].append({
                    'name': 'Symbol',
                    'value': alert.symbol,
                    'inline': True
                })
            
            payload = {
                'embeds': [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Discord alert sent: {alert.title}")
                    else:
                        logger.error(f"Discord send failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    def _get_color(self, severity: AlertSeverity) -> int:
        """Get Discord embed color based on severity"""
        colors = {
            AlertSeverity.CRITICAL: 0xFF0000,  # Red
            AlertSeverity.HIGH: 0xFF8C00,  # Dark Orange
            AlertSeverity.MEDIUM: 0xFFD700,  # Gold
            AlertSeverity.LOW: 0x00CED1,  # Dark Turquoise
            AlertSeverity.INFO: 0x4169E1  # Royal Blue
        }
        return colors.get(severity, 0x808080)  # Gray default
