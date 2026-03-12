"""
Advanced Exit Strategies
========================

Implements intelligent exit management:
1. Trailing stops with ATR adaptation
2. Partial profit taking (scale out)
3. Time-based exits for stagnant trades
4. Volatility-based TP adjustment
5. Support/resistance based exits

Target: Capture more profit, cut losses faster
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class ExitReason(Enum):
    """Reasons for exit"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    PARTIAL_PROFIT = "partial_profit"
    TIME_EXIT = "time_exit"
    BREAKEVEN = "breakeven"
    MANUAL = "manual"
    SIGNAL_REVERSAL = "signal_reversal"


class TrailingStopType(Enum):
    """Types of trailing stops"""
    FIXED_PIPS = "fixed_pips"
    ATR_BASED = "atr_based"
    PERCENTAGE = "percentage"
    SWING_BASED = "swing_based"
    CHANDELIER = "chandelier"


@dataclass
class ExitLevel:
    """An exit level for a position"""
    price: float
    exit_type: ExitReason
    percentage: float  # Percentage of position to exit
    is_active: bool = True
    triggered: bool = False
    trigger_time: Optional[datetime] = None


@dataclass
class PositionExitPlan:
    """Complete exit plan for a position"""
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    current_stop_loss: float
    original_stop_loss: float
    take_profit_levels: List[ExitLevel]
    trailing_stop: Optional[float]
    breakeven_triggered: bool
    time_exit: Optional[datetime]
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'current_stop_loss': self.current_stop_loss,
            'take_profit_levels': [
                {'price': l.price, 'pct': l.percentage, 'triggered': l.triggered}
                for l in self.take_profit_levels
            ],
            'trailing_stop': self.trailing_stop,
            'breakeven_triggered': self.breakeven_triggered,
        }


class TrailingStopManager:
    """
    Manages trailing stops for positions.
    
    PRINCIPLE: Let winners run while protecting profits.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Default trailing stop type
        self.default_type = TrailingStopType(
            self.config.get('default_type', 'atr_based')
        )
        
        # ATR multiplier for ATR-based trailing
        self.atr_multiplier = self.config.get('atr_multiplier', 2.0)
        
        # Fixed pips for fixed trailing
        self.fixed_pips = self.config.get('fixed_pips', 20)
        
        # Percentage for percentage-based trailing
        self.trail_percentage = self.config.get('trail_percentage', 0.01)
        
        # Activation threshold (profit in R before trailing starts)
        self.activation_r = self.config.get('activation_r', 1.0)
        
        logger.info(f"TrailingStopManager initialized: type={self.default_type.value}")
    
    def calculate_trailing_stop(
        self,
        direction: str,
        entry_price: float,
        current_price: float,
        current_stop: float,
        atr: Optional[float] = None,
        trail_type: Optional[TrailingStopType] = None
    ) -> Tuple[float, bool]:
        """
        Calculate new trailing stop level.
        
        Args:
            direction: 'BUY' or 'SELL'
            entry_price: Original entry price
            current_price: Current market price
            current_stop: Current stop loss level
            atr: Current ATR value
            trail_type: Type of trailing stop
        
        Returns:
            Tuple of (new_stop_level, should_update)
        """
        trail_type = trail_type or self.default_type
        
        if direction == 'BUY':
            # For long positions
            if trail_type == TrailingStopType.ATR_BASED and atr:
                new_stop = current_price - (atr * self.atr_multiplier)
            elif trail_type == TrailingStopType.FIXED_PIPS:
                new_stop = current_price - (self.fixed_pips * 0.0001)
            elif trail_type == TrailingStopType.PERCENTAGE:
                new_stop = current_price * (1 - self.trail_percentage)
            else:
                new_stop = current_stop
            
            # Only move stop up, never down
            should_update = new_stop > current_stop
            return max(new_stop, current_stop), should_update
        
        else:  # SELL
            # For short positions
            if trail_type == TrailingStopType.ATR_BASED and atr:
                new_stop = current_price + (atr * self.atr_multiplier)
            elif trail_type == TrailingStopType.FIXED_PIPS:
                new_stop = current_price + (self.fixed_pips * 0.0001)
            elif trail_type == TrailingStopType.PERCENTAGE:
                new_stop = current_price * (1 + self.trail_percentage)
            else:
                new_stop = current_stop
            
            # Only move stop down, never up
            should_update = new_stop < current_stop
            return min(new_stop, current_stop), should_update
    
    def should_activate_trailing(
        self,
        direction: str,
        entry_price: float,
        current_price: float,
        stop_loss: float
    ) -> bool:
        """Check if trailing stop should be activated"""
        # Calculate risk (R)
        risk = abs(entry_price - stop_loss)
        if risk == 0:
            return False
        
        # Calculate current profit in R
        if direction == 'BUY':
            profit = current_price - entry_price
        else:
            profit = entry_price - current_price
        
        profit_r = profit / risk
        
        return profit_r >= self.activation_r


class PartialProfitTaker:
    """
    Manages partial profit taking (scaling out).
    
    PRINCIPLE: Lock in profits while letting remainder run.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Default profit levels (R-multiples and percentages)
        self.profit_levels = self.config.get('profit_levels', [
            {'r': 1.0, 'close_pct': 0.25},  # Close 25% at 1R
            {'r': 2.0, 'close_pct': 0.50},  # Close 50% at 2R
            {'r': 3.0, 'close_pct': 0.25},  # Close remaining 25% at 3R
        ])
        
        # Move to breakeven after first target
        self.breakeven_after_first = self.config.get('breakeven_after_first', True)
        
        logger.info(f"PartialProfitTaker initialized: {len(self.profit_levels)} levels")
    
    def create_exit_levels(
        self,
        direction: str,
        entry_price: float,
        stop_loss: float
    ) -> List[ExitLevel]:
        """
        Create exit levels for a position.
        
        Args:
            direction: 'BUY' or 'SELL'
            entry_price: Entry price
            stop_loss: Stop loss price
        
        Returns:
            List of ExitLevel objects
        """
        risk = abs(entry_price - stop_loss)
        levels = []
        
        for level in self.profit_levels:
            r_multiple = level['r']
            close_pct = level['close_pct']
            
            if direction == 'BUY':
                tp_price = entry_price + (risk * r_multiple)
            else:
                tp_price = entry_price - (risk * r_multiple)
            
            levels.append(ExitLevel(
                price=tp_price,
                exit_type=ExitReason.PARTIAL_PROFIT,
                percentage=close_pct,
                is_active=True
            ))
        
        return levels
    
    def check_levels(
        self,
        direction: str,
        current_price: float,
        exit_levels: List[ExitLevel]
    ) -> List[ExitLevel]:
        """
        Check which exit levels have been triggered.
        
        Returns:
            List of triggered levels
        """
        triggered = []
        
        for level in exit_levels:
            if level.triggered or not level.is_active:
                continue
            
            if direction == 'BUY':
                if current_price >= level.price:
                    level.triggered = True
                    level.trigger_time = datetime.now()
                    triggered.append(level)
            else:
                if current_price <= level.price:
                    level.triggered = True
                    level.trigger_time = datetime.now()
                    triggered.append(level)
        
        return triggered
    
    def get_breakeven_stop(
        self,
        direction: str,
        entry_price: float,
        buffer_pips: float = 2.0
    ) -> float:
        """Calculate breakeven stop with buffer"""
        buffer = buffer_pips * 0.0001
        
        if direction == 'BUY':
            return entry_price + buffer
        else:
            return entry_price - buffer


