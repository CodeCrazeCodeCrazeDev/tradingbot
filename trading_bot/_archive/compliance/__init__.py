"""
compliance package
"""

try:
    from .fraud_detection import (
        AnomalyDetector,
        BestExecutionMonitor,
        ComplianceAlert,
        ComplianceEngine,
        ComplianceSeverity,
        ComplianceViolationType,
        PositionLimitMonitor,
        RegulatoryFramework,
        SpoofingDetector,
        TradeRecord,
        WashTradingDetector
    )
    from .trade_surveillance import (
        ComplianceViolation,
        SeverityLevel,
        SurveillanceMetrics,
        TradeRecord,
        TradeSurveillanceSystem,
        ViolationType
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in compliance: {e}')

__all__ = [
    'AnomalyDetector',
    'BestExecutionMonitor',
    'ComplianceAlert',
    'ComplianceEngine',
    'ComplianceSeverity',
    'ComplianceViolation',
    'ComplianceViolationType',
    'PositionLimitMonitor',
    'RegulatoryFramework',
    'SeverityLevel',
    'SpoofingDetector',
    'SurveillanceMetrics',
    'TradeRecord',
    'TradeSurveillanceSystem',
    'ViolationType',
    'WashTradingDetector',
]