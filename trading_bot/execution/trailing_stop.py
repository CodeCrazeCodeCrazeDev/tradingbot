"""
TRAILING STOP MODULE - P0 CRITICAL FIX
============================================================

Implements trailing stop loss functionality to capture more profit.

Features:
- Dynamic stop loss adjustment
- ATR-based trailing distance
- Profit protection
- Breakeven stop

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional

import numpy as np
from loguru import logger
import numpy


class TradeDirection(Enum):
    """Trade direction."""
    LONG = auto()
    SHORT = auto()


@dataclass
class TrailingStopState:
    """State of trailing stop."""
    entry_price: float
    initial_stop: float
    current_stop: float
    highest_price: float  # For long
    lowest_price: float   # For short
    profit_pips: float
    is_breakeven: bool
    timestamp: datetime


class TrailingStop:
    """Manages trailing stop loss."""
    
    def __init__(self, direction: TradeDirection = TradeDirection.LONG,
                 atr_multiplier: float = 2.0):
        """
        Initialize trailing stop.
        
        Args:
            direction: Trade direction (LONG or SHORT)
            atr_multiplier: ATR multiplier for stop distance (default 2.0)
        """
        try:
            self.direction = direction
            self.atr_multiplier = atr_multiplier
        
            self.entry_price = None
            self.initial_stop = None
            self.current_stop = None
            self.highest_price = None  # For long
            self.lowest_price = None   # For short
            self.is_breakeven = False
            self.state_history = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def initialize(self, entry_price: float, atr: float):
        """
        Initialize trailing stop.
        
        Args:
            entry_price: Entry price
            atr: Average True Range
        """
        try:
            self.entry_price = entry_price
        
            if self.direction == TradeDirection.LONG:
                self.initial_stop = entry_price - (atr * self.atr_multiplier)
                self.current_stop = self.initial_stop
                self.highest_price = entry_price
            else:  # SHORT
                self.initial_stop = entry_price + (atr * self.atr_multiplier)
                self.current_stop = self.initial_stop
                self.lowest_price = entry_price
        
            logger.info(f"Trailing stop initialized: entry={entry_price}, stop={self.current_stop}, atr={atr}")
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def update(self, current_price: float, atr: float) -> float:
        """
        Update trailing stop based on price movement.
        
        Args:
            current_price: Current market price
            atr: Current ATR
            
        Returns:
            Updated stop loss price
        """
        try:
            if self.entry_price is None:
                return None
        
            if self.direction == TradeDirection.LONG:
                return self._update_long(current_price, atr)
            else:
                return self._update_short(current_price, atr)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _update_long(self, current_price: float, atr: float) -> float:
        """Update trailing stop for long position."""
        try:
            if current_price > self.highest_price:
                self.highest_price = current_price
                # Move stop up by ATR
                new_stop = current_price - (atr * self.atr_multiplier)
                self.current_stop = max(self.current_stop, new_stop)
            
                logger.debug(f"Long trailing stop updated: price={current_price}, stop={self.current_stop}")
        
            # Check if breakeven
            if current_price > self.entry_price and not self.is_breakeven:
                self.is_breakeven = True
                # Move stop to breakeven
                self.current_stop = max(self.current_stop, self.entry_price)
                logger.info(f"Breakeven stop activated: {self.current_stop}")
        
            return self.current_stop
        except Exception as e:
            logger.error(f"Error in _update_long: {e}")
            raise
    
    def _update_short(self, current_price: float, atr: float) -> float:
        """Update trailing stop for short position."""
        try:
            if current_price < self.lowest_price:
                self.lowest_price = current_price
                # Move stop down by ATR
                new_stop = current_price + (atr * self.atr_multiplier)
                self.current_stop = min(self.current_stop, new_stop)
            
                logger.debug(f"Short trailing stop updated: price={current_price}, stop={self.current_stop}")
        
            # Check if breakeven
            if current_price < self.entry_price and not self.is_breakeven:
                self.is_breakeven = True
                # Move stop to breakeven
                self.current_stop = min(self.current_stop, self.entry_price)
                logger.info(f"Breakeven stop activated: {self.current_stop}")
        
            return self.current_stop
        except Exception as e:
            logger.error(f"Error in _update_short: {e}")
            raise
    
    def should_exit(self, current_price: float) -> bool:
        """
        Check if stop loss hit.
        
        Args:
            current_price: Current market price
            
        Returns:
            True if stop loss hit, False otherwise
        """
        try:
            if self.current_stop is None:
                return False
        
            if self.direction == TradeDirection.LONG:
                return current_price <= self.current_stop
            else:
                return current_price >= self.current_stop
        except Exception as e:
            logger.error(f"Error in should_exit: {e}")
            raise
    
    def get_profit_pips(self, current_price: float) -> float:
        """
        Get current profit in pips.
        
        Args:
            current_price: Current market price
            
        Returns:
            Profit in pips
        """
        try:
            if self.entry_price is None:
                return 0
        
            profit = (current_price - self.entry_price) * 10000
        
            if self.direction == TradeDirection.SHORT:
                profit = -profit
        
            return profit
        except Exception as e:
            logger.error(f"Error in get_profit_pips: {e}")
            raise
    
    def get_state(self) -> TrailingStopState:
        """Get current state."""
        try:
            profit_pips = self.get_profit_pips(
                self.highest_price if self.direction == TradeDirection.LONG else self.lowest_price
            )
        
            state = TrailingStopState(
                entry_price=self.entry_price,
                initial_stop=self.initial_stop,
                current_stop=self.current_stop,
                highest_price=self.highest_price,
                lowest_price=self.lowest_price,
                profit_pips=profit_pips,
                is_breakeven=self.is_breakeven,
                timestamp=datetime.now()
            )
        
            self.state_history.append(state)
        
            # Keep only last 1000 states
            if len(self.state_history) > 1000:
                self.state_history.pop(0)
        
            return state
        except Exception as e:
            logger.error(f"Error in get_state: {e}")
            raise
    
    def get_status(self) -> str:
        """Get human-readable status."""
        try:
            state = self.get_state()
        
            direction_str = "LONG" if self.direction == TradeDirection.LONG else "SHORT"
            breakeven_str = "✓ YES" if state.is_breakeven else "✗ NO"
        
            return f"""
    TRAILING STOP STATUS
    {'=' * 50}
    Direction: {direction_str}
    Entry Price: {state.entry_price:.5f}
    Current Stop: {state.current_stop:.5f}
    Initial Stop: {state.initial_stop:.5f}
    Highest Price (Long): {state.highest_price:.5f}
    Lowest Price (Short): {state.lowest_price:.5f}
    Profit: {state.profit_pips:.1f} pips
    Breakeven: {breakeven_str}
    {'=' * 50}
    """
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise
    
    def reset(self):
        """Reset trailing stop."""
        try:
            self.entry_price = None
            self.initial_stop = None
            self.current_stop = None
            self.highest_price = None
            self.lowest_price = None
            self.is_breakeven = False
            self.state_history.clear()
            logger.info("Trailing stop reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
