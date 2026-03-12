"""
AlphaAlgo Fault Tolerance
==========================
Circuit breakers, retry handlers, bulkheads, rate limiters, and health monitoring.
Ensures system resilience under failure conditions.
"""

from __future__ import annotations

import asyncio
import logging
import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    TypeVar, Generic
)
from collections import deque
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing, reject requests
    HALF_OPEN = auto()   # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout_seconds: float = 30.0       # Time in open state before half-open
    half_open_max_calls: int = 3        # Max calls in half-open state


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by failing fast when a service is down.
    """
    
    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        
        self._lock = asyncio.Lock()
        
        # Callbacks
        self._on_state_change: List[Callable[[CircuitState, CircuitState], None]] = []
    
    def on_state_change(self, callback: Callable[[CircuitState, CircuitState], None]):
        """Register state change callback"""
        self._on_state_change.append(callback)
    
    async def call(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """
        Execute function through circuit breaker.
        
        Raises:
            CircuitOpenError: If circuit is open
        """
        async with self._lock:
            pass
        try:
            if not await self._can_execute():
                raise CircuitOpenError(f"Circuit {self.name} is open")
        
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if time.time() - self._last_failure_time >= self.config.timeout_seconds:
                await self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        
        return False
    
    async def _on_success(self):
        """Handle successful execution"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
            elif self.state == CircuitState.CLOSED:
                self._failure_count = 0
    
    async def _on_failure(self):
        """Handle failed execution"""
        async with self._lock:
            self._last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)
            elif self.state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)
    
    async def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        
        # Reset counters
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        elif new_state == CircuitState.OPEN:
            self._success_count = 0
        
        logger.info(f"Circuit {self.name}: {old_state.name} -> {new_state.name}")
        
        for callback in self._on_state_change:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    async def reset(self):
        """Manually reset circuit to closed"""
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit state"""
        return {
            'name': self.name,
            'state': self.state.name,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'last_failure': self._last_failure_time,
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


@dataclass
class RetryConfig:
    """Configuration for retry handler"""
    max_retries: int = 3
    initial_delay_ms: int = 100
    max_delay_ms: int = 10000
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_exceptions: List[type] = field(default_factory=list)


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.
    Automatically retries failed operations.
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """
        Execute function with retry logic.
        
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                if self.config.retry_exceptions:
                    if not any(isinstance(e, exc_type) for exc_type in self.config.retry_exceptions):
                        raise
                
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.config.max_retries} "
                        f"after {delay}ms: {e}"
                    )
                    await asyncio.sleep(delay / 1000)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> int:
        """Calculate delay for attempt"""
        delay = self.config.initial_delay_ms * (
            self.config.backoff_multiplier ** attempt
        )
        delay = min(delay, self.config.max_delay_ms)
        
        if self.config.jitter:
            # Add random jitter (0-25% of delay)
            jitter = random.uniform(0, 0.25) * delay
            delay += jitter
        
        return int(delay)


