"""
Idea #66: Drawdown Control
============================
Automatic position reduction during drawdowns.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DrawdownController:
    """Control drawdowns through position management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_drawdown = self.config.get("max_drawdown", 0.1)
        self.peak_value = 0.0
        self.initialized = False
        self.metrics = {"interventions": 0}
        
    async def initialize(self):
        logger.info("Initializing Drawdown Controller")
        self.initialized = True
        
    async def update(self, portfolio_value: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        self.peak_value = max(self.peak_value, portfolio_value)
        drawdown = (self.peak_value - portfolio_value) / self.peak_value if self.peak_value > 0 else 0
        reduce_exposure = drawdown > self.max_drawdown
        if reduce_exposure:
            self.metrics["interventions"] += 1
        return {"current_drawdown": float(drawdown), "reduce_exposure": reduce_exposure, "target_reduction": 0.5 if reduce_exposure else 0}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
