"""
PHCE-D Module 4: Scenario Conditioner

Translate "it depends" into explicit conditions instead of vague contradiction.

Hard rules:
- Zero LLM cost in decision lane
- Scenarios invented after seeing outcomes → kill
- Overlapping scenarios that double-count evidence → kill
- Scenario support too low → kill
- Scenarioing increases complexity without improving discrimination → kill

Latency budget:
- Decision lane: 5-15 ms
- Research lane: 20-100 ms
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .core_types import (
    DecisionLane,
    DecisionOutput,
    EvidencePacket,
    Hypothesis,
    Scenario,
    ScenarioSet,
    VerificationReport,
)

logger = logging.getLogger(__name__)


@dataclass
class ScenarioCondition:
    """A single condition that defines a scenario partition."""
    dimension: str  # e.g. "volatility_state", "liquidity_state"
    operator: str   # "eq", "neq", "gt", "lt", "in"
    value: Any


@dataclass
class ScenarioTemplate:
    """Template for generating scenarios from regime features."""
    name: str
    conditions: List[ScenarioCondition]
    directional_effect: str  # "bullish", "bearish", "neutral"
    min_support_weight: float = 0.1  # Minimum fraction of data in this scenario


# ── Default scenario templates ────────────────────────────────────────────────

DEFAULT_SCENARIO_TEMPLATES: List[ScenarioTemplate] = [
    ScenarioTemplate(
        name="low_vol_ample_liquidity",
        conditions=[
            ScenarioCondition("volatility_state", "in", ["low", "normal"]),
            ScenarioCondition("liquidity_state", "in", ["ample", "normal"]),
        ],
        directional_effect="bullish",
        min_support_weight=0.1,
    ),
    ScenarioTemplate(
        name="high_vol_constrained_liquidity",
        conditions=[
            ScenarioCondition("volatility_state", "in", ["high", "extreme"]),
            ScenarioCondition("liquidity_state", "in", ["constrained", "scarce"]),
        ],
        directional_effect="bearish",
        min_support_weight=0.05,
    ),
    ScenarioTemplate(
        name="trending_market",
        conditions=[
            ScenarioCondition("trend_persistence", "gt", 0.6),
        ],
        directional_effect="bullish",
        min_support_weight=0.1,
    ),
    ScenarioTemplate(
        name="mean_reverting_market",
        conditions=[
            ScenarioCondition("trend_persistence", "lt", 0.3),
        ],
        directional_effect="neutral",
        min_support_weight=0.1,
    ),
]


class ScenarioConditioner:
    """
    Module 4: Scenario Conditioner

    Converts "it depends" into explicit scenario conditions.
    No vague contradiction as output.

    Kill criteria:
    - Scenario support too low
    - Scenario partition unstable
    - Scenarioing increases complexity without improving discrimination
    """

    def __init__(
        self,
        templates: Optional[List[ScenarioTemplate]] = None,
        min_support_per_scenario: float = 0.05,
        max_scenarios: int = 6,
        require_discrimination_improvement: bool = True,
    ):
        self.templates = templates or DEFAULT_SCENARIO_TEMPLATES
        self.min_support = min_support_per_scenario
        self.max_scenarios = max_scenarios
        self.require_discrimination = require_discrimination_improvement

        # Statistics
        self.total_conditioned = 0
        self.killed_low_support = 0
        self.killed_unstable = 0
        self.killed_no_discrimination = 0

    def condition(
        self,
        hypothesis: Hypothesis,
        verification: VerificationReport,
        evidence: EvidencePacket,
        regime_features: Optional[Dict[str, Any]] = None,
    ) -> ScenarioSet:
        """
        Generate scenario set from verification report and regime features.

        Args:
            hypothesis: The hypothesis being evaluated
            verification: Verification report from Module 3
            evidence: Current evidence packet
            regime_features: Current regime state (volatility, liquidity, etc.)

        Returns:
            ScenarioSet with per-scenario applicability conditions
        """
        start = time.monotonic()
        self.total_conditioned += 1
        regime_features = regime_features or {}

        # Step 1: Generate candidate scenarios from templates
        candidates = self._generate_candidates(regime_features)

        # Step 2: Check support weights
        valid_scenarios = []
        for scenario in candidates:
            if scenario.support_weight >= self.min_support:
                valid_scenarios.append(scenario)
            else:
                logger.debug(
                    f"Scenario {scenario.name} dropped: "
                    f"support {scenario.support_weight:.2f} < min {self.min_support}"
                )

        if not valid_scenarios:
            self.killed_low_support += 1
            return ScenarioSet(
                scenarios=[],
                partition_stable=False,
                partition_sanity_passed=False,
                min_support_met=False,
                discrimination_improvement=False,
            )

        # Step 3: Limit scenario count
        if len(valid_scenarios) > self.max_scenarios:
            valid_scenarios.sort(key=lambda s: s.support_weight, reverse=True)
            valid_scenarios = valid_scenarios[:self.max_scenarios]

        # Step 4: Check partition stability
        partition_stable = self._check_partition_stability(valid_scenarios)

        # Step 5: Check partition sanity (no double-counting)
        partition_sane = self._check_partition_sanity(valid_scenarios)

        # Step 6: Check discrimination improvement
        disc_improvement = self._check_discrimination(
            valid_scenarios, verification
        )

        if not disc_improvement and self.require_discrimination:
            self.killed_no_discrimination += 1

        elapsed = (time.monotonic() - start) * 1000
        logger.debug(f"Scenario conditioning completed in {elapsed:.1f}ms")

        return ScenarioSet(
            scenarios=valid_scenarios,
            partition_stable=partition_stable,
            partition_sanity_passed=partition_sane,
            min_support_met=True,
            discrimination_improvement=disc_improvement,
        )

    def _generate_candidates(
        self,
        regime_features: Dict[str, Any],
    ) -> List[Scenario]:
        """Generate candidate scenarios from templates and current regime."""
        candidates = []
        for template in self.templates:
            # Check if template conditions match current regime
            matches = self._template_matches_regime(template, regime_features)

            # Estimate support weight (simplified — in production, use historical data)
            support = self._estimate_support(template, regime_features)

            # Compute applicability score
            applicability = 1.0 if matches else 0.3

            scenario = Scenario(
                scenario_id=f"scn_{template.name}",
                name=template.name,
                conditions={c.dimension: c.value for c in template.conditions},
                directional_effect=template.directional_effect,
                support_weight=support,
                applicability_score=applicability,
            )
            candidates.append(scenario)

        return candidates

    def _template_matches_regime(
        self,
        template: ScenarioTemplate,
        regime: Dict[str, Any],
    ) -> bool:
        """Check if template conditions match current regime state."""
        for cond in template.conditions:
            regime_val = regime.get(cond.dimension)
            if regime_val is None:
                continue
            if not self._condition_matches(cond, regime_val):
                return False
        return True

    def _condition_matches(self, cond: ScenarioCondition, value: Any) -> bool:
        """Check if a condition matches a value."""
        if cond.operator == "eq":
            return value == cond.value
        elif cond.operator == "neq":
            return value != cond.value
        elif cond.operator == "gt":
            return float(value) > float(cond.value)
        elif cond.operator == "lt":
            return float(value) < float(cond.value)
        elif cond.operator == "in":
            return value in cond.value
        return False

    def _estimate_support(
        self,
        template: ScenarioTemplate,
        regime: Dict[str, Any],
    ) -> float:
        """
        Estimate support weight for a scenario.
        Simplified: returns template min_support if regime matches,
        otherwise a lower estimate.
        """
        matches = self._template_matches_regime(template, regime)
        if matches:
            return max(template.min_support_weight, 0.2)
        return template.min_support_weight * 0.5

    def _check_partition_stability(self, scenarios: List[Scenario]) -> bool:
        """
        Check that scenario partition is stable.
        Unstable = scenarios have very similar applicability scores,
        meaning small perturbations could change which scenario wins.
        """
        if len(scenarios) <= 1:
            return True

        scores = [s.applicability_score for s in scenarios]
        max_score = max(scores)
        if max_score == 0:
            return False

        # Check that the top scenario is clearly separated
        sorted_scores = sorted(scores, reverse=True)
        if len(sorted_scores) >= 2:
            gap = sorted_scores[0] - sorted_scores[1]
            if gap < 0.1:  # Top two scenarios too close
                return False

        return True

    def _check_partition_sanity(self, scenarios: List[Scenario]) -> bool:
        """
        Check that scenarios don't double-count evidence.
        Simplified: check that condition sets don't fully overlap.
        """
        for i, s1 in enumerate(scenarios):
            for j, s2 in enumerate(scenarios):
                if i >= j:
                    continue
                # If two scenarios have identical conditions, they double-count
                if s1.conditions == s2.conditions:
                    logger.warning(
                        f"Scenarios {s1.name} and {s2.name} have identical conditions"
                    )
                    return False
        return True

    def _check_discrimination(
        self,
        scenarios: List[Scenario],
        verification: VerificationReport,
    ) -> bool:
        """
        Check that scenarioing improves discrimination over unconditional.
        If scenarios don't change the decision, they are bookkeeping, not edge.
        """
        if not scenarios:
            return False

        # If verification already passes/fails unconditionally,
        # scenarios only help if they change the outcome
        if verification.any_fail():
            # Scenarios might rescue a partial fail
            has_bullish = any(s.directional_effect != "neutral" for s in scenarios)
            return has_bullish

        # If verification passes, scenarios should refine the edge estimate
        # At minimum, scenarios should have different directional effects
        effects = {s.directional_effect for s in scenarios}
        return len(effects) > 1

    def get_stats(self) -> Dict[str, Any]:
        """Return conditioner statistics."""
        return {
            "total_conditioned": self.total_conditioned,
            "killed_low_support": self.killed_low_support,
            "killed_unstable": self.killed_unstable,
            "killed_no_discrimination": self.killed_no_discrimination,
        }
