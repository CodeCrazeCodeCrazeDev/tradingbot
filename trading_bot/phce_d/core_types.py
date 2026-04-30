"""
PHCE-D Core Types — Parallel Hypothesis Correction Engine with Decision Policy

Canonical enums, data structures, and audit trail schema.
This is the single source of truth for all PHCE-D decision outputs,
hypothesis lifecycle states, contradiction taxonomies, and freshness criteria.

Hard rules enforced by types:
- No direct live execution path
- No contradiction as final output
- No LLM-only validation for high-trust claims
- UNKNOWN, HOLD, NO_TRADE are valid outputs
- Every trade-related output must pass Validation Gateway and paper trading
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── Canonical Decision Outputs ────────────────────────────────────────────────

class DecisionOutput(str, Enum):
    """
    The ONLY allowed final decision outputs from PHCE-D.

    No other string, prose, or 'contradiction' is acceptable.
    """
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    PAPER_TRADE_CANDIDATE = "PAPER_TRADE_CANDIDATE"
    REJECTED = "REJECTED"

    @classmethod
    def trade_positive(cls) -> set:
        """Outputs that imply capital deployment intent."""
        return {cls.BUY, cls.SELL, cls.PAPER_TRADE_CANDIDATE}

    @classmethod
    def abstention(cls) -> set:
        """Outputs that refuse action."""
        return {cls.HOLD, cls.NO_TRADE, cls.RESEARCH_ONLY,
                cls.NEEDS_MORE_EVIDENCE, cls.REJECTED}


class DecisionLane(str, Enum):
    """Two-lane architecture for latency separation."""
    RESEARCH = "research"    # Offline, batch, non-urgent
    DECISION = "decision"    # Bounded-latency, no parallel LLM


class LatencyClass(str, Enum):
    """Latency budget tiers — more time = better verification, NOT looser approval."""
    ULTRA_LOW = "ultra_low"   # <1 ms: deterministic only, high threshold
    LOW = "low"               # 1-20 ms: deterministic + cached stats
    MEDIUM = "medium"         # 20-100 ms: more checks, same quality bar
    RESEARCH = "research"     # >100 ms: no direct trade output


# ── Hypothesis Lifecycle ──────────────────────────────────────────────────────

class HypothesisStatus(str, Enum):
    """Hypothesis lifecycle states — most hypotheses should die."""
    ACTIVE = "ACTIVE"
    ACCUMULATING_EVIDENCE = "ACCUMULATING_EVIDENCE"
    PAPER_TRADE_CANDIDATE = "PAPER_TRADE_CANDIDATE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class LeakageRisk(str, Enum):
    """Leakage risk classification for hypothesis inputs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Contradiction Taxonomy ────────────────────────────────────────────────────

class ContradictionType(str, Enum):
    """Why evidence conflicts — determines routing to action."""
    MEASUREMENT_CONFLICT = "measurement_conflict"
    SCENARIO_CONFLICT = "scenario_conflict"
    MODEL_CONFLICT = "model_conflict"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_HYPOTHESIS = "invalid_hypothesis"


class ContradictionSeverity(str, Enum):
    """Severity of the contradiction."""
    LOW = "low"
    HIGH = "high"


# ── Evidence Freshness ────────────────────────────────────────────────────────

class EvidenceKind(str, Enum):
    """Categories of evidence with distinct freshness requirements."""
    PORTFOLIO_STATE = "portfolio_state"
    SPREAD_LIQUIDITY = "spread_liquidity"
    ONE_MINUTE_BARS = "1m_bars"
    REGIME_LABEL = "regime_label"
    COST_MODEL = "cost_model"
    VOLUME_DATA = "volume_data"
    EXTERNAL_RESEARCH = "external_research"


class EvidenceTrust(str, Enum):
    """Trust classification per evidence source."""
    HIGH = "high"           # Deterministically verified
    MEDIUM = "medium"       # Statistically estimated
    LOW = "low"             # Unverified, external, or LLM-generated
    UNTRUSTED = "untrusted"  # Provenance unknown or license unsupported


class FreshnessStatus(str, Enum):
    """Result of freshness check."""
    FRESH = "fresh"
    STALE = "stale"
    MISSING = "missing"


# ── Verification ──────────────────────────────────────────────────────────────

