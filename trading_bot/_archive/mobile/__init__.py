"""
mobile package
"""

try:
    from .pwa_alerts import (
        Alert,
        AlertChannel,
        AlertPriority,
        AlertStatus,
        PWAAlertSystem,
        PushSubscription
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in mobile: {e}')

__all__ = [
    'Alert',
    'AlertChannel',
    'AlertPriority',
    'AlertStatus',
    'PWAAlertSystem',
    'PushSubscription',
]