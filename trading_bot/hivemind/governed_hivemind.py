"""
Governed Hivemind Capability Registry and Anti-Groupthink Gates.

This module keeps the hivemind honest. It treats swarm ideas as research
capabilities until they prove decision quality after costs, leakage controls,
paper trading, and proof governance.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


class HivemindCapabilityStatus(Enum):
    """Lifecycle status for hivemind capability ideas."""

    PRODUCTION_GUARDED = "production_guarded"
    SHADOW_ONLY = "shadow_only"
    RESEARCH_ONLY = "research_only"
    EXTERNAL_INPUT_ONLY = "external_input_only"
    REJECTED = "rejected"
    PROHIBITED = "prohibited"


class HivemindCapabilityFamily(Enum):
    """The governed capability families requested for AlphaAlgo hivemind."""

    FEDERATED_LEARNING = "federated_learning"
    EVOLUTIONARY_NICHES = "evolutionary_niches"
    ANT_COLONY_EXECUTION = "ant_colony_execution"
    IMMUNE_RISK_MANAGER = "immune_risk_manager"
    INTERNAL_PREDICTION_MARKET = "internal_prediction_market"
    SWARM_REINFORCEMENT_LEARNING = "swarm_reinforcement_learning"
    MICROSTRUCTURE_MIMICRY = "microstructure_mimicry"
    MYCELIAL_NETWORK = "mycelial_network"
    FRACTAL_TIMEFRAME_CONSENSUS = "fractal_timeframe_consensus"
    HISTORICAL_NEAREST_NEIGHBORS = "historical_nearest_neighbors"
    MANIPULATION_ANOMALY_HIVEMIND = "manipulation_anomaly_hivemind"
    CROSS_ASSET_NETWORK = "cross_asset_network"
    QUANTUM_INSPIRED_SUPERPOSITION = "quantum_inspired_superposition"
    ORACLE_HIVEMIND = "oracle_hivemind"
    ZK_STRATEGY_BLENDING = "zk_strategy_blending"
    EMBEDDING_ALIGNMENT = "embedding_alignment"
    AUTOPOIETIC_BOT = "autopoietic_bot"
    ADVERSARIAL_REGIME_GAN = "adversarial_regime_gan"
    CROWDSOURCED_GENETIC_PROGRAMMING = "crowdsourced_genetic_programming"
    WHISPER_GOSSIP_NETWORK = "whisper_gossip_network"


class HivemindGateDecision(Enum):
    """Governance decision for a hivemind subsystem or vote."""

    APPROVE = "approve"
    SHADOW_ONLY = "shadow_only"
    QUARANTINE = "quarantine"
    HOLD = "hold"
    REJECT = "reject"
    RESEARCH_ONLY = "research_only"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


@dataclass(frozen=True)
class HivemindCapabilitySpec:
    """A governed capability pattern, not a marketing claim."""

    capability_id: str
    name: str
    family: HivemindCapabilityFamily
    status: HivemindCapabilityStatus
    purpose: str
    implementation_home: str
    allowed_lane: str
    inputs: List[str]
    outputs: List[str]
    validation_requirements: List[str]
    kill_criteria: List[str]
    anti_patterns: List[str]
    capital_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "family": self.family.value,
            "status": self.status.value,
            "purpose": self.purpose,
            "implementation_home": self.implementation_home,
            "allowed_lane": self.allowed_lane,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "validation_requirements": list(self.validation_requirements),
            "kill_criteria": list(self.kill_criteria),
            "anti_patterns": list(self.anti_patterns),
            "capital_eligible": self.capital_eligible,
        }


@dataclass
class HivemindGovernanceConfig:
    """Thresholds for preventing fake democracy and performance chasing."""

    min_agents: int = 3
    min_unique_signal_families: int = 3
    min_unique_modalities: int = 2
    max_pairwise_correlation: float = 0.85
    max_feature_overlap: float = 0.65
    max_drawdown_comovement: float = 0.75
    max_exposure_overlap: float = 0.70
    min_regime_coverage: int = 2
    min_causal_independence: float = 0.30
    strict_missing_measurements: bool = False

    min_paper_trades: int = 30
    min_shadow_days: int = 10
    min_oos_windows: int = 3
    min_cost_adjusted_edge: float = 0.0
    min_sharpe_delta: float = 0.10
    max_calibration_error: float = 0.15
    max_recent_turnover: float = 0.35


@dataclass
class AgentSignalProfile:
    """Measurable independence profile for one hivemind agent."""

    agent_id: str
    signal_family: str
    feature_set: Set[str] = field(default_factory=set)
    data_modalities: Set[str] = field(default_factory=set)
    regime_performance: Dict[str, float] = field(default_factory=dict)
    drawdown_signature: List[float] = field(default_factory=list)
    exposure_vector: Dict[str, float] = field(default_factory=dict)
    signal_history: List[float] = field(default_factory=list)
    failure_tags: Set[str] = field(default_factory=set)
    current_weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_vote(cls, vote: Any) -> "AgentSignalProfile":
        """Build a profile from an existing NodeVote-like object."""

        metadata = dict(getattr(vote, "metadata", {}) or {})
        node_type = getattr(vote, "node_type", "unknown")
        if hasattr(node_type, "value"):
            signal_family = str(node_type.value)
        else:
            signal_family = str(node_type)

        direction = getattr(vote, "direction", None)
        if hasattr(direction, "to_numeric"):
            current_signal = float(direction.to_numeric())
        else:
            current_signal = float(metadata.get("signal", 0.0) or 0.0)

        feature_set = set(metadata.get("feature_set", metadata.get("features", [])) or [])
        if not feature_set:
            feature_set = {signal_family}

        data_modalities = set(metadata.get("data_modalities", metadata.get("modalities", [])) or [])
        if not data_modalities:
            data_modalities = {_default_modality(signal_family)}

        history = [float(x) for x in metadata.get("signal_history", []) if _is_number(x)]
        if not history:
            history = [current_signal]

        return cls(
            agent_id=str(getattr(vote, "node_id", f"vote_{uuid.uuid4().hex[:8]}")),
            signal_family=signal_family,
            feature_set=feature_set,
            data_modalities=data_modalities,
            regime_performance={
                str(k): float(v)
                for k, v in dict(metadata.get("regime_performance", {}) or {}).items()
                if _is_number(v)
            },
            drawdown_signature=[
                float(x) for x in metadata.get("drawdown_signature", []) if _is_number(x)
            ],
            exposure_vector={
                str(k): float(v)
                for k, v in dict(metadata.get("exposure_vector", {}) or {}).items()
                if _is_number(v)
            },
            signal_history=history,
            failure_tags=set(metadata.get("failure_tags", []) or []),
            current_weight=float(getattr(vote, "weight", 1.0) or 1.0),
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "signal_family": self.signal_family,
            "feature_set": sorted(self.feature_set),
            "data_modalities": sorted(self.data_modalities),
            "regime_performance": dict(self.regime_performance),
            "drawdown_signature": list(self.drawdown_signature),
            "exposure_vector": dict(self.exposure_vector),
            "signal_history": list(self.signal_history),
            "failure_tags": sorted(self.failure_tags),
            "current_weight": self.current_weight,
            "metadata": dict(self.metadata),
        }


@dataclass
class SignalDiversityAudit:
    """Audit report for whether many agents are actually independent."""

    audit_id: str
    agent_count: int
    unique_signal_families: int
    unique_modalities: int
    max_pairwise_correlation: Optional[float]
    avg_pairwise_correlation: Optional[float]
    feature_overlap_score: float
    max_drawdown_comovement: Optional[float]
    max_exposure_overlap: Optional[float]
    failure_cluster_count: int
    regime_coverage: int
    causal_independence_score: float
    missing_measurements: List[str] = field(default_factory=list)
    passed: bool = False
    rejection_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "agent_count": self.agent_count,
            "unique_signal_families": self.unique_signal_families,
            "unique_modalities": self.unique_modalities,
            "max_pairwise_correlation": self.max_pairwise_correlation,
            "avg_pairwise_correlation": self.avg_pairwise_correlation,
            "feature_overlap_score": self.feature_overlap_score,
            "max_drawdown_comovement": self.max_drawdown_comovement,
            "max_exposure_overlap": self.max_exposure_overlap,
            "failure_cluster_count": self.failure_cluster_count,
            "regime_coverage": self.regime_coverage,
            "causal_independence_score": self.causal_independence_score,
            "missing_measurements": list(self.missing_measurements),
            "passed": self.passed,
            "rejection_reasons": list(self.rejection_reasons),
            "warnings": list(self.warnings),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HivemindVoteGuardReport:
    """Decision guard result for a proposed swarm vote."""

    proposed_action: str
    final_action: str
    decision: HivemindGateDecision
    diversity_audit: SignalDiversityAudit
    reasons: List[str] = field(default_factory=list)
    required_next_steps: List[str] = field(default_factory=list)
    proof_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposed_action": self.proposed_action,
            "final_action": self.final_action,
            "decision": self.decision.value,
            "diversity_audit": self.diversity_audit.to_dict(),
            "reasons": list(self.reasons),
            "required_next_steps": list(self.required_next_steps),
            "proof_required": self.proof_required,
        }


@dataclass
class AgentEvolutionGateReport:
    """Promotion/demotion report that avoids naive culling."""

    agent_id: str
    decision: HivemindGateDecision
    promotion_allowed: bool
    quarantine_required: bool
    reasons: List[str] = field(default_factory=list)
    required_next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "decision": self.decision.value,
            "promotion_allowed": self.promotion_allowed,
            "quarantine_required": self.quarantine_required,
            "reasons": list(self.reasons),
            "required_next_steps": list(self.required_next_steps),
        }


@dataclass
class HivemindValidationReport:
    """Generic report for ensembles, sentiment, and capability reviews."""

    subject: str
    decision: HivemindGateDecision
    passed: bool
    reasons: List[str] = field(default_factory=list)
    missing_controls: List[str] = field(default_factory=list)
    required_next_steps: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    direct_trade_allowed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "decision": self.decision.value,
            "passed": self.passed,
            "reasons": list(self.reasons),
            "missing_controls": list(self.missing_controls),
            "required_next_steps": list(self.required_next_steps),
            "metrics": dict(self.metrics),
            "direct_trade_allowed": self.direct_trade_allowed,
        }


class GovernedHivemindEngine:
    """
    Registry and guardrail engine for advanced hivemind ideas.

    It does not execute trades. It says whether a swarm idea is:
    - allowed only as research
    - allowed in shadow mode
    - allowed as a risk blocker
    - rejected or prohibited
    """

    def __init__(self, config: Optional[HivemindGovernanceConfig] = None):
        self.config = config or HivemindGovernanceConfig()
        self.capabilities = self._build_default_capabilities()

    def list_capabilities(
        self,
        status: Optional[HivemindCapabilityStatus] = None,
    ) -> List[HivemindCapabilitySpec]:
        specs = list(self.capabilities.values())
        if status is not None:
            specs = [spec for spec in specs if spec.status == status]
        return specs

    def get_capability(self, capability_id: str) -> HivemindCapabilitySpec:
        return self.capabilities[capability_id]

    def profiles_from_votes(self, votes: Iterable[Any]) -> List[AgentSignalProfile]:
        return [AgentSignalProfile.from_vote(vote) for vote in votes]

    def audit_signal_diversity(
        self,
        profiles: Sequence[AgentSignalProfile],
    ) -> SignalDiversityAudit:
        """Measure whether the hive is truly diverse or just duplicated price transforms."""

        profiles = list(profiles)
        reasons: List[str] = []
        warnings: List[str] = []
        missing: List[str] = []

        families = {profile.signal_family for profile in profiles}
        modalities: Set[str] = set()
        regimes: Set[str] = set()
        for profile in profiles:
            modalities.update(profile.data_modalities)
            regimes.update(profile.regime_performance.keys())

        signal_corrs = _pairwise_correlations([p.signal_history for p in profiles])
        drawdown_corrs = _pairwise_correlations([p.drawdown_signature for p in profiles])
        exposure_overlaps = _pairwise_exposure_overlaps([p.exposure_vector for p in profiles])
        feature_overlaps = _pairwise_jaccards([p.feature_set for p in profiles])

        if not signal_corrs:
            missing.append("signal correlation matrix")
        if not drawdown_corrs:
            missing.append("drawdown co-movement")
        if not exposure_overlaps:
            missing.append("exposure overlap")
        if not regimes:
            missing.append("regime-specific performance")
        if not feature_overlaps:
            missing.append("feature overlap score")

        max_corr, avg_corr = _max_avg_abs(signal_corrs)
        max_drawdown, _ = _max_avg_abs(drawdown_corrs)
        max_exposure, _ = _max_avg_abs(exposure_overlaps)
        feature_overlap = max(feature_overlaps) if feature_overlaps else 0.0
        failure_cluster_count = self._count_failure_clusters(profiles)

        independence_inputs = [
            value
            for value in [
                max_corr,
                feature_overlap,
                max_drawdown,
                max_exposure,
            ]
            if value is not None
        ]
        causal_independence = 1.0 - max(independence_inputs) if independence_inputs else 0.0
        causal_independence = max(0.0, min(1.0, causal_independence))

        if len(profiles) < self.config.min_agents:
            reasons.append("not enough agents for a meaningful hive")
        if len(families) < self.config.min_unique_signal_families:
            reasons.append("too few independent signal families")
        if len(modalities) < self.config.min_unique_modalities:
            reasons.append("too few independent data modalities")
        if max_corr is not None and max_corr > self.config.max_pairwise_correlation:
            reasons.append("signal correlation is too high")
        if feature_overlap > self.config.max_feature_overlap:
            reasons.append("feature overlap is too high")
        if max_drawdown is not None and max_drawdown > self.config.max_drawdown_comovement:
            reasons.append("drawdown co-movement is too high")
        if max_exposure is not None and max_exposure > self.config.max_exposure_overlap:
            reasons.append("exposure overlap is too high")
        if len(regimes) < self.config.min_regime_coverage:
            reasons.append("regime coverage is too narrow")
        if causal_independence < self.config.min_causal_independence:
            reasons.append("causal independence score is too low")

        if missing:
            warnings.append(
                "missing anti-groupthink measurements: " + ", ".join(sorted(missing))
            )
            if self.config.strict_missing_measurements:
                reasons.append("missing required diversity measurements")

        audit = SignalDiversityAudit(
            audit_id=f"hive_diversity_{uuid.uuid4().hex[:10]}",
            agent_count=len(profiles),
            unique_signal_families=len(families),
            unique_modalities=len(modalities),
            max_pairwise_correlation=max_corr,
            avg_pairwise_correlation=avg_corr,
            feature_overlap_score=feature_overlap,
            max_drawdown_comovement=max_drawdown,
            max_exposure_overlap=max_exposure,
            failure_cluster_count=failure_cluster_count,
            regime_coverage=len(regimes),
            causal_independence_score=causal_independence,
            missing_measurements=missing,
            passed=not reasons,
            rejection_reasons=reasons,
            warnings=warnings,
        )
        return audit

    def guard_collective_vote(
        self,
        profiles: Sequence[AgentSignalProfile],
        proposed_action: str,
        proof_trace_id: Optional[str] = None,
    ) -> HivemindVoteGuardReport:
        """Block trade-like hive votes when diversity/proof is insufficient."""

        audit = self.audit_signal_diversity(profiles)
        action = str(proposed_action or "HOLD").upper()
        trade_like = action in {"BUY", "SELL", "PAPER_TRADE_CANDIDATE"}
        reasons = list(audit.rejection_reasons)
        next_steps: List[str] = []

        if trade_like and not proof_trace_id:
            reasons.append("trade-like hive output has no proof trace")
            next_steps.append("route the candidate through DGS/PHCE-D proof tracing")

        if trade_like and not audit.passed:
            next_steps.extend(
                [
                    "measure signal correlation matrix",
                    "measure feature overlap and causal independence",
                    "replay failure clustering and regime-specific performance",
                ]
            )
            return HivemindVoteGuardReport(
                proposed_action=action,
                final_action="HOLD",
                decision=HivemindGateDecision.HOLD,
                diversity_audit=audit,
                reasons=reasons,
                required_next_steps=_unique(next_steps),
            )

        if trade_like and not proof_trace_id:
            return HivemindVoteGuardReport(
                proposed_action=action,
                final_action="HOLD",
                decision=HivemindGateDecision.HOLD,
                diversity_audit=audit,
                reasons=reasons,
                required_next_steps=_unique(next_steps),
            )

        return HivemindVoteGuardReport(
            proposed_action=action,
            final_action=action,
            decision=HivemindGateDecision.APPROVE if trade_like else HivemindGateDecision.SHADOW_ONLY,
            diversity_audit=audit,
            reasons=reasons,
            required_next_steps=_unique(next_steps),
        )

    def evaluate_agent_evolution(
        self,
        agent_id: str,
        metrics: Dict[str, Any],
    ) -> AgentEvolutionGateReport:
        """
        Gate agent mutation/promotion/demotion without naive recent-performance culling.
        """

        recent_sharpe = float(metrics.get("recent_sharpe", 0.0) or 0.0)
        long_run_sharpe = float(metrics.get("long_run_sharpe", 0.0) or 0.0)
        paper_trades = int(metrics.get("paper_trades", 0) or 0)
        oos_windows = int(metrics.get("oos_windows", 0) or 0)
        recent_turnover = float(metrics.get("recent_turnover", 0.0) or 0.0)
        regime_expected = bool(metrics.get("regime_expected", True))
        validation_passed = bool(metrics.get("validation_passed", False))
        cost_adjusted_edge = float(metrics.get("cost_adjusted_edge", 0.0) or 0.0)

        reasons: List[str] = []
        next_steps: List[str] = []

        if not validation_passed:
            reasons.append("validation gate has not passed")
            next_steps.append("run purged walk-forward validation and paper replay")
        if paper_trades < self.config.min_paper_trades:
            reasons.append("paper-trade sample is too small")
            next_steps.append("continue shadow mode until minimum paper trade count is met")
        if oos_windows < self.config.min_oos_windows:
            reasons.append("out-of-sample regime windows are insufficient")
        if recent_turnover > self.config.max_recent_turnover:
            reasons.append("recent allocation turnover is too high")
            next_steps.append("freeze weight changes and check performance chasing")
        if cost_adjusted_edge <= self.config.min_cost_adjusted_edge:
            reasons.append("cost-adjusted edge is not positive")

        if recent_sharpe < 0.0 and long_run_sharpe > 0.5 and not regime_expected:
            reasons.append("recent weakness may be regime mismatch, not strategy death")
            next_steps.append("quarantine instead of culling until the matching regime returns")
            return AgentEvolutionGateReport(
                agent_id=agent_id,
                decision=HivemindGateDecision.QUARANTINE,
                promotion_allowed=False,
                quarantine_required=True,
                reasons=_unique(reasons),
                required_next_steps=_unique(next_steps),
            )

        if reasons:
            return AgentEvolutionGateReport(
                agent_id=agent_id,
                decision=HivemindGateDecision.QUARANTINE,
                promotion_allowed=False,
                quarantine_required=True,
                reasons=_unique(reasons),
                required_next_steps=_unique(next_steps),
            )

        return AgentEvolutionGateReport(
            agent_id=agent_id,
            decision=HivemindGateDecision.APPROVE,
            promotion_allowed=True,
            quarantine_required=False,
            reasons=["promotion allowed only through formal governance, not live auto-culling"],
            required_next_steps=["attach proof trace and paper-trade report to promotion request"],
        )

    def validate_ml_ensemble(self, evidence: Dict[str, Any]) -> HivemindValidationReport:
        """Reject underspecified LSTM/XGBoost/sentiment stacking theater."""

        required_controls = {
            "purged_walk_forward_validation": "purged walk-forward validation",
            "embargoed_cross_validation": "embargoed cross-validation",
            "transaction_cost_model": "transaction cost model",
            "slippage_model": "slippage model",
            "feature_leakage_detection": "feature leakage detection",
            "uncertainty_calibration": "uncertainty calibration",
            "regime_conditional_evaluation": "regime-conditional evaluation",
            "live_shadow_trading": "live shadow trading",
            "model_decay_monitoring": "model decay monitoring",
        }
        missing = [
            label for key, label in required_controls.items() if not bool(evidence.get(key, False))
        ]
        reasons: List[str] = []

        if bool(evidence.get("direct_live_execution", False)):
            reasons.append("ensemble requested direct live execution")
        if missing:
            reasons.append("ensemble is missing required validation controls")

        calibration_error = evidence.get("calibration_error")
        if _is_number(calibration_error) and float(calibration_error) > self.config.max_calibration_error:
            reasons.append("calibration error is too high")

        sharpe_delta = float(evidence.get("paper_sharpe_delta", 0.0) or 0.0)
        if sharpe_delta < self.config.min_sharpe_delta:
            reasons.append("paper-trade Sharpe delta is too weak")

        cost_adjusted_edge = float(evidence.get("cost_adjusted_edge", 0.0) or 0.0)
        if cost_adjusted_edge <= self.config.min_cost_adjusted_edge:
            reasons.append("cost-adjusted edge is not positive")

        passed = not reasons and not missing
        return HivemindValidationReport(
            subject="ml_ensemble_hivemind",
            decision=HivemindGateDecision.SHADOW_ONLY if passed else HivemindGateDecision.REJECT,
            passed=passed,
            reasons=_unique(reasons),
            missing_controls=missing,
            required_next_steps=[] if passed else ["keep ensemble in research until all controls pass"],
            metrics={
                "calibration_error": calibration_error,
                "paper_sharpe_delta": sharpe_delta,
                "cost_adjusted_edge": cost_adjusted_edge,
            },
            direct_trade_allowed=False,
        )

    def govern_social_sentiment(self, evidence: Dict[str, Any]) -> HivemindValidationReport:
        """Allow social sentiment only as capped input, never as an execution brain."""

        reasons: List[str] = []
        next_steps: List[str] = []
        bot_score = float(evidence.get("bot_manipulation_score", 0.0) or 0.0)
        credibility = float(evidence.get("source_credibility", 0.0) or 0.0)
        position_size_pct = float(evidence.get("position_size_pct", 0.0) or 0.0)

        if bool(evidence.get("direct_execution_requested", False)):
            reasons.append("social sentiment cannot directly control execution")
        if not bool(evidence.get("sentiment_velocity", False)):
            reasons.append("raw sentiment is not enough; sentiment velocity is required")
        if credibility < 0.5:
            reasons.append("source credibility is too low")
        if bot_score > 0.35:
            reasons.append("bot/manipulation risk is too high")
            next_steps.append("route to manipulation detector or NO_TRADE")
        if not bool(evidence.get("price_volume_confirmation", False)):
            reasons.append("price/volume confirmation is missing")
        if not bool(evidence.get("event_classified", False)):
            reasons.append("event classification is missing")
        if position_size_pct > 0.02:
            reasons.append("sentiment-driven position cap exceeded")

        passed = not reasons
        return HivemindValidationReport(
            subject="social_sentiment_hivemind",
            decision=HivemindGateDecision.SHADOW_ONLY if passed else HivemindGateDecision.REJECT,
            passed=passed,
            reasons=_unique(reasons),
            missing_controls=[],
            required_next_steps=_unique(next_steps),
            metrics={
                "bot_manipulation_score": bot_score,
                "source_credibility": credibility,
                "position_size_pct": position_size_pct,
            },
            direct_trade_allowed=False,
        )

    def reject_dao_trade_control(self) -> HivemindValidationReport:
        """DAO voting can guide roadmap/risk appetite, not live trades."""

        return HivemindValidationReport(
            subject="dao_style_trade_control",
            decision=HivemindGateDecision.REJECT,
            passed=False,
            reasons=[
                "DAO voting is too slow, noisy, manipulable, and legally messy for live trade control",
            ],
            required_next_steps=[
                "limit humans or community votes to research priorities, roadmap, and risk appetite bands",
            ],
            direct_trade_allowed=False,
        )

    def review_capability(
        self,
        capability_id: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> HivemindValidationReport:
        """Review one advanced hivemind idea against its status and safety rules."""

        evidence = evidence or {}
        spec = self.get_capability(capability_id)
        reasons: List[str] = []
        missing: List[str] = []
        hard_reject = False

        if spec.status in {HivemindCapabilityStatus.REJECTED, HivemindCapabilityStatus.PROHIBITED}:
            reasons.append(f"{spec.name} is {spec.status.value}")
            hard_reject = True
        if bool(evidence.get("direct_live_execution", False)):
            reasons.append("direct live execution is prohibited")
            hard_reject = True
        if bool(evidence.get("bypass_validation_gateway", False)):
            reasons.append("validation gateway bypass requested")
            hard_reject = True
        if bool(evidence.get("front_run_manipulation", False)):
            reasons.append("front-running manipulation is rejected; only avoid/risk-off is allowed")
            hard_reject = True
        if capability_id == "federated_learning" and bool(evidence.get("raw_data_shared", False)):
            reasons.append("federated learning cannot share raw data")
            hard_reject = True
        if capability_id == "self_replicating_autopoietic_bot":
            reasons.append("self-replicating code is not allowed outside sandboxed governance research")
            hard_reject = True

        required_flags = [
            "proof_trace_id",
            "validation_gateway_passed",
            "paper_trading_passed",
            "cost_model_passed",
            "leakage_check_passed",
        ]
        for flag in required_flags:
            if not evidence.get(flag):
                missing.append(flag)

        if missing and spec.status in {
            HivemindCapabilityStatus.PRODUCTION_GUARDED,
            HivemindCapabilityStatus.SHADOW_ONLY,
        }:
            reasons.append("required proof/validation evidence is missing")

        passed = not reasons
        if not passed:
            if hard_reject:
                decision = HivemindGateDecision.REJECT
            elif missing:
                decision = HivemindGateDecision.NEEDS_MORE_EVIDENCE
            else:
                decision = HivemindGateDecision.RESEARCH_ONLY
        elif spec.status == HivemindCapabilityStatus.RESEARCH_ONLY:
            decision = HivemindGateDecision.RESEARCH_ONLY
        elif spec.status == HivemindCapabilityStatus.EXTERNAL_INPUT_ONLY:
            decision = HivemindGateDecision.SHADOW_ONLY
        else:
            decision = (
                HivemindGateDecision.SHADOW_ONLY
                if not spec.capital_eligible
                else HivemindGateDecision.APPROVE
            )

        return HivemindValidationReport(
            subject=capability_id,
            decision=decision,
            passed=passed,
            reasons=_unique(reasons),
            missing_controls=missing,
            required_next_steps=[] if passed else list(spec.validation_requirements),
            metrics={"status": spec.status.value, "capital_eligible": spec.capital_eligible},
            direct_trade_allowed=False,
        )

    def _count_failure_clusters(self, profiles: Sequence[AgentSignalProfile]) -> int:
        counts: Dict[str, int] = {}
        for profile in profiles:
            for tag in profile.failure_tags:
                counts[tag] = counts.get(tag, 0) + 1
        return sum(1 for count in counts.values() if count >= 2)

    def _build_default_capabilities(self) -> Dict[str, HivemindCapabilitySpec]:
        common_validation = [
            "proof trace",
            "no direct live execution",
            "validation gateway",
            "cost/slippage model",
            "paper or shadow replay",
            "bypass path scanner",
        ]

        specs = [
            HivemindCapabilitySpec(
                "federated_learning",
                "Federated Learning Hivemind",
                HivemindCapabilityFamily.FEDERATED_LEARNING,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Blend encrypted local model updates without sharing raw market/user data.",
                "trading_bot/hivemind/governed_hivemind.py plus distributed training services",
                "offline research",
                ["encrypted weight updates", "client validation metadata", "poisoning scores"],
                ["candidate global model", "privacy audit report"],
                common_validation + ["secure aggregation", "poisoned update detection"],
                ["raw data sharing", "unverified client updates", "negative paper delta"],
                ["calling privacy a feature without cryptographic/update audit"],
            ),
            HivemindCapabilitySpec(
                "evolutionary_niches",
                "Evolutionary Ecosystem with Niches",
                HivemindCapabilityFamily.EVOLUTIONARY_NICHES,
                HivemindCapabilityStatus.SHADOW_ONLY,
                "Track regime-specialized bots and rebalance only through promotion gates.",
                "trading_bot/hivemind/governed_hivemind.py",
                "shadow allocation research",
                ["niche bot metrics", "regime labels", "paper outcomes"],
                ["quarantine/promote/demote recommendation"],
                common_validation + ["regime-conditioned scoring", "quarantine before demotion"],
                ["recent-performance culling", "parameter mining", "unstable allocation turnover"],
                ["survival-of-the-fittest without regime memory"],
            ),
            HivemindCapabilitySpec(
                "ant_colony_execution",
                "Ant Colony Optimization for Trade Execution",
                HivemindCapabilityFamily.ANT_COLONY_EXECUTION,
                HivemindCapabilityStatus.SHADOW_ONLY,
                "Explore venue/order-route options with decaying heuristic scores.",
                "trading_bot/hivemind/governed_hivemind.py and execution router",
                "execution research",
                ["order book map", "fees", "liquidity", "fill history"],
                ["route score", "execution route candidate"],
                common_validation + ["venue health gate", "fill realism audit"],
                ["stale order book", "route bypasses broker/risk gate", "negative cost-adjusted fill"],
                ["digital pheromones presented as alpha"],
            ),
            HivemindCapabilitySpec(
                "immune_risk_manager",
                "Artificial Immune System Risk Manager",
                HivemindCapabilityFamily.IMMUNE_RISK_MANAGER,
                HivemindCapabilityStatus.PRODUCTION_GUARDED,
                "Detect anomalies and allow only risk-reducing responses such as hedge, flat, or NO_TRADE.",
                "trading_bot/hivemind/governed_hivemind.py and risk gates",
                "risk blocking",
                ["anomaly signatures", "market stress", "portfolio state"],
                ["risk alert", "hedge/flat recommendation", "immunological memory"],
                common_validation + ["false-positive/false-negative replay"],
                ["risk signal opens new risk", "catastrophic flag ignored"],
                ["white blood cell metaphor replacing measured anomaly detection"],
                capital_eligible=True,
            ),
            HivemindCapabilitySpec(
                "internal_prediction_market",
                "Internal Prediction Market",
                HivemindCapabilityFamily.INTERNAL_PREDICTION_MARKET,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Use virtual budgets to score sub-agent forecasts without direct trade authority.",
                "trading_bot/hivemind/governed_hivemind.py",
                "forecast research",
                ["agent forecasts", "virtual currency balances", "settled outcomes"],
                ["consensus probability", "agent calibration scores"],
                common_validation + ["proper scoring rule", "calibration registry"],
                ["wealth concentration from lucky agents", "unverified consensus used as trade approval"],
                ["market metaphor without settlement discipline"],
            ),
            HivemindCapabilitySpec(
                "swarm_reinforcement_learning",
                "Swarm Reinforcement Learning",
                HivemindCapabilityFamily.SWARM_REINFORCEMENT_LEARNING,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Test multi-agent RL only in offline and paper environments.",
                "trading_bot/hivemind/governed_hivemind.py and offline RL lab",
                "offline research",
                ["simulated environment", "reward model", "policy snapshots"],
                ["candidate policy", "risk-adjusted learning report"],
                common_validation + ["off-policy evaluation", "reward hacking audit"],
                ["live RL exploration", "reward ignores costs", "unstable policy turnover"],
                ["calling emergent cooperation alpha before paper evidence"],
            ),
            HivemindCapabilitySpec(
                "microstructure_mimicry",
                "Simulated Market Microstructure Mimicry",
                HivemindCapabilityFamily.MICROSTRUCTURE_MIMICRY,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Simulate counterparties to stress-test order-flow hypotheses.",
                "trading_bot/hivemind/governed_hivemind.py and simulation/",
                "research simulation",
                ["order book data", "counterparty templates", "fill assumptions"],
                ["microstructure stress signal", "scenario report"],
                common_validation + ["sim-to-real gap estimate"],
                ["fake counterparties fit history but fail live shadow", "fill model too idealized"],
                ["simulation treated as truth"],
            ),
            HivemindCapabilitySpec(
                "mycelial_network",
                "Mycelial Network Intelligence",
                HivemindCapabilityFamily.MYCELIAL_NETWORK,
                HivemindCapabilityStatus.PRODUCTION_GUARDED,
                "Propagate cross-asset risk context laterally without granting direct trade authority.",
                "trading_bot/hivemind/governed_hivemind.py and cross-asset risk graph",
                "risk/context propagation",
                ["cross-asset links", "volatility shocks", "correlation graph"],
                ["position-size adjustment candidate", "risk propagation trace"],
                common_validation + ["correlation stability map"],
                ["unverified contagion link", "position sizing increases portfolio risk"],
                ["distributed metaphor hiding central risk errors"],
                capital_eligible=True,
            ),
            HivemindCapabilitySpec(
                "fractal_timeframe_consensus",
                "Fractal Timeframe Consensus",
                HivemindCapabilityFamily.FRACTAL_TIMEFRAME_CONSENSUS,
                HivemindCapabilityStatus.SHADOW_ONLY,
                "Require multi-timeframe confirmation while measuring overlap and latency penalty.",
                "trading_bot/hivemind/governed_hivemind.py",
                "decision support",
                ["timeframe-specific votes", "feature overlap", "latency budget"],
                ["timeframe consensus report"],
                common_validation + ["timeframe overlap audit"],
                ["same feature resampled into fake diversity", "latency exceeds decision budget"],
                ["many timeframes voting on the same price transform"],
            ),
            HivemindCapabilitySpec(
                "historical_nearest_neighbors",
                "Historical-Hivemind via Massive Nearest-Neighbors",
                HivemindCapabilityFamily.HISTORICAL_NEAREST_NEIGHBORS,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Use historical ghosts as scenario evidence only after leakage and lockbox controls.",
                "trading_bot/hivemind/governed_hivemind.py and backtesting/",
                "historical research",
                ["point-in-time features", "nearest-neighbor index", "lockbox split"],
                ["weighted historical forecast", "neighbor provenance"],
                common_validation + ["temporal leakage quarantine", "backtest lockbox"],
                ["lookahead features", "nearest-neighbor overfit", "no paper confirmation"],
                ["past-market hive used as live oracle"],
            ),
            HivemindCapabilitySpec(
                "manipulation_anomaly_hivemind",
                "Anomaly-Focused Hivemind for Manipulation Detection",
                HivemindCapabilityFamily.MANIPULATION_ANOMALY_HIVEMIND,
                HivemindCapabilityStatus.PRODUCTION_GUARDED,
                "Detect possible manipulation and route to avoid, hedge, reduce, or NO_TRADE.",
                "trading_bot/hivemind/governed_hivemind.py and surveillance/",
                "risk blocking",
                ["order book imbalance", "sentiment velocity", "options flow", "wallet flow"],
                ["manipulation alert", "avoid/risk-off recommendation"],
                common_validation + ["false-positive replay", "market abuse policy check"],
                ["front-running manipulation", "unverified social pump signal"],
                ["turning manipulation detection into manipulation participation"],
                capital_eligible=True,
            ),
            HivemindCapabilitySpec(
                "cross_asset_network",
                "Cross-Asset Sentient Network",
                HivemindCapabilityFamily.CROSS_ASSET_NETWORK,
                HivemindCapabilityStatus.PRODUCTION_GUARDED,
                "Let asset specialists broadcast macro/risk context into portfolio sizing gates.",
                "trading_bot/hivemind/governed_hivemind.py and portfolio risk graph",
                "portfolio context",
                ["asset-agent readings", "macro features", "portfolio exposures"],
                ["cross-asset risk context", "size adjustment candidate"],
                common_validation + ["exposure overlap audit"],
                ["macro reading overrides local proof", "correlation link is stale"],
                ["sentient language without measurable cross-asset causality"],
                capital_eligible=True,
            ),
            HivemindCapabilitySpec(
                "quantum_inspired_superposition",
                "Quantum-Inspired Superposition",
                HivemindCapabilityFamily.QUANTUM_INSPIRED_SUPERPOSITION,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "A metaphor for probability aggregation; no quantum advantage claim allowed.",
                "trading_bot/hivemind/governed_hivemind.py",
                "research reporting",
                ["module probability contributions", "calibration history"],
                ["bounded probability vector", "collapse threshold report"],
                common_validation + ["calibration test"],
                ["fake quantum claims", "probabilities not calibrated"],
                ["science-flavored naming used as evidence"],
            ),
            HivemindCapabilitySpec(
                "oracle_hivemind",
                "Oracle Hivemind",
                HivemindCapabilityFamily.ORACLE_HIVEMIND,
                HivemindCapabilityStatus.EXTERNAL_INPUT_ONLY,
                "Use decentralized oracle data as an evidence input, not as a trading brain.",
                "trading_bot/hivemind/governed_hivemind.py and data_feeds/",
                "evidence intake",
                ["oracle data feeds", "node agreement metadata"],
                ["validated data point", "source trust label"],
                common_validation + ["oracle freshness and disagreement checks"],
                ["oracle delay", "oracle consensus treated as alpha"],
                ["outsourcing truth without checking latency and relevance"],
            ),
            HivemindCapabilitySpec(
                "zk_strategy_blending",
                "Zero-Knowledge Proof Strategy Blending",
                HivemindCapabilityFamily.ZK_STRATEGY_BLENDING,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Accept private strategy claims only as statistical/proof inputs, never hidden live authority.",
                "trading_bot/hivemind/governed_hivemind.py and research ingestion",
                "research intake",
                ["ZK/statistical proof", "validity metadata", "paper results"],
                ["trust-weighted external signal candidate"],
                common_validation + ["proof verifier", "sample validity audit"],
                ["proof says profitable but sample is biased", "unknown strategy controls capital"],
                ["trustless alpha claims without benchmark detail"],
            ),
            HivemindCapabilitySpec(
                "embedding_alignment",
                "Neural Embedding Alignment Hivemind",
                HivemindCapabilityFamily.EMBEDDING_ALIGNMENT,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Align multimodal networks into a shared state embedding for research signals.",
                "trading_bot/hivemind/governed_hivemind.py and multimodal/",
                "research signal",
                ["price embeddings", "news embeddings", "on-chain embeddings"],
                ["market-state embedding", "alignment score"],
                common_validation + ["modality ablation", "calibration and drift tests"],
                ["embedding drift", "modality collapse", "uninterpretable high-confidence claim"],
                ["alignment score treated as edge"],
            ),
            HivemindCapabilitySpec(
                "self_replicating_autopoietic_bot",
                "Self-Replicating Autopoietic Bot",
                HivemindCapabilityFamily.AUTOPOIETIC_BOT,
                HivemindCapabilityStatus.PROHIBITED,
                "Self-replicating code is prohibited outside sandboxed governance research.",
                "do not deploy",
                "prohibited",
                ["none for production"],
                ["rejection report"],
                ["autonomy-control approval", "sandbox only"],
                ["self-replication", "mutation of production code", "unreviewed child bots"],
                ["identity metaphors hiding uncontrolled code propagation"],
            ),
            HivemindCapabilitySpec(
                "adversarial_regime_gan",
                "Adversarial Hivemind for Regime Detection",
                HivemindCapabilityFamily.ADVERSARIAL_REGIME_GAN,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Use synthetic/real discrimination as anomaly evidence only.",
                "trading_bot/hivemind/governed_hivemind.py and simulation/",
                "research anomaly signal",
                ["real feed", "synthetic generator", "discriminator scores"],
                ["regime-break suspicion score"],
                common_validation + ["synthetic data audit", "false alarm replay"],
                ["GAN artifact interpreted as trade edge", "no live shadow confirmation"],
                ["dreamed market data treated as market data"],
            ),
            HivemindCapabilitySpec(
                "crowdsourced_genetic_programming",
                "Crowd-Sourced Genetic Programming Hivemind",
                HivemindCapabilityFamily.CROWDSOURCED_GENETIC_PROGRAMMING,
                HivemindCapabilityStatus.RESEARCH_ONLY,
                "Sandbox human-submitted rules and promote only via lockbox/paper governance.",
                "trading_bot/hivemind/governed_hivemind.py and strategy_discovery/",
                "research strategy discovery",
                ["DSL snippets", "sandbox results", "lineage"],
                ["candidate strategy", "rejection or quarantine report"],
                common_validation + ["sandboxing", "IP/license check", "genetic overfit control"],
                ["unsafe snippet", "parameter mining", "community manipulation"],
                ["human-machine hive treated as validation"],
            ),
            HivemindCapabilitySpec(
                "whisper_gossip_network",
                "Whisper Network P2P Gossip Protocol",
                HivemindCapabilityFamily.WHISPER_GOSSIP_NETWORK,
                HivemindCapabilityStatus.EXTERNAL_INPUT_ONLY,
                "Treat encrypted peer signals as low-trust evidence with source trust decay.",
                "trading_bot/hivemind/governed_hivemind.py and connectors/",
                "evidence input",
                ["encrypted peer whisper", "trust score", "freshness metadata"],
                ["low-trust context signal", "source reliability update"],
                common_validation + ["sybil resistance", "trust decay", "no direct trade control"],
                ["gossip controls trade", "trusted peer sends stale/manipulative signal"],
                ["sixth-sense framing without source accountability"],
            ),
        ]
        return {spec.capability_id: spec for spec in specs}


def create_governed_hivemind(
    config: Optional[HivemindGovernanceConfig] = None,
) -> GovernedHivemindEngine:
    return GovernedHivemindEngine(config)


def _default_modality(signal_family: str) -> str:
    family = signal_family.lower()
    if family in {"technical", "pattern", "momentum", "mean_reversion", "volatility"}:
        return "price_volume"
    if family in {"sentiment", "social", "news"}:
        return "sentiment"
    if family in {"macro", "fundamental", "correlation"}:
        return "macro"
    if family in {"execution", "microstructure", "order_flow"}:
        return "order_flow"
    if family in {"risk"}:
        return "portfolio_risk"
    return "unknown"


def _pairwise_correlations(series_list: Sequence[Sequence[float]]) -> List[float]:
    correlations: List[float] = []
    for left_index in range(len(series_list)):
        for right_index in range(left_index + 1, len(series_list)):
            corr = _pearson(series_list[left_index], series_list[right_index])
            if corr is not None:
                correlations.append(corr)
    return correlations


def _pairwise_jaccards(sets: Sequence[Set[str]]) -> List[float]:
    scores: List[float] = []
    for left_index in range(len(sets)):
        for right_index in range(left_index + 1, len(sets)):
            left = sets[left_index]
            right = sets[right_index]
            if left or right:
                scores.append(len(left & right) / max(1, len(left | right)))
    return scores


def _pairwise_exposure_overlaps(vectors: Sequence[Dict[str, float]]) -> List[float]:
    scores: List[float] = []
    for left_index in range(len(vectors)):
        for right_index in range(left_index + 1, len(vectors)):
            score = _cosine(vectors[left_index], vectors[right_index])
            if score is not None:
                scores.append(abs(score))
    return scores


def _pearson(left: Sequence[float], right: Sequence[float]) -> Optional[float]:
    size = min(len(left), len(right))
    if size < 3:
        return None
    xs = [float(value) for value in left[-size:]]
    ys = [float(value) for value in right[-size:]]
    mean_x = sum(xs) / size
    mean_y = sum(ys) / size
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def _cosine(left: Dict[str, float], right: Dict[str, float]) -> Optional[float]:
    keys = set(left) | set(right)
    if not keys:
        return None
    numerator = sum(float(left.get(key, 0.0)) * float(right.get(key, 0.0)) for key in keys)
    left_norm = math.sqrt(sum(float(left.get(key, 0.0)) ** 2 for key in keys))
    right_norm = math.sqrt(sum(float(right.get(key, 0.0)) ** 2 for key in keys))
    if left_norm == 0 or right_norm == 0:
        return None
    return numerator / (left_norm * right_norm)


def _max_avg_abs(values: Sequence[float]) -> Tuple[Optional[float], Optional[float]]:
    if not values:
        return None, None
    absolute_values = [abs(float(value)) for value in values]
    return max(absolute_values), sum(absolute_values) / len(absolute_values)


def _is_number(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return not math.isnan(numeric) and not math.isinf(numeric)


def _unique(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result
