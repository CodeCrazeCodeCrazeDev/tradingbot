"""
error_handling package
"""

try:
    from .advanced_error_handler import (
        BrokerConnectionError,
        CircuitBreaker,
        DataValidationError,
        ErrorCategory,
        ErrorContext,
        ErrorHandler,
        ErrorSeverity,
        ExecutionError,
        RateLimitError,
        RecoveryAction,
        RecoveryResult,
        RetryPolicy,
        RiskLimitError,
        TradingError,
        with_error_handling
    )
    from .circuit_breaker import CircuitBreaker, CircuitState, retry
    from .comprehensive_recovery import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerOpen,
        CircuitState,
        ErrorClassifier,
        ErrorContext,
        ErrorSeverity,
        FallbackRegistry,
        RecoveryAction,
        RecoveryOrchestrator,
        RetryPolicy,
        T,
        get_orchestrator,
        with_circuit_breaker,
        with_fallback,
        with_retry
    )
    from .health_monitor import HealthMonitor, HealthStatus, SystemComponent
    from .recovery_manager import RecoveryAction, RecoveryManager
    from .robust_error_handler import (
        CircuitBreaker,
        ErrorSeverity,
        ErrorType,
        RobustErrorHandler
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in error_handling: {e}')

__all__ = [
    'BrokerConnectionError',
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitBreakerOpen',
    'CircuitState',
    'DataValidationError',
    'ErrorCategory',
    'ErrorClassifier',
    'ErrorContext',
    'ErrorHandler',
    'ErrorSeverity',
    'ErrorType',
    'ExecutionError',
    'FallbackRegistry',
    'HealthMonitor',
    'HealthStatus',
    'RateLimitError',
    'RecoveryAction',
    'RecoveryManager',
    'RecoveryOrchestrator',
    'RecoveryResult',
    'RetryPolicy',
    'RiskLimitError',
    'RobustErrorHandler',
    'SystemComponent',
    'T',
    'TradingError',
    'get_orchestrator',
    'retry',
    'with_circuit_breaker',
    'with_error_handling',
    'with_fallback',
    'with_retry',
]