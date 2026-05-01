"""PHCE-D: Parallel Hypothesis Correction Engine with Decision Policy.

This module implements the conservative MVP described in the PHCE-D spec:
one falsifiable hypothesis, deterministic verification, cost/slippage stress,
gateway validation, and paper-trade intent logging. It deliberately has no
live execution path.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol, Sequence


class PHCEDOutput(str, Enum):
    """Allowed PHCE-D decision outputs."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    PAPER_TRADE_CANDIDATE = "PAPER_TRADE_CANDIDATE"
    REJECTED = "REJECTED"


class PHCEDLane(str, Enum):
    """PHCE-D processing lane."""

    DECISION = "decision"
    RESEARCH = "research"


class HypothesisDirection(str, Enum):
    """Directional intent implied by a hypothesis."""

    LONG = "long"
    SHORT = "short"
    NONE = "none"


class VerificationStatus(str, Enum):
    """Verifier outcome."""

    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ContradictionType(str, Enum):
    """Reason evidence conflicts."""

    NONE = "none"
    MEASUREMENT_CONFLICT = "measurement_conflict"
    SCENARIO_CONFLICT = "scenario_conflict"
    MODEL_CONFLICT = "model_conflict"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_HYPOTHESIS = "invalid_hypothesis"


@dataclass(frozen=True)
class PHCEDConfig:
    """Operational thresholds for the PHCE-D MVP."""

    max_evidence_age_seconds: float = 300.0
    min_signal_strength: float = 0.35
    min_sample_size: int = 30
    min_edge_after_cost_bps: float = 1.0
    min_credal_lower_bound: float = 0.55
    max_ambiguity: float = 0.35
    max_spread_bps: float = 50.0
    max_volatility: float = 0.50
    min_liquidity_score: float = 0.20
    max_market_hostility_score: float = 0.70
    max_drawdown: float = 0.15
    default_paper_quantity: float = 1.0
    cost_stress_multipliers: Mapping[str, float] = field(
        default_factory=lambda: {"base": 1.0, "moderate": 1.5, "harsh": 2.25}
    )


@dataclass(frozen=True)
class EvidencePacket:
    """Point-in-time evidence consumed by PHCE-D."""

    symbol: str
    as_of: float
    market_timestamp: float
    price: float
    signal_strength: float
    expected_edge_bps: float
    spread_bps: float
    slippage_bps: float
    fee_bps: float
    market_impact_bps: float
    volatility: float = 0.0
    liquidity_score: float = 1.0
    sample_size: int = 0
    horizon_seconds: int = 300
    source_id: str = "unknown"
    trusted: bool = True
    lineage_hash: str = ""
    regime: str = "unknown"
    portfolio_state: Mapping[str, Any] = field(default_factory=dict)
    feature_timestamps: Mapping[str, float] = field(default_factory=dict)
    vendor_signals: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "EvidencePacket":
        """Build evidence from a dict-like object."""

        data = dict(payload)
        required = {
            "symbol",
            "as_of",
            "market_timestamp",
            "price",
            "signal_strength",
            "expected_edge_bps",
            "spread_bps",
            "slippage_bps",
            "fee_bps",
            "market_impact_bps",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"missing required evidence fields: {', '.join(missing)}")
        return cls(**data)


@dataclass(frozen=True)
class EvidenceReport:
    """Evidence validation output."""

    accepted: bool
    freshness_seconds: float
    lineage_hash: str
    missing_fields: List[str]
    warnings: List[str]
    kill_reasons: List[str]
    trust_labels: Dict[str, str]


@dataclass(frozen=True)
class Hypothesis:
    """Falsifiable market hypothesis."""

    hypothesis_id: str
    symbol: str
    direction: HypothesisDirection
    horizon_seconds: int
    expected_edge_bps: float
    minimum_edge_bps: float
    trigger: str
    mechanism: str
    invalidation_conditions: List[str]
    required_verifiers: List[str]


@dataclass(frozen=True)
class CostStressReport:
    """Cost ladder result."""

    base_cost_bps: float
    edge_after_cost_bps: Dict[str, float]
    break_even_rung: Optional[str]
    survives_moderate_stress: bool
    survives_harsh_stress: bool


@dataclass(frozen=True)
class VerificationReport:
    """Deterministic/statistical verification output."""

    status: VerificationStatus
    passed_checks: List[str]
    failed_checks: List[str]
    unknown_checks: List[str]
    effect_size_bps: float
    cost_adjusted_edge_bps: float
    cost_report: CostStressReport
    confidence: float


@dataclass(frozen=True)
class ScenarioCondition:
    """Scenario-conditioned interpretation of a hypothesis."""

    name: str
    applies: bool
    support_weight: float
    directional_effect: str
    notes: List[str]


@dataclass(frozen=True)
class ContradictionReport:
    """Contradiction classification result."""

    contradiction_type: ContradictionType
    severity: float
    resolution_path: PHCEDOutput
    reasons: List[str]


