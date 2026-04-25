"""
Idea #145: Turnover-Constrained Rebalancing
===============================================
Minimize turnover while maintaining targets.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TurnoverConstrainedRebalancer:
    """Rebalance with turnover constraints."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_turnover = self.config.get("max_turnover", 0.2)
        self.initialized = False
        self.metrics = {"rebalances": 0}
        
    async def initialize(self):
        logger.info("Initializing Turnover-Constrained Rebalancer")
        self.initialized = True
        
    async def rebalance(self, current: Dict[str, float], target: Dict[str, float]) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        all_assets = set(current) | set(target)
        trades = {a: target.get(a, 0) - current.get(a, 0) for a in all_assets}
        total_trade = sum(abs(v) for v in trades.values())
        if total_trade > self.max_turnover:
            scale = self.max_turnover / total_trade
            trades = {k: v * scale for k, v in trades.items()}
        new_weights = {a: current.get(a, 0) + trades.get(a, 0) for a in all_assets}
        self.metrics["rebalances"] += 1
        return new_weights
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