class VerificationFlag(str, Enum):
    """Per-component verification result."""
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class SkeletonKeyResult(str, Enum):
    """Result of dumb-explanation test."""
    FANCY_SURVIVES = "fancy_survives"       # Hypothesis beats dumb explanation
    DUMB_MATCHES = "dumb_matches"           # Dumb explanation as good → REJECTED
    DUMB_OUTPERFORMS = "dumb_outperforms"   # Dumb beats fancy → REJECTED


# ── Gateway ───────────────────────────────────────────────────────────────────

class GatewayResult(str, Enum):
    """Validation gateway pass/fail."""
    PASS = "PASS"
    FAIL = "FAIL"


class CircuitBreakerTrigger(str, Enum):
    """Circuit breaker trigger conditions."""
    STALE_EVIDENCE_ACROSS_SYMBOLS = "stale_evidence_across_symbols"
    DRAWDOWN_LIMIT_BREACH = "drawdown_limit_breach"
    REPEATED_PAPER_TRADE_FAILURES = "repeated_paper_trade_failures"
    DEPENDENCY_GRAPH_FAILURE = "dependency_graph_failure"
    UNEXPECTED_LIVE_EXECUTION_PATH = "unexpected_live_execution_path"
    VALIDATION_GATEWAY_BYPASS_ATTEMPT = "validation_gateway_bypass_attempt"


# ── Paper Trade ───────────────────────────────────────────────────────────────

class PaperTradeStage(str, Enum):
    """Paper-trade promotion stages."""
    ACCUMULATING_EVIDENCE = "accumulating_evidence"
    FAILED = "failed"
    PASSED_THRESHOLD = "passed_threshold"


# ── Drift Monitor ─────────────────────────────────────────────────────────────

class DriftAction(str, Enum):
    """Actions from drift/degradation monitor."""
    HOLD_PROMOTION = "HOLD_PROMOTION"
    DEMOTE_TO_RESEARCH = "DEMOTE_TO_RESEARCH"
    SUSPEND_HYPOTHESIS = "SUSPEND_HYPOTHESIS"


# ── Core Data Structures ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class FreshnessPolicy:
    """
    Maximum age and failure output per evidence kind.
    Stale data blocks the decision — it is not merely downweighted.
    """
    evidence_kind: EvidenceKind
    max_age_seconds: float
    failure_output: DecisionOutput

    @classmethod
    def default_policies(cls) -> list:
        """P0 #3: Evidence Freshness Kill Criteria defaults."""
        return [
            cls(EvidenceKind.PORTFOLIO_STATE, 1.0, DecisionOutput.NO_TRADE),
            cls(EvidenceKind.SPREAD_LIQUIDITY, 60.0, DecisionOutput.NO_TRADE),
            cls(EvidenceKind.ONE_MINUTE_BARS, 120.0, DecisionOutput.NO_TRADE),
            cls(EvidenceKind.REGIME_LABEL, 3600.0, DecisionOutput.NEEDS_MORE_EVIDENCE),
            cls(EvidenceKind.COST_MODEL, 300.0, DecisionOutput.NO_TRADE),
            cls(EvidenceKind.VOLUME_DATA, 120.0, DecisionOutput.NO_TRADE),
            cls(EvidenceKind.EXTERNAL_RESEARCH, 86400.0, DecisionOutput.RESEARCH_ONLY),
        ]


@dataclass
class EvidenceSource:
    """Single evidence source with trust and freshness metadata."""
    source_id: str
    evidence_kind: EvidenceKind
    timestamp: float  # Unix epoch
    trust: EvidenceTrust
    value: Any = None
    lineage_hash: str = ""
    missing_fields: List[str] = field(default_factory=list)

    def check_freshness(self, policy: FreshnessPolicy, now: float) -> FreshnessStatus:
        age = now - self.timestamp
        if age < 0:
            return FreshnessStatus.STALE  # Future timestamp = broken
        if age > policy.max_age_seconds:
            return FreshnessStatus.STALE
        return FreshnessStatus.FRESH


@dataclass(frozen=True)
class EvidencePacket:
    """
    Normalized evidence packet output from Evidence Intake.
    Contains all point-in-time evidence needed to test the current hypothesis.
    """
    packet_id: str
    symbol: str
    timestamp: float
    sources: Tuple[EvidenceSource, ...]
    lineage_hash: str
    completeness_report: Dict[str, bool]
    missing_fields: List[str]
    trust_labels: Dict[str, EvidenceTrust]
    lane: DecisionLane

    def any_stale_for_high_trust(self, policies: List[FreshnessPolicy],
                                  now: float) -> bool:
        """Check if any high-trust evidence source is stale."""
        policy_map = {p.evidence_kind: p for p in policies}
        for src in self.sources:
            if src.trust == EvidenceTrust.HIGH:
                pol = policy_map.get(src.evidence_kind)
                if pol and src.check_freshness(pol, now) == FreshnessStatus.STALE:
                    return True
        return False


