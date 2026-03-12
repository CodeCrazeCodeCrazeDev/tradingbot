"""
Performance Analytics Module
Provides comprehensive performance analysis for trading strategies.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    expectancy: float = 0.0
    calmar_ratio: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceAnalytics:
    """
    Comprehensive performance analytics for trading strategies.
    
    Provides metrics calculation, analysis, and reporting.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize performance analytics.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []
        self.metrics = PerformanceMetrics()
        
        logger.info("PerformanceAnalytics initialized")
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """Add a trade to the analytics.
        
        Args:
            trade: Trade dictionary with pnl, entry_time, exit_time, etc.
        """
        self.trades.append(trade)
        self._update_metrics()
    
    def add_equity_point(self, equity: float) -> None:
        """Add an equity point to the curve.
        
        Args:
            equity: Current equity value
        """
        self.equity_curve.append(equity)
    
    def _update_metrics(self) -> None:
        """Update all performance metrics."""
        if not self.trades:
            return
        
        pnls = [t.get('pnl', 0) for t in self.trades]
        
        # Basic metrics
        self.metrics.total_trades = len(self.trades)
        self.metrics.total_return = sum(pnls)
        
        # Win/Loss analysis
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        self.metrics.winning_trades = len(wins)
        self.metrics.losing_trades = len(losses)
        self.metrics.win_rate = len(wins) / len(pnls) if pnls else 0
        
        self.metrics.avg_win = np.mean(wins) if wins else 0
        self.metrics.avg_loss = np.mean(losses) if losses else 0
        
        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        self.metrics.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Expectancy
        self.metrics.expectancy = (
            self.metrics.win_rate * self.metrics.avg_win +
            (1 - self.metrics.win_rate) * self.metrics.avg_loss
        )
        
        # Risk-adjusted metrics
        if len(pnls) > 1:
            returns = np.array(pnls)
            self.metrics.sharpe_ratio = self._calculate_sharpe(returns)
            self.metrics.sortino_ratio = self._calculate_sortino(returns)
        
        # Drawdown
        if self.equity_curve:
            self.metrics.max_drawdown = self._calculate_max_drawdown()
            if self.metrics.max_drawdown > 0:
                annual_return = self.metrics.total_return * 252 / max(len(self.trades), 1)
                self.metrics.calmar_ratio = annual_return / self.metrics.max_drawdown
        
        self.metrics.timestamp = datetime.now()
    
    def _calculate_sharpe(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        excess_returns = returns - risk_free_rate
        if np.std(excess_returns) == 0:
            return 0.0
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_sortino(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio."""
        excess_returns = returns - risk_free_rate
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0
        return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not self.equity_curve:
            return 0.0
        
        equity = np.array(self.equity_curve)
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        return float(np.max(drawdown)) if len(drawdown) > 0 else 0.0
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics.
        
        Returns:
            PerformanceMetrics object
        """
        return self.metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary as dictionary.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            'total_return': self.metrics.total_return,
            'sharpe_ratio': self.metrics.sharpe_ratio,
            'sortino_ratio': self.metrics.sortino_ratio,
            'max_drawdown': self.metrics.max_drawdown,
            'win_rate': self.metrics.win_rate,
            'profit_factor': self.metrics.profit_factor,
            'total_trades': self.metrics.total_trades,
            'winning_trades': self.metrics.winning_trades,
            'losing_trades': self.metrics.losing_trades,
            'expectancy': self.metrics.expectancy,
            'calmar_ratio': self.metrics.calmar_ratio,
            'timestamp': self.metrics.timestamp.isoformat()
        }
    
    def reset(self) -> None:
        """Reset all analytics data."""
        self.trades = []
        self.equity_curve = []
        self.metrics = PerformanceMetrics()
        logger.info("PerformanceAnalytics reset")


# Factory function
def create_performance_analytics(config: Optional[Dict] = None) -> PerformanceAnalytics:
    """Create a PerformanceAnalytics instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        PerformanceAnalytics instance
    """
    return PerformanceAnalytics(config)


__all__ = [
    'PerformanceAnalytics',
    'PerformanceMetrics',
    'create_performance_analytics',
]
