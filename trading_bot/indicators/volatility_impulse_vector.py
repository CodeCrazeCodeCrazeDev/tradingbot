"""
Volatility Impulse Vector (VII) Indicator

A composite indicator combining:
- Rate of change of volatility (derivative of ATR)
- Volume surge detection
- Order book imbalance

Detects not just if volatility is high, but whether it's accelerating
and in which direction the energy is likely to be released.

This is the "sweet spot" detector for explosive moves.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import math

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ImpulseDirection(Enum):
    """Direction of volatility impulse."""
    BULLISH_EXPLOSION = "bullish_explosion"
    BEARISH_EXPLOSION = "bearish_explosion"
    BULLISH_BUILDING = "bullish_building"
    BEARISH_BUILDING = "bearish_building"
    NEUTRAL = "neutral"
    COMPRESSION = "compression"


class ImpulseStrength(Enum):
    """Strength of the impulse."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    EXTREME = 4


@dataclass
class VIIReading:
    """Single VII reading."""
    timestamp: datetime
    vii_value: float  # -100 to +100
    direction: ImpulseDirection
    strength: ImpulseStrength
    atr: float
    atr_acceleration: float  # Rate of change of ATR
    volume_surge: float  # Volume vs average
    order_book_imbalance: float  # -1 to +1
    price_momentum: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'vii_value': self.vii_value,
            'direction': self.direction.value,
            'strength': self.strength.name,
            'atr': self.atr,
            'atr_acceleration': self.atr_acceleration,
            'volume_surge': self.volume_surge,
            'order_book_imbalance': self.order_book_imbalance,
            'price_momentum': self.price_momentum
        }


@dataclass
class ExplosionSignal:
    """Signal for imminent price explosion."""
    timestamp: datetime
    symbol: str
    direction: ImpulseDirection
    probability: float
    expected_magnitude: float  # Expected move in ATR units
    time_horizon_minutes: int
    vii_reading: VIIReading
    trigger_conditions: List[str]
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction.value,
            'probability': self.probability,
            'expected_magnitude': self.expected_magnitude,
            'time_horizon_minutes': self.time_horizon_minutes,
            'vii_value': self.vii_reading.vii_value,
            'trigger_conditions': self.trigger_conditions,
            'analysis': self.analysis
        }


class ATRCalculator:
    """
    Calculates ATR and its derivatives.
    """
    
    def __init__(self, period: int = 14):
        self.period = period
        self.tr_values: deque = deque(maxlen=period * 3)
        self.atr_values: deque = deque(maxlen=period * 2)
    
    def add_bar(self, high: float, low: float, close: float, prev_close: Optional[float] = None):
        """Add a price bar and calculate TR."""
        if prev_close is None and self.tr_values:
            # Use previous close from last TR calculation
            prev_close = close  # Fallback
        
        # True Range calculation
        if prev_close is not None:
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
        else:
            tr = high - low
        
        self.tr_values.append(tr)
    
    def get_atr(self) -> Optional[float]:
        """Get current ATR."""
        if len(self.tr_values) < self.period:
            return None
        
        # Simple moving average of TR
        recent_tr = list(self.tr_values)[-self.period:]
        atr = sum(recent_tr) / len(recent_tr)
        
        self.atr_values.append(atr)
        return atr
    
    def get_atr_acceleration(self) -> Optional[float]:
        """
        Get rate of change of ATR (second derivative of price movement).
        
        Positive = volatility increasing
        Negative = volatility decreasing
        """
        if len(self.atr_values) < 3:
            return None
        
        recent = list(self.atr_values)[-3:]
        
        # First derivative (change in ATR)
        d1 = recent[-1] - recent[-2]
        d2 = recent[-2] - recent[-3]
        
        # Second derivative (acceleration)
        acceleration = d1 - d2
        
        # Normalize by current ATR
        if recent[-1] > 0:
            return acceleration / recent[-1]
        return 0.0


