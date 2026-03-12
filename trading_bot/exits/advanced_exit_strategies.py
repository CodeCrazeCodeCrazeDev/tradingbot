"""
Advanced Exit Strategies for Trading.

This module implements:
- Multiple exit strategy types
- Dynamic stop loss management
- Trailing stop variations
- Time-based exits
- Volatility-based exits
- Profit target optimization
- Chandelier exits
- Parabolic SAR exits
- ATR-based exits
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class ExitType(Enum):
    """Types of exit strategies."""
    FIXED_STOP = "fixed_stop"
    TRAILING_STOP = "trailing_stop"
    CHANDELIER = "chandelier"
    PARABOLIC_SAR = "parabolic_sar"
    ATR_STOP = "atr_stop"
    VOLATILITY_STOP = "volatility_stop"
    TIME_BASED = "time_based"
    BREAKEVEN = "breakeven"
    PARTIAL_PROFIT = "partial_profit"
    INDICATOR_BASED = "indicator_based"


class TrailingMethod(Enum):
    """Trailing stop methods."""
    FIXED_DISTANCE = "fixed_distance"
    PERCENTAGE = "percentage"
    ATR_MULTIPLE = "atr_multiple"
    SWING_POINTS = "swing_points"
    MOVING_AVERAGE = "moving_average"
    PARABOLIC = "parabolic"
    STEP = "step"


class ExitReason(Enum):
    """Reasons for exit."""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    TIME_EXIT = "time_exit"
    BREAKEVEN = "breakeven"
    SIGNAL_EXIT = "signal_exit"
    MANUAL = "manual"
    EMERGENCY = "emergency"


@dataclass
class ExitLevel:
    """An exit level with price and size."""
    price: float
    size_percent: float
    exit_type: ExitType
    is_active: bool = True
    triggered: bool = False
    trigger_time: Optional[datetime] = None


@dataclass
class ExitSignal:
    """Signal to exit a position."""
    should_exit: bool
    exit_price: float
    exit_size: float  # 0-1 for partial, 1 for full
    reason: ExitReason
    urgency: float  # 0-1
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExitPlan:
    """Complete exit plan for a position."""
    stop_loss: float
    take_profit_levels: List[ExitLevel]
    trailing_stop: Optional[float]
    breakeven_trigger: float
    time_exit: Optional[datetime]
    current_exit_price: float
    exit_type: ExitType
    is_active: bool = True


@dataclass
class TrailingStopState:
    """State of a trailing stop."""
    initial_stop: float
    current_stop: float
    highest_price: float  # For long
    lowest_price: float  # For short
    trail_distance: float
    method: TrailingMethod
    last_update: datetime = field(default_factory=datetime.now)


class FixedStopLoss:
    """
    Fixed stop loss exit strategy.
    """
    
    def __init__(self, stop_distance: float = 0.02):
        try:
            self.stop_distance = stop_distance
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_stop(
        self,
        entry_price: float,
        direction: str
    ) -> float:
        """Calculate fixed stop loss price."""
        try:
            if direction == 'long':
                return entry_price * (1 - self.stop_distance)
            else:
                return entry_price * (1 + self.stop_distance)
        except Exception as e:
            logger.error(f"Error in calculate_stop: {e}")
            raise
    
    def check_exit(
        self,
        current_price: float,
        stop_price: float,
        direction: str
    ) -> ExitSignal:
        """Check if stop loss is triggered."""
        try:
            if direction == 'long':
                triggered = current_price <= stop_price
            else:
                triggered = current_price >= stop_price
        
            return ExitSignal(
                should_exit=triggered,
                exit_price=stop_price if triggered else current_price,
                exit_size=1.0,
                reason=ExitReason.STOP_LOSS,
                urgency=1.0 if triggered else 0.0,
                message="Stop loss triggered" if triggered else "Stop loss not triggered"
            )
        except Exception as e:
            logger.error(f"Error in check_exit: {e}")
            raise


class TrailingStop:
    """
    Trailing stop exit strategy with multiple methods.
    """
    
    def __init__(
        self,
        method: TrailingMethod = TrailingMethod.ATR_MULTIPLE,
        trail_distance: float = 0.02,
        atr_multiple: float = 2.0,
        step_size: float = 0.005
    ):
        try:
            self.method = method
            self.trail_distance = trail_distance
            self.atr_multiple = atr_multiple
            self.step_size = step_size
            self.states: Dict[str, TrailingStopState] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def initialize(
        self,
        position_id: str,
        entry_price: float,
        direction: str,
        atr: float = 0.0
    ) -> TrailingStopState:
        """Initialize trailing stop for a position."""
        try:
            if self.method == TrailingMethod.ATR_MULTIPLE:
                trail = atr * self.atr_multiple
            elif self.method == TrailingMethod.PERCENTAGE:
                trail = entry_price * self.trail_distance
            else:
                trail = self.trail_distance
        
            if direction == 'long':
                initial_stop = entry_price - trail
            else:
                initial_stop = entry_price + trail
        
            state = TrailingStopState(
                initial_stop=initial_stop,
                current_stop=initial_stop,
                highest_price=entry_price,
                lowest_price=entry_price,
                trail_distance=trail,
                method=self.method
            )
        
            self.states[position_id] = state
            return state
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def update(
        self,
        position_id: str,
        current_price: float,
        direction: str,
        atr: Optional[float] = None
    ) -> Tuple[float, bool]:
        """Update trailing stop and check if triggered."""
        try:
            if position_id not in self.states:
                return 0.0, False
        
            state = self.states[position_id]
        
            # Update trail distance if ATR-based
            if atr and self.method == TrailingMethod.ATR_MULTIPLE:
                state.trail_distance = atr * self.atr_multiple
        
            if direction == 'long':
                # Update highest price
                if current_price > state.highest_price:
                    state.highest_price = current_price
                
                    # Calculate new stop
                    if self.method == TrailingMethod.STEP:
                        # Step trailing - only move in steps
                        new_stop = current_price - state.trail_distance
                        steps = int((new_stop - state.current_stop) / self.step_size)
                        if steps > 0:
                            state.current_stop += steps * self.step_size
                    else:
                        state.current_stop = max(
                            state.current_stop,
                            current_price - state.trail_distance
                        )
            
                triggered = current_price <= state.current_stop
            
            else:  # short
                # Update lowest price
                if current_price < state.lowest_price:
                    state.lowest_price = current_price
                
                    if self.method == TrailingMethod.STEP:
                        new_stop = current_price + state.trail_distance
                        steps = int((state.current_stop - new_stop) / self.step_size)
                        if steps > 0:
                            state.current_stop -= steps * self.step_size
                    else:
                        state.current_stop = min(
                            state.current_stop,
                            current_price + state.trail_distance
                        )
            
                triggered = current_price >= state.current_stop
        
            state.last_update = datetime.now()
        
            return state.current_stop, triggered
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_stop(self, position_id: str) -> Optional[float]:
        """Get current stop price for a position."""
        try:
            if position_id in self.states:
                return self.states[position_id].current_stop
            return None
        except Exception as e:
            logger.error(f"Error in get_stop: {e}")
            raise


class ChandelierExit:
    """
    Chandelier Exit - ATR-based trailing stop from highest high.
    """
    
    def __init__(
        self,
        atr_period: int = 22,
        atr_multiple: float = 3.0,
        use_close: bool = True
    ):
        try:
            self.atr_period = atr_period
            self.atr_multiple = atr_multiple
            self.use_close = use_close
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate ATR."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
        
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
        
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr.rolling(window=self.atr_period).mean()
        except Exception as e:
            logger.error(f"Error in calculate_atr: {e}")
            raise
    
    def calculate_exit(
        self,
        df: pd.DataFrame,
        direction: str
    ) -> pd.Series:
        """Calculate Chandelier Exit levels."""
        try:
            atr = self.calculate_atr(df)
        
            if direction == 'long':
                if self.use_close:
                    highest = df['close'].rolling(window=self.atr_period).max()
                else:
                    highest = df['high'].rolling(window=self.atr_period).max()
            
                chandelier = highest - (atr * self.atr_multiple)
            else:
                if self.use_close:
                    lowest = df['close'].rolling(window=self.atr_period).min()
                else:
                    lowest = df['low'].rolling(window=self.atr_period).min()
            
                chandelier = lowest + (atr * self.atr_multiple)
        
            return chandelier
        except Exception as e:
            logger.error(f"Error in calculate_exit: {e}")
            raise
    
    def check_exit(
        self,
        df: pd.DataFrame,
        current_price: float,
        direction: str
    ) -> ExitSignal:
        """Check if Chandelier Exit is triggered."""
        try:
            chandelier = self.calculate_exit(df, direction)
            exit_level = chandelier.iloc[-1]
        
            if direction == 'long':
                triggered = current_price <= exit_level
            else:
                triggered = current_price >= exit_level
        
            return ExitSignal(
                should_exit=triggered,
                exit_price=exit_level,
                exit_size=1.0,
                reason=ExitReason.TRAILING_STOP,
                urgency=0.8 if triggered else 0.0,
                message=f"Chandelier Exit at {exit_level:.4f}"
            )
        except Exception as e:
            logger.error(f"Error in check_exit: {e}")
            raise


class ParabolicSAR:
    """
    Parabolic SAR exit strategy.
    """
    
    def __init__(
        self,
        af_start: float = 0.02,
        af_increment: float = 0.02,
        af_max: float = 0.2
    ):
        try:
            self.af_start = af_start
            self.af_increment = af_increment
            self.af_max = af_max
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_sar(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Parabolic SAR."""
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
        
            n = len(close)
            sar = np.zeros(n)
            ep = np.zeros(n)  # Extreme point
            af = np.zeros(n)  # Acceleration factor
            trend = np.zeros(n)  # 1 for up, -1 for down
        
            # Initialize
            trend[0] = 1 if close[0] > close[min(1, n-1)] else -1
            sar[0] = low[0] if trend[0] == 1 else high[0]
            ep[0] = high[0] if trend[0] == 1 else low[0]
            af[0] = self.af_start
        
            for i in range(1, n):
                # Calculate SAR
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            
                if trend[i-1] == 1:  # Uptrend
                    sar[i] = min(sar[i], low[i-1], low[max(0, i-2)])
                
                    if low[i] < sar[i]:
                        # Trend reversal
                        trend[i] = -1
                        sar[i] = ep[i-1]
                        ep[i] = low[i]
                        af[i] = self.af_start
                    else:
                        trend[i] = 1
                        if high[i] > ep[i-1]:
                            ep[i] = high[i]
                            af[i] = min(af[i-1] + self.af_increment, self.af_max)
                        else:
                            ep[i] = ep[i-1]
                            af[i] = af[i-1]
                else:  # Downtrend
                    sar[i] = max(sar[i], high[i-1], high[max(0, i-2)])
                
                    if high[i] > sar[i]:
                        # Trend reversal
                        trend[i] = 1
                        sar[i] = ep[i-1]
                        ep[i] = high[i]
                        af[i] = self.af_start
                    else:
                        trend[i] = -1
                        if low[i] < ep[i-1]:
                            ep[i] = low[i]
                            af[i] = min(af[i-1] + self.af_increment, self.af_max)
                        else:
                            ep[i] = ep[i-1]
                            af[i] = af[i-1]
        
            return pd.Series(sar, index=df.index)
        except Exception as e:
            logger.error(f"Error in calculate_sar: {e}")
            raise
    
    def check_exit(
        self,
        df: pd.DataFrame,
        current_price: float,
        direction: str
    ) -> ExitSignal:
        """Check if Parabolic SAR signals exit."""
        try:
            sar = self.calculate_sar(df)
            current_sar = sar.iloc[-1]
        
            if direction == 'long':
                triggered = current_price < current_sar
            else:
                triggered = current_price > current_sar
        
            return ExitSignal(
                should_exit=triggered,
                exit_price=current_sar,
                exit_size=1.0,
                reason=ExitReason.TRAILING_STOP,
                urgency=0.7 if triggered else 0.0,
                message=f"Parabolic SAR at {current_sar:.4f}"
            )
        except Exception as e:
            logger.error(f"Error in check_exit: {e}")
            raise


