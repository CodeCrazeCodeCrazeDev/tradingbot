"""
Advanced Circuit Breaker System

Implements sophisticated circuit breakers for flash moves, abnormal volatility,
and various market stress conditions with graduated response levels.

Features:
- Flash crash detection and response
- Volatility spike circuit breakers
- Liquidity crisis detection
- Graduated response levels (warn, throttle, halt)
- Auto-recovery with cooldown periods

Based on: HI-RSK-008 Circuit breakers for flash moves and abnormal volatility
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class BreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    HALF_OPEN = "half_open"  # Testing if safe to resume
    OPEN = "open"  # Tripped, blocking operations


class ResponseLevel(Enum):
    """Response severity levels."""
    NORMAL = 0
    WARN = 1
    THROTTLE = 2
    HALT = 3
    EMERGENCY = 4


class TriggerType(Enum):
    """Types of circuit breaker triggers."""
    FLASH_MOVE = "flash_move"
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    SPREAD_BLOWOUT = "spread_blowout"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    DRAWDOWN = "drawdown"
    DATA_STALE = "data_stale"
    EXECUTION_FAILURE = "execution_failure"
    MANUAL = "manual"


@dataclass
class BreakerTrip:
    """Record of a circuit breaker trip."""
    trip_id: str
    trigger_type: TriggerType
    trigger_value: float
    threshold: float
    response_level: ResponseLevel
    timestamp: datetime
    symbol: Optional[str]
    message: str
    auto_reset_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trip_id': self.trip_id,
            'trigger_type': self.trigger_type.value,
            'trigger_value': self.trigger_value,
            'threshold': self.threshold,
            'response_level': self.response_level.name,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'message': self.message,
            'auto_reset_at': self.auto_reset_at.isoformat() if self.auto_reset_at else None
        }


@dataclass
class BreakerConfig:
    """Configuration for a circuit breaker."""
    name: str
    trigger_type: TriggerType
    thresholds: Dict[ResponseLevel, float]  # Level -> threshold value
    cooldown_seconds: int = 300
    auto_reset: bool = True
    symbols: Optional[Set[str]] = None  # None = all symbols
    enabled: bool = True


class FlashMoveDetector:
    """
    Detects flash moves (rapid price changes).
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.price_history: Dict[str, deque] = {}
        
            # Thresholds
            self.warn_pct = self.config.get('warn_pct', 1.0)
            self.throttle_pct = self.config.get('throttle_pct', 2.0)
            self.halt_pct = self.config.get('halt_pct', 3.0)
            self.emergency_pct = self.config.get('emergency_pct', 5.0)
        
            self.window_seconds = self.config.get('window_seconds', 60)
            self.min_samples = self.config.get('min_samples', 5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_price(self, symbol: str, price: float, timestamp: datetime):
        """Add price observation."""
        try:
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=1000)
        
            self.price_history[symbol].append((timestamp, price))
        except Exception as e:
            logger.error(f"Error in add_price: {e}")
            raise
    
    def check(self, symbol: str) -> Optional[tuple]:
        """
        Check for flash move.
        
        Returns:
            Tuple of (response_level, move_pct) or None
        """
        try:
            if symbol not in self.price_history:
                return None
        
            history = self.price_history[symbol]
            if len(history) < self.min_samples:
                return None
        
            # Get prices within window
            cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
            recent = [(ts, p) for ts, p in history if ts >= cutoff]
        
            if len(recent) < 2:
                return None
        
            # Calculate max move
            prices = [p for _, p in recent]
            max_price = max(prices)
            min_price = min(prices)
        
            if min_price == 0:
                return None
        
            move_pct = abs(max_price - min_price) / min_price * 100
        
            # Determine response level
            if move_pct >= self.emergency_pct:
                return (ResponseLevel.EMERGENCY, move_pct)
            elif move_pct >= self.halt_pct:
                return (ResponseLevel.HALT, move_pct)
            elif move_pct >= self.throttle_pct:
                return (ResponseLevel.THROTTLE, move_pct)
            elif move_pct >= self.warn_pct:
                return (ResponseLevel.WARN, move_pct)
        
            return None
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class VolatilityMonitor:
    """
    Monitors volatility for spikes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.volatility_history: Dict[str, deque] = {}
        
            # Thresholds (multiples of average)
            self.warn_mult = self.config.get('warn_mult', 2.0)
            self.throttle_mult = self.config.get('throttle_mult', 3.0)
            self.halt_mult = self.config.get('halt_mult', 5.0)
        
            self.lookback = self.config.get('lookback', 20)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_volatility(self, symbol: str, volatility: float):
        """Add volatility observation."""
        try:
            if symbol not in self.volatility_history:
                self.volatility_history[symbol] = deque(maxlen=100)
        
            self.volatility_history[symbol].append(volatility)
        except Exception as e:
            logger.error(f"Error in add_volatility: {e}")
            raise
    
    def check(self, symbol: str) -> Optional[tuple]:
        """
        Check for volatility spike.
        
        Returns:
            Tuple of (response_level, spike_ratio) or None
        """
        try:
            if symbol not in self.volatility_history:
                return None
        
            history = list(self.volatility_history[symbol])
            if len(history) < self.lookback + 1:
                return None
        
            current = history[-1]
            avg = statistics.mean(history[:-1][-self.lookback:])
        
            if avg == 0:
                return None
        
            ratio = current / avg
        
            if ratio >= self.halt_mult:
                return (ResponseLevel.HALT, ratio)
            elif ratio >= self.throttle_mult:
                return (ResponseLevel.THROTTLE, ratio)
            elif ratio >= self.warn_mult:
                return (ResponseLevel.WARN, ratio)
        
            return None
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class SpreadMonitor:
    """
    Monitors bid-ask spread for blowouts.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.spread_history: Dict[str, deque] = {}
        
            # Thresholds (multiples of average)
            self.warn_mult = self.config.get('warn_mult', 3.0)
            self.throttle_mult = self.config.get('throttle_mult', 5.0)
            self.halt_mult = self.config.get('halt_mult', 10.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_spread(self, symbol: str, spread: float):
        """Add spread observation."""
        try:
            if symbol not in self.spread_history:
                self.spread_history[symbol] = deque(maxlen=100)
        
            self.spread_history[symbol].append(spread)
        except Exception as e:
            logger.error(f"Error in add_spread: {e}")
            raise
    
    def check(self, symbol: str) -> Optional[tuple]:
        """Check for spread blowout."""
        try:
            if symbol not in self.spread_history:
                return None
        
            history = list(self.spread_history[symbol])
            if len(history) < 10:
                return None
        
            current = history[-1]
            avg = statistics.mean(history[:-1])
        
            if avg == 0:
                return None
        
            ratio = current / avg
        
            if ratio >= self.halt_mult:
                return (ResponseLevel.HALT, ratio)
            elif ratio >= self.throttle_mult:
                return (ResponseLevel.THROTTLE, ratio)
            elif ratio >= self.warn_mult:
                return (ResponseLevel.WARN, ratio)
        
            return None
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class DrawdownMonitor:
    """
    Monitors portfolio drawdown.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            self.warn_pct = self.config.get('warn_pct', 3.0)
            self.throttle_pct = self.config.get('throttle_pct', 5.0)
            self.halt_pct = self.config.get('halt_pct', 10.0)
            self.emergency_pct = self.config.get('emergency_pct', 15.0)
        
            self.peak_equity = 0
            self.current_equity = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, equity: float):
        """Update equity."""
        try:
            self.current_equity = equity
            if equity > self.peak_equity:
                self.peak_equity = equity
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def check(self) -> Optional[tuple]:
        """Check for drawdown breach."""
        try:
            if self.peak_equity == 0:
                return None
        
            drawdown_pct = (self.peak_equity - self.current_equity) / self.peak_equity * 100
        
            if drawdown_pct >= self.emergency_pct:
                return (ResponseLevel.EMERGENCY, drawdown_pct)
            elif drawdown_pct >= self.halt_pct:
                return (ResponseLevel.HALT, drawdown_pct)
            elif drawdown_pct >= self.throttle_pct:
                return (ResponseLevel.THROTTLE, drawdown_pct)
            elif drawdown_pct >= self.warn_pct:
                return (ResponseLevel.WARN, drawdown_pct)
        
            return None
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class AdvancedCircuitBreaker:
    """
    Main advanced circuit breaker system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Monitors
            self.flash_detector = FlashMoveDetector(config.get('flash_move', {}))
            self.volatility_monitor = VolatilityMonitor(config.get('volatility', {}))
            self.spread_monitor = SpreadMonitor(config.get('spread', {}))
            self.drawdown_monitor = DrawdownMonitor(config.get('drawdown', {}))
        
            # State
            self.state = BreakerState.CLOSED
            self.current_level = ResponseLevel.NORMAL
            self.active_trips: Dict[str, BreakerTrip] = {}
            self.trip_history: deque = deque(maxlen=1000)
        
            # Cooldown tracking
            self.last_trip_time: Optional[datetime] = None
            self.cooldown_seconds = self.config.get('cooldown_seconds', 300)
        
            # Callbacks
            self.on_trip: Optional[Callable[[BreakerTrip], None]] = None
            self.on_reset: Optional[Callable[[str], None]] = None
        
            # Consecutive loss tracking
            self.consecutive_losses = 0
            self.max_consecutive_losses = self.config.get('max_consecutive_losses', 5)
        
            # Trip counter
            self._trip_counter = 0
        
            logger.info("AdvancedCircuitBreaker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_market_data(
        self,
        symbol: str,
        price: float,
        spread: float,
        volatility: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Update with market data.
        
        Args:
            symbol: Trading symbol
            price: Current price
            spread: Bid-ask spread
            volatility: Current volatility
            timestamp: Data timestamp
        """
        try:
            ts = timestamp or datetime.now()
        
            self.flash_detector.add_price(symbol, price, ts)
            self.spread_monitor.add_spread(symbol, spread)
            self.volatility_monitor.add_volatility(symbol, volatility)
        
            # Check all monitors
            self._check_all(symbol)
        except Exception as e:
            logger.error(f"Error in update_market_data: {e}")
            raise
    
    def update_equity(self, equity: float):
        """Update portfolio equity."""
        try:
            self.drawdown_monitor.update(equity)
        
            # Check drawdown
            result = self.drawdown_monitor.check()
            if result:
                level, value = result
                self._trip(
                    TriggerType.DRAWDOWN,
                    value,
                    self.drawdown_monitor.halt_pct,
                    level,
                    None,
                    f"Drawdown at {value:.1f}%"
                )
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise
    
    def record_trade_result(self, pnl: float):
        """Record trade result for consecutive loss tracking."""
        try:
            if pnl < 0:
                self.consecutive_losses += 1
            
                if self.consecutive_losses >= self.max_consecutive_losses:
                    self._trip(
                        TriggerType.CONSECUTIVE_LOSSES,
                        self.consecutive_losses,
                        self.max_consecutive_losses,
                        ResponseLevel.THROTTLE,
                        None,
                        f"{self.consecutive_losses} consecutive losses"
                    )
            else:
                self.consecutive_losses = 0
        except Exception as e:
            logger.error(f"Error in record_trade_result: {e}")
            raise
    
    def _check_all(self, symbol: str):
        """Check all monitors for the symbol."""
        # Flash move
        try:
            result = self.flash_detector.check(symbol)
            if result:
                level, value = result
                self._trip(
                    TriggerType.FLASH_MOVE,
                    value,
                    self.flash_detector.halt_pct,
                    level,
                    symbol,
                    f"Flash move of {value:.2f}% detected"
                )
        
            # Volatility spike
            result = self.volatility_monitor.check(symbol)
            if result:
                level, value = result
                self._trip(
                    TriggerType.VOLATILITY_SPIKE,
                    value,
                    self.volatility_monitor.halt_mult,
                    level,
                    symbol,
                    f"Volatility spike: {value:.1f}x average"
                )
        
            # Spread blowout
            result = self.spread_monitor.check(symbol)
            if result:
                level, value = result
                self._trip(
                    TriggerType.SPREAD_BLOWOUT,
                    value,
                    self.spread_monitor.halt_mult,
                    level,
                    symbol,
                    f"Spread blowout: {value:.1f}x average"
                )
        except Exception as e:
            logger.error(f"Error in _check_all: {e}")
            raise
    
    def _trip(
        self,
        trigger_type: TriggerType,
        trigger_value: float,
        threshold: float,
        level: ResponseLevel,
        symbol: Optional[str],
        message: str
    ):
        """Trip the circuit breaker."""
        try:
            self._trip_counter += 1
            trip_id = f"TRIP-{self._trip_counter:06d}"
        
            # Calculate auto-reset time
            auto_reset = None
            if level.value < ResponseLevel.EMERGENCY.value:
                auto_reset = datetime.now() + timedelta(seconds=self.cooldown_seconds)
        
            trip = BreakerTrip(
                trip_id=trip_id,
                trigger_type=trigger_type,
                trigger_value=trigger_value,
                threshold=threshold,
                response_level=level,
                timestamp=datetime.now(),
                symbol=symbol,
                message=message,
                auto_reset_at=auto_reset
            )
        
            self.active_trips[trip_id] = trip
            self.trip_history.append(trip)
            self.last_trip_time = datetime.now()
        
            # Update state
            if level.value >= ResponseLevel.HALT.value:
                self.state = BreakerState.OPEN
            elif level.value >= ResponseLevel.THROTTLE.value:
                self.state = BreakerState.HALF_OPEN
        
            # Update current level (take highest)
            if level.value > self.current_level.value:
                self.current_level = level
        
            logger.warning(f"Circuit breaker tripped: {message} (Level: {level.name})")
        
            if self.on_trip:
                self.on_trip(trip)
        except Exception as e:
            logger.error(f"Error in _trip: {e}")
            raise
    
    def manual_trip(self, reason: str, level: ResponseLevel = ResponseLevel.HALT):
        """Manually trip the circuit breaker."""
        try:
            self._trip(
                TriggerType.MANUAL,
                0,
                0,
                level,
                None,
                f"Manual trip: {reason}"
            )
        except Exception as e:
            logger.error(f"Error in manual_trip: {e}")
            raise
    
    def reset(self, trip_id: Optional[str] = None):
        """
        Reset circuit breaker.
        
        Args:
            trip_id: Specific trip to reset, or None for all
        """
        try:
            if trip_id:
                if trip_id in self.active_trips:
                    del self.active_trips[trip_id]
                    logger.info(f"Reset trip {trip_id}")
            else:
                self.active_trips.clear()
                logger.info("Reset all trips")
        
            # Recalculate state
            self._recalculate_state()
        
            if self.on_reset:
                self.on_reset(trip_id or "all")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def check_auto_reset(self):
        """Check and perform auto-resets."""
        try:
            now = datetime.now()
            to_reset = []
        
            for trip_id, trip in self.active_trips.items():
                if trip.auto_reset_at and now >= trip.auto_reset_at:
                    to_reset.append(trip_id)
        
            for trip_id in to_reset:
                self.reset(trip_id)
        except Exception as e:
            logger.error(f"Error in check_auto_reset: {e}")
            raise
    
    def _recalculate_state(self):
        """Recalculate state based on active trips."""
        try:
            if not self.active_trips:
                self.state = BreakerState.CLOSED
                self.current_level = ResponseLevel.NORMAL
                return
        
            max_level = max(t.response_level.value for t in self.active_trips.values())
            self.current_level = ResponseLevel(max_level)
        
            if max_level >= ResponseLevel.HALT.value:
                self.state = BreakerState.OPEN
            elif max_level >= ResponseLevel.THROTTLE.value:
                self.state = BreakerState.HALF_OPEN
            else:
                self.state = BreakerState.CLOSED
        except Exception as e:
            logger.error(f"Error in _recalculate_state: {e}")
            raise
    
    def can_trade(self, symbol: Optional[str] = None) -> tuple:
        """
        Check if trading is allowed.
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check auto-resets first
        try:
            self.check_auto_reset()
        
            if self.state == BreakerState.OPEN:
                return False, f"Circuit breaker OPEN: {self.current_level.name}"
        
            if self.state == BreakerState.HALF_OPEN:
                return True, f"Circuit breaker HALF_OPEN: reduced trading allowed"
        
            return True, "Circuit breaker CLOSED: normal trading"
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise
    
    def get_throttle_factor(self) -> float:
        """
        Get position size throttle factor.
        
        Returns:
            Factor to multiply position size by (0-1)
        """
        try:
            if self.current_level == ResponseLevel.NORMAL:
                return 1.0
            elif self.current_level == ResponseLevel.WARN:
                return 0.75
            elif self.current_level == ResponseLevel.THROTTLE:
                return 0.5
            elif self.current_level == ResponseLevel.HALT:
                return 0.0
            elif self.current_level == ResponseLevel.EMERGENCY:
                return 0.0
            return 1.0
        except Exception as e:
            logger.error(f"Error in get_throttle_factor: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            'state': self.state.value,
            'current_level': self.current_level.name,
            'active_trips': len(self.active_trips),
            'throttle_factor': self.get_throttle_factor(),
            'consecutive_losses': self.consecutive_losses,
            'last_trip': self.last_trip_time.isoformat() if self.last_trip_time else None,
            'can_trade': self.can_trade()[0],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_active_trips(self) -> List[Dict[str, Any]]:
        """Get all active trips."""
        return [trip.to_dict() for trip in self.active_trips.values()]


# Factory function
def create_circuit_breaker(config: Optional[Dict] = None) -> AdvancedCircuitBreaker:
    """Create AdvancedCircuitBreaker instance."""
    return AdvancedCircuitBreaker(config)


# Example usage
if __name__ == "__main__":
    import random
    import time
    
    breaker = create_circuit_breaker({
        'flash_move': {
            'warn_pct': 0.5,
            'throttle_pct': 1.0,
            'halt_pct': 2.0,
            'window_seconds': 10
        },
        'cooldown_seconds': 5
    })
    
    print("=" * 60)
    print("ADVANCED CIRCUIT BREAKER SYSTEM")
    print("=" * 60)
    
    # Simulate normal market
    print("\nSimulating normal market...")
    base_price = 100.0
    
    for i in range(10):
        price = base_price + random.uniform(-0.1, 0.1)
        breaker.update_market_data(
            symbol="TEST",
            price=price,
            spread=0.02,
            volatility=0.01,
            timestamp=datetime.now()
        )
        time.sleep(0.1)
    
    can_trade, reason = breaker.can_trade()
    print(f"Can trade: {can_trade} - {reason}")
    
    # Simulate flash crash
    print("\n" + "=" * 60)
    print("SIMULATING FLASH CRASH")
    print("=" * 60)
    
    for i in range(5):
        price = base_price * (1 - 0.01 * (i + 1))  # 1% drop per tick
        breaker.update_market_data(
            symbol="TEST",
            price=price,
            spread=0.1,  # Spread widening
            volatility=0.05,  # Volatility spike
            timestamp=datetime.now()
        )
        time.sleep(0.2)
        
        status = breaker.get_status()
        print(f"Price: {price:.2f} | State: {status['state']} | Level: {status['current_level']}")
    
    # Check status
    print("\n" + "=" * 60)
    print("CIRCUIT BREAKER STATUS")
    print("=" * 60)
    
    status = breaker.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Active trips
    print("\nActive Trips:")
    for trip in breaker.get_active_trips():
        print(f"  {trip['trip_id']}: {trip['trigger_type']} - {trip['message']}")
    
    # Wait for auto-reset
    print("\n" + "=" * 60)
    print("WAITING FOR AUTO-RESET...")
    print("=" * 60)
    
    time.sleep(6)
    breaker.check_auto_reset()
    
    status = breaker.get_status()
    print(f"\nAfter cooldown:")
    print(f"State: {status['state']}")
    print(f"Can trade: {status['can_trade']}")
