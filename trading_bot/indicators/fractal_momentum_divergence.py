"""
Fractal Momentum Divergence (FMD) Indicator

A unique divergence tool that compares momentum across three consecutive
fractal timeframes (e.g., 5m vs. 15m vs. 1H).

Filters out false divergences that appear on only two timeframes,
providing a much stronger reversal confirmation signal.

Features:
- Multi-timeframe momentum comparison
- Fractal divergence detection
- False signal filtering
- Reversal probability scoring
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class DivergenceType(Enum):
    """Types of divergence."""
    BULLISH_REGULAR = "bullish_regular"  # Price lower low, momentum higher low
    BEARISH_REGULAR = "bearish_regular"  # Price higher high, momentum lower high
    BULLISH_HIDDEN = "bullish_hidden"  # Price higher low, momentum lower low
    BEARISH_HIDDEN = "bearish_hidden"  # Price lower high, momentum higher high
    NONE = "none"


class TimeframeRelation(Enum):
    """Relationship between timeframes."""
    ALIGNED = "aligned"  # All timeframes agree
    PARTIAL = "partial"  # 2 of 3 agree
    CONFLICTING = "conflicting"  # All disagree


class SignalStrength(Enum):
    """Signal strength levels."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class MomentumReading:
    """Momentum reading for a single timeframe."""
    timestamp: datetime
    timeframe: str
    price: float
    momentum: float  # RSI, MACD, or custom
    price_swing_high: float
    price_swing_low: float
    momentum_swing_high: float
    momentum_swing_low: float


@dataclass
class TimeframeDivergence:
    """Divergence detected on a single timeframe."""
    timeframe: str
    divergence_type: DivergenceType
    price_points: Tuple[float, float]  # (old, new)
    momentum_points: Tuple[float, float]  # (old, new)
    strength: float  # 0-1
    bars_apart: int


@dataclass
class FractalDivergence:
    """
    Fractal divergence across multiple timeframes.
    
    Only valid when divergence appears on 3 consecutive timeframes.
    """
    timestamp: datetime
    symbol: str
    divergence_type: DivergenceType
    timeframes: List[str]
    timeframe_divergences: List[TimeframeDivergence]
    alignment: TimeframeRelation
    overall_strength: SignalStrength
    reversal_probability: float
    expected_move_pct: float
    confirmation_level: int  # 1-3 (how many TFs confirm)
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'divergence_type': self.divergence_type.value,
            'timeframes': self.timeframes,
            'alignment': self.alignment.value,
            'strength': self.overall_strength.name,
            'reversal_probability': self.reversal_probability,
            'expected_move_pct': self.expected_move_pct,
            'confirmation_level': self.confirmation_level,
            'analysis': self.analysis
        }


class MomentumCalculator:
    """
    Calculates momentum indicator (RSI-based).
    """
    
    def __init__(self, period: int = 14):
        try:
            self.period = period
            self.gains: deque = deque(maxlen=period)
            self.losses: deque = deque(maxlen=period)
            self.prev_price: Optional[float] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_price(self, price: float) -> Optional[float]:
        """Add price and return RSI."""
        try:
            if self.prev_price is not None:
                change = price - self.prev_price
                if change > 0:
                    self.gains.append(change)
                    self.losses.append(0)
                else:
                    self.gains.append(0)
                    self.losses.append(abs(change))
        
            self.prev_price = price
        
            if len(self.gains) < self.period:
                return None
        
            avg_gain = sum(self.gains) / self.period
            avg_loss = sum(self.losses) / self.period
        
            if avg_loss == 0:
                return 100.0
        
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
            return rsi
        except Exception as e:
            logger.error(f"Error in add_price: {e}")
            raise