class VolumeSurgeDetector:
    """
    Detects volume surges relative to average.
    """
    
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        self.volumes: deque = deque(maxlen=lookback * 2)
    
    def add_volume(self, volume: float):
        """Add volume reading."""
        self.volumes.append(volume)
    
    def get_surge_ratio(self) -> float:
        """
        Get current volume as ratio of average.
        
        Returns:
            Ratio (1.0 = average, 2.0 = double average)
        """
        if len(self.volumes) < self.lookback:
            return 1.0
        
        recent = list(self.volumes)
        current = recent[-1]
        avg = sum(recent[:-1]) / (len(recent) - 1)
        
        if avg > 0:
            return current / avg
        return 1.0
    
    def is_surge(self, threshold: float = 1.5) -> bool:
        """Check if current volume is a surge."""
        return self.get_surge_ratio() >= threshold


class OrderBookImbalanceCalculator:
    """
    Calculates order book imbalance.
    """
    
    def __init__(self, depth_levels: int = 10):
        self.depth_levels = depth_levels
        self.imbalance_history: deque = deque(maxlen=100)
    
    def calculate(
        self,
        bids: List[Tuple[float, float]],  # (price, volume)
        asks: List[Tuple[float, float]]
    ) -> float:
        """
        Calculate order book imbalance.
        
        Returns:
            Value from -1 (all asks) to +1 (all bids)
        """
        # Sum bid volume (weighted by proximity to mid)
        bid_volume = 0
        for i, (price, vol) in enumerate(bids[:self.depth_levels]):
            weight = 1.0 / (i + 1)  # Closer levels weighted more
            bid_volume += vol * weight
        
        # Sum ask volume
        ask_volume = 0
        for i, (price, vol) in enumerate(asks[:self.depth_levels]):
            weight = 1.0 / (i + 1)
            ask_volume += vol * weight
        
        total = bid_volume + ask_volume
        if total > 0:
            imbalance = (bid_volume - ask_volume) / total
        else:
            imbalance = 0.0
        
        self.imbalance_history.append(imbalance)
        return imbalance
    
    def get_imbalance_momentum(self) -> float:
        """Get rate of change of imbalance."""
        if len(self.imbalance_history) < 5:
            return 0.0
        
        recent = list(self.imbalance_history)[-5:]
        return recent[-1] - recent[0]


class MomentumCalculator:
    """
    Calculates price momentum.
    """
    
    def __init__(self, period: int = 10):
        self.period = period
        self.prices: deque = deque(maxlen=period * 2)
    
    def add_price(self, price: float):
        """Add price."""
        self.prices.append(price)
    
    def get_momentum(self) -> float:
        """
        Get price momentum.
        
        Returns:
            Percentage change over period
        """
        if len(self.prices) < self.period:
            return 0.0
        
        recent = list(self.prices)
        current = recent[-1]
        past = recent[-self.period]
        
        if past > 0:
            return (current - past) / past * 100
        return 0.0
    
    def get_momentum_acceleration(self) -> float:
        """Get rate of change of momentum."""
        if len(self.prices) < self.period + 5:
            return 0.0
        
        recent = list(self.prices)
        
        # Current momentum
        m1 = (recent[-1] - recent[-self.period]) / recent[-self.period] if recent[-self.period] > 0 else 0
        
        # Previous momentum
        m2 = (recent[-2] - recent[-self.period-1]) / recent[-self.period-1] if recent[-self.period-1] > 0 else 0
        
        return m1 - m2


