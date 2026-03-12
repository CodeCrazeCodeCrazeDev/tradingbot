"""
Owner Communication Channels

Centralized configuration for bot-to-owner communication.
All modules that need to contact the owner should use this module.

Channels:
- Email: petesonmwangi206@gmail.com
- Phone/SMS: +25479779156
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class OwnerContact:
    """Owner contact information."""
    email: str = "petesonmwangi206@gmail.com"
    phone: str = "+25479779156"
    telegram_chat_id: str = ""  # Set via env OWNER_TELEGRAM_CHAT_ID
    preferred_channel: str = "email"  # email, sms, telegram


# Singleton owner contact
OWNER = OwnerContact(
    telegram_chat_id=os.environ.get('OWNER_TELEGRAM_CHAT_ID', ''),
)


def get_notification_config() -> Dict[str, Any]:
    """
    Get notification service config pre-filled with owner details.
    
    Use this to initialize NotificationService with owner channels ready.
    """
    return {
        'email': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': OWNER.email,
            'password': os.environ.get('ALPHAALGO_EMAIL_PASSWORD', ''),
            'from_addr': OWNER.email,
            'use_tls': True,
        },
        'sms': {
            'account_sid': os.environ.get('TWILIO_ACCOUNT_SID', ''),
            'auth_token': os.environ.get('TWILIO_AUTH_TOKEN', ''),
            'from_number': os.environ.get('TWILIO_FROM_NUMBER', ''),
        },
        'telegram': {
            'bot_token': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': OWNER.telegram_chat_id,
        },
        'owner': {
            'email': OWNER.email,
            'phone': OWNER.phone,
            'telegram_chat_id': OWNER.telegram_chat_id,
        },
        'alert_levels': {
            'trade_executed': 'normal',
            'daily_summary': 'normal',
            'drawdown_warning': 'high',
            'risk_limit_breach': 'urgent',
            'system_error': 'urgent',
            'improvement_blocked': 'high',
            'safety_violation': 'urgent',
        },
    }


async def notify_owner(
    subject: str,
    message: str,
    priority: str = 'normal',
    notification_service: Optional[Any] = None,
):
    """
    Send a notification to the bot owner.
    
    Args:
        subject: Notification subject
        message: Notification body
        priority: 'low', 'normal', 'high', 'urgent'
        notification_service: Optional NotificationService instance
    """
    if notification_service is not None:
        try:
            await notification_service.send_notification(
                channel='email',
                recipient=OWNER.email,
                subject=f"[AlphaAlgo] {subject}",
                message=message,
                priority=priority,
            )
        except Exception as e:
            logger.error("Failed to send owner notification via service: %s", e)
    else:
        # Fallback: just log it
        logger.info(
            "OWNER NOTIFICATION [%s] %s: %s (to: %s / %s)",
            priority, subject, message, OWNER.email, OWNER.phone
        )


def get_owner_email() -> str:
    """Get owner email address."""
    return OWNER.email


def get_owner_phone() -> str:
    """Get owner phone number."""
    return OWNER.phone
