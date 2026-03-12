"""
API Rate Limiter with token bucket and exponential backoff.
Prevents API bans and ensures compliance with rate limits.
"""

import time
import asyncio
from collections import deque
from typing import Dict, Optional
from loguru import logger

import logging

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



class TokenBucketRateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, rate: int = 10, per: float = 1.0, burst: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
            burst: Maximum burst size
        """
        self.rate = rate
        self.per = per
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        
        logger.info(f"Rate limiter initialized: {rate} req/{per}s, burst={burst}")
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on rate
        tokens_to_add = elapsed * (self.rate / self.per)
        self.tokens = min(self.burst, self.tokens + tokens_to_add)
        self.last_update = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if acquired, False otherwise
        """
        self._refill_tokens()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def wait_for_token(self, tokens: int = 1) -> float:
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time waited in seconds
        """
        start = time.time()
        
        while not self.acquire(tokens):
            time.sleep(0.01)  # Small sleep to avoid busy waiting
        
        waited = time.time() - start
        if waited > 0.1:
            logger.warning(f"Rate limit: waited {waited:.2f}s for {tokens} tokens")
        
        return waited
    
    async def wait_for_token_async(self, tokens: int = 1) -> float:
        """Async version of wait_for_token."""
        start = time.time()
        
        while not self.acquire(tokens):
            await asyncio.sleep(0.01)
        
        waited = time.time() - start
        if waited > 0.1:
            logger.warning(f"Rate limit: waited {waited:.2f}s for {tokens} tokens")
        
        return waited


class ExponentialBackoff:
    """Exponential backoff for retrying failed requests."""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, 
                 max_retries: int = 5):
        """
        Initialize exponential backoff.
        
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            max_retries: Maximum number of retries
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.attempt = 0
        
    def get_delay(self) -> float:
        """Get delay for current attempt."""
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        self.attempt += 1
        return delay
    
    def reset(self):
        """Reset attempt counter."""
        self.attempt = 0
    
    def should_retry(self) -> bool:
        """Check if should retry."""
        return self.attempt < self.max_retries


class APIRateLimitManager:
    """Manage rate limits for multiple APIs."""
    
    def __init__(self):
        """Initialize rate limit manager."""
        self.limiters: Dict[str, TokenBucketRateLimiter] = {}
        self.backoffs: Dict[str, ExponentialBackoff] = {}
        
        logger.info("API rate limit manager initialized")
    
    def add_api(self, api_name: str, rate: int, per: float = 1.0, burst: int = None):
        """
        Add API with rate limit.
        
        Args:
            api_name: Name of the API
            rate: Requests per time period
            per: Time period in seconds
            burst: Burst size (default: 2x rate)
        """
        if burst is None:
            burst = rate * 2
        
        self.limiters[api_name] = TokenBucketRateLimiter(rate, per, burst)
        self.backoffs[api_name] = ExponentialBackoff()
        
        logger.info(f"Added rate limit for {api_name}: {rate} req/{per}s")
    
    def acquire(self, api_name: str, tokens: int = 1) -> bool:
        """Acquire tokens for API call."""
        if api_name not in self.limiters:
            logger.warning(f"No rate limit configured for {api_name}")
            return True
        
        return self.limiters[api_name].acquire(tokens)
    
    def wait_for_token(self, api_name: str, tokens: int = 1) -> float:
        """Wait for tokens to be available."""
        if api_name not in self.limiters:
            return 0.0
        
        return self.limiters[api_name].wait_for_token(tokens)
    
    async def wait_for_token_async(self, api_name: str, tokens: int = 1) -> float:
        """Async wait for tokens."""
        if api_name not in self.limiters:
            return 0.0
        
        return await self.limiters[api_name].wait_for_token_async(tokens)
    
    def handle_error(self, api_name: str, error_code: Optional[int] = None) -> float:
        """
        Handle API error with exponential backoff.
        
        Args:
            api_name: Name of the API
            error_code: HTTP error code
            
        Returns:
            Delay before retry
        """
        if api_name not in self.backoffs:
            self.backoffs[api_name] = ExponentialBackoff()
        
        backoff = self.backoffs[api_name]
        
        # Check if rate limit error
        if error_code in [429, 503]:
            delay = backoff.get_delay()
            logger.warning(f"{api_name} rate limit hit, backing off {delay:.1f}s")
            return delay
        
        return 0.0
    
    def reset_backoff(self, api_name: str):
        """Reset backoff for successful request."""
        if api_name in self.backoffs:
            self.backoffs[api_name].reset()


# Global rate limit manager instance
_rate_limit_manager = APIRateLimitManager()


def get_rate_limit_manager() -> APIRateLimitManager:
    """Get global rate limit manager."""
    return _rate_limit_manager


# Pre-configure common APIs
def setup_common_apis():
    """Setup rate limits for common trading APIs."""
    manager = get_rate_limit_manager()
    
    # MetaTrader 5
    manager.add_api('mt5', rate=100, per=1.0)
    
    # Alpha Vantage
    manager.add_api('alphavantage', rate=5, per=60.0)
    
    # Yahoo Finance
    manager.add_api('yahoo', rate=2000, per=3600.0)
    
    # Binance
    manager.add_api('binance', rate=1200, per=60.0)
    
    # Coinbase
    manager.add_api('coinbase', rate=10, per=1.0)
    
    logger.info("Common API rate limits configured")


# Auto-setup on import
setup_common_apis()