class TimeBasedExit:
    """
    Time-based exit strategies.
    """
    
    def __init__(
        self,
        max_hold_hours: int = 24,
        session_end_exit: bool = True,
        friday_close: bool = True
    ):
        try:
            self.max_hold_hours = max_hold_hours
            self.session_end_exit = session_end_exit
            self.friday_close = friday_close
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def check_exit(
        self,
        entry_time: datetime,
        current_time: Optional[datetime] = None
    ) -> ExitSignal:
        """Check if time-based exit is triggered."""
        try:
            now = current_time or datetime.now()
            hold_duration = now - entry_time
        
            # Check max hold time
            if hold_duration > timedelta(hours=self.max_hold_hours):
                return ExitSignal(
                    should_exit=True,
                    exit_price=0,  # Market price
                    exit_size=1.0,
                    reason=ExitReason.TIME_EXIT,
                    urgency=0.6,
                    message=f"Max hold time ({self.max_hold_hours}h) exceeded"
                )
        
            # Check Friday close
            if self.friday_close and now.weekday() == 4 and now.hour >= 20:
                return ExitSignal(
                    should_exit=True,
                    exit_price=0,
                    exit_size=1.0,
                    reason=ExitReason.TIME_EXIT,
                    urgency=0.8,
                    message="Friday close - avoiding weekend gap"
                )
        
            return ExitSignal(
                should_exit=False,
                exit_price=0,
                exit_size=0,
                reason=ExitReason.TIME_EXIT,
                urgency=0.0,
                message="Time exit not triggered"
            )
        except Exception as e:
            logger.error(f"Error in check_exit: {e}")
            raise


