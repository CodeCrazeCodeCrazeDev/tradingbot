"""
Circuit Breaker System for Trading Bot
=======================================

Implements the circuit breaker pattern to prevent cascading failures:
1. Monitors failure rates across components
2. Opens circuit when failures exceed threshold
3. Allows gradual recovery with half-open state
4. Prevents system overload during issues
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = auto()      # Normal operation - requests allowed
    OPEN = auto()        # Circuit tripped - requests blocked
    HALF_OPEN = auto()   # Testing recovery - limited requests allowed


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls


@dataclass
class CircuitConfig:
    """Configuration for a circuit breaker"""
    failure_threshold: int = 5           # Failures before opening
    success_threshold: int = 3           # Successes to close from half-open
    timeout_seconds: float = 60.0        # Time before attempting recovery
    half_open_max_calls: int = 3         # Max calls in half-open state
    failure_rate_threshold: float = 0.5  # Failure rate to trigger open
    window_size: int = 10                # Rolling window for rate calculation


class CircuitBreaker:
    """
    Circuit breaker for a single component/service.
    
    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Circuit tripped, all requests fail fast
    - HALF_OPEN: Testing if service recovered, limited requests
    
    Transitions:
    - CLOSED -> OPEN: When failure threshold exceeded
    - OPEN -> HALF_OPEN: After timeout period
    - HALF_OPEN -> CLOSED: When success threshold met
    - HALF_OPEN -> OPEN: When any failure occurs
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitConfig] = None,
        on_state_change: Optional[Callable] = None,
        on_open: Optional[Callable] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit (e.g., "broker_api", "data_feed")
            config: Circuit configuration
            on_state_change: Callback when state changes
            on_open: Callback when circuit opens
        """
        self.name = name
        self.config = config or CircuitConfig()
        self.on_state_change = on_state_change
        self.on_open = on_open
        
        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = datetime.utcnow()
        self._half_open_calls = 0
        
        # Rolling window for failure rate
        self._recent_results: deque = deque(maxlen=self.config.window_size)
        
        logger.info(f"CircuitBreaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get current state"""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        return self._state == CircuitState.OPEN
    
    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics"""
        return self._stats
    
    def can_execute(self) -> bool:
        """
        Check if a request can be executed.
        
        Returns:
            True if request is allowed
        """
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if timeout has passed
                elapsed = (datetime.utcnow() - self._last_state_change).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False
            
            if self._state == CircuitState.HALF_OPEN:
                # Allow limited calls in half-open
                if self._half_open_calls < self.config.half_open_max_calls:
                    return True
                return False
            
            return False
    
    def record_success(self):
        """Record a successful call"""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.last_success_time = datetime.utcnow()
            self._recent_results.append(True)
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                
                # Check if we can close the circuit
                recent_successes = sum(1 for r in list(self._recent_results)[-self.config.success_threshold:] if r)
                if recent_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    def record_failure(self, error: Optional[Exception] = None):
        """Record a failed call"""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.last_failure_time = datetime.utcnow()
            self._recent_results.append(False)
            
            if error:
                logger.warning(f"CircuitBreaker '{self.name}' recorded failure: {error}")
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens circuit
                self._transition_to(CircuitState.OPEN)
                return
            
            if self._state == CircuitState.CLOSED:
                # Check if we should open the circuit
                recent_failures = sum(1 for r in self._recent_results if not r)
                
                if recent_failures >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                elif len(self._recent_results) >= self.config.window_size:
                    failure_rate = sum(1 for r in self._recent_results if not r) / len(self._recent_results)
                    if failure_rate >= self.config.failure_rate_threshold:
                        self._transition_to(CircuitState.OPEN)
    
    def record_rejection(self):
        """Record a rejected call (circuit was open)"""
        with self._lock:
            self._stats.rejected_calls += 1
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state"""
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.utcnow()
        self._stats.state_changes += 1
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        
        logger.info(f"CircuitBreaker '{self.name}': {old_state.name} -> {new_state.name}")
        
        if self.on_state_change:
            try:
                self.on_state_change(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
        
        if new_state == CircuitState.OPEN and self.on_open:
            try:
                self.on_open(self.name)
            except Exception as e:
                logger.error(f"On open callback error: {e}")
    
    def force_open(self, reason: str = "Manual"):
        """Force the circuit open"""
        with self._lock:
            logger.warning(f"CircuitBreaker '{self.name}' forced OPEN: {reason}")
            self._transition_to(CircuitState.OPEN)
    
    def force_close(self, reason: str = "Manual"):
        """Force the circuit closed"""
        with self._lock:
            logger.info(f"CircuitBreaker '{self.name}' forced CLOSED: {reason}")
            self._transition_to(CircuitState.CLOSED)
            self._recent_results.clear()
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitStats()
            self._last_state_change = datetime.utcnow()
            self._half_open_calls = 0
            self._recent_results.clear()
            logger.info(f"CircuitBreaker '{self.name}' reset")
    
    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.name,
                "stats": {
                    "total_calls": self._stats.total_calls,
                    "successful_calls": self._stats.successful_calls,
                    "failed_calls": self._stats.failed_calls,
                    "rejected_calls": self._stats.rejected_calls,
                    "failure_rate": f"{self._stats.failure_rate:.1%}",
                    "success_rate": f"{self._stats.success_rate:.1%}",
                    "state_changes": self._stats.state_changes
                },
                "last_state_change": self._last_state_change.isoformat(),
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout_seconds": self.config.timeout_seconds
                }
            }
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
        """
        if not self.can_execute():
            self.record_rejection()
            raise CircuitOpenError(f"Circuit '{self.name}' is open")
        try:
        
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise


class CircuitOpenError(Exception):
    """Raised when trying to execute through an open circuit"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different components.
    
    Provides centralized monitoring and control of all circuits.
    """
    
    # Default circuits for trading bot
    DEFAULT_CIRCUITS = [
        "broker_api",
        "data_feed",
        "order_execution",
        "risk_check",
        "signal_generation",
        "database",
        "notification"
    ]
    
    def __init__(
        self,
        default_config: Optional[CircuitConfig] = None,
        state_file: Optional[str] = None
    ):
        """
        Initialize circuit breaker manager.
        
        Args:
            default_config: Default configuration for new circuits
            state_file: File to persist circuit states
        """
        self._lock = threading.RLock()
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._default_config = default_config or CircuitConfig()
        self._state_file = Path(state_file) if state_file else None
        
        # Callbacks
        self._on_any_open: Optional[Callable] = None
        self._on_all_closed: Optional[Callable] = None
        
        # Create default circuits
        for name in self.DEFAULT_CIRCUITS:
            self.get_or_create(name)
        
        logger.info(f"CircuitBreakerManager initialized with {len(self._circuits)} circuits")
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitConfig] = None
    ) -> CircuitBreaker:
        """
        Get existing circuit or create new one.
        
        Args:
            name: Circuit name
            config: Optional custom configuration
            
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._circuits:
                self._circuits[name] = CircuitBreaker(
                    name=name,
                    config=config or self._default_config,
                    on_state_change=self._handle_state_change,
                    on_open=self._handle_circuit_open
                )
            return self._circuits[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit by name"""
        return self._circuits.get(name)
    
    def _handle_state_change(self, name: str, old_state: CircuitState, new_state: CircuitState):
        """Handle circuit state change"""
        self._save_state()
        
        # Check if all circuits are now closed
        if new_state == CircuitState.CLOSED:
            if all(c.is_closed for c in self._circuits.values()):
                if self._on_all_closed:
                    try:
                        self._on_all_closed()
                    except Exception as e:
                        logger.error(f"All closed callback error: {e}")
    
    def _handle_circuit_open(self, name: str):
        """Handle circuit opening"""
        if self._on_any_open:
            try:
                self._on_any_open(name)
            except Exception as e:
                logger.error(f"Any open callback error: {e}")
    
    def all_closed(self) -> bool:
        """Check if all circuits are closed"""
        return all(c.is_closed for c in self._circuits.values())
    
    def any_open(self) -> bool:
        """Check if any circuit is open"""
        return any(c.is_open for c in self._circuits.values())
    
    def get_open_circuits(self) -> List[str]:
        """Get list of open circuit names"""
        return [name for name, c in self._circuits.items() if c.is_open]
    
    def force_all_open(self, reason: str = "Emergency"):
        """Force all circuits open"""
        with self._lock:
            for circuit in self._circuits.values():
                circuit.force_open(reason)
    
    def force_all_closed(self, reason: str = "Recovery"):
        """Force all circuits closed"""
        with self._lock:
            for circuit in self._circuits.values():
                circuit.force_close(reason)
    
    def reset_all(self):
        """Reset all circuits"""
        with self._lock:
            for circuit in self._circuits.values():
                circuit.reset()
    
    def get_status(self) -> Dict:
        """Get status of all circuits"""
        with self._lock:
            return {
                "all_closed": self.all_closed(),
                "any_open": self.any_open(),
                "open_circuits": self.get_open_circuits(),
                "circuits": {name: c.get_status() for name, c in self._circuits.items()}
            }
    
    def _save_state(self):
        """Save circuit states to file"""
        if not self._state_file:
            return
        try:
        
            state = {
                "timestamp": datetime.utcnow().isoformat(),
                "circuits": {
                    name: {
                        "state": c.state.name,
                        "stats": {
                            "total_calls": c.stats.total_calls,
                            "failed_calls": c.stats.failed_calls
                        }
                    }
                    for name, c in self._circuits.items()
                }
            }
            
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save circuit state: {e}")
    
    def on_any_open(self, callback: Callable):
        """Set callback for when any circuit opens"""
        self._on_any_open = callback
    
    def on_all_closed(self, callback: Callable):
        """Set callback for when all circuits close"""
        self._on_all_closed = callback


# Global instance
_global_manager: Optional[CircuitBreakerManager] = None


def get_circuit_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = CircuitBreakerManager()
    return _global_manager


def get_circuit(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name"""
    return get_circuit_manager().get_or_create(name)


def can_execute(circuit_name: str) -> bool:
    """Check if a circuit allows execution"""
    circuit = get_circuit_manager().get(circuit_name)
    return circuit.can_execute() if circuit else True