@dataclass
class HypothesisLineage:
    """
    P0 #2: Hypothesis lineage and dependency graph.
    Proves what data, features, timestamps, and labels were used.
    Any unresolved leakage risk = REJECTED.
    """
    inputs: List[str]
    point_in_time_required: bool
    forbidden_inputs: List[str]
    leakage_risk: LeakageRisk
    feature_timestamps: Dict[str, float] = field(default_factory=dict)
    label_timestamps: Dict[str, float] = field(default_factory=dict)
    regime_label_source: str = ""

    def is_rejected_for_leakage(self) -> bool:
        return self.leakage_risk != LeakageRisk.LOW


@dataclass
class Hypothesis:
    """
    A falsifiable market claim with explicit assumptions, horizon, trigger,
    and expected edge source.
    """
    hypothesis_id: str
    name: str
    direction: str  # "long" or "short"
    horizon: str  # e.g. "intraday", "overnight", "weekly"
    expected_mechanism: str
    invalidation_conditions: List[str]
    min_edge_threshold_bps: float
    required_verifier_set: List[str]
    lineage: HypothesisLineage
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    created_at: float = 0.0
    retired_at: Optional[float] = None
    retirement_reason: str = ""
    template_name: str = ""  # Which template generated this

    def __post_init__(self):
        if not self.hypothesis_id:
            self.hypothesis_id = hashlib.sha256(
                f"{self.name}:{self.direction}:{self.horizon}".encode()
            ).hexdigest()[:16]
        if self.created_at == 0.0:
            self.created_at = datetime.now(timezone.utc).timestamp()

    def is_falsifiable(self) -> bool:
        return len(self.invalidation_conditions) > 0

    def is_testable(self, available_evidence_kinds: set) -> bool:
        required = {k for k in self.required_verifier_set}
        return required.issubset(available_evidence_kinds)


@dataclass
class VerificationReport:
    """Output from Deterministic/Statistical Verifier."""
    hypothesis_id: str
    flags: Dict[str, VerificationFlag]  # component → pass/fail/unknown
    effect_size_estimate: float
    edge_before_cost_bps: float
    edge_after_cost_bps: float
    uncertainty_notes: List[str]
    sample_size: int
    sign_consistent: bool
    cost_model_applied: bool
    skeleton_key_result: Optional[SkeletonKeyResult] = None

    def any_high_trust_unknown(self) -> bool:
        return any(v == VerificationFlag.UNKNOWN for v in self.flags.values())

    def any_fail(self) -> bool:
        return any(v == VerificationFlag.FAIL for v in self.flags.values())


@dataclass
class Scenario:
    """A single scenario with applicability conditions."""
    scenario_id: str
    name: str
    conditions: Dict[str, Any]
    directional_effect: str  # "bullish", "bearish", "neutral"
    support_weight: float  # 0-1, fraction of data in this scenario
    applicability_score: float = 0.0


@dataclass
class ScenarioSet:
    """Output from Scenario Conditioner."""
    scenarios: List[Scenario]
    partition_stable: bool
    partition_sanity_passed: bool
    min_support_met: bool
    discrimination_improvement: bool  # Scenarios improve over unconditional


@dataclass
class ContradictionClassification:
    """Output from Contradiction Classifier."""
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    resolution_path: DecisionOutput
    explanation: str
    can_resolve_to_scenario: bool


@dataclass
class CredalBounds:
    """
    MVP credal probability representation.
    Only useful if they change a decision boundary.
    """
    prob_lower: float
    prob_upper: float
    ambiguity_score: float  # 0-1, width of interval normalized
    actionable: bool  # Does this interval support a distinct policy action?
    confidence_class: str  # "high", "medium", "low", "uninformative"

    def __post_init__(self):
        if self.prob_lower < 0:
            self.prob_lower = 0.0
        if self.prob_upper > 1:
            self.prob_upper = 1.0
        if self.prob_lower > self.prob_upper:
            self.prob_lower, self.prob_upper = self.prob_upper, self.prob_lower


@dataclass
class DecisionRationale:
    """Structured rationale for the decision — no prose contradictions."""
    edge_before_cost_bps: float
    edge_after_cost_bps: float
    credal_lower: float
    credal_upper: float
    ambiguity_score: float
    scenario_matched: Optional[str]
    contradiction_type: Optional[str]
    verification_flags: Dict[str, str]
    kill_reason: Optional[str] = None  # If killed at any stage


