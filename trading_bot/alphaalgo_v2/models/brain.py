"""
AlphaAlgo V2 Intelligence Brain

Coordinates all ML/AI models for intelligent trading decisions.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.types import Signal, SignalType, MarketData
from ..core.constants import MarketRegime
from .signals.generator import SignalGenerator
from .signals.ensemble import EnsembleSignalGenerator
from .regime.detector import RegimeDetector, RegimeAnalysis
from .forecasting.simple import SimpleForecaster, Forecast

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


@dataclass
class IntelligenceResult:
    """Result from intelligence analysis"""
    signal: Optional[Signal]
    regime: RegimeAnalysis
    forecast: Forecast
    confidence: float
    reasoning: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligenceBrain:
    """
    Central intelligence coordinator
    
    Combines:
    - Signal generation
    - Regime detection
    - Price forecasting
    - Confidence calibration
    
    Provides unified trading decisions with reasoning.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self._signal_generator = SignalGenerator(self.config.get("signals", {}))
        self._ensemble = EnsembleSignalGenerator(self.config.get("ensemble", {}))
        self._regime_detector = RegimeDetector(self.config.get("regime", {}))
        self._forecaster = SimpleForecaster(self.config.get("forecasting", {}))
        
        # Add signal generator to ensemble
        self._ensemble.add_generator(self._signal_generator, weight=1.0)
        
        # State
        self._last_regime: Optional[RegimeAnalysis] = None
        self._regime_history: List[RegimeAnalysis] = []
    
    async def analyze(
        self,
        symbol: str,
        data: MarketData,
        context: Optional[Dict[str, Any]] = None
    ) -> IntelligenceResult:
        """
        Perform full intelligence analysis
        
        Args:
            symbol: Trading symbol
            data: Market data
            context: Additional context
            
        Returns:
            IntelligenceResult with signal, regime, forecast, and reasoning
        """
        reasoning = []
        
        # 1. Detect regime
        regime = self._regime_detector.detect(data.ohlcv)
        self._update_regime_history(regime)
        reasoning.append(f"Regime: {regime.regime.value} (confidence: {regime.confidence:.0%})")
        
        # 2. Generate forecast
        forecast = self._forecaster.forecast(data.ohlcv)
        reasoning.append(f"Forecast: {forecast.direction} ({forecast.predicted_change:.2%})")
        
        # 3. Generate signal
        signal = await self._generate_regime_aware_signal(
            symbol, data, regime, forecast, context
        )
        
        if signal:
            reasoning.append(f"Signal: {signal.signal_type.value} at {signal.price:.5f}")
            reasoning.append(f"Confidence: {signal.confidence:.0%}")
        else:
            reasoning.append("No signal generated")
        
        # 4. Calculate overall confidence
        confidence = self._calculate_overall_confidence(signal, regime, forecast)
        
        return IntelligenceResult(
            signal=signal,
            regime=regime,
            forecast=forecast,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "symbol": symbol,
                "timeframe": data.timeframe,
                "timestamp": datetime.now().isoformat(),
            },
        )
    
    async def _generate_regime_aware_signal(
        self,
        symbol: str,
        data: MarketData,
        regime: RegimeAnalysis,
        forecast: Forecast,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Signal]:
        """Generate signal adjusted for market regime"""
        # Add regime to context
        ctx = context or {}
        ctx["regime"] = regime.regime.value
        ctx["volatility"] = regime.volatility
        ctx["forecast"] = forecast.direction
        
        # Generate base signal
        signal = await self._ensemble.generate(symbol, data, ctx)
        
        if signal is None:
            return None
        
        # Adjust confidence based on regime alignment
        adjusted_confidence = self._adjust_for_regime(signal, regime, forecast)
        
        # Create adjusted signal
        return Signal(
            id=signal.id,
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            price=signal.price,
            confidence=adjusted_confidence,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            timeframe=signal.timeframe,
            source="brain",
            metadata={
                **signal.metadata,
                "regime": regime.regime.value,
                "forecast": forecast.direction,
                "original_confidence": signal.confidence,
            },
            expires_at=signal.expires_at,
        )
    
    def _adjust_for_regime(
        self,
        signal: Signal,
        regime: RegimeAnalysis,
        forecast: Forecast
    ) -> float:
        """Adjust signal confidence based on regime and forecast alignment"""
        confidence = signal.confidence
        
        # Boost if signal aligns with regime
        if signal.signal_type == SignalType.BUY:
            if regime.regime == MarketRegime.TRENDING_UP:
                confidence *= 1.2
            elif regime.regime == MarketRegime.TRENDING_DOWN:
                confidence *= 0.7
        elif signal.signal_type == SignalType.SELL:
            if regime.regime == MarketRegime.TRENDING_DOWN:
                confidence *= 1.2
            elif regime.regime == MarketRegime.TRENDING_UP:
                confidence *= 0.7
        
        # Boost if signal aligns with forecast
        if signal.signal_type == SignalType.BUY and forecast.direction == "up":
            confidence *= 1.1
        elif signal.signal_type == SignalType.SELL and forecast.direction == "down":
            confidence *= 1.1
        elif (signal.signal_type == SignalType.BUY and forecast.direction == "down") or \
             (signal.signal_type == SignalType.SELL and forecast.direction == "up"):
            confidence *= 0.8
        
        # Reduce in volatile regime
        if regime.regime == MarketRegime.VOLATILE:
            confidence *= 0.8
        
        return min(confidence, 1.0)
    
    def _calculate_overall_confidence(
        self,
        signal: Optional[Signal],
        regime: RegimeAnalysis,
        forecast: Forecast
    ) -> float:
        """Calculate overall analysis confidence"""
        if signal is None:
            return 0.0
        
        # Weighted average
        signal_weight = 0.5
        regime_weight = 0.3
        forecast_weight = 0.2
        
        return (
            signal.confidence * signal_weight +
            regime.confidence * regime_weight +
            forecast.confidence * forecast_weight
        )
    
    def _update_regime_history(self, regime: RegimeAnalysis) -> None:
        """Update regime history for transition detection"""
        self._regime_history.append(regime)
        
        # Keep last 10 regimes
        if len(self._regime_history) > 10:
            self._regime_history = self._regime_history[-10:]
        
        self._last_regime = regime
    
    def is_regime_transitioning(self) -> bool:
        """Check if regime is transitioning"""
        if len(self._regime_history) < 3:
            return False
        
        recent = self._regime_history[-3:]
        regimes = [r.regime for r in recent]
        
        # Transitioning if regimes are different
        return len(set(regimes)) > 1
    
    def get_regime_summary(self) -> Dict[str, Any]:
        """Get regime analysis summary"""
        if not self._last_regime:
            return {}
        
        return {
            "current_regime": self._last_regime.regime.value,
            "confidence": self._last_regime.confidence,
            "volatility": self._last_regime.volatility,
            "trend_strength": self._last_regime.trend_strength,
            "transitioning": self.is_regime_transitioning(),
            "description": self._regime_detector.get_regime_description(
                self._last_regime.regime
            ),
        }
    
    def add_signal_generator(
        self,
        generator,
        weight: float = 1.0
    ) -> None:
        """Add a signal generator to the ensemble"""
        self._ensemble.add_generator(generator, weight)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get brain statistics"""
        return {
            "ensemble": self._ensemble.get_stats(),
            "regime": self.get_regime_summary(),
            "regime_history_length": len(self._regime_history),
        }
