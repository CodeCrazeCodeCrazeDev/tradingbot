"""
EXCEPTION HANDLER MODULE - P0 CRITICAL FIX
============================================================

Implements comprehensive exception handling for the trading bot.

Features:
- Graceful error handling
- Automatic retry logic
- Error logging and reporting
- Recovery procedures
- Circuit breaker pattern

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import asyncio
import logging
import traceback
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

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



# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorRecoveryStrategy(Enum):
    """Error recovery strategies."""
    RETRY = auto()
    SKIP = auto()
    FALLBACK = auto()
    SHUTDOWN = auto()


@dataclass
class ErrorRecord:
    """Record of an error."""
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    traceback_str: str
    recovery_strategy: ErrorRecoveryStrategy
    recovered: bool


class CircuitBreaker:
    """Circuit breaker pattern for error handling."""
    
    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed >= self.recovery_timeout:
                self.is_open = False
                self.failure_count = 0
                logger.info("Circuit breaker attempting recovery")
                return True
        
        return False
    
    def get_status(self) -> str:
        """Get circuit breaker status."""
        status = "OPEN" if self.is_open else "CLOSED"
        return f"CircuitBreaker: {status} (failures: {self.failure_count})"


class ExceptionHandler:
    """Handles exceptions in trading bot."""
    
    def __init__(self, max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize exception handler.
        
        Args:
            max_retries: Maximum number of retries
            retry_delay: Delay between retries (seconds)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.error_history: List[ErrorRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]
    
    def record_error(self, error_type: str, message: str,
                    severity: ErrorSeverity,
                    traceback_str: str,
                    recovery_strategy: ErrorRecoveryStrategy,
                    recovered: bool = False):
        """Record error in history."""
        record = ErrorRecord(
            timestamp=datetime.now(),
            error_type=error_type,
            message=message,
            severity=severity,
            traceback_str=traceback_str,
            recovery_strategy=recovery_strategy,
            recovered=recovered
        )
        
        self.error_history.append(record)
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history.pop(0)
    
    def handle_exception(self, exc: Exception,
                        context: str = "Unknown",
                        recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.RETRY) -> bool:
        """
        Handle exception.
        
        Args:
            exc: Exception to handle
            context: Context where exception occurred
            recovery_strategy: How to recover
            
        Returns:
            True if handled, False if critical
        """
        error_type = type(exc).__name__
        message = str(exc)
        tb_str = traceback.format_exc()
        
        # Determine severity
        if isinstance(exc, (ConnectionError, TimeoutError)):
            severity = ErrorSeverity.WARNING
        elif isinstance(exc, ValueError):
            severity = ErrorSeverity.ERROR
        else:
            severity = ErrorSeverity.CRITICAL
        
        logger.error(f"Exception in {context}: {error_type}: {message}\n{tb_str}")
        
        # Record error
        self.record_error(error_type, message, severity, tb_str, recovery_strategy)
        
        # Handle based on strategy
        if recovery_strategy == ErrorRecoveryStrategy.RETRY:
            return True  # Will retry
        elif recovery_strategy == ErrorRecoveryStrategy.SKIP:
            logger.warning(f"Skipping operation due to {error_type}")
            return True  # Continue
        elif recovery_strategy == ErrorRecoveryStrategy.FALLBACK:
            logger.warning(f"Using fallback for {error_type}")
            return True  # Continue with fallback
        else:  # SHUTDOWN
            logger.critical(f"Critical error, shutting down: {error_type}")
            return False  # Stop
    
    def get_error_summary(self, lookback_hours: int = 24) -> str:
        """Get error summary for last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return "No errors in last {} hours".format(lookback_hours)
        
        summary = f"ERROR SUMMARY (Last {lookback_hours} hours)\n"
        summary += "=" * 50 + "\n"
        
        # Group by error type
        error_counts = {}
        for error in recent_errors:
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
        
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            summary += f"{error_type}: {count}\n"
        
        summary += "=" * 50 + "\n"
        summary += f"Total: {len(recent_errors)} errors\n"
        
        return summary


# ============================================================================
# DECORATORS
# ============================================================================

def safe_async(func: Callable) -> Callable:
    """Decorator for safe async functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        handler = ExceptionHandler()
        
        for attempt in range(handler.max_retries):
            try:
                return await func(*args, **kwargs)
            
            except asyncio.TimeoutError as e:
                logger.warning(f"Timeout in {func.__name__}, attempt {attempt + 1}/{handler.max_retries}")
                if attempt < handler.max_retries - 1:
                    await asyncio.sleep(handler.retry_delay * (2 ** attempt))
                else:
                    handler.handle_exception(e, func.__name__, ErrorRecoveryStrategy.SKIP)
                    return None
            
            except ConnectionError as e:
                logger.warning(f"Connection error in {func.__name__}, attempt {attempt + 1}/{handler.max_retries}")
                if attempt < handler.max_retries - 1:
                    await asyncio.sleep(handler.retry_delay * (2 ** attempt))
                else:
                    handler.handle_exception(e, func.__name__, ErrorRecoveryStrategy.FALLBACK)
                    return None
            
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                handler.handle_exception(e, func.__name__, ErrorRecoveryStrategy.SHUTDOWN)
                raise
        
        return None
    
    return wrapper


def safe_sync(func: Callable) -> Callable:
    """Decorator for safe sync functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        handler = ExceptionHandler()
        
        for attempt in range(handler.max_retries):
            try:
                return func(*args, **kwargs)
            
            except TimeoutError as e:
                logger.warning(f"Timeout in {func.__name__}, attempt {attempt + 1}/{handler.max_retries}")
                if attempt < handler.max_retries - 1:
                    time.sleep(handler.retry_delay * (2 ** attempt))
                else:
                    handler.handle_exception(e, func.__name__, ErrorRecoveryStrategy.SKIP)
                    return None
            
            except ConnectionError as e:
                logger.warning(f"Connection error in {func.__name__}, attempt {attempt + 1}/{handler.max_retries}")
                if attempt < handler.max_retries - 1:
                    time.sleep(handler.retry_delay * (2 ** attempt))
                else:
                    handler.handle_exception(e, func.__name__, ErrorRecoveryStrategy.FALLBACK)
                    return None
            
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                handler.handle_exception(e, func.__name__, ErrorRecoveryStrategy.SHUTDOWN)
                raise
        
        return None
    
    return wrapper
