"""Frontier capability distillation under AlphaAlgo governance.

This subsystem observes frontier systems, profiles what they are good at,
extracts repeatable transferable patterns, converts weaknesses into controls,
and compiles only AlphaAlgo-native artifacts. It does not copy model weights,
prompts, proprietary data, or hidden implementation details.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class FrontierObservationType(str, Enum):
    """What kind of frontier-system evidence was observed."""

    MODEL_RELEASE = "model_release"
    PAPER = "paper"
    EVAL_RESULT = "eval_result"
    API_BEHAVIOR = "api_behavior"
    TOOL_USE_PATTERN = "tool_use_pattern"
    LONG_CONTEXT_BEHAVIOR = "long_context_behavior"
    FAILURE_REPORT = "failure_report"
    USAGE_TRACE = "usage_trace"


class CapabilityDimension(str, Enum):
    """Capability dimensions profiled for each frontier model."""

    REASONING_DEPTH = "reasoning_depth"
    SPEED = "speed"
    COST = "cost"
    TOOL_USE = "tool_use"
    MULTIMODAL = "multimodal"
    MEMORY_CONTEXT = "memory_context"
    RELIABILITY = "reliability"
    CONTROLLABILITY = "controllability"


class CapabilityPatternType(str, Enum):
    """Origin class of a transferable capability pattern."""

    ARCHITECTURAL = "architectural"
    PROCEDURAL = "procedural"
    TRAINING_RELATED = "training_related"


class AlphaAlgoArtifactKind(str, Enum):
    """Allowed AlphaAlgo-native artifact targets."""

    ROUTING_RULE = "routing_rule"
    SKILL_MODULE = "skill_module"
    TOOL_USE_PLAYBOOK = "tool_use_playbook"
    PROMPT_PROGRAM_TEMPLATE = "prompt_program_template"
    CRITIC_POLICY = "critic_policy"
    MEMORY_PATTERN = "memory_pattern"
    CONTEXT_STRATEGY = "context_strategy"
    MODEL_SELECTION_POLICY = "model_selection_policy"
    FINE_TUNE_ADAPTER_OBJECTIVE = "fine_tune_adapter_objective"
    GOVERNANCE_INVARIANT = "governance_invariant"


class ValidationMode(str, Enum):
    """Sandbox validation modes before selective rollout."""

    REPLAY = "replay"
    SIMULATION = "simulation"
    OFFLINE_EVAL = "offline_eval"
    SHADOW_MODE = "shadow_mode"
    LIMITED_LIVE_TRAFFIC = "limited_live_traffic"


class RolloutScope(str, Enum):
    """Selective rollout shape. Global rollout is intentionally absent."""

    DOMAIN_SPECIFIC = "domain_specific"
    AGENT_SPECIFIC = "agent_specific"
    TASK_SPECIFIC = "task_specific"
    BUDGET_CAPPED = "budget_capped"


class RegistryDecision(str, Enum):
    """Lifecycle decision for distilled capability artifacts."""

    KEEP = "keep"
    REVISE = "revise"
    KILL = "kill"


class DangerSeverity(str, Enum):
    """Severity of a non-transferable or dangerous frontier behavior."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReverseEngineeringSignalType(str, Enum):
    """Observable AI-system surface to reverse engineer."""

    WORKFLOW = "workflow"
    OUTPUT = "output"
    CLAIM = "claim"


class ReverseEngineeringClassification(str, Enum):
    """Classification of a reverse-engineered idea."""

    REAL_CAPABILITY = "real_capability"
    FAKE_HYPE = "fake_hype"
    REUSABLE_COMPONENT = "reusable_component"
    LOW_VALUE = "low_value"
    DANGEROUS_POWER = "dangerous_power"


@dataclass(frozen=True)
class FrontierObservation:
    """One observed piece of evidence about a frontier system."""

    observation_id: str
    model_name: str
    observation_type: FrontierObservationType
    summary: str
    observed_behavior: str
    conditions: Tuple[str, ...] = field(default_factory=tuple)
    metrics: Dict[str, float] = field(default_factory=dict)
    failure_modes: Tuple[str, ...] = field(default_factory=tuple)
    cost_estimate: float = 0.0
    latency_ms: float = 0.0
    source_uri: Optional[str] = None
    observed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["observation_type"] = self.observation_type.value
        return data


@dataclass(frozen=True)
class ModelCapabilityProfile:
    """Structured answer to what a model is good at and when."""

    model_name: str
    dimension_scores: Dict[CapabilityDimension, float]
    strengths: Tuple[str, ...]
    weaknesses: Tuple[str, ...]
    task_fit: Dict[str, float]
    conditions: Tuple[str, ...]
    failure_modes: Tuple[str, ...]
    average_cost: float
    average_latency_ms: float
    reliability: float
    controllability: float
    observation_ids: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "dimension_scores": {key.value: value for key, value in self.dimension_scores.items()},
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "task_fit": dict(self.task_fit),
            "conditions": list(self.conditions),
            "failure_modes": list(self.failure_modes),
            "average_cost": self.average_cost,
            "average_latency_ms": self.average_latency_ms,
            "reliability": self.reliability,
            "controllability": self.controllability,
            "observation_ids": list(self.observation_ids),
        }


@dataclass(frozen=True)
class BenchmarkTask:
    """AEAN/AlphaAlgo-relevant benchmark task."""

    task_id: str
    domain: str
    task_type: str
    objective: str
    baseline_score: float
    max_cost: float = 1.0
    max_latency_ms: float = 10_000.0
    required_dimensions: Tuple[CapabilityDimension, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BenchmarkResult:
    """Measured model behavior on an AlphaAlgo-relevant task."""

    task_id: str
    model_name: str
    score: float
    baseline_score: float
    cost: float
    latency_ms: float
    stability: float
    failures: Tuple[str, ...] = field(default_factory=tuple)
    side_effects: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def lift(self) -> float:
        return self.score - self.baseline_score


@dataclass(frozen=True)
class AEANGlobalObjective:
    """Hard objective constraints for retaining distilled frontier advantage."""

    min_long_term_lift: float = 0.0
    min_stability: float = 0.70
    max_cost_delta: float = 0.0
    allowed_risk_side_effects: int = 0
    require_governance_compatibility: bool = True


@dataclass(frozen=True)
class CapabilityPattern:
    """Repeatable model behavior with a transferable AlphaAlgo part."""

    pattern_id: str
    source_model: str
    name: str
    repeatable_behavior: str
    pattern_type: CapabilityPatternType
    transferable_part: str
    dimensions: Tuple[CapabilityDimension, ...]
    conditions: Tuple[str, ...]
    failure_modes: Tuple[str, ...]
    evidence_observation_ids: Tuple[str, ...]
    benchmark_task_ids: Tuple[str, ...]
    expected_lift: float
    non_transferable_notes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "source_model": self.source_model,
            "name": self.name,
            "repeatable_behavior": self.repeatable_behavior,
            "pattern_type": self.pattern_type.value,
            "transferable_part": self.transferable_part,
            "dimensions": [item.value for item in self.dimensions],
            "conditions": list(self.conditions),
            "failure_modes": list(self.failure_modes),
            "evidence_observation_ids": list(self.evidence_observation_ids),
            "benchmark_task_ids": list(self.benchmark_task_ids),
            "expected_lift": self.expected_lift,
            "non_transferable_notes": list(self.non_transferable_notes),
        }


@dataclass(frozen=True)
class WeaknessControl:
    """A frontier weakness inverted into an AlphaAlgo control."""

    weakness: str
    control_name: str
    control_rule: str
    artifact_kind: AlphaAlgoArtifactKind
    enforced_as_invariant: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["artifact_kind"] = self.artifact_kind.value
        return data


@dataclass(frozen=True)
class AlphaAlgoNativeArtifact:
    """Deployable AlphaAlgo-native result of a capability transfer."""

    artifact_id: str
    kind: AlphaAlgoArtifactKind
    name: str
    content: Dict[str, Any]
    source_pattern_id: str
    valid_domains: Tuple[str, ...]
    valid_agents: Tuple[str, ...] = field(default_factory=tuple)
    valid_tasks: Tuple[str, ...] = field(default_factory=tuple)
    budget_cap: float = 0.0
    rollback_triggers: Tuple[str, ...] = field(default_factory=tuple)
    controls: Tuple[WeaknessControl, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind.value,
            "name": self.name,
            "content": dict(self.content),
            "source_pattern_id": self.source_pattern_id,
            "valid_domains": list(self.valid_domains),
            "valid_agents": list(self.valid_agents),
            "valid_tasks": list(self.valid_tasks),
            "budget_cap": self.budget_cap,
            "rollback_triggers": list(self.rollback_triggers),
            "controls": [control.to_dict() for control in self.controls],
        }