class BulkheadState(Enum):
    """Bulkhead states"""
    AVAILABLE = auto()
    FULL = auto()
    REJECTED = auto()


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead"""
    max_concurrent: int = 10
    max_waiting: int = 100
    timeout_ms: int = 30000


class Bulkhead:
    """
    Bulkhead pattern implementation.
    Isolates failures by limiting concurrent executions.
    """
    
    def __init__(self, name: str, config: BulkheadConfig = None):
        self.name = name
        self.config = config or BulkheadConfig()
        
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._waiting = 0
        self._active = 0
        self._lock = asyncio.Lock()
        
        # Metrics
        self.metrics = {
            'accepted': 0,
            'rejected': 0,
            'completed': 0,
            'failed': 0,
        }
    
    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """
        Execute function within bulkhead.
        
        Raises:
            BulkheadFullError: If bulkhead is full
        """
        async with self._lock:
            pass
        try:
            if self._waiting >= self.config.max_waiting:
                self.metrics['rejected'] += 1
                raise BulkheadFullError(f"Bulkhead {self.name} is full")
            self._waiting += 1
        
            # Try to acquire semaphore with timeout
            try:
                await asyncio.wait_for(
                    self._semaphore.acquire(),
                    timeout=self.config.timeout_ms / 1000
                )
            except asyncio.TimeoutError:
                async with self._lock:
                    self._waiting -= 1
                self.metrics['rejected'] += 1
                raise BulkheadFullError(f"Bulkhead {self.name} timeout")
            
            async with self._lock:
                pass
            try:
                self._waiting -= 1
                self._active += 1
                self.metrics['accepted'] += 1
            
                result = await func(*args, **kwargs)
                self.metrics['completed'] += 1
                return result
            except Exception as e:
                self.metrics['failed'] += 1
                raise
            finally:
                async with self._lock:
                    self._active -= 1
                self._semaphore.release()
        
        except BulkheadFullError:
            raise
    
    def get_state(self) -> Dict[str, Any]:
        """Get bulkhead state"""
        return {
            'name': self.name,
            'active': self._active,
            'waiting': self._waiting,
            'available': self.config.max_concurrent - self._active,
            'metrics': dict(self.metrics),
        }


class BulkheadFullError(Exception):
    """Raised when bulkhead is full"""
    pass


class RateLimiter:
    """
    Token bucket rate limiter.
    Controls the rate of operations.
    """
    
    def __init__(
        self,
        rate: float,           # Tokens per second
        burst: int = None      # Max burst size
    ):
        self.rate = rate
        self.burst = burst or int(rate)
        
        self._tokens = float(self.burst)
        self._last_update = time.time()
        self._lock = asyncio.Lock()
        
        # Metrics
        self.metrics = {
            'acquired': 0,
            'rejected': 0,
            'waited': 0,
        }
    
    async def acquire(self, tokens: int = 1, wait: bool = True) -> bool:
        """
        Acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            wait: If True, wait for tokens; if False, return immediately
            
        Returns:
            True if acquired, False if rejected (when wait=False)
        """
        async with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                self.metrics['acquired'] += 1
                return True
            
            if not wait:
                self.metrics['rejected'] += 1
                return False
        
        # Wait for tokens
        wait_time = (tokens - self._tokens) / self.rate
        self.metrics['waited'] += 1
        await asyncio.sleep(wait_time)
        
        async with self._lock:
            self._refill()
            self._tokens -= tokens
            self.metrics['acquired'] += 1
            return True
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self._last_update
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_update = now
    
    def get_state(self) -> Dict[str, Any]:
        """Get rate limiter state"""
        return {
            'rate': self.rate,
            'burst': self.burst,
            'tokens': self._tokens,
            'metrics': dict(self.metrics),
        }


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """
    Health monitoring for system components.
    Tracks health status and provides alerts.
    """
    
    def __init__(self, check_interval_seconds: float = 10.0):
        self.check_interval = check_interval_seconds
        
        # Registered health checks
        self._checks: Dict[str, Callable[[], Awaitable[HealthCheck]]] = {}
        
        # Latest results
        self._results: Dict[str, HealthCheck] = {}
        
        # Callbacks
        self._on_status_change: List[Callable[[str, HealthStatus, HealthStatus], Awaitable[None]]] = []
        
        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    def register_check(
        self,
        name: str,
        check: Callable[[], Awaitable[HealthCheck]]
    ):
        """Register a health check"""
        self._checks[name] = check
        logger.info(f"Registered health check: {name}")
    
    def on_status_change(
        self,
        callback: Callable[[str, HealthStatus, HealthStatus], Awaitable[None]]
    ):
        """Register status change callback"""
        self._on_status_change.append(callback)
    
    async def start(self):
        """Start health monitoring"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started")
    
    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                await self.check_all()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(1)
    
    async def check_all(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        results = {}
        
        for name, check in self._checks.items():
            try:
                start = time.time()
                result = await asyncio.wait_for(check(), timeout=10.0)
                result.latency_ms = (time.time() - start) * 1000
                results[name] = result
            except asyncio.TimeoutError:
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message="Health check timeout",
                )
            except Exception as e:
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                )
            
            # Check for status change
            old_result = self._results.get(name)
            if old_result and old_result.status != results[name].status:
                for callback in self._on_status_change:
                    try:
                        await callback(name, old_result.status, results[name].status)
                    except Exception as e:
                        logger.error(f"Status change callback error: {e}")
        
        self._results = results
        return results
    
    async def check_one(self, name: str) -> Optional[HealthCheck]:
        """Run a specific health check"""
        if name not in self._checks:
            return None
        
        check = self._checks[name]
        try:
            start = time.time()
            result = await check()
            result.latency_ms = (time.time() - start) * 1000
            self._results[name] = result
            return result
        except Exception as e:
            result = HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )
            self._results[name] = result
            return result
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self._results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in self._results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        
        return HealthStatus.UNKNOWN
    
    def get_results(self) -> Dict[str, HealthCheck]:
        """Get latest health check results"""
        return dict(self._results)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get health summary"""
        return {
            'overall': self.get_overall_status().name,
            'checks': {
                name: {
                    'status': r.status.name,
                    'message': r.message,
                    'latency_ms': r.latency_ms,
                }
                for name, r in self._results.items()
            },
            'timestamp': time.time(),
        }
