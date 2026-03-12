"""
Antifragile Trading Mode

Instead of just minimizing drawdown, this mode profits from volatility spikes
and market chaos. Uses pre-defined "black swan" patterns to execute short-term,
high-leverage counter-trend moves to capture panic-driven overreactions.

Features:
- Black swan pattern detection
- Flash crash harvesting
- Volatility spike trading
- Counter-trend execution
- Panic detection and exploitation
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics
import math

logger = logging.getLogger(__name__)


class ChaosLevel(Enum):
    """Market chaos levels."""
    CALM = 1
    ELEVATED = 2
    HIGH = 3
    EXTREME = 4
    BLACK_SWAN = 5


class PanicType(Enum):
    """Types of market panic."""
    FLASH_CRASH = "flash_crash"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    GAP_DOWN = "gap_down"
    GAP_UP = "gap_up"
    VOLATILITY_EXPLOSION = "volatility_explosion"
    CAPITULATION = "capitulation"


class AntifragileSignal(Enum):
    """Antifragile trading signals."""
    FADE_PANIC = "fade_panic"
    RIDE_MOMENTUM = "ride_momentum"
    VOLATILITY_HARVEST = "volatility_harvest"
    MEAN_REVERSION = "mean_reversion"
    STAY_OUT = "stay_out"


@dataclass
class ChaosEvent:
    """Detected chaos event."""
    timestamp: datetime
    event_type: PanicType
    chaos_level: ChaosLevel
    magnitude: float  # Size of the move
    velocity: float  # Speed of the move
    volume_spike: float  # Volume vs average
    spread_expansion: float  # Spread vs normal
    recovery_probability: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'chaos_level': self.chaos_level.name,
            'magnitude': self.magnitude,
            'velocity': self.velocity,
            'volume_spike': self.volume_spike,
            'spread_expansion': self.spread_expansion,
            'recovery_probability': self.recovery_probability
        }


@dataclass
class AntifragileOpportunity:
    """Trading opportunity from chaos."""
    timestamp: datetime
    symbol: str
    signal: AntifragileSignal
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    target_price: float
    stop_loss: float
    position_size_multiplier: float  # Relative to normal
    confidence: float
    expected_return: float
    max_hold_minutes: int
    chaos_event: ChaosEvent
    analysis: str
    
    @property
    def risk_reward(self) -> float:
        """Calculate risk/reward ratio."""
        try:
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.target_price - self.entry_price)
            if risk > 0:
                return reward / risk
            return 0
        except Exception as e:
            logger.error(f"Error in risk_reward: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'signal': self.signal.value,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'position_size_multiplier': self.position_size_multiplier,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'risk_reward': self.risk_reward,
            'max_hold_minutes': self.max_hold_minutes,
            'analysis': self.analysis
        }


@dataclass
class MarketState:
    """Current market state for antifragile analysis."""
    price: float
    bid: float
    ask: float
    volume: float
    atr: float
    vix: Optional[float]
    timestamp: datetime


class FlashCrashDetector:
    """
    Detects flash crash patterns.
    
    Characteristics:
    - Rapid price decline (>2% in <5 minutes)
    - Volume spike
    - Spread expansion
    - Order book imbalance
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.price_history: deque = deque(maxlen=100)
            self.volume_history: deque = deque(maxlen=100)
        
            self.crash_threshold_pct = self.config.get('crash_threshold_pct', 2.0)
            self.crash_time_window = self.config.get('crash_time_window_bars', 5)
            self.volume_spike_threshold = self.config.get('volume_spike_threshold', 3.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_bar(self, price: float, volume: float):
        """Add price bar."""
        try:
            self.price_history.append((datetime.now(), price))
            self.volume_history.append(volume)
        except Exception as e:
            logger.error(f"Error in add_bar: {e}")
            raise
    
    def detect(self) -> Optional[Dict[str, Any]]:
        """Detect flash crash."""
        try:
            if len(self.price_history) < self.crash_time_window + 1:
                return None
        
            prices = list(self.price_history)
            volumes = list(self.volume_history)
        
            current_price = prices[-1][1]
            window_start_price = prices[-self.crash_time_window - 1][1]
        
            if window_start_price == 0:
                return None
        
            # Calculate move
            move_pct = (current_price - window_start_price) / window_start_price * 100
        
            # Check for crash
            if move_pct < -self.crash_threshold_pct:
                # Volume spike
                recent_volume = sum(volumes[-self.crash_time_window:])
                avg_volume = sum(volumes[:-self.crash_time_window]) / max(1, len(volumes) - self.crash_time_window)
                volume_spike = recent_volume / avg_volume if avg_volume > 0 else 1
            
                if volume_spike >= self.volume_spike_threshold:
                    return {
                        'type': PanicType.FLASH_CRASH,
                        'magnitude': abs(move_pct),
                        'velocity': abs(move_pct) / self.crash_time_window,
                        'volume_spike': volume_spike,
                        'start_price': window_start_price,
                        'current_price': current_price
                    }
        
            return None
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise


class VolatilityExploder:
    """
    Detects volatility explosions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.atr_history: deque = deque(maxlen=50)
        
            self.explosion_threshold = self.config.get('explosion_threshold', 2.5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_atr(self, atr: float):
        """Add ATR reading."""
        try:
            self.atr_history.append(atr)
        except Exception as e:
            logger.error(f"Error in add_atr: {e}")
            raise
    
    def detect(self) -> Optional[Dict[str, Any]]:
        """Detect volatility explosion."""
        try:
            if len(self.atr_history) < 20:
                return None
        
            atrs = list(self.atr_history)
            current_atr = atrs[-1]
            avg_atr = statistics.mean(atrs[:-5])
        
            if avg_atr == 0:
                return None
        
            ratio = current_atr / avg_atr
        
            if ratio >= self.explosion_threshold:
                return {
                    'type': PanicType.VOLATILITY_EXPLOSION,
                    'magnitude': ratio,
                    'current_atr': current_atr,
                    'avg_atr': avg_atr
                }
        
            return None
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise


class CapitulationDetector:
    """
    Detects market capitulation.
    
    Characteristics:
    - Extended decline
    - Extreme volume
    - Exhaustion patterns
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.price_history: deque = deque(maxlen=100)
            self.volume_history: deque = deque(maxlen=100)
        
            self.decline_threshold = self.config.get('decline_threshold_pct', 5.0)
            self.decline_bars = self.config.get('decline_bars', 20)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_bar(self, price: float, volume: float):
        """Add price bar."""
        try:
            self.price_history.append(price)
            self.volume_history.append(volume)
        except Exception as e:
            logger.error(f"Error in add_bar: {e}")
            raise
    
    def detect(self) -> Optional[Dict[str, Any]]:
        """Detect capitulation."""
        try:
            if len(self.price_history) < self.decline_bars + 1:
                return None
        
            prices = list(self.price_history)
            volumes = list(self.volume_history)
        
            current_price = prices[-1]
            start_price = prices[-self.decline_bars - 1]
        
            if start_price == 0:
                return None
        
            decline_pct = (current_price - start_price) / start_price * 100
        
            if decline_pct < -self.decline_threshold:
                # Check for volume climax
                recent_volume = sum(volumes[-5:])
                avg_volume = sum(volumes[:-5]) / max(1, len(volumes) - 5)
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
                # Check for exhaustion (slowing decline)
                recent_decline = (prices[-1] - prices[-5]) / prices[-5] * 100 if prices[-5] > 0 else 0
                earlier_decline = (prices[-5] - prices[-10]) / prices[-10] * 100 if len(prices) > 10 and prices[-10] > 0 else 0
            
                exhaustion = abs(recent_decline) < abs(earlier_decline) * 0.5
            
                if volume_ratio > 2.0 and exhaustion:
                    return {
                        'type': PanicType.CAPITULATION,
                        'magnitude': abs(decline_pct),
                        'volume_ratio': volume_ratio,
                        'exhaustion': exhaustion
                    }
        
            return None
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise


class RecoveryPredictor:
    """
    Predicts recovery probability after chaos events.
    """
    
    def __init__(self):
        # Historical recovery rates by event type
        try:
            self.recovery_rates = {
                PanicType.FLASH_CRASH: 0.85,  # Flash crashes often recover quickly
                PanicType.LIQUIDITY_CRISIS: 0.60,
                PanicType.GAP_DOWN: 0.70,
                PanicType.GAP_UP: 0.65,
                PanicType.VOLATILITY_EXPLOSION: 0.55,
                PanicType.CAPITULATION: 0.75,  # Capitulation often marks bottoms
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def predict(
        self,
        event_type: PanicType,
        magnitude: float,
        volume_spike: float
    ) -> float:
        """
        Predict recovery probability.
        
        Returns:
            Probability of recovery (0-1)
        """
        try:
            base_rate = self.recovery_rates.get(event_type, 0.5)
        
            # Adjust for magnitude (larger moves = higher recovery probability for mean reversion)
            if magnitude > 5:
                magnitude_adj = 0.1
            elif magnitude > 3:
                magnitude_adj = 0.05
            else:
                magnitude_adj = 0
        
            # Adjust for volume (higher volume = more conviction, could go either way)
            if volume_spike > 5:
                volume_adj = 0.05  # Extreme volume often marks turning points
            else:
                volume_adj = 0
        
            return min(0.95, base_rate + magnitude_adj + volume_adj)
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise


class AntifragileMode:
    """
    Main antifragile trading system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Detectors
            self.flash_crash_detector = FlashCrashDetector(config)
            self.volatility_detector = VolatilityExploder(config)
            self.capitulation_detector = CapitulationDetector(config)
            self.recovery_predictor = RecoveryPredictor()
        
            # State
            self.current_chaos_level = ChaosLevel.CALM
            self.active_events: List[ChaosEvent] = []
            self.opportunities: deque = deque(maxlen=100)
        
            # Risk parameters
            self.max_position_multiplier = self.config.get('max_position_multiplier', 2.0)
            self.min_recovery_prob = self.config.get('min_recovery_prob', 0.6)
            self.max_hold_minutes = self.config.get('max_hold_minutes', 30)
        
            logger.info("AntifragileMode initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, state: MarketState):
        """
        Update with new market state.
        
        Args:
            state: Current market state
        """
        # Update detectors
        try:
            self.flash_crash_detector.add_bar(state.price, state.volume)
            self.volatility_detector.add_atr(state.atr)
            self.capitulation_detector.add_bar(state.price, state.volume)
        
            # Detect events
            self._detect_events(state)
        
            # Update chaos level
            self._update_chaos_level(state)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _detect_events(self, state: MarketState):
        """Detect chaos events."""
        # Flash crash
        try:
            flash_crash = self.flash_crash_detector.detect()
            if flash_crash:
                self._create_event(flash_crash, state)
        
            # Volatility explosion
            vol_explosion = self.volatility_detector.detect()
            if vol_explosion:
                self._create_event(vol_explosion, state)
        
            # Capitulation
            capitulation = self.capitulation_detector.detect()
            if capitulation:
                self._create_event(capitulation, state)
        except Exception as e:
            logger.error(f"Error in _detect_events: {e}")
            raise
    
    def _create_event(self, detection: Dict, state: MarketState):
        """Create chaos event from detection."""
        try:
            event_type = detection['type']
            magnitude = detection.get('magnitude', 0)
            volume_spike = detection.get('volume_spike', 1)
        
            # Calculate spread expansion
            spread = state.ask - state.bid
            normal_spread = state.atr * 0.1  # Assume normal spread is 10% of ATR
            spread_expansion = spread / normal_spread if normal_spread > 0 else 1
        
            # Predict recovery
            recovery_prob = self.recovery_predictor.predict(event_type, magnitude, volume_spike)
        
            # Determine chaos level
            if magnitude > 10:
                chaos_level = ChaosLevel.BLACK_SWAN
            elif magnitude > 5:
                chaos_level = ChaosLevel.EXTREME
            elif magnitude > 3:
                chaos_level = ChaosLevel.HIGH
            elif magnitude > 1.5:
                chaos_level = ChaosLevel.ELEVATED
            else:
                chaos_level = ChaosLevel.CALM
        
            event = ChaosEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                chaos_level=chaos_level,
                magnitude=magnitude,
                velocity=detection.get('velocity', magnitude),
                volume_spike=volume_spike,
                spread_expansion=spread_expansion,
                recovery_probability=recovery_prob
            )
        
            self.active_events.append(event)
        
            # Keep only recent events
            cutoff = datetime.now() - timedelta(minutes=30)
            self.active_events = [e for e in self.active_events if e.timestamp >= cutoff]
        except Exception as e:
            logger.error(f"Error in _create_event: {e}")
            raise
    
    def _update_chaos_level(self, state: MarketState):
        """Update overall chaos level."""
        try:
            if not self.active_events:
                self.current_chaos_level = ChaosLevel.CALM
                return
        
            # Use highest chaos level from active events
            max_level = max(e.chaos_level.value for e in self.active_events)
            self.current_chaos_level = ChaosLevel(max_level)
        except Exception as e:
            logger.error(f"Error in _update_chaos_level: {e}")
            raise
    
    def generate_opportunity(
        self,
        symbol: str,
        state: MarketState
    ) -> Optional[AntifragileOpportunity]:
        """
        Generate trading opportunity from chaos.
        
        Args:
            symbol: Trading symbol
            state: Current market state
            
        Returns:
            AntifragileOpportunity if conditions met
        """
        try:
            if not self.active_events:
                return None
        
            # Get most significant recent event
            recent_events = [
                e for e in self.active_events
                if (datetime.now() - e.timestamp).total_seconds() < 300  # Last 5 minutes
            ]
        
            if not recent_events:
                return None
        
            event = max(recent_events, key=lambda e: e.magnitude)
        
            # Check recovery probability
            if event.recovery_probability < self.min_recovery_prob:
                return None
        
            # Determine signal and direction
            signal, direction = self._determine_signal(event, state)
        
            if signal == AntifragileSignal.STAY_OUT:
                return None
        
            # Calculate entry, target, stop
            entry, target, stop = self._calculate_levels(event, state, direction)
        
            # Position size multiplier based on confidence
            confidence = event.recovery_probability * (1 - event.spread_expansion / 10)
            position_multiplier = min(
                self.max_position_multiplier,
                1.0 + confidence * (self.max_position_multiplier - 1)
            )
        
            # Expected return
            if direction == 'LONG':
                expected_return = (target - entry) / entry * 100
            else:
                expected_return = (entry - target) / entry * 100
        
            # Generate analysis
            analysis = self._generate_analysis(event, signal, direction, confidence)
        
            opportunity = AntifragileOpportunity(
                timestamp=datetime.now(),
                symbol=symbol,
                signal=signal,
                direction=direction,
                entry_price=entry,
                target_price=target,
                stop_loss=stop,
                position_size_multiplier=position_multiplier,
                confidence=confidence,
                expected_return=expected_return,
                max_hold_minutes=self.max_hold_minutes,
                chaos_event=event,
                analysis=analysis
            )
        
            self.opportunities.append(opportunity)
            return opportunity
        except Exception as e:
            logger.error(f"Error in generate_opportunity: {e}")
            raise
    
    def _determine_signal(
        self,
        event: ChaosEvent,
        state: MarketState
    ) -> Tuple[AntifragileSignal, str]:
        """Determine signal type and direction."""
        # Flash crash -> Fade panic (buy the dip)
        try:
            if event.event_type == PanicType.FLASH_CRASH:
                if event.recovery_probability > 0.7:
                    return AntifragileSignal.FADE_PANIC, 'LONG'
        
            # Capitulation -> Mean reversion
            if event.event_type == PanicType.CAPITULATION:
                return AntifragileSignal.MEAN_REVERSION, 'LONG'
        
            # Volatility explosion -> Harvest volatility
            if event.event_type == PanicType.VOLATILITY_EXPLOSION:
                if event.magnitude > 3:
                    return AntifragileSignal.VOLATILITY_HARVEST, 'LONG'  # Straddle-like
        
            # Gap events
            if event.event_type == PanicType.GAP_DOWN:
                if event.recovery_probability > 0.65:
                    return AntifragileSignal.FADE_PANIC, 'LONG'
        
            if event.event_type == PanicType.GAP_UP:
                if event.recovery_probability > 0.65:
                    return AntifragileSignal.FADE_PANIC, 'SHORT'
        
            return AntifragileSignal.STAY_OUT, 'NONE'
        except Exception as e:
            logger.error(f"Error in _determine_signal: {e}")
            raise
    
    def _calculate_levels(
        self,
        event: ChaosEvent,
        state: MarketState,
        direction: str
    ) -> Tuple[float, float, float]:
        """Calculate entry, target, and stop levels."""
        try:
            atr = state.atr
            price = state.price
        
            if direction == 'LONG':
                # Enter at current price (or slightly below)
                entry = price
            
                # Target: recover portion of the move
                target = price + (event.magnitude / 100 * price * 0.5)  # 50% recovery
            
                # Stop: below recent low with buffer
                stop = price - atr * 1.5
            else:
                entry = price
                target = price - (event.magnitude / 100 * price * 0.5)
                stop = price + atr * 1.5
        
            return entry, target, stop
        except Exception as e:
            logger.error(f"Error in _calculate_levels: {e}")
            raise
    
    def _generate_analysis(
        self,
        event: ChaosEvent,
        signal: AntifragileSignal,
        direction: str,
        confidence: float
    ) -> str:
        """Generate analysis text."""
        try:
            parts = []
        
            parts.append(f"{event.event_type.value} detected")
            parts.append(f"Chaos level: {event.chaos_level.name}")
            parts.append(f"Magnitude: {event.magnitude:.1f}%")
            parts.append(f"Signal: {signal.value} {direction}")
            parts.append(f"Recovery prob: {event.recovery_probability:.0%}")
            parts.append(f"Confidence: {confidence:.0%}")
        
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_analysis: {e}")
            raise
    
    def get_chaos_status(self) -> Dict[str, Any]:
        """Get current chaos status."""
        return {
            'chaos_level': self.current_chaos_level.name,
            'active_events': len(self.active_events),
            'recent_opportunities': len(self.opportunities),
            'events': [e.to_dict() for e in self.active_events[-5:]],
            'timestamp': datetime.now().isoformat()
        }
    
    def is_chaos_mode_active(self) -> bool:
        """Check if chaos mode is active."""
        return self.current_chaos_level.value >= ChaosLevel.HIGH.value


# Factory function
def create_antifragile_mode(config: Optional[Dict] = None) -> AntifragileMode:
    """Create AntifragileMode instance."""
    return AntifragileMode(config)


# Example usage
if __name__ == "__main__":
    import random
    
    antifragile = create_antifragile_mode()
    
    print("=" * 60)
    print("ANTIFRAGILE TRADING MODE")
    print("=" * 60)
    
    # Simulate a flash crash scenario
    print("\nSimulating flash crash scenario...")
    
    base_price = 100.0
    
    # Normal market
    for i in range(20):
        state = MarketState(
            price=base_price + random.uniform(-0.5, 0.5),
            bid=base_price - 0.01,
            ask=base_price + 0.01,
            volume=10000 + random.randint(-2000, 2000),
            atr=0.5,
            vix=15.0,
            timestamp=datetime.now()
        )
        antifragile.update(state)
    
    print(f"Normal market - Chaos level: {antifragile.current_chaos_level.name}")
    
    # Flash crash
    print("\n--- FLASH CRASH BEGINS ---")
    
    crash_price = base_price
    for i in range(5):
        crash_price *= 0.99  # 1% drop per bar
        
        state = MarketState(
            price=crash_price,
            bid=crash_price - 0.05,  # Wider spread
            ask=crash_price + 0.05,
            volume=50000 + random.randint(0, 30000),  # Volume spike
            atr=1.5,  # Higher ATR
            vix=35.0,
            timestamp=datetime.now()
        )
        antifragile.update(state)
        
        print(f"Bar {i+1}: Price={crash_price:.2f}, Chaos={antifragile.current_chaos_level.name}")
    
    # Check for opportunity
    print("\n" + "=" * 60)
    print("OPPORTUNITY CHECK")
    print("=" * 60)
    
    opportunity = antifragile.generate_opportunity("TEST", state)
    
    if opportunity:
        print(f"\n🎯 ANTIFRAGILE OPPORTUNITY DETECTED!")
        print(f"Signal: {opportunity.signal.value}")
        print(f"Direction: {opportunity.direction}")
        print(f"Entry: {opportunity.entry_price:.2f}")
        print(f"Target: {opportunity.target_price:.2f}")
        print(f"Stop: {opportunity.stop_loss:.2f}")
        print(f"Risk/Reward: {opportunity.risk_reward:.2f}")
        print(f"Position Multiplier: {opportunity.position_size_multiplier:.2f}x")
        print(f"Confidence: {opportunity.confidence:.0%}")
        print(f"Expected Return: {opportunity.expected_return:.2f}%")
        print(f"Max Hold: {opportunity.max_hold_minutes} minutes")
        print(f"\nAnalysis: {opportunity.analysis}")
    else:
        print("\nNo opportunity generated")
    
    # Chaos status
    print("\n" + "=" * 60)
    print("CHAOS STATUS")
    print("=" * 60)
    
    status = antifragile.get_chaos_status()
    print(f"\nChaos Level: {status['chaos_level']}")
    print(f"Active Events: {status['active_events']}")
    
    if status['events']:
        print("\nRecent Events:")
        for event in status['events']:
            print(f"  {event['event_type']}: {event['magnitude']:.1f}% ({event['chaos_level']})")
