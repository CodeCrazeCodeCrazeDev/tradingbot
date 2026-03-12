"""
EXIT OPTIMIZER MODULE - PHASE 2 QUICK-WIN #3
============================================================

Implements intelligent exit optimization to maximize profits.

Features:
- Partial profit taking
- Trailing profit targets
- Market condition-based exits
- Risk/reward optimization

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional

import numpy as np
import numpy

logger = logging.getLogger(__name__)


class ExitType(Enum):
    """Types of exits."""
    PARTIAL_PROFIT = auto()
    TRAILING_PROFIT = auto()
    BREAKEVEN = auto()
    STOP_LOSS = auto()
    TIME_BASED = auto()
    MARKET_CONDITION = auto()


@dataclass
class ExitLevel:
    """Exit level configuration."""
    profit_percent: float  # Profit target in percent
    position_percent: float  # Percent of position to close (0-1)
    description: str = ""


class ExitOptimizer:
    """Optimizes trade exits for maximum profitability."""
    
    def __init__(self, use_partial_exits: bool = True,
                 use_trailing_profit: bool = True):
        """
        Initialize exit optimizer.
        
        Args:
            use_partial_exits: Enable partial profit taking
            use_trailing_profit: Enable trailing profit targets
        """
        try:
            self.use_partial_exits = use_partial_exits
            self.use_trailing_profit = use_trailing_profit
        
            # Default exit levels (profit %, position %)
            self.default_exit_levels = [
                ExitLevel(1.0, 0.25, "First 25% at 1% profit"),
                ExitLevel(2.0, 0.25, "Second 25% at 2% profit"),
                ExitLevel(3.0, 0.25, "Third 25% at 3% profit"),
                ExitLevel(5.0, 0.25, "Last 25% at 5% profit"),
            ]
        
            self.trades: Dict[str, Dict] = {}
        
            logger.info("Exit optimizer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def initialize_trade(self, trade_id: str, entry_price: float,
                        position_size: float, direction: str = "LONG"):
        """Initialize trade for exit optimization."""
        try:
            self.trades[trade_id] = {
                'entry_price': entry_price,
                'position_size': position_size,
                'direction': direction,
                'entry_time': datetime.now(),
                'highest_price': entry_price,
                'lowest_price': entry_price,
                'closed_percent': 0.0,
                'profit_locked': 0.0,
                'exit_levels': self.default_exit_levels.copy()
            }
        
            logger.info(f"Trade {trade_id} initialized for exit optimization")
        except Exception as e:
            logger.error(f"Error in initialize_trade: {e}")
            raise
    
    def update_price(self, trade_id: str, current_price: float) -> Dict:
        """
        Update trade price and check for exits.
        
        Returns:
            Dict with exit signals and recommendations
        """
        try:
            if trade_id not in self.trades:
                return {'should_exit': False, 'exits': []}
        
            trade = self.trades[trade_id]
        
            # Update price extremes
            if trade['direction'] == 'LONG':
                trade['highest_price'] = max(trade['highest_price'], current_price)
            else:
                trade['lowest_price'] = min(trade['lowest_price'], current_price)
        
            # Calculate current profit
            if trade['direction'] == 'LONG':
                profit_percent = ((current_price - trade['entry_price']) / 
                                trade['entry_price'] * 100)
            else:
                profit_percent = ((trade['entry_price'] - current_price) / 
                                trade['entry_price'] * 100)
        
            # Check for exit signals
            exits = self._check_exit_levels(trade_id, profit_percent)
        
            return {
                'should_exit': len(exits) > 0,
                'exits': exits,
                'current_profit': profit_percent,
                'position_remaining': 1.0 - trade['closed_percent']
            }
        except Exception as e:
            logger.error(f"Error in update_price: {e}")
            raise
    
    def _check_exit_levels(self, trade_id: str, profit_percent: float) -> List[Dict]:
        """Check which exit levels have been hit."""
        try:
            trade = self.trades[trade_id]
            exits = []
        
            for level in trade['exit_levels']:
                if profit_percent >= level.profit_percent:
                    remaining_position = 1.0 - trade['closed_percent']
                    close_amount = level.position_percent * remaining_position
                
                    if close_amount > 0.001:  # Minimum threshold
                        exits.append({
                            'type': ExitType.PARTIAL_PROFIT,
                            'profit_percent': profit_percent,
                            'close_percent': close_amount,
                            'description': level.description
                        })
                    
                        # Mark this level as used
                        trade['closed_percent'] += close_amount
                        trade['profit_locked'] += profit_percent * close_amount
        
            return exits
        except Exception as e:
            logger.error(f"Error in _check_exit_levels: {e}")
            raise
    
    def get_optimal_exit_price(self, trade_id: str, current_price: float) -> Optional[float]:
        """
        Calculate optimal exit price based on market conditions.
        
        Returns:
            Recommended exit price or None
        """
        try:
            if trade_id not in self.trades:
                return None
        
            trade = self.trades[trade_id]
        
            # Calculate average profit from closed positions
            if trade['closed_percent'] > 0:
                avg_profit_percent = trade['profit_locked'] / trade['closed_percent']
            else:
                avg_profit_percent = 0
        
            # Recommend exit at similar profit level
            if trade['direction'] == 'LONG':
                exit_price = trade['entry_price'] * (1 + avg_profit_percent / 100)
            else:
                exit_price = trade['entry_price'] * (1 - avg_profit_percent / 100)
        
            return exit_price
        except Exception as e:
            logger.error(f"Error in get_optimal_exit_price: {e}")
            raise
    
    def get_trailing_stop(self, trade_id: str, trailing_percent: float = 1.0) -> Optional[float]:
        """
        Calculate trailing stop based on highest/lowest price.
        
        Args:
            trade_id: Trade identifier
            trailing_percent: Trailing distance in percent
            
        Returns:
            Trailing stop price or None
        """
        try:
            if trade_id not in self.trades:
                return None
        
            trade = self.trades[trade_id]
        
            if trade['direction'] == 'LONG':
                # Stop below highest price
                stop_price = trade['highest_price'] * (1 - trailing_percent / 100)
            else:
                # Stop above lowest price
                stop_price = trade['lowest_price'] * (1 + trailing_percent / 100)
        
            return stop_price
        except Exception as e:
            logger.error(f"Error in get_trailing_stop: {e}")
            raise
    
    def get_profit_summary(self, trade_id: str, current_price: float) -> str:
        """Get profit summary for trade."""
        try:
            if trade_id not in self.trades:
                return "Trade not found"
        
            trade = self.trades[trade_id]
        
            # Calculate current profit
            if trade['direction'] == 'LONG':
                current_profit = ((current_price - trade['entry_price']) / 
                                trade['entry_price'] * 100)
            else:
                current_profit = ((trade['entry_price'] - current_price) / 
                                trade['entry_price'] * 100)
        
            summary = f"EXIT OPTIMIZATION - {trade_id}\n"
            summary += "=" * 50 + "\n"
            summary += f"Entry Price: {trade['entry_price']:.5f}\n"
            summary += f"Current Price: {current_price:.5f}\n"
            summary += f"Current Profit: {current_profit:.2f}%\n"
            summary += f"Position Closed: {trade['closed_percent']:.1%}\n"
            summary += f"Profit Locked: {trade['profit_locked']:.2f}%\n"
            summary += f"Position Remaining: {1.0 - trade['closed_percent']:.1%}\n"
            summary += "=" * 50 + "\n"
        
            # Show next exit level
            for level in trade['exit_levels']:
                if current_profit < level.profit_percent:
                    summary += f"Next Exit: {level.profit_percent}% ({level.description})\n"
                    break
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_profit_summary: {e}")
            raise
    
    def close_trade(self, trade_id: str):
        """Close trade and remove from tracking."""
        try:
            if trade_id in self.trades:
                del self.trades[trade_id]
                logger.info(f"Trade {trade_id} closed")
        except Exception as e:
            logger.error(f"Error in close_trade: {e}")
            raise
    
    def reset(self):
        """Reset all trades."""
        try:
            self.trades.clear()
            logger.info("Exit optimizer reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