@dataclass(frozen=True)
class GovernanceGateResult:
    """Governance decision before validation or rollout."""

    accepted: bool
    issues: Tuple[str, ...] = field(default_factory=tuple)
    required_invariants: Tuple[str, ...] = field(default_factory=tuple)
    notes: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SandboxValidationReport:
    """Sandbox validation summary for one artifact."""

    artifact_id: str
    modes: Tuple[ValidationMode, ...]
    improvement_vs_baseline: float
    stability: float
    cost_delta: float
    side_effects: Tuple[str, ...]
    compatible_with_global_objective: bool
    accepted: bool
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RolloutPlan:
    """Selective rollout plan; never global-first."""

    artifact_id: str
    scope: RolloutScope
    domains: Tuple[str, ...] = field(default_factory=tuple)
    agents: Tuple[str, ...] = field(default_factory=tuple)
    tasks: Tuple[str, ...] = field(default_factory=tuple)
    budget_cap: float = 0.0
    canary_fraction: float = 0.05
    rollback_triggers: Tuple[str, ...] = field(default_factory=tuple)
    approved_for_live: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["scope"] = self.scope.value
        return data


@dataclass(frozen=True)
class LineageRecord:
    """Registry record linking source model evidence to AlphaAlgo artifact."""

    lineage_id: str
    source_model: str
    observation_ids: Tuple[str, ...]
    pattern: CapabilityPattern
    artifact: AlphaAlgoNativeArtifact
    governance: GovernanceGateResult
    validation: SandboxValidationReport
    rollout: Optional[RolloutPlan]
    decision: RegistryDecision
    actual_lift: float = 0.0
    drift: float = 0.0
    failure_patterns: Tuple[str, ...] = field(default_factory=tuple)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "source_model": self.source_model,
            "observation_ids": list(self.observation_ids),
            "pattern": self.pattern.to_dict(),
            "artifact": self.artifact.to_dict(),
            "governance": asdict(self.governance),
            "validation": {
                **asdict(self.validation),
                "modes": [mode.value for mode in self.validation.modes],
            },
            "rollout": self.rollout.to_dict() if self.rollout else None,
            "decision": self.decision.value,
            "actual_lift": self.actual_lift,
            "drift": self.drift,
            "failure_patterns": list(self.failure_patterns),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class FrontierDangerNeutralization:
    """Dangerous frontier behavior converted into an AlphaAlgo control or block."""

    source_risk: str
    severity: DangerSeverity
    neutralizing_control: str
    artifact_kind: AlphaAlgoArtifactKind
    blocked_transfer: bool = False
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_risk": self.source_risk,
            "severity": self.severity.value,
            "neutralizing_control": self.neutralizing_control,
            "artifact_kind": self.artifact_kind.value,
            "blocked_transfer": self.blocked_transfer,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class FrontierArbitrageOpportunity:
    """Meta-intelligence view of frontier R&D value available to arbitrage."""

    model_name: str
    studied_outputs: Tuple[str, ...]
    useful_output_score: float
    dangerous_output_score: float
    transferable_value: float
    expected_alphaalgo_advantage: float
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AISystemObservation:
    """Observable workflow, output, or claim from an external AI system."""

    observation_id: str
    system_name: str
    signal_type: ReverseEngineeringSignalType
    workflow_steps: Tuple[str, ...] = field(default_factory=tuple)
    outputs: Tuple[str, ...] = field(default_factory=tuple)
    claims: Tuple[str, ...] = field(default_factory=tuple)
    evidence: Tuple[str, ...] = field(default_factory=tuple)
    metrics: Dict[str, float] = field(default_factory=dict)
    observed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["signal_type"] = self.signal_type.value
        return data


@dataclass(frozen=True)
class AISystemDecomposition:
    """Decomposed view of an AI-system observation."""

    observation_id: str
    tools_used: Tuple[str, ...]
    architecture_patterns: Tuple[str, ...]
    data_flow: Tuple[str, ...]
    control_surfaces: Tuple[str, ...]
    claims: Tuple[str, ...]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReverseEngineeringAssessment:
    """Classification of whether an observed idea is real, reusable, hype, or unsafe."""

    observation_id: str
    classification: ReverseEngineeringClassification
    capability_score: float
    hype_score: float
    danger_score: float
    reusable_components: Tuple[str, ...] = field(default_factory=tuple)
    rejected_ideas: Tuple[str, ...] = field(default_factory=tuple)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["classification"] = self.classification.value
        return data


@dataclass(frozen=True)
class ReusableComponentExtraction:
    """Useful reverse-engineered component that can become a native artifact."""

    component_id: str
    source_observation_id: str
    component_name: str
    pattern: str
    artifact_kind: AlphaAlgoArtifactKind
    value_score: float
    risk_controls: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["artifact_kind"] = self.artifact_kind.value
        return data


@dataclass(frozen=True)
class AISystemReverseEngineeringReport:
    """Full reverse-engineering report for external AI-system surfaces."""

    system_name: str
    observations: Tuple[AISystemObservation, ...]
    decompositions: Tuple[AISystemDecomposition, ...]
    assessments: Tuple[ReverseEngineeringAssessment, ...]
    extracted_components: Tuple[ReusableComponentExtraction, ...]
    rejected_ideas: Tuple[str, ...]
    frontier_observations: Tuple[FrontierObservation, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_name": self.system_name,
            "observations": [item.to_dict() for item in self.observations],
            "decompositions": [item.to_dict() for item in self.decompositions],
            "assessments": [item.to_dict() for item in self.assessments],
            "extracted_components": [item.to_dict() for item in self.extracted_components],
            "rejected_ideas": list(self.rejected_ideas),
            "frontier_observations": [item.to_dict() for item in self.frontier_observations],
        }


@dataclass(frozen=True)
class AlphaAlgoAdvantageReport:
    """Result of converting frontier outputs into governed AlphaAlgo advantage."""

    model_name: str
    opportunity: FrontierArbitrageOpportunity
    distillation: DistillationRunReport
    neutralized_dangers: Tuple[FrontierDangerNeutralization, ...]
    native_artifacts: Tuple[AlphaAlgoNativeArtifact, ...]
    active_rollouts: Tuple[RolloutPlan, ...]
    kept_lineage_ids: Tuple[str, ...]
    killed_lineage_ids: Tuple[str, ...]
    advantage_score: float
    reverse_engineering: Optional[AISystemReverseEngineeringReport] = None
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "opportunity": self.opportunity.to_dict(),
            "distillation": self.distillation.to_dict(),
            "neutralized_dangers": [item.to_dict() for item in self.neutralized_dangers],
            "native_artifacts": [artifact.to_dict() for artifact in self.native_artifacts],
            "active_rollouts": [rollout.to_dict() for rollout in self.active_rollouts],
            "kept_lineage_ids": list(self.kept_lineage_ids),
            "killed_lineage_ids": list(self.killed_lineage_ids),
            "advantage_score": self.advantage_score,
            "reverse_engineering": self.reverse_engineering.to_dict() if self.reverse_engineering else None,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class DistillationRunReport:
    """End-to-end distillation result."""

    model_name: str
    profile: ModelCapabilityProfile
    patterns: Tuple[CapabilityPattern, ...]
    artifacts: Tuple[AlphaAlgoNativeArtifact, ...]
    governance_results: Tuple[GovernanceGateResult, ...]
    validation_reports: Tuple[SandboxValidationReport, ...]
    rollout_plans: Tuple[RolloutPlan, ...]
    lineage_records: Tuple[LineageRecord, ...]
    rejected_patterns: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "profile": self.profile.to_dict(),
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "governance_results": [asdict(result) for result in self.governance_results],
            "validation_reports": [
                {
                    **asdict(report),
                    "modes": [mode.value for mode in report.modes],
                }
                for report in self.validation_reports
            ],
            "rollout_plans": [plan.to_dict() for plan in self.rollout_plans],
            "lineage_records": [record.to_dict() for record in self.lineage_records],
            "rejected_patterns": list(self.rejected_patterns),
        }


