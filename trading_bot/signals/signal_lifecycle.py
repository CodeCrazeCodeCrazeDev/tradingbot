"""
Signal Lifecycle Management System
Implements HI-ANA-001: Signal TTL and Confidence Decay Over Time

Ensures signals expire and confidence degrades over time to prevent
trading on stale information. Critical for production safety.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import math
import threading
from collections import deque

logger = logging.getLogger(__name__)


class SignalState(Enum):
    """Signal lifecycle states"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    EXPIRED = "expired"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class DecayFunction(Enum):
    """Types of confidence decay functions"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    STEP = "step"
    SIGMOID = "sigmoid"


@dataclass
class TradingSignal:
    """Trading signal with lifecycle management"""
    signal_id: str
    symbol: str
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    initial_confidence: float
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 300  # 5 minutes default
    decay_function: DecayFunction = DecayFunction.EXPONENTIAL
    decay_rate: float = 0.5  # Half-life for exponential
    min_confidence: float = 0.3  # Minimum viable confidence
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Lifecycle tracking
    state: SignalState = SignalState.ACTIVE
    current_confidence: float = field(init=False)
    last_updated: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    expiry_time: datetime = field(init=False)
    
    def __post_init__(self):
        try:
            self.current_confidence = self.initial_confidence
            self.expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise
    
    def get_age_seconds(self) -> float:
        """Get signal age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_remaining_ttl(self) -> float:
        """Get remaining TTL in seconds"""
        try:
            remaining = (self.expiry_time - datetime.now()).total_seconds()
            return max(0, remaining)
        except Exception as e:
            logger.error(f"Error in get_remaining_ttl: {e}")
            raise
    
    def is_expired(self) -> bool:
        """Check if signal has expired"""
        return datetime.now() >= self.expiry_time or self.state == SignalState.EXPIRED
    
    def calculate_confidence(self) -> float:
        """
        Calculate current confidence based on age and decay function
        
        Returns:
            Current confidence value (0.0 to 1.0)
        """
        try:
            if self.state in [SignalState.EXECUTED, SignalState.CANCELLED]:
                return 0.0
        
            if self.is_expired():
                self.state = SignalState.EXPIRED
                return 0.0
        
            age = self.get_age_seconds()
            ttl = self.ttl_seconds
        
            # Calculate decay based on function type
            if self.decay_function == DecayFunction.LINEAR:
                # Linear decay: confidence = initial * (1 - age/ttl)
                decay_factor = 1.0 - (age / ttl)
            
            elif self.decay_function == DecayFunction.EXPONENTIAL:
                # Exponential decay: confidence = initial * exp(-decay_rate * age)
                decay_factor = math.exp(-self.decay_rate * age / ttl)
            
            elif self.decay_function == DecayFunction.STEP:
                # Step decay: full confidence until 80% of TTL, then drop
                if age < ttl * 0.8:
                    decay_factor = 1.0
                else:
                    decay_factor = 0.5
                
            elif self.decay_function == DecayFunction.SIGMOID:
                # Sigmoid decay: smooth S-curve
                # confidence = initial / (1 + exp(k * (age - ttl/2)))
                k = 10 / ttl  # Steepness factor
                midpoint = ttl / 2
                decay_factor = 1.0 / (1.0 + math.exp(k * (age - midpoint)))
        
            else:
                decay_factor = 1.0
        
            # Apply decay
            self.current_confidence = self.initial_confidence * decay_factor
            self.last_updated = datetime.now()
        
            # Update state based on confidence
            if self.current_confidence < self.min_confidence:
                self.state = SignalState.DEGRADED
        
            return self.current_confidence
        except Exception as e:
            logger.error(f"Error in calculate_confidence: {e}")
            raise
    
    def extend_ttl(self, additional_seconds: int):
        """Extend signal TTL (e.g., if new confirming data arrives)"""
        try:
            self.expiry_time += timedelta(seconds=additional_seconds)
            logger.info(f"Signal {self.signal_id} TTL extended by {additional_seconds}s")
        except Exception as e:
            logger.error(f"Error in extend_ttl: {e}")
            raise
    
    def mark_executed(self):
        """Mark signal as executed"""
        try:
            self.state = SignalState.EXECUTED
            self.executed_at = datetime.now()
            self.current_confidence = 0.0
            logger.info(f"Signal {self.signal_id} marked as executed")
        except Exception as e:
            logger.error(f"Error in mark_executed: {e}")
            raise
    
    def cancel(self):
        """Cancel signal"""
        try:
            self.state = SignalState.CANCELLED
            self.current_confidence = 0.0
            logger.info(f"Signal {self.signal_id} cancelled")
        except Exception as e:
            logger.error(f"Error in cancel: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'initial_confidence': self.initial_confidence,
            'current_confidence': self.current_confidence,
            'created_at': self.created_at.isoformat(),
            'age_seconds': self.get_age_seconds(),
            'remaining_ttl': self.get_remaining_ttl(),
            'state': self.state.value,
            'decay_function': self.decay_function.value,
            'metadata': self.metadata
        }


