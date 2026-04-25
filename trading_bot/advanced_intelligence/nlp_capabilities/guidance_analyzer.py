"""
Idea #166: Guidance Language Analysis
========================================
Detect changes in forward guidance language.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GuidanceAnalyzer:
    """Analyze guidance language."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"analyses": 0}
        
    async def initialize(self):
        logger.info("Initializing Guidance Analyzer")
        self.initialized = True
        
    async def analyze(self, current_guidance: str, previous_guidance: str) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        positive_words = ["increase", "growth", "strong", "confident", "raise"]
        negative_words = ["decrease", "decline", "weak", "cautious", "lower"]
        current_score = sum(1 for w in positive_words if w in current_guidance.lower()) - sum(1 for w in negative_words if w in current_guidance.lower())
        previous_score = sum(1 for w in positive_words if w in previous_guidance.lower()) - sum(1 for w in negative_words if w in previous_guidance.lower())
        change = current_score - previous_score
        self.metrics["analyses"] += 1
        return {"current_tone": "positive" if current_score > 0 else "negative" if current_score < 0 else "neutral", "change": int(change), "revision": "up" if change > 0 else "down" if change < 0 else "unchanged"}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