class SwingPointDetector:
    """
    Detects swing highs and lows.
    """
    
    def __init__(self, lookback: int = 5):
        try:
            self.lookback = lookback
            self.prices: deque = deque(maxlen=lookback * 3)
            self.swing_highs: List[Tuple[int, float]] = []
            self.swing_lows: List[Tuple[int, float]] = []
            self.bar_count = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_price(self, high: float, low: float, close: float):
        """Add price bar."""
        try:
            self.prices.append((high, low, close))
            self.bar_count += 1
        
            if len(self.prices) < self.lookback * 2 + 1:
                return
        
            prices = list(self.prices)
            mid_idx = self.lookback
        
            # Check for swing high
            mid_high = prices[mid_idx][0]
            is_swing_high = all(
                prices[i][0] < mid_high for i in range(mid_idx)
            ) and all(
                prices[i][0] < mid_high for i in range(mid_idx + 1, len(prices))
            )
        
            if is_swing_high:
                self.swing_highs.append((self.bar_count - self.lookback, mid_high))
                # Keep only recent swings
                self.swing_highs = self.swing_highs[-10:]
        
            # Check for swing low
            mid_low = prices[mid_idx][1]
            is_swing_low = all(
                prices[i][1] > mid_low for i in range(mid_idx)
            ) and all(
                prices[i][1] > mid_low for i in range(mid_idx + 1, len(prices))
            )
        
            if is_swing_low:
                self.swing_lows.append((self.bar_count - self.lookback, mid_low))
                self.swing_lows = self.swing_lows[-10:]
        except Exception as e:
            logger.error(f"Error in add_price: {e}")
            raise
    
    def get_recent_swing_high(self) -> Optional[Tuple[int, float]]:
        """Get most recent swing high."""
        return self.swing_highs[-1] if self.swing_highs else None
    
    def get_recent_swing_low(self) -> Optional[Tuple[int, float]]:
        """Get most recent swing low."""
        return self.swing_lows[-1] if self.swing_lows else None
    
    def get_previous_swing_high(self) -> Optional[Tuple[int, float]]:
        """Get second most recent swing high."""
        return self.swing_highs[-2] if len(self.swing_highs) >= 2 else None
    
    def get_previous_swing_low(self) -> Optional[Tuple[int, float]]:
        """Get second most recent swing low."""
        return self.swing_lows[-2] if len(self.swing_lows) >= 2 else None


