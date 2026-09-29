"""
PHCE-D Module 7: Decision Policy Engine

Map verified, cost-adjusted, scenario-conditioned uncertainty into an allowed action.

Hard rules:
- Zero LLM cost
- No rewarding weak positive expectancy with action
- No ignoring uncertainty width
- No collapsing unknown into hold
- Policy thresholds must be tied to realized outcomes
- No measurable uplift versus simpler gating baseline → kill

Latency budget: 1-5 ms

Policy rules:
- BUY: direction long, verification passed, net edge positive after costs,
        credal lower > threshold, ambiguity < threshold, gateway passes
- SELL: same as BUY but short/exit
- HOLD: existing position, evidence doesn't justify state change
- NO_TRADE: no actionable edge, uncertainty too high, costs absorb edge
- RESEARCH_ONLY: interesting but incomplete validation
- NEEDS_MORE_EVIDENCE: hypothesis might be valid but sample/freshness insufficient
- PAPER_TRADE_CANDIDATE: passed decision criteria, safe for paper trade
- REJECTED: invalid hypothesis, failed verification, failed gateway
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .core_types import (
    ContradictionClassification,
    CredalBounds,
    DecisionLane,
    DecisionOutput,
    DecisionRationale,
    Hypothesis,
    HypothesisStatus,
    LatencyClass,
    LatencyPolicyRule,
    ScenarioSet,
    VerificationReport,
    DEFAULT_LATENCY_POLICIES,
)

logger = logging.getLogger(__name__)


@dataclass
class PolicyConfig:
    """Configuration for the decision policy engine."""
    # Edge thresholds (in bps, after cost)
    min_edge_for_buy_bps: float = 5.0
    min_edge_for_sell_bps: float = 5.0
    # Credal thresholds
    buy_credal_lower_threshold: float = 0.6
    sell_credal_lower_threshold: float = 0.6
    max_ambiguity_for_action: float = 0.4
    # Sample size
    min_sample_for_trade_action: int = 30
    # Cold start: insufficient sample → RESEARCH_ONLY, never BUY/SELL/PAPER_TRADE
    cold_start_min_trades: int = 10
    # Latency policies
    latency_policies: List[LatencyPolicyRule] = field(
        default_factory=lambda: list(DEFAULT_LATENCY_POLICIES)
    )


@dataclass
class PolicyResult:
    """Result of the decision policy evaluation."""
    output: DecisionOutput
    rationale: DecisionRationale
    processing_time_ms: float


class DecisionPolicyEngine:
    """
    Module 7: Decision Policy Engine

    Maps verified, cost-adjusted, scenario-conditioned uncertainty
    into one of the allowed decision outputs.

    No contradiction as output. No prose. One action class.

    Kill criteria:
    - No measurable uplift versus simpler gating baseline
    - Policy approves trades that fail cost-adjusted expectancy
    - Policy cannot explain abstentions and approvals in rule form
    """

    def __init__(self, config: Optional[PolicyConfig] = None):
        self.config = config or PolicyConfig()
        self._latency_map = {p.latency_class: p for p in self.config.latency_policies}

        # Statistics
        self.total_decisions = 0
        self.by_output: Dict[str, int] = {}
        self.cold_start_violations = 0

    def decide(
        self,
        hypothesis: Hypothesis,
        verification: VerificationReport,
        scenario_set: Optional[ScenarioSet],
        contradiction: Optional[ContradictionClassification],
        credal: CredalBounds,
        portfolio_context: Optional[Dict[str, Any]],
        latency_class: LatencyClass,
        sample_size: int = 0,
    ) -> PolicyResult:
        """
        Apply the decision policy to produce one final classification.

        Args:
            hypothesis: The hypothesis being evaluated
            verification: Verification report
            scenario_set: Optional scenario set
            contradiction: Optional contradiction classification
            credal: Credal probability bounds
            portfolio_context: Current portfolio state
            latency_class: Latency tier for this decision
            sample_size: Number of historical observations

        Returns:
            PolicyResult with the final decision output and rationale
        """
        start = time.monotonic()
        self.total_decisions += 1

        # Get latency policy — more time = better verification, NOT looser approval
        latency_policy = self._latency_map.get(latency_class)
        threshold_multiplier = 1.0
        if latency_policy:
            threshold_multiplier = latency_policy.threshold_multiplier

        # Build rationale
        rationale = DecisionRationale(
            edge_before_cost_bps=verification.edge_before_cost_bps,
            edge_after_cost_bps=verification.edge_after_cost_bps,
            credal_lower=credal.prob_lower,
            credal_upper=credal.prob_upper,
            ambiguity_score=credal.ambiguity_score,
            scenario_matched=None,
            contradiction_type=contradiction.contradiction_type.value if contradiction else None,
            verification_flags={k: v.value for k, v in verification.flags.items()},
        )

        # Match scenario
        if scenario_set and scenario_set.scenarios:
            best = max(scenario_set.scenarios, key=lambda s: s.applicability_score)
            rationale.scenario_matched = best.name

        # ── Decision cascade ──────────────────────────────────────────────

        # Step 1: Check if hypothesis is retired/suspended
        if hypothesis.status in (HypothesisStatus.RETIRED, HypothesisStatus.SUSPENDED):
            output = DecisionOutput.REJECTED
            rationale.kill_reason = f"hypothesis_status_{hypothesis.status.value}"

        # Step 2: Cold start check — insufficient sample NEVER produces trade-positive
        elif sample_size < self.config.cold_start_min_trades and sample_size > 0:
            output = DecisionOutput.RESEARCH_ONLY
            rationale.kill_reason = f"cold_start_sample_{sample_size}_below_{self.config.cold_start_min_trades}"

        # Step 3: Zero sample → NEEDS_MORE_EVIDENCE
        elif sample_size == 0:
            output = DecisionOutput.NEEDS_MORE_EVIDENCE
            rationale.kill_reason = "zero_sample_size"

        # Step 4: Invalid hypothesis from contradiction
        elif contradiction and contradiction.contradiction_type.value == "invalid_hypothesis":
            output = DecisionOutput.REJECTED
            rationale.kill_reason = "invalid_hypothesis"

        # Step 5: Model conflict from contradiction
        elif contradiction and contradiction.contradiction_type.value == "model_conflict":
            output = DecisionOutput.REJECTED
            rationale.kill_reason = "model_conflict"

        # Step 6: Verification hard failures
        elif verification.any_fail():
            # If cost-adjusted edge is negative, clear rejection
            if verification.edge_after_cost_bps <= 0:
                output = DecisionOutput.REJECTED
                rationale.kill_reason = "edge_after_cost_negative"
            elif not verification.sign_consistent:
                output = DecisionOutput.NO_TRADE
                rationale.kill_reason = "sign_inconsistent"
            else:
                output = DecisionOutput.REJECTED
                rationale.kill_reason = "verification_failed"

        # Step 7: Ambiguity too high for action
        elif credal.ambiguity_score > self.config.max_ambiguity_for_action * threshold_multiplier:
            output = DecisionOutput.NO_TRADE
            rationale.kill_reason = f"ambiguity_{credal.ambiguity_score:.2f}_above_threshold"

        # Step 8: Credal bounds not actionable
        elif not credal.actionable:
            output = DecisionOutput.NO_TRADE
            rationale.kill_reason = "credal_bounds_not_actionable"

        # Step 9: Edge below minimum after cost adjustment
        elif verification.edge_after_cost_bps < self.config.min_edge_for_buy_bps * threshold_multiplier:
            if verification.edge_after_cost_bps > 0:
                # Positive edge but below threshold
                output = DecisionOutput.NO_TRADE
                rationale.kill_reason = f"edge_{verification.edge_after_cost_bps:.1f}bps_below_threshold"
            else:
                output = DecisionOutput.REJECTED
                rationale.kill_reason = "edge_after_cost_non_positive"

        # Step 10: Check for BUY/SELL/PAPER_TRADE_CANDIDATE
        elif hypothesis.direction == "long" and credal.prob_lower >= self.config.buy_credal_lower_threshold * threshold_multiplier:
            # Strong enough for paper trade candidacy
            if sample_size >= self.config.min_sample_for_trade_action:
                output = DecisionOutput.PAPER_TRADE_CANDIDATE
            else:
                # Not enough sample for even paper trade
                output = DecisionOutput.RESEARCH_ONLY
                rationale.kill_reason = f"sample_{sample_size}_below_min_{self.config.min_sample_for_trade_action}"

        elif hypothesis.direction == "short" and credal.prob_lower >= self.config.sell_credal_lower_threshold * threshold_multiplier:
            if sample_size >= self.config.min_sample_for_trade_action:
                output = DecisionOutput.PAPER_TRADE_CANDIDATE
            else:
                output = DecisionOutput.RESEARCH_ONLY
                rationale.kill_reason = f"sample_{sample_size}_below_min_{self.config.min_sample_for_trade_action}"

        # Step 11: Insufficient evidence
        elif verification.any_high_trust_unknown():
            output = DecisionOutput.NEEDS_MORE_EVIDENCE
            rationale.kill_reason = "high_trust_verification_unknown"

        # Step 12: Contradiction says needs more evidence
        elif contradiction and contradiction.resolution_path == DecisionOutput.NEEDS_MORE_EVIDENCE:
            output = DecisionOutput.NEEDS_MORE_EVIDENCE

        # Step 13: Hold — existing position, no justification to change
        elif portfolio_context and portfolio_context.get("has_position", False):
            output = DecisionOutput.HOLD

        # Step 14: Default — no actionable edge
        else:
            output = DecisionOutput.NO_TRADE

        # Update stats
        output_key = output.value
        self.by_output[output_key] = self.by_output.get(output_key, 0) + 1

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            f"Decision: {output.value} for {hypothesis.name} "
            f"edge_after_cost={verification.edge_after_cost_bps:.1f}bps "
            f"credal=[{credal.prob_lower:.2f},{credal.prob_upper:.2f}] "
            f"in {elapsed:.1f}ms"
        )

        return PolicyResult(
            output=output,
            rationale=rationale,
            processing_time_ms=elapsed,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return policy engine statistics."""
        return {
            "total_decisions": self.total_decisions,
            "by_output": self.by_output,
            "cold_start_violations": self.cold_start_violations,
            "abstention_rate": sum(
                v for k, v in self.by_output.items()
                if k in {o.value for o in DecisionOutput.abstention()}
            ) / max(1, self.total_decisions),
        }
