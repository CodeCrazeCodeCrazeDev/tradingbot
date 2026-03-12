"""
Elite Trading Bot - Dynamic Trade Management

This module provides dynamic trade management capabilities for the Elite Trading Bot,
enabling sophisticated position scaling and partial exit strategies.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd

from .exit_strategy import ExitStrategy, ExitType, ExitSignal, ExitReason
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class TradeHealth(enum.Enum):
    """Trade health status."""
    EXCELLENT = "excellent"    # Trade performing very well
    GOOD = "good"             # Trade performing well
    NEUTRAL = "neutral"       # Trade performing as expected
    POOR = "poor"             # Trade underperforming
    CRITICAL = "critical"     # Trade in critical condition


@dataclass
class PartialExitRule:
    """Rule for partial position exits."""
    trigger_condition: str    # "profit_percent", "profit_points", "time", "indicator", "custom"
    trigger_value: float     # Value for the trigger condition
    exit_percentage: float   # Percentage of position to exit (0-100)
    description: str = ""    # Description of the rule
    executed: bool = False   # Whether this rule has been executed
    execution_time: Optional[datetime] = None
    execution_price: Optional[float] = None


@dataclass
class ScaleLevel:
    """Scale-in/scale-out level configuration."""
    price_level: float       # Price level for scaling
    size_percentage: float   # Percentage of total position size
    is_entry: bool          # True for scale-in, False for scale-out
    condition: str = "price"  # "price", "indicator", "time", "custom"
    executed: bool = False   # Whether this level has been executed
    execution_time: Optional[datetime] = None


class PartialExitStrategy:
    """
    Strategy for managing partial exits based on various conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize partial exit strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Partial exit rules
            self.exit_rules: List[PartialExitRule] = []
        
            logger.info("PartialExitStrategy initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "default_partial_exits": [
                    {"condition": "profit_percent", "value": 1.0, "percentage": 25.0},  # 25% at 1% profit
                    {"condition": "profit_percent", "value": 2.0, "percentage": 25.0},  # 25% at 2% profit
                    {"condition": "profit_percent", "value": 3.0, "percentage": 25.0},  # 25% at 3% profit
                ],
                "enable_time_based_exits": True,
                "time_based_exits": [
                    {"hours": 4, "percentage": 20.0},   # 20% after 4 hours
                    {"hours": 12, "percentage": 30.0},  # 30% after 12 hours
                ],
                "enable_indicator_exits": True,
                "rsi_overbought_exit": 75.0,  # Exit when RSI > 75 (for long positions)
                "rsi_oversold_exit": 25.0,    # Exit when RSI < 25 (for short positions)
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def add_exit_rule(self, rule: PartialExitRule):
        """
        Add a partial exit rule.
        
        Args:
            rule: Partial exit rule to add
        """
        try:
            self.exit_rules.append(rule)
        
            # Sort rules by trigger value (ascending)
            self.exit_rules.sort(key=lambda x: x.trigger_value)
        except Exception as e:
            logger.error(f"Error in add_exit_rule: {e}")
            raise
    
    def create_default_rules(self, entry_price: float, direction: str):
        """
        Create default partial exit rules.
        
        Args:
            entry_price: Entry price
            direction: Trade direction ("long" or "short")
        """
        # Clear existing rules
        try:
            self.exit_rules = []
        
            # Add profit-based exits
            for exit_config in self.config["default_partial_exits"]:
                rule = PartialExitRule(
                    trigger_condition=exit_config["condition"],
                    trigger_value=exit_config["value"],
                    exit_percentage=exit_config["percentage"],
                    description=f"Partial exit at {exit_config['value']}% profit"
                )
                self.add_exit_rule(rule)
        
            # Add time-based exits if enabled
            if self.config["enable_time_based_exits"]:
                for time_config in self.config["time_based_exits"]:
                    rule = PartialExitRule(
                        trigger_condition="time",
                        trigger_value=time_config["hours"],
                        exit_percentage=time_config["percentage"],
                        description=f"Time-based exit after {time_config['hours']} hours"
                    )
                    self.add_exit_rule(rule)
        except Exception as e:
            logger.error(f"Error in create_default_rules: {e}")
            raise
    
    def check_exit_rules(self, 
                        entry_price: float, 
                        entry_time: datetime,
                        current_price: float, 
                        current_time: datetime,
                        direction: str,
                        market_data: Optional[pd.DataFrame] = None) -> List[PartialExitRule]:
        """
        Check which partial exit rules should be triggered.
        
        Args:
            entry_price: Entry price
            entry_time: Entry time
            current_price: Current price
            current_time: Current time
            direction: Trade direction ("long" or "short")
            market_data: Optional market data for indicator-based exits
            
        Returns:
            List of triggered exit rules
        """
        try:
            triggered_rules = []
        
            for rule in self.exit_rules:
                if rule.executed:
                    continue  # Skip already executed rules
                
                should_trigger = False
            
                if rule.trigger_condition == "profit_percent":
                    # Calculate profit percentage
                    if direction == "long":
                        profit_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        profit_pct = ((entry_price - current_price) / entry_price) * 100
                
                    should_trigger = profit_pct >= rule.trigger_value
                
                elif rule.trigger_condition == "profit_points":
                    # Calculate profit in points
                    if direction == "long":
                        profit_points = current_price - entry_price
                    else:
                        profit_points = entry_price - current_price
                
                    should_trigger = profit_points >= rule.trigger_value
                
                elif rule.trigger_condition == "time":
                    # Check time elapsed
                    hours_elapsed = (current_time - entry_time).total_seconds() / 3600
                    should_trigger = hours_elapsed >= rule.trigger_value
                
                elif rule.trigger_condition == "indicator" and market_data is not None:
                    # Check indicator-based conditions
                    should_trigger = self._check_indicator_condition(
                        rule, direction, market_data
                    )
            
                if should_trigger:
                    # Mark rule as executed
                    rule.executed = True
                    rule.execution_time = current_time
                    rule.execution_price = current_price
                
                    triggered_rules.append(rule)
        
            return triggered_rules
        except Exception as e:
            logger.error(f"Error in check_exit_rules: {e}")
            raise
    
    def _check_indicator_condition(self, 
                                 rule: PartialExitRule, 
                                 direction: str,
                                 market_data: pd.DataFrame) -> bool:
        """
        Check indicator-based exit conditions.
        
        Args:
            rule: Partial exit rule
            direction: Trade direction
            market_data: Market data DataFrame
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            if not self.config["enable_indicator_exits"]:
                return False
            
            # Calculate RSI if not present
            if 'rsi' not in market_data.columns:
                market_data = market_data.copy()
                delta = market_data['close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
            
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
            
                rs = avg_gain / avg_loss
                market_data['rsi'] = 100 - (100 / (1 + rs))
        
            # Get latest RSI value
            if len(market_data) == 0 or market_data['rsi'].iloc[-1] is None:
                return False
            
            current_rsi = market_data['rsi'].iloc[-1]
        
            # Check RSI-based conditions
            if direction == "long" and current_rsi > self.config["rsi_overbought_exit"]:
                return True
            elif direction == "short" and current_rsi < self.config["rsi_oversold_exit"]:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _check_indicator_condition: {e}")
            raise


class ScaledExitStrategy:
    """
    Strategy for scaling in and out of positions at predefined levels.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize scaled exit strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Scale levels
            self.scale_levels: List[ScaleLevel] = []
        
            logger.info("ScaledExitStrategy initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "default_scale_out_levels": [
                    {"profit_percent": 1.0, "size_percent": 20.0},
                    {"profit_percent": 2.0, "size_percent": 30.0},
                    {"profit_percent": 3.0, "size_percent": 25.0},
                    {"profit_percent": 5.0, "size_percent": 25.0},
                ],
                "fibonacci_scaling": True,
                "fibonacci_levels": [0.382, 0.618, 1.0, 1.618],
                "fibonacci_allocations": [25.0, 30.0, 25.0, 20.0],  # Percentage allocations
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def create_scale_out_levels(self, 
                              entry_price: float, 
                              stop_loss: float,
                              direction: str):
        """
        Create scale-out levels based on configuration.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss level
            direction: Trade direction ("long" or "short")
        """
        # Clear existing levels
        try:
            self.scale_levels = []
        
            if self.config["fibonacci_scaling"]:
                # Create Fibonacci-based scale levels
                self._create_fibonacci_levels(entry_price, stop_loss, direction)
            else:
                # Create percentage-based scale levels
                self._create_percentage_levels(entry_price, direction)
        except Exception as e:
            logger.error(f"Error in create_scale_out_levels: {e}")
            raise
    
    def _create_fibonacci_levels(self, 
                               entry_price: float, 
                               stop_loss: float,
                               direction: str):
        """
        Create Fibonacci-based scale-out levels.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss level
            direction: Trade direction
        """
        # Calculate risk (distance from entry to stop)
        try:
            if direction == "long":
                risk = entry_price - stop_loss
            else:
                risk = stop_loss - entry_price
        
            # Create levels at Fibonacci extensions
            fib_levels = self.config["fibonacci_levels"]
            fib_allocations = self.config["fibonacci_allocations"]
        
            for i, (fib_ratio, allocation) in enumerate(zip(fib_levels, fib_allocations)):
                if direction == "long":
                    price_level = entry_price + (risk * fib_ratio)
                else:
                    price_level = entry_price - (risk * fib_ratio)
            
                level = ScaleLevel(
                    price_level=price_level,
                    size_percentage=allocation,
                    is_entry=False,  # Scale-out level
                    condition="price"
                )
            
                self.scale_levels.append(level)
        except Exception as e:
            logger.error(f"Error in _create_fibonacci_levels: {e}")
            raise
    
    def _create_percentage_levels(self, entry_price: float, direction: str):
        """
        Create percentage-based scale-out levels.
        
        Args:
            entry_price: Entry price
            direction: Trade direction
        """
        try:
            for level_config in self.config["default_scale_out_levels"]:
                profit_percent = level_config["profit_percent"]
                size_percent = level_config["size_percent"]
            
                if direction == "long":
                    price_level = entry_price * (1 + profit_percent / 100)
                else:
                    price_level = entry_price * (1 - profit_percent / 100)
            
                level = ScaleLevel(
                    price_level=price_level,
                    size_percentage=size_percent,
                    is_entry=False,  # Scale-out level
                    condition="price"
                )
            
                self.scale_levels.append(level)
        except Exception as e:
            logger.error(f"Error in _create_percentage_levels: {e}")
            raise
    
    def check_scale_levels(self, 
                         current_price: float, 
                         direction: str) -> List[ScaleLevel]:
        """
        Check which scale levels should be triggered.
        
        Args:
            current_price: Current price
            direction: Trade direction
            
        Returns:
            List of triggered scale levels
        """
        try:
            triggered_levels = []
        
            for level in self.scale_levels:
                if level.executed:
                    continue  # Skip already executed levels
                
                should_trigger = False
            
                if level.condition == "price":
                    if direction == "long" and not level.is_entry:
                        # Scale-out level for long position
                        should_trigger = current_price >= level.price_level
                    elif direction == "short" and not level.is_entry:
                        # Scale-out level for short position
                        should_trigger = current_price <= level.price_level
                    elif direction == "long" and level.is_entry:
                        # Scale-in level for long position (price pullback)
                        should_trigger = current_price <= level.price_level
                    elif direction == "short" and level.is_entry:
                        # Scale-in level for short position (price bounce)
                        should_trigger = current_price >= level.price_level
            
                if should_trigger:
                    # Mark level as executed
                    level.executed = True
                    level.execution_time = datetime.now()
                
                    triggered_levels.append(level)
        
            return triggered_levels
        except Exception as e:
            logger.error(f"Error in check_scale_levels: {e}")
            raise