class SignalLifecycleManager:
    """
    Manages lifecycle of trading signals with automatic expiration
    
    Features:
    - Automatic confidence decay
    - TTL-based expiration
    - Signal state tracking
    - Batch signal management
    - Performance monitoring
    """
    
    def __init__(self,
                 default_ttl_seconds: int = 300,
                 cleanup_interval_seconds: int = 60,
                 auto_cleanup: bool = True):
        """
        Initialize signal lifecycle manager
        
        Args:
            default_ttl_seconds: Default TTL for signals
            cleanup_interval_seconds: How often to clean up expired signals
            auto_cleanup: Enable automatic cleanup thread
        """
        try:
            self.default_ttl = default_ttl_seconds
            self.cleanup_interval = cleanup_interval_seconds
            self.auto_cleanup = auto_cleanup
        
            # Signal storage
            self.active_signals: Dict[str, TradingSignal] = {}
            self.signal_history: deque = deque(maxlen=1000)
        
            # Statistics
            self.stats = {
                'signals_created': 0,
                'signals_expired': 0,
                'signals_executed': 0,
                'signals_cancelled': 0,
                'avg_signal_age_at_execution': 0.0
            }
        
            # Thread safety
            self.lock = threading.RLock()
        
            # Start cleanup thread
            self.cleanup_thread = None
            if self.auto_cleanup:
                self._start_cleanup_thread()
        
            logger.info(f"Signal Lifecycle Manager initialized (default TTL: {default_ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_signal(self,
                     signal_id: str,
                     symbol: str,
                     direction: str,
                     entry_price: float,
                     stop_loss: float,
                     take_profit: float,
                     confidence: float,
                     ttl_seconds: Optional[int] = None,
                     decay_function: DecayFunction = DecayFunction.EXPONENTIAL,
                     metadata: Optional[Dict] = None) -> TradingSignal:
        """
        Create new trading signal with lifecycle management
        
        Args:
            signal_id: Unique signal identifier
            symbol: Trading symbol
            direction: BUY or SELL
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            confidence: Initial confidence (0.0 to 1.0)
            ttl_seconds: Time to live (uses default if None)
            decay_function: Type of confidence decay
            metadata: Additional metadata
        
        Returns:
            TradingSignal instance
        """
        try:
            with self.lock:
                if signal_id in self.active_signals:
                    logger.warning(f"Signal {signal_id} already exists, returning existing")
                    return self.active_signals[signal_id]
            
                signal = TradingSignal(
                    signal_id=signal_id,
                    symbol=symbol,
                    direction=direction,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    initial_confidence=confidence,
                    ttl_seconds=ttl_seconds or self.default_ttl,
                    decay_function=decay_function,
                    metadata=metadata or {}
                )
            
                self.active_signals[signal_id] = signal
                self.stats['signals_created'] += 1
            
                logger.info(f"Created signal {signal_id}: {symbol} {direction} @ {entry_price} "
                           f"(confidence: {confidence:.2f}, TTL: {signal.ttl_seconds}s)")
            
                return signal
        except Exception as e:
            logger.error(f"Error in create_signal: {e}")
            raise
    
    def get_signal(self, signal_id: str) -> Optional[TradingSignal]:
        """Get signal by ID"""
        try:
            with self.lock:
                signal = self.active_signals.get(signal_id)
                if signal:
                    # Update confidence before returning
                    signal.calculate_confidence()
                return signal
        except Exception as e:
            logger.error(f"Error in get_signal: {e}")
            raise
    
    def get_active_signals(self, 
                          symbol: Optional[str] = None,
                          min_confidence: Optional[float] = None) -> List[TradingSignal]:
        """
        Get all active signals, optionally filtered
        
        Args:
            symbol: Filter by symbol
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of active signals
        """
        try:
            with self.lock:
                signals = []
            
                for signal in self.active_signals.values():
                    # Update confidence
                    current_conf = signal.calculate_confidence()
                
                    # Apply filters
                    if symbol and signal.symbol != symbol:
                        continue
                
                    if min_confidence and current_conf < min_confidence:
                        continue
                
                    if signal.state == SignalState.ACTIVE:
                        signals.append(signal)
            
                return signals
        except Exception as e:
            logger.error(f"Error in get_active_signals: {e}")
            raise
    
    def execute_signal(self, signal_id: str) -> bool:
        """
        Mark signal as executed
        
        Args:
            signal_id: Signal to execute
        
        Returns:
            True if successful
        """
        try:
            with self.lock:
                signal = self.active_signals.get(signal_id)
                if not signal:
                    logger.warning(f"Signal {signal_id} not found")
                    return False
            
                # Track execution age
                age = signal.get_age_seconds()
                self._update_avg_execution_age(age)
            
                # Mark executed
                signal.mark_executed()
                self.stats['signals_executed'] += 1
            
                # Move to history
                self.signal_history.append(signal)
                del self.active_signals[signal_id]
            
                return True
        except Exception as e:
            logger.error(f"Error in execute_signal: {e}")
            raise
    
    def cancel_signal(self, signal_id: str) -> bool:
        """Cancel signal"""
        try:
            with self.lock:
                signal = self.active_signals.get(signal_id)
                if not signal:
                    return False
            
                signal.cancel()
                self.stats['signals_cancelled'] += 1
            
                # Move to history
                self.signal_history.append(signal)
                del self.active_signals[signal_id]
            
                return True
        except Exception as e:
            logger.error(f"Error in cancel_signal: {e}")
            raise
    
    def extend_signal_ttl(self, signal_id: str, additional_seconds: int) -> bool:
        """Extend signal TTL"""
        try:
            with self.lock:
                signal = self.active_signals.get(signal_id)
                if not signal:
                    return False
            
                signal.extend_ttl(additional_seconds)
                return True
        except Exception as e:
            logger.error(f"Error in extend_signal_ttl: {e}")
            raise
    
    def cleanup_expired_signals(self) -> int:
        """
        Remove expired signals
        
        Returns:
            Number of signals removed
        """
        try:
            with self.lock:
                expired_ids = []
            
                for signal_id, signal in self.active_signals.items():
                    if signal.is_expired():
                        expired_ids.append(signal_id)
                        signal.state = SignalState.EXPIRED
                        self.signal_history.append(signal)
            
                # Remove expired
                for signal_id in expired_ids:
                    del self.active_signals[signal_id]
            
                if expired_ids:
                    self.stats['signals_expired'] += len(expired_ids)
                    logger.info(f"Cleaned up {len(expired_ids)} expired signals")
            
                return len(expired_ids)
        except Exception as e:
            logger.error(f"Error in cleanup_expired_signals: {e}")
            raise
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            try:
                while self.auto_cleanup:
                    time.sleep(self.cleanup_interval)
                    self.cleanup_expired_signals()
            except Exception as e:
                logger.error(f"Error in cleanup_loop: {e}")
                raise
        
        self.cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("Signal cleanup thread started")
    
    def stop_cleanup_thread(self):
        """Stop cleanup thread"""
        try:
            self.auto_cleanup = False
            if self.cleanup_thread:
                self.cleanup_thread.join(timeout=5)
            logger.info("Signal cleanup thread stopped")
        except Exception as e:
            logger.error(f"Error in stop_cleanup_thread: {e}")
            raise
    
    def _update_avg_execution_age(self, age: float):
        """Update average signal age at execution"""
        try:
            current_avg = self.stats['avg_signal_age_at_execution']
            count = self.stats['signals_executed']
        
            if count == 1:
                self.stats['avg_signal_age_at_execution'] = age
            else:
                # Running average
                self.stats['avg_signal_age_at_execution'] = (
                    (current_avg * (count - 1) + age) / count
                )
        except Exception as e:
            logger.error(f"Error in _update_avg_execution_age: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get lifecycle statistics"""
        try:
            with self.lock:
                return {
                    **self.stats,
                    'active_signals': len(self.active_signals),
                    'signals_in_history': len(self.signal_history)
                }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
    
    def get_signal_summary(self) -> Dict[str, Any]:
        """Get summary of all active signals"""
        try:
            with self.lock:
                summary = {
                    'total_active': len(self.active_signals),
                    'by_state': {},
                    'by_symbol': {},
                    'avg_confidence': 0.0,
                    'avg_age': 0.0
                }
            
                if not self.active_signals:
                    return summary
            
                total_conf = 0.0
                total_age = 0.0
            
                for signal in self.active_signals.values():
                    # Update confidence
                    conf = signal.calculate_confidence()
                    age = signal.get_age_seconds()
                
                    total_conf += conf
                    total_age += age
                
                    # Count by state
                    state = signal.state.value
                    summary['by_state'][state] = summary['by_state'].get(state, 0) + 1
                
                    # Count by symbol
                    symbol = signal.symbol
                    summary['by_symbol'][symbol] = summary['by_symbol'].get(symbol, 0) + 1
            
                summary['avg_confidence'] = total_conf / len(self.active_signals)
                summary['avg_age'] = total_age / len(self.active_signals)
            
                return summary
        except Exception as e:
            logger.error(f"Error in get_signal_summary: {e}")
            raise


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create manager
    manager = SignalLifecycleManager(default_ttl_seconds=10, cleanup_interval_seconds=5)
    
    # Create test signal
    signal = manager.create_signal(
        signal_id="TEST-001",
        symbol="EURUSD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        confidence=0.85,
        ttl_seconds=10,
        decay_function=DecayFunction.EXPONENTIAL
    )
    
    # Monitor confidence decay
    for i in range(12):
        time.sleep(1)
        conf = signal.calculate_confidence()
        age = signal.get_age_seconds()
        remaining = signal.get_remaining_ttl()
        logger.info(f"Age: {age:.1f}s, Confidence: {conf:.3f}, Remaining TTL: {remaining:.1f}s, State: {signal.state.value}")
    
    # Get statistics
    stats = manager.get_statistics()
    logger.info(f"\nStatistics: {stats}")
    
    # Stop cleanup thread
    manager.stop_cleanup_thread()