class FrontierObserver:
    """Stores raw observations about frontier systems."""

    def __init__(self):
        self.observations: Dict[str, FrontierObservation] = {}

    def observe(self, observation: FrontierObservation) -> FrontierObservation:
        self.observations[observation.observation_id] = observation
        return observation

    def observe_many(self, observations: Iterable[FrontierObservation]) -> List[FrontierObservation]:
        return [self.observe(observation) for observation in observations]

    def for_model(self, model_name: str) -> List[FrontierObservation]:
        return [item for item in self.observations.values() if item.model_name == model_name]


class ModelProfiler:
    """Builds structured profiles from observations and AlphaAlgo benchmarks."""

    def build_profile(
        self,
        model_name: str,
        observations: Sequence[FrontierObservation],
        benchmark_results: Sequence[BenchmarkResult],
    ) -> ModelCapabilityProfile:
        relevant_results = [result for result in benchmark_results if result.model_name == model_name]
        dimension_scores = {dimension: self._score_dimension(dimension, observations, relevant_results) for dimension in CapabilityDimension}
        strengths = tuple(dimension.value for dimension, score in dimension_scores.items() if score >= 0.72)
        weaknesses = tuple(dimension.value for dimension, score in dimension_scores.items() if score <= 0.45)
        task_fit = self._task_fit(relevant_results)
        conditions = tuple(dict.fromkeys(condition for item in observations for condition in item.conditions))
        failure_modes = tuple(dict.fromkeys(mode for item in observations for mode in item.failure_modes))
        if relevant_results:
            failure_modes = tuple(dict.fromkeys(list(failure_modes) + [failure for result in relevant_results for failure in result.failures]))
        average_cost = _avg([item.cost_estimate for item in observations if item.cost_estimate] + [item.cost for item in relevant_results])
        average_latency = _avg([item.latency_ms for item in observations if item.latency_ms] + [item.latency_ms for item in relevant_results])
        reliability = dimension_scores[CapabilityDimension.RELIABILITY]
        controllability = dimension_scores[CapabilityDimension.CONTROLLABILITY]
        return ModelCapabilityProfile(
            model_name=model_name,
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            task_fit=task_fit,
            conditions=conditions,
            failure_modes=failure_modes,
            average_cost=average_cost,
            average_latency_ms=average_latency,
            reliability=reliability,
            controllability=controllability,
            observation_ids=tuple(item.observation_id for item in observations),
        )

    def _score_dimension(
        self,
        dimension: CapabilityDimension,
        observations: Sequence[FrontierObservation],
        results: Sequence[BenchmarkResult],
    ) -> float:
        metric_values = [item.metrics[dimension.value] for item in observations if dimension.value in item.metrics]
        if dimension == CapabilityDimension.RELIABILITY:
            metric_values.extend([max(0.0, min(result.stability - len(result.failures) * 0.08, 1.0)) for result in results])
        elif dimension == CapabilityDimension.SPEED:
            metric_values.extend([1.0 - min(result.latency_ms / 30_000.0, 1.0) for result in results])
        elif dimension == CapabilityDimension.COST:
            metric_values.extend([1.0 - min(result.cost / 10.0, 1.0) for result in results])
        else:
            metric_values.extend([max(0.0, min(0.55 + result.lift, 1.0)) for result in results if result.lift > 0])
        return round(_avg(metric_values), 4)

    def _task_fit(self, results: Sequence[BenchmarkResult]) -> Dict[str, float]:
        by_task: Dict[str, List[float]] = {}
        for result in results:
            by_task.setdefault(result.task_id, []).append(result.score)
        return {task_id: round(_avg(scores), 4) for task_id, scores in by_task.items()}


class BenchmarkHarness:
    """Records and summarizes AlphaAlgo-relevant benchmark results."""

    def __init__(self):
        self.tasks: Dict[str, BenchmarkTask] = {}
        self.results: List[BenchmarkResult] = []

    def add_task(self, task: BenchmarkTask) -> BenchmarkTask:
        self.tasks[task.task_id] = task
        return task

    def record_result(self, result: BenchmarkResult) -> BenchmarkResult:
        self.results.append(result)
        return result

    def for_model(self, model_name: str) -> List[BenchmarkResult]:
        return [result for result in self.results if result.model_name == model_name]


class CapabilityExtractor:
    """Finds repeatable transferable patterns, not model internals."""

    def extract(
        self,
        profile: ModelCapabilityProfile,
        observations: Sequence[FrontierObservation],
        benchmark_results: Sequence[BenchmarkResult],
    ) -> List[CapabilityPattern]:
        patterns: List[CapabilityPattern] = []
        positive_results = [result for result in benchmark_results if result.model_name == profile.model_name and result.lift > 0.03]
        for dimension, score in profile.dimension_scores.items():
            if score < 0.68:
                continue
            related_obs = [item for item in observations if dimension.value in item.metrics or self._dimension_is_implied(dimension, item)]
            related_results = [result for result in positive_results if self._result_matches_dimension(dimension, result)]
            if not related_obs and not related_results:
                continue
            pattern = self._build_pattern(profile, dimension, related_obs, related_results)
            if pattern.transferable_part and not self._requires_model_copy(pattern):
                patterns.append(pattern)
        return patterns

    def _build_pattern(
        self,
        profile: ModelCapabilityProfile,
        dimension: CapabilityDimension,
        observations: Sequence[FrontierObservation],
        results: Sequence[BenchmarkResult],
    ) -> CapabilityPattern:
        pattern_type = {
            CapabilityDimension.TOOL_USE: CapabilityPatternType.PROCEDURAL,
            CapabilityDimension.MEMORY_CONTEXT: CapabilityPatternType.ARCHITECTURAL,
            CapabilityDimension.REASONING_DEPTH: CapabilityPatternType.PROCEDURAL,
            CapabilityDimension.CONTROLLABILITY: CapabilityPatternType.ARCHITECTURAL,
        }.get(dimension, CapabilityPatternType.PROCEDURAL)
        behavior = self._repeatable_behavior(dimension)
        transferable = self._transferable_part(dimension)
        pattern_id = _stable_id("pattern", profile.model_name, dimension.value, ",".join(item.observation_id for item in observations))
        return CapabilityPattern(
            pattern_id=pattern_id,
            source_model=profile.model_name,
            name=f"{profile.model_name}::{dimension.value}",
            repeatable_behavior=behavior,
            pattern_type=pattern_type,
            transferable_part=transferable,
            dimensions=(dimension,),
            conditions=tuple(dict.fromkeys(condition for item in observations for condition in item.conditions)) or profile.conditions,
            failure_modes=profile.failure_modes,
            evidence_observation_ids=tuple(item.observation_id for item in observations),
            benchmark_task_ids=tuple(result.task_id for result in results),
            expected_lift=round(_avg([result.lift for result in results] or [profile.dimension_scores[dimension] - 0.55]), 4),
            non_transferable_notes=("model weights, hidden prompts, and proprietary training data are excluded",),
        )

    def _repeatable_behavior(self, dimension: CapabilityDimension) -> str:
        mapping = {
            CapabilityDimension.REASONING_DEPTH: "decomposes hard tasks into verifiable intermediate claims before acting",
            CapabilityDimension.SPEED: "routes easy subtasks through cheaper fast paths and reserves slow reasoning for blockers",
            CapabilityDimension.COST: "uses budget-aware model and tool selection instead of defaulting to maximum capability",
            CapabilityDimension.TOOL_USE: "plans tool calls in batches, executes read-only calls in parallel, and checks outputs before writes",
            CapabilityDimension.MULTIMODAL: "grounds visual or document evidence into structured facts before decision use",
            CapabilityDimension.MEMORY_CONTEXT: "compacts long context into stable facts plus recent working memory",
            CapabilityDimension.RELIABILITY: "uses self-consistency and verifier passes for high-risk outputs",
            CapabilityDimension.CONTROLLABILITY: "keeps explicit task boundaries, refusal rules, and escalation triggers",
        }
        return mapping[dimension]

    def _transferable_part(self, dimension: CapabilityDimension) -> str:
        mapping = {
            CapabilityDimension.REASONING_DEPTH: "claim decomposition plus verifier checkpoints",
            CapabilityDimension.SPEED: "latency-aware routing rule",
            CapabilityDimension.COST: "cost-budgeted model selection policy",
            CapabilityDimension.TOOL_USE: "programmatic tool-use playbook",
            CapabilityDimension.MULTIMODAL: "evidence grounding skill module",
            CapabilityDimension.MEMORY_CONTEXT: "hierarchical context strategy",
            CapabilityDimension.RELIABILITY: "critic policy with hidden/adversarial checks",
            CapabilityDimension.CONTROLLABILITY: "governance invariant and escalation policy",
        }
        return mapping[dimension]

    def _dimension_is_implied(self, dimension: CapabilityDimension, observation: FrontierObservation) -> bool:
        text = f"{observation.summary} {observation.observed_behavior}".lower()
        keywords = {
            CapabilityDimension.REASONING_DEPTH: ("reason", "decompose", "plan"),
            CapabilityDimension.SPEED: ("speed", "latency", "fast"),
            CapabilityDimension.COST: ("cost", "cheap", "budget"),
            CapabilityDimension.TOOL_USE: ("tool", "function", "api"),
            CapabilityDimension.MULTIMODAL: ("image", "video", "audio", "multimodal"),
            CapabilityDimension.MEMORY_CONTEXT: ("context", "memory", "long"),
            CapabilityDimension.RELIABILITY: ("reliable", "eval", "pass", "failure"),
            CapabilityDimension.CONTROLLABILITY: ("control", "instruction", "govern"),
        }
        return any(token in text for token in keywords[dimension])

    def _result_matches_dimension(self, dimension: CapabilityDimension, result: BenchmarkResult) -> bool:
        task_type = str(result.metadata.get("task_type", result.task_id)).lower()
        return dimension.value in task_type or any(token in task_type for token in dimension.value.split("_"))

    def _requires_model_copy(self, pattern: CapabilityPattern) -> bool:
        text = f"{pattern.repeatable_behavior} {pattern.transferable_part}".lower()
        return any(token in text for token in ("copy weights", "training data dump", "proprietary prompt"))


