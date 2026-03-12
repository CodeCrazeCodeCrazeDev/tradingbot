"""
Retry Policy - Standardized retry logic with backoff and jitter

This module provides standardized retry policies for all IO operations
with configurable max attempts, time budgets, and exponential backoff with jitter.
"""

import asyncio
import logging
import random
import time
from typing import Any, Callable, Optional, TypeVar, Union, Tuple
from functools import wraps
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

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

T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL = 'exponential'
    LINEAR = 'linear'
    CONSTANT = 'constant'


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    time_budget: Optional[float] = None  # Total time budget in seconds
    backoff_multiplier: float = 2.0
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.backoff_multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        else:  # CONSTANT
            delay = self.base_delay
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay


class RetryBudgetExceeded(Exception):
    """Raised when retry time budget is exceeded"""
    pass


class MaxRetriesExceeded(Exception):
    """Raised when max retry attempts exceeded"""
    pass


def with_retry(policy: Optional[RetryPolicy] = None, 
               retryable_exceptions: tuple = (Exception,),
               on_retry: Optional[Callable] = None):
    """
    Decorator for adding retry logic to async functions
    
    Args:
        policy: Retry policy (uses default if None)
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback called on each retry
        
    Example:
        @with_retry(RetryPolicy(max_attempts=5, base_delay=2.0))
        async def fetch_data():
            # ... code that might fail
            pass
    """
    if policy is None:
        policy = RetryPolicy()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            last_exception = None
            
            for attempt in range(1, policy.max_attempts + 1):
                try:
                    # Check time budget
                    if policy.time_budget:
                        elapsed = time.time() - start_time
                        if elapsed >= policy.time_budget:
                            raise RetryBudgetExceeded(
                                f"Time budget of {policy.time_budget}s exceeded "
                                f"after {elapsed:.1f}s"
                            )
                    
                    # Attempt the operation
                    result = await func(*args, **kwargs)
                    
                    # Success - log if retried
                    if attempt > 1:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt}"
                        )
                    
                    return result
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if attempt >= policy.max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {attempt} attempts: {e}"
                        )
                        raise MaxRetriesExceeded(
                            f"Max retries ({policy.max_attempts}) exceeded"
                        ) from e
                    
                    # Calculate delay
                    delay = policy.calculate_delay(attempt)
                    
                    # Check if delay would exceed time budget
                    if policy.time_budget:
                        elapsed = time.time() - start_time
                        if elapsed + delay >= policy.time_budget:
                            logger.warning(
                                f"{func.__name__} retry would exceed time budget, "
                                f"failing now"
                            )
                            raise RetryBudgetExceeded(
                                f"Retry would exceed time budget"
                            ) from e
                    
                    # Log retry
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt}/{policy.max_attempts}, "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt, e, delay)
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class RetryExecutor:
    """Executor for retry logic with circuit breaker pattern"""
    
    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self.failure_count = 0
        self.success_count = 0
        self.circuit_open = False
        self.circuit_open_until = 0
        self.circuit_threshold = 5  # Open circuit after N consecutive failures
        self.circuit_timeout = 60  # Keep circuit open for N seconds
    
    async def execute(self, func: Callable, *args, 
                     retryable_exceptions: tuple = (Exception,),
                     **kwargs) -> Any:
        """
        Execute function with retry logic and circuit breaker
        
        Args:
            func: Async function to execute
            *args: Function arguments
            retryable_exceptions: Exceptions to retry on
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        # Check circuit breaker
        if self.circuit_open:
            if time.time() < self.circuit_open_until:
                raise Exception("Circuit breaker is open")
            else:
                # Try to close circuit
                logger.info("Attempting to close circuit breaker")
                self.circuit_open = False
                self.failure_count = 0
        
        start_time = time.time()
        last_exception = None
        
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                # Check time budget
                if self.policy.time_budget:
                    elapsed = time.time() - start_time
                    if elapsed >= self.policy.time_budget:
                        raise RetryBudgetExceeded(
                            f"Time budget exceeded: {elapsed:.1f}s"
                        )
                
                # Execute
                result = await func(*args, **kwargs)
                
                # Success - reset failure count
                self.failure_count = 0
                self.success_count += 1
                
                return result
                
            except retryable_exceptions as e:
                last_exception = e
                self.failure_count += 1
                
                # Check circuit breaker threshold
                if self.failure_count >= self.circuit_threshold:
                    self.circuit_open = True
                    self.circuit_open_until = time.time() + self.circuit_timeout
                    logger.error(
                        f"Circuit breaker opened after {self.failure_count} failures"
                    )
                    raise Exception("Circuit breaker opened") from e
                
                # Check if we should retry
                if attempt >= self.policy.max_attempts:
                    raise MaxRetriesExceeded(
                        f"Max retries exceeded"
                    ) from e
                
                # Calculate and wait
                delay = self.policy.calculate_delay(attempt)
                logger.warning(
                    f"Retry attempt {attempt}/{self.policy.max_attempts} "
                    f"after {delay:.1f}s"
                )
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def get_stats(self) -> dict:
        """Get retry statistics"""
        return {
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'circuit_open': self.circuit_open,
            'circuit_open_until': self.circuit_open_until
        }
