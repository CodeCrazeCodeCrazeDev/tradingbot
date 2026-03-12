"""
Rate Limiter - Token bucket rate limiting with backpressure

Centralized API rate-limit handling with token bucket algorithm
and backoff with jitter for data and execution paths.
"""

import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 10.0
    burst_size: int = 20
    backoff_base: float = 1.0
    backoff_max: float = 60.0


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket
        
        Args:
            rate: Tokens per second
            capacity: Maximum tokens (burst size)
        """
        try:
            self.rate = rate
            self.capacity = capacity
            self.tokens = capacity
            self.last_update = time.time()
            self.lock = asyncio.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from bucket
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Max wait time in seconds
            
        Returns:
            True if tokens acquired, False if timeout
        """
        try:
            start_time = time.time()
        
            async with self.lock:
                while True:
                    # Refill tokens based on elapsed time
                    now = time.time()
                    elapsed = now - self.last_update
                    self.tokens = min(
                        self.capacity,
                        self.tokens + elapsed * self.rate
                    )
                    self.last_update = now
                
                    # Check if we have enough tokens
                    if self.tokens >= tokens:
                        self.tokens -= tokens
                        return True
                
                    # Check timeout
                    if timeout and (time.time() - start_time) >= timeout:
                        return False
                
                    # Calculate wait time
                    tokens_needed = tokens - self.tokens
                    wait_time = tokens_needed / self.rate
                
                    # Wait for tokens to refill
                    await asyncio.sleep(min(wait_time, 0.1))
        except Exception as e:
            logger.error(f"Error in acquire: {e}")
            raise
    
    def available_tokens(self) -> float:
        """Get current available tokens"""
        try:
            now = time.time()
            elapsed = now - self.last_update
            return min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
        except Exception as e:
            logger.error(f"Error in available_tokens: {e}")
            raise


class RateLimiter:
    """Centralized rate limiter with per-endpoint limits"""
    
    def __init__(self):
        try:
            self.buckets: Dict[str, TokenBucket] = {}
            self.configs: Dict[str, RateLimitConfig] = {}
            self.request_counts: Dict[str, int] = defaultdict(int)
            self.error_counts: Dict[str, int] = defaultdict(int)
            self.backoff_until: Dict[str, float] = defaultdict(float)
        
            logger.info("Rate limiter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def configure(self, endpoint: str, config: RateLimitConfig):
        """
        Configure rate limit for an endpoint
        
        Args:
            endpoint: Endpoint identifier
            config: Rate limit configuration
        """
        try:
            self.configs[endpoint] = config
            self.buckets[endpoint] = TokenBucket(
                rate=config.requests_per_second,
                capacity=config.burst_size
            )
            logger.info(
                f"Configured rate limit for {endpoint}: "
                f"{config.requests_per_second} req/s, burst={config.burst_size}"
            )
        except Exception as e:
            logger.error(f"Error in configure: {e}")
            raise
    
    async def acquire(self, endpoint: str, tokens: int = 1, 
                     timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make request
        
        Args:
            endpoint: Endpoint identifier
            tokens: Number of tokens (typically 1 per request)
            timeout: Max wait time
            
        Returns:
            True if acquired, False if timeout or backoff
        """
        # Check if endpoint is configured
        try:
            if endpoint not in self.buckets:
                # Auto-configure with defaults
                self.configure(endpoint, RateLimitConfig())
        
            # Check backoff
            if time.time() < self.backoff_until[endpoint]:
                wait_time = self.backoff_until[endpoint] - time.time()
                logger.warning(
                    f"Endpoint {endpoint} in backoff, waiting {wait_time:.1f}s"
                )
            
                if timeout and wait_time > timeout:
                    return False
            
                await asyncio.sleep(wait_time)
        
            # Acquire from token bucket
            bucket = self.buckets[endpoint]
            acquired = await bucket.acquire(tokens, timeout)
        
            if acquired:
                self.request_counts[endpoint] += 1
        
            return acquired
        except Exception as e:
            logger.error(f"Error in acquire: {e}")
            raise
    
    def record_error(self, endpoint: str, error: Exception):
        """
        Record error and apply backoff if needed
        
        Args:
            endpoint: Endpoint identifier
            error: Error that occurred
        """
        try:
            self.error_counts[endpoint] += 1
        
            # Check if we should apply backoff
            if self.error_counts[endpoint] >= 3:
                config = self.configs.get(endpoint, RateLimitConfig())
            
                # Calculate backoff duration with exponential increase
                backoff_duration = min(
                    config.backoff_base * (2 ** (self.error_counts[endpoint] - 3)),
                    config.backoff_max
                )
            
                # Add jitter
                import random
                backoff_duration *= (0.5 + random.random() * 0.5)
            
                self.backoff_until[endpoint] = time.time() + backoff_duration
            
                logger.warning(
                    f"Applied backoff to {endpoint} for {backoff_duration:.1f}s "
                    f"after {self.error_counts[endpoint]} errors"
                )
        except Exception as e:
            logger.error(f"Error in record_error: {e}")
            raise
    
    def record_success(self, endpoint: str):
        """
        Record successful request
        
        Args:
            endpoint: Endpoint identifier
        """
        # Reset error count on success
        try:
            if self.error_counts[endpoint] > 0:
                self.error_counts[endpoint] = max(0, self.error_counts[endpoint] - 1)
        except Exception as e:
            logger.error(f"Error in record_success: {e}")
            raise
    
    def get_stats(self, endpoint: str) -> dict:
        """Get statistics for endpoint"""
        try:
            bucket = self.buckets.get(endpoint)
            return {
                'endpoint': endpoint,
                'requests': self.request_counts[endpoint],
                'errors': self.error_counts[endpoint],
                'available_tokens': bucket.available_tokens() if bucket else 0,
                'in_backoff': time.time() < self.backoff_until[endpoint],
                'backoff_remaining': max(0, self.backoff_until[endpoint] - time.time())
            }
        except Exception as e:
            logger.error(f"Error in get_stats: {e}")
            raise
    
    def get_all_stats(self) -> Dict[str, dict]:
        """Get statistics for all endpoints"""
        return {
            endpoint: self.get_stats(endpoint)
            for endpoint in self.buckets.keys()
        }


# Global rate limiter instance
_global_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _global_limiter