class WeaknessInversionEngine:
    """Turns failure modes into controls before artifacts can roll out."""

    def invert(self, profile: ModelCapabilityProfile, pattern: CapabilityPattern) -> List[WeaknessControl]:
        weaknesses = list(profile.weaknesses) + list(profile.failure_modes) + list(pattern.failure_modes)
        controls: List[WeaknessControl] = []
        for weakness in dict.fromkeys(weaknesses):
            controls.append(self._control_for(weakness))
        if not controls:
            controls.append(
                WeaknessControl(
                    weakness="unknown_failure_mode",
                    control_name="default_sandbox_and_monitor",
                    control_rule="validate in replay and simulation; rollback on negative lift or drift",
                    artifact_kind=AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT,
                    enforced_as_invariant=True,
                )
            )
        return controls

    def _control_for(self, weakness: str) -> WeaknessControl:
        lowered = weakness.lower()
        if "cost" in lowered or "expensive" in lowered:
            return WeaknessControl(weakness, "budget_cap", "deny execution when task budget is exceeded", AlphaAlgoArtifactKind.MODEL_SELECTION_POLICY)
        if "latency" in lowered or "slow" in lowered:
            return WeaknessControl(weakness, "latency_router", "route only blocker tasks to slow path", AlphaAlgoArtifactKind.ROUTING_RULE)
        if "halluc" in lowered or "fabricat" in lowered:
            return WeaknessControl(weakness, "citation_critic", "require source-backed claims and verifier challenge", AlphaAlgoArtifactKind.CRITIC_POLICY)
        if "context" in lowered or "memory" in lowered:
            return WeaknessControl(weakness, "context_compaction", "summarize old context into stable facts plus retained recent trace", AlphaAlgoArtifactKind.CONTEXT_STRATEGY)
        if "tool" in lowered:
            return WeaknessControl(weakness, "tool_output_check", "validate tool outputs before write or trade promotion", AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK)
        if "control" in lowered or "instruction" in lowered:
            return WeaknessControl(weakness, "governance_escalation", "escalate high-risk actions to governance gate", AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT, True)
        return WeaknessControl(weakness, "sandbox_first", "use replay and simulation before rollout", AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT, True)


class SkillCompiler:
    """Compiles transferable patterns into AlphaAlgo-native artifacts."""

    def compile(self, pattern: CapabilityPattern, controls: Sequence[WeaknessControl]) -> Optional[AlphaAlgoNativeArtifact]:
        artifact_kind = self._artifact_kind(pattern)
        if artifact_kind is None:
            return None
        domains = self._domains_for(pattern)
        artifact_id = _stable_id("artifact", pattern.pattern_id, artifact_kind.value)
        rollback = (
            "actual_lift_below_zero",
            "cost_exceeds_budget",
            "failure_rate_above_baseline",
            "interferes_with_risk_or_execution_module",
        )
        return AlphaAlgoNativeArtifact(
            artifact_id=artifact_id,
            kind=artifact_kind,
            name=f"alphaalgo_{artifact_kind.value}_{pattern.pattern_id[-8:]}",
            content={
                "source_model": pattern.source_model,
                "repeatable_behavior": pattern.repeatable_behavior,
                "transferable_part": pattern.transferable_part,
                "conditions": list(pattern.conditions),
                "failure_modes": list(pattern.failure_modes),
                "implementation": self._implementation_payload(artifact_kind, pattern),
            },
            source_pattern_id=pattern.pattern_id,
            valid_domains=domains,
            valid_agents=("research_agent", "engineering_agent", "trading_reasoner"),
            valid_tasks=pattern.benchmark_task_ids,
            budget_cap=max(0.25, min(10.0, abs(pattern.expected_lift) * 25.0)),
            rollback_triggers=rollback,
            controls=tuple(controls),
        )

    def _artifact_kind(self, pattern: CapabilityPattern) -> Optional[AlphaAlgoArtifactKind]:
        dimension = pattern.dimensions[0] if pattern.dimensions else None
        mapping = {
            CapabilityDimension.REASONING_DEPTH: AlphaAlgoArtifactKind.PROMPT_PROGRAM_TEMPLATE,
            CapabilityDimension.SPEED: AlphaAlgoArtifactKind.ROUTING_RULE,
            CapabilityDimension.COST: AlphaAlgoArtifactKind.MODEL_SELECTION_POLICY,
            CapabilityDimension.TOOL_USE: AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK,
            CapabilityDimension.MULTIMODAL: AlphaAlgoArtifactKind.SKILL_MODULE,
            CapabilityDimension.MEMORY_CONTEXT: AlphaAlgoArtifactKind.CONTEXT_STRATEGY,
            CapabilityDimension.RELIABILITY: AlphaAlgoArtifactKind.CRITIC_POLICY,
            CapabilityDimension.CONTROLLABILITY: AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT,
        }
        return mapping.get(dimension)

    def _domains_for(self, pattern: CapabilityPattern) -> Tuple[str, ...]:
        domains = []
        for task_id in pattern.benchmark_task_ids:
            prefix = task_id.split(":", 1)[0]
            if prefix:
                domains.append(prefix)
        return tuple(dict.fromkeys(domains or ["research", "engineering", "trading"]))

    def _implementation_payload(self, kind: AlphaAlgoArtifactKind, pattern: CapabilityPattern) -> Dict[str, Any]:
        if kind == AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK:
            return {"steps": ["plan", "batch_read_only_calls", "validate_outputs", "gate_writes"]}
        if kind == AlphaAlgoArtifactKind.CONTEXT_STRATEGY:
            return {"memory_shape": ["stable_facts", "recent_trace", "open_risks", "dropped_summary"]}
        if kind == AlphaAlgoArtifactKind.CRITIC_POLICY:
            return {"critics": ["objective_validator", "hidden_test_challenge", "adversarial_reviewer"]}
        if kind == AlphaAlgoArtifactKind.ROUTING_RULE:
            return {"rule": "route by task difficulty, latency budget, and risk class"}
        if kind == AlphaAlgoArtifactKind.MODEL_SELECTION_POLICY:
            return {"rule": "choose cheapest model that passes task capability threshold"}
        if kind == AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT:
            return {"invariant": "frontier-derived behavior cannot approve live trading or weaken safety rules"}
        return {"template": pattern.transferable_part}


class DistillationGovernanceGate:
    """Checks alignment, risk, architecture fit, and maintainability."""

    allowed_artifacts = {item for item in AlphaAlgoArtifactKind}

    def review(self, artifact: AlphaAlgoNativeArtifact, pattern: CapabilityPattern) -> GovernanceGateResult:
        issues: List[str] = []
        invariants: List[str] = [
            "no_model_weight_copying",
            "no_hidden_prompt_or_training_data_copying",
            "no_global_first_rollout",
            "no_live_trading_without_existing_governance",
        ]
        if artifact.kind not in self.allowed_artifacts:
            issues.append("artifact is not AlphaAlgo-native")
        if not artifact.valid_domains:
            issues.append("artifact lacks valid domain scope")
        if not artifact.rollback_triggers:
            issues.append("artifact lacks rollback triggers")
        if any("copy" in note.lower() and "excluded" not in note.lower() for note in pattern.non_transferable_notes):
            issues.append("pattern may rely on non-transferable implementation details")
        if artifact.budget_cap <= 0:
            issues.append("artifact lacks a budget cap")
        if artifact.kind == AlphaAlgoArtifactKind.FINE_TUNE_ADAPTER_OBJECTIVE:
            invariants.append("adapter objective must use owned or licensed data only")
        return GovernanceGateResult(
            accepted=not issues,
            issues=tuple(issues),
            required_invariants=tuple(invariants),
            notes=("frontier capability treated as behavior pattern, not copied model internals",),
        )


