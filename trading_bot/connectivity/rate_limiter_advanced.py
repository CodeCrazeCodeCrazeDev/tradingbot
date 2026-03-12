"""
Advanced Rate Limiting System
==============================
Production-grade rate limiting with multiple algorithms,
adaptive throttling, and distributed support.
"""

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import functools
import hashlib
from typing import Set

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


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"


class RateLimitResult(Enum):
    """Rate limit check result."""
    ALLOWED = "allowed"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_second: float = 10.0
    requests_per_minute: float = 300.0
    requests_per_hour: float = 10000.0
    burst_size: int = 20
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    adaptive_enabled: bool = True
    backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 300.0
    retry_after_header: bool = True


@dataclass
class RateLimitStatus:
    """Rate limit status."""
    result: RateLimitResult
    remaining: int
    reset_at: datetime
    retry_after: float = 0.0
    current_rate: float = 0.0
    limit: float = 0.0


@dataclass
class EndpointConfig:
    """Per-endpoint rate limit configuration."""
    endpoint: str
    requests_per_second: float = 5.0
    requests_per_minute: float = 100.0
    burst_size: int = 10
    weight: int = 1  # Request weight/cost
    priority: int = 0  # Higher = more priority


# ============================================================================
# RATE LIMITERS
# ============================================================================

class BaseRateLimiter(ABC):
    """Abstract base rate limiter."""
    
    @abstractmethod
    def acquire(self, key: str = "default", weight: int = 1) -> RateLimitStatus:
        """Acquire permission to proceed."""
        pass
    
    @abstractmethod
    def get_status(self, key: str = "default") -> RateLimitStatus:
        """Get current rate limit status."""
        pass
    
    @abstractmethod
    def reset(self, key: str = "default"):
        """Reset rate limiter."""
        pass