class BreakevenManager:
    """
    Manages breakeven stop adjustments.
    """
    
    def __init__(
        self,
        trigger_r_multiple: float = 1.0,
        offset_pips: float = 2.0,
        pip_value: float = 0.0001
    ):
        try:
            self.trigger_r_multiple = trigger_r_multiple
            self.offset_pips = offset_pips
            self.pip_value = pip_value
            self.breakeven_positions: Dict[str, bool] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def check_breakeven(
        self,
        position_id: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        direction: str
    ) -> Tuple[bool, float]:
        """Check if position should move to breakeven."""
        try:
            if position_id in self.breakeven_positions:
                return False, stop_loss  # Already at breakeven
        
            risk = abs(entry_price - stop_loss)
            target = risk * self.trigger_r_multiple
        
            if direction == 'long':
                profit = current_price - entry_price
                if profit >= target:
                    new_stop = entry_price + (self.offset_pips * self.pip_value)
                    self.breakeven_positions[position_id] = True
                    return True, new_stop
            else:
                profit = entry_price - current_price
                if profit >= target:
                    new_stop = entry_price - (self.offset_pips * self.pip_value)
                    self.breakeven_positions[position_id] = True
                    return True, new_stop
        
            return False, stop_loss
        except Exception as e:
            logger.error(f"Error in check_breakeven: {e}")
            raise


