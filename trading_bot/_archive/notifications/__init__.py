"""
notifications package
"""

try:
    from .notification_manager import (
        DiscordNotifier,
        EmailNotifier,
        NotificationChannel,
        NotificationManager,
        NotificationMessage,
        NotificationPriority,
        PushNotifier,
        SMSNotifier,
        SlackNotifier,
        TelegramNotifier
    )
    from .notification_service import (
        DiscordNotifier,
        EmailNotifier,
        Notification,
        NotificationChannel,
        NotificationPriority,
        NotificationService,
        ReportGenerator,
        ReportType,
        SMSNotifier,
        SlackNotifier,
        TelegramNotifier
    )
    from .push_notifications import (
        APNSProvider,
        BasePushProvider,
        DeviceToken,
        FCMProvider,
        NotificationChannel,
        NotificationPriority,
        NotificationResult,
        PushConfig,
        PushNotification,
        PushNotificationManager,
        WebPushProvider,
        get_push_manager
    )
    from .telegram_bot import (
        NotificationType,
        TelegramBot,
        TelegramConfig,
        TelegramMessage,
        get_telegram_bot
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in notifications: {e}')

try:
    from .owner_channels import (
        OwnerContact,
        OWNER,
        get_notification_config,
        notify_owner,
        get_owner_email,
        get_owner_phone,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in notifications.owner_channels: {e}')

__all__ = [
    'APNSProvider',
    'BasePushProvider',
    'DeviceToken',
    'DiscordNotifier',
    'EmailNotifier',
    'FCMProvider',
    'Notification',
    'NotificationChannel',
    'NotificationManager',
    'NotificationMessage',
    'NotificationPriority',
    'NotificationResult',
    'NotificationService',
    'NotificationType',
    'OwnerContact',
    'OWNER',
    'PushConfig',
    'PushNotification',
    'PushNotificationManager',
    'PushNotifier',
    'ReportGenerator',
    'ReportType',
    'SMSNotifier',
    'SlackNotifier',
    'TelegramBot',
    'TelegramConfig',
    'TelegramMessage',
    'TelegramNotifier',
    'WebPushProvider',
    'get_notification_config',
    'get_owner_email',
    'get_owner_phone',
    'get_push_manager',
    'get_telegram_bot',
    'notify_owner',
]