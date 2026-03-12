"""
Circuit Breaker Manager

Comprehensive circuit breaker system for trading operations:
- Multiple circuit breakers for different components
- Automatic reset with configurable policies
- Cascading failure protection
- Health-based recovery
- Metrics and alerting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking all operations
    HALF_OPEN = "half_open"  # Testing recovery


class ResetPolicy(Enum):
    """Circuit breaker reset policies"""
    MANUAL = "manual"  # Requires manual reset
    TIME_BASED = "time_based"  # Auto-reset after timeout
    HEALTH_BASED = "health_based"  # Reset when health check passes
    GRADUAL = "gradual"  # Gradually increase allowed requests


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker"""
    name: str
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 3  # Successes in half-open before closing
    timeout_seconds: float = 60.0  # Time before attempting recovery
    reset_policy: ResetPolicy = ResetPolicy.TIME_BASED
    half_open_max_requests: int = 3  # Max requests in half-open state
    cooldown_multiplier: float = 2.0  # Multiplier for consecutive failures
    max_timeout_seconds: float = 300.0  # Maximum timeout


@dataclass
class CircuitBreakerStats:
    """Statistics for a circuit breaker"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_state_change: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    current_timeout: float = 60.0


class CircuitBreaker:
    """
    Individual circuit breaker for a component.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: All requests are rejected
    - HALF_OPEN: Limited requests allowed to test recovery
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats(current_timeout=config.timeout_seconds)
        
        self._lock = threading.Lock()
        self._half_open_requests = 0
        self._opened_at: Optional[datetime] = None
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_failure: Optional[Callable] = None
        
        logger.info(f"Circuit breaker '{config.name}' initialized")
    
    def can_execute(self) -> bool:
        """
        Check if a request can be executed.
        
        Returns:
            True if request is allowed
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                    return True
                
                self.stats.rejected_requests += 1
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                # Allow limited requests
                if self._half_open_requests < self.config.half_open_max_requests:
                    self._half_open_requests += 1
                    return True
                
                self.stats.rejected_requests += 1
                return False
            
            return False
    
    def record_success(self):
        """Record a successful request"""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.successful_requests += 1
            self.stats.last_success_time = datetime.now()
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
    
    def record_failure(self, error: Optional[Exception] = None):
        """Record a failed request"""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            self.stats.last_failure_time = datetime.now()
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            
            if self.on_failure:
                try:
                    self.on_failure(self.config.name, error)
                except Exception as e:
                    logger.error(f"Failure callback error: {e}")
            
            if self.state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to_open()
            
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.config.reset_policy == ResetPolicy.MANUAL:
            return False
        
        if self._opened_at is None:
            return True
        
        elapsed = (datetime.now() - self._opened_at).total_seconds()
        return elapsed >= self.stats.current_timeout
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self._opened_at = datetime.now()
        self._half_open_requests = 0
        
        # Increase timeout for consecutive failures
        if self.config.reset_policy == ResetPolicy.TIME_BASED:
            self.stats.current_timeout = min(
                self.stats.current_timeout * self.config.cooldown_multiplier,
                self.config.max_timeout_seconds
            )
        
        self._record_state_change(old_state, CircuitState.OPEN)
        logger.warning(
            f"Circuit breaker '{self.config.name}' OPENED "
            f"(failures: {self.stats.consecutive_failures}, timeout: {self.stats.current_timeout:.0f}s)"
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self._half_open_requests = 0
        self.stats.consecutive_successes = 0
        
        self._record_state_change(old_state, CircuitState.HALF_OPEN)
        logger.info(f"Circuit breaker '{self.config.name}' HALF_OPEN (testing recovery)")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self._opened_at = None
        self._half_open_requests = 0
        
        # Reset timeout on successful recovery
        self.stats.current_timeout = self.config.timeout_seconds
        
        self._record_state_change(old_state, CircuitState.CLOSED)
        logger.info(f"Circuit breaker '{self.config.name}' CLOSED (recovered)")
    
    def _record_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """Record state change"""
        self.stats.state_changes += 1
        self.stats.last_state_change = datetime.now()
        
        if self.on_state_change:
            try:
                self.on_state_change(self.config.name, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        with self._lock:
            old_state = self.state
            self.state = CircuitState.CLOSED
            self._opened_at = None
            self._half_open_requests = 0
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            self.stats.current_timeout = self.config.timeout_seconds
            
            if old_state != CircuitState.CLOSED:
                self._record_state_change(old_state, CircuitState.CLOSED)
            
            logger.info(f"Circuit breaker '{self.config.name}' manually reset")
    
    def force_open(self):
        """Force circuit breaker to OPEN state"""
        with self._lock:
            if self.state != CircuitState.OPEN:
                self._transition_to_open()
            logger.warning(f"Circuit breaker '{self.config.name}' forced OPEN")
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        with self._lock:
            return {
                'name': self.config.name,
                'state': self.state.value,
                'stats': {
                    'total_requests': self.stats.total_requests,
                    'successful_requests': self.stats.successful_requests,
                    'failed_requests': self.stats.failed_requests,
                    'rejected_requests': self.stats.rejected_requests,
                    'state_changes': self.stats.state_changes,
                    'consecutive_failures': self.stats.consecutive_failures,
                    'consecutive_successes': self.stats.consecutive_successes,
                    'current_timeout': self.stats.current_timeout,
                    'last_failure': self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                    'last_success': self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
                    'last_state_change': self.stats.last_state_change.isoformat() if self.stats.last_state_change else None
                },
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'success_threshold': self.config.success_threshold,
                    'timeout_seconds': self.config.timeout_seconds,
                    'reset_policy': self.config.reset_policy.value
                }
            }


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different components.
    
    Features:
    - Centralized management
    - Cascading failure protection
    - Global emergency shutdown
    - Health monitoring
    - Metrics aggregation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize circuit breaker manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Global state
        self._global_shutdown = False
        
        # Callbacks
        self.on_global_shutdown: Optional[Callable] = None
        
        # Default circuit breaker configs
        self._default_configs = {
            'broker': CircuitBreakerConfig(
                name='broker',
                failure_threshold=3,
                timeout_seconds=30,
                reset_policy=ResetPolicy.TIME_BASED
            ),
            'data_feed': CircuitBreakerConfig(
                name='data_feed',
                failure_threshold=5,
                timeout_seconds=60,
                reset_policy=ResetPolicy.TIME_BASED
            ),
            'risk': CircuitBreakerConfig(
                name='risk',
                failure_threshold=3,
                timeout_seconds=30,
                reset_policy=ResetPolicy.TIME_BASED
            ),
            'execution': CircuitBreakerConfig(
                name='execution',
                failure_threshold=3,
                timeout_seconds=30,
                reset_policy=ResetPolicy.TIME_BASED
            ),
            'analysis': CircuitBreakerConfig(
                name='analysis',
                failure_threshold=5,
                timeout_seconds=60,
                reset_policy=ResetPolicy.TIME_BASED
            )
        }
        
        # Initialize default circuit breakers
        for name, cb_config in self._default_configs.items():
            self.add_circuit_breaker(cb_config)
        
        logger.info(f"Circuit breaker manager initialized with {len(self.circuit_breakers)} breakers")
    
    def add_circuit_breaker(self, config: CircuitBreakerConfig) -> CircuitBreaker:
        """
        Add a new circuit breaker.
        
        Args:
            config: Circuit breaker configuration
            
        Returns:
            CircuitBreaker instance
        """
        cb = CircuitBreaker(config)
        cb.on_state_change = self._on_circuit_state_change
        cb.on_failure = self._on_circuit_failure
        
        self.circuit_breakers[config.name] = cb
        return cb
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)
    
    def can_execute(self, name: str) -> bool:
        """
        Check if operation can be executed.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            True if allowed
        """
        if self._global_shutdown:
            logger.warning(f"Global shutdown active - blocking {name}")
            return False
        
        cb = self.circuit_breakers.get(name)
        if cb:
            return cb.can_execute()
        
        # Unknown circuit breaker - allow by default
        logger.warning(f"Unknown circuit breaker: {name}")
        return True
    
    def record_success(self, name: str):
        """Record successful operation"""
        cb = self.circuit_breakers.get(name)
        if cb:
            cb.record_success()
    
    def record_failure(self, name: str, error: Optional[Exception] = None):
        """Record failed operation"""
        cb = self.circuit_breakers.get(name)
        if cb:
            cb.record_failure(error)
    
    def reset(self, name: str):
        """Reset specific circuit breaker"""
        cb = self.circuit_breakers.get(name)
        if cb:
            cb.reset()
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset()
        
        self._global_shutdown = False
        logger.info("All circuit breakers reset")
    
    def force_open(self, name: str):
        """Force specific circuit breaker open"""
        cb = self.circuit_breakers.get(name)
        if cb:
            cb.force_open()
    
    def global_shutdown(self):
        """Trigger global shutdown - all operations blocked"""
        self._global_shutdown = True
        
        # Open all circuit breakers
        for cb in self.circuit_breakers.values():
            cb.force_open()
        
        logger.critical("GLOBAL SHUTDOWN - All circuit breakers opened")
        
        if self.on_global_shutdown:
            try:
                self.on_global_shutdown()
            except Exception as e:
                logger.error(f"Global shutdown callback error: {e}")
    
    def _on_circuit_state_change(
        self,
        name: str,
        old_state: CircuitState,
        new_state: CircuitState
    ):
        """Handle circuit breaker state change"""
        # Check for cascading failures
        open_count = sum(
            1 for cb in self.circuit_breakers.values()
            if cb.state == CircuitState.OPEN
        )
        
        # If too many circuits are open, trigger global shutdown
        threshold = self.config.get('cascade_threshold', 3)
        if open_count >= threshold and not self._global_shutdown:
            logger.critical(
                f"Cascading failure detected - {open_count} circuits open "
                f"(threshold: {threshold})"
            )
            self.global_shutdown()
    
    def _on_circuit_failure(self, name: str, error: Optional[Exception]):
        """Handle circuit breaker failure"""
        # Log for monitoring
        logger.warning(f"Circuit '{name}' recorded failure: {error}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            'global_shutdown': self._global_shutdown,
            'circuit_breakers': {
                name: cb.get_status()
                for name, cb in self.circuit_breakers.items()
            },
            'summary': {
                'total': len(self.circuit_breakers),
                'closed': sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.CLOSED),
                'open': sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN),
                'half_open': sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.HALF_OPEN)
            }
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status"""
        status = self.get_status()
        
        # Calculate health score
        if self._global_shutdown:
            health_score = 0
            health_status = 'critical'
        elif status['summary']['open'] > 0:
            health_score = 50 - (status['summary']['open'] * 10)
            health_status = 'degraded'
        elif status['summary']['half_open'] > 0:
            health_score = 80
            health_status = 'recovering'
        else:
            health_score = 100
            health_status = 'healthy'
        
        return {
            'status': health_status,
            'score': max(0, health_score),
            'global_shutdown': self._global_shutdown,
            'circuits': status['summary']
        }


# Singleton instance
_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager(config: Optional[Dict[str, Any]] = None) -> CircuitBreakerManager:
    """Get singleton circuit breaker manager"""
    global _manager
    if _manager is None:
        _manager = CircuitBreakerManager(config)
    return _manager


# Decorator for circuit breaker protection
def circuit_protected(circuit_name: str):
    """
    Decorator to protect a function with a circuit breaker.
    
    Usage:
        @circuit_protected('broker')
        async def place_order(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_circuit_breaker_manager()
            
            if not manager.can_execute(circuit_name):
                raise CircuitBreakerOpenError(f"Circuit breaker '{circuit_name}' is open")
            try:
            
                result = await func(*args, **kwargs)
                manager.record_success(circuit_name)
                return result
            except Exception as e:
                manager.record_failure(circuit_name, e)
                raise
        
        return wrapper
    return decorator


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass
