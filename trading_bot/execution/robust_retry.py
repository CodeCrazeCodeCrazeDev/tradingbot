"""
Robust Retry System with Exponential Backoff + Jitter
Implements HI-EXE-002: Robust retry with jitter/time budget

Provides intelligent retry logic with exponential backoff, jitter,
and time budget management for reliable order execution.
"""

import time
import random
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    FIXED = "fixed"


class ErrorClass(Enum):
    """Error classification for retry decisions"""
    TRANSIENT = "transient"  # Temporary, retry
    PERMANENT = "permanent"  # Don't retry
    RATE_LIMIT = "rate_limit"  # Backoff longer
    NETWORK = "network"  # Network issue
    TIMEOUT = "timeout"  # Timeout, retry
    UNKNOWN = "unknown"  # Unknown, retry cautiously


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    initial_delay: float = 0.1  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter_factor: float = 0.1  # 10% jitter
    time_budget: float = 300.0  # 5 minutes total
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    
    # Error-specific delays
    rate_limit_delay: float = 30.0
    network_delay: float = 5.0


@dataclass
class RetryAttempt:
    """Record of a retry attempt"""
    attempt_number: int
    timestamp: datetime
    delay: float
    error: Optional[Exception] = None
    error_class: Optional[ErrorClass] = None
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attempt': self.attempt_number,
            'timestamp': self.timestamp.isoformat(),
            'delay': self.delay,
            'error': str(self.error) if self.error else None,
            'error_class': self.error_class.value if self.error_class else None,
            'success': self.success
        }


