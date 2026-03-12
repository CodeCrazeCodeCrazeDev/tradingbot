import logging
logger = logging.getLogger(__name__)
"""
Circuit Breaker Implementation for Elite Trading Bot
Provides automatic error detection and recovery mechanisms
"""
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from loguru import logger
try:
    import redis
except ImportError:
    redis = None
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



class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"         # Stopped due to errors
    HALF_OPEN = "HALF_OPEN"  # Testing if system can resume

class CircuitBreaker:
    """Circuit breaker pattern implementation for trading operations."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 reset_timeout: int = 60,
                 half_open_timeout: int = 30,
                 redis_host: str = 'localhost',
                 redis_port: int = 6379):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
    async def execute(self, 
                     operation: Callable,
                     fallback: Optional[Callable] = None,
                     **kwargs) -> Any:
        """Execute an operation with circuit breaker protection."""
        
        if self.state == CircuitState.OPEN:
            try:
                if await self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF-OPEN state")
                else:
                    return await self._handle_open_circuit(fallback, **kwargs)

                result = await operation(**kwargs)
                await self._handle_success()
                return result

            except Exception as e:
                return await self._handle_failure(e, fallback, **kwargs)

    async def _handle_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker reset to CLOSED state")
            
        # Update metrics in Redis
        self.redis.hset(
            "circuit_breaker:metrics",
            mapping={
                "state": self.state.value,
                "last_success": self.last_success_time.isoformat(),
                "failure_count": self.failure_count
            }
        )
    
    async def _handle_failure(self, 
                            error: Exception,
                            fallback: Optional[Callable],
                            **kwargs) -> Any:
        """Handle operation failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        # Log error details
        logger.error(f"Operation failed: {str(error)}")
        
        # Update metrics in Redis
        self.redis.hset(
            "circuit_breaker:metrics",
            mapping={
                "state": self.state.value,
                "last_failure": self.last_failure_time.isoformat(),
                "failure_count": self.failure_count,
                "last_error": str(error)
            }
        )
        
        # Check if we should open the circuit
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
        
        # Execute fallback if provided
        if fallback:
            try:
                return await fallback(**kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback operation failed: {str(fallback_error)}")
                raise
        
        raise error
    
    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if not self.last_failure_time:
            return True
            
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.reset_timeout
    
    async def _handle_open_circuit(self,
                                 fallback: Optional[Callable],
                                 **kwargs) -> Any:
        """Handle operations when circuit is open."""
        logger.warning("Circuit breaker is OPEN, operation rejected")
        
        if fallback:
            try:
                return await fallback(**kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback operation failed: {str(fallback_error)}")
                raise
        
        raise Exception("Circuit breaker is open")
