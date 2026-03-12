"""
Notification System - Multi-Channel Notifications

Sends notifications through various channels (email, desktop, SMS, webhooks)
when approval requests are created or decisions are made.
"""

import asyncio
import json
import logging
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    DESKTOP = "desktop"
    SMS = "sms"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class NotificationConfig:
    """Configuration for notifications"""
    enabled_channels: List[NotificationChannel]
    
    # Email config
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_from: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    
    # SMS config (optional)
    sms_provider: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_recipients: List[str] = None
    
    # Webhook config
    webhook_urls: List[str] = None
    
    # Notification rules
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_on_medium: bool = False
    notify_on_low: bool = False
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []
        if self.sms_recipients is None:
            self.sms_recipients = []
        if self.webhook_urls is None:
            self.webhook_urls = []


class NotificationSystem:
    """
    Multi-channel notification system for approval requests
    """
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        logger.info(f"Notification system initialized with channels: {[c.value for c in config.enabled_channels]}")
    
    async def start(self):
        """Start notification worker"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._notification_worker())
        logger.info("Notification worker started")
    
    async def stop(self):
        """Stop notification worker"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Notification worker stopped")
    
    async def notify_new_request(self, request):
        """Notify about new approval request"""
        from .approval_types import ApprovalPriority
        
        # Check if we should notify based on priority
        should_notify = False
        if request.priority == ApprovalPriority.CRITICAL and self.config.notify_on_critical:
            should_notify = True
        elif request.priority == ApprovalPriority.HIGH and self.config.notify_on_high:
            should_notify = True
        elif request.priority == ApprovalPriority.MEDIUM and self.config.notify_on_medium:
            should_notify = True
        elif request.priority == ApprovalPriority.LOW and self.config.notify_on_low:
            should_notify = True
        
        if not should_notify:
            return
        
        message = self._format_new_request_message(request)
        await self._send_notification(message, request.priority)
    
    async def notify_decision(self, request):
        """Notify about approval decision"""
        message = self._format_decision_message(request)
        await self._send_notification(message, request.priority)
    
    def _format_new_request_message(self, request) -> Dict[str, Any]:
        """Format new request notification message"""
        priority_emoji = {
            1: "🔴",  # CRITICAL
            2: "🟡",  # HIGH
            3: "🟢",  # MEDIUM
            4: "⚪",  # LOW
        }
        
        emoji = priority_emoji.get(request.priority.value, "⚪")
        
        return {
            'type': 'new_request',
            'subject': f"{emoji} New Approval Request: {request.title}",
            'body': f"""
New approval request requires your attention:

Request ID: {request.request_id}
Title: {request.title}
Category: {request.category.value}
Priority: {request.priority.name}
Risk Level: {request.risk_level.value.upper()}

Description:
{request.description}

Requested by: {request.requester} ({request.source_system})
Created: {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}

{f"Expires in: {request.time_remaining()}" if request.expires_at else "No expiration"}

To review and approve/reject this request:
- Web Dashboard: http://localhost:8080/approval/{request.request_id}
- CLI: python approve.py details {request.request_id}

---
AlphaAlgo Unified Approval System
""",
            'priority': request.priority.value,
            'request_id': request.request_id,
        }
    
    def _format_decision_message(self, request) -> Dict[str, Any]:
        """Format decision notification message"""
        status_emoji = {
            'approved': '✅',
            'rejected': '❌',
            'conditional': '⚠️',
            'expired': '⏰',
            'cancelled': '🚫',
        }
        
        emoji = status_emoji.get(request.status.value, '❓')
        
        decision_text = ""
        if request.decision:
            decision_text = f"""
Decision: {request.status.value.upper()}
Decided by: {request.decision.approver}
Decided at: {request.decision.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Reason: {request.decision.reason or 'N/A'}
"""
            if request.decision.conditions:
                decision_text += f"\nConditions:\n"
                for condition in request.decision.conditions:
                    decision_text += f"  - {condition}\n"
        
        return {
            'type': 'decision',
            'subject': f"{emoji} Approval Decision: {request.title}",
            'body': f"""
Approval request has been decided:

Request ID: {request.request_id}
Title: {request.title}
Category: {request.category.value}

{decision_text}

---
AlphaAlgo Unified Approval System
""",
            'priority': request.priority.value,
            'request_id': request.request_id,
            'status': request.status.value,
        }
    
    async def _send_notification(self, message: Dict[str, Any], priority):
        """Queue notification for sending"""
        await self.notification_queue.put((message, priority))
    
    async def _notification_worker(self):
        """Background worker to send notifications"""
        while self._running:
            try:
                message, priority = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )
                
                # Send through all enabled channels
                tasks = []
                for channel in self.config.enabled_channels:
                    if channel == NotificationChannel.EMAIL:
                        tasks.append(self._send_email(message))
                    elif channel == NotificationChannel.DESKTOP:
                        tasks.append(self._send_desktop(message))
                    elif channel == NotificationChannel.SMS:
                        tasks.append(self._send_sms(message))
                    elif channel == NotificationChannel.WEBHOOK:
                        tasks.append(self._send_webhook(message))
                    elif channel == NotificationChannel.LOG:
                        tasks.append(self._send_log(message))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Notification worker error: {e}")
    
    async def _send_email(self, message: Dict[str, Any]):
        """Send email notification"""
        if not self.config.email_recipients:
            return
        try:
        
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = message['subject']
            
            msg.attach(MIMEText(message['body'], 'plain'))
            
            # Send email in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email_sync,
                msg
            )
            
            logger.info(f"Email notification sent: {message['subject']}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def _send_email_sync(self, msg: MIMEMultipart):
        """Send email synchronously"""
        with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
            server.starttls()
            if self.config.email_password:
                server.login(self.config.email_from, self.config.email_password)
            server.send_message(msg)
    
    async def _send_desktop(self, message: Dict[str, Any]):
        """Send desktop notification"""
        try:
            try:
                # Try to use plyer for cross-platform notifications
                from plyer import notification
                notification.notify(
                    title=message['subject'],
                    message=message['body'][:200],  # Truncate for desktop
                    app_name='AlphaAlgo',
                    timeout=10,
                )
                logger.info(f"Desktop notification sent: {message['subject']}")
            except ImportError:
                try:
                    pass
                # Fallback to Windows toast notification

                except Exception:
                    pass
            try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(
                        message['subject'],
                        message['body'][:200],
                        duration=10,
                        threaded=True,
                    )
                    logger.info(f"Windows toast notification sent: {message['subject']}")
            except ImportError:
                    logger.warning("Desktop notifications not available (install plyer or win10toast)")
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
    
    async def _send_sms(self, message: Dict[str, Any]):
        """Send SMS notification (requires SMS provider)"""
        if not self.config.sms_provider or not self.config.sms_recipients:
            return
        try:
        
            # Placeholder for SMS integration
            # You would integrate with Twilio, AWS SNS, or other SMS provider here
            logger.info(f"SMS notification would be sent: {message['subject']}")
            logger.warning("SMS notifications not implemented - configure SMS provider")
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
    
    async def _send_webhook(self, message: Dict[str, Any]):
        """Send webhook notification"""
        if not self.config.webhook_urls:
            return
        try:
        
            import aiohttp
            
            payload = {
                'type': message['type'],
                'subject': message['subject'],
                'body': message['body'],
                'priority': message['priority'],
                'request_id': message.get('request_id'),
                'status': message.get('status'),
            }
            
            async with aiohttp.ClientSession() as session:
                for url in self.config.webhook_urls:
                    try:
                        async with session.post(url, json=payload, timeout=5) as resp:
                            if resp.status == 200:
                                logger.info(f"Webhook notification sent to {url}")
                            else:
                                logger.warning(f"Webhook returned status {resp.status}: {url}")
                    except Exception as e:
                        logger.error(f"Failed to send webhook to {url}: {e}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    async def _send_log(self, message: Dict[str, Any]):
        """Log notification"""
        logger.info(f"NOTIFICATION: {message['subject']}")
        logger.debug(f"Body: {message['body']}")


def create_notification_system(config_path: Optional[Path] = None) -> NotificationSystem:
    """Create notification system from config file"""
    if config_path and config_path.exists():
        with open(config_path) as f:
            import yaml
            config_dict = yaml.safe_load(f)
            
            # Parse config
            enabled_channels = [
                NotificationChannel(ch) for ch in config_dict.get('enabled_channels', ['log'])
            ]
            
            config = NotificationConfig(
                enabled_channels=enabled_channels,
                email_smtp_server=config_dict.get('email', {}).get('smtp_server', 'smtp.gmail.com'),
                email_smtp_port=config_dict.get('email', {}).get('smtp_port', 587),
                email_from=config_dict.get('email', {}).get('from', ''),
                email_password=config_dict.get('email', {}).get('password', ''),
                email_recipients=config_dict.get('email', {}).get('recipients', []),
                notify_on_critical=config_dict.get('rules', {}).get('notify_on_critical', True),
                notify_on_high=config_dict.get('rules', {}).get('notify_on_high', True),
                notify_on_medium=config_dict.get('rules', {}).get('notify_on_medium', False),
                notify_on_low=config_dict.get('rules', {}).get('notify_on_low', False),
            )
    else:
        # Default config - log only
        config = NotificationConfig(
            enabled_channels=[NotificationChannel.LOG],
            notify_on_critical=True,
            notify_on_high=True,
        )
    
    return NotificationSystem(config)
