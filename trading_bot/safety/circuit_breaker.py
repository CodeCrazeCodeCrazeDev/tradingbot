"""
Circuit Breaker - Trading circuit breaker mechanisms
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Tripped, no trading
    HALF_OPEN = "half_open"  # Testing


class CircuitBreaker:
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.failure_threshold = 5
            self.reset_timeout = timedelta(minutes=5)
            self.last_failure_time: Optional[datetime] = None
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("CircuitBreaker initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def record_failure(self):
        try:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker OPEN")
        except Exception as e:
            logger.error(f"Error in record_failure: {e}")
            raise
    
    def record_success(self):
        try:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
        except Exception as e:
            logger.error(f"Error in record_success: {e}")
            raise
    
    def can_execute(self) -> bool:
        try:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and datetime.utcnow() - self.last_failure_time > self.reset_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            return True  # HALF_OPEN allows one attempt
        except Exception as e:
            logger.error(f"Error in can_execute: {e}")
            raise


_breaker: Optional[CircuitBreaker] = None
def get_breaker() -> CircuitBreaker:
    try:
        global _breaker
        if _breaker is None:
            _breaker = CircuitBreaker()
        return _breaker
    except Exception as e:
        logger.error(f"Error in get_breaker: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_breaker().initialize(config)
async def start() -> bool:
    return await get_breaker().start()
async def stop() -> bool:
    return await get_breaker().stop()
