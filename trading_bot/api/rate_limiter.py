"""
API rate limiting system
Prevents exceeding broker/exchange rate limits
"""

import asyncio
import time
import logging
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

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


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int = 100
    window_seconds: int = 60
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_size: Optional[int] = None  # For token bucket
    refill_rate: Optional[float] = None  # Tokens per second


@dataclass
class RateLimitStats:
    """Rate limit statistics"""
    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    delayed_requests: int = 0
    current_usage: int = 0
    last_request_time: Optional[datetime] = None


class RateLimiter:
    """
    Flexible rate limiter with multiple strategies
    Prevents API rate limit violations
    """
    
    def __init__(self, config: RateLimitConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.stats = RateLimitStats()
        
        # Request tracking
        self.request_times: deque = deque(maxlen=config.max_requests * 2)
        
        # Token bucket state
        self.tokens = config.burst_size or config.max_requests
        self.last_refill = time.time()
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        logger.info(f"Rate limiter '{name}' initialized: {config.max_requests} req/{config.window_seconds}s")
    
    async def acquire(self, wait: bool = True) -> bool:
        """
        Acquire permission to make a request
        
        Args:
            wait: If True, wait for permission. If False, return immediately
            
        Returns:
            True if request allowed, False if rejected
        """
        async with self.lock:
            self.stats.total_requests += 1
            
            if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._sliding_window_acquire(wait)
            elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._token_bucket_acquire(wait)
            elif self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._fixed_window_acquire(wait)
            else:
                return await self._sliding_window_acquire(wait)
    
    async def _sliding_window_acquire(self, wait: bool) -> bool:
        """Sliding window rate limiting"""
        now = time.time()
        window_start = now - self.config.window_seconds
        
        # Remove old requests
        while self.request_times and self.request_times[0] < window_start:
            self.request_times.popleft()
        
        # Check if we can proceed
        current_count = len(self.request_times)
        self.stats.current_usage = current_count
        
        if current_count < self.config.max_requests:
            self.request_times.append(now)
            self.stats.allowed_requests += 1
            self.stats.last_request_time = datetime.now()
            return True
        
        if not wait:
            self.stats.rejected_requests += 1
            logger.warning(f"Rate limit exceeded for '{self.name}': {current_count}/{self.config.max_requests}")
            return False
        
        # Calculate wait time
        oldest_request = self.request_times[0]
        wait_time = (oldest_request + self.config.window_seconds) - now
        
        if wait_time > 0:
            logger.info(f"Rate limit reached for '{self.name}', waiting {wait_time:.2f}s")
            self.stats.delayed_requests += 1
            await asyncio.sleep(wait_time)
            
            # Retry after waiting
            return await self._sliding_window_acquire(wait=False)
        
        return False
    
    async def _token_bucket_acquire(self, wait: bool) -> bool:
        """Token bucket rate limiting"""
        now = time.time()
        
        # Refill tokens
        time_passed = now - self.last_refill
        refill_rate = self.config.refill_rate or (self.config.max_requests / self.config.window_seconds)
        tokens_to_add = time_passed * refill_rate
        
        self.tokens = min(
            self.config.burst_size or self.config.max_requests,
            self.tokens + tokens_to_add
        )
        self.last_refill = now
        
        self.stats.current_usage = int(self.config.max_requests - self.tokens)
        
        # Check if we have tokens
        if self.tokens >= 1:
            self.tokens -= 1
            self.stats.allowed_requests += 1
            self.stats.last_request_time = datetime.now()
            return True
        
        if not wait:
            self.stats.rejected_requests += 1
            return False
        
        # Wait for token
        wait_time = (1 - self.tokens) / refill_rate
        logger.info(f"Token bucket empty for '{self.name}', waiting {wait_time:.2f}s")
        self.stats.delayed_requests += 1
        await asyncio.sleep(wait_time)
        
        return await self._token_bucket_acquire(wait=False)
    
    async def _fixed_window_acquire(self, wait: bool) -> bool:
        """Fixed window rate limiting"""
        now = time.time()
        window_start = int(now / self.config.window_seconds) * self.config.window_seconds
        
        # Reset if new window
        if not self.request_times or self.request_times[0] < window_start:
            self.request_times.clear()
        
        current_count = len(self.request_times)
        self.stats.current_usage = current_count
        
        if current_count < self.config.max_requests:
            self.request_times.append(now)
            self.stats.allowed_requests += 1
            self.stats.last_request_time = datetime.now()
            return True
        
        if not wait:
            self.stats.rejected_requests += 1
            return False
        
        # Wait for next window
        next_window = window_start + self.config.window_seconds
        wait_time = next_window - now
        
        logger.info(f"Fixed window full for '{self.name}', waiting {wait_time:.2f}s")
        self.stats.delayed_requests += 1
        await asyncio.sleep(wait_time)
        
        return await self._fixed_window_acquire(wait=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            'name': self.name,
            'config': {
                'max_requests': self.config.max_requests,
                'window_seconds': self.config.window_seconds,
                'strategy': self.config.strategy.value
            },
            'stats': {
                'total_requests': self.stats.total_requests,
                'allowed_requests': self.stats.allowed_requests,
                'rejected_requests': self.stats.rejected_requests,
                'delayed_requests': self.stats.delayed_requests,
                'current_usage': self.stats.current_usage,
                'last_request_time': self.stats.last_request_time.isoformat() if self.stats.last_request_time else None
            },
            'utilization_pct': (self.stats.current_usage / self.config.max_requests * 100) if self.config.max_requests > 0 else 0
        }
    
    def reset(self):
        """Reset rate limiter state"""
        self.request_times.clear()
        self.tokens = self.config.burst_size or self.config.max_requests
        self.last_refill = time.time()
        self.stats = RateLimitStats()
        logger.info(f"Rate limiter '{self.name}' reset")


class MultiRateLimiter:
    """
    Manages multiple rate limiters for different endpoints/brokers
    """
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        
    def add_limiter(self, name: str, config: RateLimitConfig):
        """Add a rate limiter"""
        self.limiters[name] = RateLimiter(config, name)
        logger.info(f"Added rate limiter: {name}")
    
    async def acquire(self, name: str, wait: bool = True) -> bool:
        """Acquire from specific limiter"""
        if name not in self.limiters:
            logger.warning(f"Rate limiter '{name}' not found, allowing request")
            return True
        
        return await self.limiters[name].acquire(wait)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all limiters"""
        return {
            name: limiter.get_stats()
            for name, limiter in self.limiters.items()
        }
    
    def reset_all(self):
        """Reset all limiters"""
        for limiter in self.limiters.values():
            limiter.reset()


# Decorator for rate-limited functions
def rate_limited(limiter: RateLimiter, wait: bool = True):
    """
    Decorator to rate limit async functions
    
    Usage:
        @rate_limited(my_limiter)
        async def api_call():
            ...
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            if await limiter.acquire(wait):
                return await func(*args, **kwargs)
            else:
                raise Exception(f"Rate limit exceeded for {func.__name__}")
        return wrapper
    return decorator


# Pre-configured limiters for common brokers
BROKER_RATE_LIMITS = {
    'mt5': RateLimitConfig(max_requests=100, window_seconds=60),
    'binance': RateLimitConfig(max_requests=1200, window_seconds=60),
    'coinbase': RateLimitConfig(max_requests=10, window_seconds=1),
    'kraken': RateLimitConfig(max_requests=15, window_seconds=1),
    'ftx': RateLimitConfig(max_requests=30, window_seconds=1),
    'bybit': RateLimitConfig(max_requests=120, window_seconds=60),
}


def create_broker_limiter(broker: str) -> RateLimiter:
    """Create rate limiter for specific broker"""
    config = BROKER_RATE_LIMITS.get(broker.lower())
    if not config:
        logger.warning(f"Unknown broker '{broker}', using default limits")
        config = RateLimitConfig()
    
    return RateLimiter(config, broker)
