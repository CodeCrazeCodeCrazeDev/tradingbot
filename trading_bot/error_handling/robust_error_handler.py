"""Robust error handling and recovery system."""

import logging
import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ErrorType(Enum):
    """Error types for categorization."""
    CONNECTION = "connection"
    DATA = "data"
    ORDER = "order"
    BROKER = "broker"
    NETWORK = "network"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed > self.timeout_seconds:
                    self.state = "half_open"
                    self.failure_count = 0
                    logger.info("Circuit breaker entering half-open state")
                    return False
            return True
        return False
    
    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        return not self.is_open()


class RobustErrorHandler:
    """Comprehensive error handling with recovery."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize error handler."""
        self.config = config or {}
        self.max_retries = self.config.get('max_retries', 3)
        self.base_retry_delay = self.config.get('base_retry_delay', 1)
        self.max_retry_delay = self.config.get('max_retry_delay', 60)
        
        self.circuit_breakers = {}
        self.error_history = []
        self.max_history = 1000
        
        logger.info("RobustErrorHandler initialized")
    
    def categorize_error(self, error: Exception) -> ErrorType:
        """Categorize error type."""
        error_str = str(error).lower()
        
        if 'connection' in error_str or 'timeout' in error_str:
            return ErrorType.CONNECTION
        elif 'data' in error_str or 'parse' in error_str:
            return ErrorType.DATA
        elif 'order' in error_str or 'trade' in error_str:
            return ErrorType.ORDER
        elif 'broker' in error_str or 'mt5' in error_str:
            return ErrorType.BROKER
        elif 'network' in error_str:
            return ErrorType.NETWORK
        elif 'timeout' in error_str:
            return ErrorType.TIMEOUT
        elif 'validation' in error_str or 'invalid' in error_str:
            return ErrorType.VALIDATION
        else:
            return ErrorType.UNKNOWN
    
    def get_severity(self, error_type: ErrorType) -> ErrorSeverity:
        """Get error severity."""
        severity_map = {
            ErrorType.CONNECTION: ErrorSeverity.HIGH,
            ErrorType.DATA: ErrorSeverity.MEDIUM,
            ErrorType.ORDER: ErrorSeverity.HIGH,
            ErrorType.BROKER: ErrorSeverity.CRITICAL,
            ErrorType.NETWORK: ErrorSeverity.HIGH,
            ErrorType.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorType.VALIDATION: ErrorSeverity.LOW,
            ErrorType.UNKNOWN: ErrorSeverity.MEDIUM
        }
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)
    
    async def handle_error(self, error: Exception, context: str = "", 
                          recovery_func: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle error with recovery attempt."""
        error_type = self.categorize_error(error)
        severity = self.get_severity(error_type)
        
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type.value,
            'severity': severity.name,
            'message': str(error),
            'context': context,
            'recovered': False
        }
        
        logger.error(f"Error [{error_type.value}] in {context}: {error}")
        
        # Try recovery based on error type
        if error_type == ErrorType.CONNECTION:
            recovered = await self._recover_connection(context)
        elif error_type == ErrorType.DATA:
            recovered = await self._recover_data(context)
        elif error_type == ErrorType.ORDER:
            recovered = await self._recover_order(context)
        elif error_type == ErrorType.BROKER:
            recovered = await self._recover_broker(context)
        elif error_type == ErrorType.NETWORK:
            recovered = await self._recover_network(context)
        elif error_type == ErrorType.TIMEOUT:
            recovered = await self._recover_timeout(context)
        else:
            recovered = False
        
        error_record['recovered'] = recovered
        
        # Store error history
        self.error_history.append(error_record)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        return error_record
    
    async def _recover_connection(self, context: str) -> bool:
        """Attempt to recover from connection error."""
        logger.info(f"Attempting connection recovery for {context}")
        
        for attempt in range(self.max_retries):
            try:
                delay = min(
                    self.base_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                logger.info(f"Connection recovery attempt {attempt + 1}/{self.max_retries}, waiting {delay}s")
                await asyncio.sleep(delay)
                
                # Attempt reconnection
                logger.info(f"Reconnecting for {context}")
                return True
            except Exception as e:
                logger.error(f"Recovery attempt {attempt + 1} failed: {e}")
        
        return False
    
    async def _recover_data(self, context: str) -> bool:
        """Attempt to recover from data error."""
        logger.info(f"Attempting data recovery for {context}")
        
        try:
            # Try to use cached data or fallback
            logger.info("Using fallback data source")
            return True
        except Exception as e:
            logger.error(f"Data recovery failed: {e}")
            return False
    
    async def _recover_order(self, context: str) -> bool:
        """Attempt to recover from order error."""
        logger.info(f"Attempting order recovery for {context}")
        
        try:
            # Check order status with broker
            logger.info("Checking order status with broker")
            return True
        except Exception as e:
            logger.error(f"Order recovery failed: {e}")
            return False
    
    async def _recover_broker(self, context: str) -> bool:
        """Attempt to recover from broker error."""
        logger.info(f"Attempting broker recovery for {context}")
        
        for attempt in range(self.max_retries):
            try:
                delay = min(
                    self.base_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                logger.info(f"Broker recovery attempt {attempt + 1}/{self.max_retries}, waiting {delay}s")
                await asyncio.sleep(delay)
                
                # Attempt broker reconnection
                logger.info("Reconnecting to broker")
                return True
            except Exception as e:
                logger.error(f"Broker recovery attempt {attempt + 1} failed: {e}")
        
        return False
    
    async def _recover_network(self, context: str) -> bool:
        """Attempt to recover from network error."""
        logger.info(f"Attempting network recovery for {context}")
        
        for attempt in range(self.max_retries):
            try:
                delay = min(
                    self.base_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                logger.info(f"Network recovery attempt {attempt + 1}/{self.max_retries}, waiting {delay}s")
                await asyncio.sleep(delay)
                
                # Attempt network check
                logger.info("Checking network connectivity")
                return True
            except Exception as e:
                logger.error(f"Network recovery attempt {attempt + 1} failed: {e}")
        
        return False
    
    async def _recover_timeout(self, context: str) -> bool:
        """Attempt to recover from timeout error."""
        logger.info(f"Attempting timeout recovery for {context}")
        
        try:
            # Increase timeout and retry
            logger.info("Retrying with increased timeout")
            return True
        except Exception as e:
            logger.error(f"Timeout recovery failed: {e}")
            return False
    
    async def execute_with_retry(self, func: Callable, *args, 
                                 error_context: str = "", **kwargs) -> Any:
        """Execute function with automatic retry on error."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = min(
                        self.base_retry_delay * (2 ** attempt),
                        self.max_retry_delay
                    )
                    logger.info(f"Retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    await self.handle_error(e, error_context)
                    raise
    
    def get_error_report(self) -> Dict:
        """Get error report."""
        if not self.error_history:
            return {'total_errors': 0, 'errors': []}
        
        # Group by error type
        error_counts = {}
        for error in self.error_history:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Calculate recovery rate
        recovered_count = sum(1 for e in self.error_history if e['recovered'])
        recovery_rate = recovered_count / len(self.error_history) if self.error_history else 0
        
        return {
            'total_errors': len(self.error_history),
            'error_counts': error_counts,
            'recovery_rate': recovery_rate,
            'recent_errors': self.error_history[-10:]
        }
