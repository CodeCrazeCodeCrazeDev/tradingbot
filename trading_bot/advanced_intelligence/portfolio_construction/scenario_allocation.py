"""
Idea #143: Scenario-Based Allocation
=====================================
Allocate based on scenario probabilities.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ScenarioBasedAllocator:
    """Allocate based on scenarios."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"allocations": 0}
        
    async def initialize(self):
        logger.info("Initializing Scenario-Based Allocator")
        self.initialized = True
        
    async def allocate(self, scenario_probs: Dict[str, float], scenario_returns: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        expected_returns = {}
        for asset in set(a for s in scenario_returns.values() for a in s):
            er = sum(scenario_probs.get(s, 0) * scenario_returns[s].get(asset, 0) for s in scenario_probs)
            expected_returns[asset] = er
        total = sum(expected_returns.values())
        weights = {k: max(0, v) / total if total > 0 else 0 for k, v in expected_returns.items()}
        self.metrics["allocations"] += 1
        return weights
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
