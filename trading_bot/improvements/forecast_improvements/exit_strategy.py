"""
Exit Strategy Enhancement - Improvement #6 (HIGH PRIORITY)
==========================================================

Dynamic adaptive exits to capture more profit and cut losses faster.

Features:
- Trailing stop with ATR adaptation
- Partial profit taking (25% at 1R, 50% at 2R)
- Time-based exit for stagnant trades
- Volatility-based TP adjustment
- Support/resistance based exits
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class ExitType(Enum):
    """Exit types"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    PARTIAL_PROFIT = "partial_profit"
    TIME_BASED = "time_based"
    BREAKEVEN = "breakeven"
    SUPPORT_RESISTANCE = "support_resistance"
    MANUAL = "manual"
    SIGNAL_REVERSAL = "signal_reversal"


class ExitUrgency(Enum):
    """Exit urgency levels"""
    IMMEDIATE = "immediate"
    SOON = "soon"
    NORMAL = "normal"
    OPTIONAL = "optional"


@dataclass
class ExitLevel:
    """Exit level definition"""
    price: float
    exit_type: ExitType
    quantity_percent: float  # 0-1, portion to exit
    reason: str
    urgency: ExitUrgency = ExitUrgency.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExitRecommendation:
    """Exit recommendation"""
    symbol: str
    should_exit: bool
    exit_type: ExitType
    exit_price: float
    quantity_percent: float
    urgency: ExitUrgency
    reasons: List[str] = field(default_factory=list)
    pnl_estimate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    """Position for exit management"""
    symbol: str
    direction: str  # "buy" or "sell"
    entry_price: float
    current_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    atr_at_entry: float = 0.0
    partial_exits: List[Dict] = field(default_factory=list)
    trailing_stop: Optional[float] = None
    breakeven_activated: bool = False


