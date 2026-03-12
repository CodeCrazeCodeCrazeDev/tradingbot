"""
Comprehensive Error Recovery System
====================================
Production-grade error handling with retry logic, circuit breakers,
graceful degradation, and automatic recovery.
"""

import asyncio
import functools
import logging
import random
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
import threading
from collections import deque
from typing import Set

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Log and continue
    MEDIUM = "medium"     # Retry with backoff
    HIGH = "high"         # Circuit breaker
    CRITICAL = "critical" # Immediate escalation


class RecoveryAction(Enum):
    """Recovery actions."""
    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_DEGRADE = "graceful_degrade"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ErrorContext:
    """Context for error handling."""
    error: Exception
    error_type: str
    severity: ErrorSeverity
    timestamp: datetime
    component: str
    operation: str
    attempt: int = 1
    max_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    
    def __post_init__(self):
        if not self.stack_trace:
            self.stack_trace = traceback.format_exc()


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class RecoveryResult:
    """Result of recovery attempt."""
    success: bool
    action_taken: RecoveryAction
    result: Any = None
    error: Optional[Exception] = None
    attempts: int = 1
    duration: float = 0.0


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by stopping requests to failing services.
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
        self._state_change_callbacks: List[Callable] = []
        
    @property
    def state(self) -> CircuitState:
        """Get current state, checking for timeout."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time:
                    elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout:
                        self._transition_to(CircuitState.HALF_OPEN)
            return self._state
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        
        logger.info(f"Circuit breaker '{self.name}': {old_state.value} -> {new_state.value}")
        
        for callback in self._state_change_callbacks:
            try:
                callback(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def record_success(self):
        """Record successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._half_open_calls += 1
                
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self):
        """Record failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            
            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        state = self.state  # This checks timeout
        
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            return False
        elif state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.config.half_open_max_calls:
                    return True
                return False
        
        return False
    
    def on_state_change(self, callback: Callable):
        """Register state change callback."""
        self._state_change_callbacks.append(callback)
    
    def reset(self):
        """Reset circuit breaker."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None


# ============================================================================
# RETRY HANDLER
# ============================================================================

class RetryHandler:
    """
    Handles retry logic with exponential backoff and jitter.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._attempt_history: deque = deque(maxlen=100)
        
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay
        )
        
        if self.config.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if should retry."""
        if attempt >= self.config.max_attempts:
            return False
        
        # Check non-retryable first
        if isinstance(error, self.config.non_retryable_exceptions):
            return False
        
        # Check retryable
        if isinstance(error, self.config.retryable_exceptions):
            return True
        
        return False
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_error = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                self._attempt_history.append({
                    'timestamp': datetime.utcnow(),
                    'attempt': attempt,
                    'success': True,
                })
                
                return result
                
            except Exception as e:
                last_error = e
                
                self._attempt_history.append({
                    'timestamp': datetime.utcnow(),
                    'attempt': attempt,
                    'success': False,
                    'error': str(e),
                })
                
                if not self.should_retry(e, attempt):
                    raise
                
                delay = self.calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
        
        raise last_error


# ============================================================================
# ERROR CLASSIFIER
# ============================================================================

