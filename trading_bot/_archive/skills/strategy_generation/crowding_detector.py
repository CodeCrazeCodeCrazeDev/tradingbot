"""
Skill #68: Crowding Detector
============================

Detects strategy crowding and overcrowded trades.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class CrowdingResult:
    """Crowding detection result."""
    crowding_score: float
    crowded_signals: List[str]
    uniqueness_score: float
    recommended_action: str
    trading_signal: str


class CrowdingDetector:
    """Detects strategy and trade crowding."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("CrowdingDetector initialized")
    
    def detect(self, strategy_returns: np.ndarray, market_returns: np.ndarray) -> CrowdingResult:
        """Detect crowding in strategy."""
        if len(strategy_returns) < 20:
            return self._create_empty_result()
        
        # Correlation with market (high = crowded)
        corr = np.corrcoef(strategy_returns, market_returns)[0, 1]
        crowding = abs(corr)
        
        crowded = []
        if crowding > 0.7:
            crowded.append("high_market_correlation")
        
        uniqueness = 1 - crowding
        action = "reduce_exposure" if crowding > 0.7 else "maintain"
        
        return CrowdingResult(
            crowding_score=crowding, crowded_signals=crowded,
            uniqueness_score=uniqueness, recommended_action=action,
            trading_signal=f"CROWDING: {crowding:.0%}, uniqueness {uniqueness:.0%}"
        )
    
    def _create_empty_result(self) -> CrowdingResult:
        return CrowdingResult(0, [], 0, "", "Insufficient data")
