"""
Idea #106: Flash Crash Detector
=================================
Detect flash crash conditions.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FlashCrashDetector:
    """Detect flash crash events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.threshold = self.config.get("threshold", 0.05)
        self.initialized = False
        self.metrics = {"detections": 0}
        
    async def initialize(self):
        logger.info("Initializing Flash Crash Detector")
        self.initialized = True
        
    async def detect(self, prices: List[float], window: int = 10) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        if len(prices) < window:
            return {"flash_crash": False, "decline": 0}
        recent = prices[-window:]
        max_price = max(recent)
        min_price = min(recent)
        decline = (max_price - min_price) / max_price if max_price > 0 else 0
        is_crash = decline > self.threshold
        if is_crash:
            self.metrics["detections"] += 1
        return {"flash_crash": is_crash, "decline": float(decline), "duration_bars": window}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