class ErrorClassifier:
    """
    Classifies errors and determines appropriate recovery actions.
    """
    
    def __init__(self):
        self._rules: List[Dict] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default classification rules."""
        # Network errors - retry
        self.add_rule(
            error_types=[ConnectionError, TimeoutError, OSError],
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.RETRY,
        )
        
        # Rate limiting - backoff
        self.add_rule(
            error_patterns=["rate limit", "too many requests", "429"],
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.RETRY,
        )
        
        # Authentication - escalate
        self.add_rule(
            error_patterns=["unauthorized", "authentication", "401", "403"],
            severity=ErrorSeverity.HIGH,
            action=RecoveryAction.ESCALATE,
        )
        
        # Data errors - skip
        self.add_rule(
            error_types=[ValueError, TypeError, KeyError],
            severity=ErrorSeverity.LOW,
            action=RecoveryAction.SKIP,
        )
        
        # Critical errors - circuit break
        self.add_rule(
            error_types=[MemoryError, SystemExit],
            severity=ErrorSeverity.CRITICAL,
            action=RecoveryAction.CIRCUIT_BREAK,
        )
    
    def add_rule(
        self,
        error_types: Optional[List[Type[Exception]]] = None,
        error_patterns: Optional[List[str]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        action: RecoveryAction = RecoveryAction.RETRY,
    ):
        """Add classification rule."""
        self._rules.append({
            'error_types': error_types or [],
            'error_patterns': error_patterns or [],
            'severity': severity,
            'action': action,
        })
    
    def classify(self, error: Exception) -> tuple:
        """Classify error and return severity and action."""
        error_str = str(error).lower()
        error_type = type(error)
        
        for rule in self._rules:
            # Check error types
            if rule['error_types']:
                if any(isinstance(error, t) for t in rule['error_types']):
                    return rule['severity'], rule['action']
            
            # Check patterns
            if rule['error_patterns']:
                if any(p.lower() in error_str for p in rule['error_patterns']):
                    return rule['severity'], rule['action']
        
        # Default
        return ErrorSeverity.MEDIUM, RecoveryAction.RETRY


# ============================================================================
# FALLBACK HANDLER
# ============================================================================

class FallbackHandler:
    """
    Manages fallback strategies for graceful degradation.
    """
    
    def __init__(self):
        self._fallbacks: Dict[str, List[Callable]] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self._default_ttl = timedelta(minutes=5)
    
    def register_fallback(self, operation: str, fallback: Callable, priority: int = 0):
        """Register fallback for operation."""
        if operation not in self._fallbacks:
            self._fallbacks[operation] = []
        
        self._fallbacks[operation].append((priority, fallback))
        self._fallbacks[operation].sort(key=lambda x: x[0], reverse=True)
    
    def set_cached_value(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set cached fallback value."""
        self._cache[key] = value
        self._cache_ttl[key] = datetime.utcnow() + (ttl or self._default_ttl)
    
    def get_cached_value(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            if datetime.utcnow() < self._cache_ttl.get(key, datetime.min):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_ttl[key]
        return None
    
    async def execute_fallback(self, operation: str, *args, **kwargs) -> Any:
        """Execute fallback for operation."""
        fallbacks = self._fallbacks.get(operation, [])
        
        for priority, fallback in fallbacks:
            try:
                if asyncio.iscoroutinefunction(fallback):
                    result = await fallback(*args, **kwargs)
                else:
                    result = fallback(*args, **kwargs)
                
                logger.info(f"Fallback succeeded for {operation}")
                return result
                
            except Exception as e:
                logger.warning(f"Fallback failed for {operation}: {e}")
                continue
        
        # Try cache
        cache_key = f"{operation}:{hash(str(args) + str(kwargs))}"
        cached = self.get_cached_value(cache_key)
        if cached is not None:
            logger.info(f"Using cached value for {operation}")
            return cached
        
        raise RuntimeError(f"All fallbacks failed for {operation}")


# ============================================================================
# RECOVERY MANAGER
# ============================================================================

class RecoveryManager:
    """
    Central manager for error recovery.
    Coordinates circuit breakers, retries, and fallbacks.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.fallback_handler = FallbackHandler()
        self.error_classifier = ErrorClassifier()
        self._error_history: deque = deque(maxlen=1000)
        self._recovery_stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._escalation_callbacks: List[Callable] = []
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    def get_retry_handler(self, name: str, config: Optional[RetryConfig] = None) -> RetryHandler:
        """Get or create retry handler."""
        if name not in self.retry_handlers:
            self.retry_handlers[name] = RetryHandler(config)
        return self.retry_handlers[name]
    
    def on_escalation(self, callback: Callable):
        """Register escalation callback."""
        self._escalation_callbacks.append(callback)
    
    def _escalate(self, context: ErrorContext):
        """Escalate error to registered handlers."""
        for callback in self._escalation_callbacks:
            try:
                callback(context)
            except Exception as e:
                logger.error(f"Escalation callback error: {e}")
    
    async def execute_with_recovery(
        self,
        func: Callable,
        component: str,
        operation: str,
        *args,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        **kwargs
    ) -> RecoveryResult:
        """
        Execute function with full recovery support.
        """
        start_time = time.time()
        cb = self.get_circuit_breaker(f"{component}:{operation}", circuit_config)
        retry = self.get_retry_handler(f"{component}:{operation}", retry_config)
        
        # Check circuit breaker
        if not cb.can_execute():
            logger.warning(f"Circuit breaker open for {component}:{operation}")
            
            # Try fallback
            try:
                result = await self.fallback_handler.execute_fallback(
                    operation, *args, **kwargs
                )
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.FALLBACK,
                    result=result,
                    duration=time.time() - start_time,
                )
            except Exception as e:
                return RecoveryResult(
                    success=False,
                    action_taken=RecoveryAction.CIRCUIT_BREAK,
                    error=e,
                    duration=time.time() - start_time,
                )
        
        # Try with retry
        attempt = 0
        last_error = None
        
        for attempt in range(1, (retry_config or RetryConfig()).max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                cb.record_success()
                self._record_success(component, operation)
                
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.RETRY if attempt > 1 else RecoveryAction.SKIP,
                    result=result,
                    attempts=attempt,
                    duration=time.time() - start_time,
                )
                
            except Exception as e:
                last_error = e
                severity, action = self.error_classifier.classify(e)
                
                context = ErrorContext(
                    error=e,
                    error_type=type(e).__name__,
                    severity=severity,
                    timestamp=datetime.utcnow(),
                    component=component,
                    operation=operation,
                    attempt=attempt,
                )
                
                self._record_error(context)
                
                # Handle based on severity
                if severity == ErrorSeverity.CRITICAL:
                    cb.record_failure()
                    self._escalate(context)
                    
                    return RecoveryResult(
                        success=False,
                        action_taken=RecoveryAction.ESCALATE,
                        error=e,
                        attempts=attempt,
                        duration=time.time() - start_time,
                    )
                
                if action == RecoveryAction.SKIP:
                    return RecoveryResult(
                        success=False,
                        action_taken=RecoveryAction.SKIP,
                        error=e,
                        attempts=attempt,
                        duration=time.time() - start_time,
                    )
                
                if not retry.should_retry(e, attempt):
                    cb.record_failure()
                    break
                
                delay = retry.calculate_delay(attempt)
                logger.warning(f"Retry {attempt}: {e}. Waiting {delay:.2f}s")
                await asyncio.sleep(delay)
        
        # All retries failed
        cb.record_failure()
        
        # Try fallback
        try:
            result = await self.fallback_handler.execute_fallback(
                operation, *args, **kwargs
            )
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.FALLBACK,
                result=result,
                attempts=attempt,
                duration=time.time() - start_time,
            )
        except Exception:
            pass
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.GRACEFUL_DEGRADE,
            error=last_error,
            attempts=attempt,
            duration=time.time() - start_time,
        )
    
    def _record_error(self, context: ErrorContext):
        """Record error in history."""
        with self._lock:
            self._error_history.append({
                'timestamp': context.timestamp,
                'component': context.component,
                'operation': context.operation,
                'error_type': context.error_type,
                'severity': context.severity.value,
                'message': str(context.error),
            })
            
            key = f"{context.component}:{context.operation}"
            if key not in self._recovery_stats:
                self._recovery_stats[key] = {'success': 0, 'failure': 0}
            self._recovery_stats[key]['failure'] += 1
    
    def _record_success(self, component: str, operation: str):
        """Record successful operation."""
        with self._lock:
            key = f"{component}:{operation}"
            if key not in self._recovery_stats:
                self._recovery_stats[key] = {'success': 0, 'failure': 0}
            self._recovery_stats[key]['success'] += 1
    
    def get_stats(self) -> Dict:
        """Get recovery statistics."""
        with self._lock:
            return {
                'error_count': len(self._error_history),
                'circuit_breakers': {
                    name: cb.state.value for name, cb in self.circuit_breakers.items()
                },
                'operation_stats': self._recovery_stats.copy(),
            }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """Get recent errors."""
        with self._lock:
            return list(self._error_history)[-limit:]


# ============================================================================
# DECORATORS
# ============================================================================

def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    """Decorator for retry logic."""
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        retryable_exceptions=retryable_exceptions,
    )
    handler = RetryHandler(config)
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await handler.execute_with_retry(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.get_event_loop().run_until_complete(
                handler.execute_with_retry(func, *args, **kwargs)
            )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 30.0,
):
    """Decorator for circuit breaker."""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
    )
    cb = CircuitBreaker(name, config)
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not cb.can_execute():
                raise RuntimeError(f"Circuit breaker '{name}' is open")
            try:
            
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not cb.can_execute():
                raise RuntimeError(f"Circuit breaker '{name}' is open")
            try:
            
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """Get global recovery manager instance."""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ErrorSeverity', 'RecoveryAction', 'CircuitState',
    'ErrorContext', 'RetryConfig', 'CircuitBreakerConfig', 'RecoveryResult',
    'CircuitBreaker', 'RetryHandler', 'ErrorClassifier', 'FallbackHandler',
    'RecoveryManager', 'with_retry', 'with_circuit_breaker', 'get_recovery_manager',
]
