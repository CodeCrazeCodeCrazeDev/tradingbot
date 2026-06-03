"""
Ignorance Score Engine
======================

Computes the unified Ignorance Score (0.0-1.0) to drive system governance
and automatic risk reduction.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from .world_state import MarketWorldState, SystemMode


class IgnoranceScoreEngine:
    """
    Unified engine for computing system-wide ignorance/uncertainty.
    Enables "reduce activity when understanding decreases".
    """

    def __init__(
        self,
        warn_threshold: float = 0.3,
        defensive_threshold: float = 0.6,
        halt_threshold: float = 0.8
    ):
        self.warn_threshold = warn_threshold
        self.defensive_threshold = defensive_threshold
        self.halt_threshold = halt_threshold

        # History for tracking acceleration
        self.score_history: List[float] = []
        self.error_history: List[float] = []

    def compute_ignorance(self, world_state: MarketWorldState) -> float:
        """
        Compute unified ignorance score (0.0 to 1.0).

        Combines:
        - Epistemic Uncertainty (Model ignorance)
        - Regime Entropy (Classification uncertainty)
        - Systemic Risk (Market instability)
        - Prediction Error Acceleration (Feedback loop)
        """
        # 1. Base Epistemic Score (scaled disagreement)
        epistemic_score = min(1.0, world_state.epistemic_uncertainty / 2.0)

        # 2. Regime Confusion Score
        regime_score = min(1.0, world_state.regime_entropy)

        # 3. Systemic Instability
        instability_score = world_state.systemic_risk_level

        # 4. Error Acceleration (if history available)
        accel_score = 0.0
        if len(self.error_history) >= 3:
            recent_errors = self.error_history[-3:]
            # If error is growing
            if recent_errors[-1] > recent_errors[-2] > recent_errors[-3]:
                accel_score = 0.2

        # Weighted Combination
        ignorance_score = (
            0.4 * epistemic_score +
            0.3 * regime_score +
            0.2 * instability_score +
            0.1 * accel_score
        )

        final_score = float(np.clip(ignorance_score, 0.0, 1.0))
        self.score_history.append(final_score)

        return final_score

    def get_recommended_mode(self, ignorance_score: float) -> SystemMode:
        """
        Map ignorance score to mandatory system mode.
        """
        if ignorance_score >= self.halt_threshold:
            return SystemMode.HALT
        elif ignorance_score >= self.defensive_threshold:
            return SystemMode.DEFENSIVE
        elif ignorance_score >= self.warn_threshold:
            return SystemMode.REDUCED_RISK
        else:
            return SystemMode.NORMAL

    def register_prediction_error(self, error: float):
        """Record prediction error for acceleration detection."""
        self.error_history.append(error)
        if len(self.error_history) > 100:
            self.error_history.pop(0)

    def process_world_state(self, world_state: MarketWorldState) -> MarketWorldState:
        """
        Enrich a WorldState with ignorance score and recommended mode.
        """
        score = self.compute_ignorance(world_state)
        mode = self.get_recommended_mode(score)

        # Create new state with updated governance fields
        from dataclasses import replace
        return replace(world_state, ignorance_score=score, recommended_mode=mode)