class DynamicTradeManager:
    """
    Dynamic trade manager that combines multiple exit strategies and
    adapts based on trade performance and market conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize dynamic trade manager.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Initialize strategies
            self.partial_exit_strategy = PartialExitStrategy(
                self.config.get("partial_exit_config")
            )
            self.scaled_exit_strategy = ScaledExitStrategy(
                self.config.get("scaled_exit_config")
            )
        
            # Active trades
            self.active_trades: Dict[str, Dict[str, Any]] = {}
        
            logger.info("DynamicTradeManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "enable_partial_exits": True,
                "enable_scaled_exits": True,
                "enable_trade_health_monitoring": True,
                "health_check_interval_minutes": 5,
                "poor_performance_threshold": -0.5,  # -0.5% performance threshold
                "excellent_performance_threshold": 2.0,  # 2% performance threshold
                "enable_dynamic_stop_adjustment": True,
                "stop_adjustment_factor": 0.5,  # Factor for adjusting stops based on performance
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def register_trade(self, 
                     trade_id: str,
                     symbol: str,
                     entry_price: float,
                     direction: str,
                     stop_loss: float,
                     take_profit: float,
                     entry_time: datetime,
                     position_size: float = 1.0) -> Dict[str, Any]:
        """
        Register a trade for dynamic management.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            entry_price: Entry price
            direction: Trade direction ("long" or "short")
            stop_loss: Initial stop loss
            take_profit: Initial take profit
            entry_time: Entry time
            position_size: Position size
            
        Returns:
            Trade information dictionary
        """
        # Create partial exit rules
        try:
            if self.config["enable_partial_exits"]:
                self.partial_exit_strategy.create_default_rules(entry_price, direction)
        
            # Create scale-out levels
            if self.config["enable_scaled_exits"]:
                self.scaled_exit_strategy.create_scale_out_levels(
                    entry_price, stop_loss, direction
                )
        
            # Create trade information
            trade_info = {
                "id": trade_id,
                "symbol": symbol,
                "entry_price": entry_price,
                "direction": direction,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "entry_time": entry_time,
                "position_size": position_size,
                "remaining_size": position_size,
                "partial_exits": [],
                "scale_exits": [],
                "health": TradeHealth.NEUTRAL,
                "last_health_check": entry_time,
                "performance_history": [],
                "notes": []
            }
        
            # Store trade
            self.active_trades[trade_id] = trade_info
        
            logger.info(f"Registered trade {trade_id} for dynamic management")
        
            return trade_info
        except Exception as e:
            logger.error(f"Error in register_trade: {e}")
            raise
    
    def update_trade(self, 
                   trade_id: str,
                   current_price: float,
                   current_time: datetime,
                   market_data: Optional[pd.DataFrame] = None) -> List[ExitSignal]:
        """
        Update trade and generate exit signals.
        
        Args:
            trade_id: Trade identifier
            current_price: Current price
            current_time: Current time
            market_data: Optional market data
            
        Returns:
            List of exit signals
        """
        try:
            if trade_id not in self.active_trades:
                logger.warning(f"Trade {trade_id} not found")
                return []
        
            trade = self.active_trades[trade_id]
            exit_signals = []
        
            # Update trade health
            if self.config["enable_trade_health_monitoring"]:
                self._update_trade_health(trade, current_price, current_time)
        
            # Check partial exit rules
            if self.config["enable_partial_exits"]:
                triggered_rules = self.partial_exit_strategy.check_exit_rules(
                    entry_price=trade["entry_price"],
                    entry_time=trade["entry_time"],
                    current_price=current_price,
                    current_time=current_time,
                    direction=trade["direction"],
                    market_data=market_data
                )
            
                for rule in triggered_rules:
                    # Create exit signal
                    signal = ExitSignal(
                        id=f"partial_{trade_id}_{len(trade['partial_exits'])}",
                        symbol=trade["symbol"],
                        timestamp=current_time,
                        exit_type=ExitType.PARTIAL_EXIT,
                        exit_reason=ExitReason.TARGET_REACHED,
                        price=current_price,
                        position_id=trade_id,
                        direction=trade["direction"],
                        size_percentage=rule.exit_percentage,
                        confidence=1.0,
                        notes=rule.description
                    )
                
                    exit_signals.append(signal)
                
                    # Update trade
                    exit_size = trade["remaining_size"] * (rule.exit_percentage / 100)
                    trade["remaining_size"] -= exit_size
                
                    trade["partial_exits"].append({
                        "time": current_time,
                        "price": current_price,
                        "size": exit_size,
                        "rule": rule.description
                    })
        
            # Check scale-out levels
            if self.config["enable_scaled_exits"]:
                triggered_levels = self.scaled_exit_strategy.check_scale_levels(
                    current_price=current_price,
                    direction=trade["direction"]
                )
            
                for level in triggered_levels:
                    if not level.is_entry:  # Only process scale-out levels
                        # Create exit signal
                        signal = ExitSignal(
                            id=f"scale_{trade_id}_{len(trade['scale_exits'])}",
                            symbol=trade["symbol"],
                            timestamp=current_time,
                            exit_type=ExitType.SCALED_TAKE_PROFIT,
                            exit_reason=ExitReason.TARGET_REACHED,
                            price=level.price_level,
                            position_id=trade_id,
                            direction=trade["direction"],
                            size_percentage=level.size_percentage,
                            confidence=1.0,
                            notes=f"Scale-out at {level.price_level}"
                        )
                    
                        exit_signals.append(signal)
                    
                        # Update trade
                        exit_size = trade["remaining_size"] * (level.size_percentage / 100)
                        trade["remaining_size"] -= exit_size
                    
                        trade["scale_exits"].append({
                            "time": current_time,
                            "price": level.price_level,
                            "size": exit_size,
                            "level": level.price_level
                        })
        
            # Adjust stops based on performance if enabled
            if self.config["enable_dynamic_stop_adjustment"]:
                self._adjust_stops_based_on_performance(trade, current_price)
        
            return exit_signals
        except Exception as e:
            logger.error(f"Error in update_trade: {e}")
            raise
    
    def _update_trade_health(self, 
                           trade: Dict[str, Any], 
                           current_price: float,
                           current_time: datetime):
        """
        Update trade health status.
        
        Args:
            trade: Trade information dictionary
            current_price: Current price
            current_time: Current time
        """
        # Check if it's time for health check
        try:
            time_since_last_check = current_time - trade["last_health_check"]
            check_interval = timedelta(minutes=self.config["health_check_interval_minutes"])
        
            if time_since_last_check < check_interval:
                return  # Too soon for another check
        
            # Calculate current performance
            entry_price = trade["entry_price"]
            direction = trade["direction"]
        
            if direction == "long":
                performance_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                performance_pct = ((entry_price - current_price) / entry_price) * 100
        
            # Record performance
            trade["performance_history"].append({
                "time": current_time,
                "price": current_price,
                "performance_pct": performance_pct
            })
        
            # Determine health status
            if performance_pct >= self.config["excellent_performance_threshold"]:
                new_health = TradeHealth.EXCELLENT
            elif performance_pct >= 1.0:
                new_health = TradeHealth.GOOD
            elif performance_pct >= 0.0:
                new_health = TradeHealth.NEUTRAL
            elif performance_pct >= self.config["poor_performance_threshold"]:
                new_health = TradeHealth.POOR
            else:
                new_health = TradeHealth.CRITICAL
        
            # Update health if changed
            if new_health != trade["health"]:
                old_health = trade["health"]
                trade["health"] = new_health
            
                trade["notes"].append({
                    "time": current_time,
                    "message": f"Health changed from {old_health.value} to {new_health.value}",
                    "performance": performance_pct
                })
            
                logger.info(f"Trade {trade['id']} health changed to {new_health.value}")
        
            # Update last health check time
            trade["last_health_check"] = current_time
        except Exception as e:
            logger.error(f"Error in _update_trade_health: {e}")
            raise
    
    def _adjust_stops_based_on_performance(self, 
                                         trade: Dict[str, Any], 
                                         current_price: float):
        """
        Adjust stop loss based on trade performance.
        
        Args:
            trade: Trade information dictionary
            current_price: Current price
        """
        # Only adjust for excellent performing trades
        try:
            if trade["health"] != TradeHealth.EXCELLENT:
                return
        
            # Calculate potential new stop level
            entry_price = trade["entry_price"]
            direction = trade["direction"]
            adjustment_factor = self.config["stop_adjustment_factor"]
        
            if direction == "long":
                # Move stop closer to current price for long positions
                distance_to_current = current_price - trade["stop_loss"]
                new_stop = trade["stop_loss"] + (distance_to_current * adjustment_factor)
            
                # Only move stop up (never down)
                if new_stop > trade["stop_loss"]:
                    trade["stop_loss"] = new_stop
                
                    trade["notes"].append({
                        "time": datetime.now(),
                        "message": f"Stop loss adjusted to {new_stop} due to excellent performance"
                    })
            else:
                # Move stop closer to current price for short positions
                distance_to_current = trade["stop_loss"] - current_price
                new_stop = trade["stop_loss"] - (distance_to_current * adjustment_factor)
            
                # Only move stop down (never up)
                if new_stop < trade["stop_loss"]:
                    trade["stop_loss"] = new_stop
                
                    trade["notes"].append({
                        "time": datetime.now(),
                        "message": f"Stop loss adjusted to {new_stop} due to excellent performance"
                    })
        except Exception as e:
            logger.error(f"Error in _adjust_stops_based_on_performance: {e}")
            raise
    
    def get_trade_summary(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary information for a trade.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Trade summary dictionary or None if not found
        """
        try:
            if trade_id not in self.active_trades:
                return None
        
            trade = self.active_trades[trade_id]
        
            # Calculate current performance if we have recent data
            current_performance = 0.0
            if trade["performance_history"]:
                current_performance = trade["performance_history"][-1]["performance_pct"]
        
            # Calculate total exits
            total_exits = len(trade["partial_exits"]) + len(trade["scale_exits"])
        
            summary = {
                "id": trade["id"],
                "symbol": trade["symbol"],
                "direction": trade["direction"],
                "entry_price": trade["entry_price"],
                "current_stop_loss": trade["stop_loss"],
                "take_profit": trade["take_profit"],
                "position_size": trade["position_size"],
                "remaining_size": trade["remaining_size"],
                "health": trade["health"].value,
                "current_performance_pct": current_performance,
                "total_exits": total_exits,
                "partial_exits_count": len(trade["partial_exits"]),
                "scale_exits_count": len(trade["scale_exits"]),
                "notes_count": len(trade["notes"])
            }
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_trade_summary: {e}")
            raise
    
    def get_all_trades_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary for all active trades.
        
        Returns:
            List of trade summaries
        """
        try:
            summaries = []
        
            for trade_id in self.active_trades:
                summary = self.get_trade_summary(trade_id)
                if summary:
                    summaries.append(summary)
        
            return summaries
        except Exception as e:
            logger.error(f"Error in get_all_trades_summary: {e}")
            raise
    
    def remove_trade(self, trade_id: str) -> bool:
        """
        Remove a trade from management.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            True if trade was removed, False if not found
        """
        try:
            if trade_id in self.active_trades:
                del self.active_trades[trade_id]
                logger.info(f"Removed trade {trade_id} from dynamic management")
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in remove_trade: {e}")
            raise
