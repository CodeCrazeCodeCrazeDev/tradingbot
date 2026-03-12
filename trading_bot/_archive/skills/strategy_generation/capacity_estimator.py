"""
Skill #67: Strategy Capacity Estimator
======================================

Estimates maximum capital capacity for strategies.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CapacityResult:
    """Strategy capacity result."""
    max_capacity: float
    current_utilization: float
    impact_at_capacity: float
    optimal_size: float
    trading_signal: str


class StrategyCapacityEstimator:
    """Estimates strategy capital capacity."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("StrategyCapacityEstimator initialized")
    
    def estimate(self, avg_volume: float, spread: float, alpha: float, current_aum: float) -> CapacityResult:
        """Estimate strategy capacity."""
        # Capacity based on market impact
        daily_volume_usd = avg_volume * 1000  # Assume $1000 per unit
        max_participation = 0.05  # 5% of volume
        
        max_capacity = daily_volume_usd * max_participation / spread
        utilization = current_aum / max_capacity if max_capacity > 0 else 0
        
        # Impact at capacity
        impact = spread * np.sqrt(utilization)
        
        # Optimal size (where alpha > impact)
        optimal = max_capacity * (alpha / (spread + 1e-10)) ** 2
        
        return CapacityResult(
            max_capacity=max_capacity, current_utilization=utilization,
            impact_at_capacity=impact, optimal_size=min(optimal, max_capacity),
            trading_signal=f"CAPACITY: Max ${max_capacity:,.0f}, {utilization:.0%} utilized"
        )