class TokenBucketLimiter(BaseRateLimiter):
    """
    Token bucket rate limiter.
    Allows bursts up to bucket size, then rate-limits.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._buckets: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def _get_bucket(self, key: str) -> Dict:
        """Get or create bucket for key."""
        if key not in self._buckets:
            self._buckets[key] = {
                'tokens': self.config.burst_size,
                'last_update': time.time(),
                'requests': 0,
            }
        return self._buckets[key]
    
    def _refill(self, bucket: Dict):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket['last_update']
        
        # Add tokens based on rate
        new_tokens = elapsed * self.config.requests_per_second
        bucket['tokens'] = min(
            self.config.burst_size,
            bucket['tokens'] + new_tokens
        )
        bucket['last_update'] = now
    
    def acquire(self, key: str = "default", weight: int = 1) -> RateLimitStatus:
        """Acquire tokens from bucket."""
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)
            
            if bucket['tokens'] >= weight:
                bucket['tokens'] -= weight
                bucket['requests'] += 1
                
                return RateLimitStatus(
                    result=RateLimitResult.ALLOWED,
                    remaining=int(bucket['tokens']),
                    reset_at=datetime.utcnow() + timedelta(seconds=1),
                    current_rate=bucket['requests'],
                    limit=self.config.requests_per_second,
                )
            else:
                # Calculate wait time
                tokens_needed = weight - bucket['tokens']
                wait_time = tokens_needed / self.config.requests_per_second
                
                return RateLimitStatus(
                    result=RateLimitResult.RATE_LIMITED,
                    remaining=0,
                    reset_at=datetime.utcnow() + timedelta(seconds=wait_time),
                    retry_after=wait_time,
                    current_rate=bucket['requests'],
                    limit=self.config.requests_per_second,
                )
    
    def get_status(self, key: str = "default") -> RateLimitStatus:
        """Get current status."""
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)
            
            return RateLimitStatus(
                result=RateLimitResult.ALLOWED if bucket['tokens'] >= 1 else RateLimitResult.RATE_LIMITED,
                remaining=int(bucket['tokens']),
                reset_at=datetime.utcnow() + timedelta(seconds=1),
                current_rate=bucket['requests'],
                limit=self.config.requests_per_second,
            )
    
    def reset(self, key: str = "default"):
        """Reset bucket."""
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]


class SlidingWindowLimiter(BaseRateLimiter):
    """
    Sliding window rate limiter.
    Tracks requests in a sliding time window.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._windows: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def _get_window(self, key: str) -> deque:
        """Get or create window for key."""
        if key not in self._windows:
            self._windows[key] = deque()
        return self._windows[key]
    
    def _clean_window(self, window: deque, window_size: float):
        """Remove old entries from window."""
        cutoff = time.time() - window_size
        while window and window[0] < cutoff:
            window.popleft()
    
    def acquire(self, key: str = "default", weight: int = 1) -> RateLimitStatus:
        """Check if request is allowed."""
        with self._lock:
            window = self._get_window(key)
            now = time.time()
            
            # Clean old entries (1 minute window)
            self._clean_window(window, 60.0)
            
            # Check limit
            if len(window) + weight <= self.config.requests_per_minute:
                for _ in range(weight):
                    window.append(now)
                
                return RateLimitStatus(
                    result=RateLimitResult.ALLOWED,
                    remaining=int(self.config.requests_per_minute - len(window)),
                    reset_at=datetime.utcnow() + timedelta(seconds=60),
                    current_rate=len(window),
                    limit=self.config.requests_per_minute,
                )
            else:
                # Calculate wait time
                oldest = window[0] if window else now
                wait_time = 60.0 - (now - oldest)
                
                return RateLimitStatus(
                    result=RateLimitResult.RATE_LIMITED,
                    remaining=0,
                    reset_at=datetime.utcnow() + timedelta(seconds=wait_time),
                    retry_after=wait_time,
                    current_rate=len(window),
                    limit=self.config.requests_per_minute,
                )
    
    def get_status(self, key: str = "default") -> RateLimitStatus:
        """Get current status."""
        with self._lock:
            window = self._get_window(key)
            self._clean_window(window, 60.0)
            
            remaining = int(self.config.requests_per_minute - len(window))
            
            return RateLimitStatus(
                result=RateLimitResult.ALLOWED if remaining > 0 else RateLimitResult.RATE_LIMITED,
                remaining=max(0, remaining),
                reset_at=datetime.utcnow() + timedelta(seconds=60),
                current_rate=len(window),
                limit=self.config.requests_per_minute,
            )
    
    def reset(self, key: str = "default"):
        """Reset window."""
        with self._lock:
            if key in self._windows:
                self._windows[key].clear()


