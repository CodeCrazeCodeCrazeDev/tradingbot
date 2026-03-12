"""
Elite Trading Bot - Adaptive Exits

This module provides adaptive exit strategies that adjust based on market conditions,
volatility, and price action.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .exit_strategy import (
    ExitStrategy, ExitType, ExitSignal, ExitReason,
    TrailingStop, TakeProfit, BreakEven
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class FibonacciExitLevels:
    """Fibonacci-based exit levels."""
    entry_price: float
    stop_loss: float
    direction: str  # "long" or "short"
    levels: Dict[float, float] = field(default_factory=dict)  # Fib ratio -> price level
    size_allocation: Dict[float, float] = field(default_factory=dict)  # Fib ratio -> size percentage
    
    def __post_init__(self):
        """Calculate Fibonacci levels after initialization."""
        try:
            self.calculate_levels()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise
    
    def calculate_levels(self):
        """Calculate Fibonacci exit levels."""
        # Common Fibonacci ratios
        try:
            fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618]
        
            # Calculate range
            if self.direction == "long":
                range_size = self.entry_price - self.stop_loss
            
                # Calculate levels
                self.levels = {
                    ratio: self.entry_price + (range_size * ratio)
                    for ratio in fib_ratios
                }
            
                # Default size allocation (can be customized)
                self.size_allocation = {
                    0.382: 20.0,  # 20% at 0.382
                    0.618: 30.0,  # 30% at 0.618
                    1.0: 30.0,    # 30% at 1.0
                    1.618: 20.0   # 20% at 1.618
                }
            else:
                range_size = self.stop_loss - self.entry_price
            
                # Calculate levels
                self.levels = {
                    ratio: self.entry_price - (range_size * ratio)
                    for ratio in fib_ratios
                }
            
                # Default size allocation (can be customized)
                self.size_allocation = {
                    0.382: 20.0,  # 20% at 0.382
                    0.618: 30.0,  # 30% at 0.618
                    1.0: 30.0,    # 30% at 1.0
                    1.618: 20.0   # 20% at 1.618
                }
        except Exception as e:
            logger.error(f"Error in calculate_levels: {e}")
            raise
    
    def get_next_level(self, current_price: float) -> Optional[Tuple[float, float, float]]:
        """
        Get the next exit level based on current price.
        
        Args:
            current_price: Current price
            
        Returns:
            Tuple of (ratio, price, size_percentage) or None if no levels remain
        """
        try:
            if self.direction == "long":
                # Find the next level above current price
                next_levels = [(ratio, price) for ratio, price in self.levels.items() if price > current_price]
                if not next_levels:
                    return None
                
                # Get the closest level
                next_ratio, next_price = min(next_levels, key=lambda x: x[1])
            
                # Get size allocation for this level
                size_percentage = self.size_allocation.get(next_ratio, 0.0)
            
                return next_ratio, next_price, size_percentage
            else:
                # Find the next level below current price
                next_levels = [(ratio, price) for ratio, price in self.levels.items() if price < current_price]
                if not next_levels:
                    return None
                
                # Get the closest level
                next_ratio, next_price = max(next_levels, key=lambda x: x[1])
            
                # Get size allocation for this level
                size_percentage = self.size_allocation.get(next_ratio, 0.0)
            
                return next_ratio, next_price, size_percentage
        except Exception as e:
            logger.error(f"Error in get_next_level: {e}")
            raise
    
    def get_level_by_ratio(self, ratio: float) -> Optional[float]:
        """
        Get price level for a specific Fibonacci ratio.
        
        Args:
            ratio: Fibonacci ratio
            
        Returns:
            Price level or None if ratio not found
        """
        return self.levels.get(ratio)


@dataclass
class TimeBasedExit:
    """Time-based exit configuration."""
    max_duration: timedelta  # Maximum trade duration
    partial_exits: List[Tuple[timedelta, float]] = field(default_factory=list)  # List of (time, size_percentage) tuples
    
    def should_exit(self, entry_time: datetime, current_time: datetime) -> Tuple[bool, float]:
        """
        Check if time-based exit should be triggered.
        
        Args:
            entry_time: Trade entry time
            current_time: Current time
            
        Returns:
            Tuple of (should_exit, size_percentage)
        """
        # Check if max duration reached
        try:
            if current_time - entry_time >= self.max_duration:
                return True, 100.0  # Full exit
        
            # Check for partial exits
            for duration, size_percentage in self.partial_exits:
                if current_time - entry_time >= duration:
                    # Remove this partial exit to avoid triggering again
                    self.partial_exits.remove((duration, size_percentage))
                    return True, size_percentage
        
            return False, 0.0
        except Exception as e:
            logger.error(f"Error in should_exit: {e}")
            raise


class VolatilityBasedExit(ExitStrategy):
    """
    Exit strategy that adapts based on market volatility.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize volatility-based exit strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            super().__init__(config)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            super()._init_default_config()
        
            defaults = {
                "atr_period": 14,  # Period for ATR calculation
                "atr_multiplier": 2.0,  # Multiplier for ATR-based stops
                "volatility_adjustment_factor": 1.0,  # Factor to adjust stops based on volatility
                "min_stop_distance_percent": 0.5,  # Minimum stop distance as percentage
                "max_stop_distance_percent": 5.0,  # Maximum stop distance as percentage
                "enable_volatility_expansion_exit": True,  # Exit on volatility expansion
                "volatility_expansion_threshold": 2.0,  # Threshold for volatility expansion (multiple of average)
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def calculate_volatility_adjusted_stops(self, 
                                         df: pd.DataFrame, 
                                         entry_price: float, 
                                         direction: str) -> Dict[str, float]:
        """
        Calculate volatility-adjusted stop levels.
        
        Args:
            df: OHLCV DataFrame
            entry_price: Entry price
            direction: Trade direction ("long" or "short")
            
        Returns:
            Dictionary of exit levels
        """
        # Calculate ATR
        try:
            atr = self._calculate_atr(df, self.config["atr_period"])
        
            # Calculate stop distance based on ATR
            stop_distance = atr * self.config["atr_multiplier"] * self.config["volatility_adjustment_factor"]
        
            # Apply minimum and maximum constraints
            min_distance = entry_price * (self.config["min_stop_distance_percent"] / 100)
            max_distance = entry_price * (self.config["max_stop_distance_percent"] / 100)
        
            stop_distance = max(min_distance, min(stop_distance, max_distance))
        
            # Calculate stop loss level
            if direction == "long":
                stop_loss = entry_price - stop_distance
            else:
                stop_loss = entry_price + stop_distance
        
            # Calculate take profit based on risk-reward ratio
            risk_reward = self.config["default_risk_reward_ratio"]
        
            if direction == "long":
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * risk_reward)
            else:
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * risk_reward)
        
            # Calculate breakeven level
            breakeven = entry_price
            if self.config["enable_breakeven_stop"]:
                buffer_percent = self.config["breakeven_buffer_percent"]
                if direction == "long":
                    breakeven = entry_price * (1 + buffer_percent / 100)
                else:
                    breakeven = entry_price * (1 - buffer_percent / 100)
        
            return {
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "breakeven": breakeven,
                "atr": atr
            }
        except Exception as e:
            logger.error(f"Error in calculate_volatility_adjusted_stops: {e}")
            raise
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range.
        
        Args:
            df: OHLCV DataFrame
            period: ATR period
            
        Returns:
            ATR value
        """
        try:
            if len(df) < period + 1:
                # Not enough data, use a simple approximation
                return (df['high'] - df['low']).mean()
        
            # Calculate True Range
            high = df['high']
            low = df['low']
            close = df['close'].shift(1)
        
            tr1 = high - low
            tr2 = (high - close).abs()
            tr3 = (low - close).abs()
        
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
            # Calculate ATR
            atr = tr.rolling(window=period).mean().iloc[-1]
        
            return atr
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
    
    def check_volatility_expansion(self, 
                                df: pd.DataFrame, 
                                current_price: float, 
                                direction: str) -> Tuple[bool, Optional[ExitReason]]:
        """
        Check for volatility expansion that might trigger an exit.
        
        Args:
            df: OHLCV DataFrame
            current_price: Current price
            direction: Trade direction ("long" or "short")
            
        Returns:
            Tuple of (should_exit, exit_reason)
        """
        try:
            if not self.config["enable_volatility_expansion_exit"]:
                return False, None
            
            # Calculate current ATR
            current_atr = self._calculate_atr(df, self.config["atr_period"])
        
            # Calculate average ATR over a longer period
            avg_atr = self._calculate_atr(df, self.config["atr_period"] * 3)
        
            # Check for volatility expansion
            if current_atr > avg_atr * self.config["volatility_expansion_threshold"]:
                # Check if expansion is against our position
                last_candle = df.iloc[-1]
            
                if direction == "long" and last_candle['close'] < last_candle['open']:
                    # Bearish candle during volatility expansion in a long position
                    return True, ExitReason.VOLATILITY_EVENT
                elif direction == "short" and last_candle['close'] > last_candle['open']:
                    # Bullish candle during volatility expansion in a short position
                    return True, ExitReason.VOLATILITY_EVENT
        
            return False, None
        except Exception as e:
            logger.error(f"Error in check_volatility_expansion: {e}")
            raise
    
    def update_volatility_trailing_stop(self, 
                                     df: pd.DataFrame, 
                                     entry_price: float, 
                                     current_price: float, 
                                     direction: str,
                                     current_stop: Optional[float] = None) -> float:
        """
        Update trailing stop based on volatility.
        
        Args:
            df: OHLCV DataFrame
            entry_price: Entry price
            current_price: Current price
            direction: Trade direction ("long" or "short")
            current_stop: Current stop level
            
        Returns:
            Updated trailing stop level
        """
        # Calculate ATR
        try:
            atr = self._calculate_atr(df, self.config["atr_period"])
        
            # Create trailing stop configuration
            trailing_config = TrailingStop(
                initial_distance=self.config["atr_multiplier"],
                distance_type="atr",
                activation_threshold=self.config["trailing_stop_activation_percent"]
            )
        
            # Update trailing stop
            return self.update_trailing_stop(
                entry_price=entry_price,
                current_price=current_price,
                direction=direction,
                trailing_config=trailing_config,
                current_stop=current_stop,
                atr=atr
            )
        except Exception as e:
            logger.error(f"Error in update_volatility_trailing_stop: {e}")
            raise


class AdaptiveExitStrategy(ExitStrategy):
    """
    Exit strategy that adapts based on market conditions, volatility,
    and price action.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adaptive exit strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            super().__init__(config)
        
            # Initialize components
            self.volatility_exit = VolatilityBasedExit(self.config.get("volatility_exit_config"))
        
            # Active trades tracking
            self.active_trades: Dict[str, Dict[str, Any]] = {}
        
            logger.info("AdaptiveExitStrategy initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            super()._init_default_config()
        
            defaults = {
                "enable_fibonacci_exits": True,  # Enable Fibonacci-based exits
                "enable_time_based_exits": True,  # Enable time-based exits
                "max_trade_duration_hours": 48,  # Maximum trade duration in hours
                "partial_exit_times": [  # List of (hours, percentage) tuples
                    (4, 25.0),  # 25% after 4 hours
                    (12, 25.0),  # 25% after 12 hours
                    (24, 25.0)   # 25% after 24 hours
                ],
                "enable_market_condition_exits": True,  # Exit based on market conditions
                "trend_change_exit": True,  # Exit on trend change
                "support_resistance_exit": True,  # Exit at support/resistance levels
                "enable_dynamic_risk_reward": True,  # Dynamically adjust risk-reward ratio
                "initial_risk_reward_ratio": 2.0,  # Initial risk-reward ratio
                "max_risk_reward_ratio": 5.0,  # Maximum risk-reward ratio
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
                     size: float = 1.0) -> Dict[str, Any]:
        """
        Register a new trade for adaptive exit management.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Symbol
            entry_price: Entry price
            direction: Trade direction ("long" or "short")
            stop_loss: Initial stop loss level
            take_profit: Initial take profit level
            entry_time: Entry time
            size: Position size
            
        Returns:
            Trade information dictionary
        """
        # Create Fibonacci exit levels
        try:
            fib_levels = FibonacciExitLevels(
                entry_price=entry_price,
                stop_loss=stop_loss,
                direction=direction
            )
        
            # Create time-based exit configuration
            time_exits = []
            if self.config["enable_time_based_exits"]:
                time_exits = [
                    (timedelta(hours=hours), percentage)
                    for hours, percentage in self.config["partial_exit_times"]
                ]
            
            time_based_exit = TimeBasedExit(
                max_duration=timedelta(hours=self.config["max_trade_duration_hours"]),
                partial_exits=time_exits
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
                "size": size,
                "remaining_size": size,
                "fib_levels": fib_levels,
                "time_based_exit": time_based_exit,
                "trailing_stop": None,
                "breakeven_activated": False,
                "partial_exits": [],
                "last_update_time": entry_time
            }
        
            # Store trade information
            self.active_trades[trade_id] = trade_info
        
            logger.info(f"Registered trade {trade_id} for adaptive exit management")
        
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
        Update trade and check for exit signals.
        
        Args:
            trade_id: Trade identifier
            current_price: Current price
            current_time: Current time
            market_data: Optional market data DataFrame
            
        Returns:
            List of exit signals
        """
        try:
            if trade_id not in self.active_trades:
                logger.warning(f"Trade {trade_id} not found")
                return []
            
            # Get trade information
            trade = self.active_trades[trade_id]
        
            # Update last update time
            trade["last_update_time"] = current_time
        
            # Check for exit signals
            exit_signals = []
        
            # Check stop loss and take profit
            basic_exit, exit_reason, exit_price = self.check_exit_conditions(
                entry_price=trade["entry_price"],
                current_price=current_price,
                direction=trade["direction"],
                stop_loss=trade["stop_loss"],
                take_profit=trade["take_profit"],
                trailing_stop=trade.get("trailing_stop")
            )
        
            if basic_exit:
                # Create exit signal
                signal = self.create_exit_signal(
                    symbol=trade["symbol"],
                    exit_reason=exit_reason,
                    exit_price=exit_price,
                    position_id=trade_id,
                    direction=trade["direction"]
                )
            
                exit_signals.append(signal)
            
                # Remove trade from active trades
                del self.active_trades[trade_id]
            
                return exit_signals
        
            # Update trailing stop if enabled
            if self.config["enable_trailing_stop"] and market_data is not None:
                new_trailing_stop = self.volatility_exit.update_volatility_trailing_stop(
                    df=market_data,
                    entry_price=trade["entry_price"],
                    current_price=current_price,
                    direction=trade["direction"],
                    current_stop=trade.get("trailing_stop")
                )
            
                trade["trailing_stop"] = new_trailing_stop
        
            # Check breakeven stop
            if self.config["enable_breakeven_stop"] and not trade["breakeven_activated"]:
                should_activate, breakeven_level = self.check_breakeven_stop(
                    entry_price=trade["entry_price"],
                    current_price=current_price,
                    direction=trade["direction"],
                    stop_loss=trade["stop_loss"]
                )
            
                if should_activate:
                    trade["stop_loss"] = breakeven_level
                    trade["breakeven_activated"] = True
                
                    logger.info(f"Activated breakeven stop for trade {trade_id} at {breakeven_level}")
        
            # Check Fibonacci exit levels
            if self.config["enable_fibonacci_exits"]:
                next_level = trade["fib_levels"].get_next_level(current_price)
            
                if next_level:
                    ratio, price, size_percentage = next_level
                
                    # Check if price has reached this level
                    level_reached = False
                
                    if trade["direction"] == "long" and current_price >= price:
                        level_reached = True
                    elif trade["direction"] == "short" and current_price <= price:
                        level_reached = True
                
                    if level_reached:
                        # Calculate exit size
                        exit_size = trade["remaining_size"] * (size_percentage / 100)
                    
                        # Create partial exit signal
                        signal = ExitSignal(
                            id=f"fib_exit_{trade_id}_{ratio}",
                            symbol=trade["symbol"],
                            timestamp=current_time,
                            exit_type=ExitType.FIBONACCI_EXIT,
                            exit_reason=ExitReason.TARGET_REACHED,
                            price=price,
                            position_id=trade_id,
                            direction=trade["direction"],
                            size_percentage=size_percentage,
                            confidence=1.0,
                            notes=f"Fibonacci exit at {ratio} ratio"
                        )
                    
                        exit_signals.append(signal)
                    
                        # Update remaining size
                        trade["remaining_size"] -= exit_size
                    
                        # Record partial exit
                        trade["partial_exits"].append({
                            "time": current_time,
                            "price": price,
                            "size": exit_size,
                            "ratio": ratio
                        })
                    
                        logger.info(f"Fibonacci exit triggered for trade {trade_id} at ratio {ratio}")
        
            # Check time-based exits
            if self.config["enable_time_based_exits"]:
                should_exit, size_percentage = trade["time_based_exit"].should_exit(
                    entry_time=trade["entry_time"],
                    current_time=current_time
                )
            
                if should_exit and size_percentage > 0:
                    # Calculate exit size
                    exit_size = trade["remaining_size"] * (size_percentage / 100)
                
                    # Create time-based exit signal
                    signal = ExitSignal(
                        id=f"time_exit_{trade_id}_{len(trade['partial_exits'])}",
                        symbol=trade["symbol"],
                        timestamp=current_time,
                        exit_type=ExitType.TIME_BASED_EXIT,
                        exit_reason=ExitReason.TIME_EXIT,
                        price=current_price,
                        position_id=trade_id,
                        direction=trade["direction"],
                        size_percentage=size_percentage,
                        confidence=1.0,
                        notes=f"Time-based exit after {(current_time - trade['entry_time']).total_seconds() / 3600:.1f} hours"
                    )
                
                    exit_signals.append(signal)
                
                    # Update remaining size
                    trade["remaining_size"] -= exit_size
                
                    # Record partial exit
                    trade["partial_exits"].append({
                        "time": current_time,
                        "price": current_price,
                        "size": exit_size,
                        "time_based": True
                    })
                
                    logger.info(f"Time-based exit triggered for trade {trade_id}")
        
            # Check volatility expansion exit
            if market_data is not None:
                should_exit, exit_reason = self.volatility_exit.check_volatility_expansion(
                    df=market_data,
                    current_price=current_price,
                    direction=trade["direction"]
                )
            
                if should_exit:
                    # Create volatility expansion exit signal
                    signal = self.create_exit_signal(
                        symbol=trade["symbol"],
                        exit_reason=exit_reason,
                        exit_price=current_price,
                        position_id=trade_id,
                        direction=trade["direction"]
                    )
                
                    exit_signals.append(signal)
                
                    # Remove trade from active trades
                    del self.active_trades[trade_id]
                
                    logger.info(f"Volatility expansion exit triggered for trade {trade_id}")
                
                    return exit_signals
        
            return exit_signals
        except Exception as e:
            logger.error(f"Error in update_trade: {e}")
            raise
    
    def get_trade_info(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific trade.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Trade information dictionary or None if not found
        """
        return self.active_trades.get(trade_id)
    
    def get_active_trades(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active trades.
        
        Returns:
            Dictionary of trade_id -> trade_info
        """
        return self.active_trades.copy()
    
    def remove_trade(self, trade_id: str) -> bool:
        """
        Remove a trade from active management.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            True if trade was removed, False if not found
        """
        try:
            if trade_id in self.active_trades:
                del self.active_trades[trade_id]
                logger.info(f"Removed trade {trade_id} from active management")
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in remove_trade: {e}")
            raise
