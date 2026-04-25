"""
Idea #118: Spread Capture Strategy
=====================================
Capture bid-ask spread opportunities.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SpreadCaptureStrategy:
    """Capture bid-ask spreads."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_spread = self.config.get("min_spread", 0.001)
        self.initialized = False
        self.metrics = {"captures": 0}
        
    async def initialize(self):
        logger.info("Initializing Spread Capture Strategy")
        self.initialized = True
        
    async def evaluate(self, bid: float, ask: float, volume: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        spread = (ask - bid) / ((ask + bid) / 2) if (ask + bid) > 0 else 0
        capture = spread > self.min_spread and volume > 1000
        if capture:
            self.metrics["captures"] += 1
        return {"should_capture": capture, "spread_bps": float(spread * 10000), "expected_pnl": float(spread * volume * 0.5)}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