class AdvancedExitManager:
    """
    Complete advanced exit management system.
    """
    
    def __init__(
        self,
        trailing_stop: Optional[TrailingStop] = None,
        chandelier: Optional[ChandelierExit] = None,
        parabolic_sar: Optional[ParabolicSAR] = None,
        time_exit: Optional[TimeBasedExit] = None,
        breakeven: Optional[BreakevenManager] = None
    ):
        try:
            self.trailing_stop = trailing_stop or TrailingStop()
            self.chandelier = chandelier or ChandelierExit()
            self.parabolic_sar = parabolic_sar or ParabolicSAR()
            self.time_exit = time_exit or TimeBasedExit()
            self.breakeven = breakeven or BreakevenManager()
        
            self.exit_plans: Dict[str, ExitPlan] = {}
            self.exit_history: List[ExitSignal] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def create_exit_plan(
        self,
        position_id: str,
        entry_price: float,
        direction: str,
        stop_loss: float,
        take_profit_levels: List[Tuple[float, float]] = None,  # (price, size_pct)
        atr: float = 0.0,
        max_hold_hours: int = 24
    ) -> ExitPlan:
        """Create a comprehensive exit plan."""
        # Initialize trailing stop
        try:
            self.trailing_stop.initialize(position_id, entry_price, direction, atr)
        
            # Create take profit levels
            tp_levels = []
            if take_profit_levels:
                for price, size_pct in take_profit_levels:
                    tp_levels.append(ExitLevel(
                        price=price,
                        size_percent=size_pct,
                        exit_type=ExitType.PARTIAL_PROFIT
                    ))
        
            # Calculate breakeven trigger
            risk = abs(entry_price - stop_loss)
            breakeven_trigger = entry_price + risk if direction == 'long' else entry_price - risk
        
            plan = ExitPlan(
                stop_loss=stop_loss,
                take_profit_levels=tp_levels,
                trailing_stop=self.trailing_stop.get_stop(position_id),
                breakeven_trigger=breakeven_trigger,
                time_exit=datetime.now() + timedelta(hours=max_hold_hours),
                current_exit_price=stop_loss,
                exit_type=ExitType.TRAILING_STOP
            )
        
            self.exit_plans[position_id] = plan
            return plan
        except Exception as e:
            logger.error(f"Error in create_exit_plan: {e}")
            raise
    
    def update_and_check(
        self,
        position_id: str,
        current_price: float,
        direction: str,
        entry_time: datetime,
        df: Optional[pd.DataFrame] = None,
        atr: Optional[float] = None
    ) -> List[ExitSignal]:
        """Update exit levels and check for exit signals."""
        try:
            signals = []
        
            if position_id not in self.exit_plans:
                return signals
        
            plan = self.exit_plans[position_id]
        
            # Check stop loss
            if direction == 'long' and current_price <= plan.stop_loss:
                signals.append(ExitSignal(
                    should_exit=True,
                    exit_price=plan.stop_loss,
                    exit_size=1.0,
                    reason=ExitReason.STOP_LOSS,
                    urgency=1.0,
                    message="Stop loss hit"
                ))
            elif direction == 'short' and current_price >= plan.stop_loss:
                signals.append(ExitSignal(
                    should_exit=True,
                    exit_price=plan.stop_loss,
                    exit_size=1.0,
                    reason=ExitReason.STOP_LOSS,
                    urgency=1.0,
                    message="Stop loss hit"
                ))
        
            # Check take profit levels
            for level in plan.take_profit_levels:
                if level.triggered or not level.is_active:
                    continue
            
                if direction == 'long' and current_price >= level.price:
                    level.triggered = True
                    level.trigger_time = datetime.now()
                    signals.append(ExitSignal(
                        should_exit=True,
                        exit_price=level.price,
                        exit_size=level.size_percent,
                        reason=ExitReason.TAKE_PROFIT,
                        urgency=0.8,
                        message=f"Take profit level hit at {level.price:.4f}"
                    ))
                elif direction == 'short' and current_price <= level.price:
                    level.triggered = True
                    level.trigger_time = datetime.now()
                    signals.append(ExitSignal(
                        should_exit=True,
                        exit_price=level.price,
                        exit_size=level.size_percent,
                        reason=ExitReason.TAKE_PROFIT,
                        urgency=0.8,
                        message=f"Take profit level hit at {level.price:.4f}"
                    ))
        
            # Update and check trailing stop
            trail_price, trail_triggered = self.trailing_stop.update(
                position_id, current_price, direction, atr
            )
            plan.trailing_stop = trail_price
        
            if trail_triggered:
                signals.append(ExitSignal(
                    should_exit=True,
                    exit_price=trail_price,
                    exit_size=1.0,
                    reason=ExitReason.TRAILING_STOP,
                    urgency=0.9,
                    message=f"Trailing stop hit at {trail_price:.4f}"
                ))
        
            # Check time-based exit
            time_signal = self.time_exit.check_exit(entry_time)
            if time_signal.should_exit:
                signals.append(time_signal)
        
            # Check Chandelier exit if we have data
            if df is not None and len(df) > 22:
                chandelier_signal = self.chandelier.check_exit(df, current_price, direction)
                if chandelier_signal.should_exit:
                    signals.append(chandelier_signal)
        
            # Store signals
            self.exit_history.extend(signals)
        
            return signals
        except Exception as e:
            logger.error(f"Error in update_and_check: {e}")
            raise
    
    def get_best_exit(self, signals: List[ExitSignal]) -> Optional[ExitSignal]:
        """Get the best exit signal from multiple signals."""
        try:
            if not signals:
                return None
        
            # Prioritize by urgency and reason
            priority = {
                ExitReason.STOP_LOSS: 5,
                ExitReason.EMERGENCY: 5,
                ExitReason.TRAILING_STOP: 4,
                ExitReason.TAKE_PROFIT: 3,
                ExitReason.TIME_EXIT: 2,
                ExitReason.SIGNAL_EXIT: 2,
                ExitReason.BREAKEVEN: 1,
                ExitReason.MANUAL: 1
            }
        
            return max(signals, key=lambda s: (priority.get(s.reason, 0), s.urgency))
        except Exception as e:
            logger.error(f"Error in get_best_exit: {e}")
            raise
    
    def remove_position(self, position_id: str) -> None:
        """Remove position from tracking."""
        try:
            if position_id in self.exit_plans:
                del self.exit_plans[position_id]
            if position_id in self.trailing_stop.states:
                del self.trailing_stop.states[position_id]
        except Exception as e:
            logger.error(f"Error in remove_position: {e}")
            raise


