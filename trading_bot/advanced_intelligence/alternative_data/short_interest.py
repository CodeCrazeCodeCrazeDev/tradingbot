"""
Idea #60: Short Interest Monitor
==================================
Track short interest and borrowing costs.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShortInterestMonitor:
    """Monitor short interest for trading signals."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.short_data: Dict[str, List[Dict]] = {}
        self.initialized = False
        self.metrics = {"symbols_tracked": 0}
        
    async def initialize(self):
        logger.info("Initializing Short Interest Monitor")
        self.initialized = True
        
    async def track_short_interest(self, symbol: str, short_pct: float, borrow_rate: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        if symbol not in self.short_data:
            self.short_data[symbol] = []
        self.short_data[symbol].append({"short_pct": short_pct, "borrow_rate": borrow_rate, "timestamp": datetime.now()})
        self.metrics["symbols_tracked"] = len(self.short_data)
        return {"symbol": symbol, "short_interest": short_pct, "squeeze_risk": "high" if short_pct > 20 else "low"}
    
    async def detect_squeeze_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        for symbol, data in self.short_data.items():
            if data and data[-1]["short_pct"] > 15:
                candidates.append({"symbol": symbol, "short_pct": data[-1]["short_pct"], "borrow_rate": data[-1]["borrow_rate"]})
        return sorted(candidates, key=lambda x: x["short_pct"], reverse=True)
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.short_data.clear()
        self.initialized = False