class SandboxValidator:
    """Validates artifacts in replay/simulation/offline/shadow before rollout."""

    def __init__(self, objective: Optional[AEANGlobalObjective] = None):
        self.objective = objective or AEANGlobalObjective()

    def validate(
        self,
        artifact: AlphaAlgoNativeArtifact,
        benchmark_results: Sequence[BenchmarkResult],
        modes: Sequence[ValidationMode] = (ValidationMode.REPLAY, ValidationMode.SIMULATION, ValidationMode.OFFLINE_EVAL),
    ) -> SandboxValidationReport:
        relevant = [result for result in benchmark_results if result.task_id in artifact.valid_tasks] or list(benchmark_results)
        lift = _avg([result.lift for result in relevant])
        stability = _avg([result.stability for result in relevant])
        cost_delta = _avg([result.cost for result in relevant]) - artifact.budget_cap
        side_effects = tuple(dict.fromkeys(side for result in relevant for side in result.side_effects))
        risk_side_effects = tuple(
            side
            for side in side_effects
            if "risk_limit" in side.lower() or "live_trade" in side.lower() or "governance" in side.lower()
        )
        compatible = not risk_side_effects if self.objective.require_governance_compatibility else True
        accepted = (
            lift > self.objective.min_long_term_lift
            and stability >= self.objective.min_stability
            and cost_delta <= self.objective.max_cost_delta
            and len(risk_side_effects) <= self.objective.allowed_risk_side_effects
            and compatible
            and len(modes) >= 2
        )
        return SandboxValidationReport(
            artifact_id=artifact.artifact_id,
            modes=tuple(modes),
            improvement_vs_baseline=round(lift, 4),
            stability=round(stability, 4),
            cost_delta=round(cost_delta, 4),
            side_effects=side_effects,
            compatible_with_global_objective=compatible,
            accepted=accepted,
            metrics={
                "lift": round(lift, 4),
                "stability": round(stability, 4),
                "cost_delta": round(cost_delta, 4),
                "risk_side_effect_count": len(risk_side_effects),
            },
        )


class RolloutManager:
    """Creates selective deployment plans only."""

    def plan(self, artifact: AlphaAlgoNativeArtifact, validation: SandboxValidationReport) -> Optional[RolloutPlan]:
        if not validation.accepted:
            return None
        if artifact.valid_tasks:
            scope = RolloutScope.TASK_SPECIFIC
        elif artifact.valid_agents:
            scope = RolloutScope.AGENT_SPECIFIC
        elif artifact.valid_domains:
            scope = RolloutScope.DOMAIN_SPECIFIC
        else:
            scope = RolloutScope.BUDGET_CAPPED
        return RolloutPlan(
            artifact_id=artifact.artifact_id,
            scope=scope,
            domains=artifact.valid_domains,
            agents=artifact.valid_agents,
            tasks=artifact.valid_tasks,
            budget_cap=artifact.budget_cap,
            canary_fraction=0.05,
            rollback_triggers=artifact.rollback_triggers,
            approved_for_live=False,
        )


class FrontierCapabilityLineageStore:
    """Stores extracted patterns, validation evidence, and lifecycle decisions."""

    def __init__(self):
        self.records: Dict[str, LineageRecord] = {}

    def add(self, record: LineageRecord) -> LineageRecord:
        self.records[record.lineage_id] = record
        return record

    def decide(self, actual_lift: float, drift: float, failure_patterns: Sequence[str]) -> RegistryDecision:
        if actual_lift > 0 and drift <= 0.10 and not failure_patterns:
            return RegistryDecision.KEEP
        if actual_lift > 0 and drift <= 0.25:
            return RegistryDecision.REVISE
        return RegistryDecision.KILL

    def list_records(self) -> List[LineageRecord]:
        return list(self.records.values())


class FrontierCapabilityDistillationEngine:
    """Full observe-profile-benchmark-extract-compile-validate-rollout loop."""

    def __init__(
        self,
        observer: Optional[FrontierObserver] = None,
        profiler: Optional[ModelProfiler] = None,
        harness: Optional[BenchmarkHarness] = None,
        extractor: Optional[CapabilityExtractor] = None,
        weakness_inverter: Optional[WeaknessInversionEngine] = None,
        compiler: Optional[SkillCompiler] = None,
        governance: Optional[DistillationGovernanceGate] = None,
        validator: Optional[SandboxValidator] = None,
        rollout_manager: Optional[RolloutManager] = None,
        lineage_store: Optional[FrontierCapabilityLineageStore] = None,
    ):
        self.observer = observer or FrontierObserver()
        self.profiler = profiler or ModelProfiler()
        self.harness = harness or BenchmarkHarness()
        self.extractor = extractor or CapabilityExtractor()
        self.weakness_inverter = weakness_inverter or WeaknessInversionEngine()
        self.compiler = compiler or SkillCompiler()
        self.governance = governance or DistillationGovernanceGate()
        self.validator = validator or SandboxValidator()
        self.rollout_manager = rollout_manager or RolloutManager()
        self.lineage_store = lineage_store or FrontierCapabilityLineageStore()

    def run(
        self,
        model_name: str,
        observations: Sequence[FrontierObservation],
        benchmark_tasks: Sequence[BenchmarkTask],
        benchmark_results: Sequence[BenchmarkResult],
    ) -> DistillationRunReport:
        self.observer.observe_many(observations)
        for task in benchmark_tasks:
            self.harness.add_task(task)
        for result in benchmark_results:
            self.harness.record_result(result)

        model_observations = self.observer.for_model(model_name)
        model_results = self.harness.for_model(model_name)
        profile = self.profiler.build_profile(model_name, model_observations, model_results)
        patterns = self.extractor.extract(profile, model_observations, model_results)

        artifacts: List[AlphaAlgoNativeArtifact] = []
        governance_results: List[GovernanceGateResult] = []
        validations: List[SandboxValidationReport] = []
        rollouts: List[RolloutPlan] = []
        lineage_records: List[LineageRecord] = []
        rejected_patterns: List[str] = []

        for pattern in patterns:
            controls = self.weakness_inverter.invert(profile, pattern)
            artifact = self.compiler.compile(pattern, controls)
            if artifact is None:
                rejected_patterns.append(f"{pattern.pattern_id}: not compilable to AlphaAlgo-native artifact")
                continue
            governance = self.governance.review(artifact, pattern)
            governance_results.append(governance)
            if not governance.accepted:
                rejected_patterns.append(f"{pattern.pattern_id}: governance rejected {governance.issues}")
                continue
            validation = self.validator.validate(artifact, model_results)
            validations.append(validation)
            rollout = self.rollout_manager.plan(artifact, validation)
            if rollout:
                rollouts.append(rollout)
            decision = self.lineage_store.decide(
                actual_lift=validation.improvement_vs_baseline,
                drift=0.0 if validation.accepted else 0.30,
                failure_patterns=validation.side_effects,
            )
            record = LineageRecord(
                lineage_id=_stable_id("lineage", model_name, pattern.pattern_id, artifact.artifact_id),
                source_model=model_name,
                observation_ids=pattern.evidence_observation_ids,
                pattern=pattern,
                artifact=artifact,
                governance=governance,
                validation=validation,
                rollout=rollout,
                decision=decision,
                actual_lift=validation.improvement_vs_baseline,
                drift=0.0 if validation.accepted else 0.30,
                failure_patterns=validation.side_effects,
            )
            self.lineage_store.add(record)
            artifacts.append(artifact)
            lineage_records.append(record)

        return DistillationRunReport(
            model_name=model_name,
            profile=profile,
            patterns=tuple(patterns),
            artifacts=tuple(artifacts),
            governance_results=tuple(governance_results),
            validation_reports=tuple(validations),
            rollout_plans=tuple(rollouts),
            lineage_records=tuple(lineage_records),
            rejected_patterns=tuple(rejected_patterns),
        )


