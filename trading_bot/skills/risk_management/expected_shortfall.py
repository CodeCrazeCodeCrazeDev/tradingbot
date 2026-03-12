"""
Skill #54: Expected Shortfall
=============================

Calculates Expected Shortfall (CVaR) for tail risk measurement.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExpectedShortfallResult:
    """Expected Shortfall result."""
    var: float
    expected_shortfall: float
    tail_ratio: float
    worst_losses: list
    trading_signal: str


class ExpectedShortfall:
    """Calculates Expected Shortfall (CVaR)."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("ExpectedShortfall initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(self, returns: np.ndarray, confidence: float = 0.99) -> ExpectedShortfallResult:
        """Calculate Expected Shortfall."""
        try:
            if len(returns) < 20:
                return self._create_empty_result()
        
            var = np.percentile(returns, (1 - confidence) * 100)
            tail_returns = returns[returns <= var]
            es = np.mean(tail_returns) if len(tail_returns) > 0 else var
            tail_ratio = es / var if var != 0 else 1
            worst = sorted(returns)[:5]
        
            signal = self._generate_signal(var, es, tail_ratio)
        
            return ExpectedShortfallResult(
                var=abs(var), expected_shortfall=abs(es),
                tail_ratio=tail_ratio, worst_losses=worst, trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def _generate_signal(self, var: float, es: float, ratio: float) -> str:
        try:
            if ratio > 1.5:
                return f"FAT TAILS: ES/VaR ratio {ratio:.2f}, ES={abs(es):.2%}"
            return f"NORMAL TAILS: VaR={abs(var):.2%}, ES={abs(es):.2%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> ExpectedShortfallResult:
        return ExpectedShortfallResult(0, 0, 0, [], "Insufficient data")
