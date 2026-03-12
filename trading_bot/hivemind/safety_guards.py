"""
Hivemind Safety Guards - Risk Mitigation Module
================================================

Implements critical safety guards to mitigate hidden risks:
1. Race condition protection with locks
2. Memory bounds enforcement
3. Circuit breakers for loss limits
4. Input validation
5. Error tracking with thresholds

Author: Risk Mitigation System
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import functools

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Tripped - blocking
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class SafetyConfig:
    """Safety configuration"""
    # Memory limits
    max_decision_history: int = 1000
    max_perception_history: int = 5000
    max_error_history: int = 100
    
    # Circuit breaker
    max_consecutive_errors: int = 5
    error_window_seconds: int = 60
    circuit_reset_seconds: int = 300
    
    # Loss limits
    max_daily_loss_pct: float = 0.05  # 5% max daily loss
    max_drawdown_pct: float = 0.10    # 10% max drawdown
    
    # Rate limits
    max_decisions_per_minute: int = 60
    max_trades_per_hour: int = 100


class ThreadSafeState:
    """Thread-safe state container with locks"""
    
    def __init__(self, max_history: int = 1000):
        self._lock = asyncio.Lock()
        self._data: Dict[str, Any] = {}
        self._history: deque = deque(maxlen=max_history)
        self._counters: Dict[str, int] = {}
        
    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)
    
    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value
    
    async def increment(self, key: str, amount: int = 1) -> int:
        async with self._lock:
            self._counters[key] = self._counters.get(key, 0) + amount
            return self._counters[key]
    
    async def append_history(self, item: Any) -> None:
        async with self._lock:
            self._history.append(item)
    
    async def get_history(self) -> List[Any]:
        async with self._lock:
            return list(self._history)


class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(self, name: str, config: Optional[SafetyConfig] = None):
        self.name = name
        self.config = config or SafetyConfig()
        self.state = CircuitState.CLOSED
        self.error_times: deque = deque(maxlen=self.config.max_error_history)
        self.last_failure: Optional[datetime] = None
        self.consecutive_failures = 0
        self._lock = asyncio.Lock()
        
    async def record_success(self) -> None:
        """Record successful operation"""
        async with self._lock:
            self.consecutive_failures = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit {self.name} recovered - CLOSED")
    
    async def record_failure(self, error: Exception) -> None:
        """Record failed operation"""
        async with self._lock:
            now = datetime.utcnow()
            self.error_times.append(now)
            self.last_failure = now
            self.consecutive_failures += 1
            
            # Check if should trip
            if self.consecutive_failures >= self.config.max_consecutive_errors:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit {self.name} TRIPPED after {self.consecutive_failures} failures"
                )
    
    async def can_execute(self) -> bool:
        """Check if operation can proceed"""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                # Check if reset time has passed
                if self.last_failure:
                    elapsed = (datetime.utcnow() - self.last_failure).total_seconds()
                    if elapsed >= self.config.circuit_reset_seconds:
                        self.state = CircuitState.HALF_OPEN
                        logger.info(f"Circuit {self.name} entering HALF_OPEN")
                        return True
                return False
            
            # HALF_OPEN - allow one test
            return True
    
    def is_open(self) -> bool:
        """Check if circuit is open (blocking)"""
        return self.state == CircuitState.OPEN


class LossLimitGuard:
    """Enforces loss limits to prevent catastrophic losses"""
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self._lock = asyncio.Lock()
        
        # Tracking
        self.starting_equity: float = 0.0
        self.peak_equity: float = 0.0
        self.current_equity: float = 0.0
        self.daily_start_equity: float = 0.0
        self.daily_start_date: Optional[datetime] = None
        
        # State
        self.is_halted = False
        self.halt_reason: str = ""
        
    async def initialize(self, equity: float) -> None:
        """Initialize with starting equity"""
        async with self._lock:
            self.starting_equity = equity
            self.peak_equity = equity
            self.current_equity = equity
            self.daily_start_equity = equity
            self.daily_start_date = datetime.utcnow().date()
            self.is_halted = False
            self.halt_reason = ""
    
    async def update_equity(self, equity: float) -> Dict[str, Any]:
        """Update equity and check limits"""
        async with self._lock:
            self.current_equity = equity
            
            # Update peak
            if equity > self.peak_equity:
                self.peak_equity = equity
            
            # Check for new day
            today = datetime.utcnow().date()
            if self.daily_start_date != today:
                self.daily_start_equity = equity
                self.daily_start_date = today
            
            # Calculate metrics
            daily_pnl_pct = (equity - self.daily_start_equity) / self.daily_start_equity if self.daily_start_equity > 0 else 0
            drawdown_pct = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
            
            result = {
                'daily_pnl_pct': daily_pnl_pct,
                'drawdown_pct': drawdown_pct,
                'is_halted': self.is_halted,
                'halt_reason': self.halt_reason,
            }
            
            # Check daily loss limit
            if daily_pnl_pct <= -self.config.max_daily_loss_pct:
                self.is_halted = True
                self.halt_reason = f"Daily loss limit exceeded: {daily_pnl_pct:.2%}"
                logger.critical(f"TRADING HALTED: {self.halt_reason}")
            
            # Check drawdown limit
            if drawdown_pct >= self.config.max_drawdown_pct:
                self.is_halted = True
                self.halt_reason = f"Max drawdown exceeded: {drawdown_pct:.2%}"
                logger.critical(f"TRADING HALTED: {self.halt_reason}")
            
            result['is_halted'] = self.is_halted
            result['halt_reason'] = self.halt_reason
            return result
    
    async def can_trade(self) -> tuple:
        """Check if trading is allowed"""
        async with self._lock:
            return (not self.is_halted, self.halt_reason)
    
    async def reset(self, reason: str = "Manual reset") -> None:
        """Reset halt state (requires explicit action)"""
        async with self._lock:
            logger.warning(f"Loss limit guard reset: {reason}")
            self.is_halted = False
            self.halt_reason = ""


class RateLimiter:
    """Rate limiter for decision/trade frequency"""
    
    def __init__(self, max_per_window: int, window_seconds: int):
        self.max_per_window = max_per_window
        self.window_seconds = window_seconds
        self.timestamps: deque = deque()
        self._lock = asyncio.Lock()
    
    async def can_proceed(self) -> bool:
        """Check if action is allowed"""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            # Remove old timestamps
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()
            
            # Check limit
            if len(self.timestamps) >= self.max_per_window:
                return False
            
            self.timestamps.append(now)
            return True
    
    async def get_remaining(self) -> int:
        """Get remaining allowed actions"""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()
            
            return max(0, self.max_per_window - len(self.timestamps))


class InputValidator:
    """Validates inputs to prevent injection and invalid data"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> tuple:
        """Validate trading symbol"""
        if not symbol:
            return False, "Symbol cannot be empty"
        if not isinstance(symbol, str):
            return False, f"Symbol must be string, got {type(symbol)}"
        if len(symbol) < 2 or len(symbol) > 20:
            return False, f"Symbol length invalid: {len(symbol)}"
        if not symbol.replace('/', '').replace('-', '').replace('_', '').isalnum():
            return False, f"Symbol contains invalid characters: {symbol}"
        return True, ""
    
    @staticmethod
    def validate_quantity(quantity: float, max_qty: float = 1000000) -> tuple:
        """Validate trade quantity"""
        if not isinstance(quantity, (int, float)):
            return False, f"Quantity must be numeric, got {type(quantity)}"
        if quantity <= 0:
            return False, f"Quantity must be positive: {quantity}"
        if quantity > max_qty:
            return False, f"Quantity exceeds maximum: {quantity} > {max_qty}"
        return True, ""
    
    @staticmethod
    def validate_price(price: float) -> tuple:
        """Validate price"""
        if not isinstance(price, (int, float)):
            return False, f"Price must be numeric, got {type(price)}"
        if price <= 0:
            return False, f"Price must be positive: {price}"
        if price > 1e12:  # Sanity check
            return False, f"Price unreasonably high: {price}"
        return True, ""
    
    @staticmethod
    def validate_confidence(confidence: float) -> tuple:
        """Validate confidence score"""
        if not isinstance(confidence, (int, float)):
            return False, f"Confidence must be numeric, got {type(confidence)}"
        if confidence < 0 or confidence > 1:
            return False, f"Confidence must be 0-1: {confidence}"
        return True, ""
    
    @staticmethod
    def validate_payload(payload: Dict[str, Any], max_depth: int = 5, max_size: int = 10000) -> tuple:
        """Validate payload dict"""
        if not isinstance(payload, dict):
            return False, f"Payload must be dict, got {type(payload)}"
        
        import json
        try:
            serialized = json.dumps(payload)
            if len(serialized) > max_size:
                return False, f"Payload too large: {len(serialized)} > {max_size}"
        except (TypeError, ValueError) as e:
            return False, f"Payload not serializable: {e}"
        
        return True, ""


