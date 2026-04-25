"""
Idea #87: Risk Overlay Manager
================================
Overlay risk management across strategies.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RiskOverlayManager:
    """Manage risk overlay across strategies."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"overlays_applied": 0}
        
    async def initialize(self):
        logger.info("Initializing Risk Overlay Manager")
        self.initialized = True
        
    async def apply_overlay(self, strategy_risks: Dict[str, float], max_total_risk: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        total_risk = sum(strategy_risks.values())
        scale_factor = min(1.0, max_total_risk / total_risk) if total_risk > 0 else 1.0
        scaled_risks = {k: v * scale_factor for k, v in strategy_risks.items()}
        self.metrics["overlays_applied"] += 1
        return {"original_risk": float(total_risk), "scaled_risk": float(total_risk * scale_factor), "scale_factor": float(scale_factor)}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
