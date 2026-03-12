"""
Elite Trailing Stop-Loss System
Advanced stop-loss management with multiple trailing strategies
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class TrailingType(Enum):
    """Types of trailing stop strategies"""
    FIXED = "fixed"  # Fixed distance
    ATR = "atr"  # ATR-based
    PERCENTAGE = "percentage"  # Percentage-based
    PARABOLIC = "parabolic"  # Parabolic SAR
    CHANDELIER = "chandelier"  # Chandelier exit
    BREAKEVEN = "breakeven"  # Move to breakeven


@dataclass
class TrailingStopConfig:
    """Configuration for trailing stop"""
    trailing_type: TrailingType = TrailingType.ATR
    atr_multiplier: float = 2.0
    percentage: float = 0.02  # 2%
    fixed_distance: float = 0.0010  # 10 pips for forex
    breakeven_trigger: float = 1.5  # Move to BE at 1.5x risk
    lock_profit_at: float = 2.0  # Lock profit at 2x risk


class TrailingStop:
    """
    Elite Trailing Stop Manager
    
    Features:
    - Multiple trailing strategies
    - Automatic breakeven
    - Profit locking
    - Partial position management
    """
    
    def __init__(self, 
                 entry_price: float,
                 direction: str,  # 'BUY' or 'SELL'
                 initial_stop: float,
                 config: Optional[TrailingStopConfig] = None):
        
        try:
            self.entry_price = entry_price
            self.direction = direction.upper()
            self.initial_stop = initial_stop
            self.config = config or TrailingStopConfig()
        
            self.current_stop = initial_stop
            self.highest_price = entry_price if direction == 'BUY' else entry_price
            self.lowest_price = entry_price if direction == 'SELL' else entry_price
            self.is_at_breakeven = False
            self.profit_locked = False
        
            self.update_history: List[Dict] = []
        
            logger.info(f"Trailing stop initialized: {direction} @ {entry_price}, SL: {initial_stop}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, current_price: float, atr: Optional[float] = None) -> Dict:
        """
        Update trailing stop based on current price
        
        Returns:
            Dict with stop update info
        """
        try:
            old_stop = self.current_stop
        
            if self.direction == 'BUY':
                # Update highest price
                if current_price > self.highest_price:
                    self.highest_price = current_price
            
                # Calculate new stop based on strategy
                new_stop = self._calculate_buy_stop(current_price, atr)
            
                # Only move stop up, never down
                if new_stop > self.current_stop:
                    self.current_stop = new_stop
                
            else:  # SELL
                # Update lowest price
                if current_price < self.lowest_price:
                    self.lowest_price = current_price
            
                # Calculate new stop
                new_stop = self._calculate_sell_stop(current_price, atr)
            
                # Only move stop down, never up
                if new_stop < self.current_stop:
                    self.current_stop = new_stop
        
            # Check for breakeven
            self._check_breakeven(current_price)
        
            # Check for profit lock
            self._check_profit_lock(current_price)
        
            # Record update
            update_info = {
                'timestamp': datetime.now(),
                'price': current_price,
                'old_stop': old_stop,
                'new_stop': self.current_stop,
                'moved': self.current_stop != old_stop,
                'at_breakeven': self.is_at_breakeven,
                'profit_locked': self.profit_locked
            }
        
            self.update_history.append(update_info)
        
            if update_info['moved']:
                logger.info(f"Stop moved: {old_stop:.5f} → {self.current_stop:.5f}")
        
            return update_info
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _calculate_buy_stop(self, current_price: float, atr: Optional[float]) -> float:
        """Calculate trailing stop for BUY position"""
        try:
            if self.config.trailing_type == TrailingType.ATR and atr:
                return self.highest_price - (self.config.atr_multiplier * atr)
        
            elif self.config.trailing_type == TrailingType.PERCENTAGE:
                return self.highest_price * (1 - self.config.percentage)
        
            elif self.config.trailing_type == TrailingType.FIXED:
                return self.highest_price - self.config.fixed_distance
        
            else:
                # Default to ATR if available, else percentage
                if atr:
                    return self.highest_price - (self.config.atr_multiplier * atr)
                return self.highest_price * (1 - self.config.percentage)
        except Exception as e:
            logger.error(f"Error in _calculate_buy_stop: {e}")
            raise
    
    def _calculate_sell_stop(self, current_price: float, atr: Optional[float]) -> float:
        """Calculate trailing stop for SELL position"""
        try:
            if self.config.trailing_type == TrailingType.ATR and atr:
                return self.lowest_price + (self.config.atr_multiplier * atr)
        
            elif self.config.trailing_type == TrailingType.PERCENTAGE:
                return self.lowest_price * (1 + self.config.percentage)
        
            elif self.config.trailing_type == TrailingType.FIXED:
                return self.lowest_price + self.config.fixed_distance
        
            else:
                if atr:
                    return self.lowest_price + (self.config.atr_multiplier * atr)
                return self.lowest_price * (1 + self.config.percentage)
        except Exception as e:
            logger.error(f"Error in _calculate_sell_stop: {e}")
            raise
    
    def _check_breakeven(self, current_price: float):
        """Check if should move to breakeven"""
        try:
            if self.is_at_breakeven:
                return
        
            initial_risk = abs(self.entry_price - self.initial_stop)
        
            if self.direction == 'BUY':
                profit = current_price - self.entry_price
                if profit >= initial_risk * self.config.breakeven_trigger:
                    self.current_stop = self.entry_price
                    self.is_at_breakeven = True
                    logger.info("✅ Stop moved to BREAKEVEN")
        
            else:  # SELL
                profit = self.entry_price - current_price
                if profit >= initial_risk * self.config.breakeven_trigger:
                    self.current_stop = self.entry_price
                    self.is_at_breakeven = True
                    logger.info("✅ Stop moved to BREAKEVEN")
        except Exception as e:
            logger.error(f"Error in _check_breakeven: {e}")
            raise
    
    def _check_profit_lock(self, current_price: float):
        """Check if should lock in profit"""
        try:
            if self.profit_locked:
                return
        
            initial_risk = abs(self.entry_price - self.initial_stop)
        
            if self.direction == 'BUY':
                profit = current_price - self.entry_price
                if profit >= initial_risk * self.config.lock_profit_at:
                    # Lock in profit at entry + 1x risk
                    self.current_stop = max(self.current_stop, self.entry_price + initial_risk)
                    self.profit_locked = True
                    logger.info("✅ PROFIT LOCKED")
        
            else:  # SELL
                profit = self.entry_price - current_price
                if profit >= initial_risk * self.config.lock_profit_at:
                    self.current_stop = min(self.current_stop, self.entry_price - initial_risk)
                    self.profit_locked = True
                    logger.info("✅ PROFIT LOCKED")
        except Exception as e:
            logger.error(f"Error in _check_profit_lock: {e}")
            raise
    
    def is_stopped_out(self, current_price: float) -> bool:
        """Check if position should be stopped out"""
        try:
            if self.direction == 'BUY':
                return current_price <= self.current_stop
            else:
                return current_price >= self.current_stop
        except Exception as e:
            logger.error(f"Error in is_stopped_out: {e}")
            raise
    
    def get_status(self) -> Dict:
        """Get current trailing stop status"""
        return {
            'entry_price': self.entry_price,
            'direction': self.direction,
            'current_stop': self.current_stop,
            'initial_stop': self.initial_stop,
            'highest_price': self.highest_price if self.direction == 'BUY' else None,
            'lowest_price': self.lowest_price if self.direction == 'SELL' else None,
            'is_at_breakeven': self.is_at_breakeven,
            'profit_locked': self.profit_locked,
            'updates_count': len(self.update_history)
        }


class PositionManager:
    """
    Manages multiple positions with trailing stops
    """
    
    def __init__(self):
        try:
            self.positions: Dict[str, TrailingStop] = {}
            logger.info("Position Manager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_position(self, position_id: str, entry_price: float, 
                    direction: str, initial_stop: float,
                    config: Optional[TrailingStopConfig] = None):
        """Add new position with trailing stop"""
        try:
            self.positions[position_id] = TrailingStop(
                entry_price, direction, initial_stop, config
            )
            logger.info(f"Position added: {position_id}")
        except Exception as e:
            logger.error(f"Error in add_position: {e}")
            raise
    
    def update_position(self, position_id: str, current_price: float, 
                       atr: Optional[float] = None) -> Optional[Dict]:
        """Update position's trailing stop"""
        try:
            if position_id not in self.positions:
                logger.warning(f"Position {position_id} not found")
                return None
        
            return self.positions[position_id].update(current_price, atr)
        except Exception as e:
            logger.error(f"Error in update_position: {e}")
            raise
    
    def check_stops(self, prices: Dict[str, float]) -> List[str]:
        """
        Check all positions for stop-outs
        
        Returns:
            List of position IDs that were stopped out
        """
        try:
            stopped_out = []
        
            for position_id, trailing_stop in self.positions.items():
                if position_id in prices:
                    if trailing_stop.is_stopped_out(prices[position_id]):
                        stopped_out.append(position_id)
                        logger.warning(f"🛑 Position {position_id} STOPPED OUT")
        
            return stopped_out
        except Exception as e:
            logger.error(f"Error in check_stops: {e}")
            raise
    
    def remove_position(self, position_id: str):
        """Remove position"""
        try:
            if position_id in self.positions:
                del self.positions[position_id]
                logger.info(f"Position removed: {position_id}")
        except Exception as e:
            logger.error(f"Error in remove_position: {e}")
            raise
    
    def get_all_status(self) -> Dict:
        """Get status of all positions"""
        return {
            pid: ts.get_status()
            for pid, ts in self.positions.items()
        }


# Export
__all__ = ['TrailingStop', 'PositionManager', 'TrailingStopConfig', 'TrailingType']
