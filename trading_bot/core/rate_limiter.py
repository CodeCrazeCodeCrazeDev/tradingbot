"""
Rate Limiter for API Calls
Prevents API bans and ensures fair usage of external services.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""
    name: str
    max_requests: int
    window_seconds: float
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_limit: Optional[int] = None  # For token bucket
    retry_after_seconds: float = 1.0


@dataclass
class RateLimitStats:
    """Statistics for rate limiting."""
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    total_wait_time_seconds: float = 0.0
    last_request_time: Optional[datetime] = None


class RateLimiter:
    """
    Rate limiter for API calls.
    
    Features:
    - Multiple rate limiting strategies
    - Per-endpoint limits
    - Automatic retry with backoff
    - Statistics tracking
    """
    
    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        try:
            self.default_config = default_config or RateLimitConfig(
                name="default",
                max_requests=60,
                window_seconds=60.0
            )
        
            # Per-endpoint configurations
            self._configs: Dict[str, RateLimitConfig] = {}
        
            # Request tracking (sliding window)
            self._request_times: Dict[str, deque] = {}
        
            # Token bucket state
            self._tokens: Dict[str, float] = {}
            self._last_refill: Dict[str, float] = {}
        
            # Statistics
            self._stats: Dict[str, RateLimitStats] = {}
        
            # Lock for thread safety
            self._lock = asyncio.Lock()
        
            logger.info("RateLimiter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def configure(self, endpoint: str, config: RateLimitConfig):
        """Configure rate limit for a specific endpoint."""
        try:
            self._configs[endpoint] = config
            self._request_times[endpoint] = deque()
            self._stats[endpoint] = RateLimitStats()
        
            if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                self._tokens[endpoint] = float(config.burst_limit or config.max_requests)
                self._last_refill[endpoint] = time.time()
        
            logger.info(f"Configured rate limit for {endpoint}: {config.max_requests}/{config.window_seconds}s")
        except Exception as e:
            logger.error(f"Error in configure: {e}")
            raise
    
    async def acquire(self, endpoint: str = "default") -> bool:
        """
        Acquire permission to make a request.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        try:
            async with self._lock:
                config = self._configs.get(endpoint, self.default_config)
            
                # Initialize if needed
                if endpoint not in self._request_times:
                    self._request_times[endpoint] = deque()
                    self._stats[endpoint] = RateLimitStats()
            
                stats = self._stats[endpoint]
                stats.total_requests += 1
            
                allowed = False
            
                if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                    allowed = self._check_sliding_window(endpoint, config)
                elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                    allowed = self._check_token_bucket(endpoint, config)
                elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
                    allowed = self._check_fixed_window(endpoint, config)
                else:
                    allowed = self._check_sliding_window(endpoint, config)
            
                if allowed:
                    stats.allowed_requests += 1
                    stats.last_request_time = datetime.now()
                else:
                    stats.blocked_requests += 1
            
                return allowed
        except Exception as e:
            logger.error(f"Error in acquire: {e}")
            raise
    
    def _check_sliding_window(self, endpoint: str, config: RateLimitConfig) -> bool:
        """Check rate limit using sliding window."""
        try:
            now = time.time()
            window_start = now - config.window_seconds
        
            # Remove old requests
            requests = self._request_times[endpoint]
            while requests and requests[0] < window_start:
                requests.popleft()
        
            # Check if under limit
            if len(requests) < config.max_requests:
                requests.append(now)
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _check_sliding_window: {e}")
            raise
    
    def _check_token_bucket(self, endpoint: str, config: RateLimitConfig) -> bool:
        """Check rate limit using token bucket."""
        try:
            now = time.time()
        
            # Refill tokens
            if endpoint not in self._tokens:
                self._tokens[endpoint] = float(config.burst_limit or config.max_requests)
                self._last_refill[endpoint] = now
        
            elapsed = now - self._last_refill[endpoint]
            refill_rate = config.max_requests / config.window_seconds
            self._tokens[endpoint] = min(
                config.burst_limit or config.max_requests,
                self._tokens[endpoint] + elapsed * refill_rate
            )
            self._last_refill[endpoint] = now
        
            # Check if token available
            if self._tokens[endpoint] >= 1:
                self._tokens[endpoint] -= 1
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _check_token_bucket: {e}")
            raise
    
    def _check_fixed_window(self, endpoint: str, config: RateLimitConfig) -> bool:
        """Check rate limit using fixed window."""
        try:
            now = time.time()
            window_start = int(now / config.window_seconds) * config.window_seconds
        
            # Count requests in current window
            requests = self._request_times[endpoint]
            count = sum(1 for t in requests if t >= window_start)
        
            if count < config.max_requests:
                requests.append(now)
                # Clean old entries
                while requests and requests[0] < window_start - config.window_seconds:
                    requests.popleft()
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _check_fixed_window: {e}")
            raise
    
    async def wait_and_acquire(self, endpoint: str = "default", max_wait: float = 30.0) -> bool:
        """
        Wait for rate limit and acquire permission.
        
        Args:
            endpoint: The endpoint to rate limit
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if acquired, False if timed out
        """
        try:
            start_time = time.time()
            config = self._configs.get(endpoint, self.default_config)
        
            while time.time() - start_time < max_wait:
                if await self.acquire(endpoint):
                    wait_time = time.time() - start_time
                    if endpoint in self._stats:
                        self._stats[endpoint].total_wait_time_seconds += wait_time
                    return True
            
                await asyncio.sleep(config.retry_after_seconds)
        
            return False
        except Exception as e:
            logger.error(f"Error in wait_and_acquire: {e}")
            raise
    
    def get_wait_time(self, endpoint: str = "default") -> float:
        """Get estimated wait time until next request is allowed."""
        try:
            config = self._configs.get(endpoint, self.default_config)
            requests = self._request_times.get(endpoint, deque())
        
            if len(requests) < config.max_requests:
                return 0.0
        
            # Calculate when oldest request will expire
            if requests:
                oldest = requests[0]
                wait_time = (oldest + config.window_seconds) - time.time()
                return max(0.0, wait_time)
        
            return 0.0
        except Exception as e:
            logger.error(f"Error in get_wait_time: {e}")
            raise
    
    def get_stats(self, endpoint: str = "default") -> RateLimitStats:
        """Get statistics for an endpoint."""
        return self._stats.get(endpoint, RateLimitStats())
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all endpoints."""
        return {
            endpoint: {
                'total_requests': stats.total_requests,
                'allowed_requests': stats.allowed_requests,
                'blocked_requests': stats.blocked_requests,
                'block_rate': stats.blocked_requests / stats.total_requests if stats.total_requests > 0 else 0,
                'total_wait_time_seconds': round(stats.total_wait_time_seconds, 2),
                'last_request_time': stats.last_request_time.isoformat() if stats.last_request_time else None
            }
            for endpoint, stats in self._stats.items()
        }
    
    def reset(self, endpoint: Optional[str] = None):
        """Reset rate limit state."""
        try:
            if endpoint:
                if endpoint in self._request_times:
                    self._request_times[endpoint].clear()
                if endpoint in self._tokens:
                    config = self._configs.get(endpoint, self.default_config)
                    self._tokens[endpoint] = float(config.burst_limit or config.max_requests)
            else:
                for ep in self._request_times:
                    self._request_times[ep].clear()
                for ep in self._tokens:
                    config = self._configs.get(ep, self.default_config)
                    self._tokens[ep] = float(config.burst_limit or config.max_requests)
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


def rate_limited(
    limiter: RateLimiter,
    endpoint: str = "default",
    max_wait: float = 30.0
):
    """
    Decorator for rate-limited async functions.
    
    Usage:
        @rate_limited(limiter, "api_endpoint")
        async def call_api():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if await limiter.wait_and_acquire(endpoint, max_wait):
                    return await func(*args, **kwargs)
                else:
                    raise TimeoutError(f"Rate limit timeout for {endpoint}")
            except Exception as e:
                logger.error(f"Error in wrapper: {e}")
                raise
        return wrapper
    return decorator


