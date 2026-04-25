"""
Idea #105: Momentum Ignition Detector
=======================================
Detect momentum ignition patterns.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MomentumIgnitionDetector:
    """Detect momentum ignition."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"detections": 0}
        
    async def initialize(self):
        logger.info("Initializing Momentum Ignition Detector")
        self.initialized = True
        
    async def detect(self, volume_profile: List[float], price_changes: List[float]) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        volume_spike = volume_profile[-1] / np.mean(volume_profile[:-1]) if len(volume_profile) > 1 and np.mean(volume_profile[:-1]) > 0 else 1
        price_momentum = sum(price_changes[-3:]) if len(price_changes) >= 3 else 0
        is_ignition = volume_spike > 3 and abs(price_momentum) > 0.02
        if is_ignition:
            self.metrics["detections"] += 1
        return {"is_ignition": is_ignition, "volume_spike": float(volume_spike), "direction": "up" if price_momentum > 0 else "down"}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