@dataclass(frozen=True)
class CredalProbabilityReport:
    """Bounded uncertainty output."""

    lower_probability: float
    upper_probability: float
    ambiguity: float
    confidence_class: str


@dataclass(frozen=True)
class GatewayResult:
    """Validation gateway result."""

    approved: bool
    reasons: List[str]
    warnings: List[str]
    residual_risk_score: float


@dataclass(frozen=True)
class PaperTradeIntent:
    """Paper-only order intent; this is not executable capital use."""

    intent_id: str
    symbol: str
    side: PHCEDOutput
    quantity: float
    reference_price: float
    created_at: float
    decision_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PHCEDDecisionRecord:
    """Complete PHCE-D decision record."""

    decision_id: str
    symbol: str
    lane: PHCEDLane
    policy_output: PHCEDOutput
    final_output: PHCEDOutput
    capital_allowed: bool
    evidence_report: EvidenceReport
    hypothesis: Optional[Hypothesis]
    verification: Optional[VerificationReport]
    scenarios: List[ScenarioCondition]
    contradiction: ContradictionReport
    credal_probabilities: Optional[CredalProbabilityReport]
    gateway_result: Optional[GatewayResult]
    paper_trade_intent: Optional[PaperTradeIntent]
    proof_trace: Dict[str, Any]
    reason_codes: List[str]
    rationale: str
    required_next_step: str
    created_at: float

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe dict representation."""

        return _to_jsonable(asdict(self))


class ValidationGateway(Protocol):
    """Gateway protocol for external risk validators."""

    def validate(self, decision: PHCEDOutput, evidence: EvidencePacket, hypothesis: Hypothesis) -> GatewayResult:
        """Validate a trade-related decision."""


class InMemoryPaperTradeLogger:
    """Small paper intent logger for MVP and tests."""

    def __init__(self) -> None:
        self.intents: List[PaperTradeIntent] = []

    def record(self, intent: PaperTradeIntent) -> None:
        self.intents.append(intent)


class SimpleValidationGateway:
    """Fail-closed deterministic gateway for the PHCE-D MVP."""

    def __init__(self, config: PHCEDConfig) -> None:
        self.config = config

    def validate(self, decision: PHCEDOutput, evidence: EvidencePacket, hypothesis: Hypothesis) -> GatewayResult:
        reasons: List[str] = []
        warnings: List[str] = []
        risk_score = 0.0
        portfolio = dict(evidence.portfolio_state or {})
        metadata = dict(evidence.metadata or {})

        if decision not in {PHCEDOutput.BUY, PHCEDOutput.SELL}:
            return GatewayResult(False, ["gateway only validates trade-related BUY/SELL policy outputs"], warnings, 100.0)

        hostility = float(metadata.get("market_hostility_score", 0.0))
        if hostility > self.config.max_market_hostility_score:
            reasons.append("market hostility score exceeds gateway threshold")
            risk_score += 35.0

        if bool(metadata.get("event_risk_embargo", False)):
            reasons.append("event-risk embargo is active")
            risk_score += 35.0

        if bool(metadata.get("catastrophic_risk", False)):
            reasons.append("catastrophic risk flag is active")
            risk_score += 50.0

        broker_health = str(metadata.get("broker_venue_health", "healthy")).lower()
        if broker_health not in {"healthy", "ok", "normal"}:
            reasons.append(f"broker/venue health is {broker_health}")
            risk_score += 25.0

        drawdown = abs(float(portfolio.get("drawdown", 0.0)))
        if drawdown > self.config.max_drawdown:
            reasons.append("portfolio drawdown exceeds gateway threshold")
            risk_score += 25.0

        if evidence.liquidity_score < self.config.min_liquidity_score:
            reasons.append("liquidity score is below gateway threshold")
            risk_score += 20.0

        if evidence.volatility > self.config.max_volatility:
            reasons.append("volatility exceeds gateway threshold")
            risk_score += 20.0

        if evidence.spread_bps > self.config.max_spread_bps:
            reasons.append("spread exceeds gateway threshold")
            risk_score += 20.0

        if portfolio.get("already_exposed_to_symbol"):
            warnings.append("portfolio already has exposure to this symbol")
            risk_score += 5.0

        return GatewayResult(
            approved=not reasons,
            reasons=reasons,
            warnings=warnings,
            residual_risk_score=min(risk_score, 100.0),
        )


class ParallelHypothesisCorrectionEngine:
    """PHCE-D MVP AI engine.

    The engine can recommend a policy direction and promote that direction to
    paper-trade candidacy. It intentionally never returns capital permission.
    """

    def __init__(
        self,
        config: Optional[PHCEDConfig] = None,
        gateway: Optional[ValidationGateway] = None,
        paper_logger: Optional[InMemoryPaperTradeLogger] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.config = config or PHCEDConfig()
        self.gateway = gateway or SimpleValidationGateway(self.config)
        self.paper_logger = paper_logger or InMemoryPaperTradeLogger()
        self.clock = clock or time.time
        self.decisions: List[PHCEDDecisionRecord] = []

    def evaluate(
        self,
        evidence: EvidencePacket | Mapping[str, Any],
        lane: PHCEDLane | str = PHCEDLane.DECISION,
    ) -> PHCEDDecisionRecord:
        """Evaluate one evidence packet through the PHCE-D MVP pipeline."""

        packet = self._coerce_evidence(evidence)
        lane_enum = PHCEDLane(lane)
        created_at = self.clock()
        evidence_report = self._intake_evidence(packet, created_at)
        decision_id = self._make_id("phced-decision", packet, created_at)

        if not evidence_report.accepted:
            output = self._evidence_failure_output(evidence_report)
            record = self._build_record(
                decision_id=decision_id,
                packet=packet,
                lane=lane_enum,
                policy_output=output,
                final_output=output,
                evidence_report=evidence_report,
                hypothesis=None,
                verification=None,
                scenarios=[],
                contradiction=ContradictionReport(
                    contradiction_type=ContradictionType.INVALID_HYPOTHESIS,
                    severity=1.0,
                    resolution_path=output,
                    reasons=evidence_report.kill_reasons,
                ),
                credal_probabilities=None,
                gateway_result=None,
                paper_trade_intent=None,
                reason_codes=["EVIDENCE_REJECTED"],
                rationale="Evidence intake failed: " + "; ".join(evidence_report.kill_reasons),
                required_next_step="Repair or replace the evidence packet before evaluating this hypothesis.",
                created_at=created_at,
            )
            return self._remember(record)

        hypothesis = self._generate_hypothesis(packet)
        if hypothesis.direction == HypothesisDirection.NONE:
            final_output = PHCEDOutput.HOLD if packet.portfolio_state.get("position_open") else PHCEDOutput.NO_TRADE
            record = self._build_record(
                decision_id=decision_id,
                packet=packet,
                lane=lane_enum,
                policy_output=final_output,
                final_output=final_output,
                evidence_report=evidence_report,
                hypothesis=hypothesis,
                verification=None,
                scenarios=[],
                contradiction=ContradictionReport(
                    contradiction_type=ContradictionType.NONE,
                    severity=0.0,
                    resolution_path=final_output,
                    reasons=["signal strength below hypothesis trigger threshold"],
                ),
                credal_probabilities=None,
                gateway_result=None,
                paper_trade_intent=None,
                reason_codes=["NO_ACTIONABLE_SIGNAL"],
                rationale="Signal did not clear the pre-registered trigger threshold.",
                required_next_step="Wait for stronger evidence or keep observing.",
                created_at=created_at,
            )
            return self._remember(record)

        verification = self._verify(packet, hypothesis)
        scenarios = self._condition_scenarios(packet, verification)
        contradiction = self._classify_contradiction(packet, hypothesis, verification, scenarios)
        credal = self._compute_credal_bounds(packet, verification, contradiction, scenarios)
        policy_output, reason_codes, rationale, required_next_step = self._apply_policy(
            packet=packet,
            hypothesis=hypothesis,
            verification=verification,
            contradiction=contradiction,
            credal=credal,
            lane=lane_enum,
        )

        gateway_result: Optional[GatewayResult] = None
        paper_trade_intent: Optional[PaperTradeIntent] = None
        final_output = policy_output

        if policy_output in {PHCEDOutput.BUY, PHCEDOutput.SELL}:
            gateway_result = self.gateway.validate(policy_output, packet, hypothesis)
            if gateway_result.approved:
                final_output = PHCEDOutput.PAPER_TRADE_CANDIDATE
                paper_trade_intent = self._paper_trade_intent(decision_id, packet, policy_output, created_at)
                self.paper_logger.record(paper_trade_intent)
                reason_codes.append("GATEWAY_APPROVED_PAPER_ONLY")
                required_next_step = "Run in paper trading or shadow mode; capital use remains blocked."
            else:
                final_output = PHCEDOutput.REJECTED
                reason_codes.append("VALIDATION_GATEWAY_REJECTED")
                rationale = "Validation gateway rejected the trade-related policy output."
                required_next_step = "Fix the blocking gateway condition or keep the hypothesis in research."

        record = self._build_record(
            decision_id=decision_id,
            packet=packet,
            lane=lane_enum,
            policy_output=policy_output,
            final_output=final_output,
            evidence_report=evidence_report,
            hypothesis=hypothesis,
            verification=verification,
            scenarios=scenarios,
            contradiction=contradiction,
            credal_probabilities=credal,
            gateway_result=gateway_result,
            paper_trade_intent=paper_trade_intent,
            reason_codes=reason_codes,
            rationale=rationale,
            required_next_step=required_next_step,
            created_at=created_at,
        )
        return self._remember(record)

    def _coerce_evidence(self, evidence: EvidencePacket | Mapping[str, Any]) -> EvidencePacket:
        if isinstance(evidence, EvidencePacket):
            return evidence
        return EvidencePacket.from_mapping(evidence)

    def _intake_evidence(self, packet: EvidencePacket, now: float) -> EvidenceReport:
        kill_reasons: List[str] = []
        warnings: List[str] = []
        missing_fields: List[str] = []

        freshness = max(0.0, now - packet.market_timestamp)
        if freshness > self.config.max_evidence_age_seconds:
            kill_reasons.append("market evidence is stale")

        if not packet.trusted:
            kill_reasons.append("evidence source is not trusted for high-trust claims")

        if packet.price <= 0:
            kill_reasons.append("price must be positive")

        for field_name in ("spread_bps", "slippage_bps", "fee_bps", "market_impact_bps"):
            value = float(getattr(packet, field_name))
            if value < 0:
                kill_reasons.append(f"{field_name} cannot be negative")

        for feature_name, timestamp in packet.feature_timestamps.items():
            if timestamp > packet.as_of:
                kill_reasons.append(f"feature {feature_name} has lookahead timestamp")

        if packet.lineage_hash:
            lineage_hash = packet.lineage_hash
        else:
            lineage_hash = _stable_hash(
                {
                    "symbol": packet.symbol,
                    "as_of": packet.as_of,
                    "source_id": packet.source_id,
                    "market_timestamp": packet.market_timestamp,
                }
            )
            warnings.append("lineage hash was generated from evidence metadata")

        return EvidenceReport(
            accepted=not kill_reasons,
            freshness_seconds=freshness,
            lineage_hash=lineage_hash,
            missing_fields=missing_fields,
            warnings=warnings,
            kill_reasons=kill_reasons,
            trust_labels={packet.source_id: "trusted" if packet.trusted else "untrusted"},
        )

    def _generate_hypothesis(self, packet: EvidencePacket) -> Hypothesis:
        strength = float(packet.signal_strength)
        if abs(strength) < self.config.min_signal_strength:
            direction = HypothesisDirection.NONE
            trigger = "signal strength below trigger"
        elif strength > 0:
            direction = HypothesisDirection.LONG
            trigger = f"signal_strength >= {self.config.min_signal_strength:.2f}"
        else:
            direction = HypothesisDirection.SHORT
            trigger = f"signal_strength <= -{self.config.min_signal_strength:.2f}"

        hypothesis_id = self._make_id("phced-hypothesis", packet, packet.as_of)
        return Hypothesis(
            hypothesis_id=hypothesis_id,
            symbol=packet.symbol.upper(),
            direction=direction,
            horizon_seconds=packet.horizon_seconds,
            expected_edge_bps=packet.expected_edge_bps,
            minimum_edge_bps=self.config.min_edge_after_cost_bps,
            trigger=trigger,
            mechanism="short-horizon directional edge after deterministic cost filtering",
            invalidation_conditions=[
                "cost-adjusted edge falls below threshold",
                "sample size is insufficient",
                "vendor evidence materially disagrees",
                "validation gateway rejects trade-related output",
            ],
            required_verifiers=["sample_size", "cost_adjusted_edge", "cost_stress_ladder", "gateway"],
        )

    def _verify(self, packet: EvidencePacket, hypothesis: Hypothesis) -> VerificationReport:
        passed: List[str] = []
        failed: List[str] = []
        unknown: List[str] = []

        if packet.sample_size >= self.config.min_sample_size:
            passed.append("sample_size")
        else:
            unknown.append("sample_size")

        if packet.spread_bps <= self.config.max_spread_bps:
            passed.append("spread_budget")
        else:
            failed.append("spread_budget")

        base_cost = self._base_cost_bps(packet)
        edge_after_cost: Dict[str, float] = {}
        break_even_rung: Optional[str] = None
        for rung, multiplier in self.config.cost_stress_multipliers.items():
            edge = packet.expected_edge_bps - base_cost * float(multiplier)
            edge_after_cost[rung] = edge
            if break_even_rung is None and edge <= 0:
                break_even_rung = rung

        moderate_edge = edge_after_cost.get("moderate", edge_after_cost.get("base", 0.0))
        harsh_edge = edge_after_cost.get("harsh", moderate_edge)
        cost_adjusted_edge = edge_after_cost.get("base", packet.expected_edge_bps - base_cost)

        if cost_adjusted_edge >= self.config.min_edge_after_cost_bps:
            passed.append("base_cost_adjusted_edge")
        else:
            failed.append("base_cost_adjusted_edge")

        if moderate_edge >= self.config.min_edge_after_cost_bps:
            passed.append("moderate_cost_stress")
        else:
            failed.append("moderate_cost_stress")

        if packet.liquidity_score >= self.config.min_liquidity_score:
            passed.append("liquidity")
        else:
            failed.append("liquidity")

        if packet.volatility <= self.config.max_volatility:
            passed.append("volatility")
        else:
            failed.append("volatility")

        status = VerificationStatus.PASSED
        if failed:
            status = VerificationStatus.FAILED
        elif unknown:
            status = VerificationStatus.UNKNOWN

        confidence = min(
            0.95,
            max(
                0.05,
                0.40
                + min(abs(packet.signal_strength), 1.0) * 0.25
                + min(max(cost_adjusted_edge, 0.0) / 100.0, 0.20)
                + min(packet.sample_size / max(self.config.min_sample_size * 4, 1), 0.10),
            ),
        )

        return VerificationReport(
            status=status,
            passed_checks=passed,
            failed_checks=failed,
            unknown_checks=unknown,
            effect_size_bps=packet.expected_edge_bps,
            cost_adjusted_edge_bps=cost_adjusted_edge,
            cost_report=CostStressReport(
                base_cost_bps=base_cost,
                edge_after_cost_bps=edge_after_cost,
                break_even_rung=break_even_rung,
                survives_moderate_stress=moderate_edge >= self.config.min_edge_after_cost_bps,
                survives_harsh_stress=harsh_edge >= self.config.min_edge_after_cost_bps,
            ),
            confidence=confidence,
        )

    def _condition_scenarios(
        self,
        packet: EvidencePacket,
        verification: VerificationReport,
    ) -> List[ScenarioCondition]:
        scenarios: List[ScenarioCondition] = []
        high_vol = packet.volatility > self.config.max_volatility * 0.7
        low_liquidity = packet.liquidity_score < max(self.config.min_liquidity_score * 1.75, 0.35)

        scenarios.append(
            ScenarioCondition(
                name="current_regime",
                applies=True,
                support_weight=min(1.0, packet.sample_size / max(self.config.min_sample_size, 1)),
                directional_effect="supports" if verification.cost_adjusted_edge_bps > 0 else "rejects",
                notes=[f"regime={packet.regime}"],
            )
        )
        if high_vol:
            scenarios.append(
                ScenarioCondition(
                    name="high_volatility",
                    applies=True,
                    support_weight=0.50,
                    directional_effect="weakens",
                    notes=["volatility can break normal cost and edge assumptions"],
                )
            )
        if low_liquidity:
            scenarios.append(
                ScenarioCondition(
                    name="thin_liquidity",
                    applies=True,
                    support_weight=0.40,
                    directional_effect="weakens",
                    notes=["liquidity is close to the minimum threshold"],
                )
            )
        return scenarios

    def _classify_contradiction(
        self,
        packet: EvidencePacket,
        hypothesis: Hypothesis,
        verification: VerificationReport,
        scenarios: Sequence[ScenarioCondition],
    ) -> ContradictionReport:
        reasons: List[str] = []
        severity = 0.0
        contradiction_type = ContradictionType.NONE
        resolution = PHCEDOutput.NO_TRADE

        vendor_values = [float(v) for v in packet.vendor_signals.values()]
        if len(vendor_values) >= 2:
            signs = {1 if value > 0 else -1 if value < 0 else 0 for value in vendor_values}
            if len(signs - {0}) > 1:
                contradiction_type = ContradictionType.MEASUREMENT_CONFLICT
                severity = max(severity, 0.75)
                reasons.append("data vendors disagree on signal direction")
            if max(vendor_values) - min(vendor_values) > max(abs(packet.signal_strength), 0.1):
                contradiction_type = ContradictionType.MEASUREMENT_CONFLICT
                severity = max(severity, 0.55)
                reasons.append("data vendor signal dispersion is high")

        if verification.status == VerificationStatus.UNKNOWN:
            contradiction_type = ContradictionType.INSUFFICIENT_EVIDENCE
            severity = max(severity, 0.45)
            reasons.append("verification has unknown checks")
            resolution = PHCEDOutput.NEEDS_MORE_EVIDENCE

        if verification.status == VerificationStatus.FAILED:
            contradiction_type = ContradictionType.MODEL_CONFLICT
            severity = max(severity, 0.85)
            reasons.append("deterministic verifier rejected the hypothesis")
            resolution = PHCEDOutput.NO_TRADE

        if hypothesis.direction == HypothesisDirection.NONE:
            contradiction_type = ContradictionType.INVALID_HYPOTHESIS
            severity = 1.0
            reasons.append("hypothesis has no actionable direction")
            resolution = PHCEDOutput.NO_TRADE

        if any(s.directional_effect == "weakens" for s in scenarios) and severity < 0.50:
            contradiction_type = ContradictionType.SCENARIO_CONFLICT
            severity = max(severity, 0.30)
            reasons.append("scenario conditions weaken the hypothesis")

        if not reasons:
            reasons.append("no material contradiction detected")

        return ContradictionReport(
            contradiction_type=contradiction_type,
            severity=min(severity, 1.0),
            resolution_path=resolution,
            reasons=reasons,
        )

    def _compute_credal_bounds(
        self,
        packet: EvidencePacket,
        verification: VerificationReport,
        contradiction: ContradictionReport,
        scenarios: Sequence[ScenarioCondition],
    ) -> CredalProbabilityReport:
        scenario_penalty = sum(0.05 for scenario in scenarios if scenario.directional_effect == "weakens")
        ambiguity = min(
            0.95,
            0.10
            + contradiction.severity * 0.35
            + (0.15 if verification.status == VerificationStatus.UNKNOWN else 0.0)
            + scenario_penalty,
        )
        edge_bonus = min(max(verification.cost_adjusted_edge_bps, 0.0) / 100.0, 0.15)
        signal_bonus = min(abs(packet.signal_strength), 1.0) * 0.25
        center = min(0.95, max(0.05, 0.50 + signal_bonus + edge_bonus - contradiction.severity * 0.15))
        lower = max(0.0, center - ambiguity / 2.0)
        upper = min(1.0, center + ambiguity / 2.0)
        if lower >= 0.65 and ambiguity <= 0.20:
            confidence_class = "high"
        elif lower >= self.config.min_credal_lower_bound and ambiguity <= self.config.max_ambiguity:
            confidence_class = "usable"
        elif ambiguity > self.config.max_ambiguity:
            confidence_class = "ambiguous"
        else:
            confidence_class = "weak"
        return CredalProbabilityReport(lower, upper, ambiguity, confidence_class)

    def _apply_policy(
        self,
        packet: EvidencePacket,
        hypothesis: Hypothesis,
        verification: VerificationReport,
        contradiction: ContradictionReport,
        credal: CredalProbabilityReport,
        lane: PHCEDLane,
    ) -> tuple[PHCEDOutput, List[str], str, str]:
        reason_codes: List[str] = []

        if lane == PHCEDLane.RESEARCH and verification.status != VerificationStatus.PASSED:
            return (
                PHCEDOutput.RESEARCH_ONLY,
                ["RESEARCH_LANE_NOT_TRADE_READY"],
                "Research lane produced an incomplete or unverified hypothesis.",
                "Keep this in research until deterministic verification passes.",
            )

        if verification.status == VerificationStatus.UNKNOWN:
            return (
                PHCEDOutput.NEEDS_MORE_EVIDENCE,
                ["INSUFFICIENT_SAMPLE_OR_UNKNOWN_CHECK"],
                "Verifier could not establish enough evidence for a trade-related output.",
                "Collect more point-in-time evidence before promotion.",
            )

        if verification.status == VerificationStatus.FAILED:
            return (
                PHCEDOutput.NO_TRADE,
                ["VERIFIER_FAILED", *[f"FAILED_{name.upper()}" for name in verification.failed_checks]],
                "Deterministic verifier rejected the hypothesis.",
                "Do not trade; inspect failed verifier checks.",
            )

        if contradiction.severity >= 0.70:
            return (
                contradiction.resolution_path,
                ["CONTRADICTION_TOO_SEVERE"],
                "Evidence conflict is too severe for an actionable output.",
                "Resolve measurement/model conflict or abstain.",
            )

        if credal.ambiguity > self.config.max_ambiguity:
            return (
                PHCEDOutput.NO_TRADE,
                ["CREDAL_AMBIGUITY_TOO_HIGH"],
                "Credal interval is too wide for action.",
                "Wait for clearer evidence or narrower scenario conditions.",
            )

        if credal.lower_probability < self.config.min_credal_lower_bound:
            return (
                PHCEDOutput.NO_TRADE,
                ["CREDAL_LOWER_BOUND_TOO_LOW"],
                "Lower probability bound does not support action.",
                "Keep observing or refine the hypothesis.",
            )

        if not verification.cost_report.survives_moderate_stress:
            return (
                PHCEDOutput.NO_TRADE,
                ["COST_STRESS_FAILED"],
                "Expected edge does not survive moderate cost stress.",
                "Do not promote until the edge survives realistic costs.",
            )

        if hypothesis.direction == HypothesisDirection.LONG:
            reason_codes.append("POLICY_BUY_PAPER_ONLY")
            return (
                PHCEDOutput.BUY,
                reason_codes,
                "Policy supports a long paper-trade candidate after cost and uncertainty checks.",
                "Pass Validation Gateway before paper-trade logging.",
            )

        if hypothesis.direction == HypothesisDirection.SHORT:
            reason_codes.append("POLICY_SELL_PAPER_ONLY")
            return (
                PHCEDOutput.SELL,
                reason_codes,
                "Policy supports a short paper-trade candidate after cost and uncertainty checks.",
                "Pass Validation Gateway before paper-trade logging.",
            )

        return (
            PHCEDOutput.NO_TRADE,
            ["NO_ACTIONABLE_DIRECTION"],
            "No actionable hypothesis direction was available.",
            "Wait for a valid hypothesis.",
        )

    def _paper_trade_intent(
        self,
        decision_id: str,
        packet: EvidencePacket,
        side: PHCEDOutput,
        created_at: float,
    ) -> PaperTradeIntent:
        return PaperTradeIntent(
            intent_id=self._make_id("phced-paper-intent", packet, created_at),
            symbol=packet.symbol.upper(),
            side=side,
            quantity=self.config.default_paper_quantity,
            reference_price=packet.price,
            created_at=created_at,
            decision_id=decision_id,
            metadata={
                "mode": "paper_only",
                "capital_allowed": False,
                "lineage_hash": packet.lineage_hash,
            },
        )

    def _base_cost_bps(self, packet: EvidencePacket) -> float:
        return (
            max(packet.spread_bps, 0.0) * 0.5
            + max(packet.slippage_bps, 0.0)
            + max(packet.fee_bps, 0.0)
            + max(packet.market_impact_bps, 0.0)
        )

    def _evidence_failure_output(self, evidence_report: EvidenceReport) -> PHCEDOutput:
        if any("stale" in reason for reason in evidence_report.kill_reasons):
            return PHCEDOutput.NEEDS_MORE_EVIDENCE
        return PHCEDOutput.REJECTED

    def _build_record(
        self,
        decision_id: str,
        packet: EvidencePacket,
        lane: PHCEDLane,
        policy_output: PHCEDOutput,
        final_output: PHCEDOutput,
        evidence_report: EvidenceReport,
        hypothesis: Optional[Hypothesis],
        verification: Optional[VerificationReport],
        scenarios: List[ScenarioCondition],
        contradiction: ContradictionReport,
        credal_probabilities: Optional[CredalProbabilityReport],
        gateway_result: Optional[GatewayResult],
        paper_trade_intent: Optional[PaperTradeIntent],
        reason_codes: List[str],
        rationale: str,
        required_next_step: str,
        created_at: float,
    ) -> PHCEDDecisionRecord:
        return PHCEDDecisionRecord(
            decision_id=decision_id,
            symbol=packet.symbol.upper(),
            lane=lane,
            policy_output=policy_output,
            final_output=final_output,
            capital_allowed=False,
            evidence_report=evidence_report,
            hypothesis=hypothesis,
            verification=verification,
            scenarios=scenarios,
            contradiction=contradiction,
            credal_probabilities=credal_probabilities,
            gateway_result=gateway_result,
            paper_trade_intent=paper_trade_intent,
            proof_trace=self._build_proof_trace(
                decision_id=decision_id,
                packet=packet,
                policy_output=policy_output,
                final_output=final_output,
                evidence_report=evidence_report,
                hypothesis=hypothesis,
                verification=verification,
                scenarios=scenarios,
                contradiction=contradiction,
                credal_probabilities=credal_probabilities,
                gateway_result=gateway_result,
                paper_trade_intent=paper_trade_intent,
                reason_codes=reason_codes,
                rationale=rationale,
                created_at=created_at,
            ),
            reason_codes=reason_codes,
            rationale=rationale,
            required_next_step=required_next_step,
            created_at=created_at,
        )

    def _remember(self, record: PHCEDDecisionRecord) -> PHCEDDecisionRecord:
        self.decisions.append(record)
        return record

    def _build_proof_trace(
        self,
        decision_id: str,
        packet: EvidencePacket,
        policy_output: PHCEDOutput,
        final_output: PHCEDOutput,
        evidence_report: EvidenceReport,
        hypothesis: Optional[Hypothesis],
        verification: Optional[VerificationReport],
        scenarios: List[ScenarioCondition],
        contradiction: ContradictionReport,
        credal_probabilities: Optional[CredalProbabilityReport],
        gateway_result: Optional[GatewayResult],
        paper_trade_intent: Optional[PaperTradeIntent],
        reason_codes: List[str],
        rationale: str,
        created_at: float,
    ) -> Dict[str, Any]:
        """Build the claim -> evidence -> proof -> action trace for PHCE-D."""

        trace_id = f"proof-{decision_id}"
        action_candidate = {
            "decision_id": decision_id,
            "symbol": packet.symbol.upper(),
            "policy_output": policy_output.value,
            "final_output": final_output.value,
            "capital_allowed": False,
        }

        evidence_id = evidence_report.lineage_hash or self._make_id("phced-evidence", packet, created_at)
        claims: List[Dict[str, Any]] = []
        assumptions: List[Dict[str, Any]] = []

        if hypothesis is not None:
            thesis = {
                "claim_id": f"{decision_id}:thesis",
                "kind": "thesis",
                "statement": (
                    f"{hypothesis.direction.value} hypothesis for {hypothesis.symbol} over "
                    f"{hypothesis.horizon_seconds}s expects {hypothesis.expected_edge_bps:.4f} bps gross edge"
                ),
                "confidence": verification.confidence if verification else 0.0,
                "critical": True,
                "evidence_refs": [evidence_id],
                "invalidation_conditions": list(hypothesis.invalidation_conditions),
            }
            claims.append(thesis)
            assumption = {
                "claim_id": f"{decision_id}:cost-assumption",
                "kind": "assumption",
                "statement": "cost, slippage, spread, and market impact estimates are representative for paper-only evaluation",
                "confidence": 0.5,
                "critical": True,
                "evidence_refs": [evidence_id],
            }
            assumptions.append(assumption)
            claims.append(assumption)

        verifier_results: List[Dict[str, Any]] = []
        if verification is not None:
            verifier_results.append(
                {
                    "check_id": f"{decision_id}:deterministic-verifier",
                    "check_type": "deterministic_statistical_verifier",
                    "passed": verification.status == VerificationStatus.PASSED,
                    "severity": 0.0 if verification.status == VerificationStatus.PASSED else 0.8,
                    "passed_checks": list(verification.passed_checks),
                    "failed_checks": list(verification.failed_checks),
                    "unknown_checks": list(verification.unknown_checks),
                    "cost_adjusted_edge_bps": verification.cost_adjusted_edge_bps,
                    "cost_stress": _to_jsonable(verification.cost_report),
                }
            )

        if gateway_result is not None:
            verifier_results.append(
                {
                    "check_id": f"{decision_id}:validation-gateway",
                    "check_type": "validation_gateway",
                    "passed": gateway_result.approved,
                    "severity": gateway_result.residual_risk_score / 100.0,
                    "reasons": list(gateway_result.reasons),
                    "warnings": list(gateway_result.warnings),
                }
            )

        adversarial_challenges = []
        if contradiction.contradiction_type != ContradictionType.NONE:
            adversarial_challenges.append(
                {
                    "check_id": f"{decision_id}:contradiction",
                    "check_type": contradiction.contradiction_type.value,
                    "passed": contradiction.severity < 0.70,
                    "severity": contradiction.severity,
                    "details": list(contradiction.reasons),
                }
            )

        missing_evidence = list(evidence_report.missing_fields)
        missing_evidence.extend(evidence_report.kill_reasons)
        contradictions = [] if contradiction.contradiction_type == ContradictionType.NONE else list(contradiction.reasons)

        proof_status = "sufficient"
        if final_output in {PHCEDOutput.REJECTED, PHCEDOutput.NO_TRADE, PHCEDOutput.NEEDS_MORE_EVIDENCE, PHCEDOutput.RESEARCH_ONLY}:
            proof_status = "insufficient"
        if contradictions and contradiction.severity >= 0.70:
            proof_status = "contradicted"
        if verification is None:
            proof_status = "unverified"

        graph_sufficient = final_output == PHCEDOutput.PAPER_TRADE_CANDIDATE and proof_status == "sufficient"
        trace = {
            "trace_id": trace_id,
            "action_candidate": action_candidate,
            "claims": claims,
            "assumptions": assumptions,
            "evidence_refs": [evidence_id],
            "missing_evidence": missing_evidence,
            "contradictions": contradictions,
            "adversarial_challenges": adversarial_challenges,
            "verifier_results": verifier_results,
            "uncertainty_profile": _to_jsonable(credal_probabilities) if credal_probabilities else {},
            "refusal_or_approval_reason": rationale,
            "final_decision": final_output.value,
            "downstream_action": "paper_trade_log" if paper_trade_intent else "refuse_or_observe",
            "outcome_ref": paper_trade_intent.intent_id if paper_trade_intent else None,
            "proof_status": proof_status,
            "graph_sufficient": graph_sufficient,
            "reason_codes": list(reason_codes),
            "scenario_conditions": [_to_jsonable(scenario) for scenario in scenarios],
            "created_at": created_at,
        }
        trace["trace_hash"] = _stable_hash(trace)
        return trace

    def _make_id(self, prefix: str, packet: EvidencePacket, timestamp: float) -> str:
        digest = _stable_hash(
            {
                "prefix": prefix,
                "symbol": packet.symbol.upper(),
                "as_of": packet.as_of,
                "timestamp": timestamp,
                "signal_strength": packet.signal_strength,
                "expected_edge_bps": packet.expected_edge_bps,
            }
        )[:16]
        return f"{prefix}-{digest}"


PHCEDAI = ParallelHypothesisCorrectionEngine


def create_phce_d_ai(config: Optional[PHCEDConfig] = None) -> ParallelHypothesisCorrectionEngine:
    """Factory used by callers that want a PHCE-D AI component."""

    return ParallelHypothesisCorrectionEngine(config=config)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(_to_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(inner) for inner in value]
    return value
