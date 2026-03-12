"""
Signal TTL and Confidence Decay Manager

Implements time-to-live (TTL) for trading signals with confidence decay over time.
Signals become less reliable as they age, and this module manages that decay.

Features:
- Signal TTL enforcement
- Confidence decay over time (exponential, linear, step)
- Signal freshness tracking
- Stale signal filtering
- Signal lifecycle management

Based on: HI-ANA-001 Signal TTL and confidence decay over time
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class DecayType(Enum):
    """Types of confidence decay."""
    EXPONENTIAL = "exponential"  # Fast initial decay, slows over time
    LINEAR = "linear"  # Constant decay rate
    STEP = "step"  # Discrete steps at intervals
    SIGMOID = "sigmoid"  # S-curve decay
    NONE = "none"  # No decay


class SignalStatus(Enum):
    """Signal lifecycle status."""
    FRESH = "fresh"  # Just created
    VALID = "valid"  # Within TTL, confidence acceptable
    DECAYING = "decaying"  # Confidence below threshold but not expired
    STALE = "stale"  # Past TTL, should not be used
    EXPIRED = "expired"  # Removed from system


@dataclass
class SignalMetadata:
    """Metadata for a trading signal."""
    signal_id: str
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    original_confidence: float
    current_confidence: float
    created_at: datetime
    ttl_seconds: int
    decay_type: DecayType
    status: SignalStatus = SignalStatus.FRESH
    last_updated: datetime = field(default_factory=datetime.now)
    decay_rate: float = 0.1  # Decay parameter
    min_confidence: float = 0.3  # Minimum confidence before stale
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        """Get signal age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def remaining_ttl_seconds(self) -> float:
        """Get remaining TTL in seconds."""
        return max(0, self.ttl_seconds - self.age_seconds)
    
    @property
    def is_expired(self) -> bool:
        """Check if signal is expired."""
        return self.age_seconds >= self.ttl_seconds
    
    @property
    def freshness_ratio(self) -> float:
        """Get freshness as ratio (1.0 = fresh, 0.0 = expired)."""
        try:
            if self.ttl_seconds <= 0:
                return 0.0
            return max(0, 1 - self.age_seconds / self.ttl_seconds)
        except Exception as e:
            logger.error(f"Error in freshness_ratio: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'original_confidence': self.original_confidence,
            'current_confidence': self.current_confidence,
            'created_at': self.created_at.isoformat(),
            'age_seconds': self.age_seconds,
            'ttl_seconds': self.ttl_seconds,
            'remaining_ttl': self.remaining_ttl_seconds,
            'status': self.status.value,
            'freshness_ratio': self.freshness_ratio,
            'decay_type': self.decay_type.value
        }