# Pre-configured limiters for common APIs
class CommonRateLimits:
    """Pre-configured rate limits for common APIs."""
    
    @staticmethod
    def binance() -> RateLimitConfig:
        """Binance API rate limit (1200 requests/minute)."""
        return RateLimitConfig(
            name="binance",
            max_requests=1200,
            window_seconds=60.0,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
    
    @staticmethod
    def coinbase() -> RateLimitConfig:
        """Coinbase API rate limit (10 requests/second)."""
        return RateLimitConfig(
            name="coinbase",
            max_requests=10,
            window_seconds=1.0,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
    
    @staticmethod
    def alpaca() -> RateLimitConfig:
        """Alpaca API rate limit (200 requests/minute)."""
        return RateLimitConfig(
            name="alpaca",
            max_requests=200,
            window_seconds=60.0,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
    
    @staticmethod
    def interactive_brokers() -> RateLimitConfig:
        """Interactive Brokers rate limit (50 requests/second)."""
        return RateLimitConfig(
            name="interactive_brokers",
            max_requests=50,
            window_seconds=1.0,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_limit=100
        )


# Singleton instance
_default_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the default rate limiter."""
    try:
        global _default_limiter
        if _default_limiter is None:
            _default_limiter = RateLimiter()
            # Configure common endpoints
            _default_limiter.configure("binance", CommonRateLimits.binance())
            _default_limiter.configure("coinbase", CommonRateLimits.coinbase())
            _default_limiter.configure("alpaca", CommonRateLimits.alpaca())
        return _default_limiter
    except Exception as e:
        logger.error(f"Error in get_rate_limiter: {e}")
        raise


__all__ = [
    'RateLimiter',
    'RateLimitConfig',
    'RateLimitStats',
    'RateLimitStrategy',
    'CommonRateLimits',
    'rate_limited',
    'get_rate_limiter'
]
