"""
Multi-Channel Notification Manager
Sends trading alerts via multiple channels
"""

import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification channels"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    DISCORD = "discord"
    SLACK = "slack"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationMessage:
    """Notification message structure"""
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    emoji: Optional[str] = None


class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send Telegram notification"""
        if not self.enabled:
            logger.warning("Telegram not configured")
            return False
        try:
        
            
            emoji = message.emoji or self._get_priority_emoji(message.priority)
            text = f"{emoji} *{message.title}*\n\n{message.message}"
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False
    
    def _get_priority_emoji(self, priority: NotificationPriority) -> str:
        """Get emoji for priority"""
        emojis = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "⚠️",
            NotificationPriority.HIGH: "🚨",
            NotificationPriority.CRITICAL: "🔥"
        }
        return emojis.get(priority, "📢")


class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, to_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.to_email = to_email
        self.enabled = all([smtp_server, username, password, to_email])
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send email notification"""
        if not self.enabled:
            logger.warning("Email not configured")
            return False
        try:
        
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = self.to_email
            msg['Subject'] = f"[{message.priority.value.upper()}] {message.title}"
            
            body = f"""
            <html>
            <body>
                <h2>{message.title}</h2>
                <p><strong>Priority:</strong> {message.priority.value.upper()}</p>
                <p><strong>Time:</strong> {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{message.message.replace(chr(10), '<br>')}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False


class SMSNotifier:
    """SMS notification handler (Twilio)"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_number = to_number
        self.enabled = all([account_sid, auth_token, from_number, to_number])
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send SMS notification"""
        if not self.enabled:
            logger.warning("SMS not configured")
            return False
        try:
        
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            text = f"[{message.priority.value.upper()}] {message.title}\n{message.message[:140]}"
            
            client.messages.create(
                body=text,
                from_=self.from_number,
                to=self.to_number
            )
            
            return True
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return False


class DiscordNotifier:
    """Discord notification handler"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send Discord notification"""
        if not self.enabled:
            logger.warning("Discord not configured")
            return False
        try:
        
            
            color = self._get_priority_color(message.priority)
            
            payload = {
                "embeds": [{
                    "title": message.title,
                    "description": message.message,
                    "color": color,
                    "timestamp": message.timestamp.isoformat(),
                    "footer": {"text": f"Priority: {message.priority.value.upper()}"}
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 204
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return False
    
    def _get_priority_color(self, priority: NotificationPriority) -> int:
        """Get color for priority"""
        colors = {
            NotificationPriority.LOW: 0x3498db,      # Blue
            NotificationPriority.MEDIUM: 0xf39c12,   # Orange
            NotificationPriority.HIGH: 0xe74c3c,     # Red
            NotificationPriority.CRITICAL: 0x8b0000  # Dark Red
        }
        return colors.get(priority, 0x95a5a6)


class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send Slack notification"""
        if not self.enabled:
            logger.warning("Slack not configured")
            return False
        try:
        
            
            emoji = message.emoji or self._get_priority_emoji(message.priority)
            
            payload = {
                "text": f"{emoji} *{message.title}*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": message.title}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message.message}
                    },
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"*Priority:* {message.priority.value.upper()}"},
                            {"type": "mrkdwn", "text": f"*Time:* {message.timestamp.strftime('%H:%M:%S')}"}
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False
    
    def _get_priority_emoji(self, priority: NotificationPriority) -> str:
        """Get emoji for priority"""
        emojis = {
            NotificationPriority.LOW: ":information_source:",
            NotificationPriority.MEDIUM: ":warning:",
            NotificationPriority.HIGH: ":rotating_light:",
            NotificationPriority.CRITICAL: ":fire:"
        }
        return emojis.get(priority, ":bell:")


class PushNotifier:
    """Push notification handler (Pushover)"""
    
    def __init__(self, user_key: str, api_token: str):
        self.user_key = user_key
        self.api_token = api_token
        self.enabled = all([user_key, api_token])
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send push notification"""
        if not self.enabled:
            logger.warning("Push notifications not configured")
            return False
        try:
        
            
            priority = self._get_pushover_priority(message.priority)
            
            payload = {
                "token": self.api_token,
                "user": self.user_key,
                "title": message.title,
                "message": message.message,
                "priority": priority
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.pushover.net/1/messages.json", data=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Push notification failed: {e}")
            return False
    
    def _get_pushover_priority(self, priority: NotificationPriority) -> int:
        """Convert to Pushover priority"""
        priorities = {
            NotificationPriority.LOW: -1,
            NotificationPriority.MEDIUM: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.CRITICAL: 2
        }
        return priorities.get(priority, 0)


class NotificationManager:
    """
    Central notification manager
    Sends notifications via multiple channels
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize notification manager"""
        self.config = config or {}
        
        # Initialize notifiers
        self.notifiers = {}
        self._init_notifiers()
        
        # Notification history
        self.history = []
        self.max_history = 1000
    
    def _init_notifiers(self):
        """Initialize all notifiers"""
        # Telegram
        if 'telegram' in self.config:
            self.notifiers[NotificationChannel.TELEGRAM] = TelegramNotifier(
                bot_token=self.config['telegram'].get('bot_token'),
                chat_id=self.config['telegram'].get('chat_id')
            )
        
        # Email
        if 'email' in self.config:
            self.notifiers[NotificationChannel.EMAIL] = EmailNotifier(
                smtp_server=self.config['email'].get('smtp_server'),
                smtp_port=self.config['email'].get('smtp_port', 587),
                username=self.config['email'].get('username'),
                password=self.config['email'].get('password'),
                to_email=self.config['email'].get('to_email')
            )
        
        # SMS
        if 'sms' in self.config:
            self.notifiers[NotificationChannel.SMS] = SMSNotifier(
                account_sid=self.config['sms'].get('account_sid'),
                auth_token=self.config['sms'].get('auth_token'),
                from_number=self.config['sms'].get('from_number'),
                to_number=self.config['sms'].get('to_number')
            )
        
        # Discord
        if 'discord' in self.config:
            self.notifiers[NotificationChannel.DISCORD] = DiscordNotifier(
                webhook_url=self.config['discord'].get('webhook_url')
            )
        
        # Slack
        if 'slack' in self.config:
            self.notifiers[NotificationChannel.SLACK] = SlackNotifier(
                webhook_url=self.config['slack'].get('webhook_url')
            )
        
        # Push
        if 'push' in self.config:
            self.notifiers[NotificationChannel.PUSH] = PushNotifier(
                user_key=self.config['push'].get('user_key'),
                api_token=self.config['push'].get('api_token')
            )
    
    async def send(self, message: NotificationMessage) -> Dict[NotificationChannel, bool]:
        """Send notification via specified channels"""
        results = {}
        
        for channel in message.channels:
            if channel in self.notifiers:
                try:
                    success = await self.notifiers[channel].send(message)
                    results[channel] = success
                except Exception as e:
                    logger.error(f"Failed to send via {channel.value}: {e}")
                    results[channel] = False
            else:
                logger.warning(f"Channel {channel.value} not configured")
                results[channel] = False
        
        # Store in history
        self.history.append({
            'message': message,
            'results': results,
            'timestamp': datetime.now()
        })
        
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return results
    
    async def send_trade_alert(self, trade_data: Dict[str, Any], priority: NotificationPriority = NotificationPriority.MEDIUM):
        """Send trade alert"""
        emoji = "📈" if trade_data.get('direction') == 'LONG' else "📉"
        
        message = NotificationMessage(
            title=f"Trade {trade_data.get('action', 'OPENED')}",
            message=self._format_trade_message(trade_data),
            priority=priority,
            channels=[NotificationChannel.TELEGRAM, NotificationChannel.DISCORD],
            timestamp=datetime.now(),
            emoji=emoji
        )
        
        return await self.send(message)
    
    async def send_profit_alert(self, profit_data: Dict[str, Any]):
        """Send profit alert"""
        message = NotificationMessage(
            title="💰 Profit Target Hit!",
            message=self._format_profit_message(profit_data),
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.TELEGRAM, NotificationChannel.PUSH],
            timestamp=datetime.now(),
            emoji="💰"
        )
        
        return await self.send(message)
    
    async def send_loss_alert(self, loss_data: Dict[str, Any]):
        """Send loss alert"""
        message = NotificationMessage(
            title="⚠️ Stop Loss Hit",
            message=self._format_loss_message(loss_data),
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.TELEGRAM],
            timestamp=datetime.now(),
            emoji="⚠️"
        )
        
        return await self.send(message)
    
    async def send_system_alert(self, alert_message: str, priority: NotificationPriority = NotificationPriority.HIGH):
        """Send system alert"""
        message = NotificationMessage(
            title="🔧 System Alert",
            message=alert_message,
            priority=priority,
            channels=[NotificationChannel.TELEGRAM, NotificationChannel.EMAIL],
            timestamp=datetime.now(),
            emoji="🔧"
        )
        
        return await self.send(message)
    
    def _format_trade_message(self, trade_data: Dict[str, Any]) -> str:
        """Format trade message"""
        return f"""
Symbol: {trade_data.get('symbol')}
Direction: {trade_data.get('direction')}
Entry: {trade_data.get('entry_price')}
Stop Loss: {trade_data.get('stop_loss')}
Take Profit: {trade_data.get('take_profit')}
Position Size: {trade_data.get('position_size')} lots
Risk: {trade_data.get('risk_percent')}%
Confidence: {trade_data.get('confidence', 0)*100:.1f}%
        """.strip()
    
    def _format_profit_message(self, profit_data: Dict[str, Any]) -> str:
        """Format profit message"""
        return f"""
Symbol: {profit_data.get('symbol')}
Entry: {profit_data.get('entry_price')}
Exit: {profit_data.get('exit_price')}
Profit: ${profit_data.get('profit_usd'):.2f} ({profit_data.get('profit_pips')} pips)
ROI: {profit_data.get('roi_percent'):.2f}%
Duration: {profit_data.get('duration')}
        """.strip()
    
    def _format_loss_message(self, loss_data: Dict[str, Any]) -> str:
        """Format loss message"""
        return f"""
Symbol: {loss_data.get('symbol')}
Entry: {loss_data.get('entry_price')}
Exit: {loss_data.get('exit_price')}
Loss: ${loss_data.get('loss_usd'):.2f} ({loss_data.get('loss_pips')} pips)
Risk Managed: {loss_data.get('risk_percent')}%
        """.strip()


__all__ = [
    'NotificationManager',
    'NotificationChannel',
    'NotificationPriority',
    'NotificationMessage',
    'TelegramNotifier',
    'EmailNotifier',
    'SMSNotifier',
    'DiscordNotifier',
    'SlackNotifier',
    'PushNotifier'
]
