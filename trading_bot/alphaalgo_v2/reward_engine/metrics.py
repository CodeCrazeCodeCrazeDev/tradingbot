"""
AlphaAlgo V2 Performance Metrics

Calculates performance metrics for reward calculation.
"""

from dataclasses import dataclass
from typing import List, Optional
import math

import logging
logger = logging.getLogger(__name__)



@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    profit_factor: float = 1.0
    win_rate: float = 0.5
    max_drawdown: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns: List of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods per year
        
    Returns:
        Annualized Sharpe ratio
    """
    try:
        if not returns or len(returns) < 2:
            return 0.0
    
        mean_return = sum(returns) / len(returns)
        excess_return = mean_return - (risk_free_rate / periods_per_year)
    
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0.0
    
        if std_dev == 0:
            return 0.0
    
        return (excess_return / std_dev) * math.sqrt(periods_per_year)
    except Exception as e:
        logger.error(f"Error in calculate_sharpe_ratio: {e}")
        raise


def calculate_sortino_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Sortino ratio (uses downside deviation)
    
    Args:
        returns: List of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods per year
        
    Returns:
        Annualized Sortino ratio
    """
    try:
        if not returns or len(returns) < 2:
            return 0.0
    
        mean_return = sum(returns) / len(returns)
        excess_return = mean_return - (risk_free_rate / periods_per_year)
    
        # Calculate downside deviation
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return float('inf') if excess_return > 0 else 0.0
    
        downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
        downside_dev = math.sqrt(downside_variance)
    
        if downside_dev == 0:
            return 0.0
    
        return (excess_return / downside_dev) * math.sqrt(periods_per_year)
    except Exception as e:
        logger.error(f"Error in calculate_sortino_ratio: {e}")
        raise


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown
    
    Args:
        equity_curve: List of equity values
        
    Returns:
        Maximum drawdown as decimal (0.20 = 20%)
    """
    try:
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
    
        peak = equity_curve[0]
        max_dd = 0.0
    
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, drawdown)
    
        return max_dd
    except Exception as e:
        logger.error(f"Error in calculate_max_drawdown: {e}")
        raise


def calculate_profit_factor(
    gross_profit: float,
    gross_loss: float
) -> float:
    """
    Calculate profit factor
    
    Args:
        gross_profit: Total profit from winning trades
        gross_loss: Total loss from losing trades (positive value)
        
    Returns:
        Profit factor (gross_profit / gross_loss)
    """
    try:
        if gross_loss == 0:
            return 2.0 if gross_profit > 0 else 1.0
        return gross_profit / gross_loss
    except Exception as e:
        logger.error(f"Error in calculate_profit_factor: {e}")
        raise
