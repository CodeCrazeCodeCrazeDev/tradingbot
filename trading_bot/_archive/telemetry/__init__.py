"""
telemetry package
"""

try:
    from .health import (
        ComponentHealth,
        HealthChecker,
        HealthStatus,
        get_health_checker,
        liveness_probe,
        readiness_probe,
        retry
    )
    from .logging_config import (
        ColoredFormatter,
        LogLevel,
        StructuredFormatter,
        StructuredLogger,
        get_logger,
        log_risk_event,
        log_signal,
        log_trade,
        setup_logging
    )
    from .metrics import (
        MetricType,
        MetricsCollector,
        SystemMetrics,
        TradingMetrics,
        get_metrics_collector,
        timed
    )
    from .tracing import (
        Span,
        Tracer,
        get_tracer,
        trace
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in telemetry: {e}')

__all__ = [
    'ColoredFormatter',
    'ComponentHealth',
    'HealthChecker',
    'HealthStatus',
    'LogLevel',
    'MetricType',
    'MetricsCollector',
    'Span',
    'StructuredFormatter',
    'StructuredLogger',
    'SystemMetrics',
    'Tracer',
    'TradingMetrics',
    'get_health_checker',
    'get_logger',
    'get_metrics_collector',
    'get_tracer',
    'liveness_probe',
    'log_risk_event',
    'log_signal',
    'log_trade',
    'readiness_probe',
    'retry',
    'setup_logging',
    'timed',
    'trace',
]