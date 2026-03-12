"""
Advanced Error Handling System

Production-grade error handling:
- Structured error classification
- Recovery mechanisms
- Circuit breakers
- Graceful degradation
- Error logging and alerting
"""

import asyncio
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import sys
from collections import deque

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    BROKER = "broker"
    DATA = "data"
    VALIDATION = "validation"
    EXECUTION = "execution"
    RISK = "risk"
    ML_MODEL = "ml_model"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Recovery actions"""
    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    ALERT_AND_CONTINUE = "alert_and_continue"
    ESCALATE = "escalate"


@dataclass
class ErrorContext:
    """Context information for an error"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    exception: Exception
    message: str
    stack_trace: str
    component: str
    operation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    recovery_action: Optional[RecoveryAction] = None
    recovered: bool = False
    recovery_attempts: int = 0


@dataclass
class RecoveryResult:
    """Result of a recovery attempt"""
    success: bool
    action_taken: RecoveryAction
    attempts: int
    final_error: Optional[Exception] = None
    fallback_result: Any = None


class TradingError(Exception):
    """Base exception for trading errors"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = True,
        metadata: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.metadata = metadata or {}


class BrokerConnectionError(TradingError):
    """Broker connection error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.BROKER, **kwargs)


class DataValidationError(TradingError):
    """Data validation error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


class ExecutionError(TradingError):
    """Trade execution error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.EXECUTION, **kwargs)


