Comprehensive Error Recovery System
====================================

Provides robust error handling with:
- Automatic retry with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- State recovery
- Error classification and routing

Usage:
    from trading_bot.error_handling import (
        RetryPolicy, CircuitBreaker, RecoveryOrchestrator,
        with_retry, with_circuit_breaker
    )
    
    # Use decorators
    @with_retry(max_attempts=3, backoff_factor=2.0)
    async def fetch_data():
        ...
    
    @with_circuit_breaker(failure_threshold=5, reset_timeout=60)
    async def execute_order():
        ...
"""

import asyncio
import functools
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import (, Callable, Dict, Optional, Set
    Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union
)
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Retry immediately
    MEDIUM = "medium"     # Retry with backoff
    HIGH = "high"         # Trigger circuit breaker
    CRITICAL = "critical" # Immediate escalation


class RecoveryAction(Enum):
    """Recovery actions."""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"
    IGNORE = "ignore"


@dataclass
class ErrorContext:
    """Context for an error occurrence."""
    error: Exception
    error_type: str
    severity: ErrorSeverity
    timestamp: datetime
    operation: str
    attempt: int
    max_attempts: int
    traceback: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: float = 0.1
    retryable_exceptions: Set[Type[Exception]] = field(
        default_factory=lambda: {Exception}
    )
    non_retryable_exceptions: Set[Type[Exception]] = field(
        default_factory=lambda: {KeyboardInterrupt, SystemExit}
    )
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt."""
        import random
        delay = min(
            self.initial_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )
        # Add jitter
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)
        return max(0, delay)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should be retried."""
        if attempt >= self.max_attempts:
            return False
        
        # Check non-retryable first
        for exc_type in self.non_retryable_exceptions:
            if isinstance(exception, exc_type):
                return False
        
        # Check retryable
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    success_threshold: int = 2
    reset_timeout: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    Prevents cascading failures by temporarily blocking
    requests to a failing service.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if reset timeout has passed
                if self._last_failure_time:
                    elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                    if elapsed >= self.config.reset_timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
            
            return self._state
    
    def is_available(self) -> bool:
        """Check if the circuit allows requests."""
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
            return False
        
        return False  # OPEN
    
    def record_success(self):
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit {self.name} CLOSED after recovery")
            else:
                self._failure_count = 0
    
    def record_failure(self, exception: Exception):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit {self.name} OPEN after half-open failure")
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name} OPEN after {self._failure_count} failures")
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit {self.name} manually reset")


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class FallbackRegistry:
    """Registry for fallback functions."""
    
    def __init__(self):
        self._fallbacks: Dict[str, Callable] = {}
    
    def register(self, operation: str, fallback: Callable):
        """Register a fallback for an operation."""
        self._fallbacks[operation] = fallback
    
    def get(self, operation: str) -> Optional[Callable]:
        """Get fallback for an operation."""
        return self._fallbacks.get(operation)
    
    def has_fallback(self, operation: str) -> bool:
        """Check if operation has a fallback."""
        return operation in self._fallbacks


class ErrorClassifier:
    """Classifies errors by severity and determines recovery action."""
    
    # Error type to severity mapping
    SEVERITY_MAP: Dict[Type[Exception], ErrorSeverity] = {
        ConnectionError: ErrorSeverity.MEDIUM,
        TimeoutError: ErrorSeverity.MEDIUM,
        OSError: ErrorSeverity.MEDIUM,
        ValueError: ErrorSeverity.LOW,
        KeyError: ErrorSeverity.LOW,
        TypeError: ErrorSeverity.LOW,
        RuntimeError: ErrorSeverity.HIGH,
        MemoryError: ErrorSeverity.CRITICAL,
        SystemError: ErrorSeverity.CRITICAL,
    }
    
    @classmethod
    def classify(cls, exception: Exception) -> ErrorSeverity:
        """Classify an exception by severity."""
        for exc_type, severity in cls.SEVERITY_MAP.items():
            if isinstance(exception, exc_type):
                return severity
        return ErrorSeverity.MEDIUM
    
    @classmethod
    def get_action(cls, severity: ErrorSeverity, attempt: int, max_attempts: int) -> RecoveryAction:
        """Determine recovery action based on severity and attempts."""
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.ESCALATE
        
        if attempt >= max_attempts:
            if severity == ErrorSeverity.HIGH:
                return RecoveryAction.CIRCUIT_BREAK
            return RecoveryAction.FALLBACK
        
        return RecoveryAction.RETRY


class RecoveryOrchestrator:
    """
    Orchestrates error recovery across the system.
    
    Coordinates retry logic, circuit breakers, and fallbacks.
    """
    
    def __init__(
        self,
        default_retry_policy: Optional[RetryPolicy] = None,
        state_file: Optional[str] = None
    ):
        self.default_retry_policy = default_retry_policy or RetryPolicy()
        self.state_file = Path(state_file) if state_file else None
        
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallbacks = FallbackRegistry()
        self.error_history: deque = deque(maxlen=1000)
        
        self._lock = threading.Lock()
        
        # Load state if available
        if self.state_file and self.state_file.exists():
            self._load_state()
    
    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self._lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name, config)
            return self.circuit_breakers[name]
    
    def register_fallback(self, operation: str, fallback: Callable):
        """Register a fallback function."""
        self.fallbacks.register(operation, fallback)
    
    async def execute_with_recovery(
        self,
        operation: str,
        func: Callable[..., T],
        *args,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker: Optional[str] = None,
        **kwargs
    ) -> T:
        """
        Execute a function with full recovery support.
        
        Args:
            operation: Name of the operation
            func: Function to execute
            retry_policy: Optional custom retry policy
            circuit_breaker: Optional circuit breaker name
            *args, **kwargs: Arguments to pass to func
            
        Returns:
            Result of the function
            
        Raises:
            Exception: If all recovery attempts fail
        """
        policy = retry_policy or self.default_retry_policy
        cb = self.get_circuit_breaker(circuit_breaker) if circuit_breaker else None
        
        last_exception = None
        
        for attempt in range(policy.max_attempts):
            # Check circuit breaker
            if cb and not cb.is_available():
                raise CircuitBreakerOpen(f"Circuit breaker {circuit_breaker} is open")
            
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success
                if cb:
                    cb.record_success()
                
                return result
                
            except Exception as e:
                last_exception = e
                severity = ErrorClassifier.classify(e)
                
                # Record error
                context = ErrorContext(
                    error=e,
                    error_type=type(e).__name__,
                    severity=severity,
                    timestamp=datetime.utcnow(),
                    operation=operation,
                    attempt=attempt + 1,
                    max_attempts=policy.max_attempts,
                    traceback=traceback.format_exc()
                )
                self.error_history.append(context)
                
                # Record circuit breaker failure
                if cb:
                    cb.record_failure(e)
                
                # Determine action
                action = ErrorClassifier.get_action(severity, attempt + 1, policy.max_attempts)
                
                if action == RecoveryAction.ESCALATE:
                    logger.critical(f"Critical error in {operation}: {e}")
                    raise
                
                if action == RecoveryAction.CIRCUIT_BREAK:
                    logger.error(f"Circuit breaking {operation} after {attempt + 1} failures")
                    break
                
                if action == RecoveryAction.RETRY:
                    if policy.should_retry(e, attempt + 1):
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Retrying {operation} in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{policy.max_attempts}): {e}"
                        )
                        await asyncio.sleep(delay)
                        continue
        
        # All retries exhausted, try fallback
        fallback = self.fallbacks.get(operation)
        if fallback:
            logger.info(f"Using fallback for {operation}")
            try:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                return fallback(*args, **kwargs)
            except Exception as fb_error:
                logger.error(f"Fallback for {operation} also failed: {fb_error}")
        
        # No fallback or fallback failed
        raise last_exception
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        errors_by_type: Dict[str, int] = {}
        errors_by_severity: Dict[str, int] = {}
        
        for ctx in self.error_history:
            errors_by_type[ctx.error_type] = errors_by_type.get(ctx.error_type, 0) + 1
            errors_by_severity[ctx.severity.value] = errors_by_severity.get(ctx.severity.value, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'by_type': errors_by_type,
            'by_severity': errors_by_severity,
            'circuit_breakers': {
                name: cb.state.value
                for name, cb in self.circuit_breakers.items()
            }
        }
    
    def _load_state(self):
        """Load state from file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                # Restore circuit breaker states if needed
                logger.info(f"Loaded recovery state from {self.state_file}")
        except Exception as e:
            logger.warning(f"Failed to load recovery state: {e}")
    
    def save_state(self):
        """Save state to file."""
        if not self.state_file:
            return
        
        try:
            state = {
                'timestamp': datetime.utcnow().isoformat(),
                'circuit_breakers': {
                    name: {
                        'state': cb.state.value,
                        'failure_count': cb._failure_count
                    }
                    for name, cb in self.circuit_breakers.items()
                }
            }
            
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recovery state: {e}")