class AISystemReverseEngineeringEngine:
    """Reverse engineers observable AI-system behavior into transferable evidence.

    It observes workflows, outputs, and claims; decomposes tool use,
    architecture pattern, and data flow; classifies real capability versus hype;
    extracts reusable components; and rejects low-value or dangerous ideas before
    the distillation compiler sees them.
    """

    tool_terms = ("tool", "api", "function", "search", "browser", "retrieval", "code", "sandbox", "benchmark")
    architecture_terms = ("agent", "router", "critic", "verifier", "memory", "context", "planner", "orchestrator")
    data_flow_terms = ("retrieve", "rank", "summarize", "compress", "validate", "execute", "observe", "feedback")
    hype_terms = ("magic", "guaranteed", "perfect", "sentient", "infinite", "always", "autonomous profit")
    danger_terms = (
        "bypass",
        "self approve",
        "self-approve",
        "credential",
        "broker",
        "risk limit",
        "unguarded write",
        "live deployment",
        "copy weights",
        "proprietary data",
    )

    def run(self, system_name: str, observations: Sequence[AISystemObservation]) -> AISystemReverseEngineeringReport:
        decompositions = tuple(self.decompose(observation) for observation in observations)
        assessments = tuple(
            self.classify(observation, decomposition)
            for observation, decomposition in zip(observations, decompositions)
        )
        components = tuple(
            component
            for observation, decomposition, assessment in zip(observations, decompositions, assessments)
            for component in self.extract(observation, decomposition, assessment)
        )
        rejected = tuple(
            idea
            for assessment in assessments
            for idea in assessment.rejected_ideas
        )
        frontier_observations = tuple(
            self.to_frontier_observation(system_name, observation, decomposition, assessment, component)
            for observation, decomposition, assessment in zip(observations, decompositions, assessments)
            for component in self.extract(observation, decomposition, assessment)
        )
        return AISystemReverseEngineeringReport(
            system_name=system_name,
            observations=tuple(observations),
            decompositions=decompositions,
            assessments=assessments,
            extracted_components=components,
            rejected_ideas=rejected,
            frontier_observations=frontier_observations,
        )

    def decompose(self, observation: AISystemObservation) -> AISystemDecomposition:
        text = self._text(observation)
        tools = self._extract_terms(text, self.tool_terms)
        architecture = self._extract_terms(text, self.architecture_terms)
        data_flow = self._extract_terms(text, self.data_flow_terms)
        controls = tuple(
            token
            for token in ("critic", "verifier", "sandbox", "approval", "rollback", "budget", "risk")
            if token in text
        )
        evidence_score = min(len(observation.evidence) * 0.15, 0.45)
        structure_score = min((len(tools) + len(architecture) + len(data_flow)) * 0.06, 0.45)
        confidence = round(min(1.0, 0.10 + evidence_score + structure_score + _avg(observation.metrics.values()) * 0.20), 4)
        return AISystemDecomposition(
            observation_id=observation.observation_id,
            tools_used=tools,
            architecture_patterns=architecture,
            data_flow=data_flow,
            control_surfaces=controls,
            claims=observation.claims,
            confidence=confidence,
        )

    def classify(
        self,
        observation: AISystemObservation,
        decomposition: AISystemDecomposition,
    ) -> ReverseEngineeringAssessment:
        text = self._text(observation)
        hype_score = min(sum(1 for token in self.hype_terms if token in text) * 0.25, 1.0)
        danger_score = min(sum(1 for token in self.danger_terms if token in text) * 0.25, 1.0)
        evidence_strength = min(len(observation.evidence) * 0.18 + _avg(observation.metrics.values()) * 0.40, 1.0)
        structure_strength = min(
            (len(decomposition.tools_used) + len(decomposition.architecture_patterns) + len(decomposition.data_flow)) * 0.08,
            1.0,
        )
        capability_score = round(min(1.0, evidence_strength + structure_strength - hype_score * 0.35), 4)

        rejected: List[str] = []
        if danger_score >= 0.50:
            classification = ReverseEngineeringClassification.DANGEROUS_POWER
            rejected.append("dangerous authority is not transferable into AEAN runtime")
        elif hype_score >= 0.50 and capability_score < 0.55:
            classification = ReverseEngineeringClassification.FAKE_HYPE
            rejected.append("claim is hype-heavy and evidence-light")
        elif capability_score < 0.40:
            classification = ReverseEngineeringClassification.LOW_VALUE
            rejected.append("low measurable value for AEAN global objective")
        elif decomposition.tools_used or decomposition.architecture_patterns or decomposition.data_flow:
            classification = ReverseEngineeringClassification.REUSABLE_COMPONENT
        else:
            classification = ReverseEngineeringClassification.REAL_CAPABILITY

        reusable = ()
        if classification in {ReverseEngineeringClassification.REAL_CAPABILITY, ReverseEngineeringClassification.REUSABLE_COMPONENT}:
            reusable = tuple(
                dict.fromkeys(
                    list(decomposition.tools_used)
                    + list(decomposition.architecture_patterns)
                    + list(decomposition.data_flow)
                    + list(decomposition.control_surfaces)
                )
            )

        return ReverseEngineeringAssessment(
            observation_id=observation.observation_id,
            classification=classification,
            capability_score=capability_score,
            hype_score=round(hype_score, 4),
            danger_score=round(danger_score, 4),
            reusable_components=reusable,
            rejected_ideas=tuple(rejected),
            rationale=self._rationale(classification),
        )

    def extract(
        self,
        observation: AISystemObservation,
        decomposition: AISystemDecomposition,
        assessment: ReverseEngineeringAssessment,
    ) -> List[ReusableComponentExtraction]:
        if assessment.classification not in {
            ReverseEngineeringClassification.REAL_CAPABILITY,
            ReverseEngineeringClassification.REUSABLE_COMPONENT,
        }:
            return []

        components: List[ReusableComponentExtraction] = []
        for component in assessment.reusable_components:
            kind = self._artifact_kind_for(component)
            if assessment.capability_score < 0.45:
                continue
            components.append(
                ReusableComponentExtraction(
                    component_id=_stable_id("component", observation.observation_id, component, kind.value),
                    source_observation_id=observation.observation_id,
                    component_name=component,
                    pattern=self._pattern_for(component, decomposition),
                    artifact_kind=kind,
                    value_score=assessment.capability_score,
                    risk_controls=self._risk_controls_for(component),
                )
            )
        return components

    def to_frontier_observation(
        self,
        system_name: str,
        observation: AISystemObservation,
        decomposition: AISystemDecomposition,
        assessment: ReverseEngineeringAssessment,
        component: ReusableComponentExtraction,
    ) -> FrontierObservation:
        dimension = self._dimension_for(component)
        observation_type = {
            AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK: FrontierObservationType.TOOL_USE_PATTERN,
            AlphaAlgoArtifactKind.CONTEXT_STRATEGY: FrontierObservationType.LONG_CONTEXT_BEHAVIOR,
            AlphaAlgoArtifactKind.CRITIC_POLICY: FrontierObservationType.EVAL_RESULT,
            AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT: FrontierObservationType.FAILURE_REPORT,
        }.get(component.artifact_kind, FrontierObservationType.USAGE_TRACE)
        return FrontierObservation(
            observation_id=_stable_id("revobs", observation.observation_id, component.component_id),
            model_name=system_name,
            observation_type=observation_type,
            summary=f"Reverse engineered {component.component_name}: {component.pattern}",
            observed_behavior=component.pattern,
            conditions=tuple(dict.fromkeys(decomposition.data_flow + decomposition.control_surfaces)),
            metrics={dimension.value: component.value_score},
            failure_modes=tuple(component.risk_controls),
            cost_estimate=float(observation.metrics.get("cost", 0.0)),
            latency_ms=float(observation.metrics.get("latency_ms", 0.0)),
        )

    def _text(self, observation: AISystemObservation) -> str:
        return " ".join(
            list(observation.workflow_steps)
            + list(observation.outputs)
            + list(observation.claims)
            + list(observation.evidence)
        ).lower()

    def _extract_terms(self, text: str, candidates: Sequence[str]) -> Tuple[str, ...]:
        return tuple(token for token in candidates if token in text)

    def _rationale(self, classification: ReverseEngineeringClassification) -> str:
        return {
            ReverseEngineeringClassification.REAL_CAPABILITY: "evidence supports real task-relevant capability",
            ReverseEngineeringClassification.REUSABLE_COMPONENT: "observable structure can be converted into AEAN-native components",
            ReverseEngineeringClassification.FAKE_HYPE: "claim lacks enough evidence or repeatable mechanism",
            ReverseEngineeringClassification.LOW_VALUE: "expected value is too small for risk and maintenance cost",
            ReverseEngineeringClassification.DANGEROUS_POWER: "behavior would weaken governance or runtime safety",
        }[classification]

    def _artifact_kind_for(self, component: str) -> AlphaAlgoArtifactKind:
        if component in {"tool", "api", "function", "search", "browser", "retrieval", "code", "sandbox", "benchmark"}:
            return AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK
        if component in {"memory", "context", "compress", "summarize"}:
            return AlphaAlgoArtifactKind.CONTEXT_STRATEGY
        if component in {"critic", "verifier", "validate"}:
            return AlphaAlgoArtifactKind.CRITIC_POLICY
        if component in {"router", "orchestrator", "agent", "planner"}:
            return AlphaAlgoArtifactKind.ROUTING_RULE
        if component in {"approval", "rollback", "budget", "risk"}:
            return AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT
        return AlphaAlgoArtifactKind.SKILL_MODULE

    def _pattern_for(self, component: str, decomposition: AISystemDecomposition) -> str:
        flow = " -> ".join(decomposition.data_flow or ("observe", "validate", "apply"))
        return f"{component} component used inside flow: {flow}"

    def _risk_controls_for(self, component: str) -> Tuple[str, ...]:
        controls = {
            AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK: ("validate tool output before action", "sandbox write operations"),
            AlphaAlgoArtifactKind.CONTEXT_STRATEGY: ("detect context drift", "retain audit trace"),
            AlphaAlgoArtifactKind.CRITIC_POLICY: ("require independent critic pass", "run hidden/adversarial checks"),
            AlphaAlgoArtifactKind.ROUTING_RULE: ("budget cap", "latency cap", "risk-class escalation"),
            AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT: ("governance approval required", "rollback trigger required"),
            AlphaAlgoArtifactKind.SKILL_MODULE: ("sandbox validation required",),
        }
        return controls[self._artifact_kind_for(component)]

    def _dimension_for(self, component: ReusableComponentExtraction) -> CapabilityDimension:
        mapping = {
            AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK: CapabilityDimension.TOOL_USE,
            AlphaAlgoArtifactKind.CONTEXT_STRATEGY: CapabilityDimension.MEMORY_CONTEXT,
            AlphaAlgoArtifactKind.CRITIC_POLICY: CapabilityDimension.RELIABILITY,
            AlphaAlgoArtifactKind.ROUTING_RULE: CapabilityDimension.SPEED,
            AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT: CapabilityDimension.CONTROLLABILITY,
            AlphaAlgoArtifactKind.SKILL_MODULE: CapabilityDimension.REASONING_DEPTH,
        }
        return mapping.get(component.artifact_kind, CapabilityDimension.REASONING_DEPTH)


