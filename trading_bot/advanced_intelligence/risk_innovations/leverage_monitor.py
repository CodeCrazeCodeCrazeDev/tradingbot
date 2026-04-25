"""
Idea #77: Leverage Monitor
============================
Monitor and control leverage levels.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class LeverageMonitor:
    """Monitor leverage levels."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_leverage = self.config.get("max_leverage", 2.0)
        self.initialized = False
        self.metrics = {"checks": 0}
        
    async def initialize(self):
        logger.info("Initializing Leverage Monitor")
        self.initialized = True
        
    async def check_leverage(self, gross_exposure: float, equity: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        leverage = gross_exposure / equity if equity > 0 else 0
        self.metrics["checks"] += 1
        return {"leverage": float(leverage), "max_allowed": self.max_leverage, "breach": leverage > self.max_leverage}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