class AdaptiveTrailingStop:
    """ATR-based adaptive trailing stop"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.atr_multiplier = self.config.get('atr_multiplier', 2.0)
            self.activation_profit = self.config.get('activation_profit', 1.0)  # 1R profit to activate
            self.tightening_factor = self.config.get('tightening_factor', 0.1)  # Tighten by 10% per R
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_trailing_stop(
        self,
        position: Position,
        current_atr: float
    ) -> Tuple[Optional[float], str]:
        """Calculate trailing stop level"""
        # Calculate current profit in R
        try:
            risk = abs(position.entry_price - position.stop_loss)
            if risk == 0:
                return None, "Zero risk - cannot calculate trailing stop"
        
            if position.direction.lower() == 'buy':
                current_profit = position.current_price - position.entry_price
            else:
                current_profit = position.entry_price - position.current_price
        
            profit_r = current_profit / risk
        
            # Only activate after minimum profit
            if profit_r < self.activation_profit:
                return None, f"Profit ({profit_r:.1f}R) below activation threshold ({self.activation_profit}R)"
        
            # Calculate ATR-based trailing distance
            # Tighten as profit increases
            tightening = 1 - (min(profit_r - self.activation_profit, 3) * self.tightening_factor)
            trailing_distance = current_atr * self.atr_multiplier * tightening
        
            # Calculate trailing stop price
            if position.direction.lower() == 'buy':
                trailing_stop = position.current_price - trailing_distance
                # Never below entry
                trailing_stop = max(trailing_stop, position.entry_price)
                # Never below current trailing stop
                if position.trailing_stop:
                    trailing_stop = max(trailing_stop, position.trailing_stop)
            else:
                trailing_stop = position.current_price + trailing_distance
                # Never above entry
                trailing_stop = min(trailing_stop, position.entry_price)
                # Never above current trailing stop
                if position.trailing_stop:
                    trailing_stop = min(trailing_stop, position.trailing_stop)
        
            return trailing_stop, f"Trailing stop at {trailing_stop:.5f} ({profit_r:.1f}R profit)"
        except Exception as e:
            logger.error(f"Error in calculate_trailing_stop: {e}")
            raise
    
    def should_trigger(self, position: Position) -> Tuple[bool, str]:
        """Check if trailing stop should trigger"""
        try:
            if position.trailing_stop is None:
                return False, "No trailing stop set"
        
            if position.direction.lower() == 'buy':
                if position.current_price <= position.trailing_stop:
                    return True, f"Price {position.current_price:.5f} hit trailing stop {position.trailing_stop:.5f}"
            else:
                if position.current_price >= position.trailing_stop:
                    return True, f"Price {position.current_price:.5f} hit trailing stop {position.trailing_stop:.5f}"
        
            return False, "Trailing stop not triggered"
        except Exception as e:
            logger.error(f"Error in should_trigger: {e}")
            raise


class PartialProfitTaker:
    """Partial profit taking system"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            # Default: 25% at 1R, 25% at 2R, 25% at 3R, 25% runner
            self.profit_levels = self.config.get('profit_levels', [
                {'r_multiple': 1.0, 'exit_percent': 0.25},
                {'r_multiple': 2.0, 'exit_percent': 0.25},
                {'r_multiple': 3.0, 'exit_percent': 0.25},
            ])
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_partial_exit(self, position: Position) -> List[ExitLevel]:
        """Check if partial profit should be taken"""
        try:
            exits = []
        
            # Calculate current profit in R
            risk = abs(position.entry_price - position.stop_loss)
            if risk == 0:
                return exits
        
            if position.direction.lower() == 'buy':
                current_profit = position.current_price - position.entry_price
            else:
                current_profit = position.entry_price - position.current_price
        
            profit_r = current_profit / risk
        
            # Check each profit level
            already_exited = sum(p.get('percent', 0) for p in position.partial_exits)
        
            for level in self.profit_levels:
                r_target = level['r_multiple']
                exit_percent = level['exit_percent']
            
                # Check if this level was already taken
                level_taken = any(
                    p.get('r_multiple') == r_target 
                    for p in position.partial_exits
                )
            
                if not level_taken and profit_r >= r_target:
                    # Calculate exit price for this R level
                    if position.direction.lower() == 'buy':
                        exit_price = position.entry_price + (risk * r_target)
                    else:
                        exit_price = position.entry_price - (risk * r_target)
                
                    exits.append(ExitLevel(
                        price=exit_price,
                        exit_type=ExitType.PARTIAL_PROFIT,
                        quantity_percent=exit_percent,
                        reason=f"Take {exit_percent:.0%} profit at {r_target}R",
                        urgency=ExitUrgency.NORMAL
                    ))
        
            return exits
        except Exception as e:
            logger.error(f"Error in check_partial_exit: {e}")
            raise
    
    def get_remaining_quantity(self, position: Position) -> float:
        """Get remaining quantity after partial exits"""
        try:
            exited = sum(p.get('percent', 0) for p in position.partial_exits)
            return max(0, 1 - exited)
        except Exception as e:
            logger.error(f"Error in get_remaining_quantity: {e}")
            raise


