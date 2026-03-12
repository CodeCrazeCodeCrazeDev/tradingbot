"""
Skill #52: Incremental VaR Calculator
=====================================

Calculates the marginal contribution of a new position to portfolio VaR.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class IncrementalVaRResult:
    """Incremental VaR result."""
    portfolio_var_before: float
    portfolio_var_after: float
    incremental_var: float
    diversification_benefit: float
    trading_signal: str


class IncrementalVaRCalculator:
    """Calculates incremental VaR for new positions."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("IncrementalVaRCalculator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        portfolio_returns: np.ndarray,
        new_position_returns: np.ndarray,
        new_position_weight: float,
        confidence: float = 0.99
    ) -> IncrementalVaRResult:
        """Calculate incremental VaR."""
        try:
            if len(portfolio_returns) < 20 or len(new_position_returns) < 20:
                return self._create_empty_result()
        
            # VaR before
            var_before = abs(np.percentile(portfolio_returns, (1 - confidence) * 100))
        
            # Combined returns
            combined = (1 - new_position_weight) * portfolio_returns + new_position_weight * new_position_returns
            var_after = abs(np.percentile(combined, (1 - confidence) * 100))
        
            # Incremental VaR
            incremental = var_after - var_before
        
            # Standalone VaR of new position
            standalone_var = abs(np.percentile(new_position_returns, (1 - confidence) * 100)) * new_position_weight
        
            # Diversification benefit
            diversification = standalone_var - incremental
        
            signal = self._generate_signal(incremental, diversification)
        
            return IncrementalVaRResult(
                portfolio_var_before=var_before,
                portfolio_var_after=var_after,
                incremental_var=incremental,
                diversification_benefit=diversification,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def _generate_signal(self, incr: float, div: float) -> str:
        """Generate signal."""
        try:
            if incr < 0:
                return f"RISK REDUCING: Position reduces VaR by {abs(incr):.2%}"
            elif div > 0:
                return f"DIVERSIFIED: Incremental VaR {incr:.2%}, diversification benefit {div:.2%}"
            return f"CONCENTRATED: Incremental VaR {incr:.2%}, no diversification"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> IncrementalVaRResult:
        return IncrementalVaRResult(0, 0, 0, 0, "Insufficient data")
