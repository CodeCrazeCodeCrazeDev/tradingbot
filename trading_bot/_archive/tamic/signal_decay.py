"""
TAMIC Signal Decay

Implements signal half-life enforcement:
- Estimates predictive half-life for each signal
- Tracks decay across regimes
- Automatically suppresses signals past expiration
- Treats expired signals as false information
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from .core import TimeHorizon, SignalHalfLife

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal with decay tracking"""
    id: str
    symbol: str
    horizon: TimeHorizon
    signal_type: str
    direction: int  # 1 for bullish, -1 for bearish, 0 for neutral
    confidence: float  # 0-1
    creation_time: datetime
    half_life: SignalHalfLife
    half_life_seconds: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        """Get signal age in seconds"""
        return (datetime.now() - self.creation_time).total_seconds()
    
    @property
    def decay_factor(self) -> float:
        """Calculate decay factor based on half-life"""
        if self.half_life_seconds <= 0:
            return 0.0
        
        age = self.age_seconds
        return 2 ** (-age / self.half_life_seconds)
    
    @property
    def current_confidence(self) -> float:
        """Get current confidence after decay"""
        return self.confidence * self.decay_factor
    
    @property
    def is_expired(self) -> bool:
        """Check if signal is expired (less than 10% of original confidence)"""
        return self.decay_factor < 0.1


@dataclass
class SignalDecayResult:
    """Result from signal decay analysis"""
    signals: List[Signal]
    active_signals: List[Signal]
    expired_signals: List[Signal]
    half_life: SignalHalfLife
    confidence: float
    is_expired: bool
    reason: str = ""


