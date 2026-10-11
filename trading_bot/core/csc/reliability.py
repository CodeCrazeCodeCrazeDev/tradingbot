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
            # Trust ramp: unmeasured influence must sit below proven-good
            # (~1.5+) but above proven-bad (~0.1). A flat 1.0 floor let
            # untested advisors out-vote measured-bad ones; ramping
            # 0.5 -> 1.0 across n preserves a uniform start (the tilt is
            # normalized, so an all-new stack still votes) while new
            # entrants can no longer out-influence a measured advisor.
            n = agent_regime_metrics.total_predictions if agent_regime_metrics else 0
            return 0.5 + 0.05 * n

        # Higher calibration error -> Lower weight
        # Higher precision -> Higher weight
        reliability_score = agent_regime_metrics.precision * (1.0 - agent_regime_metrics.calibration_error)
        return max(0.1, min(2.0, reliability_score * 2.0))

    # Regime-conditional directional eligibility: an advisor whose
    # measured precision in a regime is significantly below chance is
    # demoted to evidence-only — its direction stops voting in that
    # regime rather than dragging consensus. 0.35 sits ~2 SEs below
    # 0.5 at n=10, so noise doesn't flip eligibility; n<10 stays
    # eligible (the trust ramp governs unmeasured influence).
    DIRECTION_MIN_PRECISION = 0.35
    DIRECTION_MIN_SAMPLES = 10

    def eligible_direction(self, agent_id: str, regime: str) -> bool:
        """False when the agent's measured regime precision is
        significantly below chance — systematically-wrong votes are
        evidence, not signal. (Inverting them is a research question,
        not a live path — it would double-count the same data that
        measured them.)"""
        m = self.metrics.get(agent_id, {}).get(regime)
        if not m or m.total_predictions < self.DIRECTION_MIN_SAMPLES:
            return True
        return m.precision >= self.DIRECTION_MIN_PRECISION

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
