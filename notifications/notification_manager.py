"""
Notification management system
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification priority levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    TELEGRAM = "telegram"
    SMS = "sms"
    WEBHOOK = "webhook"
    LOG = "log"


class NotificationManager:
    """
    Manages notifications across multiple channels.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Channel configurations
        self.email_config = self.config.get('email', {})
        self.telegram_config = self.config.get('telegram', {})
        self.sms_config = self.config.get('sms', {})
        self.webhook_config = self.config.get('webhook', {})
        
        # Notification history
        self.notifications = []
        
        # Rate limiting
        self.rate_limits = {
            NotificationLevel.INFO: 60,  # Max per hour
            NotificationLevel.WARNING: 30,
            NotificationLevel.ERROR: 20,
            NotificationLevel.CRITICAL: 10
        }
        
        logger.info("✅ Notification Manager initialized")
    
    async def send(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        channels: List[NotificationChannel] = None,
        metadata: Dict = None
    ):
        """Send notification to specified channels."""
        if channels is None:
            channels = [NotificationChannel.LOG]
        
        # Check rate limits
        if not self._check_rate_limit(level):
            logger.warning(f"⚠️ Rate limit exceeded for {level.value}")
            return
        
        # Record notification
        notification = {
            'message': message,
            'level': level,
            'channels': channels,
            'metadata': metadata or {},
            'timestamp': datetime.now()
        }
        self.notifications.append(notification)
        
        # Send to each channel
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                tasks.append(self._send_email(message, level, metadata))
            elif channel == NotificationChannel.TELEGRAM:
                tasks.append(self._send_telegram(message, level, metadata))
            elif channel == NotificationChannel.SMS:
                tasks.append(self._send_sms(message, level, metadata))
            elif channel == NotificationChannel.WEBHOOK:
                tasks.append(self._send_webhook(message, level, metadata))
            elif channel == NotificationChannel.LOG:
                self._send_log(message, level, metadata)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_email(self, message: str, level: NotificationLevel, metadata: Dict):
        """Send email notification."""
        if not self.email_config.get('enabled'):
            return
        
        try:
            # Placeholder for email sending logic
            logger.info(f"📧 Email notification: {message}")
        except Exception as e:
            logger.error(f"❌ Email send error: {e}")
    
    async def _send_telegram(self, message: str, level: NotificationLevel, metadata: Dict):
        """Send Telegram notification."""
        if not self.telegram_config.get('enabled'):
            return
        
        try:
            # Placeholder for Telegram sending logic
            logger.info(f"📱 Telegram notification: {message}")
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
    
    async def _send_sms(self, message: str, level: NotificationLevel, metadata: Dict):
        """Send SMS notification."""
        if not self.sms_config.get('enabled'):
            return
        
        try:
            # Placeholder for SMS sending logic
            logger.info(f"📲 SMS notification: {message}")
        except Exception as e:
            logger.error(f"❌ SMS send error: {e}")
    
    async def _send_webhook(self, message: str, level: NotificationLevel, metadata: Dict):
        """Send webhook notification."""
        if not self.webhook_config.get('enabled'):
            return
        
        try:
            # Placeholder for webhook sending logic
            logger.info(f"🔗 Webhook notification: {message}")
        except Exception as e:
            logger.error(f"❌ Webhook send error: {e}")
    
    def _send_log(self, message: str, level: NotificationLevel, metadata: Dict):
        """Send log notification."""
        if level == NotificationLevel.INFO:
            logger.info(f"ℹ️ {message}")
        elif level == NotificationLevel.WARNING:
            logger.warning(f"⚠️ {message}")
        elif level == NotificationLevel.ERROR:
            logger.error(f"❌ {message}")
        elif level == NotificationLevel.CRITICAL:
            logger.critical(f"🚨 {message}")
    
    def _check_rate_limit(self, level: NotificationLevel) -> bool:
        """Check if notification rate limit is exceeded."""
        from datetime import timedelta
        
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_count = len([
            n for n in self.notifications
            if n['level'] == level and n['timestamp'] > hour_ago
        ])
        
        return recent_count < self.rate_limits[level]
    
    async def notify_trade(self, symbol: str, side: str, quantity: float, price: float):
        """Send trade notification."""
        message = f"Trade executed: {side} {quantity} {symbol} @ {price}"
        await self.send(
            message,
            NotificationLevel.INFO,
            [NotificationChannel.LOG, NotificationChannel.TELEGRAM],
            {'symbol': symbol, 'side': side, 'quantity': quantity, 'price': price}
        )
    
    async def notify_error(self, error: str, context: Dict = None):
        """Send error notification."""
        message = f"Error: {error}"
        await self.send(
            message,
            NotificationLevel.ERROR,
            [NotificationChannel.LOG, NotificationChannel.EMAIL],
            context
        )
    
    async def notify_critical(self, message: str, context: Dict = None):
        """Send critical notification."""
        await self.send(
            message,
            NotificationLevel.CRITICAL,
            [NotificationChannel.LOG, NotificationChannel.EMAIL, NotificationChannel.TELEGRAM, NotificationChannel.SMS],
            context
        )
    
    def get_recent_notifications(self, hours: int = 24) -> List[Dict]:
        """Get recent notifications."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            n for n in self.notifications
            if n['timestamp'] > cutoff
        ]
