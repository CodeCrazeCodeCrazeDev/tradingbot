"""
PHCE-D Module 2: Hypothesis Generator

Produce a falsifiable market claim with explicit assumptions, horizon,
trigger, and expected edge source.

Hard rules:
- No falsifiable trigger → kill
- No invalidation rule → kill
- Expected gross edge below likely transaction costs → kill
- Claim depends only on unverified LLM reasoning → kill
- Unresolved leakage risk in lineage → kill
- MVP: one hypothesis at a time

Latency budget:
- Decision lane MVP: 1-5 ms using deterministic templates only
- Research lane: up to 500 ms for optional LLM-assisted proposal

Cost budget:
- Decision lane: zero LLM cost
- Research lane: cap at one low-cost proposal pass per evidence packet
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from .core_types import (
    DecisionLane,
    DecisionOutput,
    Hypothesis,
    HypothesisLineage,
    HypothesisStatus,
    LeakageRisk,
    PHCEDError,
    LeakageDetectedError,
)

logger = logging.getLogger(__name__)


@dataclass
class HypothesisTemplate:
    """
    A deterministic hypothesis template — no LLM required.
    Templates are the only way hypotheses are generated in the decision lane.
    """
    template_name: str
    direction: str  # "long" or "short"
    horizon: str
    expected_mechanism: str
    invalidation_conditions: List[str]
    min_edge_threshold_bps: float
    required_verifier_set: List[str]
    required_inputs: List[str]
    forbidden_inputs: List[str]
    leakage_risk: LeakageRisk = LeakageRisk.LOW
    point_in_time_required: bool = True

    def instantiate(
        self,
        symbol: str,
        evidence_kinds: set,
        now: float,
    ) -> Optional[Hypothesis]:
        """
        Create a Hypothesis from this template if the evidence supports it.
        Returns None if the template cannot be instantiated.
        """
        # Check that required evidence kinds are available
        required_kinds = set(self.required_verifier_set)
        if not required_kinds.issubset(evidence_kinds):
            logger.debug(
                f"Template {self.template_name} skipped: missing evidence "
                f"{required_kinds - evidence_kinds}"
            )
            return None

        lineage = HypothesisLineage(
            inputs=self.required_inputs,
            point_in_time_required=self.point_in_time_required,
            forbidden_inputs=self.forbidden_inputs,
            leakage_risk=self.leakage_risk,
        )

        # Kill if leakage risk is not LOW
        if lineage.is_rejected_for_leakage():
            logger.warning(
                f"Template {self.template_name} rejected: "
                f"leakage risk = {self.leakage_risk.value}"
            )
            return None

        hypothesis = Hypothesis(
            hypothesis_id="",
            name=f"{self.template_name}_{symbol}",
            direction=self.direction,
            horizon=self.horizon,
            expected_mechanism=self.expected_mechanism,
            invalidation_conditions=list(self.invalidation_conditions),
            min_edge_threshold_bps=self.min_edge_threshold_bps,
            required_verifier_set=list(self.required_verifier_set),
            lineage=lineage,
            status=HypothesisStatus.ACTIVE,
            created_at=now,
            template_name=self.template_name,
        )
        return hypothesis


@dataclass
class GenerationResult:
    """Result of hypothesis generation."""
    hypothesis: Optional[Hypothesis]
    accepted: bool
    kill_reason: Optional[str]
    template_used: Optional[str]
    processing_time_ms: float


# ── Built-in MVP Templates ────────────────────────────────────────────────────

MOMENTUM_BREAKOUT_V1 = HypothesisTemplate(
    template_name="momentum_breakout_v1",
    direction="long",
    horizon="intraday",
    expected_mechanism=(
        "Short-horizon directional signal strength exceeds threshold X, "
        "and estimated edge after fees, slippage, and market impact remains "
        "above threshold Y."
    ),
    invalidation_conditions=[
        "signal_strength_below_threshold",
        "edge_after_cost_negative",
        "spread_widens_beyond_2x_normal",
        "volume_drops_below_50th_percentile",
        "regime_shift_detected",
    ],
    min_edge_threshold_bps=5.0,
    required_verifier_set=["1m_bars", "spread_liquidity", "cost_model"],
    required_inputs=["close_price_1m", "volume_1m", "spread", "portfolio_exposure"],
    forbidden_inputs=["future_return", "post_signal_regime_label", "revised_macro_data"],
    leakage_risk=LeakageRisk.LOW,
    point_in_time_required=True,
)

MEAN_REVERSION_V1 = HypothesisTemplate(
    template_name="mean_reversion_v1",
    direction="long",
    horizon="intraday",
    expected_mechanism=(
        "Price deviation from short-term VWAP exceeds threshold, "
        "reversion expected within N bars. Edge must survive costs."
    ),
    invalidation_conditions=[
        "deviation_below_threshold",
        "edge_after_cost_negative",
        "trending_market_regime_active",
        "liquidity_insufficient_for_entry",
    ],
    min_edge_threshold_bps=5.0,
    required_verifier_set=["1m_bars", "spread_liquidity", "cost_model"],
    required_inputs=["close_price_1m", "volume_1m", "vwap", "spread"],
    forbidden_inputs=["future_return", "post_signal_regime_label"],
    leakage_risk=LeakageRisk.LOW,
    point_in_time_required=True,
)

DEFAULT_TEMPLATES: List[HypothesisTemplate] = [MOMENTUM_BREAKOUT_V1, MEAN_REVERSION_V1]


class HypothesisGenerator:
    """
    Module 2: Hypothesis Generator

    MVP: one hypothesis at a time, deterministic templates only.
    No LLM in decision lane. Research lane may use one low-cost LLM pass.

    Kill criteria:
    - No falsifiable trigger
    - No invalidation rule
    - Expected gross edge below likely transaction costs
    - Claim depends only on unverified LLM reasoning
    - Unresolved leakage risk
    """

    def __init__(
        self,
        templates: Optional[List[HypothesisTemplate]] = None,
        max_active_hypotheses: int = 1,
        allow_llm_in_research: bool = True,
        min_edge_bps: float = 5.0,
        historical_failure_memory: Optional[List[Dict[str, Any]]] = None,
    ):
        self.templates = templates or DEFAULT_TEMPLATES
        self.max_active = max_active_hypotheses
        self.allow_llm_in_research = allow_llm_in_research
        self.min_edge_bps = min_edge_bps
        self.failure_memory = historical_failure_memory or []

        # Active hypotheses
        self.active_hypotheses: Dict[str, Hypothesis] = {}

        # Statistics
        self.total_generated = 0
        self.killed_no_falsifiable_trigger = 0
        self.killed_no_invalidation = 0
        self.killed_edge_below_cost = 0
        self.killed_leakage = 0
        self.killed_duplicate = 0

    def generate(
        self,
        symbol: str,
        evidence_kinds: set,
        lane: DecisionLane,
        now: Optional[float] = None,
        custom_template_name: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate one hypothesis from templates.

        In the decision lane, only deterministic templates are used.
        In the research lane, an optional LLM-assisted proposal may be added.

        Args:
            symbol: Trading symbol
            evidence_kinds: Available evidence kinds
            lane: Decision or research lane
            now: Current timestamp
            custom_template_name: If specified, use only this template

        Returns:
            GenerationResult with hypothesis if accepted, or kill reason
        """
        start = time.monotonic()
        now = now or time.time()

        # Check active hypothesis limit
        if len(self.active_hypotheses) >= self.max_active:
            elapsed = (time.monotonic() - start) * 1000
            return GenerationResult(
                hypothesis=None,
                accepted=False,
                kill_reason="max_active_hypotheses_reached",
                template_used=None,
                processing_time_ms=elapsed,
            )

        # Select template(s) to try
        templates_to_try = self.templates
        if custom_template_name:
            templates_to_try = [
                t for t in self.templates
                if t.template_name == custom_template_name
            ]
            if not templates_to_try:
                elapsed = (time.monotonic() - start) * 1000
                return GenerationResult(
                    hypothesis=None,
                    accepted=False,
                    kill_reason=f"template_not_found: {custom_template_name}",
                    template_used=None,
                    processing_time_ms=elapsed,
                )

        # Try each template until one succeeds
        for template in templates_to_try:
            hypothesis = template.instantiate(symbol, evidence_kinds, now)
            if hypothesis is None:
                continue

            # Validate the hypothesis
            validation = self._validate_hypothesis(hypothesis)
            if not validation["valid"]:
                elapsed = (time.monotonic() - start) * 1000
                return GenerationResult(
                    hypothesis=None,
                    accepted=False,
                    kill_reason=validation["reason"],
                    template_used=template.template_name,
                    processing_time_ms=elapsed,
                )

            # Check for duplicates
            if self._is_duplicate(hypothesis):
                self.killed_duplicate += 1
                continue

            # Register
            self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis
            self.total_generated += 1

            elapsed = (time.monotonic() - start) * 1000
            return GenerationResult(
                hypothesis=hypothesis,
                accepted=True,
                kill_reason=None,
                template_used=template.template_name,
                processing_time_ms=elapsed,
            )

        # No template matched
        elapsed = (time.monotonic() - start) * 1000
        return GenerationResult(
            hypothesis=None,
            accepted=False,
            kill_reason="no_template_matched_available_evidence",
            template_used=None,
            processing_time_ms=elapsed,
        )

    def retire_hypothesis(
        self,
        hypothesis_id: str,
        reason: str,
        now: Optional[float] = None,
    ) -> bool:
        """
        Retire a hypothesis. Most hypotheses should die.

        Retirement triggers:
        - Edge below cost floor
        - Verifier returns UNKNOWN too often
        - Paper-trade performance fails
        - Regime no longer appears
        - Repeated re-parameterization without improvement
        """
        now = now or time.time()
        hyp = self.active_hypotheses.get(hypothesis_id)
        if hyp is None:
            logger.warning(f"Hypothesis {hypothesis_id} not found for retirement")
            return False

        hyp.status = HypothesisStatus.RETIRED
        hyp.retired_at = now
        hyp.retirement_reason = reason
        del self.active_hypotheses[hypothesis_id]

        logger.info(
            f"Hypothesis {hypothesis_id} RETIRED: {reason}"
        )
        return True

    def suspend_hypothesis(self, hypothesis_id: str, reason: str) -> bool:
        """Suspend a hypothesis temporarily."""
        hyp = self.active_hypotheses.get(hypothesis_id)
        if hyp is None:
            return False
        hyp.status = HypothesisStatus.SUSPENDED
        logger.info(f"Hypothesis {hypothesis_id} SUSPENDED: {reason}")
        return True

    def _validate_hypothesis(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """
        Validate a hypothesis against kill criteria.

        Kill criteria:
        - No falsifiable trigger (no invalidation conditions)
        - No invalidation rule
        - Expected gross edge below likely transaction costs
        - Unresolved leakage risk
        """
        if not hypothesis.is_falsifiable():
            self.killed_no_invalidation += 1
            return {"valid": False, "reason": "no_invalidation_conditions"}

        if not hypothesis.invalidation_conditions:
            self.killed_no_falsifiable_trigger += 1
            return {"valid": False, "reason": "no_falsifiable_trigger"}

        if hypothesis.min_edge_threshold_bps < self.min_edge_bps:
            self.killed_edge_below_cost += 1
            return {"valid": False, "reason": "edge_below_minimum_transaction_cost"}

        if hypothesis.lineage.is_rejected_for_leakage():
            self.killed_leakage += 1
            return {"valid": False, "reason": "unresolved_leakage_risk"}

        return {"valid": True, "reason": None}

    def _is_duplicate(self, hypothesis: Hypothesis) -> bool:
        """Check if hypothesis duplicates an active one under different wording."""
        for active in self.active_hypotheses.values():
            if (active.direction == hypothesis.direction and
                    active.horizon == hypothesis.horizon and
                    active.template_name == hypothesis.template_name and
                    active.name.split("_")[0] == hypothesis.name.split("_")[0]):
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Return generator statistics."""
        return {
            "total_generated": self.total_generated,
            "active_count": len(self.active_hypotheses),
            "killed_no_falsifiable_trigger": self.killed_no_falsifiable_trigger,
            "killed_no_invalidation": self.killed_no_invalidation,
            "killed_edge_below_cost": self.killed_edge_below_cost,
            "killed_leakage": self.killed_leakage,
            "killed_duplicate": self.killed_duplicate,
            "templates_available": len(self.templates),
        }
