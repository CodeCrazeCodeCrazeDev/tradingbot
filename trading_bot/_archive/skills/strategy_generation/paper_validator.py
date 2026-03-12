"""
Skill #72: Paper Trading Validator
==================================

Validates strategies through paper trading simulation.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class PaperTradingResult:
    """Paper trading validation result."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    validation_passed: bool
    trading_signal: str


class PaperTradingValidator:
    """Validates strategies via paper trading."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_sharpe = self.config.get('min_sharpe', 0.5)
        self.max_drawdown = self.config.get('max_drawdown', 0.2)
        logger.info("PaperTradingValidator initialized")
    
    def validate(self, signals: np.ndarray, prices: np.ndarray) -> PaperTradingResult:
        """Validate strategy with paper trading."""
        if len(signals) < 20 or len(prices) < 20:
            return self._create_empty_result()
        
        returns = np.diff(prices) / prices[:-1]
        strategy_returns = signals[:-1] * returns
        
        total_ret = np.sum(strategy_returns)
        sharpe = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-10) * np.sqrt(252)
        
        cumulative = np.cumprod(1 + strategy_returns)
        peak = np.maximum.accumulate(cumulative)
        max_dd = abs(np.min((cumulative - peak) / peak))
        
        trades = np.sum(np.abs(np.diff(signals)) > 0)
        wins = np.sum(strategy_returns > 0)
        win_rate = wins / (len(strategy_returns) + 1e-10)
        
        passed = sharpe > self.min_sharpe and max_dd < self.max_drawdown
        
        return PaperTradingResult(
            total_return=total_ret, sharpe_ratio=sharpe, max_drawdown=max_dd,
            win_rate=win_rate, num_trades=trades, validation_passed=passed,
            trading_signal=f"{'PASSED' if passed else 'FAILED'}: Sharpe {sharpe:.2f}, DD {max_dd:.0%}"
        )
    
    def _create_empty_result(self) -> PaperTradingResult:
        return PaperTradingResult(0, 0, 0, 0, 0, False, "Insufficient data")