# Global orchestrator instance
_orchestrator: Optional[RecoveryOrchestrator] = None


def get_orchestrator() -> RecoveryOrchestrator:
    """Get the global recovery orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RecoveryOrchestrator()
    return _orchestrator


# Decorators

def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    retryable_exceptions: Optional[Set[Type[Exception]]] = None
):
    """
    Decorator for automatic retry with exponential backoff.
    
    Usage:
        @with_retry(max_attempts=3, backoff_factor=2.0)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        policy = RetryPolicy(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            initial_delay=initial_delay,
            retryable_exceptions=retryable_exceptions or {Exception}
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            orchestrator = get_orchestrator()
            return await orchestrator.execute_with_recovery(
                func.__name__,
                func,
                *args,
                retry_policy=policy,
                **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    reset_timeout: float = 60.0
):
    """
    Decorator for circuit breaker protection.
    
    Usage:
        @with_circuit_breaker(failure_threshold=5, reset_timeout=60)
        async def call_external_service():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cb_name = name or func.__name__
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            orchestrator = get_orchestrator()
            return await orchestrator.execute_with_recovery(
                func.__name__,
                func,
                *args,
                circuit_breaker=cb_name,
                **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_fallback(fallback_func: Callable):
    """
    Decorator to register a fallback function.
    
    Usage:
        def fallback_fetch():
            return cached_data
        
        @with_fallback(fallback_fetch)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        orchestrator = get_orchestrator()
        orchestrator.register_fallback(func.__name__, fallback_func)
        return func
    
    return decorator


__all__ = [
    'RetryPolicy',
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitBreakerOpen',
    'CircuitState',
    'RecoveryOrchestrator',
    'ErrorClassifier',
    'ErrorSeverity',
    'RecoveryAction',
    'ErrorContext',
    'FallbackRegistry',
    'get_orchestrator',
    'with_retry',
    'with_circuit_breaker',
    'with_fallback',
]