class SignalExpirationPolicy:
    """
    Policy for signal expiration handling.
    
    Determines how expired signals are treated and what actions to take.
    """
    
    def __init__(self, strict_expiration: bool = True):
        """
        Initialize signal expiration policy.
        
        Args:
            strict_expiration: If True, expired signals are treated as false information
        """
        self.strict_expiration = strict_expiration
        self.logger = logging.getLogger("trading_bot.tamic.signal_expiration")
    
    def check_signal(self, signal: Signal) -> Tuple[bool, str]:
        """
        Check if a signal should be considered expired.
        
        Args:
            signal: The signal to check
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not self.strict_expiration:
            # In non-strict mode, signals are never considered "expired"
            # but their confidence still decays
            return True, ""
        
        if signal.is_expired:
            return False, f"Signal expired (age: {signal.age_seconds:.1f}s, half-life: {signal.half_life_seconds:.1f}s)"
        
        return True, ""


class HalfLifeTracker:
    """
    Tracks signal half-lives and adjusts based on market conditions.
    """
    
    def __init__(self):
        """Initialize half-life tracker"""
        self.logger = logging.getLogger("trading_bot.tamic.half_life_tracker")
        
        # Default half-life values in seconds
        self.default_half_lives = {
            TimeHorizon.MICROSTRUCTURE: {
                "default": 60,  # 1 minute
                "trending": 90,  # 1.5 minutes
                "ranging": 45,   # 45 seconds
                "volatile": 30   # 30 seconds
            },
            TimeHorizon.INTRADAY: {
                "default": 3600,  # 1 hour
                "trending": 5400,  # 1.5 hours
                "ranging": 2700,   # 45 minutes
                "volatile": 1800    # 30 minutes
            },
            TimeHorizon.SHORT_SWING: {
                "default": 43200,  # 12 hours
                "trending": 64800,  # 18 hours
                "ranging": 32400,   # 9 hours
                "volatile": 21600   # 6 hours
            },
            TimeHorizon.MEDIUM_HORIZON: {
                "default": 172800,  # 2 days
                "trending": 259200,  # 3 days
                "ranging": 129600,   # 1.5 days
                "volatile": 86400    # 1 day
            }
        }
        
        # Signal type specific adjustments
        self.signal_type_adjustments = {
            "trend": 1.5,      # Trend signals last longer
            "reversal": 0.7,   # Reversal signals decay faster
            "breakout": 0.8,   # Breakout signals decay faster
            "support": 1.2,    # Support/resistance signals last longer
            "resistance": 1.2,
            "momentum": 0.9,   # Momentum signals decay slightly faster
            "volatility": 0.6, # Volatility signals decay much faster
            "sentiment": 0.8,  # Sentiment signals decay faster
            "fundamental": 2.0 # Fundamental signals last much longer
        }
        
        # Performance tracking for half-life adjustment
        self.performance_history = {}
    
    def estimate_half_life(
        self,
        horizon: TimeHorizon,
        signal_type: str,
        market_regime: str = "default"
    ) -> Tuple[SignalHalfLife, float]:
        """
        Estimate half-life for a signal based on horizon, type, and market regime.
        
        Args:
            horizon: Time horizon
            signal_type: Type of signal
            market_regime: Current market regime
            
        Returns:
            Tuple of (half_life_enum, half_life_seconds)
        """
        # Get base half-life for horizon and regime
        base_seconds = self.default_half_lives.get(horizon, {}).get(
            market_regime, 
            self.default_half_lives.get(horizon, {}).get("default", 3600)
        )
        
        # Apply signal type adjustment
        adjustment = self.signal_type_adjustments.get(signal_type.lower(), 1.0)
        half_life_seconds = base_seconds * adjustment
        
        # Determine half-life enum
        half_life_enum = self._seconds_to_half_life_enum(half_life_seconds)
        
        return half_life_enum, half_life_seconds
    
    def _seconds_to_half_life_enum(self, seconds: float) -> SignalHalfLife:
        """Convert seconds to half-life enum"""
        if seconds < 3600:  # Less than 1 hour
            return SignalHalfLife.VERY_SHORT
        elif seconds < 14400:  # Less than 4 hours
            return SignalHalfLife.SHORT
        elif seconds < 86400:  # Less than 24 hours
            return SignalHalfLife.MEDIUM
        elif seconds < 259200:  # Less than 3 days
            return SignalHalfLife.LONG
        else:
            return SignalHalfLife.VERY_LONG
    
    def update_from_performance(
        self,
        signal_id: str,
        was_successful: bool,
        actual_duration: float
    ) -> None:
        """
        Update half-life estimates based on actual signal performance.
        
        Args:
            signal_id: ID of the signal
            was_successful: Whether the signal was successful
            actual_duration: Actual duration the signal remained valid in seconds
        """
        if signal_id not in self.performance_history:
            self.logger.warning(f"Signal {signal_id} not found in performance history")
            return
        
        # This would implement a learning mechanism to adjust half-lives
        # based on actual performance
        # For now, we'll just log the information
        self.logger.info(
            f"Signal {signal_id} performance: success={was_successful}, "
            f"actual_duration={actual_duration:.1f}s"
        )


class SignalDecay:
    """
    Implements signal half-life enforcement.
    
    Estimates predictive half-life for each signal, tracks decay across regimes,
    and automatically suppresses signals past expiration.
    """
    
    def __init__(self, strict_expiration: bool = True):
        """
        Initialize signal decay system.
        
        Args:
            strict_expiration: If True, expired signals are treated as false information
        """
        self.logger = logging.getLogger("trading_bot.tamic.signal_decay")
        self.signals = {}  # Dict of signal_id -> Signal
        self.half_life_tracker = HalfLifeTracker()
        self.expiration_policy = SignalExpirationPolicy(strict_expiration)
    
    def create_signal(
        self,
        symbol: str,
        horizon: TimeHorizon,
        signal_type: str,
        direction: int,
        confidence: float,
        source: str,
        market_regime: str = "default",
        metadata: Dict[str, Any] = None
    ) -> Signal:
        """
        Create a new signal with appropriate half-life.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            signal_type: Type of signal
            direction: Direction (1=bullish, -1=bearish, 0=neutral)
            confidence: Initial confidence (0-1)
            source: Source of the signal
            market_regime: Current market regime
            metadata: Additional metadata
            
        Returns:
            Created Signal object
        """
        # Generate unique ID
        signal_id = str(uuid.uuid4())
        
        # Estimate half-life
        half_life_enum, half_life_seconds = self.half_life_tracker.estimate_half_life(
            horizon, signal_type, market_regime
        )
        
        # Create signal
        signal = Signal(
            id=signal_id,
            symbol=symbol,
            horizon=horizon,
            signal_type=signal_type,
            direction=direction,
            confidence=confidence,
            creation_time=datetime.now(),
            half_life=half_life_enum,
            half_life_seconds=half_life_seconds,
            source=source,
            metadata=metadata or {}
        )
        
        # Store signal
        self.signals[signal_id] = signal
        
        self.logger.info(
            f"Created {signal_type} signal for {symbol} on {horizon.value} horizon "
            f"with {half_life_enum.value} half-life ({half_life_seconds:.1f}s)"
        )
        
        return signal
    
    def get_signal(self, signal_id: str) -> Optional[Signal]:
        """Get a signal by ID"""
        return self.signals.get(signal_id)
    
    def get_signals_for_symbol(
        self,
        symbol: str,
        horizon: Optional[TimeHorizon] = None
    ) -> List[Signal]:
        """Get all signals for a symbol, optionally filtered by horizon"""
        result = []
        for signal in self.signals.values():
            if signal.symbol == symbol:
                if horizon is None or signal.horizon == horizon:
                    result.append(signal)
        return result
    
    def update_signal_confidence(
        self,
        signal_id: str,
        new_confidence: float
    ) -> Optional[Signal]:
        """Update a signal's base confidence"""
        signal = self.get_signal(signal_id)
        if signal:
            signal.confidence = new_confidence
            self.logger.debug(f"Updated signal {signal_id} confidence to {new_confidence}")
        return signal
    
    def expire_signal(self, signal_id: str) -> None:
        """Manually expire a signal"""
        if signal_id in self.signals:
            del self.signals[signal_id]
            self.logger.info(f"Manually expired signal {signal_id}")
    
    def cleanup_expired_signals(self) -> int:
        """
        Remove expired signals from storage.
        
        Returns:
            Number of signals removed
        """
        expired_ids = []
        for signal_id, signal in self.signals.items():
            if signal.is_expired:
                expired_ids.append(signal_id)
        
        for signal_id in expired_ids:
            del self.signals[signal_id]
        
        if expired_ids:
            self.logger.debug(f"Cleaned up {len(expired_ids)} expired signals")
        
        return len(expired_ids)
    
    async def analyze_signals(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any]
    ) -> SignalDecayResult:
        """
        Analyze signals for a symbol and horizon, applying decay.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            
        Returns:
            SignalDecayResult with active and expired signals
        """
        # Clean up expired signals first
        self.cleanup_expired_signals()
        
        # Get signals for this symbol and horizon
        signals = self.get_signals_for_symbol(symbol, horizon)
        
        # Separate active and expired signals
        active_signals = []
        expired_signals = []
        
        for signal in signals:
            is_valid, reason = self.expiration_policy.check_signal(signal)
            if is_valid:
                active_signals.append(signal)
            else:
                expired_signals.append(signal)
        
        # Determine overall half-life based on active signals
        if active_signals:
            # Use the most common half-life among active signals
            half_life_counts = {}
            for signal in active_signals:
                half_life = signal.half_life
                half_life_counts[half_life] = half_life_counts.get(half_life, 0) + 1
            
            most_common_half_life = max(
                half_life_counts.items(), 
                key=lambda x: x[1]
            )[0]
        else:
            # Default half-life if no active signals
            most_common_half_life = SignalHalfLife.MEDIUM
        
        # Calculate aggregate confidence from active signals
        if active_signals:
            # Weighted average of current confidence values
            total_weight = 0
            weighted_confidence = 0
            
            for signal in active_signals:
                # Weight by original confidence
                weight = signal.confidence
                total_weight += weight
                weighted_confidence += signal.current_confidence * weight
            
            if total_weight > 0:
                aggregate_confidence = weighted_confidence / total_weight
            else:
                aggregate_confidence = 0.0
        else:
            aggregate_confidence = 0.0
        
        # Determine if all signals are expired
        is_expired = len(active_signals) == 0 and len(signals) > 0
        reason = "All signals expired" if is_expired else ""
        
        return SignalDecayResult(
            signals=signals,
            active_signals=active_signals,
            expired_signals=expired_signals,
            half_life=most_common_half_life,
            confidence=aggregate_confidence,
            is_expired=is_expired,
            reason=reason
        )
    
    def extract_signals_from_market_data(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        market_regime: str = "default"
    ) -> List[Signal]:
        """
        Extract signals from market data.
        
        This is a convenience method to create signals from market data.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            market_regime: Current market regime
            
        Returns:
            List of created signals
        """
        created_signals = []
        
        # Check if market_data contains signals
        if "signals" in market_data:
            signals_data = market_data["signals"]
            
            if isinstance(signals_data, list):
                for signal_data in signals_data:
                    if isinstance(signal_data, dict):
                        signal_type = signal_data.get("type", "unknown")
                        direction = signal_data.get("direction", 0)
                        confidence = signal_data.get("confidence", 0.5)
                        source = signal_data.get("source", "market_data")
                        metadata = signal_data.get("metadata", {})
                        
                        signal = self.create_signal(
                            symbol=symbol,
                            horizon=horizon,
                            signal_type=signal_type,
                            direction=direction,
                            confidence=confidence,
                            source=source,
                            market_regime=market_regime,
                            metadata=metadata
                        )
                        
                        created_signals.append(signal)
            
            elif isinstance(signals_data, dict):
                for signal_type, signal_data in signals_data.items():
                    if isinstance(signal_data, dict):
                        direction = signal_data.get("direction", 0)
                        confidence = signal_data.get("confidence", 0.5)
                        source = signal_data.get("source", "market_data")
                        metadata = signal_data.get("metadata", {})
                        
                        signal = self.create_signal(
                            symbol=symbol,
                            horizon=horizon,
                            signal_type=signal_type,
                            direction=direction,
                            confidence=confidence,
                            source=source,
                            market_regime=market_regime,
                            metadata=metadata
                        )
                        
                        created_signals.append(signal)
        
        return created_signals
