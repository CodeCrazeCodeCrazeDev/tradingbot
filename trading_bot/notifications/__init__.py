"""
Notifications Module
============================================================

Auto-generated integration file.
"""

# notification_manager
try:
    from .notification_manager import (
        NotificationManager,
    )
except ImportError as e:
    # notification_manager not available
    pass

# push_notifications
try:
    from .push_notifications import (
        PushNotificationManager,
    )
except ImportError as e:
    # push_notifications not available
    pass

__all__ = [
    'NotificationManager',
    'PushNotificationManager',
]
