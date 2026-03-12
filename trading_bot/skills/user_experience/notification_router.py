"""
Skill #99: Notification Router
==============================

Routes notifications to appropriate channels.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    """Notification message."""
    channel: str
    message: str
    priority: str
    sent_at: datetime


@dataclass
class RouterResult:
    """Notification routing result."""
    notifications_sent: List[Notification]
    failed_count: int
    trading_signal: str


class NotificationRouter:
    """Routes notifications to channels."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.channels = ['email', 'sms', 'push', 'slack', 'telegram']
            self.preferences: Dict[str, List[str]] = {}
            logger.info("NotificationRouter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_preferences(self, priority: str, channels: List[str]):
        """Set channel preferences for priority level."""
        try:
            self.preferences[priority] = channels
        except Exception as e:
            logger.error(f"Error in set_preferences: {e}")
            raise
    
    def route(self, message: str, priority: str = 'medium') -> RouterResult:
        """Route notification to appropriate channels."""
        try:
            channels = self.preferences.get(priority, ['push'])
            notifications = []
            failed = 0
        
            for channel in channels:
                if channel in self.channels:
                    notifications.append(Notification(channel, message, priority, datetime.now()))
                else:
                    failed += 1
        
            return RouterResult(
                notifications_sent=notifications, failed_count=failed,
                trading_signal=f"NOTIFIED: {len(notifications)} channels, {failed} failed"
            )
        except Exception as e:
            logger.error(f"Error in route: {e}")
            raise
