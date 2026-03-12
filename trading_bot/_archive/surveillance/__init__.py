"""
surveillance package
"""

try:
    from .trade_surveillance import TradeSurveillance, create_trade_surveillance
    from .trade_surveillance_impl import (
        AlertSeverity,
        ComplianceMonitor,
        ComplianceRule,
        LayeringDetector,
        ManipulationType,
        Order,
        SpoofingDetector,
        SurveillanceAlert,
        Trade,
        TradeSurveillanceSystem,
        WashTradingDetector,
        create_surveillance_system
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in surveillance: {e}')

__all__ = [
    'AlertSeverity',
    'ComplianceMonitor',
    'ComplianceRule',
    'LayeringDetector',
    'ManipulationType',
    'Order',
    'SpoofingDetector',
    'SurveillanceAlert',
    'Trade',
    'TradeSurveillance',
    'TradeSurveillanceSystem',
    'WashTradingDetector',
    'create_surveillance_system',
    'create_trade_surveillance',
]