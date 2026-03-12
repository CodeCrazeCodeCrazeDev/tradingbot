"""
Signal Engine - Unified interface for signal generation and management

This module provides a centralized SignalEngine class that coordinates
all signal generation, validation, and lifecycle management.

Author: AlphaAlgo Trading System
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    ENTRY_LONG = auto()
    ENTRY_SHORT = auto()
    EXIT_LONG = auto()
    EXIT_SHORT = auto()
    SCALE_IN = auto()
    SCALE_OUT = auto()
    HOLD = auto()
    NO_SIGNAL = auto()


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class Signal:
    """Represents a trading signal"""
    signal_id: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float
    price: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    expiry: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if signal is still valid"""
        if self.expiry and datetime.now() > self.expiry:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'signal_type': self.signal_type.name,
            'strength': self.strength.name,
            'confidence': self.confidence,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'expiry': self.expiry.isoformat() if self.expiry else None
        }


class SignalEngine:
    """
    Unified Signal Engine for generating and managing trading signals.
    
    This class coordinates:
    - Multiple signal generators
    - Signal validation and filtering
    - Signal lifecycle management
    - Ensemble signal combination
    - Regime-based signal gating
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Signal Engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.generators: Dict[str, Callable] = {}
        self.validators: List[Callable] = []
        self.active_signals: Dict[str, Signal] = {}
        self.signal_history: List[Signal] = []
        self.current_regime: str = "unknown"
        
        # Default settings
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.max_signals_per_symbol = self.config.get('max_signals_per_symbol', 3)
        self.signal_ttl_seconds = self.config.get('signal_ttl_seconds', 300)
        
        logger.info("SignalEngine initialized")
    
    def register_generator(self, name: str, generator: Callable) -> None:
        """
        Register a signal generator.
        
        Args:
            name: Generator name
            generator: Callable that generates signals
        """
        self.generators[name] = generator
        logger.info(f"Registered signal generator: {name}")
    
    def register_validator(self, validator: Callable) -> None:
        """
        Register a signal validator.
        
        Args:
            validator: Callable that validates signals
        """
        self.validators.append(validator)
        logger.info(f"Registered signal validator: {validator.__name__}")
    
    def set_regime(self, regime: str) -> None:
        """
        Set the current market regime.
        
        Args:
            regime: Market regime identifier
        """
        self.current_regime = regime
        logger.info(f"Market regime set to: {regime}")
    
    def generate_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        generators: Optional[List[str]] = None
    ) -> List[Signal]:
        """
        Generate signals for a symbol using registered generators.
        
        Args:
            symbol: Trading symbol
            data: Market data DataFrame
            generators: Optional list of specific generators to use
        
        Returns:
            List of generated signals
        """
        signals = []
        
        # Use specified generators or all registered
        gen_names = generators or list(self.generators.keys())
        
        for gen_name in gen_names:
            if gen_name not in self.generators:
                logger.warning(f"Generator not found: {gen_name}")
                continue
            try:
            
                generator = self.generators[gen_name]
                gen_signals = generator(symbol, data, self.current_regime)
                
                if gen_signals:
                    if isinstance(gen_signals, Signal):
                        gen_signals = [gen_signals]
                    signals.extend(gen_signals)
                    
            except Exception as e:
                logger.error(f"Error in generator {gen_name}: {e}")
        
        # Validate signals
        validated_signals = self._validate_signals(signals)
        
        # Filter by confidence
        filtered_signals = [
            s for s in validated_signals 
            if s.confidence >= self.min_confidence
        ]
        
        # Store signals
        for signal in filtered_signals:
            self.active_signals[signal.signal_id] = signal
            self.signal_history.append(signal)
        
        logger.info(f"Generated {len(filtered_signals)} signals for {symbol}")
        return filtered_signals
    
    def _validate_signals(self, signals: List[Signal]) -> List[Signal]:
        """Validate signals through all registered validators"""
        validated = []
        
        for signal in signals:
            is_valid = True
            
            for validator in self.validators:
                try:
                    if not validator(signal):
                        is_valid = False
                        break
                except Exception as e:
                    logger.error(f"Validator error: {e}")
                    is_valid = False
                    break
            
            if is_valid:
                validated.append(signal)
        
        return validated
    
    def combine_signals(
        self,
        signals: List[Signal],
        method: str = "weighted_vote"
    ) -> Optional[Signal]:
        """
        Combine multiple signals into a single signal.
        
        Args:
            signals: List of signals to combine
            method: Combination method
        
        Returns:
            Combined signal or None
        """
        if not signals:
            return None
        
        if len(signals) == 1:
            return signals[0]
        
        if method == "weighted_vote":
            return self._weighted_vote_combine(signals)
        elif method == "majority":
            return self._majority_combine(signals)
        elif method == "highest_confidence":
            return max(signals, key=lambda s: s.confidence)
        else:
            logger.warning(f"Unknown combination method: {method}")
            return signals[0]
    
    def _weighted_vote_combine(self, signals: List[Signal]) -> Signal:
        """Combine signals using weighted voting"""
        # Group by signal type
        type_votes: Dict[SignalType, float] = {}
        
        for signal in signals:
            if signal.signal_type not in type_votes:
                type_votes[signal.signal_type] = 0
            type_votes[signal.signal_type] += signal.confidence
        
        # Find winning type
        winning_type = max(type_votes.keys(), key=lambda t: type_votes[t])
        
        # Get signals of winning type
        winning_signals = [s for s in signals if s.signal_type == winning_type]
        
        # Calculate combined confidence
        combined_confidence = np.mean([s.confidence for s in winning_signals])
        
        # Use the most recent signal as base
        base_signal = max(winning_signals, key=lambda s: s.timestamp)
        
        return Signal(
            signal_id=f"combined_{base_signal.signal_id}",
            symbol=base_signal.symbol,
            signal_type=winning_type,
            strength=base_signal.strength,
            confidence=combined_confidence,
            price=base_signal.price,
            timestamp=datetime.now(),
            source="ensemble",
            metadata={
                'combined_from': [s.signal_id for s in signals],
                'vote_weights': type_votes
            },
            stop_loss=base_signal.stop_loss,
            take_profit=base_signal.take_profit
        )
    
    def _majority_combine(self, signals: List[Signal]) -> Signal:
        """Combine signals using majority voting"""
        type_counts: Dict[SignalType, int] = {}
        
        for signal in signals:
            if signal.signal_type not in type_counts:
                type_counts[signal.signal_type] = 0
            type_counts[signal.signal_type] += 1
        
        winning_type = max(type_counts.keys(), key=lambda t: type_counts[t])
        winning_signals = [s for s in signals if s.signal_type == winning_type]
        
        return max(winning_signals, key=lambda s: s.confidence)
    
    def get_active_signals(self, symbol: Optional[str] = None) -> List[Signal]:
        """
        Get active signals, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            List of active signals
        """
        # Clean expired signals
        self._cleanup_expired_signals()
        
        signals = list(self.active_signals.values())
        
        if symbol:
            signals = [s for s in signals if s.symbol == symbol]
        
        return signals
    
    def _cleanup_expired_signals(self) -> None:
        """Remove expired signals from active signals"""
        expired = [
            sid for sid, signal in self.active_signals.items()
            if not signal.is_valid()
        ]
        
        for sid in expired:
            del self.active_signals[sid]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired signals")
    
    def cancel_signal(self, signal_id: str) -> bool:
        """
        Cancel an active signal.
        
        Args:
            signal_id: Signal ID to cancel
        
        Returns:
            True if cancelled, False if not found
        """
        if signal_id in self.active_signals:
            del self.active_signals[signal_id]
            logger.info(f"Cancelled signal: {signal_id}")
            return True
        return False
    
    def get_signal_stats(self) -> Dict[str, Any]:
        """Get signal statistics"""
        return {
            'active_signals': len(self.active_signals),
            'total_generated': len(self.signal_history),
            'generators_registered': len(self.generators),
            'validators_registered': len(self.validators),
            'current_regime': self.current_regime
        }
    
    def create_signal(
        self,
        symbol: str,
        signal_type: SignalType,
        confidence: float,
        price: float,
        source: str = "manual",
        **kwargs
    ) -> Signal:
        """
        Create a new signal manually.
        
        Args:
            symbol: Trading symbol
            signal_type: Type of signal
            confidence: Confidence level (0-1)
            price: Current price
            source: Signal source
            **kwargs: Additional signal parameters
        
        Returns:
            Created signal
        """
        signal_id = f"{symbol}_{signal_type.name}_{datetime.now().timestamp()}"
        
        # Determine strength from confidence
        if confidence >= 0.9:
            strength = SignalStrength.VERY_STRONG
        elif confidence >= 0.75:
            strength = SignalStrength.STRONG
        elif confidence >= 0.6:
            strength = SignalStrength.MODERATE
        elif confidence >= 0.4:
            strength = SignalStrength.WEAK
        else:
            strength = SignalStrength.VERY_WEAK
        
        signal = Signal(
            signal_id=signal_id,
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            price=price,
            timestamp=datetime.now(),
            source=source,
            metadata=kwargs.get('metadata', {}),
            stop_loss=kwargs.get('stop_loss'),
            take_profit=kwargs.get('take_profit'),
            expiry=kwargs.get('expiry')
        )
        
        self.active_signals[signal_id] = signal
        self.signal_history.append(signal)
        
        logger.info(f"Created signal: {signal_id}")
        return signal


# Factory function
def create_signal_engine(config: Optional[Dict[str, Any]] = None) -> SignalEngine:
    """Create a configured SignalEngine instance"""
    return SignalEngine(config)


# Singleton instance
_signal_engine: Optional[SignalEngine] = None


def get_signal_engine() -> SignalEngine:
    """Get the global SignalEngine instance"""
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = SignalEngine()
    return _signal_engine