class AdaptiveRateLimiter(BaseRateLimiter):
    """
    Adaptive rate limiter.
    Adjusts limits based on response patterns and errors.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._base_limiter = TokenBucketLimiter(config)
        self._error_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
        self._backoff_until: Dict[str, float] = {}
        self._current_multiplier: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def acquire(self, key: str = "default", weight: int = 1) -> RateLimitStatus:
        """Acquire with adaptive behavior."""
        with self._lock:
            # Check if in backoff
            if key in self._backoff_until:
                if time.time() < self._backoff_until[key]:
                    wait_time = self._backoff_until[key] - time.time()
                    return RateLimitStatus(
                        result=RateLimitResult.RATE_LIMITED,
                        remaining=0,
                        reset_at=datetime.utcnow() + timedelta(seconds=wait_time),
                        retry_after=wait_time,
                        limit=self.config.requests_per_second,
                    )
                else:
                    del self._backoff_until[key]
            
            # Get effective weight based on current multiplier
            multiplier = self._current_multiplier.get(key, 1.0)
            effective_weight = int(weight * multiplier)
            
            return self._base_limiter.acquire(key, effective_weight)
    
    def record_success(self, key: str = "default"):
        """Record successful request."""
        with self._lock:
            self._success_counts[key] = self._success_counts.get(key, 0) + 1
            
            # Gradually reduce multiplier on success
            if key in self._current_multiplier:
                self._current_multiplier[key] = max(
                    1.0,
                    self._current_multiplier[key] * 0.95
                )
    
    def record_error(self, key: str = "default", is_rate_limit: bool = False):
        """Record error."""
        with self._lock:
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
            
            if is_rate_limit:
                # Increase backoff
                current_backoff = self._current_multiplier.get(key, 1.0)
                new_backoff = min(
                    current_backoff * self.config.backoff_multiplier,
                    self.config.max_backoff_seconds
                )
                self._current_multiplier[key] = new_backoff
                
                # Set backoff period
                self._backoff_until[key] = time.time() + new_backoff
    
    def get_status(self, key: str = "default") -> RateLimitStatus:
        """Get current status."""
        return self._base_limiter.get_status(key)
    
    def reset(self, key: str = "default"):
        """Reset limiter."""
        with self._lock:
            self._base_limiter.reset(key)
            self._error_counts.pop(key, None)
            self._success_counts.pop(key, None)
            self._backoff_until.pop(key, None)
            self._current_multiplier.pop(key, None)


# ============================================================================
# RATE LIMIT MANAGER
# ============================================================================

class RateLimitManager:
    """
    Central rate limit manager.
    Manages multiple limiters for different endpoints/services.
    """
    
    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self.default_config = default_config or RateLimitConfig()
        self._limiters: Dict[str, BaseRateLimiter] = {}
        self._endpoint_configs: Dict[str, EndpointConfig] = {}
        self._global_limiter: Optional[BaseRateLimiter] = None
        self._stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        
        # Create default global limiter
        self._global_limiter = self._create_limiter(self.default_config)
    
    def _create_limiter(self, config: RateLimitConfig) -> BaseRateLimiter:
        """Create limiter based on algorithm."""
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return TokenBucketLimiter(config)
        elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return SlidingWindowLimiter(config)
        elif config.algorithm == RateLimitAlgorithm.ADAPTIVE:
            return AdaptiveRateLimiter(config)
        else:
            return TokenBucketLimiter(config)
    
    def configure_endpoint(self, endpoint_config: EndpointConfig):
        """Configure rate limits for specific endpoint."""
        with self._lock:
            self._endpoint_configs[endpoint_config.endpoint] = endpoint_config
            
            # Create limiter for endpoint
            config = RateLimitConfig(
                requests_per_second=endpoint_config.requests_per_second,
                requests_per_minute=endpoint_config.requests_per_minute,
                burst_size=endpoint_config.burst_size,
                algorithm=self.default_config.algorithm,
            )
            self._limiters[endpoint_config.endpoint] = self._create_limiter(config)
    
    def acquire(
        self,
        endpoint: str = "default",
        key: str = "default",
        weight: Optional[int] = None,
    ) -> RateLimitStatus:
        """Acquire rate limit permission."""
        with self._lock:
            # Get endpoint config
            endpoint_config = self._endpoint_configs.get(endpoint)
            if weight is None:
                weight = endpoint_config.weight if endpoint_config else 1
            
            # Check global limit first
            global_status = self._global_limiter.acquire(key, weight)
            if global_status.result != RateLimitResult.ALLOWED:
                self._record_stat(endpoint, "global_limited")
                return global_status
            
            # Check endpoint-specific limit
            limiter = self._limiters.get(endpoint)
            if limiter:
                status = limiter.acquire(key, weight)
                if status.result != RateLimitResult.ALLOWED:
                    self._record_stat(endpoint, "endpoint_limited")
                    return status
            
            self._record_stat(endpoint, "allowed")
            return RateLimitStatus(
                result=RateLimitResult.ALLOWED,
                remaining=global_status.remaining,
                reset_at=global_status.reset_at,
                limit=global_status.limit,
            )
    
    async def acquire_async(
        self,
        endpoint: str = "default",
        key: str = "default",
        weight: Optional[int] = None,
        wait: bool = True,
        max_wait: float = 60.0,
    ) -> RateLimitStatus:
        """Acquire with async waiting."""
        start_time = time.time()
        
        while True:
            status = self.acquire(endpoint, key, weight)
            
            if status.result == RateLimitResult.ALLOWED:
                return status
            
            if not wait:
                return status
            
            # Check max wait
            elapsed = time.time() - start_time
            if elapsed >= max_wait:
                return status
            
            # Wait and retry
            wait_time = min(status.retry_after, max_wait - elapsed)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
    
    def record_response(
        self,
        endpoint: str,
        key: str = "default",
        success: bool = True,
        is_rate_limit_error: bool = False,
    ):
        """Record response for adaptive limiting."""
        limiter = self._limiters.get(endpoint)
        if isinstance(limiter, AdaptiveRateLimiter):
            if success:
                limiter.record_success(key)
            else:
                limiter.record_error(key, is_rate_limit_error)
        
        # Also update global if adaptive
        if isinstance(self._global_limiter, AdaptiveRateLimiter):
            if success:
                self._global_limiter.record_success(key)
            else:
                self._global_limiter.record_error(key, is_rate_limit_error)
    
    def _record_stat(self, endpoint: str, stat_type: str):
        """Record statistics."""
        if endpoint not in self._stats:
            self._stats[endpoint] = {
                'allowed': 0,
                'global_limited': 0,
                'endpoint_limited': 0,
            }
        self._stats[endpoint][stat_type] = self._stats[endpoint].get(stat_type, 0) + 1
    
    def get_stats(self) -> Dict:
        """Get rate limit statistics."""
        with self._lock:
            return {
                'endpoints': self._stats.copy(),
                'global_status': self._global_limiter.get_status().remaining if self._global_limiter else 0,
            }
    
    def reset(self, endpoint: Optional[str] = None, key: str = "default"):
        """Reset rate limiters."""
        with self._lock:
            if endpoint:
                limiter = self._limiters.get(endpoint)
                if limiter:
                    limiter.reset(key)
            else:
                for limiter in self._limiters.values():
                    limiter.reset(key)
                if self._global_limiter:
                    self._global_limiter.reset(key)


# ============================================================================
# DECORATORS
# ============================================================================

def rate_limited(
    endpoint: str = "default",
    weight: int = 1,
    wait: bool = True,
    max_wait: float = 60.0,
):
    """Decorator for rate limiting functions."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_rate_limit_manager()
            status = await manager.acquire_async(endpoint, weight=weight, wait=wait, max_wait=max_wait)
            
            if status.result != RateLimitResult.ALLOWED:
                raise RateLimitExceeded(f"Rate limit exceeded for {endpoint}", status)
            try:
            
                result = await func(*args, **kwargs)
                manager.record_response(endpoint, success=True)
                return result
            except Exception as e:
                is_rate_limit = "rate limit" in str(e).lower() or "429" in str(e)
                manager.record_response(endpoint, success=False, is_rate_limit_error=is_rate_limit)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_rate_limit_manager()
            status = manager.acquire(endpoint, weight=weight)
            
            if status.result != RateLimitResult.ALLOWED:
                raise RateLimitExceeded(f"Rate limit exceeded for {endpoint}", status)
            try:
            
                result = func(*args, **kwargs)
                manager.record_response(endpoint, success=True)
                return result
            except Exception as e:
                is_rate_limit = "rate limit" in str(e).lower() or "429" in str(e)
                manager.record_response(endpoint, success=False, is_rate_limit_error=is_rate_limit)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception."""
    
    def __init__(self, message: str, status: RateLimitStatus):
        super().__init__(message)
        self.status = status


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_rate_limit_manager: Optional[RateLimitManager] = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get global rate limit manager."""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
    return _rate_limit_manager


def configure_rate_limits(config: RateLimitConfig):
    """Configure global rate limits."""
    global _rate_limit_manager
    _rate_limit_manager = RateLimitManager(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'RateLimitAlgorithm', 'RateLimitResult', 'RateLimitConfig',
    'RateLimitStatus', 'EndpointConfig', 'BaseRateLimiter',
    'TokenBucketLimiter', 'SlidingWindowLimiter', 'AdaptiveRateLimiter',
    'RateLimitManager', 'rate_limited', 'RateLimitExceeded',
    'get_rate_limit_manager', 'configure_rate_limits',
]
