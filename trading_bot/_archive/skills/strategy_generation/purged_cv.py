"""
Skill #74: Combinatorial Purged CV
==================================

Cross-validation with purging to prevent data leakage.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class PurgedCVResult:
    """Purged CV result."""
    cv_scores: List[float]
    mean_score: float
    std_score: float
    overfitting_score: float
    trading_signal: str


class CombinatorialPurgedCV:
    """Combinatorial purged cross-validation."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.n_splits = self.config.get('n_splits', 5)
        self.purge_gap = self.config.get('purge_gap', 5)
        logger.info("CombinatorialPurgedCV initialized")
    
    def validate(self, prices: np.ndarray, strategy_func) -> PurgedCVResult:
        """Perform purged cross-validation."""
        if len(prices) < 100:
            return self._create_empty_result()
        
        fold_size = len(prices) // self.n_splits
        scores = []
        
        for i in range(self.n_splits):
            # Test fold
            test_start = i * fold_size
            test_end = (i + 1) * fold_size
            
            # Train folds with purging
            train_mask = np.ones(len(prices), dtype=bool)
            train_mask[max(0, test_start - self.purge_gap):min(len(prices), test_end + self.purge_gap)] = False
            
            train_prices = prices[train_mask]
            test_prices = prices[test_start:test_end]
            
            if len(train_prices) > 20 and len(test_prices) > 10:
                score = strategy_func(train_prices, test_prices)
                scores.append(score)
        
        mean_score = np.mean(scores) if scores else 0
        std_score = np.std(scores) if scores else 0
        overfitting = std_score / (abs(mean_score) + 1e-10)
        
        return PurgedCVResult(
            cv_scores=scores, mean_score=mean_score, std_score=std_score,
            overfitting_score=overfitting,
            trading_signal=f"PURGED CV: Mean {mean_score:.3f} ± {std_score:.3f}"
        )
    
    def _create_empty_result(self) -> PurgedCVResult:
        return PurgedCVResult([], 0, 0, 0, "Insufficient data")
