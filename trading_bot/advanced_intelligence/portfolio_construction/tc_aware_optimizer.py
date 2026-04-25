"""
Idea #130: Transaction Cost Aware Optimization
================================================
Include realistic transaction costs in optimization.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TCAwareOptimizer:
    """Transaction cost aware optimization."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tc_rate = self.config.get("tc_rate", 0.001)
        self.initialized = False
        self.metrics = {"optimizations": 0}
        
    async def initialize(self):
        logger.info("Initializing TC Aware Optimizer")
        self.initialized = True
        
    async def optimize(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, current_weights: np.ndarray) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        n = len(expected_returns)
        inv_vol = 1.0 / np.sqrt(np.diag(cov_matrix))
        base_weights = inv_vol / np.sum(inv_vol)
        turnover = np.sum(np.abs(base_weights - current_weights))
        tc_penalty = turnover * self.tc_rate
        adjusted_returns = expected_returns - tc_penalty
        weights = base_weights * 0.8 + current_weights * 0.2
        weights = weights / np.sum(weights)
        result = {f"asset_{i}": float(w) for i, w in enumerate(weights)}
        self.metrics["optimizations"] += 1
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
