"""
Elite Trading Bot - Rate Limiter

This module provides rate limiting functionality to ensure API requests
comply with service provider limits and avoid being blocked.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

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


class TokenBucket:
    """
    Token bucket algorithm implementation for rate limiting.
    
    The token bucket algorithm works by having a bucket that is filled with tokens
    at a constant rate. When a request is made, a token is removed from the bucket.
    If the bucket is empty, the request is delayed until a token becomes available.
    """
    
    def __init__(self, 
                 rate: float, 
                 capacity: int,
                 initial_tokens: Optional[int] = None):
        """
        Initialize the token bucket.
        
        Args:
            rate: Token refill rate per second
            capacity: Maximum number of tokens in the bucket
            initial_tokens: Initial number of tokens (defaults to capacity)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.time()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from the bucket, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Wait time in seconds
        """
        if tokens > self.capacity:
            raise ValueError(f"Cannot acquire {tokens} tokens (exceeds capacity {self.capacity})")
        
        # Refill tokens based on elapsed time
        self._refill()
        
        # Calculate wait time if not enough tokens
        if self.tokens < tokens:
            wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self._refill()  # Refill again after waiting
        
        # Acquire tokens
        self.tokens -= tokens
        
        return 0.0  # No wait time if enough tokens were available
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate new tokens
        new_tokens = elapsed * self.rate
        
        # Update tokens and last refill time
        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now


class SlidingWindowCounter:
    """
    Sliding window counter for rate limiting.
    
    The sliding window counter keeps track of request counts within a time window,
    allowing for more precise rate limiting than the token bucket algorithm.
    """
    
    def __init__(self, window_size: int, max_requests: int):
        """
        Initialize the sliding window counter.
        
        Args:
            window_size: Window size in seconds
            max_requests: Maximum number of requests allowed in the window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []  # List of request timestamps
    
    async def acquire(self) -> float:
        """
        Acquire permission to make a request, waiting if necessary.
        
        Returns:
            Wait time in seconds
        """
        now = time.time()
        
        # Remove expired requests
        cutoff = now - self.window_size
        self.requests = [ts for ts in self.requests if ts > cutoff]
        
        # Check if we've reached the limit
        if len(self.requests) >= self.max_requests:
            # Calculate wait time until oldest request expires
            wait_time = self.requests[0] + self.window_size - now
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # After waiting, remove expired requests again
                now = time.time()
                cutoff = now - self.window_size
                self.requests = [ts for ts in self.requests if ts > cutoff]
        
        # Add current request
        self.requests.append(now)
        
        return 0.0  # No wait time if under the limit


