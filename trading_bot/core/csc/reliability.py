"""
Agent Reliability Tracking - UCA-2026 Core
=========================================

Calculates calibration metrics (ECE, Brier) and predictive precision/recall
per agent and market regime.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ReliabilityMetrics:
    agent_id: str
    regime: str
    calibration_error: float = 0.0  # Expected Calibration Error
    brier_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    false_positives: int = 0
    false_negatives: int = 0
    total_predictions: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class ReliabilityTracker:
    """
    Tracks and updates agent reliability across different market regimes.
    """
    def __init__(self):
        self.metrics: Dict[str, Dict[str, ReliabilityMetrics]] = {} # agent_id -> {regime: metrics}

    def get_agent_weight(self, agent_id: str, regime: str) -> float:
        """
        Calculates a dynamic weight for an agent based on its regime-specific reliability.
        """
        agent_regime_metrics = self.metrics.get(agent_id, {}).get(regime)
        if not agent_regime_metrics or agent_regime_metrics.total_predictions < 10:
            return 1.0 # Default weight for new/untracked agents

        # Higher calibration error -> Lower weight
        # Higher precision -> Higher weight
        reliability_score = agent_regime_metrics.precision * (1.0 - agent_regime_metrics.calibration_error)
        return max(0.1, min(2.0, reliability_score * 2.0))

    def update_metrics(self, agent_id: str, regime: str, was_correct: bool, confidence: float):
        """
        Updates metrics after a trade outcome is known.
        """
        if agent_id not in self.metrics:
            self.metrics[agent_id] = {}
        if regime not in self.metrics[agent_id]:
            self.metrics[agent_id][regime] = ReliabilityMetrics(agent_id=agent_id, regime=regime)

        m = self.metrics[agent_id][regime]
        m.total_predictions += 1

        # Incremental Brier Score update
        error = (confidence - (1.0 if was_correct else 0.0)) ** 2
        m.brier_score = (m.brier_score * (m.total_predictions - 1) + error) / m.total_predictions

        # Update precision/recall (Simplified)
        if was_correct:
            m.precision = (m.precision * (m.total_predictions - 1) + 1.0) / m.total_predictions
        else:
            m.false_positives += 1
            m.precision = (m.precision * (m.total_predictions - 1)) / m.total_predictions

        m.last_updated = datetime.utcnow()
        logger.debug(f"Reliability updated for {agent_id} in {regime}: precision={m.precision:.2f}")