class ConfidenceDecayCalculator:
    """
    Calculates confidence decay based on different decay models.
    """
    
    @staticmethod
    def calculate(
        original_confidence: float,
        age_seconds: float,
        ttl_seconds: float,
        decay_type: DecayType,
        decay_rate: float = 0.1
    ) -> float:
        """
        Calculate decayed confidence.
        
        Args:
            original_confidence: Initial confidence (0-1)
            age_seconds: Time since signal creation
            ttl_seconds: Total TTL
            decay_type: Type of decay function
            decay_rate: Decay rate parameter
            
        Returns:
            Decayed confidence value
        """
        try:
            if decay_type == DecayType.NONE:
                return original_confidence
        
            if ttl_seconds <= 0:
                return 0.0
        
            # Normalized time (0 to 1)
            t = min(1.0, age_seconds / ttl_seconds)
        
            if decay_type == DecayType.EXPONENTIAL:
                # Exponential decay: C(t) = C0 * e^(-λt)
                decay_factor = math.exp(-decay_rate * t * 10)
                return original_confidence * decay_factor
        
            elif decay_type == DecayType.LINEAR:
                # Linear decay: C(t) = C0 * (1 - t)
                return original_confidence * (1 - t)
        
            elif decay_type == DecayType.STEP:
                # Step decay: drops at intervals
                steps = 4
                step_size = 1.0 / steps
                current_step = int(t / step_size)
                decay_factor = 1 - (current_step * step_size)
                return original_confidence * decay_factor
        
            elif decay_type == DecayType.SIGMOID:
                # Sigmoid decay: S-curve centered at midpoint
                # Stays high initially, then drops rapidly
                midpoint = 0.5
                steepness = 10
                sigmoid = 1 / (1 + math.exp(steepness * (t - midpoint)))
                return original_confidence * sigmoid
        
            return original_confidence
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class SignalTTLManager:
    """
    Main signal TTL and confidence decay manager.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Default settings
            self.default_ttl_seconds = self.config.get('default_ttl_seconds', 300)  # 5 minutes
            self.default_decay_type = DecayType(
                self.config.get('default_decay_type', 'exponential')
            )
            self.default_decay_rate = self.config.get('default_decay_rate', 0.1)
            self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.3)
            self.cleanup_interval_seconds = self.config.get('cleanup_interval_seconds', 60)
        
            # Signal storage
            self.signals: Dict[str, SignalMetadata] = {}
            self.signals_by_symbol: Dict[str, List[str]] = defaultdict(list)
        
            # TTL overrides by signal type
            self.ttl_overrides: Dict[str, int] = self.config.get('ttl_overrides', {
                'scalp': 60,  # 1 minute
                'intraday': 300,  # 5 minutes
                'swing': 3600,  # 1 hour
                'position': 86400,  # 1 day
            })
        
            # Callbacks
            self.on_signal_stale: Optional[Callable[[SignalMetadata], None]] = None
            self.on_signal_expired: Optional[Callable[[SignalMetadata], None]] = None
        
            # Statistics
            self.stats = {
                'signals_created': 0,
                'signals_expired': 0,
                'signals_used_fresh': 0,
                'signals_used_decayed': 0,
            }
        
            logger.info("SignalTTLManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_signal(
        self,
        signal_id: str,
        symbol: str,
        signal_type: str,
        confidence: float,
        ttl_seconds: Optional[int] = None,
        decay_type: Optional[DecayType] = None,
        source: str = "",
        metadata: Optional[Dict] = None
    ) -> SignalMetadata:
        """
        Register a new signal with TTL.
        
        Args:
            signal_id: Unique signal identifier
            symbol: Trading symbol
            signal_type: Signal type (BUY, SELL, etc.)
            confidence: Initial confidence (0-1)
            ttl_seconds: Time-to-live in seconds
            decay_type: Type of confidence decay
            source: Signal source identifier
            metadata: Additional metadata
            
        Returns:
            SignalMetadata for the registered signal
        """
        # Determine TTL
        try:
            if ttl_seconds is None:
                # Check for type-based override
                for key, override_ttl in self.ttl_overrides.items():
                    if key.lower() in signal_type.lower():
                        ttl_seconds = override_ttl
                        break
                else:
                    ttl_seconds = self.default_ttl_seconds
        
            signal = SignalMetadata(
                signal_id=signal_id,
                symbol=symbol,
                signal_type=signal_type,
                original_confidence=confidence,
                current_confidence=confidence,
                created_at=datetime.now(),
                ttl_seconds=ttl_seconds,
                decay_type=decay_type or self.default_decay_type,
                decay_rate=self.default_decay_rate,
                min_confidence=self.min_confidence_threshold,
                source=source,
                metadata=metadata or {}
            )
        
            self.signals[signal_id] = signal
            self.signals_by_symbol[symbol].append(signal_id)
            self.stats['signals_created'] += 1
        
            logger.debug(f"Registered signal {signal_id} for {symbol} with TTL {ttl_seconds}s")
        
            return signal
        except Exception as e:
            logger.error(f"Error in register_signal: {e}")
            raise
    
    def get_signal(
        self,
        signal_id: str,
        update_confidence: bool = True
    ) -> Optional[SignalMetadata]:
        """
        Get signal with updated confidence.
        
        Args:
            signal_id: Signal identifier
            update_confidence: Whether to update confidence based on decay
            
        Returns:
            SignalMetadata or None if not found/expired
        """
        try:
            if signal_id not in self.signals:
                return None
        
            signal = self.signals[signal_id]
        
            if update_confidence:
                self._update_signal_confidence(signal)
        
            # Check if expired
            if signal.is_expired:
                signal.status = SignalStatus.EXPIRED
                if self.on_signal_expired:
                    self.on_signal_expired(signal)
                return None
        
            return signal
        except Exception as e:
            logger.error(f"Error in get_signal: {e}")
            raise
    
    def get_valid_signals(
        self,
        symbol: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[SignalMetadata]:
        """
        Get all valid (non-expired) signals.
        
        Args:
            symbol: Filter by symbol
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of valid signals
        """
        try:
            min_conf = min_confidence or self.min_confidence_threshold
            valid_signals = []
        
            signal_ids = (
                self.signals_by_symbol.get(symbol, [])
                if symbol else list(self.signals.keys())
            )
        
            for signal_id in signal_ids:
                signal = self.get_signal(signal_id)
                if signal and signal.current_confidence >= min_conf:
                    valid_signals.append(signal)
        
            return valid_signals
        except Exception as e:
            logger.error(f"Error in get_valid_signals: {e}")
            raise
    
    def get_freshest_signal(
        self,
        symbol: str,
        signal_type: Optional[str] = None
    ) -> Optional[SignalMetadata]:
        """
        Get the freshest valid signal for a symbol.
        
        Args:
            symbol: Trading symbol
            signal_type: Optional filter by signal type
            
        Returns:
            Freshest valid signal or None
        """
        try:
            valid = self.get_valid_signals(symbol)
        
            if signal_type:
                valid = [s for s in valid if s.signal_type == signal_type]
        
            if not valid:
                return None
        
            # Sort by freshness (highest first)
            valid.sort(key=lambda s: s.freshness_ratio, reverse=True)
        
            return valid[0]
        except Exception as e:
            logger.error(f"Error in get_freshest_signal: {e}")
            raise
    
    def _update_signal_confidence(self, signal: SignalMetadata):
        """Update signal confidence based on decay."""
        try:
            new_confidence = ConfidenceDecayCalculator.calculate(
                signal.original_confidence,
                signal.age_seconds,
                signal.ttl_seconds,
                signal.decay_type,
                signal.decay_rate
            )
        
            signal.current_confidence = new_confidence
            signal.last_updated = datetime.now()
        
            # Update status
            if signal.is_expired:
                signal.status = SignalStatus.EXPIRED
            elif new_confidence < signal.min_confidence:
                if signal.status != SignalStatus.STALE:
                    signal.status = SignalStatus.STALE
                    if self.on_signal_stale:
                        self.on_signal_stale(signal)
            elif signal.freshness_ratio < 0.5:
                signal.status = SignalStatus.DECAYING
            else:
                signal.status = SignalStatus.VALID
        except Exception as e:
            logger.error(f"Error in _update_signal_confidence: {e}")
            raise
    
    def invalidate_signal(self, signal_id: str):
        """Manually invalidate a signal."""
        try:
            if signal_id in self.signals:
                signal = self.signals[signal_id]
                signal.status = SignalStatus.EXPIRED
                signal.current_confidence = 0
            
                logger.debug(f"Invalidated signal {signal_id}")
        except Exception as e:
            logger.error(f"Error in invalidate_signal: {e}")
            raise
    
    def cleanup_expired(self) -> int:
        """
        Remove expired signals from storage.
        
        Returns:
            Number of signals removed
        """
        try:
            expired_ids = []
        
            for signal_id, signal in self.signals.items():
                if signal.is_expired or signal.status == SignalStatus.EXPIRED:
                    expired_ids.append(signal_id)
        
            for signal_id in expired_ids:
                signal = self.signals.pop(signal_id)
            
                # Remove from symbol index
                if signal.symbol in self.signals_by_symbol:
                    if signal_id in self.signals_by_symbol[signal.symbol]:
                        self.signals_by_symbol[signal.symbol].remove(signal_id)
            
                self.stats['signals_expired'] += 1
        
            if expired_ids:
                logger.debug(f"Cleaned up {len(expired_ids)} expired signals")
        
            return len(expired_ids)
        except Exception as e:
            logger.error(f"Error in cleanup_expired: {e}")
            raise
    
    def use_signal(self, signal_id: str) -> Optional[SignalMetadata]:
        """
        Mark a signal as used and track statistics.
        
        Args:
            signal_id: Signal identifier
            
        Returns:
            Signal if valid, None otherwise
        """
        try:
            signal = self.get_signal(signal_id)
        
            if signal:
                if signal.freshness_ratio > 0.8:
                    self.stats['signals_used_fresh'] += 1
                else:
                    self.stats['signals_used_decayed'] += 1
        
            return signal
        except Exception as e:
            logger.error(f"Error in use_signal: {e}")
            raise
    
    def get_signal_health(self, signal_id: str) -> Dict[str, Any]:
        """
        Get detailed health information for a signal.
        
        Returns:
            Health metrics dictionary
        """
        try:
            signal = self.get_signal(signal_id)
        
            if not signal:
                return {'status': 'not_found'}
        
            return {
                'signal_id': signal_id,
                'status': signal.status.value,
                'freshness_ratio': signal.freshness_ratio,
                'confidence_decay': signal.original_confidence - signal.current_confidence,
                'decay_rate_per_minute': (
                    (signal.original_confidence - signal.current_confidence) /
                    (signal.age_seconds / 60) if signal.age_seconds > 0 else 0
                ),
                'remaining_ttl_seconds': signal.remaining_ttl_seconds,
                'is_usable': (
                    signal.status in [SignalStatus.FRESH, SignalStatus.VALID, SignalStatus.DECAYING]
                    and signal.current_confidence >= self.min_confidence_threshold
                )
            }
        except Exception as e:
            logger.error(f"Error in get_signal_health: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        try:
            active_signals = len(self.signals)
            valid_signals = len([s for s in self.signals.values() if not s.is_expired])
        
            avg_confidence = 0
            if valid_signals > 0:
                avg_confidence = sum(
                    s.current_confidence for s in self.signals.values() if not s.is_expired
                ) / valid_signals
        
            return {
                'active_signals': active_signals,
                'valid_signals': valid_signals,
                'expired_signals': self.stats['signals_expired'],
                'total_created': self.stats['signals_created'],
                'signals_used_fresh': self.stats['signals_used_fresh'],
                'signals_used_decayed': self.stats['signals_used_decayed'],
                'average_confidence': avg_confidence,
                'symbols_tracked': len(self.signals_by_symbol),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise


# Factory function
def create_signal_ttl_manager(config: Optional[Dict] = None) -> SignalTTLManager:
    """Create SignalTTLManager instance."""
    return SignalTTLManager(config)


# Example usage
if __name__ == "__main__":
    import time
    
    manager = create_signal_ttl_manager({
        'default_ttl_seconds': 10,
        'default_decay_type': 'exponential',
        'min_confidence_threshold': 0.3
    })
    
    print("=" * 60)
    print("SIGNAL TTL AND CONFIDENCE DECAY MANAGER")
    print("=" * 60)
    
    # Register signals
    signal1 = manager.register_signal(
        signal_id="SIG001",
        symbol="EURUSD",
        signal_type="BUY",
        confidence=0.85,
        ttl_seconds=10,
        decay_type=DecayType.EXPONENTIAL
    )
    
    signal2 = manager.register_signal(
        signal_id="SIG002",
        symbol="EURUSD",
        signal_type="SELL",
        confidence=0.75,
        ttl_seconds=10,
        decay_type=DecayType.LINEAR
    )
    
    print(f"\nRegistered signals:")
    print(f"  SIG001: {signal1.signal_type} @ {signal1.original_confidence:.0%} (exponential decay)")
    print(f"  SIG002: {signal2.signal_type} @ {signal2.original_confidence:.0%} (linear decay)")
    
    # Watch decay over time
    print("\n" + "=" * 60)
    print("CONFIDENCE DECAY OVER TIME")
    print("=" * 60)
    
    for i in range(12):
        time.sleep(1)
        
        s1 = manager.get_signal("SIG001")
        s2 = manager.get_signal("SIG002")
        
        if s1 or s2:
            print(f"\nSecond {i+1}:")
            if s1:
                print(f"  SIG001: {s1.current_confidence:.1%} ({s1.status.value})")
            else:
                print(f"  SIG001: EXPIRED")
            if s2:
                print(f"  SIG002: {s2.current_confidence:.1%} ({s2.status.value})")
            else:
                print(f"  SIG002: EXPIRED")
    
    # Get valid signals
    print("\n" + "=" * 60)
    print("VALID SIGNALS")
    print("=" * 60)
    
    valid = manager.get_valid_signals("EURUSD")
    print(f"\nValid signals for EURUSD: {len(valid)}")
    
    # Cleanup
    cleaned = manager.cleanup_expired()
    print(f"Cleaned up {cleaned} expired signals")
    
    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