class RateLimiter:
    """
    Rate limiter for API requests to multiple services.
    
    Features:
    - Support for multiple rate limiting algorithms
    - Per-service rate limits
    - Per-endpoint rate limits
    - Automatic waiting for rate limit compliance
    - Rate limit tracking and statistics
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Service-level rate limiters
        self.service_limiters: Dict[str, TokenBucket] = {}
        
        # Endpoint-level rate limiters
        self.endpoint_limiters: Dict[str, Dict[str, SlidingWindowCounter]] = {}
        
        # Rate limit tracking
        self.request_counts: Dict[str, int] = {}
        self.wait_times: Dict[str, float] = {}
        
        logger.info("RateLimiter initialized")
    
    def add_service_limit(self, 
                         service_name: str, 
                         rate: float, 
                         capacity: int):
        """
        Add a service-level rate limit.
        
        Args:
            service_name: Name of the service
            rate: Requests per second
            capacity: Maximum burst capacity
        """
        self.service_limiters[service_name] = TokenBucket(rate, capacity)
        logger.info(f"Added service rate limit for {service_name}: {rate} req/s, capacity {capacity}")
    
    def add_endpoint_limit(self, 
                          service_name: str, 
                          endpoint: str, 
                          window_size: int, 
                          max_requests: int):
        """
        Add an endpoint-level rate limit.
        
        Args:
            service_name: Name of the service
            endpoint: API endpoint
            window_size: Window size in seconds
            max_requests: Maximum requests in window
        """
        if service_name not in self.endpoint_limiters:
            self.endpoint_limiters[service_name] = {}
        
        self.endpoint_limiters[service_name][endpoint] = SlidingWindowCounter(window_size, max_requests)
        logger.info(f"Added endpoint rate limit for {service_name}/{endpoint}: {max_requests} req/{window_size}s")
    
    async def acquire(self, 
                     service_name: str, 
                     endpoint: Optional[str] = None) -> float:
        """
        Acquire permission to make a request, waiting if necessary.
        
        Args:
            service_name: Name of the service
            endpoint: Optional API endpoint
            
        Returns:
            Wait time in seconds
        """
        total_wait_time = 0.0
        
        # Track request count
        self.request_counts[service_name] = self.request_counts.get(service_name, 0) + 1
        
        # Apply service-level rate limit
        if service_name in self.service_limiters:
            service_wait = await self.service_limiters[service_name].acquire()
            total_wait_time += service_wait
        
        # Apply endpoint-level rate limit
        if endpoint and service_name in self.endpoint_limiters and endpoint in self.endpoint_limiters[service_name]:
            endpoint_wait = await self.endpoint_limiters[service_name][endpoint].acquire()
            total_wait_time += endpoint_wait
        
        # Track wait time
        if total_wait_time > 0:
            self.wait_times[service_name] = self.wait_times.get(service_name, 0.0) + total_wait_time
            logger.debug(f"Rate limit wait for {service_name}: {total_wait_time:.2f}s")
        
        return total_wait_time
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get rate limiting statistics.
        
        Returns:
            Dictionary of rate limiting statistics by service
        """
        stats = {}
        
        for service_name in set(list(self.service_limiters.keys()) + list(self.request_counts.keys())):
            service_stats = {
                "requests": self.request_counts.get(service_name, 0),
                "wait_time": self.wait_times.get(service_name, 0.0),
            }
            
            if service_name in self.service_limiters:
                limiter = self.service_limiters[service_name]
                service_stats["rate"] = limiter.rate
                service_stats["capacity"] = limiter.capacity
                service_stats["available_tokens"] = limiter.tokens
            
            if service_name in self.endpoint_limiters:
                service_stats["endpoints"] = len(self.endpoint_limiters[service_name])
            
            stats[service_name] = service_stats
        
        return stats
    
    def reset_stats(self):
        """Reset rate limiting statistics."""
        self.request_counts = {}
        self.wait_times = {}
        logger.info("Rate limiting statistics reset")


# Common rate limit configurations for popular financial APIs
COMMON_RATE_LIMITS = {
    "alpha_vantage": {
        "service": (5/60, 5),  # 5 requests per minute
    },
    "yahoo_finance": {
        "service": (2, 10),  # 2 requests per second, burst of 10
    },
    "binance": {
        "service": (10, 50),  # 10 requests per second, burst of 50
        "endpoints": {
            "klines": (60, 1000),  # 1000 requests per minute
            "depth": (10, 50),     # 50 requests per 10 seconds
            "trades": (60, 1000)   # 1000 requests per minute
        }
    },
    "coinbase": {
        "service": (3, 15),  # 3 requests per second, burst of 15
    },
    "iex_cloud": {
        "service": (5, 25),  # 5 requests per second, burst of 25
    },
    "finnhub": {
        "service": (1, 30),  # 1 request per second, burst of 30
    }
}


def create_common_rate_limiter() -> RateLimiter:
    """
    Create a rate limiter with common configurations.
    
    Returns:
        Configured RateLimiter
    """
    limiter = RateLimiter()
    
    for service_name, config in COMMON_RATE_LIMITS.items():
        # Add service-level limit
        if "service" in config:
            rate, capacity = config["service"]
            limiter.add_service_limit(service_name, rate, capacity)
        
        # Add endpoint-level limits
        if "endpoints" in config:
            for endpoint, (window_size, max_requests) in config["endpoints"].items():
                limiter.add_endpoint_limit(service_name, endpoint, window_size, max_requests)
    
    return limiter