class FrontierDangerNeutralizer:
    """Neutralizes dangerous parts of frontier capability before transfer."""

    critical_terms = (
        "live deployment bypass",
        "self approval",
        "self-approval",
        "risk limit",
        "credential",
        "broker",
        "copy weights",
        "training data dump",
        "proprietary prompt",
        "jailbreak",
        "prompt injection",
        "unguarded tool write",
    )
    high_terms = (
        "hallucination",
        "fabrication",
        "context drift",
        "unbounded autonomy",
        "tool output",
        "expensive",
        "slow",
    )

    def neutralize(
        self,
        report: DistillationRunReport,
    ) -> Tuple[Tuple[FrontierDangerNeutralization, ...], Tuple[str, ...]]:
        neutralizations: List[FrontierDangerNeutralization] = []
        killed_lineage_ids: List[str] = []

        for record in report.lineage_records:
            risks = self._risks_for(record)
            for risk in risks:
                neutralization = self._neutralization_for(risk)
                neutralizations.append(neutralization)
                if neutralization.blocked_transfer:
                    killed_lineage_ids.append(record.lineage_id)

            if not record.validation.compatible_with_global_objective:
                neutralizations.append(
                    FrontierDangerNeutralization(
                        source_risk="artifact side effect conflicts with AlphaAlgo global objective",
                        severity=DangerSeverity.CRITICAL,
                        neutralizing_control="kill artifact and require redesign in sandbox",
                        artifact_kind=AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT,
                        blocked_transfer=True,
                        rationale="frontier-derived behavior may not weaken survival, risk, or controllability",
                    )
                )
                killed_lineage_ids.append(record.lineage_id)

        return tuple(neutralizations), tuple(dict.fromkeys(killed_lineage_ids))

    def _risks_for(self, record: LineageRecord) -> List[str]:
        risks = list(record.pattern.failure_modes)
        risks.extend(record.failure_patterns)
        risks.extend(record.validation.side_effects)
        risks.extend(control.weakness for control in record.artifact.controls)
        return list(dict.fromkeys(risk for risk in risks if risk))

    def _neutralization_for(self, risk: str) -> FrontierDangerNeutralization:
        lowered = risk.lower()
        if any(term in lowered for term in self.critical_terms):
            return FrontierDangerNeutralization(
                source_risk=risk,
                severity=DangerSeverity.CRITICAL,
                neutralizing_control="block transfer; require governance invariant and sandbox redesign",
                artifact_kind=AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT,
                blocked_transfer=True,
                rationale="dangerous frontier power is not transferable into AlphaAlgo runtime authority",
            )
        if any(term in lowered for term in self.high_terms):
            return FrontierDangerNeutralization(
                source_risk=risk,
                severity=DangerSeverity.HIGH,
                neutralizing_control="wrap with critic, objective validation, and rollback triggers",
                artifact_kind=AlphaAlgoArtifactKind.CRITIC_POLICY,
                blocked_transfer=False,
                rationale="weakness becomes a controlled verifier or monitoring rule",
            )
        return FrontierDangerNeutralization(
            source_risk=risk,
            severity=DangerSeverity.MEDIUM,
            neutralizing_control="sandbox-first validation and drift monitoring",
            artifact_kind=AlphaAlgoArtifactKind.GOVERNANCE_INVARIANT,
            blocked_transfer=False,
            rationale="unknown frontier failure mode is contained before rollout",
        )


class FrontierArbitrageLedger:
    """Long-lived meta-intelligence ledger of frontier-to-AlphaAlgo advantage."""

    def __init__(self):
        self.reports: Dict[str, AlphaAlgoAdvantageReport] = {}

    def add(self, report: AlphaAlgoAdvantageReport) -> AlphaAlgoAdvantageReport:
        report_id = _stable_id("advantage", report.model_name, str(len(self.reports)), str(report.advantage_score))
        self.reports[report_id] = report
        return report

    def cumulative_advantage(self) -> float:
        return round(sum(report.advantage_score for report in self.reports.values()), 4)

    def killed_lineage_ids(self) -> Tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                lineage_id
                for report in self.reports.values()
                for lineage_id in report.killed_lineage_ids
            )
        )

    def list_reports(self) -> List[AlphaAlgoAdvantageReport]:
        return list(self.reports.values())