class TimeBasedExit:
    """Time-based exit for stagnant trades"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_hold_hours = self.config.get('max_hold_hours', 48)
            self.stagnant_hours = self.config.get('stagnant_hours', 12)
            self.stagnant_threshold = self.config.get('stagnant_threshold', 0.3)  # 0.3R movement
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_time_exit(self, position: Position) -> Tuple[bool, str, ExitUrgency]:
        """Check if position should be exited due to time"""
        try:
            hold_time = datetime.now() - position.entry_time
            hold_hours = hold_time.total_seconds() / 3600
        
            # Check max hold time
            if hold_hours >= self.max_hold_hours:
                return True, f"Max hold time ({self.max_hold_hours}h) exceeded", ExitUrgency.SOON
        
            # Check for stagnant trade
            if hold_hours >= self.stagnant_hours:
                risk = abs(position.entry_price - position.stop_loss)
                if risk > 0:
                    if position.direction.lower() == 'buy':
                        movement = position.current_price - position.entry_price
                    else:
                        movement = position.entry_price - position.current_price
                
                    movement_r = movement / risk
                
                    if abs(movement_r) < self.stagnant_threshold:
                        return True, f"Stagnant trade ({hold_hours:.1f}h, {movement_r:.2f}R)", ExitUrgency.NORMAL
        
            return False, f"Hold time: {hold_hours:.1f}h", ExitUrgency.OPTIONAL
        except Exception as e:
            logger.error(f"Error in check_time_exit: {e}")
            raise
    
    def get_time_pressure(self, position: Position) -> float:
        """Get time pressure score (0-1)"""
        try:
            hold_time = datetime.now() - position.entry_time
            hold_hours = hold_time.total_seconds() / 3600
        
            return min(hold_hours / self.max_hold_hours, 1.0)
        except Exception as e:
            logger.error(f"Error in get_time_pressure: {e}")
            raise


class VolatilityBasedTP:
    """Volatility-based take profit adjustment"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.base_rr = self.config.get('base_rr', 2.0)  # Base risk/reward
            self.vol_adjustment_factor = self.config.get('vol_adjustment_factor', 0.5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_dynamic_tp(
        self,
        position: Position,
        current_atr: float,
        historical_atr: float
    ) -> Tuple[float, str]:
        """Calculate volatility-adjusted take profit"""
        try:
            risk = abs(position.entry_price - position.stop_loss)
        
            if historical_atr == 0:
                vol_ratio = 1.0
            else:
                vol_ratio = current_atr / historical_atr
        
            # Adjust R/R based on volatility
            # Higher volatility = larger targets
            # Lower volatility = smaller targets
            adjusted_rr = self.base_rr * (1 + (vol_ratio - 1) * self.vol_adjustment_factor)
            adjusted_rr = max(1.5, min(adjusted_rr, 4.0))  # Clamp between 1.5 and 4
        
            # Calculate new TP
            if position.direction.lower() == 'buy':
                new_tp = position.entry_price + (risk * adjusted_rr)
            else:
                new_tp = position.entry_price - (risk * adjusted_rr)
        
            return new_tp, f"Volatility-adjusted TP at {adjusted_rr:.1f}R (vol ratio: {vol_ratio:.2f})"
        except Exception as e:
            logger.error(f"Error in calculate_dynamic_tp: {e}")
            raise
    
    def should_extend_tp(
        self,
        position: Position,
        current_atr: float,
        historical_atr: float
    ) -> Tuple[bool, float, str]:
        """Check if TP should be extended due to increased volatility"""
        try:
            if historical_atr == 0:
                return False, position.take_profit, "No historical ATR"
        
            vol_ratio = current_atr / historical_atr
        
            if vol_ratio > 1.3:  # 30% increase in volatility
                new_tp, reason = self.calculate_dynamic_tp(position, current_atr, historical_atr)
            
                # Only extend, never reduce
                if position.direction.lower() == 'buy':
                    if new_tp > position.take_profit:
                        return True, new_tp, f"Extending TP due to increased volatility: {reason}"
                else:
                    if new_tp < position.take_profit:
                        return True, new_tp, f"Extending TP due to increased volatility: {reason}"
        
            return False, position.take_profit, "No TP extension needed"
        except Exception as e:
            logger.error(f"Error in should_extend_tp: {e}")
            raise


class SupportResistanceExit:
    """Support/resistance based exit management"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.proximity_threshold = self.config.get('proximity_threshold', 0.002)  # 0.2%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def find_exit_levels(
        self,
        position: Position,
        resistance_levels: List[float],
        support_levels: List[float]
    ) -> List[ExitLevel]:
        """Find exit levels based on S/R"""
        try:
            exits = []
        
            if position.direction.lower() == 'buy':
                # For long, look for resistance levels above current price
                for level in resistance_levels:
                    if level > position.current_price:
                        distance = (level - position.current_price) / position.current_price
                    
                        # Calculate profit at this level
                        risk = abs(position.entry_price - position.stop_loss)
                        profit = level - position.entry_price
                        profit_r = profit / risk if risk > 0 else 0
                    
                        if profit_r >= 1.0:  # At least 1R profit
                            exits.append(ExitLevel(
                                price=level,
                                exit_type=ExitType.SUPPORT_RESISTANCE,
                                quantity_percent=0.5,  # Take half at resistance
                                reason=f"Resistance at {level:.5f} ({profit_r:.1f}R)",
                                urgency=ExitUrgency.NORMAL
                            ))
            else:
                # For short, look for support levels below current price
                for level in support_levels:
                    if level < position.current_price:
                        distance = (position.current_price - level) / position.current_price
                    
                        risk = abs(position.entry_price - position.stop_loss)
                        profit = position.entry_price - level
                        profit_r = profit / risk if risk > 0 else 0
                    
                        if profit_r >= 1.0:
                            exits.append(ExitLevel(
                                price=level,
                                exit_type=ExitType.SUPPORT_RESISTANCE,
                                quantity_percent=0.5,
                                reason=f"Support at {level:.5f} ({profit_r:.1f}R)",
                                urgency=ExitUrgency.NORMAL
                            ))
        
            return exits
        except Exception as e:
            logger.error(f"Error in find_exit_levels: {e}")
            raise
    
    def check_level_proximity(
        self,
        position: Position,
        resistance_levels: List[float],
        support_levels: List[float]
    ) -> Tuple[bool, str]:
        """Check if price is near a key level"""
        try:
            if position.direction.lower() == 'buy':
                for level in resistance_levels:
                    distance = abs(position.current_price - level) / level
                    if distance <= self.proximity_threshold:
                        return True, f"Near resistance at {level:.5f}"
            else:
                for level in support_levels:
                    distance = abs(position.current_price - level) / level
                    if distance <= self.proximity_threshold:
                        return True, f"Near support at {level:.5f}"
        
            return False, "Not near key levels"
        except Exception as e:
            logger.error(f"Error in check_level_proximity: {e}")
            raise


class ExitStrategyEnhancer:
    """
    Master exit strategy enhancement system.
    Combines all exit methods.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.trailing_stop = AdaptiveTrailingStop(self.config)
            self.partial_profit = PartialProfitTaker(self.config)
            self.time_exit = TimeBasedExit(self.config)
            self.volatility_tp = VolatilityBasedTP(self.config)
            self.sr_exit = SupportResistanceExit(self.config)
        
            # Configuration
            self.breakeven_activation = self.config.get('breakeven_activation', 1.0)  # 1R to move to breakeven
        
            # Statistics
            self.exit_history: deque = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def manage_position(
        self,
        position: Position,
        current_atr: float,
        historical_atr: float,
        resistance_levels: List[float] = None,
        support_levels: List[float] = None
    ) -> List[ExitRecommendation]:
        """Manage position and generate exit recommendations"""
        try:
            recommendations = []
            resistance_levels = resistance_levels or []
            support_levels = support_levels or []
        
            # 1. Check stop loss
            if self._check_stop_loss(position):
                recommendations.append(ExitRecommendation(
                    symbol=position.symbol,
                    should_exit=True,
                    exit_type=ExitType.STOP_LOSS,
                    exit_price=position.stop_loss,
                    quantity_percent=1.0,
                    urgency=ExitUrgency.IMMEDIATE,
                    reasons=["Stop loss hit"],
                    pnl_estimate=self._calculate_pnl(position, position.stop_loss)
                ))
                return recommendations  # Exit immediately
        
            # 2. Check take profit
            if self._check_take_profit(position):
                recommendations.append(ExitRecommendation(
                    symbol=position.symbol,
                    should_exit=True,
                    exit_type=ExitType.TAKE_PROFIT,
                    exit_price=position.take_profit,
                    quantity_percent=1.0,
                    urgency=ExitUrgency.IMMEDIATE,
                    reasons=["Take profit hit"],
                    pnl_estimate=self._calculate_pnl(position, position.take_profit)
                ))
                return recommendations
        
            # 3. Update trailing stop
            new_trailing, trailing_reason = self.trailing_stop.calculate_trailing_stop(position, current_atr)
            if new_trailing:
                position.trailing_stop = new_trailing
        
            # Check if trailing stop triggered
            trailing_triggered, trailing_msg = self.trailing_stop.should_trigger(position)
            if trailing_triggered:
                recommendations.append(ExitRecommendation(
                    symbol=position.symbol,
                    should_exit=True,
                    exit_type=ExitType.TRAILING_STOP,
                    exit_price=position.trailing_stop,
                    quantity_percent=1.0,
                    urgency=ExitUrgency.IMMEDIATE,
                    reasons=[trailing_msg],
                    pnl_estimate=self._calculate_pnl(position, position.trailing_stop)
                ))
                return recommendations
        
            # 4. Check breakeven
            if not position.breakeven_activated:
                should_breakeven, be_reason = self._check_breakeven(position)
                if should_breakeven:
                    position.breakeven_activated = True
                    position.stop_loss = position.entry_price
                    recommendations.append(ExitRecommendation(
                        symbol=position.symbol,
                        should_exit=False,
                        exit_type=ExitType.BREAKEVEN,
                        exit_price=position.entry_price,
                        quantity_percent=0.0,
                        urgency=ExitUrgency.OPTIONAL,
                        reasons=[be_reason]
                    ))
        
            # 5. Check partial profit taking
            partial_exits = self.partial_profit.check_partial_exit(position)
            for exit_level in partial_exits:
                recommendations.append(ExitRecommendation(
                    symbol=position.symbol,
                    should_exit=True,
                    exit_type=exit_level.exit_type,
                    exit_price=exit_level.price,
                    quantity_percent=exit_level.quantity_percent,
                    urgency=exit_level.urgency,
                    reasons=[exit_level.reason],
                    pnl_estimate=self._calculate_pnl(position, exit_level.price) * exit_level.quantity_percent
                ))
        
            # 6. Check time-based exit
            time_exit, time_reason, time_urgency = self.time_exit.check_time_exit(position)
            if time_exit:
                remaining = self.partial_profit.get_remaining_quantity(position)
                recommendations.append(ExitRecommendation(
                    symbol=position.symbol,
                    should_exit=True,
                    exit_type=ExitType.TIME_BASED,
                    exit_price=position.current_price,
                    quantity_percent=remaining,
                    urgency=time_urgency,
                    reasons=[time_reason],
                    pnl_estimate=self._calculate_pnl(position, position.current_price) * remaining
                ))
        
            # 7. Check S/R based exits
            sr_exits = self.sr_exit.find_exit_levels(position, resistance_levels, support_levels)
            for exit_level in sr_exits:
                # Check if price is near this level
                near_level, _ = self.sr_exit.check_level_proximity(
                    position, resistance_levels, support_levels
                )
                if near_level:
                    recommendations.append(ExitRecommendation(
                        symbol=position.symbol,
                        should_exit=True,
                        exit_type=exit_level.exit_type,
                        exit_price=exit_level.price,
                        quantity_percent=exit_level.quantity_percent,
                        urgency=ExitUrgency.SOON,
                        reasons=[exit_level.reason],
                        pnl_estimate=self._calculate_pnl(position, exit_level.price) * exit_level.quantity_percent
                    ))
        
            # 8. Check if TP should be extended
            should_extend, new_tp, extend_reason = self.volatility_tp.should_extend_tp(
                position, current_atr, historical_atr
            )
            if should_extend:
                position.take_profit = new_tp
                recommendations.append(ExitRecommendation(
                    symbol=position.symbol,
                    should_exit=False,
                    exit_type=ExitType.TAKE_PROFIT,
                    exit_price=new_tp,
                    quantity_percent=0.0,
                    urgency=ExitUrgency.OPTIONAL,
                    reasons=[extend_reason]
                ))
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in manage_position: {e}")
            raise
    
    def _check_stop_loss(self, position: Position) -> bool:
        """Check if stop loss is hit"""
        try:
            if position.direction.lower() == 'buy':
                return position.current_price <= position.stop_loss
            else:
                return position.current_price >= position.stop_loss
        except Exception as e:
            logger.error(f"Error in _check_stop_loss: {e}")
            raise
    
    def _check_take_profit(self, position: Position) -> bool:
        """Check if take profit is hit"""
        try:
            if position.direction.lower() == 'buy':
                return position.current_price >= position.take_profit
            else:
                return position.current_price <= position.take_profit
        except Exception as e:
            logger.error(f"Error in _check_take_profit: {e}")
            raise
    
    def _check_breakeven(self, position: Position) -> Tuple[bool, str]:
        """Check if should move to breakeven"""
        try:
            risk = abs(position.entry_price - position.stop_loss)
            if risk == 0:
                return False, "Zero risk"
        
            if position.direction.lower() == 'buy':
                profit = position.current_price - position.entry_price
            else:
                profit = position.entry_price - position.current_price
        
            profit_r = profit / risk
        
            if profit_r >= self.breakeven_activation:
                return True, f"Move to breakeven at {self.breakeven_activation}R profit"
        
            return False, f"Profit ({profit_r:.2f}R) below breakeven threshold"
        except Exception as e:
            logger.error(f"Error in _check_breakeven: {e}")
            raise
    
    def _calculate_pnl(self, position: Position, exit_price: float) -> float:
        """Calculate P&L for exit price"""
        try:
            if position.direction.lower() == 'buy':
                return (exit_price - position.entry_price) * position.quantity
            else:
                return (position.entry_price - exit_price) * position.quantity
        except Exception as e:
            logger.error(f"Error in _calculate_pnl: {e}")
            raise
    
    def get_exit_summary(self, position: Position) -> Dict[str, Any]:
        """Get exit management summary"""
        try:
            risk = abs(position.entry_price - position.stop_loss)
        
            if position.direction.lower() == 'buy':
                current_profit = position.current_price - position.entry_price
            else:
                current_profit = position.entry_price - position.current_price
        
            profit_r = current_profit / risk if risk > 0 else 0
        
            return {
                'symbol': position.symbol,
                'direction': position.direction,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'trailing_stop': position.trailing_stop,
                'breakeven_activated': position.breakeven_activated,
                'profit_r': profit_r,
                'partial_exits': len(position.partial_exits),
                'remaining_quantity': self.partial_profit.get_remaining_quantity(position),
                'hold_time_hours': (datetime.now() - position.entry_time).total_seconds() / 3600,
                'time_pressure': self.time_exit.get_time_pressure(position)
            }
        except Exception as e:
            logger.error(f"Error in get_exit_summary: {e}")
            raise
    
    def record_exit(self, position: Position, exit_type: ExitType, exit_price: float, quantity_percent: float):
        """Record exit for statistics"""
        try:
            pnl = self._calculate_pnl(position, exit_price) * quantity_percent
        
            self.exit_history.append({
                'timestamp': datetime.now(),
                'symbol': position.symbol,
                'direction': position.direction,
                'exit_type': exit_type.value,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'quantity_percent': quantity_percent,
                'hold_time_hours': (datetime.now() - position.entry_time).total_seconds() / 3600
            })
        except Exception as e:
            logger.error(f"Error in record_exit: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get exit statistics"""
        try:
            if not self.exit_history:
                return {'total_exits': 0}
        
            history = list(self.exit_history)
        
            exit_type_dist = {}
            for exit in history:
                et = exit['exit_type']
                exit_type_dist[et] = exit_type_dist.get(et, 0) + 1
        
            profitable = [e for e in history if e['pnl'] > 0]
            losing = [e for e in history if e['pnl'] < 0]
        
            return {
                'total_exits': len(history),
                'exit_type_distribution': exit_type_dist,
                'profitable_exits': len(profitable),
                'losing_exits': len(losing),
                'avg_pnl': statistics.mean(e['pnl'] for e in history),
                'avg_hold_time_hours': statistics.mean(e['hold_time_hours'] for e in history),
                'total_pnl': sum(e['pnl'] for e in history)
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