# Convenience functions
def calculate_trailing_stop(
    entry_price: float,
    current_price: float,
    direction: str,
    atr: float,
    atr_multiple: float = 2.0
) -> float:
    """Calculate trailing stop price."""
    try:
        trail_distance = atr * atr_multiple
    
        if direction == 'long':
            return max(entry_price - trail_distance, current_price - trail_distance)
        else:
            return min(entry_price + trail_distance, current_price + trail_distance)
    except Exception as e:
        logger.error(f"Error in calculate_trailing_stop: {e}")
        raise


def calculate_chandelier_exit(
    df: pd.DataFrame,
    direction: str,
    period: int = 22,
    atr_multiple: float = 3.0
) -> float:
    """Calculate Chandelier Exit price."""
    try:
        chandelier = ChandelierExit(atr_period=period, atr_multiple=atr_multiple)
        levels = chandelier.calculate_exit(df, direction)
        return float(levels.iloc[-1])
    except Exception as e:
        logger.error(f"Error in calculate_chandelier_exit: {e}")
        raise


def get_exit_recommendation(
    entry_price: float,
    current_price: float,
    stop_loss: float,
    direction: str,
    entry_time: datetime,
    df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """Get exit recommendation for a position."""
    try:
        manager = AdvancedExitManager()
    
        # Create simple exit plan
        plan = manager.create_exit_plan(
            position_id="temp",
            entry_price=entry_price,
            direction=direction,
            stop_loss=stop_loss
        )
    
        # Check exits
        signals = manager.update_and_check(
            position_id="temp",
            current_price=current_price,
            direction=direction,
            entry_time=entry_time,
            df=df
        )
    
        best_signal = manager.get_best_exit(signals)
    
        return {
            'should_exit': best_signal.should_exit if best_signal else False,
            'exit_price': best_signal.exit_price if best_signal else 0,
            'reason': best_signal.reason.value if best_signal else None,
            'trailing_stop': plan.trailing_stop,
            'signals_count': len(signals)
        }
    except Exception as e:
        logger.error(f"Error in get_exit_recommendation: {e}")
        raise
