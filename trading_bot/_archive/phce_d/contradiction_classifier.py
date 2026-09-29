"""
PHCE-D Module 5: Contradiction Classifier

Classify why evidence conflicts and route to the right outcome.

Hard rules:
- Zero LLM cost
- No contradiction as final output — must resolve to an action class
- Treating noise as contradiction → avoid
- Hiding invalidity inside "needs more evidence" → avoid
- Forced averaging of opposing signals → avoid

Latency budget: 1-5 ms

Uses the Contradiction-to-Action Routing Table (P1 #11) for deterministic routing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .core_types import (
    ContradictionClassification,
    ContradictionRoutingRule,
    ContradictionSeverity,
    ContradictionType,
    DecisionOutput,
    ScenarioSet,
    VerificationReport,
    DEFAULT_CONTRADICTION_ROUTING,
)

logger = logging.getLogger(__name__)


class ContradictionClassifier:
    """
    Module 5: Contradiction Classifier

    Classifies why evidence conflicts and routes to the correct outcome
    using a deterministic routing table.

    No contradiction is ever the final output.
    Every conflict resolves to: NO_TRADE, NEEDS_MORE_EVIDENCE,
    RESEARCH_ONLY, REJECTED, or a scenario-conditioned candidate.
    """

    def __init__(
        self,
        routing_table: Optional[List[ContradictionRoutingRule]] = None,
    ):
        self.routing_table = routing_table or DEFAULT_CONTRADICTION_ROUTING
        self._routing_map = {
            (r.contradiction_type, r.severity): r.output
            for r in self.routing_table
        }

        # Statistics
        self.total_classified = 0
        self.by_type: Dict[str, int] = {}
        self.by_severity: Dict[str, int] = {}

    def classify(
        self,
        verification: VerificationReport,
        scenario_set: Optional[ScenarioSet] = None,
    ) -> ContradictionClassification:
        """
        Classify the contradiction and determine the resolution path.

        Args:
            verification: Verification report from Module 3
            scenario_set: Optional scenario set from Module 4

        Returns:
            ContradictionClassification with type, severity, and resolution path
        """
        start = time.monotonic()
        self.total_classified += 1

        # Step 1: Determine if there is a contradiction
        contradiction_type = self._detect_contradiction_type(verification, scenario_set)
        severity = self._assess_severity(verification, contradiction_type)

        # Step 2: Route to the correct output using the routing table
        resolution = self._route(contradiction_type, severity)

        # Step 3: Determine if this can be resolved into scenario conditions
        can_resolve = self._can_resolve_to_scenario(
            contradiction_type, severity, scenario_set
        )

        # Step 4: If scenario-resolvable, upgrade resolution
        if can_resolve and resolution in (DecisionOutput.NO_TRADE, DecisionOutput.NEEDS_MORE_EVIDENCE):
            resolution = DecisionOutput.PAPER_TRADE_CANDIDATE

        # Update stats
        type_key = contradiction_type.value
        sev_key = severity.value
        self.by_type[type_key] = self.by_type.get(type_key, 0) + 1
        self.by_severity[sev_key] = self.by_severity.get(sev_key, 0) + 1

        elapsed = (time.monotonic() - start) * 1000
        logger.debug(
            f"Contradiction classified: {contradiction_type.value}/{severity.value} "
            f"→ {resolution.value} in {elapsed:.1f}ms"
        )

        return ContradictionClassification(
            contradiction_type=contradiction_type,
            severity=severity,
            resolution_path=resolution,
            explanation=self._build_explanation(contradiction_type, severity, verification),
            can_resolve_to_scenario=can_resolve,
        )

    def _detect_contradiction_type(
        self,
        verification: VerificationReport,
        scenario_set: Optional[ScenarioSet],
    ) -> ContradictionType:
        """
        Detect the type of contradiction from verification results.

        Classification logic:
        - MODEL_CONFLICT: A deterministic check fails outright
        - MEASUREMENT_CONFLICT: Different evidence sources disagree
        - SCENARIO_CONFLICT: Evidence is consistent but direction varies by scenario
        - INSUFFICIENT_EVIDENCE: Too many UNKNOWN flags
        - INVALID_HYPOTHESIS: Fundamental hypothesis issues
        """
        flags = verification.flags

        # Check for model conflict (deterministic failure)
        if verification.any_fail():
            # If cost-adjusted edge fails, that's a model conflict
            if flags.get("cost_adjusted_edge") == "fail":
                return ContradictionType.MODEL_CONFLICT
            # If skeleton key fails, the hypothesis is invalid
            if flags.get("skeleton_key") == "fail":
                return ContradictionType.INVALID_HYPOTHESIS
            # Other deterministic failures are measurement conflicts
            return ContradictionType.MEASUREMENT_CONFLICT

        # Check for insufficient evidence
        unknown_count = sum(1 for v in flags.values() if v == "unknown")
        total = len(flags)
        if total > 0 and unknown_count / total > 0.4:
            return ContradictionType.INSUFFICIENT_EVIDENCE

        # Check for scenario conflict
        if scenario_set and scenario_set.discrimination_improvement:
            effects = {s.directional_effect for s in scenario_set.scenarios}
            if len(effects) > 1:
                return ContradictionType.SCENARIO_CONFLICT

        # Default: if we got here with no clear conflict, check for noise
        if not verification.sign_consistent:
            return ContradictionType.MEASUREMENT_CONFLICT

        # No real contradiction — but if we're called, something is off
        return ContradictionType.INSUFFICIENT_EVIDENCE

    def _assess_severity(
        self,
        verification: VerificationReport,
        contradiction_type: ContradictionType,
    ) -> ContradictionSeverity:
        """
        Assess the severity of the contradiction.

        High severity = blocks any positive action
        Low severity = may be resolvable with scenario conditioning
        """
        # Model conflicts and invalid hypotheses are always high severity
        if contradiction_type in (ContradictionType.MODEL_CONFLICT, ContradictionType.INVALID_HYPOTHESIS):
            return ContradictionSeverity.HIGH

        # Check if cost-adjusted edge is negative
        if verification.edge_after_cost_bps <= 0:
            return ContradictionSeverity.HIGH

        # Check if effect size is very small
        if verification.effect_size_estimate < 2.0:  # Less than 2 bps
            return ContradictionSeverity.HIGH

        # Check unknown rate
        flags = verification.flags
        unknown_count = sum(1 for v in flags.values() if v == "unknown")
        total = len(flags)
        if total > 0 and unknown_count / total > 0.5:
            return ContradictionSeverity.HIGH

        # Default to low severity for resolvable conflicts
        return ContradictionSeverity.LOW

    def _route(
        self,
        contradiction_type: ContradictionType,
        severity: ContradictionSeverity,
    ) -> DecisionOutput:
        """Route contradiction to output using the deterministic routing table."""
        result = self._routing_map.get((contradiction_type, severity))
        if result is not None:
            return result

        # Fallback: conservative default
        if severity == ContradictionSeverity.HIGH:
            return DecisionOutput.REJECTED
        return DecisionOutput.NO_TRADE

    def _can_resolve_to_scenario(
        self,
        contradiction_type: ContradictionType,
        severity: ContradictionSeverity,
        scenario_set: Optional[ScenarioSet],
    ) -> bool:
        """
        Determine if the contradiction can be resolved into scenario conditions.

        Only scenario conflicts with low severity can be resolved.
        Everything else must route to a non-trade output.
        """
        if contradiction_type != ContradictionType.SCENARIO_CONFLICT:
            return False
        if severity == ContradictionSeverity.HIGH:
            return False
        if scenario_set is None:
            return False
        if not scenario_set.partition_stable:
            return False
        if not scenario_set.min_support_met:
            return False
        return True

    def _build_explanation(
        self,
        contradiction_type: ContradictionType,
        severity: ContradictionSeverity,
        verification: VerificationReport,
    ) -> str:
        """Build a human-readable explanation of the contradiction."""
        parts = [f"{contradiction_type.value}/{severity.value}"]

        if verification.edge_after_cost_bps <= 0:
            parts.append("edge_after_cost_negative")
        if not verification.sign_consistent:
            parts.append("sign_inconsistent")
        if verification.any_high_trust_unknown():
            parts.append("high_trust_unknown")

        failed = [k for k, v in verification.flags.items() if v == "fail"]
        if failed:
            parts.append(f"failed_checks={','.join(failed)}")

        return "; ".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Return classifier statistics."""
        return {
            "total_classified": self.total_classified,
            "by_type": self.by_type,
            "by_severity": self.by_severity,
        }