# ── P0 #1: Decision Audit Trail Schema ────────────────────────────────────────

@dataclass
class DecisionAuditRecord:
    """
    The core artifact PHCE-D emits.
    Without this fixed schema, PHCE-D cannot be benchmarked, audited,
    replayed, debugged, or improved.
    """
    decision_id: str
    timestamp: str  # ISO-8601
    symbol: str
    hypothesis_id: str
    output_class: DecisionOutput
    edge_before_cost_bps: float
    edge_after_cost_bps: float
    credal_lower: float
    credal_upper: float
    ambiguity_score: float
    scenario_matched: Optional[str]
    contradiction_type: Optional[str]
    gateway_result: GatewayResult
    latency_ms: float
    cost_usd_cents: float
    lane: DecisionLane
    latency_class: LatencyClass
    rationale: Optional[DecisionRationale] = None
    # Hypothesis lineage summary
    hypothesis_leakage_risk: Optional[str] = None
    hypothesis_inputs: Optional[List[str]] = None
    # Verification summary
    verification_pass_count: int = 0
    verification_fail_count: int = 0
    verification_unknown_count: int = 0
    # Freshness
    evidence_stale: bool = False
    evidence_missing_fields: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.decision_id:
            self.decision_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> str:
        d = asdict(self)
        d["output_class"] = self.output_class.value
        d["gateway_result"] = self.gateway_result.value
        d["lane"] = self.lane.value
        d["latency_class"] = self.latency_class.value
        return json.dumps(d, default=str, sort_keys=True)

    def compute_hash(self) -> str:
        content = self.to_json().encode()
        return hashlib.sha256(content).hexdigest()[:16]


# ── Contradiction-to-Action Routing Table (P1 #11) ────────────────────────────

@dataclass(frozen=True)
class ContradictionRoutingRule:
    """Deterministic mapping from contradiction type/severity to output."""
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    output: DecisionOutput


DEFAULT_CONTRADICTION_ROUTING: List[ContradictionRoutingRule] = [
    ContradictionRoutingRule(ContradictionType.MEASUREMENT_CONFLICT, ContradictionSeverity.HIGH, DecisionOutput.REJECTED),
    ContradictionRoutingRule(ContradictionType.MEASUREMENT_CONFLICT, ContradictionSeverity.LOW, DecisionOutput.NO_TRADE),
    ContradictionRoutingRule(ContradictionType.SCENARIO_CONFLICT, ContradictionSeverity.LOW, DecisionOutput.PAPER_TRADE_CANDIDATE),
    ContradictionRoutingRule(ContradictionType.SCENARIO_CONFLICT, ContradictionSeverity.HIGH, DecisionOutput.NEEDS_MORE_EVIDENCE),
    ContradictionRoutingRule(ContradictionType.MODEL_CONFLICT, ContradictionSeverity.LOW, DecisionOutput.REJECTED),
    ContradictionRoutingRule(ContradictionType.MODEL_CONFLICT, ContradictionSeverity.HIGH, DecisionOutput.REJECTED),
    ContradictionRoutingRule(ContradictionType.INSUFFICIENT_EVIDENCE, ContradictionSeverity.LOW, DecisionOutput.NEEDS_MORE_EVIDENCE),
    ContradictionRoutingRule(ContradictionType.INSUFFICIENT_EVIDENCE, ContradictionSeverity.HIGH, DecisionOutput.NEEDS_MORE_EVIDENCE),
    ContradictionRoutingRule(ContradictionType.INVALID_HYPOTHESIS, ContradictionSeverity.LOW, DecisionOutput.REJECTED),
    ContradictionRoutingRule(ContradictionType.INVALID_HYPOTHESIS, ContradictionSeverity.HIGH, DecisionOutput.REJECTED),
]


# ── Latency-Dependent Decision Policy ─────────────────────────────────────────

@dataclass(frozen=True)
class LatencyPolicyRule:
    """
    More time = better verification, NOT looser approval.
    Thresholds never decrease with more time.
    """
    latency_class: LatencyClass
    budget_ms: float
    allow_llm: bool
    allow_statistical: bool
    threshold_multiplier: float  # >= 1.0 always; higher = more conservative


