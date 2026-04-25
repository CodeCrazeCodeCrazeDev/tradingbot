"""
Idea #137: Factor Crowding Detection
======================================
Avoid crowded factor exposures.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FactorCrowdingDetector:
    """Detect factor crowding."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.crowding_threshold = self.config.get("crowding_threshold", 0.8)
        self.initialized = False
        self.metrics = {"detections": 0}
        
    async def initialize(self):
        logger.info("Initializing Factor Crowding Detector")
        self.initialized = True
        
    async def detect(self, factor_flows: Dict[str, float], historical_avg: Dict[str, float]) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        crowded_factors = []
        for factor, flow in factor_flows.items():
            ratio = flow / historical_avg.get(factor, flow) if historical_avg.get(factor, 0) > 0 else 1
            if ratio > self.crowding_threshold:
                crowded_factors.append(factor)
        if crowded_factors:
            self.metrics["detections"] += len(crowded_factors)
        return {"crowded_factors": crowded_factors, "crowding_level": len(crowded_factors) / len(factor_flows) if factor_flows else 0}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
