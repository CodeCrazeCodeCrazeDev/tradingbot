"""
PHCE-D Module 6: Credal Probability Engine

Represent uncertainty as a bounded set of probabilities instead of fake point precision.

MVP: simple lower/upper bounds only.
Do not build complicated credal algebra until simple bounds fail.

Hard rules:
- Zero LLM cost
- Fake precision is forbidden
- Intervals so wide they are operationally useless → kill
- Credal bounds that do not support a distinct policy action → bookkeeping, not edge

Latency budget: 1-10 ms
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .core_types import (
    ContradictionClassification,
    CredalBounds,
    DecisionOutput,
    ScenarioSet,
    VerificationFlag,
    VerificationReport,
)

logger = logging.getLogger(__name__)


@dataclass
class CredalConfig:
    """Configuration for the credal probability engine."""
    # Thresholds for actionability
    buy_threshold_lower: float = 0.6     # Credal lower bound must exceed this for BUY
    sell_threshold_lower: float = 0.6    # Credal lower bound must exceed this for SELL
    ambiguity_action_threshold: float = 0.4  # Ambiguity above this blocks action
    # Interval width that makes bounds operationally useless
    max_interval_width: float = 0.6      # If upper - lower > this, not actionable
    # Prior reliability weights
    verification_weight: float = 0.5
    scenario_weight: float = 0.3
    prior_weight: float = 0.2


class CredalProbabilityEngine:
    """
    Module 6: Credal Probability Engine (MVP)

    Produces lower and upper probability bounds per outcome,
    an ambiguity score, and a confidence class.

    Only useful if the bounds change a decision boundary.
    If they do not affect the policy outcome, they are bookkeeping, not edge.

    Kill criteria:
    - Interval width exceeds actionability threshold
    - Credal bounds do not support a distinct policy action
    - Ambiguity remains too high after scenario conditioning
    """

    def __init__(self, config: Optional[CredalConfig] = None):
        self.config = config or CredalConfig()

        # Calibration tracking
        self._calibration_history: List[Dict[str, Any]] = []

        # Statistics
        self.total_computed = 0
        self.killed_uninformative = 0
        self.killed_ambiguity = 0

    def compute(
        self,
        verification: VerificationReport,
        scenario_set: Optional[ScenarioSet],
        contradiction: Optional[ContradictionClassification],
        prior_reliability: float = 0.5,
    ) -> CredalBounds:
        """
        Compute credal probability bounds from verification, scenarios,
        and contradiction classification.

        Args:
            verification: Verification report from Module 3
            scenario_set: Optional scenario set from Module 4
            contradiction: Optional contradiction classification from Module 5
            prior_reliability: Historical reliability of this hypothesis family (0-1)

        Returns:
            CredalBounds with lower/upper probability, ambiguity, and actionability
        """
        start = time.monotonic()
        self.total_computed += 1

        # Step 1: Base probability from verification
        base_prob = self._verification_to_probability(verification)

        # Step 2: Adjust for scenario conditioning
        scenario_adjustment = 0.0
        if scenario_set and scenario_set.discrimination_improvement:
            scenario_adjustment = self._scenario_adjustment(scenario_set)

        # Step 3: Adjust for contradiction
        contradiction_adjustment = 0.0
        if contradiction:
            contradiction_adjustment = self._contradiction_adjustment(contradiction)

        # Step 4: Compute bounds
        point_estimate = (
            base_prob * self.config.verification_weight +
            (base_prob + scenario_adjustment) * self.config.scenario_weight +
            prior_reliability * self.config.prior_weight
        )
        point_estimate = max(0.0, min(1.0, point_estimate))

        # Width of interval depends on uncertainty sources
        uncertainty_width = self._compute_uncertainty_width(
            verification, scenario_set, contradiction
        )

        prob_lower = max(0.0, point_estimate - uncertainty_width / 2)
        prob_upper = min(1.0, point_estimate + uncertainty_width / 2)

        # Apply contradiction penalty
        if contradiction_adjustment < 0:
            prob_upper = min(prob_upper, point_estimate + contradiction_adjustment)

        # Step 5: Compute ambiguity score
        ambiguity = prob_upper - prob_lower

        # Step 6: Determine actionability
        actionable = self._is_actionable(prob_lower, prob_upper, ambiguity)

        # Step 7: Determine confidence class
        confidence_class = self._classify_confidence(prob_lower, prob_upper, ambiguity)

        # Kill checks
        if ambiguity > self.config.max_interval_width:
            self.killed_uninformative += 1
            logger.debug(
                f"Credal bounds uninformative: width={ambiguity:.2f} > "
                f"max={self.config.max_interval_width}"
            )

        if ambiguity > self.config.ambiguity_action_threshold and not actionable:
            self.killed_ambiguity += 1

        elapsed = (time.monotonic() - start) * 1000
        logger.debug(
            f"Credal bounds: [{prob_lower:.2f}, {prob_upper:.2f}] "
            f"ambiguity={ambiguity:.2f} actionable={actionable} in {elapsed:.1f}ms"
        )

        return CredalBounds(
            prob_lower=prob_lower,
            prob_upper=prob_upper,
            ambiguity_score=ambiguity,
            actionable=actionable,
            confidence_class=confidence_class,
        )

    def _verification_to_probability(self, verification: VerificationReport) -> float:
        """Convert verification flags to a base probability estimate."""
        flags = verification.flags
        if not flags:
            return 0.3  # No evidence → low prior

        pass_count = sum(1 for v in flags.values() if v == VerificationFlag.PASS)
        fail_count = sum(1 for v in flags.values() if v == VerificationFlag.FAIL)
        unknown_count = sum(1 for v in flags.values() if v == VerificationFlag.UNKNOWN)
        total = len(flags)

        if total == 0:
            return 0.3

        # Weighted: passes contribute positively, fails negatively, unknowns reduce confidence
        pass_ratio = pass_count / total
        fail_ratio = fail_count / total
        unknown_ratio = unknown_count / total

        # Base probability from pass/fail ratio
        if fail_count > 0:
            base = pass_ratio / (pass_ratio + fail_ratio) * 0.8
        else:
            base = 0.5 + pass_ratio * 0.3

        # Reduce for unknowns
        base -= unknown_ratio * 0.15

        # Adjust for cost-adjusted edge
        if verification.edge_after_cost_bps > 0:
            base += min(0.1, verification.edge_after_cost_bps / 100.0)
        elif verification.edge_after_cost_bps <= 0:
            base -= 0.2

        # Adjust for sign consistency
        if not verification.sign_consistent:
            base -= 0.15

        return max(0.05, min(0.95, base))

    def _scenario_adjustment(self, scenario_set: ScenarioSet) -> float:
        """Compute probability adjustment from scenario conditioning."""
        if not scenario_set.scenarios:
            return 0.0

        # If scenarios discriminate, they reduce uncertainty
        # The best scenario's applicability score provides a positive adjustment
        best = max(scenario_set.scenarios, key=lambda s: s.applicability_score)
        if best.directional_effect in ("bullish", "bearish"):
            return best.applicability_score * 0.1
        return 0.0

    def _contradiction_adjustment(self, contradiction: ContradictionClassification) -> float:
        """Compute probability adjustment from contradiction classification."""
        adjustments = {
            "measurement_conflict": -0.1,
            "scenario_conflict": -0.05,
            "model_conflict": -0.3,
            "insufficient_evidence": -0.1,
            "invalid_hypothesis": -0.5,
        }
        return adjustments.get(contradiction.contradiction_type.value, -0.1)

    def _compute_uncertainty_width(
        self,
        verification: VerificationReport,
        scenario_set: Optional[ScenarioSet],
        contradiction: Optional[ContradictionClassification],
    ) -> float:
        """
        Compute the width of the credal interval.
        More uncertainty sources → wider interval.
        """
        width = 0.2  # Base width

        # Add width for each UNKNOWN flag
        unknown_count = sum(
            1 for v in verification.flags.values()
            if v == VerificationFlag.UNKNOWN
        )
        width += unknown_count * 0.08

        # Add width for sign inconsistency
        if not verification.sign_consistent:
            width += 0.1

        # Add width for small sample
        if verification.sample_size < 30:
            width += 0.1

        # Reduce width if scenarios are well-conditioned
        if scenario_set and scenario_set.discrimination_improvement:
            width -= 0.05

        # Add width for contradiction
        if contradiction:
            width += 0.1

        return max(0.05, min(0.8, width))

    def _is_actionable(self, lower: float, upper: float, ambiguity: float) -> bool:
        """
        Determine if the credal bounds support a distinct policy action.
        If they don't change the decision, they are bookkeeping, not edge.
        """
        # If ambiguity is too high, not actionable
        if ambiguity > self.config.ambiguity_action_threshold:
            return False

        # If lower bound exceeds buy/sell threshold, actionable
        if lower >= self.config.buy_threshold_lower:
            return True

        # If upper bound is below hold threshold, actionable (abstain)
        if upper < 0.3:
            return True

        # If interval straddles a decision boundary, it's informative
        if lower < self.config.buy_threshold_lower <= upper:
            return True

        return False

    def _classify_confidence(self, lower: float, upper: float, ambiguity: float) -> str:
        """Classify the confidence level."""
        if ambiguity < 0.1 and lower > 0.7:
            return "high"
        elif ambiguity < 0.2 and lower > 0.5:
            return "medium"
        elif ambiguity < 0.4:
            return "low"
        else:
            return "uninformative"

    def record_calibration(
        self,
        predicted_lower: float,
        predicted_upper: float,
        actual_outcome: bool,
    ) -> None:
        """
        Record calibration data for later analysis.
        The actual outcome should be a boolean: did the trade win?
        """
        self._calibration_history.append({
            "predicted_lower": predicted_lower,
            "predicted_upper": predicted_upper,
            "actual": actual_outcome,
            "covered": predicted_lower <= (1.0 if actual_outcome else 0.0) <= predicted_upper,
        })

    def get_calibration_stats(self) -> Dict[str, Any]:
        """Return calibration statistics."""
        if not self._calibration_history:
            return {"status": "no_data"}

        total = len(self._calibration_history)
        covered = sum(1 for c in self._calibration_history if c["covered"])
        avg_width = sum(
            c["predicted_upper"] - c["predicted_lower"]
            for c in self._calibration_history
        ) / total

        return {
            "total_observations": total,
            "coverage_rate": covered / total,
            "avg_interval_width": avg_width,
            "ideal_coverage": avg_width,  # For well-calibrated intervals, coverage ≈ width
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        return {
            "total_computed": self.total_computed,
            "killed_uninformative": self.killed_uninformative,
            "killed_ambiguity": self.killed_ambiguity,
            "calibration": self.get_calibration_stats(),
        }