DEFAULT_LATENCY_POLICIES: List[LatencyPolicyRule] = [
    LatencyPolicyRule(LatencyClass.ULTRA_LOW, 1.0, False, False, 1.5),
    LatencyPolicyRule(LatencyClass.LOW, 20.0, False, True, 1.2),
    LatencyPolicyRule(LatencyClass.MEDIUM, 100.0, False, True, 1.0),
    LatencyPolicyRule(LatencyClass.RESEARCH, float("inf"), True, True, 1.0),
]


# ── Paper-Trade Promotion Thresholds ──────────────────────────────────────────

@dataclass
class PaperTradePromotionThresholds:
    """Configurable thresholds for paper-trade promotion."""
    min_trades: int = 50
    min_days: int = 20
    min_regimes: int = 2
    min_cost_adjusted_sharpe: float = 0.5
    max_drawdown_pct: float = 10.0
    benchmark_delta_required: bool = True


# ── Execution Realism ─────────────────────────────────────────────────────────

@dataclass
class ExecutionRealismConfig:
    """
    P0 #4: Paper trading must punish signals using realistic execution.
    If realistic execution removes the edge → REJECTED or NO_TRADE.
    """
    half_spread_penalty_bps: float = 1.0
    slippage_penalty_bps: float = 2.0
    partial_fill_rate: float = 0.95
    delay_jitter_ms: float = 50.0
    market_impact_coefficient_bps: float = 5.0
    liquidity_rejection_threshold: float = 0.1  # Participation rate above which to reject


# ── Hypothesis Retirement Triggers ────────────────────────────────────────────

@dataclass(frozen=True)
class RetirementTrigger:
    """Condition that causes a hypothesis to be retired."""
    trigger_name: str
    description: str
    check: str  # Function name or expression


DEFAULT_RETIREMENT_TRIGGERS: List[RetirementTrigger] = [
    RetirementTrigger("edge_below_cost_floor", "Edge after costs is negative or below minimum", "edge_after_cost_bps < min_edge_threshold_bps"),
    RetirementTrigger("verifier_unknown_too_often", "Verifier returns UNKNOWN more than threshold", "unknown_rate > max_unknown_rate"),
    RetirementTrigger("paper_trade_performance_fails", "Paper-trade Sharpe or hit-rate below thresholds", "paper_sharpe < min_sharpe"),
    RetirementTrigger("regime_no_longer_appears", "Regime label associated with hypothesis not seen recently", "regime_last_seen > regime_max_age"),
    RetirementTrigger("repeated_reparameterization", "Hypothesis re-parameterized N times without improvement", "reparam_count > max_reparam_without_improvement"),
]


# ── Refusal and Abstention Quality Metrics (P0 #8) ────────────────────────────

@dataclass
class RefusalMetrics:
    """
    Measure refusal quality — the system's main job is refusing bad trades.
    Without this, NO_TRADE can become lazy over-filtering.
    """
    refusal_precision: float = 0.0   # Rejected trades that would have lost
    refusal_recall: float = 0.0      # Losing trades correctly rejected
    false_abstention_rate: float = 0.0  # Rejected trades that would have won
    abstention_cost: float = 0.0     # Opportunity cost from missed winners
    needs_evidence_resolution_rate: float = 0.0  # How often uncertainty resolves cleanly
    total_refusals: int = 0
    total_approvals: int = 0


# ── Governance Layer (P0 #10) ─────────────────────────────────────────────────

@dataclass(frozen=True)
class GovernanceReviewRequirement:
    """Items that require mandatory human review."""
    first_capital_eligibility: bool = True
    validation_gateway_rule_changes: bool = True
    cost_model_changes: bool = True
    threshold_changes: bool = True
    circuit_breaker_reset: bool = True
    retired_hypothesis_resurrection: bool = True


# ── Exceptions ────────────────────────────────────────────────────────────────

class PHCEDError(Exception):
    """Base exception for PHCE-D."""
    pass


class EvidenceStaleError(PHCEDError):
    """Stale evidence for high-trust claim — decision must be killed."""
    pass


class LeakageDetectedError(PHCEDError):
    """Unresolved leakage risk in hypothesis lineage."""
    pass


class GatewayBypassError(PHCEDError):
    """Attempt to bypass the validation gateway."""
    pass


class CircuitBreakerTrippedError(PHCEDError):
    """Circuit breaker has been triggered — all trade-positive outputs paused."""
    pass


class ColdStartViolationError(PHCEDError):
    """Insufficient sample size for trade-positive output."""
    pass


class ContradictionAsOutputError(PHCEDError):
    """Someone tried to output 'contradiction' as a final decision."""
    pass