class FrontierMetaIntelligenceLayer:
    """Continuously arbitrages frontier capability into AlphaAlgo-native advantage.

    Frontier labs perform expensive capability discovery. This layer studies the
    observable outputs, extracts useful repeatable behavior, neutralizes dangerous
    behavior, and converts the remaining transfer into governed AlphaAlgo-native
    artifacts with lineage, validation, rollout caps, and rollback triggers.
    """

    def __init__(
        self,
        distillation_engine: Optional[FrontierCapabilityDistillationEngine] = None,
        reverse_engineer: Optional[AISystemReverseEngineeringEngine] = None,
        neutralizer: Optional[FrontierDangerNeutralizer] = None,
        ledger: Optional[FrontierArbitrageLedger] = None,
        min_advantage_score: float = 0.01,
    ):
        self.distillation_engine = distillation_engine or FrontierCapabilityDistillationEngine()
        self.reverse_engineer = reverse_engineer or AISystemReverseEngineeringEngine()
        self.neutralizer = neutralizer or FrontierDangerNeutralizer()
        self.ledger = ledger or FrontierArbitrageLedger()
        self.min_advantage_score = min_advantage_score

    def arbitrage_frontier(
        self,
        model_name: str,
        observations: Sequence[FrontierObservation],
        benchmark_tasks: Sequence[BenchmarkTask],
        benchmark_results: Sequence[BenchmarkResult],
        reverse_engineering: Optional[AISystemReverseEngineeringReport] = None,
    ) -> AlphaAlgoAdvantageReport:
        distillation = self.distillation_engine.run(model_name, observations, benchmark_tasks, benchmark_results)
        neutralized_dangers, killed_lineage_ids = self.neutralizer.neutralize(distillation)
        killed = set(killed_lineage_ids)
        active_records = [record for record in distillation.lineage_records if record.lineage_id not in killed]
        active_artifacts = tuple(record.artifact for record in active_records)
        active_rollouts = tuple(record.rollout for record in active_records if record.rollout is not None)
        advantage_score = self._advantage_score(distillation, active_records, neutralized_dangers)

        if advantage_score < self.min_advantage_score:
            killed.update(record.lineage_id for record in active_records)
            active_records = []
            active_artifacts = ()
            active_rollouts = ()
            advantage_score = 0.0

        opportunity = self._opportunity(
            model_name,
            observations,
            distillation,
            neutralized_dangers,
            advantage_score,
        )
        report = AlphaAlgoAdvantageReport(
            model_name=model_name,
            opportunity=opportunity,
            distillation=distillation,
            neutralized_dangers=neutralized_dangers,
            native_artifacts=active_artifacts,
            active_rollouts=active_rollouts,
            kept_lineage_ids=tuple(record.lineage_id for record in active_records),
            killed_lineage_ids=tuple(dict.fromkeys(killed)),
            advantage_score=round(advantage_score, 4),
            reverse_engineering=reverse_engineering,
            notes=(
                "frontier outputs are treated as external R&D signals",
                "useful behavior is converted into AlphaAlgo-native artifacts",
                "dangerous or non-transferable power is blocked or converted into controls",
            ),
        )
        self.ledger.add(report)
        return report

    def reverse_engineer_system(
        self,
        system_name: str,
        system_observations: Sequence[AISystemObservation],
    ) -> AISystemReverseEngineeringReport:
        return self.reverse_engineer.run(system_name, system_observations)

    def arbitrage_reverse_engineered_system(
        self,
        system_name: str,
        system_observations: Sequence[AISystemObservation],
        benchmark_tasks: Sequence[BenchmarkTask],
        benchmark_results: Sequence[BenchmarkResult],
    ) -> AlphaAlgoAdvantageReport:
        reverse_report = self.reverse_engineer_system(system_name, system_observations)
        return self.arbitrage_frontier(
            system_name,
            reverse_report.frontier_observations,
            benchmark_tasks,
            benchmark_results,
            reverse_engineering=reverse_report,
        )

    def run_once(
        self,
        model_name: str,
        observations: Sequence[FrontierObservation],
        benchmark_tasks: Sequence[BenchmarkTask],
        benchmark_results: Sequence[BenchmarkResult],
    ) -> AlphaAlgoAdvantageReport:
        return self.arbitrage_frontier(model_name, observations, benchmark_tasks, benchmark_results)

    async def run_continuous(
        self,
        feed_provider: Any,
        sleep_seconds: float = 300.0,
        max_cycles: Optional[int] = None,
    ) -> Tuple[AlphaAlgoAdvantageReport, ...]:
        """Run bounded or continuous frontier-arbitrage cycles.

        feed_provider returns an iterable of dictionaries with model_name,
        observations, benchmark_tasks, and benchmark_results. max_cycles keeps
        tests and sandbox runs bounded; production schedulers can pass None.
        """
        reports: List[AlphaAlgoAdvantageReport] = []
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            batch = feed_provider()
            if hasattr(batch, "__await__"):
                batch = await batch
            for item in batch:
                if "system_observations" in item:
                    reports.append(
                        self.arbitrage_reverse_engineered_system(
                            item["model_name"],
                            item.get("system_observations", ()),
                            item.get("benchmark_tasks", ()),
                            item.get("benchmark_results", ()),
                        )
                    )
                else:
                    reports.append(
                        self.arbitrage_frontier(
                            item["model_name"],
                            item.get("observations", ()),
                            item.get("benchmark_tasks", ()),
                            item.get("benchmark_results", ()),
                        )
                    )
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                await asyncio.sleep(sleep_seconds)
        return tuple(reports)

    def monitor_update(
        self,
        report: AlphaAlgoAdvantageReport,
        actual_lift: float,
        drift: float,
        failure_patterns: Sequence[str],
    ) -> RegistryDecision:
        decision = self.distillation_engine.lineage_store.decide(actual_lift, drift, failure_patterns)
        if decision == RegistryDecision.KILL:
            return RegistryDecision.KILL
        if actual_lift < report.advantage_score * 0.5 or drift > 0.10 or failure_patterns:
            return RegistryDecision.REVISE
        return RegistryDecision.KEEP

    def _advantage_score(
        self,
        distillation: DistillationRunReport,
        active_records: Sequence[LineageRecord],
        neutralizations: Sequence[FrontierDangerNeutralization],
    ) -> float:
        lift = sum(max(record.actual_lift, 0.0) for record in active_records)
        artifact_bonus = len(active_records) * 0.02
        cost_penalty = sum(max(record.validation.cost_delta, 0.0) for record in active_records)
        danger_penalty = sum(
            0.04
            for item in neutralizations
            if item.severity in {DangerSeverity.HIGH, DangerSeverity.CRITICAL} and not item.blocked_transfer
        )
        rejected_penalty = len(distillation.rejected_patterns) * 0.01
        return max(0.0, lift + artifact_bonus - cost_penalty - danger_penalty - rejected_penalty)

    def _opportunity(
        self,
        model_name: str,
        observations: Sequence[FrontierObservation],
        distillation: DistillationRunReport,
        neutralizations: Sequence[FrontierDangerNeutralization],
        advantage_score: float,
    ) -> FrontierArbitrageOpportunity:
        useful_output_score = round(
            _avg([score for score in distillation.profile.dimension_scores.values() if score >= 0.60]),
            4,
        )
        dangerous_output_score = round(
            _avg(
                [
                    1.0 if item.severity == DangerSeverity.CRITICAL else 0.7 if item.severity == DangerSeverity.HIGH else 0.35
                    for item in neutralizations
                ]
            ),
            4,
        )
        transferable_value = round(sum(max(record.actual_lift, 0.0) for record in distillation.lineage_records), 4)
        return FrontierArbitrageOpportunity(
            model_name=model_name,
            studied_outputs=tuple(item.observation_id for item in observations),
            useful_output_score=useful_output_score,
            dangerous_output_score=dangerous_output_score,
            transferable_value=transferable_value,
            expected_alphaalgo_advantage=round(advantage_score, 4),
            notes=(
                "frontier capability discovery is arbitraged through observable outputs only",
                "non-transferable internals are excluded",
            ),
        )


def _avg(values: Iterable[float]) -> float:
    items = [float(value) for value in values]
    if not items:
        return 0.0
    return sum(items) / len(items)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


__all__ = [
    "AlphaAlgoArtifactKind",
    "AlphaAlgoNativeArtifact",
    "AEANGlobalObjective",
    "AISystemDecomposition",
    "AISystemObservation",
    "AISystemReverseEngineeringEngine",
    "AISystemReverseEngineeringReport",
    "BenchmarkHarness",
    "BenchmarkResult",
    "BenchmarkTask",
    "CapabilityDimension",
    "CapabilityExtractor",
    "CapabilityPattern",
    "CapabilityPatternType",
    "DistillationGovernanceGate",
    "DistillationRunReport",
    "AlphaAlgoAdvantageReport",
    "DangerSeverity",
    "FrontierCapabilityDistillationEngine",
    "FrontierCapabilityLineageStore",
    "FrontierArbitrageLedger",
    "FrontierArbitrageOpportunity",
    "FrontierDangerNeutralization",
    "FrontierDangerNeutralizer",
    "FrontierMetaIntelligenceLayer",
    "FrontierObservation",
    "FrontierObservationType",
    "FrontierObserver",
    "GovernanceGateResult",
    "LineageRecord",
    "ModelCapabilityProfile",
    "ModelProfiler",
    "RegistryDecision",
    "ReusableComponentExtraction",
    "ReverseEngineeringAssessment",
    "ReverseEngineeringClassification",
    "ReverseEngineeringSignalType",
    "RolloutManager",
    "RolloutPlan",
    "RolloutScope",
    "SandboxValidationReport",
    "SandboxValidator",
    "SkillCompiler",
    "ValidationMode",
    "WeaknessControl",
    "WeaknessInversionEngine",
]
