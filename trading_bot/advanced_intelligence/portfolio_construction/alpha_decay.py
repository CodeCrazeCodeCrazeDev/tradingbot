"""
Idea #147: Alpha Decay Modeling
================================
Model and account for alpha decay in allocation.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AlphaDecayModel:
    """Model alpha decay over time."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.decay_rate = self.config.get("decay_rate", 0.1)
        self.initialized = False
        self.metrics = {"projections": 0}
        
    async def initialize(self):
        logger.info("Initializing Alpha Decay Model")
        self.initialized = True
        
    async def project(self, current_alpha: Dict[str, float], months: int) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        projected = {k: v * np.exp(-self.decay_rate * months / 12) for k, v in current_alpha.items()}
        self.metrics["projections"] += 1
        return projected
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
