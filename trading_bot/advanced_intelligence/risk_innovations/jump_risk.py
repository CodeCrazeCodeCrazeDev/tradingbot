"""
Idea #90: Jump Risk Detection
===============================
Detect and model jump risk in prices.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class JumpRiskDetector:
    """Detect jump risk in prices."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.jump_threshold = self.config.get("jump_threshold", 3.0)
        self.initialized = False
        self.metrics = {"jumps_detected": 0}
        
    async def initialize(self):
        logger.info("Initializing Jump Risk Detector")
        self.initialized = True
        
    async def detect_jumps(self, returns: np.ndarray) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        std = np.std(returns)
        jumps = np.abs(returns) > self.jump_threshold * std
        jump_indices = np.where(jumps)[0].tolist()
        self.metrics["jumps_detected"] += len(jump_indices)
        return {"jump_count": int(np.sum(jumps)), "jump_indices": jump_indices, "jump_intensity": float(np.sum(jumps) / len(returns)) if len(returns) > 0 else 0}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