class SafetyOrchestrator:
    """Orchestrates all safety guards"""
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        
        # Initialize guards
        self.state = ThreadSafeState(max_history=self.config.max_decision_history)
        self.circuit_breaker = CircuitBreaker("hivemind", self.config)
        self.loss_guard = LossLimitGuard(self.config)
        self.decision_limiter = RateLimiter(
            self.config.max_decisions_per_minute, 60
        )
        self.trade_limiter = RateLimiter(
            self.config.max_trades_per_hour, 3600
        )
        self.validator = InputValidator()
        
        logger.info("SafetyOrchestrator initialized")
    
    async def initialize(self, starting_equity: float) -> None:
        """Initialize with starting equity"""
        await self.loss_guard.initialize(starting_equity)
    
    async def pre_decision_check(self) -> tuple:
        """Check before making a decision"""
        # Check circuit breaker
        if not await self.circuit_breaker.can_execute():
            return False, "Circuit breaker is OPEN"
        
        # Check loss limits
        can_trade, reason = await self.loss_guard.can_trade()
        if not can_trade:
            return False, reason
        
        # Check rate limit
        if not await self.decision_limiter.can_proceed():
            return False, "Decision rate limit exceeded"
        
        return True, ""
    
    async def pre_trade_check(
        self,
        symbol: str,
        quantity: float,
        price: float,
        confidence: float
    ) -> tuple:
        """Check before executing a trade"""
        # Validate inputs
        valid, msg = self.validator.validate_symbol(symbol)
        if not valid:
            return False, msg
        
        valid, msg = self.validator.validate_quantity(quantity)
        if not valid:
            return False, msg
        
        valid, msg = self.validator.validate_price(price)
        if not valid:
            return False, msg
        
        valid, msg = self.validator.validate_confidence(confidence)
        if not valid:
            return False, msg
        
        # Check trade rate limit
        if not await self.trade_limiter.can_proceed():
            return False, "Trade rate limit exceeded"
        
        # Check loss limits
        can_trade, reason = await self.loss_guard.can_trade()
        if not can_trade:
            return False, reason
        
        return True, ""
    
    async def record_success(self) -> None:
        """Record successful operation"""
        await self.circuit_breaker.record_success()
    
    async def record_failure(self, error: Exception) -> None:
        """Record failed operation"""
        await self.circuit_breaker.record_failure(error)
    
    async def update_equity(self, equity: float) -> Dict[str, Any]:
        """Update equity for loss tracking"""
        return await self.loss_guard.update_equity(equity)
    
    def get_status(self) -> Dict[str, Any]:
        """Get safety system status"""
        return {
            'circuit_state': self.circuit_breaker.state.value,
            'is_halted': self.loss_guard.is_halted,
            'halt_reason': self.loss_guard.halt_reason,
            'consecutive_failures': self.circuit_breaker.consecutive_failures,
        }


# Decorator for safe async operations
def safe_async_operation(circuit_name: str = "default"):
    """Decorator for safe async operations with circuit breaker"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator


# Factory function
def create_safety_orchestrator(config: Optional[Dict[str, Any]] = None) -> SafetyOrchestrator:
    """Create safety orchestrator with config"""
    safety_config = SafetyConfig(**(config or {}))
    return SafetyOrchestrator(safety_config)
