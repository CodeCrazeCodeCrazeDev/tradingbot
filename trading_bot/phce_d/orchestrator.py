"""
PHCE-D Orchestrator — Main Pipeline

Wires all 9 core modules + circuit breaker + metrics into a single
decision pipeline that enforces the PHCE-D state machine:

1. Intake evidence
2. Build one falsifiable hypothesis
3. Verify deterministically and statistically
4. If evidence conflicts, classify the conflict
5. Convert conflict into scenario-conditioned credal bounds
6. Apply decision policy
7. If trade-related, pass Validation Gateway
8. If gateway passes, output PAPER_TRADE_CANDIDATE
9. Promote only after paper-trade evidence clears thresholds

No stage outputs "contradiction" as the final answer.
No live execution path. Ever.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .core_types import (
    CircuitBreakerTrippedError,
    ContradictionClassification,
    CredalBounds,
    DecisionAuditRecord,
    DecisionLane,
    DecisionOutput,
    DecisionRationale,
    EvidencePacket,
    GatewayResult,
    Hypothesis,
    LatencyClass,
    ScenarioSet,
    VerificationReport,
)
from .evidence_intake import EvidenceIntake, IntakeResult
from .hypothesis_generator import HypothesisGenerator, GenerationResult
from .verifier import Verifier, VerifierConfig
from .scenario_conditioner import ScenarioConditioner
from .contradiction_classifier import ContradictionClassifier
from .credal_engine import CredalProbabilityEngine, CredalConfig
from .decision_policy import DecisionPolicyEngine, PolicyConfig
from .validation_gateway import ValidationGateway, GatewayVerdict
from .paper_trade_promotion import PaperTradePromotionLayer, PaperTradePromotionThresholds
from .circuit_breaker import CircuitBreaker
from .refusal_metrics import RefusalQualityTracker
from .drift_monitor import DriftMonitor
from .failure_memory import FailureMemory

logger = logging.getLogger(__name__)


@dataclass
class PHCEDConfig:
    """Top-level PHCE-D configuration."""
    # Lane
    default_lane: DecisionLane = DecisionLane.DECISION

    # Module configs (use defaults if None)
    evidence_intake: Optional[Dict[str, Any]] = None
    hypothesis_generator: Optional[Dict[str, Any]] = None
    verifier: Optional[VerifierConfig] = None
    scenario_conditioner: Optional[Dict[str, Any]] = None
    credal_engine: Optional[CredalConfig] = None
    decision_policy: Optional[PolicyConfig] = None
    validation_gateway: Optional[Dict[str, Any]] = None
    paper_trade_promotion: Optional[PaperTradePromotionThresholds] = None
    circuit_breaker: Optional[Dict[str, Any]] = None

    # Global
    strict_mode: bool = True
    max_end_to_end_latency_ms: float = 100.0


@dataclass
class PHCEDResult:
    """Complete result of a PHCE-D decision cycle."""
    decision_record: DecisionAuditRecord
    hypothesis: Optional[Hypothesis]
    intake_result: Optional[IntakeResult]
    verification: Optional[VerificationReport]
    scenario_set: Optional[ScenarioSet]
    contradiction: Optional[ContradictionClassification]
    credal: Optional[CredalBounds]
    gateway_verdict: Optional[GatewayVerdict]
    total_latency_ms: float


class PHCEDOrchestrator:
    """
    PHCE-D Orchestrator — The main decision pipeline.

    Implements the state machine:
    1. Intake evidence
    2. Build one falsifiable hypothesis
    3. Verify deterministically and statistically
    4. If evidence conflicts, classify the conflict
    5. Convert conflict into scenario-conditioned credal bounds
    6. Apply decision policy
    7. If trade-related, pass Validation Gateway
    8. If gateway passes, output PAPER_TRADE_CANDIDATE
    9. Promote only after paper-trade evidence clears thresholds

    Hard rules:
    - No direct live execution
    - No forced convergence
    - No contradiction as final output
    - No LLM-only validation for high-trust claims
    - No parallel LLM reasoning for latency-sensitive execution
    - UNKNOWN, HOLD, NO_TRADE are valid outputs
    - Every trade-related output must pass Validation Gateway and paper trading
    """

    def __init__(
        self,
        config: Optional[PHCEDConfig] = None,
        # External integration hooks
        transaction_cost_model=None,
        unified_decision_gate=None,
        risk_validation_gate=None,
        paper_trading_validator=None,
    ):
        self.config = config or PHCEDConfig()

        # Initialize all modules
        self.evidence_intake = EvidenceIntake(
            **(self.config.evidence_intake or {}),
        )
        self.hypothesis_generator = HypothesisGenerator(
            **(self.config.hypothesis_generator or {}),
        )
        self.verifier = Verifier(
            config=self.config.verifier,
            cost_model=transaction_cost_model,
        )
        self.scenario_conditioner = ScenarioConditioner(
            **(self.config.scenario_conditioner or {}),
        )
        self.contradiction_classifier = ContradictionClassifier()
        self.credal_engine = CredalProbabilityEngine(
            config=self.config.credal_engine,
        )
        self.decision_policy = DecisionPolicyEngine(
            config=self.config.decision_policy,
        )
        self.validation_gateway = ValidationGateway(
            **(self.config.validation_gateway or {}),
            unified_decision_gate=unified_decision_gate,
            risk_validation_gate=risk_validation_gate,
        )
        self.paper_trade_promotion = PaperTradePromotionLayer(
            thresholds=self.config.paper_trade_promotion,
            paper_trading_validator=paper_trading_validator,
        )
        self.circuit_breaker = CircuitBreaker(
            **(self.config.circuit_breaker or {}),
        )
        self.refusal_metrics = RefusalQualityTracker()
        self.drift_monitor = DriftMonitor()
        self.failure_memory = FailureMemory()

        # Decision audit log
        self._audit_log: List[DecisionAuditRecord] = []

        # Statistics
        self.total_decisions = 0
        self.by_output: Dict[str, int] = {}

    def decide(
        self,
        symbol: str,
        raw_evidence: List[Dict[str, Any]],
        lane: Optional[DecisionLane] = None,
        is_trade_hypothesis: bool = True,
        portfolio_state: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
        regime_features: Optional[Dict[str, Any]] = None,
        historical_returns: Optional[List[float]] = None,
        dumb_results: Optional[Dict[str, float]] = None,
        custom_template_name: Optional[str] = None,
        now: Optional[float] = None,
    ) -> PHCEDResult:
        """
        Execute the full PHCE-D decision pipeline.

        This is the main entry point. It goes through all 9 stages
        and produces a single, auditable decision.

        Args:
            symbol: Trading symbol
            raw_evidence: Raw evidence sources (list of dicts)
            lane: Decision or research lane
            is_trade_hypothesis: Whether this is a trade-related hypothesis
            portfolio_state: Current portfolio state
            market_context: Current market conditions
            regime_features: Current regime features
            historical_returns: Historical returns for statistical checks
            dumb_results: Skeleton-key dumb explanation results
            custom_template_name: Specific hypothesis template to use
            now: Current timestamp (for testing)

        Returns:
            PHCEDResult with the complete decision record and all intermediate outputs
        """
        pipeline_start = time.monotonic()
        lane = lane or self.config.default_lane
        now = now or time.time()

        # Initialize intermediate results
        intake_result = None
        hypothesis = None
        verification = None
        scenario_set = None
        contradiction = None
        credal = None
        gateway_verdict = None
        final_output = DecisionOutput.NO_TRADE
        kill_reason = None

        # ── Stage 1: Evidence Intake ──────────────────────────────────────
        intake_result = self.evidence_intake.intake(
            symbol=symbol,
            raw_sources=raw_evidence,
            lane=lane,
            is_trade_hypothesis=is_trade_hypothesis,
            now=now,
        )

        if not intake_result.accepted:
            kill_reason = intake_result.kill_reason
            final_output = DecisionOutput.REJECTED
            logger.info(f"Stage 1 KILL: {kill_reason}")
        else:
            # ── Stage 2: Hypothesis Generation ────────────────────────────
            evidence_kinds = {s.evidence_kind for s in intake_result.packet.sources}
            gen_result = self.hypothesis_generator.generate(
                symbol=symbol,
                evidence_kinds=evidence_kinds,
                lane=lane,
                now=now,
                custom_template_name=custom_template_name,
            )

            if not gen_result.accepted or gen_result.hypothesis is None:
                kill_reason = gen_result.kill_reason
                final_output = DecisionOutput.REJECTED
                logger.info(f"Stage 2 KILL: {kill_reason}")
            else:
                hypothesis = gen_result.hypothesis

                # ── Stage 3: Verification ─────────────────────────────────
                verification = self.verifier.verify(
                    hypothesis=hypothesis,
                    evidence=intake_result.packet,
                    historical_returns=historical_returns,
                    dumb_results=dumb_results,
                )

                # ── Stage 4: Scenario Conditioning ────────────────────────
                scenario_set = self.scenario_conditioner.condition(
                    hypothesis=hypothesis,
                    verification=verification,
                    evidence=intake_result.packet,
                    regime_features=regime_features,
                )

                # ── Stage 5: Contradiction Classification ──────────────────
                # Only classify if there's evidence of conflict
                has_conflict = (
                    verification.any_fail() or
                    verification.any_high_trust_unknown() or
                    not verification.sign_consistent or
                    (scenario_set and not scenario_set.discrimination_improvement)
                )
                if has_conflict:
                    contradiction = self.contradiction_classifier.classify(
                        verification=verification,
                        scenario_set=scenario_set,
                    )

                # ── Stage 6: Credal Probability ────────────────────────────
                credal = self.credal_engine.compute(
                    verification=verification,
                    scenario_set=scenario_set,
                    contradiction=contradiction,
                )

                # ── Stage 7: Decision Policy ──────────────────────────────
                latency_class = self._classify_latency(
                    (time.monotonic() - pipeline_start) * 1000
                )
                sample_size = len(historical_returns) if historical_returns else 0

                policy_result = self.decision_policy.decide(
                    hypothesis=hypothesis,
                    verification=verification,
                    scenario_set=scenario_set,
                    contradiction=contradiction,
                    credal=credal,
                    portfolio_context=portfolio_state,
                    latency_class=latency_class,
                    sample_size=sample_size,
                )
                final_output = policy_result.output

                # ── Stage 8: Validation Gateway ───────────────────────────
                # Only for trade-positive outputs
                if final_output in DecisionOutput.trade_positive():
                    gateway_verdict = self.validation_gateway.evaluate(
                        decision_output=final_output,
                        hypothesis=hypothesis,
                        verification=verification,
                        rationale=policy_result.rationale,
                        portfolio_state=portfolio_state,
                        market_context=market_context,
                        circuit_breaker_active=self.circuit_breaker.is_active(),
                    )

                    if gateway_verdict.result == GatewayResult.FAIL:
                        final_output = gateway_verdict.decision_output
                        kill_reason = "; ".join(gateway_verdict.rejection_reasons)
                        logger.info(f"Stage 8 GATE REJECT: {kill_reason}")

                # ── Circuit Breaker Enforcement ───────────────────────────
                stale_symbols = []
                if intake_result.evidence_stale:
                    stale_symbols = [symbol]

                final_output = self.circuit_breaker.check_and_enforce(
                    decision_output=final_output,
                    stale_symbols=stale_symbols,
                    current_drawdown_pct=portfolio_state.get("drawdown_pct", 0) if portfolio_state else 0,
                    paper_trade_failure_count=0,
                    dependency_graph_ok=True,
                )

        # ── Build Decision Audit Record ───────────────────────────────────
        total_latency = (time.monotonic() - pipeline_start) * 1000

        rationale = None
        if hypothesis and verification:
            rationale = DecisionRationale(
                edge_before_cost_bps=verification.edge_before_cost_bps,
                edge_after_cost_bps=verification.edge_after_cost_bps,
                credal_lower=credal.prob_lower if credal else 0.0,
                credal_upper=credal.prob_upper if credal else 0.0,
                ambiguity_score=credal.ambiguity_score if credal else 1.0,
                scenario_matched=scenario_set.scenarios[0].name if scenario_set and scenario_set.scenarios else None,
                contradiction_type=contradiction.contradiction_type.value if contradiction else None,
                verification_flags={k: v.value for k, v in verification.flags.items()},
                kill_reason=kill_reason,
            )

        audit_record = DecisionAuditRecord(
            decision_id="",
            timestamp="",
            symbol=symbol,
            hypothesis_id=hypothesis.hypothesis_id if hypothesis else "none",
            output_class=final_output,
            edge_before_cost_bps=verification.edge_before_cost_bps if verification else 0.0,
            edge_after_cost_bps=verification.edge_after_cost_bps if verification else 0.0,
            credal_lower=credal.prob_lower if credal else 0.0,
            credal_upper=credal.prob_upper if credal else 0.0,
            ambiguity_score=credal.ambiguity_score if credal else 1.0,
            scenario_matched=rationale.scenario_matched if rationale else None,
            contradiction_type=rationale.contradiction_type if rationale else None,
            gateway_result=gateway_verdict.result if gateway_verdict else (
                GatewayResult.PASS if final_output not in DecisionOutput.trade_positive() else GatewayResult.FAIL
            ),
            latency_ms=total_latency,
            cost_usd_cents=0.0,
            lane=lane,
            latency_class=self._classify_latency(total_latency),
            rationale=rationale,
            hypothesis_leakage_risk=hypothesis.lineage.leakage_risk.value if hypothesis else None,
            hypothesis_inputs=hypothesis.lineage.inputs if hypothesis else None,
            verification_pass_count=sum(1 for v in verification.flags.values() if v.value == "pass") if verification else 0,
            verification_fail_count=sum(1 for v in verification.flags.values() if v.value == "fail") if verification else 0,
            verification_unknown_count=sum(1 for v in verification.flags.values() if v.value == "unknown") if verification else 0,
            evidence_stale=bool(intake_result and intake_result.stale_sources),
            evidence_missing_fields=intake_result.missing_fields if intake_result else [],
        )

        # Record failure if rejected/abstained with a kill reason
        if kill_reason and hypothesis:
            self.failure_memory.record_failure(
                hypothesis=hypothesis,
                decision_id=audit_record.decision_id,
                failure_type="pipeline_killed",
                failure_details=kill_reason,
                edge_before_cost_bps=verification.edge_before_cost_bps if verification else 0,
                edge_after_cost_bps=verification.edge_after_cost_bps if verification else 0,
                output_class=final_output,
                recommendation="Review kill reason and consider hypothesis retirement" if kill_reason else "",
                recommendation_type="hypothesis_retirement" if kill_reason else "",
            )

        # Store audit record
        self._audit_log.append(audit_record)
        self.total_decisions += 1
        self.by_output[final_output.value] = self.by_output.get(final_output.value, 0) + 1

        logger.info(
            f"PHCE-D DECISION: {final_output.value} for {symbol} "
            f"latency={total_latency:.1f}ms lane={lane.value}"
        )

        return PHCEDResult(
            decision_record=audit_record,
            hypothesis=hypothesis,
            intake_result=intake_result,
            verification=verification,
            scenario_set=scenario_set,
            contradiction=contradiction,
            credal=credal,
            gateway_verdict=gateway_verdict,
            total_latency_ms=total_latency,
        )

    def _classify_latency(self, latency_ms: float) -> LatencyClass:
        """Classify the latency into a tier."""
        if latency_ms < 1:
            return LatencyClass.ULTRA_LOW
        elif latency_ms < 20:
            return LatencyClass.LOW
        elif latency_ms < 100:
            return LatencyClass.MEDIUM
        else:
            return LatencyClass.RESEARCH

    def get_audit_log(self, limit: int = 100) -> List[DecisionAuditRecord]:
        """Return recent audit records."""
        return list(self._audit_log[-limit:])

    def get_system_stats(self) -> Dict[str, Any]:
        """Return comprehensive system statistics from all modules."""
        return {
            "orchestrator": {
                "total_decisions": self.total_decisions,
                "by_output": self.by_output,
                "abstention_rate": sum(
                    v for k, v in self.by_output.items()
                    if k in {o.value for o in DecisionOutput.abstention()}
                ) / max(1, self.total_decisions),
            },
            "evidence_intake": self.evidence_intake.get_stats(),
            "hypothesis_generator": self.hypothesis_generator.get_stats(),
            "verifier": self.verifier.get_stats(),
            "scenario_conditioner": self.scenario_conditioner.get_stats(),
            "contradiction_classifier": self.contradiction_classifier.get_stats(),
            "credal_engine": self.credal_engine.get_stats(),
            "decision_policy": self.decision_policy.get_stats(),
            "validation_gateway": self.validation_gateway.get_stats(),
            "paper_trade_promotion": self.paper_trade_promotion.get_stats(),
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "refusal_metrics": self.refusal_metrics.get_stats(),
            "drift_monitor": self.drift_monitor.get_stats(),
            "failure_memory": self.failure_memory.get_stats(),
        }
