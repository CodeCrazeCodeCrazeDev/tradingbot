"""
Idea #138: Style Drift Monitor
==============================
Detect and correct portfolio style drift.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class StyleDriftMonitor:
    """Monitor style drift."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.drift_threshold = self.config.get("drift_threshold", 0.1)
        self.initialized = False
        self.metrics = {"alerts": 0}
        
    async def initialize(self):
        logger.info("Initializing Style Drift Monitor")
        self.initialized = True
        
    async def check_drift(self, target_exposures: Dict[str, float], current_exposures: Dict[str, float]) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        all_factors = set(target_exposures) | set(current_exposures)
        drift = {f: abs(target_exposures.get(f, 0) - current_exposures.get(f, 0)) for f in all_factors}
        max_drift = max(drift.values()) if drift else 0
        needs_rebalance = max_drift > self.drift_threshold
        if needs_rebalance:
            self.metrics["alerts"] += 1
        return {"drift_by_factor": drift, "max_drift": float(max_drift), "needs_rebalance": needs_rebalance}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
