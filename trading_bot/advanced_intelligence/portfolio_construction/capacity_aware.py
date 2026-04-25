"""
Idea #146: Capacity-Aware Allocation
=====================================
Consider strategy capacity in allocation.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CapacityAwareAllocator:
    """Allocate considering strategy capacity."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"allocations": 0}
        
    async def initialize(self):
        logger.info("Initializing Capacity-Aware Allocator")
        self.initialized = True
        
    async def allocate(self, base_weights: Dict[str, float], capacities: Dict[str, float], aum: float) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        adjusted = {}
        for strategy, weight in base_weights.items():
            capacity = capacities.get(strategy, float('inf'))
            intended_allocation = weight * aum
            if intended_allocation > capacity * 0.8:
                adjusted[strategy] = capacity * 0.8 / aum
            else:
                adjusted[strategy] = weight
        total = sum(adjusted.values())
        normalized = {k: v / total for k, v in adjusted.items()}
        self.metrics["allocations"] += 1
        return normalized
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