class VolatilityImpulseVector:
    """
    Main VII indicator system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Component calculators
        self.atr_calc = ATRCalculator(self.config.get('atr_period', 14))
        self.volume_detector = VolumeSurgeDetector(self.config.get('volume_lookback', 20))
        self.ob_calc = OrderBookImbalanceCalculator(self.config.get('ob_depth', 10))
        self.momentum_calc = MomentumCalculator(self.config.get('momentum_period', 10))
        
        # History
        self.readings: deque = deque(maxlen=500)
        
        # Weights for VII calculation
        self.weights = {
            'atr_acceleration': self.config.get('w_atr_accel', 0.35),
            'volume_surge': self.config.get('w_volume', 0.25),
            'ob_imbalance': self.config.get('w_ob', 0.25),
            'momentum': self.config.get('w_momentum', 0.15)
        }
        
        logger.info("VolatilityImpulseVector initialized")
    
    def update(
        self,
        high: float,
        low: float,
        close: float,
        volume: float,
        prev_close: Optional[float] = None,
        bids: Optional[List[Tuple[float, float]]] = None,
        asks: Optional[List[Tuple[float, float]]] = None
    ) -> Optional[VIIReading]:
        """
        Update VII with new data.
        
        Args:
            high: Bar high
            low: Bar low
            close: Bar close
            volume: Bar volume
            prev_close: Previous close
            bids: Order book bids
            asks: Order book asks
            
        Returns:
            VIIReading if enough data, None otherwise
        """
        # Update components
        self.atr_calc.add_bar(high, low, close, prev_close)
        self.volume_detector.add_volume(volume)
        self.momentum_calc.add_price(close)
        
        # Get ATR metrics
        atr = self.atr_calc.get_atr()
        atr_accel = self.atr_calc.get_atr_acceleration()
        
        if atr is None or atr_accel is None:
            return None
        
        # Get volume surge
        volume_surge = self.volume_detector.get_surge_ratio()
        
        # Get order book imbalance
        if bids and asks:
            ob_imbalance = self.ob_calc.calculate(bids, asks)
        else:
            ob_imbalance = 0.0
        
        # Get momentum
        momentum = self.momentum_calc.get_momentum()
        
        # Calculate VII value
        vii_value = self._calculate_vii(atr_accel, volume_surge, ob_imbalance, momentum)
        
        # Determine direction and strength
        direction = self._determine_direction(vii_value, atr_accel, ob_imbalance, momentum)
        strength = self._determine_strength(abs(vii_value))
        
        reading = VIIReading(
            timestamp=datetime.now(),
            vii_value=vii_value,
            direction=direction,
            strength=strength,
            atr=atr,
            atr_acceleration=atr_accel,
            volume_surge=volume_surge,
            order_book_imbalance=ob_imbalance,
            price_momentum=momentum
        )
        
        self.readings.append(reading)
        return reading
    
    def _calculate_vii(
        self,
        atr_accel: float,
        volume_surge: float,
        ob_imbalance: float,
        momentum: float
    ) -> float:
        """
        Calculate VII composite value.
        
        Returns value from -100 to +100.
        """
        # Normalize components
        
        # ATR acceleration: typically -0.5 to +0.5, scale to -100 to +100
        atr_component = max(-100, min(100, atr_accel * 200))
        
        # Volume surge: 0.5 to 3.0 typical, scale to 0 to 100
        volume_component = max(0, min(100, (volume_surge - 1) * 50))
        
        # OB imbalance: -1 to +1, scale to -100 to +100
        ob_component = ob_imbalance * 100
        
        # Momentum: typically -5% to +5%, scale to -100 to +100
        momentum_component = max(-100, min(100, momentum * 20))
        
        # Combine with direction from OB and momentum
        direction_sign = 1 if (ob_component + momentum_component) > 0 else -1
        
        # VII = weighted combination
        vii = (
            abs(atr_component) * self.weights['atr_acceleration'] +
            volume_component * self.weights['volume_surge']
        ) * direction_sign
        
        # Add directional components
        vii += ob_component * self.weights['ob_imbalance']
        vii += momentum_component * self.weights['momentum']
        
        return max(-100, min(100, vii))
    
    def _determine_direction(
        self,
        vii: float,
        atr_accel: float,
        ob_imbalance: float,
        momentum: float
    ) -> ImpulseDirection:
        """Determine impulse direction."""
        # Check for compression (decreasing volatility)
        if atr_accel < -0.1:
            return ImpulseDirection.COMPRESSION
        
        # Determine bullish vs bearish
        directional_score = ob_imbalance * 0.5 + (momentum / 5) * 0.5
        
        if vii > 30:
            if directional_score > 0.2:
                return ImpulseDirection.BULLISH_EXPLOSION
            elif directional_score < -0.2:
                return ImpulseDirection.BEARISH_EXPLOSION
            else:
                return ImpulseDirection.BULLISH_BUILDING if directional_score > 0 else ImpulseDirection.BEARISH_BUILDING
        elif vii < -30:
            if directional_score < -0.2:
                return ImpulseDirection.BEARISH_EXPLOSION
            elif directional_score > 0.2:
                return ImpulseDirection.BULLISH_EXPLOSION
            else:
                return ImpulseDirection.BEARISH_BUILDING if directional_score < 0 else ImpulseDirection.BULLISH_BUILDING
        else:
            if atr_accel > 0.05:
                return ImpulseDirection.BULLISH_BUILDING if directional_score > 0 else ImpulseDirection.BEARISH_BUILDING
            return ImpulseDirection.NEUTRAL
    
    def _determine_strength(self, abs_vii: float) -> ImpulseStrength:
        """Determine impulse strength."""
        if abs_vii >= 70:
            return ImpulseStrength.EXTREME
        elif abs_vii >= 50:
            return ImpulseStrength.STRONG
        elif abs_vii >= 30:
            return ImpulseStrength.MODERATE
        else:
            return ImpulseStrength.WEAK
    
    def detect_explosion(self, symbol: str) -> Optional[ExplosionSignal]:
        """
        Detect imminent price explosion.
        
        Returns:
            ExplosionSignal if explosion conditions met
        """
        if len(self.readings) < 5:
            return None
        
        current = self.readings[-1]
        
        # Check for explosion conditions
        triggers = []
        
        # Condition 1: High VII value
        if abs(current.vii_value) >= 50:
            triggers.append(f"High VII: {current.vii_value:.1f}")
        
        # Condition 2: Accelerating volatility
        if current.atr_acceleration > 0.1:
            triggers.append(f"Volatility accelerating: {current.atr_acceleration:.2f}")
        
        # Condition 3: Volume surge
        if current.volume_surge >= 2.0:
            triggers.append(f"Volume surge: {current.volume_surge:.1f}x")
        
        # Condition 4: Strong order book imbalance
        if abs(current.order_book_imbalance) >= 0.4:
            triggers.append(f"OB imbalance: {current.order_book_imbalance:.2f}")
        
        # Condition 5: Momentum alignment
        if abs(current.price_momentum) >= 0.5:
            triggers.append(f"Momentum: {current.price_momentum:.2f}%")
        
        # Need at least 3 conditions for explosion signal
        if len(triggers) < 3:
            return None
        
        # Calculate probability and magnitude
        probability = min(0.95, 0.5 + len(triggers) * 0.1)
        magnitude = abs(current.vii_value) / 20  # Expected move in ATR units
        
        # Time horizon based on strength
        if current.strength == ImpulseStrength.EXTREME:
            time_horizon = 15
        elif current.strength == ImpulseStrength.STRONG:
            time_horizon = 30
        else:
            time_horizon = 60
        
        # Generate analysis
        analysis = self._generate_explosion_analysis(current, triggers)
        
        return ExplosionSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=current.direction,
            probability=probability,
            expected_magnitude=magnitude,
            time_horizon_minutes=time_horizon,
            vii_reading=current,
            trigger_conditions=triggers,
            analysis=analysis
        )
    
    def _generate_explosion_analysis(
        self,
        reading: VIIReading,
        triggers: List[str]
    ) -> str:
        """Generate explosion analysis."""
        parts = []
        
        # Direction
        if 'BULLISH' in reading.direction.value:
            parts.append("BULLISH explosion imminent")
        elif 'BEARISH' in reading.direction.value:
            parts.append("BEARISH explosion imminent")
        else:
            parts.append("Directional explosion building")
        
        # Strength
        parts.append(f"Strength: {reading.strength.name}")
        
        # Key drivers
        parts.append(f"Triggers: {len(triggers)}")
        
        # ATR context
        if reading.atr_acceleration > 0:
            parts.append("Volatility expanding")
        else:
            parts.append("Volatility contracting")
        
        return " | ".join(parts)
    
    def get_current_reading(self) -> Optional[VIIReading]:
        """Get most recent reading."""
        if self.readings:
            return self.readings[-1]
        return None
    
    def get_trend(self, periods: int = 10) -> str:
        """Get VII trend over recent periods."""
        if len(self.readings) < periods:
            return "INSUFFICIENT_DATA"
        
        recent = [r.vii_value for r in list(self.readings)[-periods:]]
        
        # Calculate slope
        avg_first_half = sum(recent[:periods//2]) / (periods//2)
        avg_second_half = sum(recent[periods//2:]) / (periods - periods//2)
        
        change = avg_second_half - avg_first_half
        
        if change > 10:
            return "STRONGLY_RISING"
        elif change > 3:
            return "RISING"
        elif change < -10:
            return "STRONGLY_FALLING"
        elif change < -3:
            return "FALLING"
        else:
            return "FLAT"
    
    def get_status(self) -> Dict[str, Any]:
        """Get indicator status."""
        current = self.get_current_reading()
        
        return {
            'readings_count': len(self.readings),
            'current_vii': current.vii_value if current else None,
            'current_direction': current.direction.value if current else None,
            'current_strength': current.strength.name if current else None,
            'trend': self.get_trend(),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_vii_indicator(config: Optional[Dict] = None) -> VolatilityImpulseVector:
    """Create VolatilityImpulseVector instance."""
    return VolatilityImpulseVector(config)


# Example usage
if __name__ == "__main__":
    import random
    
    vii = create_vii_indicator()
    
    print("=" * 60)
    print("VOLATILITY IMPULSE VECTOR (VII)")
    print("=" * 60)
    
    # Simulate price data with building volatility
    base_price = 100.0
    prev_close = base_price
    
    print("\nSimulating market data with building volatility...")
    
    for i in range(30):
        # Increasing volatility over time
        volatility = 0.5 + (i / 30) * 1.5
        
        high = prev_close + random.uniform(0, volatility)
        low = prev_close - random.uniform(0, volatility)
        close = prev_close + random.uniform(-volatility/2, volatility/2)
        
        # Increasing volume
        volume = 10000 * (1 + i / 15)
        
        # Simulated order book
        bids = [(close - 0.01 * j, random.randint(100, 1000) * (1 + i/30)) for j in range(1, 11)]
        asks = [(close + 0.01 * j, random.randint(100, 800)) for j in range(1, 11)]
        
        reading = vii.update(high, low, close, volume, prev_close, bids, asks)
        
        if reading and i >= 15:
            print(f"\nBar {i}: Close={close:.2f}")
            print(f"  VII: {reading.vii_value:.1f}")
            print(f"  Direction: {reading.direction.value}")
            print(f"  Strength: {reading.strength.name}")
            print(f"  ATR Accel: {reading.atr_acceleration:.3f}")
            print(f"  Volume Surge: {reading.volume_surge:.2f}x")
            print(f"  OB Imbalance: {reading.order_book_imbalance:.2f}")
        
        prev_close = close
    
    # Check for explosion
    print("\n" + "=" * 60)
    print("EXPLOSION DETECTION")
    print("=" * 60)
    
    explosion = vii.detect_explosion("TEST")
    
    if explosion:
        print(f"\n🚨 EXPLOSION SIGNAL DETECTED!")
        print(f"Direction: {explosion.direction.value}")
        print(f"Probability: {explosion.probability:.0%}")
        print(f"Expected Magnitude: {explosion.expected_magnitude:.1f} ATR")
        print(f"Time Horizon: {explosion.time_horizon_minutes} minutes")
        print(f"\nTriggers:")
        for trigger in explosion.trigger_conditions:
            print(f"  ✓ {trigger}")
        print(f"\nAnalysis: {explosion.analysis}")
    else:
        print("\nNo explosion signal detected")
    
    # Status
    print("\n" + "=" * 60)
    print("STATUS")
    print("=" * 60)
    status = vii.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
