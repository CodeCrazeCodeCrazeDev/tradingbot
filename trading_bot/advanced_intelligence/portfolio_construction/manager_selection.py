"""
Idea #148: Manager Selection Optimization
===========================================
Optimal allocation across external managers.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ManagerSelectionOptimizer:
    """Optimize manager allocation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"optimizations": 0}
        
    async def initialize(self):
        logger.info("Initializing Manager Selection Optimizer")
        self.initialized = True
        
    async def optimize(self, manager_alphas: Dict[str, float], manager_tracking_errors: Dict[str, float], info_ratios: Dict[str, float]) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        total_ir = sum(info_ratios.values())
        weights = {k: v / total_ir if total_ir > 0 else 1.0 / len(info_ratios) for k, v in info_ratios.items()}
        self.metrics["optimizations"] += 1
        return weights
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
