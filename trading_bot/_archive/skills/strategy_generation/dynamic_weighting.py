"""
Skill #70: Dynamic Strategy Weighting
=====================================

Dynamically adjusts strategy weights based on performance.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeightingResult:
    """Dynamic weighting result."""
    weights: Dict[str, float]
    weight_changes: Dict[str, float]
    rebalance_needed: bool
    trading_signal: str


class DynamicStrategyWeighting:
    """Dynamically weights strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.current_weights: Dict[str, float] = {}
        logger.info("DynamicStrategyWeighting initialized")
    
    def calculate_weights(self, performance_dict: Dict[str, float]) -> WeightingResult:
        """Calculate dynamic weights."""
        if not performance_dict:
            return WeightingResult({}, {}, False, "No strategies")
        
        # Performance-based weighting
        total_perf = sum(max(0.01, p) for p in performance_dict.values())
        new_weights = {k: max(0.01, v) / total_perf for k, v in performance_dict.items()}
        
        # Calculate changes
        changes = {k: new_weights[k] - self.current_weights.get(k, 0) for k in new_weights}
        
        # Check if rebalance needed
        rebalance = any(abs(c) > 0.1 for c in changes.values())
        
        self.current_weights = new_weights
        
        return WeightingResult(
            weights=new_weights, weight_changes=changes,
            rebalance_needed=rebalance,
            trading_signal=f"WEIGHTS: {'Rebalance needed' if rebalance else 'Stable'}"
        )
