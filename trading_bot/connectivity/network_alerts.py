"""
Network Alert System
Sends alerts via email, SMS, and Telegram for network issues.
"""

import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime
try:
    import aiohttp
except ImportError:
    aiohttp = None
import json

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class NetworkAlertSystem:
    """
    Alert system for network monitoring.
    
    Supports:
    - Email alerts
    - Telegram notifications
    - SMS alerts (via Twilio)
    - Webhook notifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize alert system."""
        self.config = config
        
        # Email settings
        self.email_enabled = config.get('email', {}).get('enabled', False)
        self.email_from = config.get('email', {}).get('from_address', '')
        self.email_to = config.get('email', {}).get('to_address', '')
        self.smtp_host = config.get('email', {}).get('smtp_host', 'smtp.gmail.com')
        self.smtp_port = config.get('email', {}).get('smtp_port', 587)
        self.smtp_user = config.get('email', {}).get('smtp_user', '')
        self.smtp_password = config.get('email', {}).get('smtp_password', '')
        
        # Telegram settings
        self.telegram_enabled = config.get('telegram', {}).get('enabled', False)
        self.telegram_bot_token = config.get('telegram', {}).get('bot_token', '')
        self.telegram_chat_id = config.get('telegram', {}).get('chat_id', '')
        
        # SMS settings (Twilio)
        self.sms_enabled = config.get('sms', {}).get('enabled', False)
        self.twilio_account_sid = config.get('sms', {}).get('account_sid', '')
        self.twilio_auth_token = config.get('sms', {}).get('auth_token', '')
        self.twilio_from_number = config.get('sms', {}).get('from_number', '')
        self.twilio_to_number = config.get('sms', {}).get('to_number', '')
        
        # Webhook settings
        self.webhook_enabled = config.get('webhook', {}).get('enabled', False)
        self.webhook_url = config.get('webhook', {}).get('url', '')
        
        # Alert throttling
        self.last_alert_time = {}
        self.min_alert_interval_seconds = config.get('min_alert_interval_seconds', 300)  # 5 minutes
        
        logger.info("NetworkAlertSystem initialized")
        logger.info(f"Email: {self.email_enabled}, Telegram: {self.telegram_enabled}, SMS: {self.sms_enabled}")
    
    async def send_alert(self, alert: Dict[str, Any]):
        """
        Send alert through all enabled channels.
        
        Args:
            alert: Alert dictionary with keys:
                - level: INFO, WARNING, CRITICAL
                - message: Alert message
                - timestamp: ISO timestamp
                - network_status: Current network status
                - trading_mode: Current trading mode
        """
        level = alert.get('level', 'INFO')
        message = alert.get('message', '')
        
        # Check throttling
        if not self._should_send_alert(level, message):
            logger.debug(f"Alert throttled: {message}")
            return
        
        # Send through all enabled channels
        tasks = []
        
        if self.email_enabled:
            tasks.append(self._send_email(alert))
        
        if self.telegram_enabled:
            tasks.append(self._send_telegram(alert))
        
        if self.sms_enabled and level == 'CRITICAL':
            # Only send SMS for critical alerts
            tasks.append(self._send_sms(alert))
        
        if self.webhook_enabled:
            tasks.append(self._send_webhook(alert))
        
        # Execute all tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Alert channel {i} failed: {result}")
        
        # Update last alert time
        self.last_alert_time[level] = datetime.now()
    
    def _should_send_alert(self, level: str, message: str) -> bool:
        """Check if alert should be sent based on throttling."""
        # Always send critical alerts
        if level == 'CRITICAL':
            return True
        
        # Check last alert time
        last_time = self.last_alert_time.get(level)
        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < self.min_alert_interval_seconds:
                return False
        
        return True
    
    async def _send_email(self, alert: Dict[str, Any]):
        """Send email alert."""
        level = alert.get('level', 'INFO')
        message = alert.get('message', '')
        timestamp = alert.get('timestamp', datetime.now().isoformat())
        network_status = alert.get('network_status', 'unknown')
        trading_mode = alert.get('trading_mode', 'unknown')
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg['Subject'] = f"[{level}] AlphaAlgo Network Alert"
        
        # Email body
        body = f"""
AlphaAlgo Network Alert

Level: {level}
Time: {timestamp}
Network Status: {network_status}
Trading Mode: {trading_mode}

Message:
{message}

---
This is an automated alert from AlphaAlgo Trading Bot.
"""
        
        try:
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {level}")
        
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            raise
    
    async def _send_telegram(self, alert: Dict[str, Any]):
        """Send Telegram alert."""
        try:
            level = alert.get('level', 'INFO')
            message = alert.get('message', '')
            
            # Format message with emoji
            emoji = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'CRITICAL': '🚨'
            }.get(level, '📢')
            
            telegram_message = f"{emoji} *{level}*\n\n{message}"
            
            # Send via Telegram API
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    'chat_id': self.telegram_chat_id,
                    'text': telegram_message,
                    'parse_mode': 'Markdown'
                }) as response:
                    if response.status == 200:
                        logger.info(f"Telegram alert sent: {level}")
                    else:
                        logger.error(f"Telegram API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            raise
    
    async def _send_sms(self, alert: Dict[str, Any]):
        """Send SMS alert via Twilio."""
        try:
            level = alert.get('level', 'INFO')
            message = alert.get('message', '')
            
            # Truncate message for SMS (160 chars)
            sms_message = f"[{level}] {message}"[:160]
            
            # Send via Twilio API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            
            auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(url, data={
                    'From': self.twilio_from_number,
                    'To': self.twilio_to_number,
                    'Body': sms_message
                }) as response:
                    if response.status == 201:
                        logger.info(f"SMS alert sent: {level}")
                    else:
                        logger.error(f"Twilio API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            raise
    
    async def _send_webhook(self, alert: Dict[str, Any]):
        """Send webhook notification."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=alert) as response:
                    if response.status == 200:
                        logger.info("Webhook alert sent")
                    else:
                        logger.error(f"Webhook error: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            raise


def create_alert_callback(alert_system: NetworkAlertSystem):
    """Create alert callback for network monitor."""
    async def callback(alert: Dict[str, Any]):
        await alert_system.send_alert(alert)
    
    return callback
