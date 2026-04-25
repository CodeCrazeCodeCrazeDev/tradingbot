"""
Idea #107: Circuit Breaker Monitor
===================================
Monitor circuit breaker conditions.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerMonitor:
    """Monitor trading halts."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.levels = [0.07, 0.13, 0.20]
        self.initialized = False
        self.metrics = {"triggers": 0}
        
    async def initialize(self):
        logger.info("Initializing Circuit Breaker Monitor")
        self.initialized = True
        
    async def check(self, current_price: float, reference_price: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        decline = (reference_price - current_price) / reference_price if reference_price > 0 else 0
        level = 0
        for i, l in enumerate(self.levels):
            if decline >= l:
                level = i + 1
        if level > 0:
            self.metrics["triggers"] += 1
        return {"level": level, "decline": float(decline), "halt": level >= 1}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
