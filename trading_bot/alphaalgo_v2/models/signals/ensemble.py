"""
AlphaAlgo V2 Ensemble Signal Generator

Combines multiple signal generators for robust signals.
"""

import logging
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timedelta

from ...core.interfaces import ISignalGenerator
from ...core.types import Signal, SignalType, MarketData
from ...core.constants import DEFAULT_CONFIDENCE_THRESHOLD
import asyncio

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



logger = logging.getLogger(__name__)


class EnsembleSignalGenerator(ISignalGenerator):
    """
    Ensemble signal generator
    
    Combines signals from multiple generators using:
    - Weighted voting
    - Confidence aggregation
    - Conflict resolution
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._name = "ensemble"
        self._confidence_threshold = self.config.get(
            "confidence_threshold",
            DEFAULT_CONFIDENCE_THRESHOLD
        )
        
        # Generators with weights
        self._generators: List[tuple[ISignalGenerator, float]] = []
        self._min_agreement = self.config.get("min_agreement", 0.6)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold
    
    def add_generator(
        self,
        generator: ISignalGenerator,
        weight: float = 1.0
    ) -> None:
        """Add a signal generator with weight"""
        self._generators.append((generator, weight))
        logger.info(f"Added generator: {generator.name} (weight={weight})")
    
    def remove_generator(self, name: str) -> bool:
        """Remove a generator by name"""
        for i, (gen, _) in enumerate(self._generators):
            if gen.name == name:
                del self._generators[i]
                return True
        return False
    
    async def generate(
        self,
        symbol: str,
        data: MarketData,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Signal]:
        """
        Generate ensemble signal
        
        Aggregates signals from all generators and returns
        consensus signal if agreement threshold is met.
        """
        if not self._generators:
            logger.warning("No generators configured")
            return None
        
        # Collect signals from all generators
        signals: List[tuple[Signal, float]] = []
        
        for generator, weight in self._generators:
            try:
                signal = await generator.generate(symbol, data, context)
                if signal:
                    signals.append((signal, weight))
            except Exception as e:
                logger.error(f"Generator {generator.name} failed: {e}")
        
        if not signals:
            return None
        
        # Aggregate signals
        return self._aggregate_signals(symbol, data, signals)
    
    def _aggregate_signals(
        self,
        symbol: str,
        data: MarketData,
        signals: List[tuple[Signal, float]]
    ) -> Optional[Signal]:
        """Aggregate signals using weighted voting"""
        total_weight = sum(w for _, w in signals)
        
        # Count votes
        buy_weight = 0.0
        sell_weight = 0.0
        buy_confidence = 0.0
        sell_confidence = 0.0
        
        for signal, weight in signals:
            if signal.signal_type == SignalType.BUY:
                buy_weight += weight
                buy_confidence += signal.confidence * weight
            elif signal.signal_type == SignalType.SELL:
                sell_weight += weight
                sell_confidence += signal.confidence * weight
        
        # Determine consensus
        buy_agreement = buy_weight / total_weight if total_weight > 0 else 0
        sell_agreement = sell_weight / total_weight if total_weight > 0 else 0
        
        if buy_agreement >= self._min_agreement:
            signal_type = SignalType.BUY
            confidence = buy_confidence / buy_weight if buy_weight > 0 else 0
            agreement = buy_agreement
        elif sell_agreement >= self._min_agreement:
            signal_type = SignalType.SELL
            confidence = sell_confidence / sell_weight if sell_weight > 0 else 0
            agreement = sell_agreement
        else:
            return None
        
        if confidence < self._confidence_threshold:
            return None
        
        # Get price and levels from first matching signal
        matching_signals = [
            s for s, _ in signals
            if s.signal_type == signal_type
        ]
        
        if not matching_signals:
            return None
        
        base_signal = matching_signals[0]
        
        # Average stop loss and take profit
        stop_losses = [s.stop_loss for s in matching_signals if s.stop_loss]
        take_profits = [s.take_profit for s in matching_signals if s.take_profit]
        
        return Signal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            signal_type=signal_type,
            price=base_signal.price,
            confidence=confidence,
            stop_loss=sum(stop_losses) / len(stop_losses) if stop_losses else None,
            take_profit=sum(take_profits) / len(take_profits) if take_profits else None,
            timeframe=data.timeframe,
            source=self._name,
            metadata={
                "agreement": agreement,
                "generators": len(signals),
                "buy_weight": buy_weight,
                "sell_weight": sell_weight,
            },
            expires_at=datetime.now() + timedelta(minutes=30),
        )
    
    def get_confidence(self, signal: Signal) -> float:
        """Get signal confidence"""
        return signal.confidence
    
    async def validate(self, signal: Signal) -> bool:
        """Validate signal"""
        if signal.is_expired:
            return False
        
        if signal.confidence < self._confidence_threshold:
            return False
        
        # Check agreement threshold
        agreement = signal.metadata.get("agreement", 0)
        if agreement < self._min_agreement:
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ensemble statistics"""
        return {
            "generators": len(self._generators),
            "generator_names": [g.name for g, _ in self._generators],
            "min_agreement": self._min_agreement,
            "confidence_threshold": self._confidence_threshold,
        }