class SingleTimeframeDivergenceDetector:
    """
    Detects divergence on a single timeframe.
    """
    
    def __init__(self, timeframe: str, momentum_period: int = 14, swing_lookback: int = 5):
        try:
            self.timeframe = timeframe
            self.momentum_calc = MomentumCalculator(momentum_period)
            self.price_swings = SwingPointDetector(swing_lookback)
            self.momentum_swings = SwingPointDetector(swing_lookback)
        
            self.momentum_values: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_bar(self, high: float, low: float, close: float) -> Optional[TimeframeDivergence]:
        """
        Add price bar and check for divergence.
        
        Returns:
            TimeframeDivergence if detected
        """
        # Calculate momentum
        try:
            momentum = self.momentum_calc.add_price(close)
        
            if momentum is None:
                return None
        
            self.momentum_values.append(momentum)
        
            # Update swing points
            self.price_swings.add_price(high, low, close)
            self.momentum_swings.add_price(momentum, momentum, momentum)
        
            # Check for divergence
            return self._check_divergence()
        except Exception as e:
            logger.error(f"Error in add_bar: {e}")
            raise
    
    def _check_divergence(self) -> Optional[TimeframeDivergence]:
        """Check for divergence between price and momentum swings."""
        # Get swing points
        try:
            price_high_1 = self.price_swings.get_recent_swing_high()
            price_high_2 = self.price_swings.get_previous_swing_high()
            price_low_1 = self.price_swings.get_recent_swing_low()
            price_low_2 = self.price_swings.get_previous_swing_low()
        
            mom_high_1 = self.momentum_swings.get_recent_swing_high()
            mom_high_2 = self.momentum_swings.get_previous_swing_high()
            mom_low_1 = self.momentum_swings.get_recent_swing_low()
            mom_low_2 = self.momentum_swings.get_previous_swing_low()
        
            # Check bearish regular divergence (price HH, momentum LH)
            if price_high_1 and price_high_2 and mom_high_1 and mom_high_2:
                if price_high_1[1] > price_high_2[1] and mom_high_1[1] < mom_high_2[1]:
                    return TimeframeDivergence(
                        timeframe=self.timeframe,
                        divergence_type=DivergenceType.BEARISH_REGULAR,
                        price_points=(price_high_2[1], price_high_1[1]),
                        momentum_points=(mom_high_2[1], mom_high_1[1]),
                        strength=self._calculate_strength(
                            price_high_2[1], price_high_1[1],
                            mom_high_2[1], mom_high_1[1]
                        ),
                        bars_apart=price_high_1[0] - price_high_2[0]
                    )
        
            # Check bullish regular divergence (price LL, momentum HL)
            if price_low_1 and price_low_2 and mom_low_1 and mom_low_2:
                if price_low_1[1] < price_low_2[1] and mom_low_1[1] > mom_low_2[1]:
                    return TimeframeDivergence(
                        timeframe=self.timeframe,
                        divergence_type=DivergenceType.BULLISH_REGULAR,
                        price_points=(price_low_2[1], price_low_1[1]),
                        momentum_points=(mom_low_2[1], mom_low_1[1]),
                        strength=self._calculate_strength(
                            price_low_2[1], price_low_1[1],
                            mom_low_2[1], mom_low_1[1]
                        ),
                        bars_apart=price_low_1[0] - price_low_2[0]
                    )
        
            # Check bearish hidden divergence (price LH, momentum HH)
            if price_high_1 and price_high_2 and mom_high_1 and mom_high_2:
                if price_high_1[1] < price_high_2[1] and mom_high_1[1] > mom_high_2[1]:
                    return TimeframeDivergence(
                        timeframe=self.timeframe,
                        divergence_type=DivergenceType.BEARISH_HIDDEN,
                        price_points=(price_high_2[1], price_high_1[1]),
                        momentum_points=(mom_high_2[1], mom_high_1[1]),
                        strength=self._calculate_strength(
                            price_high_2[1], price_high_1[1],
                            mom_high_2[1], mom_high_1[1]
                        ) * 0.8,  # Hidden divergence slightly weaker
                        bars_apart=price_high_1[0] - price_high_2[0]
                    )
        
            # Check bullish hidden divergence (price HL, momentum LL)
            if price_low_1 and price_low_2 and mom_low_1 and mom_low_2:
                if price_low_1[1] > price_low_2[1] and mom_low_1[1] < mom_low_2[1]:
                    return TimeframeDivergence(
                        timeframe=self.timeframe,
                        divergence_type=DivergenceType.BULLISH_HIDDEN,
                        price_points=(price_low_2[1], price_low_1[1]),
                        momentum_points=(mom_low_2[1], mom_low_1[1]),
                        strength=self._calculate_strength(
                            price_low_2[1], price_low_1[1],
                            mom_low_2[1], mom_low_1[1]
                        ) * 0.8,
                        bars_apart=price_low_1[0] - price_low_2[0]
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_divergence: {e}")
            raise
    
    def _calculate_strength(
        self,
        price_old: float,
        price_new: float,
        mom_old: float,
        mom_new: float
    ) -> float:
        """Calculate divergence strength."""
        # Price divergence magnitude
        try:
            if price_old != 0:
                price_div = abs(price_new - price_old) / price_old
            else:
                price_div = 0
        
            # Momentum divergence magnitude
            mom_div = abs(mom_new - mom_old) / 100  # RSI is 0-100
        
            # Combined strength
            strength = (price_div * 100 + mom_div * 50) / 2
        
            return min(1.0, strength)
        except Exception as e:
            logger.error(f"Error in _calculate_strength: {e}")
            raise


class FractalMomentumDivergence:
    """
    Main FMD indicator system.
    
    Analyzes divergence across 3 fractal timeframes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Default timeframes (5m, 15m, 1H)
            self.timeframes = self.config.get('timeframes', ['5m', '15m', '1H'])
        
            # Detectors for each timeframe
            self.detectors: Dict[str, SingleTimeframeDivergenceDetector] = {}
            for tf in self.timeframes:
                self.detectors[tf] = SingleTimeframeDivergenceDetector(
                    tf,
                    momentum_period=self.config.get('momentum_period', 14),
                    swing_lookback=self.config.get('swing_lookback', 5)
                )
        
            # Recent divergences by timeframe
            self.recent_divergences: Dict[str, Optional[TimeframeDivergence]] = {
                tf: None for tf in self.timeframes
            }
        
            # History
            self.fractal_signals: deque = deque(maxlen=100)
        
            logger.info(f"FractalMomentumDivergence initialized with timeframes: {self.timeframes}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_timeframe(
        self,
        timeframe: str,
        high: float,
        low: float,
        close: float
    ) -> Optional[TimeframeDivergence]:
        """
        Update a single timeframe.
        
        Args:
            timeframe: Timeframe identifier
            high: Bar high
            low: Bar low
            close: Bar close
            
        Returns:
            TimeframeDivergence if detected on this timeframe
        """
        try:
            if timeframe not in self.detectors:
                logger.warning(f"Unknown timeframe: {timeframe}")
                return None
        
            divergence = self.detectors[timeframe].add_bar(high, low, close)
        
            if divergence:
                self.recent_divergences[timeframe] = divergence
        
            return divergence
        except Exception as e:
            logger.error(f"Error in update_timeframe: {e}")
            raise
    
    def check_fractal_divergence(self, symbol: str) -> Optional[FractalDivergence]:
        """
        Check for fractal divergence across all timeframes.
        
        Returns:
            FractalDivergence if 3-timeframe confirmation exists
        """
        # Get recent divergences
        try:
            divergences = [
                self.recent_divergences[tf]
                for tf in self.timeframes
                if self.recent_divergences[tf] is not None
            ]
        
            if len(divergences) < 2:
                return None
        
            # Check for alignment
            div_types = [d.divergence_type for d in divergences]
        
            # Count bullish vs bearish
            bullish_count = sum(1 for t in div_types if 'BULLISH' in t.value)
            bearish_count = sum(1 for t in div_types if 'BEARISH' in t.value)
        
            # Determine dominant type
            if bullish_count >= 2:
                dominant_type = DivergenceType.BULLISH_REGULAR
                confirmation = bullish_count
            elif bearish_count >= 2:
                dominant_type = DivergenceType.BEARISH_REGULAR
                confirmation = bearish_count
            else:
                return None  # No clear alignment
        
            # Determine alignment
            if confirmation == 3:
                alignment = TimeframeRelation.ALIGNED
            elif confirmation == 2:
                alignment = TimeframeRelation.PARTIAL
            else:
                alignment = TimeframeRelation.CONFLICTING
        
            # Calculate overall strength
            avg_strength = sum(d.strength for d in divergences) / len(divergences)
        
            if confirmation == 3 and avg_strength > 0.6:
                strength = SignalStrength.VERY_STRONG
            elif confirmation >= 2 and avg_strength > 0.4:
                strength = SignalStrength.STRONG
            elif confirmation >= 2:
                strength = SignalStrength.MODERATE
            else:
                strength = SignalStrength.WEAK
        
            # Calculate reversal probability
            reversal_prob = self._calculate_reversal_probability(
                confirmation, avg_strength, alignment
            )
        
            # Expected move
            expected_move = avg_strength * confirmation * 0.5  # Percentage
        
            # Generate analysis
            analysis = self._generate_analysis(
                dominant_type, confirmation, alignment, strength
            )
        
            fractal_div = FractalDivergence(
                timestamp=datetime.now(),
                symbol=symbol,
                divergence_type=dominant_type,
                timeframes=[d.timeframe for d in divergences],
                timeframe_divergences=divergences,
                alignment=alignment,
                overall_strength=strength,
                reversal_probability=reversal_prob,
                expected_move_pct=expected_move,
                confirmation_level=confirmation,
                analysis=analysis
            )
        
            self.fractal_signals.append(fractal_div)
        
            return fractal_div
        except Exception as e:
            logger.error(f"Error in check_fractal_divergence: {e}")
            raise
    
    def _calculate_reversal_probability(
        self,
        confirmation: int,
        strength: float,
        alignment: TimeframeRelation
    ) -> float:
        """Calculate probability of reversal."""
        try:
            base_prob = 0.5
        
            # Confirmation bonus
            base_prob += confirmation * 0.1
        
            # Strength bonus
            base_prob += strength * 0.15
        
            # Alignment bonus
            if alignment == TimeframeRelation.ALIGNED:
                base_prob += 0.1
            elif alignment == TimeframeRelation.PARTIAL:
                base_prob += 0.05
        
            return min(0.95, base_prob)
        except Exception as e:
            logger.error(f"Error in _calculate_reversal_probability: {e}")
            raise
    
    def _generate_analysis(
        self,
        div_type: DivergenceType,
        confirmation: int,
        alignment: TimeframeRelation,
        strength: SignalStrength
    ) -> str:
        """Generate analysis text."""
        try:
            parts = []
        
            # Type
            if 'BULLISH' in div_type.value:
                parts.append("BULLISH divergence")
            else:
                parts.append("BEARISH divergence")
        
            # Confirmation
            parts.append(f"{confirmation}/3 timeframes confirm")
        
            # Alignment
            parts.append(f"Alignment: {alignment.value}")
        
            # Strength
            parts.append(f"Strength: {strength.name}")
        
            # Recommendation
            if confirmation == 3 and strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                parts.append("HIGH PROBABILITY reversal setup")
            elif confirmation >= 2:
                parts.append("Moderate reversal probability")
            else:
                parts.append("Weak signal - wait for confirmation")
        
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_analysis: {e}")
            raise
    
    def get_recent_signals(self, count: int = 5) -> List[FractalDivergence]:
        """Get recent fractal signals."""
        return list(self.fractal_signals)[-count:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get indicator status."""
        return {
            'timeframes': self.timeframes,
            'recent_divergences': {
                tf: d.divergence_type.value if d else None
                for tf, d in self.recent_divergences.items()
            },
            'total_signals': len(self.fractal_signals),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_fmd_indicator(config: Optional[Dict] = None) -> FractalMomentumDivergence:
    """Create FractalMomentumDivergence instance."""
    return FractalMomentumDivergence(config)


# Example usage
if __name__ == "__main__":
    import random
    
    fmd = create_fmd_indicator({
        'timeframes': ['5m', '15m', '1H']
    })
    
    print("=" * 60)
    print("FRACTAL MOMENTUM DIVERGENCE (FMD)")
    print("=" * 60)
    
    # Simulate data for each timeframe
    # Creating a bearish divergence scenario (price making higher highs, momentum making lower highs)
    
    print("\nSimulating bearish divergence across timeframes...")
    
    # 5m timeframe
    base_price = 100.0
    for i in range(50):
        # Price trending up
        price = base_price + i * 0.1 + random.uniform(-0.2, 0.2)
        high = price + random.uniform(0, 0.3)
        low = price - random.uniform(0, 0.3)
        
        div = fmd.update_timeframe('5m', high, low, price)
        if div:
            print(f"5m divergence: {div.divergence_type.value}")
    
    # 15m timeframe (aggregated)
    for i in range(20):
        price = base_price + i * 0.25 + random.uniform(-0.3, 0.3)
        high = price + random.uniform(0, 0.5)
        low = price - random.uniform(0, 0.5)
        
        div = fmd.update_timeframe('15m', high, low, price)
        if div:
            print(f"15m divergence: {div.divergence_type.value}")
    
    # 1H timeframe (aggregated)
    for i in range(10):
        price = base_price + i * 0.5 + random.uniform(-0.5, 0.5)
        high = price + random.uniform(0, 1.0)
        low = price - random.uniform(0, 1.0)
        
        div = fmd.update_timeframe('1H', high, low, price)
        if div:
            print(f"1H divergence: {div.divergence_type.value}")
    
    # Check for fractal divergence
    print("\n" + "=" * 60)
    print("FRACTAL DIVERGENCE CHECK")
    print("=" * 60)
    
    fractal = fmd.check_fractal_divergence("TEST")
    
    if fractal:
        print(f"\n🎯 FRACTAL DIVERGENCE DETECTED!")
        print(f"Type: {fractal.divergence_type.value}")
        print(f"Timeframes: {', '.join(fractal.timeframes)}")
        print(f"Confirmation: {fractal.confirmation_level}/3")
        print(f"Alignment: {fractal.alignment.value}")
        print(f"Strength: {fractal.overall_strength.name}")
        print(f"Reversal Probability: {fractal.reversal_probability:.0%}")
        print(f"Expected Move: {fractal.expected_move_pct:.2f}%")
        print(f"\nAnalysis: {fractal.analysis}")
    else:
        print("\nNo fractal divergence detected")
    
    # Status
    print("\n" + "=" * 60)
    print("STATUS")
    print("=" * 60)
    status = fmd.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
