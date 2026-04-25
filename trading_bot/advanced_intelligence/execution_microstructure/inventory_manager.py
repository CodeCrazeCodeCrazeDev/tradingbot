"""
Idea #119: Inventory Manager
================================
Manage market making inventory.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class InventoryManager:
    """Manage trading inventory."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.target = self.config.get("target_inventory", 0)
        self.max = self.config.get("max_inventory", 1000)
        self.initialized = False
        self.metrics = {"adjustments": 0}
        
    async def initialize(self):
        logger.info("Initializing Inventory Manager")
        self.initialized = True
        
    async def adjust(self, current: float, pnl: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        deviation = abs(current - self.target)
        skew = -np.sign(current) * min(deviation / self.max, 0.5) if self.max > 0 else 0
        self.metrics["adjustments"] += 1
        return {"current": current, "target": self.target, "skew": float(skew), "unwind_needed": deviation > self.max * 0.8}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
