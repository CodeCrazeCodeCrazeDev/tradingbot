"""
Idea #59: Analyst Revision Tracking
=====================================
Track analyst estimate revisions and upgrades/downgrades.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AnalystRevisionTracker:
    """Track analyst revisions for trading signals."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.revisions: Dict[str, List[Dict]] = {}
        self.initialized = False
        self.metrics = {"revisions_tracked": 0}
        
    async def initialize(self):
        logger.info("Initializing Analyst Revision Tracker")
        self.initialized = True
        
    async def track_revision(self, company: str, analyst: str, old_target: float, new_target: float) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        if company not in self.revisions:
            self.revisions[company] = []
        self.revisions[company].append({"analyst": analyst, "old": old_target, "new": new_target, "timestamp": datetime.now()})
        self.metrics["revisions_tracked"] += 1
        change = (new_target - old_target) / old_target
        return {"company": company, "revision_pct": float(change), "direction": "upgrade" if change > 0 else "downgrade"}
    
    async def get_consensus_trend(self, company: str) -> Dict[str, Any]:
        revisions = self.revisions.get(company, [])
        if not revisions:
            return {"company": company, "trend": "neutral", "revision_count": 0}
        upgrades = sum(1 for r in revisions if r["new"] > r["old"])
        downgrades = len(revisions) - upgrades
        return {"company": company, "upgrades": upgrades, "downgrades": downgrades, "trend": "bullish" if upgrades > downgrades else "bearish"}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.revisions.clear()
        self.initialized = False