class TimeBasedExitManager:
    """
    Manages time-based exits for stagnant trades.
    
    PRINCIPLE: Don't let capital sit in non-performing trades.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Maximum time in trade (hours)
        self.max_trade_hours = self.config.get('max_trade_hours', 48)
        
        # Time to exit if no progress (hours)
        self.stagnant_hours = self.config.get('stagnant_hours', 24)
        
        # Minimum profit to avoid time exit (in R)
        self.min_profit_r = self.config.get('min_profit_r', 0.5)
        
        logger.info(f"TimeBasedExitManager initialized: max={self.max_trade_hours}h")
    
    def should_exit(
        self,
        entry_time: datetime,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        direction: str
    ) -> Tuple[bool, str]:
        """
        Check if trade should be exited due to time.
        
        Returns:
            Tuple of (should_exit, reason)
        """
        now = datetime.now()
        hours_in_trade = (now - entry_time).total_seconds() / 3600
        
        # Check maximum time
        if hours_in_trade >= self.max_trade_hours:
            return True, f"Max time reached ({self.max_trade_hours}h)"
        
        # Calculate current profit in R
        risk = abs(entry_price - stop_loss)
        if risk == 0:
            return False, "Cannot calculate R"
        
        if direction == 'BUY':
            profit = current_price - entry_price
        else:
            profit = entry_price - current_price
        
        profit_r = profit / risk
        
        # Check for stagnant trade
        if hours_in_trade >= self.stagnant_hours and profit_r < self.min_profit_r:
            return True, f"Stagnant trade ({hours_in_trade:.1f}h, {profit_r:.2f}R)"
        
        return False, "Trade within time limits"
    
    def get_time_exit(
        self,
        entry_time: datetime
    ) -> datetime:
        """Get the time exit deadline"""
        return entry_time + timedelta(hours=self.max_trade_hours)


class AdvancedExitManager:
    """
    Master exit management system combining all strategies.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.trailing = TrailingStopManager(self.config.get('trailing', {}))
        self.partial = PartialProfitTaker(self.config.get('partial', {}))
        self.time_exit = TimeBasedExitManager(self.config.get('time', {}))
        
        # Active position plans
        self.position_plans: Dict[str, PositionExitPlan] = {}
        
        logger.info("AdvancedExitManager initialized - All exit systems active")
    
    def create_exit_plan(
        self,
        position_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        entry_time: Optional[datetime] = None
    ) -> PositionExitPlan:
        """
        Create a complete exit plan for a new position.
        
        Args:
            position_id: Unique position identifier
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            entry_price: Entry price
            stop_loss: Initial stop loss
            entry_time: Entry timestamp
        
        Returns:
            PositionExitPlan with all exit levels
        """
        entry_time = entry_time or datetime.now()
        
        # Create partial profit levels
        tp_levels = self.partial.create_exit_levels(direction, entry_price, stop_loss)
        
        # Create exit plan
        plan = PositionExitPlan(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            current_stop_loss=stop_loss,
            original_stop_loss=stop_loss,
            take_profit_levels=tp_levels,
            trailing_stop=None,
            breakeven_triggered=False,
            time_exit=self.time_exit.get_time_exit(entry_time)
        )
        
        self.position_plans[position_id] = plan
        
        logger.info(f"Exit plan created for {position_id}: {len(tp_levels)} TP levels")
        
        return plan
    
    def update_exit_plan(
        self,
        position_id: str,
        current_price: float,
        current_atr: Optional[float] = None,
        entry_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update exit plan based on current price.
        
        Returns:
            Dict with actions to take
        """
        if position_id not in self.position_plans:
            return {'error': 'Position not found'}
        
        plan = self.position_plans[position_id]
        actions = {
            'update_stop': False,
            'new_stop': plan.current_stop_loss,
            'close_partial': [],
            'close_full': False,
            'close_reason': None,
        }
        
        # 1. Check partial profit levels
        triggered = self.partial.check_levels(
            plan.direction, current_price, plan.take_profit_levels
        )
        
        for level in triggered:
            actions['close_partial'].append({
                'percentage': level.percentage,
                'price': level.price,
                'reason': ExitReason.PARTIAL_PROFIT.value
            })
            
            # Move to breakeven after first target
            if self.partial.breakeven_after_first and not plan.breakeven_triggered:
                be_stop = self.partial.get_breakeven_stop(
                    plan.direction, plan.entry_price
                )
                
                if plan.direction == 'BUY' and be_stop > plan.current_stop_loss:
                    plan.current_stop_loss = be_stop
                    plan.breakeven_triggered = True
                    actions['update_stop'] = True
                    actions['new_stop'] = be_stop
                elif plan.direction == 'SELL' and be_stop < plan.current_stop_loss:
                    plan.current_stop_loss = be_stop
                    plan.breakeven_triggered = True
                    actions['update_stop'] = True
                    actions['new_stop'] = be_stop
        
        # 2. Check trailing stop
        if self.trailing.should_activate_trailing(
            plan.direction, plan.entry_price, current_price, plan.original_stop_loss
        ):
            new_stop, should_update = self.trailing.calculate_trailing_stop(
                plan.direction,
                plan.entry_price,
                current_price,
                plan.current_stop_loss,
                current_atr
            )
            
            if should_update:
                plan.current_stop_loss = new_stop
                plan.trailing_stop = new_stop
                actions['update_stop'] = True
                actions['new_stop'] = new_stop
        
        # 3. Check time-based exit
        if entry_time:
            should_exit, reason = self.time_exit.should_exit(
                entry_time,
                plan.entry_price,
                current_price,
                plan.original_stop_loss,
                plan.direction
            )
            
            if should_exit:
                actions['close_full'] = True
                actions['close_reason'] = reason
        
        # 4. Check stop loss hit
        if plan.direction == 'BUY' and current_price <= plan.current_stop_loss:
            actions['close_full'] = True
            actions['close_reason'] = ExitReason.STOP_LOSS.value
        elif plan.direction == 'SELL' and current_price >= plan.current_stop_loss:
            actions['close_full'] = True
            actions['close_reason'] = ExitReason.STOP_LOSS.value
        
        return actions
    
    def remove_position(self, position_id: str):
        """Remove a position from tracking"""
        if position_id in self.position_plans:
            del self.position_plans[position_id]
    
    def get_position_plan(self, position_id: str) -> Optional[PositionExitPlan]:
        """Get exit plan for a position"""
        return self.position_plans.get(position_id)
    
    def calculate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> float:
        """Calculate risk/reward ratio"""
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0.0
        
        return reward / risk