class RobustRetry:
    """
    Robust retry mechanism with intelligent backoff
    
    Features:
    - Exponential backoff with jitter
    - Time budget management
    - Error classification
    - Retry statistics
    - Circuit breaker integration
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize robust retry system
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
        
        # Statistics
        self.stats = {
            'total_operations': 0,
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_after_retries': 0,
            'time_budget_exceeded': 0
        }
        
        # Retry history
        self.retry_history: List[RetryAttempt] = []
        
        logger.info(f"Robust Retry initialized (max_attempts: {self.config.max_attempts}, "
                   f"strategy: {self.config.strategy.value})")
    
    def execute(self,
               operation: Callable,
               error_classifier: Optional[Callable[[Exception], ErrorClass]] = None,
               on_retry: Optional[Callable[[int, Exception], None]] = None,
               operation_name: str = "operation") -> Any:
        """
        Execute operation with robust retry logic
        
        Args:
            operation: Function to execute
            error_classifier: Function to classify errors
            on_retry: Callback on each retry
            operation_name: Name for logging
        
        Returns:
            Result of successful operation
        
        Raises:
            Exception: If all retries exhausted
        """
        self.stats['total_operations'] += 1
        
        start_time = time.time()
        attempts = []
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.stats['total_attempts'] += 1
            
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed > self.config.time_budget:
                self.stats['time_budget_exceeded'] += 1
                logger.error(f"{operation_name}: Time budget exceeded ({elapsed:.1f}s > {self.config.time_budget}s)")
                raise TimeoutError(f"Time budget exceeded after {attempt-1} attempts")
            try:
            
                # Attempt operation
                logger.debug(f"{operation_name}: Attempt {attempt}/{self.config.max_attempts}")
                result = operation()
                
                # Success!
                attempt_record = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    delay=0,
                    success=True
                )
                attempts.append(attempt_record)
                self.retry_history.append(attempt_record)
                
                if attempt > 1:
                    self.stats['successful_retries'] += 1
                    logger.info(f"{operation_name}: Succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                # Classify error
                error_class = error_classifier(e) if error_classifier else self._classify_error(e)
                
                # Check if should retry
                if error_class == ErrorClass.PERMANENT:
                    logger.error(f"{operation_name}: Permanent error, not retrying: {e}")
                    self.stats['failed_after_retries'] += 1
                    raise
                
                # Last attempt?
                if attempt == self.config.max_attempts:
                    logger.error(f"{operation_name}: Failed after {attempt} attempts: {e}")
                    self.stats['failed_after_retries'] += 1
                    raise
                
                # Calculate delay
                delay = self._calculate_delay(attempt, error_class)
                remaining_budget = self.config.time_budget - (time.time() - start_time)
                delay = min(delay, remaining_budget)
                
                # Record attempt
                attempt_record = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    delay=delay,
                    error=e,
                    error_class=error_class,
                    success=False
                )
                attempts.append(attempt_record)
                self.retry_history.append(attempt_record)
                
                # Callback
                if on_retry:
                    try:
                        on_retry(attempt, e)
                    except Exception as callback_error:
                        logger.error(f"Retry callback error: {callback_error}")
                
                # Log and wait
                logger.warning(f"{operation_name}: Attempt {attempt} failed ({error_class.value}), "
                             f"retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
    
    def _classify_error(self, error: Exception) -> ErrorClass:
        """
        Classify error for retry decision
        
        Args:
            error: Exception to classify
        
        Returns:
            Error classification
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Permanent errors (don't retry)
        permanent_keywords = ['invalid', 'forbidden', 'unauthorized', 'not found', 'bad request']
        if any(kw in error_str for kw in permanent_keywords):
            return ErrorClass.PERMANENT
        
        # Rate limit errors
        rate_limit_keywords = ['rate limit', 'too many requests', '429']
        if any(kw in error_str for kw in rate_limit_keywords):
            return ErrorClass.RATE_LIMIT
        
        # Network errors
        network_keywords = ['connection', 'network', 'unreachable', 'timeout']
        if any(kw in error_str for kw in network_keywords) or 'timeout' in error_type:
            return ErrorClass.NETWORK
        
        # Timeout errors
        if 'timeout' in error_type or 'timeout' in error_str:
            return ErrorClass.TIMEOUT
        
        # Default to transient (retry)
        return ErrorClass.TRANSIENT
    
    def _calculate_delay(self, attempt: int, error_class: ErrorClass) -> float:
        """
        Calculate delay before next retry
        
        Args:
            attempt: Current attempt number
            error_class: Type of error
        
        Returns:
            Delay in seconds
        """
        # Error-specific delays
        if error_class == ErrorClass.RATE_LIMIT:
            base_delay = self.config.rate_limit_delay
        elif error_class == ErrorClass.NETWORK:
            base_delay = self.config.network_delay
        else:
            # Calculate based on strategy
            if self.config.strategy == RetryStrategy.EXPONENTIAL:
                base_delay = self.config.initial_delay * (self.config.exponential_base ** (attempt - 1))
            elif self.config.strategy == RetryStrategy.LINEAR:
                base_delay = self.config.initial_delay * attempt
            elif self.config.strategy == RetryStrategy.FIBONACCI:
                base_delay = self._fibonacci(attempt) * self.config.initial_delay
            else:  # FIXED
                base_delay = self.config.initial_delay
        
        # Cap at max delay
        base_delay = min(base_delay, self.config.max_delay)
        
        # Add jitter (randomness to prevent thundering herd)
        jitter = base_delay * self.config.jitter_factor * (2 * random.random() - 1)
        final_delay = base_delay + jitter
        
        # Ensure positive
        return max(0.0, final_delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return {
            **self.stats,
            'retry_history_count': len(self.retry_history),
            'success_rate': (
                self.stats['successful_retries'] / self.stats['total_operations'] * 100
                if self.stats['total_operations'] > 0 else 0
            )
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            'total_operations': 0,
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_after_retries': 0,
            'time_budget_exceeded': 0
        }
        self.retry_history.clear()


def retry_with_backoff(max_attempts: int = 5,
                       initial_delay: float = 0.1,
                       max_delay: float = 60.0,
                       jitter_factor: float = 0.1):
    """
    Decorator for automatic retry with exponential backoff
    
    Usage:
        @retry_with_backoff(max_attempts=3)
        def risky_operation():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                jitter_factor=jitter_factor
            )
            retry = RobustRetry(config)
            return retry.execute(
                lambda: func(*args, **kwargs),
                operation_name=func.__name__
            )
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create retry system
    retry = RobustRetry(RetryConfig(
        max_attempts=5,
        initial_delay=0.5,
        max_delay=10.0,
        jitter_factor=0.2,
        time_budget=30.0
    ))
    
    # Test 1: Operation that succeeds after retries
    attempt_count = [0]
    
    def flaky_operation():
        try:
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ConnectionError("Network error")
            return "Success!"

            result = retry.execute(flaky_operation, operation_name="test_operation")
            logger.info(f"Result: {result}")
        except Exception as e:
            logger.info(f"Failed: {e}")

    # Test 2: Using decorator
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def another_operation():
        try:
            if random.random() < 0.5:
                raise TimeoutError("Timeout")
            return "Done"

            result = another_operation()
            logger.info(f"Decorator result: {result}")
        except Exception as e:
            logger.info(f"Decorator failed: {e}")

    # Print statistics
    stats = retry.get_statistics()
    logger.info(f"\nStatistics: {stats}")