class RiskLimitError(TradingError):
    """Risk limit exceeded error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RISK, severity=ErrorSeverity.WARNING, **kwargs)


class RateLimitError(TradingError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RATE_LIMIT, **kwargs)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, requests are blocked
    - HALF_OPEN: Testing if system recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker {self.name}: OPEN -> HALF_OPEN")
                    return True
            return False
        
        # HALF_OPEN
        return self.half_open_calls < self.half_open_max_calls
    
    def record_success(self):
        """Record successful execution"""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            self.half_open_calls += 1
            
            if self.success_count >= self.half_open_max_calls:
                self.state = "CLOSED"
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN -> CLOSED")
        else:
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.warning(f"Circuit breaker {self.name}: HALF_OPEN -> OPEN")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker {self.name}: CLOSED -> OPEN (failures: {self.failure_count})")
    
    def get_state(self) -> Dict:
        """Get circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryPolicy:
    """
    Configurable retry policy with exponential backoff.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: List[Type[Exception]] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if should retry"""
        if attempt >= self.max_retries:
            return False
        
        # Check if exception is retryable
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                # Check if TradingError and not recoverable
                if isinstance(exception, TradingError) and not exception.recoverable:
                    return False
                return True
        
        return False
    
    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry"""
        import random
        
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


class ErrorHandler:
    """
    Central error handling system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Error tracking
        self.errors: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = {}
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Recovery handlers
        self.recovery_handlers: Dict[ErrorCategory, Callable] = {}
        
        # Fallback functions
        self.fallbacks: Dict[str, Callable] = {}
        
        # Alert handlers
        self.alert_handlers: List[Callable] = []
        
        # Default retry policy
        self.default_retry_policy = RetryPolicy()
    
    def register_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        """Register a circuit breaker"""
        self.circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    
    def register_recovery_handler(
        self,
        category: ErrorCategory,
        handler: Callable
    ):
        """Register a recovery handler for an error category"""
        self.recovery_handlers[category] = handler
    
    def register_fallback(self, operation: str, fallback: Callable):
        """Register a fallback function for an operation"""
        self.fallbacks[operation] = fallback
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler"""
        self.alert_handlers.append(handler)
    
    def classify_error(self, exception: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error"""
        if isinstance(exception, TradingError):
            return exception.category, exception.severity
        
        # Classify by exception type
        error_type = type(exception).__name__
        
        if 'Connection' in error_type or 'Network' in error_type:
            return ErrorCategory.NETWORK, ErrorSeverity.ERROR
        elif 'Timeout' in error_type:
            return ErrorCategory.TIMEOUT, ErrorSeverity.WARNING
        elif 'Auth' in error_type or 'Permission' in error_type:
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.CRITICAL
        elif 'Validation' in error_type or 'Value' in error_type:
            return ErrorCategory.VALIDATION, ErrorSeverity.WARNING
        elif 'Database' in error_type or 'SQL' in error_type:
            return ErrorCategory.DATABASE, ErrorSeverity.ERROR
        else:
            return ErrorCategory.UNKNOWN, ErrorSeverity.ERROR
    
    def handle_error(
        self,
        exception: Exception,
        component: str,
        operation: str,
        metadata: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Handle an error with classification and logging.
        
        Returns:
            ErrorContext with error details
        """
        import uuid
        
        category, severity = self.classify_error(exception)
        
        context = ErrorContext(
            error_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            exception=exception,
            message=str(exception),
            stack_trace=traceback.format_exc(),
            component=component,
            operation=operation,
            metadata=metadata or {}
        )
        
        # Track error
        self.errors.append(context)
        error_key = f"{category.value}:{component}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log error
        log_message = f"[{context.error_id}] {category.value.upper()} in {component}.{operation}: {exception}"
        
        if severity == ErrorSeverity.CRITICAL or severity == ErrorSeverity.FATAL:
            logger.critical(log_message)
        elif severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Fire alerts for critical errors
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            self._fire_alert(context)
        
        return context
    
    async def handle_with_recovery(
        self,
        exception: Exception,
        component: str,
        operation: str,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker_name: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> RecoveryResult:
        """
        Handle error with recovery attempt.
        """
        context = self.handle_error(exception, component, operation, metadata)
        
        # Check circuit breaker
        if circuit_breaker_name and circuit_breaker_name in self.circuit_breakers:
            cb = self.circuit_breakers[circuit_breaker_name]
            cb.record_failure()
            
            if not cb.can_execute():
                context.recovery_action = RecoveryAction.CIRCUIT_BREAK
                return RecoveryResult(
                    success=False,
                    action_taken=RecoveryAction.CIRCUIT_BREAK,
                    attempts=0,
                    final_error=exception
                )
        
        # Try recovery handler
        if context.category in self.recovery_handlers:
            try:
                handler = self.recovery_handlers[context.category]
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
                
                context.recovered = True
                context.recovery_action = RecoveryAction.FALLBACK
                
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.FALLBACK,
                    attempts=1
                )
            except Exception as e:
                logger.error(f"Recovery handler failed: {e}")
        
        # Try fallback
        if operation in self.fallbacks:
            try:
                fallback = self.fallbacks[operation]
                if asyncio.iscoroutinefunction(fallback):
                    result = await fallback()
                else:
                    result = fallback()
                
                context.recovered = True
                context.recovery_action = RecoveryAction.FALLBACK
                
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.FALLBACK,
                    attempts=1,
                    fallback_result=result
                )
            except Exception as e:
                logger.error(f"Fallback failed: {e}")
        
        # No recovery possible
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ALERT_AND_CONTINUE,
            attempts=context.recovery_attempts,
            final_error=exception
        )
    
    def _fire_alert(self, context: ErrorContext):
        """Fire alert for critical error"""
        alert = {
            'error_id': context.error_id,
            'category': context.category.value,
            'severity': context.severity.value,
            'component': context.component,
            'operation': context.operation,
            'message': context.message,
            'timestamp': context.timestamp.isoformat()
        }
        
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def get_error_summary(self) -> Dict:
        """Get error summary"""
        recent_errors = list(self.errors)[-100:]
        
        by_category = {}
        by_severity = {}
        by_component = {}
        
        for error in recent_errors:
            cat = error.category.value
            sev = error.severity.value
            comp = error.component
            
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_component[comp] = by_component.get(comp, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'recent_count': len(recent_errors),
            'by_category': by_category,
            'by_severity': by_severity,
            'by_component': by_component,
            'circuit_breakers': {
                name: cb.get_state()
                for name, cb in self.circuit_breakers.items()
            }
        }


def with_error_handling(
    handler: ErrorHandler,
    component: str,
    operation: str,
    circuit_breaker: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None
):
    """
    Decorator for error handling with retry and circuit breaker.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            policy = retry_policy or handler.default_retry_policy
            attempt = 0
            last_exception = None
            
            while attempt <= policy.max_retries:
                # Check circuit breaker
                if circuit_breaker and circuit_breaker in handler.circuit_breakers:
                    try:
                        cb = handler.circuit_breakers[circuit_breaker]
                        if not cb.can_execute():
                            raise TradingError(
                                f"Circuit breaker {circuit_breaker} is open",
                                category=ErrorCategory.UNKNOWN,
                                recoverable=False
                            )

                        result = await func(*args, **kwargs)

                        # Record success
                        if circuit_breaker and circuit_breaker in handler.circuit_breakers:
                            handler.circuit_breakers[circuit_breaker].record_success()

                        return result

                    except Exception as e:
                        last_exception = e
                        handler.handle_error(e, component, operation)

                        if policy.should_retry(e, attempt):
                            delay = policy.get_delay(attempt)
                            logger.info(f"Retrying {operation} in {delay:.1f}s (attempt {attempt + 1}/{policy.max_retries})")
                            await asyncio.sleep(delay)
                            attempt += 1
                        else:
                            break

            # All retries failed
            if circuit_breaker and circuit_breaker in handler.circuit_breakers:
                handler.circuit_breakers[circuit_breaker].record_failure()
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler.handle_error(e, component, operation)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create error handler
    handler = ErrorHandler()
    
    # Register circuit breaker
    handler.register_circuit_breaker("broker", failure_threshold=3, recovery_timeout=30)
    
    # Register fallback
    handler.register_fallback("get_price", lambda: 1.1000)
    
    # Simulate errors
    print("\n" + "="*60)
    logger.info("ERROR HANDLING TEST")
    print("="*60)
    
    # Test error classification
    errors = [
        BrokerConnectionError("Connection refused"),
        DataValidationError("Invalid OHLCV data"),
        RateLimitError("API rate limit exceeded"),
        ExecutionError("Order rejected"),
        ValueError("Invalid value")
    ]
    
    for error in errors:
        context = handler.handle_error(error, "test_component", "test_operation")
        logger.info(f"\nError: {error}")
        logger.info(f"  Category: {context.category.value}")
        logger.info(f"  Severity: {context.severity.value}")
    
    # Test circuit breaker
    logger.info("\n\nCircuit Breaker Test:")
    cb = handler.circuit_breakers["broker"]
    
    for i in range(5):
        cb.record_failure()
        logger.info(f"  After failure {i+1}: {cb.state}")
    
    logger.info(f"  Can execute: {cb.can_execute()}")
    
    # Print summary
    logger.info(f"\n\nError Summary:\n{handler.get_error_summary()}")
    print("="*60)
