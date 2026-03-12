"""
Skill #45: Urgency Classifier
=============================

Classifies order urgency based on alpha decay,
market conditions, and portfolio constraints.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UrgencyLevel(Enum):
    """Order urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UrgencyResult:
    """Urgency classification result."""
    urgency_level: UrgencyLevel
    urgency_score: float
    alpha_decay_factor: float
    market_timing_factor: float
    recommended_duration: int
    trading_signal: str


class UrgencyClassifier:
    """Classifies order execution urgency."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("UrgencyClassifier initialized")
    
    def classify(
        self,
        alpha_half_life: float,
        signal_strength: float,
        volatility: float,
        time_to_close: float = 390
    ) -> UrgencyResult:
        """Classify order urgency."""
        # Alpha decay factor
        alpha_decay = 1 - np.exp(-1 / (alpha_half_life + 1))
        
        # Market timing factor
        market_timing = volatility * 10 + (1 - time_to_close / 390)
        
        # Combined urgency score
        urgency_score = 0.5 * alpha_decay + 0.3 * signal_strength + 0.2 * market_timing
        
        # Classify
        if urgency_score > 0.8:
            level = UrgencyLevel.CRITICAL
            duration = 5
        elif urgency_score > 0.6:
            level = UrgencyLevel.HIGH
            duration = 15
        elif urgency_score > 0.4:
            level = UrgencyLevel.MEDIUM
            duration = 30
        else:
            level = UrgencyLevel.LOW
            duration = 60
        
        signal = self._generate_signal(level, urgency_score, duration)
        
        return UrgencyResult(
            urgency_level=level,
            urgency_score=urgency_score,
            alpha_decay_factor=alpha_decay,
            market_timing_factor=market_timing,
            recommended_duration=duration,
            trading_signal=signal
        )
    
    def _generate_signal(self, level: UrgencyLevel, score: float, duration: int) -> str:
        """Generate signal."""
        return f"{level.value.upper()} URGENCY ({score:.0%}): Execute within {duration} minutes"
