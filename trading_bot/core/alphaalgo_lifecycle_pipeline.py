"""AlphaAlgo Lifecycle Pipeline — nine-stage autonomous research-to-deployment loop.

Stage flow:
    1. Observe frontier systems
    2. Benchmark capability
    3. Extract useful pattern
    4. Convert into AlphaAlgo module
    5. Test in sandbox
    6. Run counterintelligence attacks
    7. Deploy only if metrics improve
    8. Monitor live performance
    9. Kill or revise if it decays

Every stage is a hard gate: failure at any stage halts progression for that
artifact and records the rejection reason in the lineage store.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .frontier_capability_distillation import (
    AEANGlobalObjective,
    AlphaAlgoNativeArtifact,
    AlphaAlgoArtifactKind,
    BenchmarkHarness,
    BenchmarkResult,
    BenchmarkTask,
    CapabilityExtractor,
    CapabilityPattern,
    DistillationGovernanceGate,
    DistillationRunReport,
    FrontierDangerNeutralizer,
    FrontierMetaIntelligenceLayer,
    FrontierObservation,
    FrontierObserver,
    GovernanceGateResult,
    LineageRecord,
    ModelProfiler,
    RegistryDecision,
    RolloutManager,
    RolloutPlan,
    SandboxValidationReport,
    SandboxValidator,
    SkillCompiler,
    WeaknessInversionEngine,
)
from .signal_counterintelligence import (
    CounterintelligenceFinding,
    CounterintelligenceMode,
    IntelligenceDecision,
    SignalAttackVector,
)

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    OBSERVE_FRONTIER = "observe_frontier"
    BENCHMARK_CAPABILITY = "benchmark_capability"
    EXTRACT_PATTERN = "extract_pattern"
    CONVERT_TO_MODULE = "convert_to_module"
    SANDBOX_TEST = "sandbox_test"
    COUNTERINTELLIGENCE_ATTACK = "counterintelligence_attack"
    DEPLOYMENT_GATE = "deployment_gate"
    LIVE_MONITORING = "live_monitoring"
    KILL_OR_REVISE = "kill_or_revise"


class ArtifactLifecycleState(str, Enum):
    CANDIDATE = "candidate"
    SANDBOX_PASSED = "sandbox_passed"
    CI_PASSED = "ci_passed"
    DEPLOYED = "deployed"
    MONITORING = "monitoring"
    KILLED = "killed"
    REVISED = "revised"
    REJECTED = "rejected"


class DeploymentVerdict(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    DEFER = "defer"


class DecaySeverity(str, Enum):
    NONE = "none"
    EARLY_WARNING = "early_warning"
    MODERATE = "moderate"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"


@dataclass
class StageResult:
    stage: PipelineStage
    passed: bool
    artifact_id: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    rejection_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


@dataclass
class CounterintelligenceAttackResult:
    artifact_id: str
    survived: bool
    findings: List[CounterintelligenceFinding]
    attack_vectors_used: List[SignalAttackVector]
    compliance_score: float
    reliability_score: float
    verdict: IntelligenceDecision
    rejection_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "survived": self.survived,
            "findings": [f.to_dict() for f in self.findings],
            "attack_vectors_used": [v.value for v in self.attack_vectors_used],
            "compliance_score": self.compliance_score,
            "reliability_score": self.reliability_score,
            "verdict": self.verdict.value,
            "rejection_reasons": list(self.rejection_reasons),
        }


@dataclass
class DeploymentGateResult:
    artifact_id: str
    verdict: DeploymentVerdict
    baseline_metrics: Dict[str, float]
    candidate_metrics: Dict[str, float]
    improvement_delta: Dict[str, float]
    minimum_improvement_required: float
    actual_improvement: float
    passed: bool
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        return data


@dataclass
class DecayDetectionReport:
    artifact_id: str
    severity: DecaySeverity
    current_performance: float
    peak_performance: float
    decay_rate: float
    time_since_peak: float
    consecutive_losses: int
    regime_shift_detected: bool
    alpha_half_life_estimate: float
    action_required: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class ArtifactLifecycleRecord:
    artifact_id: str
    artifact: Optional[AlphaAlgoNativeArtifact] = None
    pattern: Optional[CapabilityPattern] = None
    source_model: str = ""
    state: ArtifactLifecycleState = ArtifactLifecycleState.CANDIDATE
    current_stage: PipelineStage = PipelineStage.OBSERVE_FRONTIER
    stage_results: List[StageResult] = field(default_factory=list)
    ci_result: Optional[CounterintelligenceAttackResult] = None
    deployment_result: Optional[DeploymentGateResult] = None
    decay_report: Optional[DecayDetectionReport] = None
    final_decision: Optional[RegistryDecision] = None
    performance_history: List[Dict[str, float]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    killed_at: Optional[float] = None
    revised_at: Optional[float] = None
    deployed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "source_model": self.source_model,
            "state": self.state.value,
            "current_stage": self.current_stage.value,
            "stage_results": [r.to_dict() for r in self.stage_results],
            "ci_result": self.ci_result.to_dict() if self.ci_result else None,
            "deployment_result": self.deployment_result.to_dict() if self.deployment_result else None,
            "decay_report": self.decay_report.to_dict() if self.decay_report else None,
            "final_decision": self.final_decision.value if self.final_decision else None,
            "performance_history": list(self.performance_history),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "killed_at": self.killed_at,
            "revised_at": self.revised_at,
            "deployed_at": self.deployed_at,
        }


@dataclass
class PipelineRunReport:
    run_id: str
    model_name: str
    artifacts_entered: int
    artifacts_passed_sandbox: int
    artifacts_passed_ci: int
    artifacts_deployed: int
    artifacts_killed: int
    artifacts_revised: int
    lifecycle_records: List[ArtifactLifecycleRecord]
    total_advantage_score: float
    elapsed_seconds: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "model_name": self.model_name,
            "artifacts_entered": self.artifacts_entered,
            "artifacts_passed_sandbox": self.artifacts_passed_sandbox,
            "artifacts_passed_ci": self.artifacts_passed_ci,
            "artifacts_deployed": self.artifacts_deployed,
            "artifacts_killed": self.artifacts_killed,
            "artifacts_revised": self.artifacts_revised,
            "lifecycle_records": [r.to_dict() for r in self.lifecycle_records],
            "total_advantage_score": round(self.total_advantage_score, 4),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "timestamp": self.timestamp,
        }


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _avg(values: Iterable[float]) -> float:
    items = [float(v) for v in values]
    return sum(items) / len(items) if items else 0.0


# ---------------------------------------------------------------------------
# Stage 6: Counterintelligence Attacker
# ---------------------------------------------------------------------------

class CounterintelligenceAttacker:
    """Runs adversarial counterintelligence attacks against sandbox-passed artifacts."""

    ATTACK_VECTORS = (
        SignalAttackVector.OVERFITTING,
        SignalAttackVector.REGIME_FRAGILITY,
        SignalAttackVector.CAUSAL_PLAUSIBILITY_FAILURE,
        SignalAttackVector.CROWDING_CAPACITY_RISK,
        SignalAttackVector.EXECUTION_STRESS_FAILURE,
        SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR,
        SignalAttackVector.DATA_LEAKAGE,
        SignalAttackVector.WEAK_CLAIM,
    )

    def __init__(
        self,
        mode: CounterintelligenceMode = CounterintelligenceMode.HARD_GATE,
        min_compliance: float = 0.80,
        min_reliability: float = 0.70,
    ):
        self.mode = mode
        self.min_compliance = min_compliance
        self.min_reliability = min_reliability

    def attack(
        self,
        artifact: AlphaAlgoNativeArtifact,
        validation: SandboxValidationReport,
        pattern: Optional[CapabilityPattern] = None,
    ) -> CounterintelligenceAttackResult:
        findings: List[CounterintelligenceFinding] = []
        rejection_reasons: List[str] = []
        vectors_used: List[SignalAttackVector] = []

        for vector in self.ATTACK_VECTORS:
            finding = self._probe(vector, artifact, validation, pattern)
            if finding is not None:
                findings.append(finding)
            vectors_used.append(vector)

        compliance = self._compliance_score(findings)
        reliability = self._reliability_score(findings, validation)

        if compliance < self.min_compliance:
            rejection_reasons.append(
                f"compliance {compliance:.3f} below minimum {self.min_compliance}"
            )
        if reliability < self.min_reliability:
            rejection_reasons.append(
                f"reliability {reliability:.3f} below minimum {self.min_reliability}"
            )

        critical = [f for f in findings if f.severity == "critical"]
        high = [f for f in findings if f.severity == "high"]

        if self.mode == CounterintelligenceMode.HARD_GATE:
            survived = (
                not critical and not high
                and compliance >= self.min_compliance
                and reliability >= self.min_reliability
            )
        elif self.mode == CounterintelligenceMode.ADVISORY:
            survived = not critical and compliance >= self.min_compliance
        else:
            survived = True

        if not survived:
            verdict = IntelligenceDecision.REJECT
        elif high:
            verdict = IntelligenceDecision.QUARANTINE
        else:
            verdict = IntelligenceDecision.ACCEPT

        if not survived and not rejection_reasons:
            rejection_reasons.append(
                f"failed CI: {len(critical)} critical, {len(high)} high findings"
            )

        return CounterintelligenceAttackResult(
            artifact_id=artifact.artifact_id,
            survived=survived,
            findings=findings,
            attack_vectors_used=vectors_used,
            compliance_score=round(compliance, 4),
            reliability_score=round(reliability, 4),
            verdict=verdict,
            rejection_reasons=rejection_reasons,
        )

    def _probe(self, vector, artifact, validation, pattern):
        probes = {
            SignalAttackVector.OVERFITTING: self._probe_overfitting,
            SignalAttackVector.REGIME_FRAGILITY: self._probe_regime,
            SignalAttackVector.CAUSAL_PLAUSIBILITY_FAILURE: self._probe_causal,
            SignalAttackVector.CROWDING_CAPACITY_RISK: self._probe_crowding,
            SignalAttackVector.EXECUTION_STRESS_FAILURE: self._probe_exec_stress,
            SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR: self._probe_adv_market,
            SignalAttackVector.DATA_LEAKAGE: self._probe_leakage,
            SignalAttackVector.WEAK_CLAIM: self._probe_weak_claim,
        }
        fn = probes.get(vector)
        return fn(artifact, validation, pattern) if fn else None

    def _probe_overfitting(self, artifact, validation, pattern):
        if validation.stability < 0.55:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "overfitting"),
                vector=SignalAttackVector.OVERFITTING,
                severity="high",
                description=f"stability {validation.stability:.3f} indicates overfitting",
            )
        if validation.improvement_vs_baseline > 0.5 and validation.stability < 0.70:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "overfit_high_lift"),
                vector=SignalAttackVector.OVERFITTING,
                severity="critical",
                description="high lift with moderate stability suggests overfitting",
            )
        return None

    def _probe_regime(self, artifact, validation, pattern):
        conditions = artifact.content.get("conditions", []) if artifact.content else []
        if len(conditions) <= 1:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "regime_frag"),
                vector=SignalAttackVector.REGIME_FRAGILITY,
                severity="high",
                description="artifact validated under too few conditions",
            )
        if pattern and len(pattern.failure_modes) > 3:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "regime_failures"),
                vector=SignalAttackVector.REGIME_FRAGILITY,
                severity="medium",
                description=f"{len(pattern.failure_modes)} known failure modes",
            )
        return None

    def _probe_causal(self, artifact, validation, pattern):
        behavior = artifact.content.get("repeatable_behavior", "") if artifact.content else ""
        transferable = artifact.content.get("transferable_part", "") if artifact.content else ""
        if not behavior or not transferable:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "causal"),
                vector=SignalAttackVector.CAUSAL_PLAUSIBILITY_FAILURE,
                severity="medium",
                description="artifact lacks causal mechanism description",
            )
        return None

    def _probe_crowding(self, artifact, validation, pattern):
        if artifact.budget_cap <= 0:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "crowding"),
                vector=SignalAttackVector.CROWDING_CAPACITY_RISK,
                severity="medium",
                description="no budget cap — crowding uncontrolled",
            )
        return None

    def _probe_exec_stress(self, artifact, validation, pattern):
        if validation.cost_delta > 0:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "exec_stress"),
                vector=SignalAttackVector.EXECUTION_STRESS_FAILURE,
                severity="medium",
                description=f"cost delta {validation.cost_delta:.3f} — stress risk",
            )
        return None

    def _probe_adv_market(self, artifact, validation, pattern):
        risk_side = [s for s in validation.side_effects if "risk" in s.lower() or "live" in s.lower()]
        if risk_side:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "adv_market"),
                vector=SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR,
                severity="critical",
                description=f"risk side effects: {risk_side}",
            )
        return None

    def _probe_leakage(self, artifact, validation, pattern):
        notes = list(pattern.non_transferable_notes) if pattern else []
        for note in notes:
            if any(t in note.lower() for t in ("lookahead", "future data", "survivorship", "leakage")):
                return CounterintelligenceFinding(
                    finding_id=_stable_id("ci", artifact.artifact_id, "leakage"),
                    vector=SignalAttackVector.DATA_LEAKAGE,
                    severity="critical",
                    description=f"potential data leakage: {note}",
                )
        return None

    def _probe_weak_claim(self, artifact, validation, pattern):
        if validation.improvement_vs_baseline <= 0:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "weak_claim"),
                vector=SignalAttackVector.WEAK_CLAIM,
                severity="high",
                description="no improvement over baseline",
            )
        if validation.improvement_vs_baseline < 0.02:
            return CounterintelligenceFinding(
                finding_id=_stable_id("ci", artifact.artifact_id, "weak_marginal"),
                vector=SignalAttackVector.WEAK_CLAIM,
                severity="medium",
                description="marginal improvement — weak claim",
            )
        return None

    def _compliance_score(self, findings):
        if not findings:
            return 1.0
        penalty = sum(
            0.30 if f.severity == "critical" else 0.15 if f.severity == "high" else 0.05
            for f in findings
        )
        return max(0.0, round(1.0 - penalty, 4))

    def _reliability_score(self, findings, validation):
        base = validation.stability
        penalty = sum(
            0.20 if f.severity == "critical" else 0.10 if f.severity == "high" else 0.03
            for f in findings
        )
        return max(0.0, round(base - penalty, 4))


# ---------------------------------------------------------------------------
# Stage 7: Deployment Gate
# ---------------------------------------------------------------------------

class DeploymentGate:
    """Deploys only if metrics improve over baseline."""

    def __init__(
        self,
        minimum_improvement: float = 0.01,
        key_metrics: Sequence[str] = ("sharpe", "win_rate", "profit_factor", "stability"),
    ):
        self.minimum_improvement = minimum_improvement
        self.key_metrics = list(key_metrics)

    def evaluate(
        self,
        artifact: AlphaAlgoNativeArtifact,
        validation: SandboxValidationReport,
        baseline_metrics: Optional[Dict[str, float]] = None,
        candidate_metrics: Optional[Dict[str, float]] = None,
    ) -> DeploymentGateResult:
        baseline = dict(baseline_metrics or {})
        candidate = dict(candidate_metrics or {})

        if not baseline:
            baseline = self._baseline_from_validation(validation)
        if not candidate:
            candidate = self._candidate_from_validation(validation)

        delta: Dict[str, float] = {}
        for key in self.key_metrics:
            b = baseline.get(key, 0.0)
            c = candidate.get(key, 0.0)
            delta[key] = round(c - b, 6)

        actual_improvement = self._weighted_improvement(delta)
        reasons: List[str] = []

        if actual_improvement < self.minimum_improvement:
            verdict = DeploymentVerdict.DENY
            reasons.append(
                f"improvement {actual_improvement:.4f} below minimum {self.minimum_improvement}"
            )
        elif any(v < 0 for v in delta.values()):
            negative_keys = [k for k, v in delta.items() if v < 0]
            verdict = DeploymentVerdict.DEFER
            reasons.append(f"negative delta on: {negative_keys} — defer for review")
        else:
            verdict = DeploymentVerdict.APPROVE

        passed = verdict == DeploymentVerdict.APPROVE

        return DeploymentGateResult(
            artifact_id=artifact.artifact_id,
            verdict=verdict,
            baseline_metrics=baseline,
            candidate_metrics=candidate,
            improvement_delta=delta,
            minimum_improvement_required=self.minimum_improvement,
            actual_improvement=round(actual_improvement, 6),
            passed=passed,
            reasons=reasons,
        )

    def _baseline_from_validation(self, v: SandboxValidationReport) -> Dict[str, float]:
        return {"sharpe": 0.0, "win_rate": 0.50, "profit_factor": 1.0, "stability": v.stability}

    def _candidate_from_validation(self, v: SandboxValidationReport) -> Dict[str, float]:
        return {
            "sharpe": v.improvement_vs_baseline,
            "win_rate": 0.50 + v.improvement_vs_baseline * 0.10,
            "profit_factor": 1.0 + v.improvement_vs_baseline,
            "stability": v.stability,
        }

    def _weighted_improvement(self, delta: Dict[str, float]) -> float:
        weights = {"sharpe": 0.35, "win_rate": 0.20, "profit_factor": 0.25, "stability": 0.20}
        return sum(delta.get(k, 0.0) * weights.get(k, 0.25) for k in self.key_metrics)


# ---------------------------------------------------------------------------
# Stages 8-9: Decay Monitor
# ---------------------------------------------------------------------------

class DecayMonitor:
    """Monitors live performance and detects alpha decay.

    Tracks performance over time, detects when alpha is decaying, and
    recommends kill or revise actions based on decay severity.
    """

    def __init__(
        self,
        early_warning_threshold: float = 0.15,
        moderate_threshold: float = 0.30,
        severe_threshold: float = 0.50,
        min_observations: int = 5,
        half_life_warning: float = 7.0,
    ):
        self.early_warning_threshold = early_warning_threshold
        self.moderate_threshold = moderate_threshold
        self.severe_threshold = severe_threshold
        self.min_observations = min_observations
        self.half_life_warning = half_life_warning

    def detect_decay(
        self,
        record: ArtifactLifecycleRecord,
        current_performance: float,
        regime_shift: bool = False,
    ) -> DecayDetectionReport:
        history = record.performance_history
        if not history:
            return self._no_decay(record.artifact_id, current_performance)

        peak = max(h.get("performance", current_performance) for h in history)
        time_since_peak = 0.0
        for i, h in enumerate(history):
            if h.get("performance", 0) == peak:
                time_since_peak = time.time() - h.get("timestamp", time.time())
                break

        decay_from_peak = max(0.0, peak - current_performance)
        decay_rate = decay_from_peak / max(time_since_peak, 1.0)

        consecutive = 0
        for h in reversed(history):
            if h.get("loss", False):
                consecutive += 1
            else:
                break

        half_life = self._estimate_half_life(history)

        severity = self._classify_severity(
            decay_from_peak, decay_rate, consecutive, regime_shift, half_life
        )
        action = self._action_for(severity, record)

        return DecayDetectionReport(
            artifact_id=record.artifact_id,
            severity=severity,
            current_performance=round(current_performance, 6),
            peak_performance=round(peak, 6),
            decay_rate=round(decay_rate, 6),
            time_since_peak=round(time_since_peak, 2),
            consecutive_losses=consecutive,
            regime_shift_detected=regime_shift,
            alpha_half_life_estimate=round(half_life, 2),
            action_required=action,
            details={
                "decay_from_peak": round(decay_from_peak, 6),
                "observation_count": len(history),
            },
        )

    def decide_kill_or_revise(
        self,
        decay: DecayDetectionReport,
        record: ArtifactLifecycleRecord,
    ) -> RegistryDecision:
        if decay.severity == DecaySeverity.CATASTROPHIC:
            return RegistryDecision.KILL
        if decay.severity == DecaySeverity.SEVERE:
            return RegistryDecision.KILL
        if decay.severity == DecaySeverity.MODERATE:
            if decay.consecutive_losses >= 10:
                return RegistryDecision.KILL
            return RegistryDecision.REVISE
        if decay.severity == DecaySeverity.EARLY_WARNING:
            return RegistryDecision.REVISE
        return RegistryDecision.KEEP

    def _no_decay(self, artifact_id: str, performance: float) -> DecayDetectionReport:
        return DecayDetectionReport(
            artifact_id=artifact_id,
            severity=DecaySeverity.NONE,
            current_performance=round(performance, 6),
            peak_performance=round(performance, 6),
            decay_rate=0.0,
            time_since_peak=0.0,
            consecutive_losses=0,
            regime_shift_detected=False,
            alpha_half_life_estimate=float("inf"),
            action_required="continue_monitoring",
        )

    def _classify_severity(self, decay, rate, consecutive, regime_shift, half_life):
        if regime_shift and decay > self.severe_threshold:
            return DecaySeverity.CATASTROPHIC
        if decay > self.severe_threshold:
            return DecaySeverity.SEVERE
        if decay > self.moderate_threshold:
            return DecaySeverity.MODERATE
        if decay > self.early_warning_threshold:
            return DecaySeverity.EARLY_WARNING
        if consecutive >= 5:
            return DecaySeverity.EARLY_WARNING
        if half_life < self.half_life_warning and half_life > 0:
            return DecaySeverity.EARLY_WARNING
        return DecaySeverity.NONE

    def _action_for(self, severity, record):
        actions = {
            DecaySeverity.NONE: "continue_monitoring",
            DecaySeverity.EARLY_WARNING: "increase_monitoring_frequency_and_prepare_revision",
            DecaySeverity.MODERATE: "revise_artifact_or_restrict_scope",
            DecaySeverity.SEVERE: "kill_artifact_immediately",
            DecaySeverity.CATASTROPHIC: "kill_and_investigate_root_cause",
        }
        return actions.get(severity, "continue_monitoring")

    def _estimate_half_life(self, history):
        if len(history) < self.min_observations:
            return float("inf")
        perfs = [h.get("performance", 0.0) for h in history]
        if not perfs or perfs[0] <= 0:
            return float("inf")
        half_val = perfs[0] / 2.0
        for i, p in enumerate(perfs):
            if p <= half_val:
                timestamps = [h.get("timestamp", i) for h in history]
                if timestamps[i] > timestamps[0]:
                    return timestamps[i] - timestamps[0]
        return float("inf")


STAGE_ORDER = (
    PipelineStage.OBSERVE_FRONTIER,
    PipelineStage.BENCHMARK_CAPABILITY,
    PipelineStage.EXTRACT_PATTERN,
    PipelineStage.CONVERT_TO_MODULE,
    PipelineStage.SANDBOX_TEST,
    PipelineStage.COUNTERINTELLIGENCE_ATTACK,
    PipelineStage.DEPLOYMENT_GATE,
    PipelineStage.LIVE_MONITORING,
    PipelineStage.KILL_OR_REVISE,
)


class AlphaAlgoLifecyclePipeline:
    """Nine-stage autonomous research-to-deployment pipeline.

    Stages 1-4: FrontierMetaIntelligenceLayer (observe, benchmark, extract, convert)
    Stage 5:   SandboxValidator (sandbox test)
    Stage 6:   CounterintelligenceAttacker (CI attacks)
    Stage 7:   DeploymentGate (deploy only if metrics improve)
    Stages 8-9: DecayMonitor (monitor live, kill or revise)
    """

    def __init__(
        self,
        meta_layer: Optional[FrontierMetaIntelligenceLayer] = None,
        sandbox: Optional[SandboxValidator] = None,
        ci_attacker: Optional[CounterintelligenceAttacker] = None,
        deployment_gate: Optional[DeploymentGate] = None,
        decay_monitor: Optional[DecayMonitor] = None,
        objective: Optional[AEANGlobalObjective] = None,
    ):
        self.meta_layer = meta_layer or FrontierMetaIntelligenceLayer()
        self.sandbox = sandbox or SandboxValidator(objective or AEANGlobalObjective())
        self.ci_attacker = ci_attacker or CounterintelligenceAttacker()
        self.deployment_gate = deployment_gate or DeploymentGate()
        self.decay_monitor = decay_monitor or DecayMonitor()
        self.objective = objective or AEANGlobalObjective()
        self.lifecycle_records: Dict[str, ArtifactLifecycleRecord] = {}

    def run(
        self,
        model_name: str,
        observations: Sequence[FrontierObservation],
        benchmark_tasks: Sequence[BenchmarkTask],
        benchmark_results: Sequence[BenchmarkResult],
        baseline_metrics: Optional[Dict[str, float]] = None,
    ) -> PipelineRunReport:
        start = time.time()

        # Stages 1-4: observe -> benchmark -> extract -> convert
        advantage_report = self.meta_layer.arbitrage_frontier(
            model_name, observations, benchmark_tasks, benchmark_results
        )
        distillation = advantage_report.distillation
        records: List[ArtifactLifecycleRecord] = []

        for artifact, pattern in zip(distillation.artifacts, distillation.patterns):
            record = self._init_record(artifact, pattern, model_name)
            self.lifecycle_records[record.artifact_id] = record

            # Stage 5: Sandbox test
            if not self._stage_sandbox(record, distillation):
                records.append(record)
                continue

            # Stage 6: Counterintelligence attacks
            if not self._stage_ci_attack(record, distillation):
                records.append(record)
                continue

            # Stage 7: Deployment gate
            if not self._stage_deployment_gate(record, baseline_metrics):
                records.append(record)
                continue

            # Stages 8-9: Deployed to live monitoring
            record.state = ArtifactLifecycleState.MONITORING
            record.current_stage = PipelineStage.LIVE_MONITORING
            record.deployed_at = time.time()
            record.updated_at = time.time()
            record.stage_results.append(StageResult(
                stage=PipelineStage.LIVE_MONITORING,
                passed=True,
                artifact_id=record.artifact_id,
                details={"status": "deployed_to_live_monitoring"},
            ))
            records.append(record)

        elapsed = time.time() - start
        return PipelineRunReport(
            run_id=_stable_id("pipeline", model_name, str(start)),
            model_name=model_name,
            artifacts_entered=len(records),
            artifacts_passed_sandbox=sum(
                1 for r in records
                if any(s.stage == PipelineStage.SANDBOX_TEST and s.passed for s in r.stage_results)
            ),
            artifacts_passed_ci=sum(
                1 for r in records
                if r.state in (ArtifactLifecycleState.CI_PASSED, ArtifactLifecycleState.DEPLOYED, ArtifactLifecycleState.MONITORING)
            ),
            artifacts_deployed=sum(
                1 for r in records
                if r.state in (ArtifactLifecycleState.DEPLOYED, ArtifactLifecycleState.MONITORING)
            ),
            artifacts_killed=sum(1 for r in records if r.state == ArtifactLifecycleState.KILLED),
            artifacts_revised=sum(1 for r in records if r.state == ArtifactLifecycleState.REVISED),
            lifecycle_records=records,
            total_advantage_score=advantage_report.advantage_score,
            elapsed_seconds=elapsed,
        )

    def _init_record(self, artifact, pattern, model_name):
        record = ArtifactLifecycleRecord(
            artifact_id=artifact.artifact_id,
            artifact=artifact,
            pattern=pattern,
            source_model=model_name,
            state=ArtifactLifecycleState.CANDIDATE,
            current_stage=PipelineStage.CONVERT_TO_MODULE,
        )
        for stage in (PipelineStage.OBSERVE_FRONTIER, PipelineStage.BENCHMARK_CAPABILITY,
                      PipelineStage.EXTRACT_PATTERN, PipelineStage.CONVERT_TO_MODULE):
            record.stage_results.append(StageResult(
                stage=stage, passed=True, artifact_id=artifact.artifact_id,
                details={"artifact_kind": artifact.kind.value} if stage == PipelineStage.CONVERT_TO_MODULE else {},
            ))
        return record

    def _stage_sandbox(self, record, distillation):
        artifact = record.artifact
        if artifact is None:
            record.state = ArtifactLifecycleState.REJECTED
            record.stage_results.append(StageResult(
                stage=PipelineStage.SANDBOX_TEST, passed=False,
                artifact_id=record.artifact_id, rejection_reasons=["no artifact"],
            ))
            return False

        matching = [v for v in distillation.validation_reports if v.artifact_id == artifact.artifact_id]
        validation = matching[0] if matching else self.sandbox.validate(artifact, [])
        passed = validation.accepted

        record.stage_results.append(StageResult(
            stage=PipelineStage.SANDBOX_TEST, passed=passed,
            artifact_id=record.artifact_id,
            details={"improvement": validation.improvement_vs_baseline, "stability": validation.stability},
            rejection_reasons=[] if passed else ["sandbox validation failed"],
        ))
        if passed:
            record.state = ArtifactLifecycleState.SANDBOX_PASSED
            record.current_stage = PipelineStage.SANDBOX_TEST
        else:
            record.state = ArtifactLifecycleState.REJECTED
            record.final_decision = RegistryDecision.KILL
        record.updated_at = time.time()
        return passed

    def _stage_ci_attack(self, record, distillation):
        artifact = record.artifact
        if artifact is None:
            return False

        matching = [v for v in distillation.validation_reports if v.artifact_id == artifact.artifact_id]
        validation = matching[0] if matching else self.sandbox.validate(artifact, [])
        ci_result = self.ci_attacker.attack(artifact, validation, record.pattern)
        record.ci_result = ci_result

        passed = ci_result.survived
        record.stage_results.append(StageResult(
            stage=PipelineStage.COUNTERINTELLIGENCE_ATTACK, passed=passed,
            artifact_id=record.artifact_id,
            details={"compliance": ci_result.compliance_score, "reliability": ci_result.reliability_score},
            rejection_reasons=ci_result.rejection_reasons,
        ))
        if passed:
            record.state = ArtifactLifecycleState.CI_PASSED
            record.current_stage = PipelineStage.COUNTERINTELLIGENCE_ATTACK
        else:
            record.state = ArtifactLifecycleState.REJECTED
            record.final_decision = RegistryDecision.KILL
        record.updated_at = time.time()
        return passed

    def _stage_deployment_gate(self, record, baseline_metrics):
        artifact = record.artifact
        if artifact is None:
            return False

        validation = self.sandbox.validate(artifact, [])
        gate_result = self.deployment_gate.evaluate(artifact, validation, baseline_metrics)
        record.deployment_result = gate_result

        passed = gate_result.passed
        record.stage_results.append(StageResult(
            stage=PipelineStage.DEPLOYMENT_GATE, passed=passed,
            artifact_id=record.artifact_id,
            details={"verdict": gate_result.verdict.value, "improvement": gate_result.actual_improvement},
            rejection_reasons=gate_result.reasons,
        ))
        if passed:
            record.state = ArtifactLifecycleState.DEPLOYED
            record.current_stage = PipelineStage.DEPLOYMENT_GATE
        else:
            record.state = ArtifactLifecycleState.REJECTED
            record.final_decision = RegistryDecision.KILL
        record.updated_at = time.time()
        return passed

    # ------------------------------------------------------------------
    # Live monitoring + kill/revise (stages 8-9)
    # ------------------------------------------------------------------

    def monitor_artifact(self, artifact_id, current_performance, regime_shift=False):
        record = self.lifecycle_records.get(artifact_id)
        if record is None:
            return DecayDetectionReport(
                artifact_id=artifact_id, severity=DecaySeverity.NONE,
                current_performance=current_performance, peak_performance=current_performance,
                decay_rate=0.0, time_since_peak=0.0, consecutive_losses=0,
                regime_shift_detected=False, alpha_half_life_estimate=float("inf"),
                action_required="artifact_not_found",
            )

        record.performance_history.append({
            "performance": current_performance, "timestamp": time.time(),
            "regime_shift": regime_shift,
        })
        decay = self.decay_monitor.detect_decay(record, current_performance, regime_shift)
        record.decay_report = decay
        record.stage_results.append(StageResult(
            stage=PipelineStage.LIVE_MONITORING,
            passed=decay.severity in (DecaySeverity.NONE, DecaySeverity.EARLY_WARNING),
            artifact_id=artifact_id,
            details={"severity": decay.severity.value, "action": decay.action_required},
        ))
        record.updated_at = time.time()
        return decay

    def kill_or_revise(self, artifact_id, current_performance, regime_shift=False):
        record = self.lifecycle_records.get(artifact_id)
        if record is None:
            return None

        decay = self.monitor_artifact(artifact_id, current_performance, regime_shift)
        decision = self.decay_monitor.decide_kill_or_revise(decay, record)
        record.final_decision = decision

        if decision == RegistryDecision.KILL:
            record.state = ArtifactLifecycleState.KILLED
            record.killed_at = time.time()
            action = "killed"
        elif decision == RegistryDecision.REVISE:
            record.state = ArtifactLifecycleState.REVISED
            record.revised_at = time.time()
            action = "revised"
        else:
            action = "kept"

        record.stage_results.append(StageResult(
            stage=PipelineStage.KILL_OR_REVISE,
            passed=decision != RegistryDecision.KILL,
            artifact_id=artifact_id,
            details={"decision": decision.value, "severity": decay.severity.value, "action": action},
        ))
        record.updated_at = time.time()
        return record

    async def run_continuous(
        self,
        feed_provider,
        baseline_metrics=None,
        sleep_seconds: float = 300.0,
        max_cycles: Optional[int] = None,
    ):
        reports = []
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            batch = feed_provider()
            if hasattr(batch, "__await__"):
                batch = await batch
            for item in batch:
                report = self.run(
                    item["model_name"],
                    item.get("observations", ()),
                    item.get("benchmark_tasks", ()),
                    item.get("benchmark_results", ()),
                    baseline_metrics,
                )
                reports.append(report)
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                await asyncio.sleep(sleep_seconds)
        return tuple(reports)


__all__ = [
    "AlphaAlgoLifecyclePipeline",
    "ArtifactLifecycleRecord",
    "ArtifactLifecycleState",
    "CounterintelligenceAttackResult",
    "CounterintelligenceAttacker",
    "DecayDetectionReport",
    "DecayMonitor",
    "DecaySeverity",
    "DeploymentGate",
    "DeploymentGateResult",
    "DeploymentVerdict",
    "PipelineRunReport",
    "PipelineStage",
    "STAGE_ORDER",
    "StageResult",
]
