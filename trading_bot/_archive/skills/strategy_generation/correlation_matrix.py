"""
Skill #69: Strategy Correlation Matrix
======================================

Analyzes correlations between multiple strategies.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class CorrelationMatrixResult:
    """Strategy correlation result."""
    correlation_matrix: np.ndarray
    strategy_names: List[str]
    avg_correlation: float
    most_correlated_pair: tuple
    diversification_ratio: float
    trading_signal: str


class StrategyCorrelationMatrix:
    """Analyzes strategy correlations."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("StrategyCorrelationMatrix initialized")
    
    def analyze(self, returns_dict: Dict[str, np.ndarray]) -> CorrelationMatrixResult:
        """Analyze strategy correlations."""
        if len(returns_dict) < 2:
            return self._create_empty_result()
        
        names = list(returns_dict.keys())
        returns = np.array([returns_dict[n] for n in names])
        
        corr_matrix = np.corrcoef(returns)
        
        # Average correlation (excluding diagonal)
        mask = ~np.eye(len(names), dtype=bool)
        avg_corr = np.mean(corr_matrix[mask])
        
        # Most correlated pair
        corr_matrix_masked = corr_matrix.copy()
        np.fill_diagonal(corr_matrix_masked, -1)
        max_idx = np.unravel_index(np.argmax(corr_matrix_masked), corr_matrix_masked.shape)
        most_corr = (names[max_idx[0]], names[max_idx[1]])
        
        # Diversification ratio
        div_ratio = 1 / (1 + avg_corr)
        
        return CorrelationMatrixResult(
            correlation_matrix=corr_matrix, strategy_names=names,
            avg_correlation=avg_corr, most_correlated_pair=most_corr,
            diversification_ratio=div_ratio,
            trading_signal=f"CORRELATION: Avg {avg_corr:.2f}, diversification {div_ratio:.2f}"
        )
    
    def _create_empty_result(self) -> CorrelationMatrixResult:
        return CorrelationMatrixResult(np.array([]), [], 0, ("", ""), 0, "Insufficient data")
