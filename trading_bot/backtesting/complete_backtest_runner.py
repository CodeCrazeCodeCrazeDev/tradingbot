"""
COMPLETE BACKTEST RUNNER - VALIDATION MODULE
============================================================

Runs comprehensive backtests on all 4 phases of the trading system.

Features:
- Historical data loading
- Trade simulation
- Performance metrics calculation
- Drawdown analysis
- Risk/reward analysis
- Win rate calculation
- Sharpe ratio calculation

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import numpy

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    """Backtest performance metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    avg_profit_per_trade: float
    max_drawdown: float
    sharpe_ratio: float
    risk_reward_ratio: float
    profit_factor: float
    consecutive_wins: int
    consecutive_losses: int
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class CompleteBacktestRunner:
    """Runs comprehensive backtests on the complete trading system."""
    
    def __init__(self, initial_balance: float = 10000.0,
                 risk_per_trade: float = 0.02):
        """
        Initialize backtest runner.
        
        Args:
            initial_balance: Starting account balance
            risk_per_trade: Risk per trade as percentage
        """
        try:
            self.initial_balance = initial_balance
            self.risk_per_trade = risk_per_trade
        
            # Trade tracking
            self.trades: List[Dict] = []
            self.balance_history: List[float] = [initial_balance]
            self.equity_curve: List[float] = [initial_balance]
        
            logger.info(f"Backtest runner initialized: ${initial_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_trade(self, entry_price: float, exit_price: float,
                 position_size: float, direction: str = "LONG",
                 entry_time: datetime = None, exit_time: datetime = None) -> Dict:
        """
        Add a completed trade to backtest.
        
        Returns:
            Trade result dict
        """
        try:
            if direction == "LONG":
                profit = (exit_price - entry_price) * position_size
            else:  # SHORT
                profit = (entry_price - exit_price) * position_size
        
            profit_percent = (profit / (entry_price * position_size)) * 100 if entry_price > 0 else 0
        
            trade = {
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position_size,
                'direction': direction,
                'profit': profit,
                'profit_percent': profit_percent,
                'entry_time': entry_time or datetime.now(),
                'exit_time': exit_time or datetime.now(),
                'won': profit > 0
            }
        
            self.trades.append(trade)
        
            # Update balance
            current_balance = self.balance_history[-1] + profit
            self.balance_history.append(current_balance)
            self.equity_curve.append(current_balance)
        
            return trade
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def calculate_metrics(self) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics."""
        try:
            if not self.trades:
                return BacktestMetrics(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0,
                    total_profit=0,
                    avg_profit_per_trade=0,
                    max_drawdown=0,
                    sharpe_ratio=0,
                    risk_reward_ratio=0,
                    profit_factor=0,
                    consecutive_wins=0,
                    consecutive_losses=0
                )
        
            # Basic metrics
            total_trades = len(self.trades)
            winning_trades = sum(1 for t in self.trades if t['won'])
            losing_trades = total_trades - winning_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
            # Profit metrics
            total_profit = sum(t['profit'] for t in self.trades)
            avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0
        
            # Drawdown
            max_drawdown = self._calculate_max_drawdown()
        
            # Sharpe ratio
            sharpe_ratio = self._calculate_sharpe_ratio()
        
            # Risk/reward
            winning_trades_list = [t for t in self.trades if t['won']]
            losing_trades_list = [t for t in self.trades if not t['won']]
        
            avg_win = sum(t['profit'] for t in winning_trades_list) / len(winning_trades_list) if winning_trades_list else 0
            avg_loss = abs(sum(t['profit'] for t in losing_trades_list) / len(losing_trades_list)) if losing_trades_list else 0
        
            risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
            # Profit factor
            gross_profit = sum(t['profit'] for t in winning_trades_list)
            gross_loss = abs(sum(t['profit'] for t in losing_trades_list))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
            # Consecutive wins/losses
            consecutive_wins = self._calculate_consecutive_wins()
            consecutive_losses = self._calculate_consecutive_losses()
        
            return BacktestMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_profit=total_profit,
                avg_profit_per_trade=avg_profit_per_trade,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                risk_reward_ratio=risk_reward_ratio,
                profit_factor=profit_factor,
                consecutive_wins=consecutive_wins,
                consecutive_losses=consecutive_losses
            )
        except Exception as e:
            logger.error(f"Error in calculate_metrics: {e}")
            raise
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        try:
            if not self.equity_curve:
                return 0
        
            peak = self.equity_curve[0]
            max_dd = 0
        
            for value in self.equity_curve:
                if value > peak:
                    peak = value
            
                dd = (peak - value) / peak if peak > 0 else 0
                max_dd = max(max_dd, dd)
        
            return max_dd
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown: {e}")
            raise
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        try:
            if len(self.equity_curve) < 2:
                return 0
        
            returns = []
            for i in range(1, len(self.equity_curve)):
                ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
                returns.append(ret)
        
            if not returns:
                return 0
        
            avg_return = np.mean(returns)
            std_return = np.std(returns)
        
            if std_return == 0:
                return 0
        
            # Annualized Sharpe (assuming 252 trading days)
            sharpe = (avg_return - risk_free_rate / 252) / std_return * np.sqrt(252)
        
            return sharpe
        except Exception as e:
            logger.error(f"Error in _calculate_sharpe_ratio: {e}")
            raise
    
    def _calculate_consecutive_wins(self) -> int:
        """Calculate maximum consecutive wins."""
        try:
            if not self.trades:
                return 0
        
            max_consecutive = 0
            current_consecutive = 0
        
            for trade in self.trades:
                if trade['won']:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
        
            return max_consecutive
        except Exception as e:
            logger.error(f"Error in _calculate_consecutive_wins: {e}")
            raise
    
    def _calculate_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses."""
        try:
            if not self.trades:
                return 0
        
            max_consecutive = 0
            current_consecutive = 0
        
            for trade in self.trades:
                if not trade['won']:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
        
            return max_consecutive
        except Exception as e:
            logger.error(f"Error in _calculate_consecutive_losses: {e}")
            raise
    
    def get_backtest_summary(self) -> str:
        """Get human-readable backtest summary."""
        try:
            metrics = self.calculate_metrics()
        
            summary = "BACKTEST RESULTS\n"
            summary += "=" * 60 + "\n\n"
        
            summary += "TRADE STATISTICS:\n"
            summary += f"  Total Trades: {metrics.total_trades}\n"
            summary += f"  Winning Trades: {metrics.winning_trades}\n"
            summary += f"  Losing Trades: {metrics.losing_trades}\n"
            summary += f"  Win Rate: {metrics.win_rate:.1%}\n"
            summary += "\n"
        
            summary += "PROFIT METRICS:\n"
            summary += f"  Total Profit: ${metrics.total_profit:,.2f}\n"
            summary += f"  Avg Profit/Trade: ${metrics.avg_profit_per_trade:,.2f}\n"
            summary += f"  Profit Factor: {metrics.profit_factor:.2f}\n"
            summary += "\n"
        
            summary += "RISK METRICS:\n"
            summary += f"  Max Drawdown: {metrics.max_drawdown:.1%}\n"
            summary += f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}\n"
            summary += f"  Risk/Reward Ratio: {metrics.risk_reward_ratio:.2f}:1\n"
            summary += "\n"
        
            summary += "STREAK METRICS:\n"
            summary += f"  Max Consecutive Wins: {metrics.consecutive_wins}\n"
            summary += f"  Max Consecutive Losses: {metrics.consecutive_losses}\n"
            summary += "\n"
        
            summary += "ACCOUNT METRICS:\n"
            summary += f"  Starting Balance: ${self.initial_balance:,.2f}\n"
            summary += f"  Ending Balance: ${self.balance_history[-1]:,.2f}\n"
            summary += f"  Return: {((self.balance_history[-1] - self.initial_balance) / self.initial_balance * 100):.2f}%\n"
            summary += "=" * 60 + "\n"
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_backtest_summary: {e}")
            raise
    
    def get_performance_vs_targets(self) -> Dict[str, Dict]:
        """Compare performance against targets."""
        try:
            metrics = self.calculate_metrics()
        
            targets = {
                'win_rate': 0.65,
                'sharpe_ratio': 2.0,
                'max_drawdown': 0.08,
                'risk_reward_ratio': 3.0
            }
        
            performance = {
                'win_rate': {
                    'actual': metrics.win_rate,
                    'target': targets['win_rate'],
                    'met': metrics.win_rate >= targets['win_rate']
                },
                'sharpe_ratio': {
                    'actual': metrics.sharpe_ratio,
                    'target': targets['sharpe_ratio'],
                    'met': metrics.sharpe_ratio >= targets['sharpe_ratio']
                },
                'max_drawdown': {
                    'actual': metrics.max_drawdown,
                    'target': targets['max_drawdown'],
                    'met': metrics.max_drawdown <= targets['max_drawdown']
                },
                'risk_reward_ratio': {
                    'actual': metrics.risk_reward_ratio,
                    'target': targets['risk_reward_ratio'],
                    'met': metrics.risk_reward_ratio >= targets['risk_reward_ratio']
                }
            }
        
            return performance
        except Exception as e:
            logger.error(f"Error in get_performance_vs_targets: {e}")
            raise
    
    def reset(self):
        """Reset backtest."""
        try:
            self.trades.clear()
            self.balance_history = [self.initial_balance]
            self.equity_curve = [self.initial_balance]
            logger.info("Backtest reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
