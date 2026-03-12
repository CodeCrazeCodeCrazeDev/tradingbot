"""
from typing import List, Optional, Set
Notification and Reporting Service

Complete notification infrastructure:
- Email notifications
- SMS alerts (Twilio)
- Telegram bot
- Slack integration
- Discord webhooks
- Scheduled reports (daily/weekly/monthly)
"""

import asyncio
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import os
import io

logger = logging.getLogger(__name__)

# Optional imports
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ReportType(Enum):
    """Report types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TRADE_SUMMARY = "trade_summary"
    PERFORMANCE = "performance"
    RISK = "risk"


@dataclass
class Notification:
    """Notification data"""
    notification_id: str
    channel: NotificationChannel
    priority: NotificationPriority
    subject: str
    message: str
    recipient: str
    timestamp: datetime = field(default_factory=datetime.now)
    sent: bool = False
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'notification_id': self.notification_id,
            'channel': self.channel.value,
            'priority': self.priority.value,
            'subject': self.subject,
            'message': self.message,
            'recipient': self.recipient,
            'timestamp': self.timestamp.isoformat(),
            'sent': self.sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error': self.error
        }


class EmailNotifier:
    """Email notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_addr = config.get('from_addr', self.username)
        self.use_tls = config.get('use_tls', True)
        
        logger.info("EmailNotifier initialized")
    
    async def send(
        self,
        to_addr: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """Send email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            
            # Plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # HTML
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename={attachment['filename']}"
                    )
                    msg.attach(part)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_addr}")
            return True
            
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False


class SMSNotifier:
    """SMS notification service using Twilio"""
    
    def __init__(self, config: Dict[str, Any]):
        self.account_sid = config.get('account_sid')
        self.auth_token = config.get('auth_token')
        self.from_number = config.get('from_number')
        
        if TWILIO_AVAILABLE and self.account_sid and self.auth_token:
            self.client = TwilioClient(self.account_sid, self.auth_token)
        else:
            self.client = None
        
        logger.info("SMSNotifier initialized")
    
    async def send(self, to_number: str, message: str) -> bool:
        """Send SMS"""
        if not self.client:
            logger.warning("Twilio client not available")
            return False
        try:
        
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}")
            return True
            
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return False


class TelegramNotifier:
    """Telegram bot notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.bot_token = config.get('bot_token')
        self.default_chat_id = config.get('chat_id')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        logger.info("TelegramNotifier initialized")
    
    async def send(
        self,
        message: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """Send Telegram message"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available")
            return False
        
        chat_id = chat_id or self.default_chat_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": parse_mode
                    }
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Telegram message sent to {chat_id}")
                        return True
                    else:
                        logger.error(f"Telegram send failed: {resp.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False
    
    async def send_document(
        self,
        document: bytes,
        filename: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> bool:
        """Send document via Telegram"""
        if not AIOHTTP_AVAILABLE:
            return False
        
        chat_id = chat_id or self.default_chat_id
        
        try:
            data = aiohttp.FormData()
            data.add_field('chat_id', chat_id)
            data.add_field('document', document, filename=filename)
            if caption:
                data.add_field('caption', caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendDocument",
                    data=data
                ) as resp:
                    return resp.status == 200
                    
        except Exception as e:
            logger.error(f"Telegram document send failed: {e}")
            return False


class SlackNotifier:
    """Slack notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get('webhook_url')
        self.default_channel = config.get('channel', '#trading')
        
        logger.info("SlackNotifier initialized")
    
    async def send(
        self,
        message: str,
        channel: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """Send Slack message"""
        if not AIOHTTP_AVAILABLE or not self.webhook_url:
            return False
        try:
        
            payload = {
                "channel": channel or self.default_channel,
                "text": message
            }
            
            if attachments:
                payload["attachments"] = attachments
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.info("Slack message sent")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False


class DiscordNotifier:
    """Discord webhook notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get('webhook_url')
        
        logger.info("DiscordNotifier initialized")
    
    async def send(
        self,
        message: str,
        username: str = "AlphaAlgo Bot",
        embeds: Optional[List[Dict]] = None
    ) -> bool:
        """Send Discord message"""
        if not AIOHTTP_AVAILABLE or not self.webhook_url:
            return False
        try:
        
            payload = {
                "username": username,
                "content": message
            }
            
            if embeds:
                payload["embeds"] = embeds
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as resp:
                    if resp.status in [200, 204]:
                        logger.info("Discord message sent")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return False


class ReportGenerator:
    """Generate trading reports"""
    
    def __init__(self, database=None):
        self.database = database
    
    async def generate_daily_report(self, date: Optional[datetime] = None) -> Dict:
        """Generate daily trading report"""
        date = date or datetime.now()
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        report = {
            'report_type': 'daily',
            'date': date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'trades': [],
            'performance': {}
        }
        
        if self.database:
            # Get trades
            trades = await self.database.get_trades(
                start_time=start,
                end_time=end
            )
            report['trades'] = trades
            
            # Get statistics
            stats = await self.database.get_trade_statistics(
                start_time=start,
                end_time=end
            )
            report['summary'] = stats
        
        return report
    
    async def generate_weekly_report(self, week_start: Optional[datetime] = None) -> Dict:
        """Generate weekly trading report"""
        if week_start is None:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
        
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        report = {
            'report_type': 'weekly',
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'daily_breakdown': [],
            'top_performers': [],
            'worst_performers': []
        }
        
        if self.database:
            stats = await self.database.get_trade_statistics(
                start_time=week_start,
                end_time=week_end
            )
            report['summary'] = stats
        
        return report
    
    async def generate_monthly_report(self, month: Optional[datetime] = None) -> Dict:
        """Generate monthly trading report"""
        if month is None:
            month = datetime.now()
        
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            month_end = month_start.replace(year=month.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month.month + 1)
        
        report = {
            'report_type': 'monthly',
            'month': month_start.strftime('%Y-%m'),
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'weekly_breakdown': [],
            'symbol_performance': {},
            'strategy_performance': {}
        }
        
        if self.database:
            stats = await self.database.get_trade_statistics(
                start_time=month_start,
                end_time=month_end
            )
            report['summary'] = stats
        
        return report
    
    def format_report_text(self, report: Dict) -> str:
        """Format report as text"""
        lines = []
        
        report_type = report.get('report_type', 'unknown').upper()
        lines.append(f"📊 {report_type} TRADING REPORT")
        lines.append("=" * 40)
        
        if 'date' in report:
            lines.append(f"Date: {report['date']}")
        elif 'week_start' in report:
            lines.append(f"Week: {report['week_start']} to {report['week_end']}")
        elif 'month' in report:
            lines.append(f"Month: {report['month']}")
        
        lines.append("")
        
        summary = report.get('summary', {})
        if summary:
            lines.append("📈 SUMMARY")
            lines.append("-" * 20)
            lines.append(f"Total Trades: {summary.get('total_trades', 0)}")
            lines.append(f"Winning Trades: {summary.get('winning_trades', 0)}")
            lines.append(f"Losing Trades: {summary.get('losing_trades', 0)}")
            lines.append(f"Win Rate: {summary.get('win_rate', 0):.1f}%")
            lines.append(f"Total P&L: ${summary.get('total_pnl', 0):,.2f}")
            lines.append(f"Average P&L: ${summary.get('average_pnl', 0):,.2f}")
        
        lines.append("")
        lines.append(f"Generated: {report.get('generated_at', '')}")
        
        return "\n".join(lines)
    
    def format_report_html(self, report: Dict) -> str:
        """Format report as HTML"""
        summary = report.get('summary', {})
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .metric {{ margin: 10px 0; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>📊 {report.get('report_type', '').upper()} TRADING REPORT</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">Total Trades: <strong>{summary.get('total_trades', 0)}</strong></div>
                <div class="metric">Win Rate: <strong>{summary.get('win_rate', 0):.1f}%</strong></div>
                <div class="metric">Total P&L: <strong class="{'positive' if summary.get('total_pnl', 0) >= 0 else 'negative'}">${summary.get('total_pnl', 0):,.2f}</strong></div>
            </div>
            
            <p><small>Generated: {report.get('generated_at', '')}</small></p>
        </body>
        </html>
        """
        
        return html


class NotificationService:
    """
    Unified notification service.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize notifiers
        self.email = None
        self.sms = None
        self.telegram = None
        self.slack = None
        self.discord = None
        
        if 'email' in self.config:
            self.email = EmailNotifier(self.config['email'])
        
        if 'sms' in self.config:
            self.sms = SMSNotifier(self.config['sms'])
        
        if 'telegram' in self.config:
            self.telegram = TelegramNotifier(self.config['telegram'])
        
        if 'slack' in self.config:
            self.slack = SlackNotifier(self.config['slack'])
        
        if 'discord' in self.config:
            self.discord = DiscordNotifier(self.config['discord'])
        
        # Report generator
        self.report_generator = ReportGenerator()
        
        # Notification history
        self.history: List[Notification] = []
        self.max_history = self.config.get('max_history', 1000)
        
        # Scheduled reports
        self._scheduler_task: Optional[asyncio.Task] = None
        self.scheduled_reports: List[Dict] = []
        
        logger.info("NotificationService initialized")
    
    def set_database(self, database):
        """Set database for report generation"""
        self.report_generator.database = database
    
    async def send(
        self,
        channel: NotificationChannel,
        subject: str,
        message: str,
        recipient: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Send notification"""
        import uuid
        
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            channel=channel,
            priority=priority,
            subject=subject,
            message=message,
            recipient=recipient,
            metadata=kwargs
        )
        
        success = False
        
        try:
            if channel == NotificationChannel.EMAIL and self.email:
                success = await self.email.send(
                    recipient, subject, message,
                    html_body=kwargs.get('html_body'),
                    attachments=kwargs.get('attachments')
                )
            
            elif channel == NotificationChannel.SMS and self.sms:
                success = await self.sms.send(recipient, message)
            
            elif channel == NotificationChannel.TELEGRAM and self.telegram:
                success = await self.telegram.send(message, chat_id=recipient)
            
            elif channel == NotificationChannel.SLACK and self.slack:
                success = await self.slack.send(message, channel=recipient)
            
            elif channel == NotificationChannel.DISCORD and self.discord:
                success = await self.discord.send(message)
            
            notification.sent = success
            notification.sent_at = datetime.now() if success else None
            
        except Exception as e:
            notification.error = str(e)
            logger.error(f"Notification failed: {e}")
        
        # Store in history
        self.history.append(notification)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return success
    
    async def send_trade_notification(
        self,
        trade_data: Dict,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """Send trade notification"""
        channels = channels or [NotificationChannel.TELEGRAM]
        
        # Format message
        symbol = trade_data.get('symbol', 'Unknown')
        side = trade_data.get('side', 'Unknown')
        pnl = trade_data.get('pnl', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        message = f"""
{emoji} *Trade Closed*

Symbol: {symbol}
Side: {side.upper()}
P&L: ${pnl:,.2f}
        """.strip()
        
        for channel in channels:
            await self.send(
                channel=channel,
                subject=f"Trade: {symbol}",
                message=message,
                recipient=self.config.get(channel.value, {}).get('default_recipient', ''),
                priority=NotificationPriority.NORMAL
            )
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning",
        channels: Optional[List[NotificationChannel]] = None
    ):
        """Send alert notification"""
        channels = channels or [NotificationChannel.TELEGRAM, NotificationChannel.SLACK]
        
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = emoji_map.get(severity, "📢")
        
        formatted_message = f"""
{emoji} *{title}*

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        priority = NotificationPriority.URGENT if severity == "critical" else NotificationPriority.HIGH
        
        for channel in channels:
            await self.send(
                channel=channel,
                subject=title,
                message=formatted_message,
                recipient=self.config.get(channel.value, {}).get('default_recipient', ''),
                priority=priority
            )
    
    async def send_report(
        self,
        report_type: ReportType,
        channels: Optional[List[NotificationChannel]] = None,
        **kwargs
    ):
        """Generate and send report"""
        channels = channels or [NotificationChannel.EMAIL, NotificationChannel.TELEGRAM]
        
        # Generate report
        if report_type == ReportType.DAILY:
            report = await self.report_generator.generate_daily_report(kwargs.get('date'))
        elif report_type == ReportType.WEEKLY:
            report = await self.report_generator.generate_weekly_report(kwargs.get('week_start'))
        elif report_type == ReportType.MONTHLY:
            report = await self.report_generator.generate_monthly_report(kwargs.get('month'))
        else:
            report = {'report_type': report_type.value}
        
        # Format
        text_report = self.report_generator.format_report_text(report)
        html_report = self.report_generator.format_report_html(report)
        
        # Send
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                await self.send(
                    channel=channel,
                    subject=f"AlphaAlgo {report_type.value.title()} Report",
                    message=text_report,
                    recipient=self.config.get('email', {}).get('default_recipient', ''),
                    html_body=html_report
                )
            else:
                await self.send(
                    channel=channel,
                    subject=f"{report_type.value.title()} Report",
                    message=text_report,
                    recipient=self.config.get(channel.value, {}).get('default_recipient', '')
                )
    
    def schedule_report(
        self,
        report_type: ReportType,
        schedule: str,  # "daily", "weekly", "monthly"
        time_of_day: str = "09:00",
        channels: Optional[List[NotificationChannel]] = None
    ):
        """Schedule recurring report"""
        self.scheduled_reports.append({
            'report_type': report_type,
            'schedule': schedule,
            'time_of_day': time_of_day,
            'channels': channels or [NotificationChannel.EMAIL],
            'last_sent': None
        })
        logger.info(f"Scheduled {report_type.value} report: {schedule} at {time_of_day}")
    
    async def start_scheduler(self):
        """Start report scheduler"""
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Report scheduler started")
    
    async def stop_scheduler(self):
        """Stop report scheduler"""
        if self._scheduler_task:
            self._scheduler_task.cancel()
        logger.info("Report scheduler stopped")
    
    async def _scheduler_loop(self):
        """Scheduler loop"""
        while True:
            try:
                now = datetime.now()
                
                for report_config in self.scheduled_reports:
                    should_send = self._should_send_report(report_config, now)
                    
                    if should_send:
                        await self.send_report(
                            report_config['report_type'],
                            report_config['channels']
                        )
                        report_config['last_sent'] = now
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def _should_send_report(self, config: Dict, now: datetime) -> bool:
        """Check if report should be sent"""
        time_parts = config['time_of_day'].split(':')
        target_hour = int(time_parts[0])
        target_minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        if now.hour != target_hour or now.minute != target_minute:
            return False
        
        last_sent = config.get('last_sent')
        if last_sent and (now - last_sent).total_seconds() < 3600:
            return False
        
        schedule = config['schedule']
        
        if schedule == 'daily':
            return True
        elif schedule == 'weekly' and now.weekday() == 0:  # Monday
            return True
        elif schedule == 'monthly' and now.day == 1:
            return True
        
        return False
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get notification history"""
        return [n.to_dict() for n in self.history[-limit:]]


# Export
__all__ = [
    'NotificationService',
    'NotificationChannel',
    'NotificationPriority',
    'ReportType',
    'ReportGenerator',
    'EmailNotifier',
    'SMSNotifier',
    'TelegramNotifier',
    'SlackNotifier',
    'DiscordNotifier'
]
