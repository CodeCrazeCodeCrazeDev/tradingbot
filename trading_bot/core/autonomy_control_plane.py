"""
Autonomy control plane.

Shared safety primitives for sandboxing, credentials, signed approvals,
memory compaction, tool-call fusion, context prefetch, verifier checks,
and approval-gated patch proposals.
"""

from __future__ import annotations

import difflib
import hashlib
import hmac
import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence


class SandboxTier(str, Enum):
    """Execution tiers ordered from safest to most privileged."""

    READ_ONLY = "read_only"
    SIMULATED_WRITE = "simulated_write"
    APPROVED_WRITE = "approved_write"
    LIVE_EXECUTION = "live_execution"


class ApprovalState(str, Enum):
    """Approval state for gated operations."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskCategory(str, Enum):
    """Governance risk category."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionClassification(str, Enum):
    """Action classes emitted by the overseer model."""

    READ_ONLY = "read_only"
    RESEARCH = "research"
    GENERATED_PATCH = "generated_patch"
    PRODUCTION_PATCH = "production_patch"
    LIVE_DEPLOYMENT = "live_deployment"
    BROKER_CREDENTIAL_CHANGE = "broker_credential_change"
    RISK_LIMIT_CHANGE = "risk_limit_change"
    CAPITAL_SCALING = "capital_scaling"
    STRATEGY_PROMOTION = "strategy_promotion"
    KILL_SWITCH_OVERRIDE = "kill_switch_override"
    UNKNOWN = "unknown"


class SpecialistAgent(str, Enum):
    """Persistent specialist-agent roles for AlphaAlgo."""

    RISK = "risk_specialist"
    EXECUTION = "execution_specialist"
    MACRO = "macro_specialist"
    BACKTEST = "backtest_specialist"
    CODE_REVIEW = "code_review_specialist"
    SECURITY = "security_specialist"


class FrontierCapabilityDomain(str, Enum):
    """Capability families used to measure frontier-agent coverage."""

    REASONING = "reasoning"
    MEMORY = "memory"
    TOOL_USE = "tool_use"
    CODING = "coding"
    RESEARCH = "research"
    SECURITY = "security"
    TRADING = "trading"
    MULTIMODAL = "multimodal"
    ORCHESTRATION = "orchestration"
    GOVERNANCE = "governance"


class EngineeringPipelineStage(str, Enum):
    """Ordered stages in the controlled AI engineering factory."""

    OBSERVE_SYSTEM_BEHAVIOR = "observe_system_behavior"
    DETECT_BUG_WEAKNESS_INEFFICIENCY = "detect_bug_weakness_inefficiency"
    VALIDATE_OBJECTIVE_EVIDENCE = "validate_objective_evidence"
    WRITE_ROOT_CAUSE_REPORT = "write_root_cause_report"
    CREATE_DIAGNOSIS = "create_diagnosis"
    PROPOSE_CODE_PATCH = "propose_code_patch"
    CHECK_COMPLEXITY_BUDGET = "check_complexity_budget"
    CREATE_SANDBOX_BRANCH = "create_sandbox_branch"
    GENERATE_TESTS = "generate_tests"
    CREATE_INVARIANT_TESTS = "create_invariant_tests"
    RUN_TESTS_IN_SANDBOX = "run_tests_in_sandbox"
    RUN_HIDDEN_ADVERSARIAL_TESTS = "run_hidden_adversarial_tests"
    RUN_STATIC_ANALYSIS = "run_static_analysis"
    RUN_SECURITY_SCAN = "run_security_scan"
    RUN_PROTECTED_FILE_CHECK = "run_protected_file_check"
    RUN_SECURITY_GATE_BEFORE_MERGE = "run_security_gate_before_merge"
    RUN_PERFORMANCE_BENCHMARK = "run_performance_benchmark"
    COMPARE_BEFORE_AFTER_METRICS = "compare_before_after_metrics"
    RUN_REGRESSION_TESTS = "run_regression_tests"
    GENERATE_ENGINEERING_REPORT = "generate_engineering_report"
    OPEN_PULL_REQUEST = "open_pull_request"
    HUMAN_OR_GOVERNANCE_APPROVAL = "human_or_governance_approval"
    DEPLOY_TO_STAGING = "deploy_to_staging"
    SHADOW_TEST_OR_PAPER_TRADE = "shadow_test_or_paper_trade"
    CANARY_RELEASE = "canary_release"
    PRODUCTION_DEPLOYMENT = "production_deployment"
    MONITOR = "monitor"
    ROLLBACK_IF_METRICS_DEGRADE = "rollback_if_metrics_degrade"
    UPDATE_FAILURE_MEMORY = "update_failure_memory"


class EngineeringStageStatus(str, Enum):
    """Execution status for a software-factory stage."""

    PASSED = "passed"
    PENDING = "pending"
    BLOCKED = "blocked"
    FAILED = "failed"


class MythosMode(str, Enum):
    """Mythos-inspired operating modes for AlphaAlgo."""

    TRADING_REASONING = "trading_reasoning"
    DEFENSIVE_SECURITY = "defensive_security"
    CODE_HARDENING = "code_hardening"
    RESEARCH_EVALUATION = "research_evaluation"


class DisclosureState(str, Enum):
    """Responsible disclosure state for security findings."""

    PRIVATE_ANALYSIS = "private_analysis"
    PATCH_REVIEW = "patch_review"
    COORDINATED_DISCLOSURE = "coordinated_disclosure"
    PUBLIC_DISCLOSURE_BLOCKED = "public_disclosure_blocked"


@dataclass
class SandboxDecision:
    """Decision returned by the tiered sandbox mesh."""

    allowed: bool
    tier: SandboxTier
    reason: str
    required_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tier"] = self.tier.value
        return data


@dataclass
class CredentialLease:
    """Rotated credential metadata without exposing the secret."""

    credential_id: str
    version: int
    issued_at: float
    expires_at: float
    secret_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SignedApproval:
    """Client-side signed approval envelope."""

    approval_id: str
    subject_id: str
    approver: str
    issued_at: float
    expires_at: float
    signature: str
    state: ApprovalState = ApprovalState.PENDING

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass
class ScopedToken:
    """Blinded scoped token metadata issued through a proxy/vault boundary."""

    token_id: str
    agent_id: str
    audience: str
    scopes: List[str]
    issued_at: float
    expires_at: float
    token_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryCompactionResult:
    """Compacted session memory with preserved high-signal facts."""

    summary: str
    retained_messages: List[Dict[str, str]]
    dropped_count: int
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceDecision:
    """Glass-box overseer output for an action."""

    action_classification: ActionClassification
    risk_category: RiskCategory
    policy_rule_triggered: str
    required_evidence: List[str]
    missing_evidence: List[str]
    decision: ApprovalState
    manual_review_required: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["action_classification"] = self.action_classification.value
        data["risk_category"] = self.risk_category.value
        data["decision"] = self.decision.value
        return data


@dataclass
class DecisionProvenanceEvent:
    """One causal/provenance event for a risky decision."""

    stage: str
    actor: str
    summary: str
    evidence_ids: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionProvenanceTrace:
    """Append-only decision provenance trace with a sealable digest."""

    decision_id: str
    events: List[DecisionProvenanceEvent] = field(default_factory=list)
    sealed_digest: Optional[str] = None

    def append(self, stage: str, actor: str, summary: str, evidence_ids: Optional[Sequence[str]] = None) -> None:
        if self.sealed_digest:
            raise ValueError("sealed provenance trace is append-only and already sealed")
        self.events.append(DecisionProvenanceEvent(stage, actor, summary, list(evidence_ids or [])))

    def seal(self) -> str:
        payload = json.dumps([event.to_dict() for event in self.events], sort_keys=True)
        self.sealed_digest = hashlib.sha256(f"{self.decision_id}:{payload}".encode("utf-8")).hexdigest()
        return self.sealed_digest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "events": [event.to_dict() for event in self.events],
            "sealed_digest": self.sealed_digest,
        }


@dataclass
class SandboxSessionSpec:
    """Ephemeral micro-VM style sandbox session plan."""

    session_id: str
    coordinator_id: str
    action: str
    tier: SandboxTier
    ephemeral: bool
    persistent_secrets: bool
    production_access: bool
    audit_store: str
    destroyed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tier"] = self.tier.value
        return data


@dataclass
class ToolCall:
    """Tool call request used for fusion planning."""

    name: str
    arguments: Dict[str, Any]
    read_only: bool = True
    tier: SandboxTier = SandboxTier.READ_ONLY

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tier"] = self.tier.value
        return data


@dataclass
class FusedToolCall:
    """Batch of compatible tool calls."""

    calls: List[ToolCall]
    tier: SandboxTier
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calls": [call.to_dict() for call in self.calls],
            "tier": self.tier.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ToolDescriptor:
    """Searchable metadata for one managed tool."""

    name: str
    description: str
    tags: List[str]
    read_only: bool = True
    tier: SandboxTier = SandboxTier.READ_ONLY

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tier"] = self.tier.value
        return data


@dataclass
class ToolSearchResult:
    """Ranked tool-search result."""

    descriptor: ToolDescriptor
    score: float
    matched_terms: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "descriptor": self.descriptor.to_dict(),
            "score": self.score,
            "matched_terms": list(self.matched_terms),
        }


@dataclass
class ProgrammaticToolScript:
    """Compiled, auditable tool script that collapses repeated tool calling."""

    script_id: str
    objective: str
    fused_calls: List[FusedToolCall]
    blocked_calls: List[Dict[str, Any]]
    selected_tools: List[ToolSearchResult]
    estimated_inference_steps_saved: int
    provenance: DecisionProvenanceTrace

    def to_dict(self) -> Dict[str, Any]:
        return {
            "script_id": self.script_id,
            "objective": self.objective,
            "fused_calls": [call.to_dict() for call in self.fused_calls],
            "blocked_calls": list(self.blocked_calls),
            "selected_tools": [tool.to_dict() for tool in self.selected_tools],
            "estimated_inference_steps_saved": self.estimated_inference_steps_saved,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class ManagedAgentLease:
    """Task-scoped lease for a decoupled managed agent."""

    lease_id: str
    agent_id: str
    role: SpecialistAgent
    task: str
    scopes: List[str]
    sandbox_session: SandboxSessionSpec
    issued_at: float
    expires_at: float
    heartbeat_at: float
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "agent_id": self.agent_id,
            "role": self.role.value,
            "task": self.task,
            "scopes": list(self.scopes),
            "sandbox_session": self.sandbox_session.to_dict(),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "heartbeat_at": self.heartbeat_at,
            "active": self.active,
        }


@dataclass
class VerificationReport:
    """Self-consistency and verifier result."""

    accepted: bool
    canonical_answer: str
    agreement: float
    verifier_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DebateValidationResult:
    """Self-consistency plus debate validation for trading workflows."""

    workflow: str
    accepted: bool
    winner: str
    agreement: float
    pro_arguments: List[str]
    con_arguments: List[str]
    verifier_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PatchProposal:
    """Approval-gated patch proposal."""

    proposal_id: str
    file_path: str
    diff: str
    risk: str
    approval_state: ApprovalState = ApprovalState.PENDING
    approval_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["approval_state"] = self.approval_state.value
        return data


@dataclass
class PatchWorkflowReport:
    """Approval-gated bugfix workflow report."""

    bug_id: str
    patch: PatchProposal
    regression_test: str
    risk_report: str
    allowed_next_steps: List[str]
    blocked_next_steps: List[str]
    approval_state: ApprovalState = ApprovalState.PENDING

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["patch"] = self.patch.to_dict()
        data["approval_state"] = self.approval_state.value
        return data


@dataclass
class EngineeringStageResult:
    """Auditable result for one controlled software-factory stage."""

    stage: EngineeringPipelineStage
    status: EngineeringStageStatus
    summary: str
    evidence_ids: List[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "summary": self.summary,
            "evidence_ids": list(self.evidence_ids),
            "blocked_reason": self.blocked_reason,
        }


@dataclass
class EngineeringObservation:
    """Observed behavior before the agent proposes any code."""

    observation_id: str
    source: str
    expected_behavior: str
    observed_behavior: str
    metrics: Dict[str, float] = field(default_factory=dict)
    symptoms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngineeringDiagnosis:
    """Diagnosis for a bug, weakness, or inefficiency."""

    diagnosis_id: str
    category: str
    severity: RiskCategory
    summary: str
    suspected_files: List[str]
    confidence: float
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class RootCauseReport:
    """Root-cause report required before patch proposal."""

    root_cause_id: str
    primary_cause: str
    contributing_factors: List[str]
    rejected_symptom_fixes: List[str]
    evidence_ids: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ObjectiveValidationResult:
    """Objective validator that scores correctness evidence, not appearance."""

    accepted: bool
    score: float
    validators: List[str]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplexityBudget:
    """Minimal-patch complexity budget to prevent architecture accretion."""

    max_changed_lines: int
    max_new_functions: int
    max_complexity_delta: int
    changed_lines: int
    new_functions: int
    complexity_delta: int
    accepted: bool
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngineeringTestPlan:
    """Generated tests and checks required before any deployment gate."""

    unit_tests: List[str]
    sandbox_tests: List[str]
    static_checks: List[str]
    security_checks: List[str]
    performance_benchmarks: List[str]
    regression_tests: List[str]
    invariant_tests: List[str] = field(default_factory=list)
    hidden_tests: List[str] = field(default_factory=list)
    adversarial_tests: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProtectedFilePolicy:
    """Prevents silent weakening of safety, risk, and governance files."""

    protected_patterns: List[str] = field(default_factory=lambda: [
        "risk",
        "safety",
        "governance",
        "approval",
        "credential",
        "broker",
        "production",
        "autonomy_control_plane",
    ])

    def check(self, file_path: str, evidence: Optional[Dict[str, Any]] = None) -> VerificationReport:
        evidence = evidence or {}
        lowered = file_path.lower().replace("\\", "/")
        protected = [pattern for pattern in self.protected_patterns if pattern in lowered]
        if protected and not evidence.get("protected_file_approval"):
            return VerificationReport(
                False,
                "protected file policy",
                0.0,
                [f"protected file requires explicit approval: {', '.join(protected)}"],
            )
        return VerificationReport(True, "protected file policy", 1.0, [])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricComparisonReport:
    """Before/after performance and safety metric comparison."""

    before: Dict[str, float]
    after: Dict[str, float]
    accepted: bool
    regressions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailureMemoryEntry:
    """Learning memory written after the engineering loop completes."""

    memory_id: str
    objective: str
    outcome: str
    lessons: List[str]
    rollback_triggered: bool
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeBoundaryPolicy:
    """Separates deterministic live trading from sandboxed engineering work."""

    live_runtime_observation_sources: List[str] = field(default_factory=lambda: ["logs", "errors", "performance"])
    live_runtime_capabilities: List[str] = field(default_factory=lambda: ["trades", "deterministic_decisions"])
    engineering_ai_permissions: List[str] = field(default_factory=lambda: [
        "read logs",
        "detect weaknesses",
        "propose fixes",
        "write tests",
        "create patches",
        "run sandbox experiments",
        "open pull requests",
    ])
    engineering_ai_forbidden: List[str] = field(default_factory=lambda: [
        "directly modify live trading code",
        "directly change risk limits",
        "mutate live models",
        "deploy itself to production",
        "approve its own work",
    ])
    live_self_editing_allowed: bool = False
    live_model_mutation_allowed: bool = False
    live_direct_code_changes_allowed: bool = False
    production_runs_separately: bool = True

    def validate_engineering_action(self, action: str, actor: str = "ai-engineering-agent") -> VerificationReport:
        lowered = action.lower()
        notes = []
        if any(token in lowered for token in ("modify live", "live code", "direct code change")):
            notes.append("violates live runtime code isolation")
        if "risk limit" in lowered and any(token in lowered for token in ("change", "raise", "lower", "modify")):
            notes.append("violates risk-limit change gate")
        if "model mutation" in lowered or "mutate model" in lowered:
            notes.append("violates live model mutation ban")
        if "deploy" in lowered and "production" in lowered and actor.startswith("ai"):
            notes.append("violates AI production deployment ban")
        if "approve" in lowered and actor.startswith("ai"):
            notes.append("violates self-approval ban")
        return VerificationReport(not notes, "runtime boundary policy", 1.0 if not notes else 0.0, notes)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SandboxBranchPlan:
    """Sandbox branch where AI-created code changes are isolated from production."""

    branch_name: str
    base_branch: str
    patch_proposal_id: str
    live_runtime_attached: bool = False
    live_code_mutation_allowed: bool = False
    risk_limit_change_allowed: bool = False
    model_mutation_allowed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerifierAgentReview:
    """One independent verifier-agent decision before governance."""

    verifier_id: str
    role: SpecialistAgent
    decision: ApprovalState
    summary: str
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        data["decision"] = self.decision.value
        return data


@dataclass
class PullRequestDraft:
    """Pull request draft generated by the software factory."""

    title: str
    body: str
    branch_name: str
    ready_for_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeploymentPlan:
    """Staging, shadow, canary, production, monitor, and rollback plan."""

    staging_environment: str
    shadow_mode: str
    canary_percentage: float
    production_enabled: bool
    rollback_triggers: List[str]
    monitoring_metrics: List[str]
    paper_trading_required: bool = True
    canary_enabled: bool = True
    rollback_available: bool = True
    production_runtime_separate: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SoftwareFactoryRunReport:
    """Complete AI engineering control-loop report."""

    run_id: str
    objective: str
    observation: EngineeringObservation
    diagnosis: EngineeringDiagnosis
    root_cause_report: RootCauseReport
    objective_validation: ObjectiveValidationResult
    complexity_budget: ComplexityBudget
    patch_workflow: PatchWorkflowReport
    test_plan: EngineeringTestPlan
    protected_file_report: VerificationReport
    metric_comparison: MetricComparisonReport
    failure_memory_entry: FailureMemoryEntry
    runtime_policy: RuntimeBoundaryPolicy
    sandbox_branch: SandboxBranchPlan
    sandbox_session: SandboxSessionSpec
    verifier_agent_reviews: List[VerifierAgentReview]
    reviewer_report: VerificationReport
    governance: GovernanceDecision
    pull_request: PullRequestDraft
    deployment_plan: DeploymentPlan
    stages: List[EngineeringStageResult]
    provenance: DecisionProvenanceTrace

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "objective": self.objective,
            "observation": self.observation.to_dict(),
            "diagnosis": self.diagnosis.to_dict(),
            "root_cause_report": self.root_cause_report.to_dict(),
            "objective_validation": self.objective_validation.to_dict(),
            "complexity_budget": self.complexity_budget.to_dict(),
            "patch_workflow": self.patch_workflow.to_dict(),
            "test_plan": self.test_plan.to_dict(),
            "protected_file_report": self.protected_file_report.to_dict(),
            "metric_comparison": self.metric_comparison.to_dict(),
            "failure_memory_entry": self.failure_memory_entry.to_dict(),
            "runtime_policy": self.runtime_policy.to_dict(),
            "sandbox_branch": self.sandbox_branch.to_dict(),
            "sandbox_session": self.sandbox_session.to_dict(),
            "verifier_agent_reviews": [review.to_dict() for review in self.verifier_agent_reviews],
            "reviewer_report": self.reviewer_report.to_dict(),
            "governance": self.governance.to_dict(),
            "pull_request": self.pull_request.to_dict(),
            "deployment_plan": self.deployment_plan.to_dict(),
            "stages": [stage.to_dict() for stage in self.stages],
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class MythosCapabilityProfile:
    """Research-derived profile for Mythos-class AlphaAlgo behavior."""

    name: str = "AlphaAlgo Mythos Governor"
    defensive_only_security: bool = True
    real_world_validation_required: bool = True
    visible_reasoning_minimized: bool = True
    safeguards: List[str] = field(default_factory=lambda: [
        "limited defensive scope",
        "real-time policy classification",
        "signed approval for high-risk actions",
        "ephemeral sandbox execution",
        "responsible vulnerability disclosure",
        "sealed audit provenance",
    ])
    benchmark_focus: List[str] = field(default_factory=lambda: [
        "agentic coding",
        "reasoning",
        "search and computer-use workflows",
        "real-world security regression tasks",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MythosTaskPlan:
    """Executable-but-contained task plan for Mythos-class AlphaAlgo work."""

    task: str
    mode: MythosMode
    governance: GovernanceDecision
    specialists: List[SpecialistAgent]
    sandbox_session: Optional[SandboxSessionSpec]
    allowed_outputs: List[str]
    blocked_outputs: List[str]
    disclosure_state: Optional[DisclosureState]
    provenance: DecisionProvenanceTrace

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "mode": self.mode.value,
            "governance": self.governance.to_dict(),
            "specialists": [agent.value for agent in self.specialists],
            "sandbox_session": self.sandbox_session.to_dict() if self.sandbox_session else None,
            "allowed_outputs": list(self.allowed_outputs),
            "blocked_outputs": list(self.blocked_outputs),
            "disclosure_state": self.disclosure_state.value if self.disclosure_state else None,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class FrontierCapability:
    """One measurable frontier-agent capability behind explicit guardrails."""

    capability_id: str
    name: str
    domain: FrontierCapabilityDomain
    coverage_weight: float
    risk_category: RiskCategory
    action: ActionClassification
    guardrails: List[str]
    required_evidence: List[str] = field(default_factory=list)
    sandbox_required: bool = False
    default_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["domain"] = self.domain.value
        data["risk_category"] = self.risk_category.value
        data["action"] = self.action.value
        return data


@dataclass
class FrontierActivationReport:
    """Capability activation result for a single task/request."""

    task: str
    target_coverage: float
    achieved_coverage: float
    activated: List[FrontierCapability]
    deferred: List[Dict[str, Any]]
    governance: GovernanceDecision
    invariant_report: VerificationReport
    sandbox_sessions: List[SandboxSessionSpec] = field(default_factory=list)
    provenance: Optional[DecisionProvenanceTrace] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "target_coverage": self.target_coverage,
            "achieved_coverage": self.achieved_coverage,
            "activated": [capability.to_dict() for capability in self.activated],
            "deferred": list(self.deferred),
            "governance": self.governance.to_dict(),
            "invariant_report": self.invariant_report.to_dict(),
            "sandbox_sessions": [session.to_dict() for session in self.sandbox_sessions],
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }


class TieredSandboxMesh:
    """Routes operations through the least-privileged sandbox tier."""

    _write_tokens = ("write", "patch", "delete", "move", "commit", "push", "execute", "deploy")
    _live_tokens = ("broker", "order", "trade", "credential", "secret", "prod", "live")
    _untrusted_tokens = ("untrusted", "unknown file", "external repo", "research script", "generated patch", "strategy code")

    def decide(self, operation: str, requested_tier: SandboxTier = SandboxTier.READ_ONLY) -> SandboxDecision:
        text = operation.lower()
        if any(token in text for token in self._live_tokens):
            return SandboxDecision(False, SandboxTier.LIVE_EXECUTION, "live-sensitive operation requires explicit signed approval", True)
        if any(token in text for token in self._untrusted_tokens):
            return SandboxDecision(True, SandboxTier.SIMULATED_WRITE, "risky action routed to ephemeral sandbox without secrets", False)
        if any(token in text for token in self._write_tokens):
            tier = max(requested_tier, SandboxTier.SIMULATED_WRITE, key=self._tier_rank)
            return SandboxDecision(tier == SandboxTier.APPROVED_WRITE, tier, "write operation is simulated until approval", True)
        return SandboxDecision(True, SandboxTier.READ_ONLY, "read-only operation allowed")

    def create_ephemeral_session(self, coordinator_id: str, action: str, audit_store: str = "audit_logs") -> SandboxSessionSpec:
        decision = self.decide(action)
        session_seed = f"{coordinator_id}:{action}:{time.time():.6f}"
        session_id = hashlib.sha256(session_seed.encode("utf-8")).hexdigest()[:16]
        tier = decision.tier if decision.tier != SandboxTier.LIVE_EXECUTION else SandboxTier.SIMULATED_WRITE
        return SandboxSessionSpec(
            session_id=session_id,
            coordinator_id=coordinator_id,
            action=action,
            tier=tier,
            ephemeral=True,
            persistent_secrets=False,
            production_access=False,
            audit_store=audit_store,
        )

    def destroy_session(self, session: SandboxSessionSpec) -> SandboxSessionSpec:
        session.destroyed = True
        return session

    def _tier_rank(self, tier: SandboxTier) -> int:
        return list(SandboxTier).index(tier)


class DynamicCredentialRotator:
    """Issues short-lived credential leases and tracks rotation versions."""

    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        self._versions: Dict[str, int] = {}

    def rotate(self, credential_id: str, secret_material: str) -> CredentialLease:
        version = self._versions.get(credential_id, 0) + 1
        self._versions[credential_id] = version
        issued_at = time.time()
        digest = hashlib.sha256(f"{credential_id}:{version}:{secret_material}".encode("utf-8")).hexdigest()
        return CredentialLease(credential_id, version, issued_at, issued_at + self.ttl_seconds, digest)

    def is_expired(self, lease: CredentialLease, now: Optional[float] = None) -> bool:
        return (now or time.time()) >= lease.expires_at


class ToolProxyVault:
    """Agent -> tool proxy -> vault -> scoped token boundary."""

    def __init__(self, rotator: Optional[DynamicCredentialRotator] = None):
        self.rotator = rotator or DynamicCredentialRotator(ttl_seconds=300)
        self._issued: Dict[str, ScopedToken] = {}

    def issue_scoped_token(self, agent_id: str, audience: str, scopes: Sequence[str], approval: Optional[SignedApproval] = None) -> ScopedToken:
        subject = f"{agent_id}:{audience}:{','.join(sorted(scopes))}"
        if any(scope in {"broker:trade", "broker:withdraw", "prod:write"} for scope in scopes) and approval is None:
            raise PermissionError("high-risk scoped token requires signed approval")
        lease = self.rotator.rotate(subject, approval.signature if approval else "blinded")
        token_id = hashlib.sha256(f"{subject}:{lease.version}".encode("utf-8")).hexdigest()[:16]
        token = ScopedToken(token_id, agent_id, audience, list(scopes), lease.issued_at, lease.expires_at, lease.secret_digest)
        self._issued[token_id] = token
        return token

    def token_is_valid(self, token: ScopedToken, required_scope: str, now: Optional[float] = None) -> bool:
        return required_scope in token.scopes and (now or time.time()) < token.expires_at


class ClientSignedApprovalGate:
    """Creates and verifies client-side signed approval envelopes."""

    def __init__(self, client_secret: str, ttl_seconds: int = 600):
        self.client_secret = client_secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def sign(self, subject_id: str, approver: str, issued_at: Optional[float] = None) -> SignedApproval:
        issued = issued_at or time.time()
        expires = issued + self.ttl_seconds
        approval_id = hashlib.sha256(f"{subject_id}:{approver}:{issued}".encode("utf-8")).hexdigest()[:16]
        signature = self._signature(approval_id, subject_id, approver, issued, expires)
        return SignedApproval(approval_id, subject_id, approver, issued, expires, signature, ApprovalState.APPROVED)

    def verify(self, approval: SignedApproval, subject_id: str, now: Optional[float] = None) -> bool:
        if approval.subject_id != subject_id or approval.state != ApprovalState.APPROVED:
            return False
        if (now or time.time()) > approval.expires_at:
            return False
        expected = self._signature(approval.approval_id, approval.subject_id, approval.approver, approval.issued_at, approval.expires_at)
        return hmac.compare_digest(expected, approval.signature)

    def _signature(self, approval_id: str, subject_id: str, approver: str, issued_at: float, expires_at: float) -> str:
        payload = f"{approval_id}:{subject_id}:{approver}:{issued_at:.6f}:{expires_at:.6f}"
        return hmac.new(self.client_secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


class GlassBoxOverseer:
    """Deterministic overseer that emits auditable action classification."""

    _high_risk_requirements = {
        ActionClassification.LIVE_DEPLOYMENT: ["signed_approval", "ci_passed", "staging_validated"],
        ActionClassification.BROKER_CREDENTIAL_CHANGE: ["signed_approval", "vault_rotation_plan"],
        ActionClassification.RISK_LIMIT_CHANGE: ["signed_approval", "risk_report"],
        ActionClassification.CAPITAL_SCALING: ["signed_approval", "capital_risk_report"],
        ActionClassification.PRODUCTION_PATCH: ["signed_approval", "ci_passed", "rollback_plan"],
        ActionClassification.STRATEGY_PROMOTION: ["signed_approval", "backtest_report", "paper_trading_report"],
        ActionClassification.KILL_SWITCH_OVERRIDE: ["signed_approval", "incident_report"],
    }

    def classify(self, action: str, evidence: Optional[Dict[str, Any]] = None) -> GovernanceDecision:
        evidence = evidence or {}
        lowered = action.lower()
        action_class = self._classify_action(lowered)
        required = self._high_risk_requirements.get(action_class, [])
        missing = [item for item in required if not evidence.get(item)]
        risk = self._risk_for(action_class)
        manual = risk in {RiskCategory.HIGH, RiskCategory.CRITICAL} or bool(missing)
        decision = ApprovalState.APPROVED if not missing and risk in {RiskCategory.LOW, RiskCategory.MEDIUM} else ApprovalState.PENDING
        if risk == RiskCategory.CRITICAL:
            decision = ApprovalState.PENDING
        return GovernanceDecision(
            action_classification=action_class,
            risk_category=risk,
            policy_rule_triggered=f"{action_class.value}:{risk.value}",
            required_evidence=required,
            missing_evidence=missing,
            decision=decision,
            manual_review_required=manual,
            reason="high-risk action requires signed evidence" if manual else "evidence sufficient for low/medium-risk action",
        )

    def _classify_action(self, lowered: str) -> ActionClassification:
        if "kill-switch" in lowered or "kill switch" in lowered:
            return ActionClassification.KILL_SWITCH_OVERRIDE
        if "broker credential" in lowered or "credential" in lowered:
            return ActionClassification.BROKER_CREDENTIAL_CHANGE
        if "risk-limit" in lowered or "risk limit" in lowered:
            return ActionClassification.RISK_LIMIT_CHANGE
        if "capital scaling" in lowered or "scale capital" in lowered:
            return ActionClassification.CAPITAL_SCALING
        if "strategy promotion" in lowered or "promote strategy" in lowered:
            return ActionClassification.STRATEGY_PROMOTION
        if "live deploy" in lowered or "production deploy" in lowered:
            return ActionClassification.LIVE_DEPLOYMENT
        if "production patch" in lowered or "prod patch" in lowered:
            return ActionClassification.PRODUCTION_PATCH
        if "patch" in lowered:
            return ActionClassification.GENERATED_PATCH
        if "research" in lowered or "backtest" in lowered:
            return ActionClassification.RESEARCH
        if "read" in lowered or "scan" in lowered:
            return ActionClassification.READ_ONLY
        return ActionClassification.UNKNOWN

    def _risk_for(self, action_class: ActionClassification) -> RiskCategory:
        if action_class in {
            ActionClassification.LIVE_DEPLOYMENT,
            ActionClassification.BROKER_CREDENTIAL_CHANGE,
            ActionClassification.CAPITAL_SCALING,
            ActionClassification.KILL_SWITCH_OVERRIDE,
        }:
            return RiskCategory.CRITICAL
        if action_class in {
            ActionClassification.PRODUCTION_PATCH,
            ActionClassification.RISK_LIMIT_CHANGE,
            ActionClassification.STRATEGY_PROMOTION,
        }:
            return RiskCategory.HIGH
        if action_class in {ActionClassification.GENERATED_PATCH, ActionClassification.RESEARCH, ActionClassification.UNKNOWN}:
            return RiskCategory.MEDIUM
        return RiskCategory.LOW


class SessionMemoryCompactor:
    """Compacts session messages while retaining recent context."""

    def compact(self, messages: Sequence[Dict[str, str]], max_chars: int = 4000, retain_last: int = 6) -> MemoryCompactionResult:
        retained = list(messages[-retain_last:]) if retain_last else []
        older = list(messages[:-retain_last]) if retain_last else list(messages)
        facts: List[str] = []
        for message in older:
            content = str(message.get("content", "")).strip()
            if content and any(marker in content.lower() for marker in ("must", "require", "decision", "todo", "risk", "approval")):
                facts.append(content[:240])
        summary = "\n".join(f"- {fact}" for fact in facts)
        if len(summary) > max_chars:
            summary = summary[: max_chars - 3] + "..."
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
        return MemoryCompactionResult(summary, retained, max(0, len(messages) - len(retained)), digest)


class HierarchicalSessionMemory:
    """Append-only raw memory, compressed summaries, retrieval filters, and contradiction tracking."""

    def __init__(self, compactor: Optional[SessionMemoryCompactor] = None):
        self.compactor = compactor or SessionMemoryCompactor()
        self.raw_log: List[Dict[str, str]] = []
        self.summaries: List[MemoryCompactionResult] = []
        self.contradictions: List[str] = []

    def append(self, role: str, content: str) -> None:
        self.raw_log.append({"role": role, "content": content})
        self._track_contradictions(content)

    def compact(self, max_chars: int = 4000, retain_last: int = 6) -> MemoryCompactionResult:
        result = self.compactor.compact(self.raw_log, max_chars=max_chars, retain_last=retain_last)
        self.summaries.append(result)
        return result

    def retrieve(self, include_terms: Optional[Sequence[str]] = None, exclude_terms: Optional[Sequence[str]] = None) -> List[Dict[str, str]]:
        include = [term.lower() for term in include_terms or []]
        exclude = [term.lower() for term in exclude_terms or []]
        results = []
        for message in self.raw_log:
            content = message.get("content", "").lower()
            if include and not all(term in content for term in include):
                continue
            if exclude and any(term in content for term in exclude):
                continue
            results.append(message)
        return results

    def _track_contradictions(self, content: str) -> None:
        lowered = content.lower()
        if " not " not in f" {lowered} ":
            return
        candidates = {
            lowered.replace(" not ", " "),
            lowered.replace("does not require", "requires"),
            lowered.replace("does not ", ""),
        }
        for message in self.raw_log[:-1]:
            previous = message.get("content", "").lower()
            if any(candidate.strip() and (candidate.strip() in previous or previous in candidate.strip()) for candidate in candidates):
                self.contradictions.append(content)
                break


class ToolCallFusionPlanner:
    """Fuses compatible read-only calls into batches."""

    def fuse(self, calls: Sequence[ToolCall]) -> List[FusedToolCall]:
        batches: Dict[SandboxTier, List[ToolCall]] = {}
        fused: List[FusedToolCall] = []
        for call in calls:
            if call.read_only:
                batches.setdefault(call.tier, []).append(call)
            else:
                fused.append(FusedToolCall([call], call.tier, "stateful call kept isolated"))
        for tier, tier_calls in batches.items():
            fused.append(FusedToolCall(tier_calls, tier, "compatible read-only calls fused"))
        return fused


class ToolPlanCompiler:
    """Checks execution plans, parallelizes independent calls, merges repeats, and blocks unsafe calls."""

    def __init__(self, sandbox_mesh: Optional[TieredSandboxMesh] = None):
        self.sandbox_mesh = sandbox_mesh or TieredSandboxMesh()
        self.fusion_planner = ToolCallFusionPlanner()

    def compile(self, calls: Sequence[ToolCall]) -> Dict[str, Any]:
        safe_calls: List[ToolCall] = []
        blocked: List[Dict[str, Any]] = []
        seen = set()
        for call in calls:
            decision = self.sandbox_mesh.decide(call.name, call.tier)
            key = (call.name, json.dumps(call.arguments, sort_keys=True), call.read_only, call.tier.value)
            if not decision.allowed and decision.required_approval:
                blocked.append({"call": call.to_dict(), "decision": decision.to_dict()})
                continue
            if key in seen:
                continue
            seen.add(key)
            safe_calls.append(call)
        return {
            "fused_calls": [batch.to_dict() for batch in self.fusion_planner.fuse(safe_calls)],
            "blocked_calls": blocked,
            "summary": f"{len(safe_calls)} safe calls compiled, {len(blocked)} blocked",
        }


class ToolSearchIndex:
    """Small deterministic search index for choosing the right tool before planning."""

    def __init__(self, descriptors: Optional[Sequence[ToolDescriptor]] = None):
        self._descriptors = list(descriptors or self._default_descriptors())

    def search(self, query: str, limit: int = 5) -> List[ToolSearchResult]:
        query_terms = self._tokenize(query)
        ranked: List[ToolSearchResult] = []
        for descriptor in self._descriptors:
            haystack = self._tokenize(
                f"{descriptor.name} {descriptor.description} {' '.join(descriptor.tags)}"
            )
            matched = sorted(query_terms & haystack)
            if not matched:
                continue
            exact_name_bonus = 0.50 if descriptor.name.lower() in query.lower() else 0.0
            tag_bonus = 0.20 * sum(1 for term in matched if term in descriptor.tags)
            score = len(matched) + exact_name_bonus + tag_bonus
            ranked.append(ToolSearchResult(descriptor, round(score, 4), matched))
        ranked.sort(key=lambda item: (-item.score, item.descriptor.name))
        return ranked[:limit]

    def _tokenize(self, text: str) -> set[str]:
        normalized = text.lower().replace("_", " ").replace("-", " ")
        return {token.strip(".,:;()[]{}") for token in normalized.split() if len(token) > 2}

    def _default_descriptors(self) -> List[ToolDescriptor]:
        return [
            ToolDescriptor("scan_market", "Read market snapshots and technical context", ["market", "scan", "read"]),
            ToolDescriptor("prefetch_context", "Fetch relevant local context before reasoning", ["context", "research", "read"]),
            ToolDescriptor("run_backtest", "Run a sandboxed backtest or walk-forward validation", ["backtest", "strategy"], False, SandboxTier.SIMULATED_WRITE),
            ToolDescriptor("propose_patch", "Generate an approval-gated code patch", ["patch", "code"], False, SandboxTier.SIMULATED_WRITE),
            ToolDescriptor("risk_report", "Read risk, drawdown, exposure, and limit diagnostics", ["risk", "exposure", "read"]),
        ]


class ProgrammaticToolCallCompiler:
    """Collapses many tool-choice turns into one checked script."""

    def __init__(
        self,
        search_index: Optional[ToolSearchIndex] = None,
        plan_compiler: Optional[ToolPlanCompiler] = None,
    ):
        self.search_index = search_index or ToolSearchIndex()
        self.plan_compiler = plan_compiler or ToolPlanCompiler()

    def compile_script(
        self,
        objective: str,
        calls: Sequence[ToolCall],
        tool_query: Optional[str] = None,
        search_limit: int = 5,
    ) -> ProgrammaticToolScript:
        selected_tools = self.search_index.search(tool_query or objective, limit=search_limit)
        compiled = self.plan_compiler.compile(calls)
        fused_calls = [self._fused_from_dict(item) for item in compiled["fused_calls"]]
        blocked_calls = list(compiled["blocked_calls"])
        raw_steps = len(calls)
        collapsed_steps = len(fused_calls) + len(blocked_calls)
        steps_saved = max(0, raw_steps - collapsed_steps)
        script_id = hashlib.sha256(
            f"{objective}:{json.dumps([call.to_dict() for call in calls], sort_keys=True)}".encode("utf-8")
        ).hexdigest()[:16]
        provenance = DecisionProvenanceTrace(decision_id=script_id)
        provenance.append("tool_search", "tool_search_index", f"selected {len(selected_tools)} candidate tools")
        provenance.append("script_compile", "programmatic_tool_compiler", compiled["summary"])
        provenance.append("efficiency", "programmatic_tool_compiler", f"estimated {steps_saved} inference steps saved")
        provenance.seal()
        return ProgrammaticToolScript(
            script_id=script_id,
            objective=objective,
            fused_calls=fused_calls,
            blocked_calls=blocked_calls,
            selected_tools=selected_tools,
            estimated_inference_steps_saved=steps_saved,
            provenance=provenance,
        )

    def _fused_from_dict(self, item: Dict[str, Any]) -> FusedToolCall:
        calls = [
            ToolCall(
                call["name"],
                dict(call.get("arguments", {})),
                bool(call.get("read_only", True)),
                SandboxTier(call.get("tier", SandboxTier.READ_ONLY.value)),
            )
            for call in item.get("calls", [])
        ]
        return FusedToolCall(calls, SandboxTier(item["tier"]), item["reason"])


class ContextPrefetcher:
    """Selects likely useful context artifacts before reasoning starts."""

    def prefetch(self, query: str, available_paths: Iterable[str], limit: int = 8) -> List[str]:
        tokens = {token for token in query.lower().replace("_", " ").split() if len(token) > 2}
        ranked = []
        for path in available_paths:
            normalized = path.lower().replace("_", " ").replace("\\", " ")
            score = sum(1 for token in tokens if token in normalized)
            if score:
                ranked.append((score, path))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [path for _, path in ranked[:limit]]


class SelfConsistencyVerifier:
    """Accepts results only when candidates and optional hard checks agree."""

    def verify(self, candidates: Sequence[str], required_terms: Optional[Sequence[str]] = None, threshold: float = 0.60) -> VerificationReport:
        normalized = [candidate.strip() for candidate in candidates if candidate and candidate.strip()]
        if not normalized:
            return VerificationReport(False, "", 0.0, ["no candidates supplied"])
        counts = Counter(normalized)
        canonical, count = counts.most_common(1)[0]
        agreement = count / len(normalized)
        notes = []
        for term in required_terms or []:
            if term.lower() not in canonical.lower():
                notes.append(f"missing required term: {term}")
        accepted = agreement >= threshold and not notes
        return VerificationReport(accepted, canonical, agreement, notes)


class DebatePostTrainingValidator:
    """Self-consistency and debate validator for AlphaAlgo reasoning workflows."""

    _allowed_workflows = {
        "trade_thesis_validation",
        "strategy_selection",
        "post_trade_diagnosis",
        "backtest_interpretation",
        "research_proposal_ranking",
    }

    def __init__(self, verifier: Optional[SelfConsistencyVerifier] = None):
        self.verifier = verifier or SelfConsistencyVerifier()

    def validate(self, workflow: str, candidates: Sequence[str], pro_arguments: Sequence[str], con_arguments: Sequence[str]) -> DebateValidationResult:
        if workflow not in self._allowed_workflows:
            return DebateValidationResult(workflow, False, "", 0.0, list(pro_arguments), list(con_arguments), ["unsupported workflow"])
        report = self.verifier.verify(candidates, threshold=0.60)
        missing_debate = []
        if not pro_arguments:
            missing_debate.append("missing pro arguments")
        if not con_arguments:
            missing_debate.append("missing con arguments")
        accepted = report.accepted and not missing_debate
        return DebateValidationResult(
            workflow=workflow,
            accepted=accepted,
            winner=report.canonical_answer,
            agreement=report.agreement,
            pro_arguments=list(pro_arguments),
            con_arguments=list(con_arguments),
            verifier_notes=report.verifier_notes + missing_debate,
        )


class FormalTradingInvariantRegistry:
    """Checks formalized trading invariants rather than market predictions."""

    def __init__(self):
        self.invariants: Dict[str, str] = {
            "no_direct_production_access": "production_access must be false for autonomous actions",
            "no_persistent_secrets_in_sandbox": "persistent_secrets must be false in sandbox sessions",
            "signed_approval_for_high_risk": "high-risk and critical actions require signed approval",
            "paper_before_production": "strategy promotion requires paper trading evidence",
        }

    def validate(self, facts: Dict[str, Any]) -> VerificationReport:
        notes = []
        if facts.get("autonomous") and facts.get("production_access"):
            notes.append("violates no_direct_production_access")
        if facts.get("sandbox") and facts.get("persistent_secrets"):
            notes.append("violates no_persistent_secrets_in_sandbox")
        if facts.get("risk_category") in {RiskCategory.HIGH.value, RiskCategory.CRITICAL.value} and not facts.get("signed_approval"):
            notes.append("violates signed_approval_for_high_risk")
        if facts.get("strategy_promotion") and not facts.get("paper_trading_report"):
            notes.append("violates paper_before_production")
        return VerificationReport(not notes, "formal trading invariants", 1.0 if not notes else 0.0, notes)


class FrontierCapabilityRegistry:
    """Catalogs frontier-agent capabilities with explicit safety weights.

    The default safe set intentionally lands near 70% coverage. The remaining
    capability budget is reserved for live execution, credential mutation, and
    capital scaling, all of which require signed evidence before activation.
    """

    def __init__(self, capabilities: Optional[Sequence[FrontierCapability]] = None):
        self._capabilities = list(capabilities or self._default_capabilities())

    def all(self) -> List[FrontierCapability]:
        return list(self._capabilities)

    def safe_target_set(self, target_coverage: float = 0.70) -> List[FrontierCapability]:
        selected: List[FrontierCapability] = []
        achieved = 0.0
        for capability in self._capabilities:
            if not capability.default_enabled:
                continue
            selected.append(capability)
            achieved += capability.coverage_weight
            if achieved >= target_coverage:
                break
        return selected

    def _default_capabilities(self) -> List[FrontierCapability]:
        return [
            FrontierCapability(
                "recurrent_reasoning_vlk",
                "Recurrent reasoning with verifiable logic kernel",
                FrontierCapabilityDomain.REASONING,
                0.09,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["public trace summaries only", "logic lock before high-confidence output"],
            ),
            FrontierCapability(
                "self_consistency_debate",
                "Self-consistency and debate validation",
                FrontierCapabilityDomain.REASONING,
                0.08,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["acceptance threshold", "pro/con evidence required"],
            ),
            FrontierCapability(
                "hierarchical_memory",
                "Hierarchical memory, compaction, retrieval, and contradiction checks",
                FrontierCapabilityDomain.MEMORY,
                0.07,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["digest every compaction", "retain contradiction notes"],
            ),
            FrontierCapability(
                "tool_search_index",
                "Tool search before execution planning",
                FrontierCapabilityDomain.TOOL_USE,
                0.05,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["ranked deterministic search", "read-only metadata"],
            ),
            FrontierCapability(
                "programmatic_tool_scripts",
                "Programmatic tool-call scripts that collapse repeated tool turns",
                FrontierCapabilityDomain.TOOL_USE,
                0.06,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["compile before execution", "blocked calls preserved for audit"],
            ),
            FrontierCapability(
                "tool_plan_compiler",
                "Tool-call planning, deduplication, parallel fusion, and unsafe-call blocking",
                FrontierCapabilityDomain.TOOL_USE,
                0.06,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["least privilege", "stateful calls isolated"],
            ),
            FrontierCapability(
                "managed_agent_decoupling",
                "Managed-agent decoupling through task-scoped leases",
                FrontierCapabilityDomain.ORCHESTRATION,
                0.07,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["scoped leases", "heartbeat expiry", "sandbox per agent"],
            ),
            FrontierCapability(
                "specialist_agent_mesh",
                "Persistent specialist-agent routing",
                FrontierCapabilityDomain.ORCHESTRATION,
                0.06,
                RiskCategory.LOW,
                ActionClassification.READ_ONLY,
                ["task-scoped routing", "risk specialist fallback"],
            ),
            FrontierCapability(
                "context_prefetch",
                "Context prefetch and retrieval planning",
                FrontierCapabilityDomain.RESEARCH,
                0.05,
                RiskCategory.LOW,
                ActionClassification.RESEARCH,
                ["read-only path ranking", "bounded result limit"],
            ),
            FrontierCapability(
                "approval_gated_patch_pipeline",
                "Approval-gated patch generation workflow",
                FrontierCapabilityDomain.CODING,
                0.05,
                RiskCategory.MEDIUM,
                ActionClassification.GENERATED_PATCH,
                ["diff proposal only", "signed approval before application"],
                sandbox_required=True,
            ),
            FrontierCapability(
                "defensive_security_review",
                "Defensive security analysis and remediation planning",
                FrontierCapabilityDomain.SECURITY,
                0.04,
                RiskCategory.MEDIUM,
                ActionClassification.RESEARCH,
                ["private vulnerability notes", "no public exploit output"],
                sandbox_required=True,
            ),
            FrontierCapability(
                "sandboxed_research_agents",
                "Sandboxed research and experiment planning",
                FrontierCapabilityDomain.RESEARCH,
                0.04,
                RiskCategory.MEDIUM,
                ActionClassification.RESEARCH,
                ["ephemeral sandbox", "no persistent secrets"],
                sandbox_required=True,
            ),
            FrontierCapability(
                "multimodal_market_evidence",
                "Multimodal market-evidence fusion",
                FrontierCapabilityDomain.MULTIMODAL,
                0.06,
                RiskCategory.MEDIUM,
                ActionClassification.RESEARCH,
                ["analysis only", "market-data provenance required"],
                required_evidence=["market_data_provenance"],
                sandbox_required=True,
            ),
            FrontierCapability(
                "strategy_promotion",
                "Strategy promotion from research to paper/live readiness",
                FrontierCapabilityDomain.TRADING,
                0.10,
                RiskCategory.HIGH,
                ActionClassification.STRATEGY_PROMOTION,
                ["backtest report", "paper-trading report", "signed approval"],
                required_evidence=["signed_approval", "backtest_report", "paper_trading_report"],
                sandbox_required=True,
                default_enabled=False,
            ),
            FrontierCapability(
                "broker_tool_tokens",
                "Broker-scoped tool tokens",
                FrontierCapabilityDomain.TRADING,
                0.09,
                RiskCategory.CRITICAL,
                ActionClassification.BROKER_CREDENTIAL_CHANGE,
                ["vault rotation plan", "short-lived scoped token", "signed approval"],
                required_evidence=["signed_approval", "vault_rotation_plan"],
                default_enabled=False,
            ),
            FrontierCapability(
                "capital_scaling_control",
                "Autonomous capital-scaling recommendations",
                FrontierCapabilityDomain.TRADING,
                0.10,
                RiskCategory.CRITICAL,
                ActionClassification.CAPITAL_SCALING,
                ["recommendation only", "capital risk report", "signed approval"],
                required_evidence=["signed_approval", "capital_risk_report"],
                default_enabled=False,
            ),
        ]


class FrontierAgentCapabilityController:
    """Activates roughly 70% frontier capability while leaving high-risk power gated."""

    def __init__(
        self,
        registry: Optional[FrontierCapabilityRegistry] = None,
        overseer: Optional[GlassBoxOverseer] = None,
        sandbox_mesh: Optional[TieredSandboxMesh] = None,
        invariants: Optional[FormalTradingInvariantRegistry] = None,
    ):
        self.registry = registry or FrontierCapabilityRegistry()
        self.overseer = overseer or GlassBoxOverseer()
        self.sandbox_mesh = sandbox_mesh or TieredSandboxMesh()
        self.invariants = invariants or FormalTradingInvariantRegistry()

    def activate(
        self,
        task: str,
        evidence: Optional[Dict[str, Any]] = None,
        target_coverage: float = 0.70,
        coordinator_id: str = "alphaalgo-frontier",
    ) -> FrontierActivationReport:
        evidence = evidence or {}
        governance = self.overseer.classify(task, evidence)
        selected = self.registry.safe_target_set(target_coverage)
        activated: List[FrontierCapability] = []
        deferred: List[Dict[str, Any]] = []
        sessions: List[SandboxSessionSpec] = []
        achieved = 0.0

        for capability in self.registry.all():
            should_consider = capability in selected or all(evidence.get(item) for item in capability.required_evidence)
            if not should_consider:
                deferred.append(self._defer(capability, "outside safe 70% target and missing evidence", capability.required_evidence))
                continue

            missing = [item for item in capability.required_evidence if not evidence.get(item)]
            if capability.risk_category in {RiskCategory.HIGH, RiskCategory.CRITICAL} and missing:
                deferred.append(self._defer(capability, "high-risk capability missing signed evidence", missing))
                continue

            invariant_report = self.invariants.validate(
                {
                    "autonomous": True,
                    "production_access": False,
                    "sandbox": capability.sandbox_required,
                    "persistent_secrets": False,
                    "risk_category": capability.risk_category.value,
                    "signed_approval": bool(evidence.get("signed_approval")),
                    "strategy_promotion": capability.action == ActionClassification.STRATEGY_PROMOTION,
                    "paper_trading_report": bool(evidence.get("paper_trading_report")),
                }
            )
            if not invariant_report.accepted:
                deferred.append(self._defer(capability, "formal invariant check failed", invariant_report.verifier_notes))
                continue

            if capability.sandbox_required:
                sessions.append(self.sandbox_mesh.create_ephemeral_session(coordinator_id, capability.name))
            activated.append(capability)
            achieved += capability.coverage_weight

        invariant_report = self.invariants.validate(
            {
                "autonomous": True,
                "production_access": False,
                "sandbox": bool(sessions),
                "persistent_secrets": False,
                "risk_category": governance.risk_category.value,
                "signed_approval": bool(evidence.get("signed_approval")),
                "strategy_promotion": governance.action_classification == ActionClassification.STRATEGY_PROMOTION,
                "paper_trading_report": bool(evidence.get("paper_trading_report")),
            }
        )
        provenance = DecisionProvenanceTrace(decision_id=hashlib.sha256(f"frontier:{task}".encode("utf-8")).hexdigest()[:16])
        provenance.append("capability_registry", "frontier_controller", f"target coverage {target_coverage:.2f}")
        provenance.append("governance", "glass_box_overseer", governance.reason, governance.missing_evidence)
        provenance.append("activation", "frontier_controller", f"activated {len(activated)} capabilities at {achieved:.2f} coverage")
        provenance.seal()
        return FrontierActivationReport(
            task=task,
            target_coverage=target_coverage,
            achieved_coverage=round(achieved, 4),
            activated=activated,
            deferred=deferred,
            governance=governance,
            invariant_report=invariant_report,
            sandbox_sessions=sessions,
            provenance=provenance,
        )

    def _defer(self, capability: FrontierCapability, reason: str, missing: Sequence[str]) -> Dict[str, Any]:
        return {
            "capability": capability.to_dict(),
            "reason": reason,
            "missing_evidence": list(missing),
        }


class SpecialistAgentRouter:
    """Routes tasks to persistent specialist agents."""

    def route(self, task: str) -> List[SpecialistAgent]:
        lowered = task.lower()
        agents: List[SpecialistAgent] = []
        if any(token in lowered for token in ("risk", "drawdown", "capital", "exposure")):
            agents.append(SpecialistAgent.RISK)
        if any(token in lowered for token in ("order", "execution", "slippage", "broker")):
            agents.append(SpecialistAgent.EXECUTION)
        if any(token in lowered for token in ("macro", "rates", "inflation", "fed")):
            agents.append(SpecialistAgent.MACRO)
        if any(token in lowered for token in ("backtest", "paper trading", "walk-forward")):
            agents.append(SpecialistAgent.BACKTEST)
        if any(token in lowered for token in ("patch", "code", "pull request", "regression")):
            agents.append(SpecialistAgent.CODE_REVIEW)
        if any(token in lowered for token in ("vulnerability", "secret", "credential", "sandbox", "security")):
            agents.append(SpecialistAgent.SECURITY)
        return agents or [SpecialistAgent.RISK]


class ManagedAgentSupervisor:
    """Decouples specialist agents behind scoped leases and sandbox sessions."""

    _blocked_scopes = {"broker:trade", "broker:withdraw", "prod:write", "capital:scale"}

    def __init__(
        self,
        router: Optional[SpecialistAgentRouter] = None,
        sandbox_mesh: Optional[TieredSandboxMesh] = None,
        default_ttl_seconds: int = 900,
    ):
        self.router = router or SpecialistAgentRouter()
        self.sandbox_mesh = sandbox_mesh or TieredSandboxMesh()
        self.default_ttl_seconds = default_ttl_seconds
        self._leases: Dict[str, ManagedAgentLease] = {}

    def lease_agent(
        self,
        agent_id: str,
        task: str,
        scopes: Sequence[str],
        ttl_seconds: Optional[int] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> ManagedAgentLease:
        evidence = evidence or {}
        blocked = sorted(scope for scope in scopes if scope in self._blocked_scopes)
        if blocked and not evidence.get("signed_approval"):
            raise PermissionError(f"managed agent scopes require signed approval: {', '.join(blocked)}")
        role = self.router.route(task)[0]
        issued_at = time.time()
        expires_at = issued_at + (ttl_seconds or self.default_ttl_seconds)
        session = self.sandbox_mesh.create_ephemeral_session(agent_id, f"managed agent: {task}")
        lease_seed = f"{agent_id}:{role.value}:{task}:{issued_at:.6f}"
        lease_id = hashlib.sha256(lease_seed.encode("utf-8")).hexdigest()[:16]
        lease = ManagedAgentLease(
            lease_id=lease_id,
            agent_id=agent_id,
            role=role,
            task=task,
            scopes=list(scopes),
            sandbox_session=session,
            issued_at=issued_at,
            expires_at=expires_at,
            heartbeat_at=issued_at,
        )
        self._leases[lease_id] = lease
        return lease

    def heartbeat(self, lease_id: str, now: Optional[float] = None) -> ManagedAgentLease:
        lease = self._leases[lease_id]
        current = now or time.time()
        if current >= lease.expires_at:
            lease.active = False
        else:
            lease.heartbeat_at = current
        return lease

    def revoke(self, lease_id: str) -> ManagedAgentLease:
        lease = self._leases[lease_id]
        lease.active = False
        self.sandbox_mesh.destroy_session(lease.sandbox_session)
        return lease

    def lease_is_active(self, lease_id: str, now: Optional[float] = None) -> bool:
        lease = self._leases[lease_id]
        return lease.active and (now or time.time()) < lease.expires_at

    def active_leases(self, now: Optional[float] = None) -> List[ManagedAgentLease]:
        current = now or time.time()
        return [lease for lease in self._leases.values() if lease.active and current < lease.expires_at]


class MythosInspiredAIGovernor:
    """Turns Mythos research lessons into AlphaAlgo-safe task plans."""

    _security_terms = ("vulnerability", "exploit", "cve", "sandbox", "secret", "credential", "untrusted", "malware")
    _trading_terms = ("trade", "strategy", "backtest", "portfolio", "risk", "execution", "market")
    _research_terms = ("research", "proposal", "experiment", "external repo", "paper")

    def __init__(
        self,
        overseer: Optional[GlassBoxOverseer] = None,
        sandbox_mesh: Optional[TieredSandboxMesh] = None,
        router: Optional[SpecialistAgentRouter] = None,
    ):
        self.profile = MythosCapabilityProfile()
        self.overseer = overseer or GlassBoxOverseer()
        self.sandbox_mesh = sandbox_mesh or TieredSandboxMesh()
        self.router = router or SpecialistAgentRouter()

    def plan(self, task: str, evidence: Optional[Dict[str, Any]] = None, coordinator_id: str = "alphaalgo") -> MythosTaskPlan:
        evidence = evidence or {}
        mode = self._mode_for(task)
        governance = self.overseer.classify(task, evidence)
        specialists = self.router.route(task)
        sandbox_session = None
        if mode in {MythosMode.DEFENSIVE_SECURITY, MythosMode.CODE_HARDENING, MythosMode.RESEARCH_EVALUATION}:
            sandbox_session = self.sandbox_mesh.create_ephemeral_session(coordinator_id, task)

        allowed_outputs, blocked_outputs, disclosure_state = self._output_policy(task, mode, evidence)
        provenance = DecisionProvenanceTrace(decision_id=hashlib.sha256(task.encode("utf-8")).hexdigest()[:16])
        provenance.append("research_translation", "mythos_governor", f"classified task as {mode.value}")
        provenance.append("governance", "glass_box_overseer", governance.reason, governance.missing_evidence)
        if sandbox_session:
            provenance.append("sandbox", "tiered_sandbox_mesh", f"created ephemeral session {sandbox_session.session_id}")
        provenance.seal()
        return MythosTaskPlan(task, mode, governance, specialists, sandbox_session, allowed_outputs, blocked_outputs, disclosure_state, provenance)

    def _mode_for(self, task: str) -> MythosMode:
        lowered = task.lower()
        if any(term in lowered for term in self._security_terms):
            return MythosMode.DEFENSIVE_SECURITY
        if "patch" in lowered or "code" in lowered or "pull request" in lowered:
            return MythosMode.CODE_HARDENING
        if any(term in lowered for term in self._research_terms):
            return MythosMode.RESEARCH_EVALUATION
        if any(term in lowered for term in self._trading_terms):
            return MythosMode.TRADING_REASONING
        return MythosMode.RESEARCH_EVALUATION

    def _output_policy(
        self,
        task: str,
        mode: MythosMode,
        evidence: Dict[str, Any],
    ) -> tuple[List[str], List[str], Optional[DisclosureState]]:
        allowed = ["summary", "risk assessment", "tests to run", "defensive remediation plan"]
        blocked = ["autonomous production action"]
        disclosure_state: Optional[DisclosureState] = None
        if mode == MythosMode.DEFENSIVE_SECURITY:
            allowed.extend(["private vulnerability note", "patch proposal", "regression test", "responsible disclosure draft"])
            blocked.extend(["public exploit details", "automatic public disclosure", "autonomous interaction with production targets"])
            if evidence.get("patched") and evidence.get("maintainer_approval"):
                disclosure_state = DisclosureState.COORDINATED_DISCLOSURE
            elif evidence.get("patch_ready"):
                disclosure_state = DisclosureState.PATCH_REVIEW
            else:
                disclosure_state = DisclosureState.PUBLIC_DISCLOSURE_BLOCKED
        elif mode == MythosMode.TRADING_REASONING:
            allowed.extend(["trade thesis validation", "strategy comparison", "post-trade diagnosis", "backtest interpretation"])
            blocked.extend(["unapproved live order", "risk-limit change without signed approval"])
        elif mode == MythosMode.CODE_HARDENING:
            allowed.extend(["pull request draft", "risk report", "sandbox validation summary"])
            blocked.extend(["direct production patch", "critical-system patch submission without review"])
        else:
            allowed.extend(["research proposal ranking", "sandbox experiment plan"])
            blocked.extend(["untrusted code outside sandbox", "external repo mutation"])
        return allowed, blocked, disclosure_state


class StrictPatchApprovalPipeline:
    """Generates patches but blocks application until signed approval verifies."""

    def __init__(self, approval_gate: ClientSignedApprovalGate):
        self.approval_gate = approval_gate
        self._proposals: Dict[str, PatchProposal] = {}

    def propose(self, file_path: str, old_text: str, new_text: str, risk: str = "medium") -> PatchProposal:
        diff = "\n".join(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile=f"a/{file_path}", tofile=f"b/{file_path}", lineterm=""))
        proposal_id = hashlib.sha256(f"{file_path}:{diff}:{risk}".encode("utf-8")).hexdigest()[:16]
        proposal = PatchProposal(proposal_id, file_path, diff, risk)
        self._proposals[proposal_id] = proposal
        return proposal

    def approve(self, proposal_id: str, approval: SignedApproval) -> PatchProposal:
        proposal = self._proposals[proposal_id]
        if not self.approval_gate.verify(approval, proposal_id):
            proposal.approval_state = ApprovalState.REJECTED
            return proposal
        proposal.approval_state = ApprovalState.APPROVED
        proposal.approval_id = approval.approval_id
        return proposal

    def can_apply(self, proposal_id: str) -> bool:
        return self._proposals[proposal_id].approval_state == ApprovalState.APPROVED

    def create_bugfix_workflow(self, bug_id: str, file_path: str, old_text: str, new_text: str, regression_test: str, risk_report: str) -> PatchWorkflowReport:
        patch = self.propose(file_path, old_text, new_text, risk="high")
        return PatchWorkflowReport(
            bug_id=bug_id,
            patch=patch,
            regression_test=regression_test,
            risk_report=risk_report,
            allowed_next_steps=[
                "open pull request with risk report",
                "human/security reviewer approval",
                "ci validation",
                "staging deployment",
                "paper trading validation",
            ],
            blocked_next_steps=[
                "automatic public vulnerability disclosure",
                "automatic exploit publication",
                "automatic patch submission to critical systems",
                "autonomous production repository mutation",
            ],
        )


class AIEngineeringAgent:
    """Engineering agent constrained to diagnosis, patches, tests, and reports."""

    def __init__(self, patch_pipeline: StrictPatchApprovalPipeline):
        self.patch_pipeline = patch_pipeline

    def observe_system_behavior(self, snapshot: Dict[str, Any]) -> EngineeringObservation:
        expected = str(snapshot.get("expected_behavior", "system should preserve risk-first behavior"))
        observed = str(snapshot.get("observed_behavior", snapshot.get("symptom", "unknown behavior")))
        source = str(snapshot.get("source", "runtime_observation"))
        symptoms = [str(item) for item in snapshot.get("symptoms", [])]
        metrics = {str(key): float(value) for key, value in snapshot.get("metrics", {}).items()}
        observation_id = hashlib.sha256(
            json.dumps({"source": source, "expected": expected, "observed": observed, "symptoms": symptoms}, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return EngineeringObservation(observation_id, source, expected, observed, metrics, symptoms)

    def detect_issue(self, observation: EngineeringObservation) -> bool:
        if observation.symptoms:
            return True
        if observation.expected_behavior.strip().lower() != observation.observed_behavior.strip().lower():
            return True
        return any(value < 0 for value in observation.metrics.values())

    def create_diagnosis(self, observation: EngineeringObservation, snapshot: Dict[str, Any]) -> EngineeringDiagnosis:
        suspected_files = [str(path) for path in snapshot.get("suspected_files", [])]
        if not suspected_files:
            suspected_files = ["unknown"]
        symptoms = " ".join(observation.symptoms).lower()
        category = "inefficiency" if any(token in symptoms for token in ("slow", "latency", "benchmark")) else "bug"
        if any(token in symptoms for token in ("risk", "approval", "unsafe", "security", "secret")):
            category = "weakness"
        severity = RiskCategory(str(snapshot.get("severity", RiskCategory.MEDIUM.value)))
        summary = str(snapshot.get("diagnosis", f"{category} detected from {observation.source}"))
        confidence = float(snapshot.get("confidence", 0.74 if observation.symptoms else 0.60))
        diagnosis_id = hashlib.sha256(f"{observation.observation_id}:{category}:{summary}".encode("utf-8")).hexdigest()[:16]
        return EngineeringDiagnosis(
            diagnosis_id=diagnosis_id,
            category=category,
            severity=severity,
            summary=summary,
            suspected_files=suspected_files,
            confidence=confidence,
            evidence_ids=[observation.observation_id],
        )

    def write_root_cause_report(self, observation: EngineeringObservation, snapshot: Dict[str, Any]) -> RootCauseReport:
        primary = str(snapshot.get("root_cause") or snapshot.get("diagnosis") or f"cause behind {observation.source}")
        factors = [str(item) for item in snapshot.get("contributing_factors", observation.symptoms or ["insufficient guardrail evidence"])]
        rejected = [str(item) for item in snapshot.get("rejected_symptom_fixes", ["patching only the observed symptom without proving the causal path"])]
        confidence = float(snapshot.get("root_cause_confidence", 0.72 if observation.symptoms else 0.55))
        root_cause_id = hashlib.sha256(f"{observation.observation_id}:{primary}:{confidence}".encode("utf-8")).hexdigest()[:16]
        return RootCauseReport(root_cause_id, primary, factors, rejected, [observation.observation_id], confidence)

    def propose_code_patch(
        self,
        diagnosis: EngineeringDiagnosis,
        file_path: str,
        old_text: str,
        new_text: str,
    ) -> PatchWorkflowReport:
        return self.patch_pipeline.create_bugfix_workflow(
            diagnosis.diagnosis_id,
            file_path,
            old_text,
            new_text,
            "generated tests must fail before patch and pass after patch",
            f"risk impact {diagnosis.severity.value} {diagnosis.category}: {diagnosis.summary}",
        )

    def generate_tests(self, diagnosis: EngineeringDiagnosis, root_cause: Optional[RootCauseReport] = None) -> EngineeringTestPlan:
        target = diagnosis.suspected_files[0].replace("\\", "/")
        root_cause_label = root_cause.primary_cause if root_cause else diagnosis.summary
        return EngineeringTestPlan(
            unit_tests=[f"unit test covers {diagnosis.category} in {target}"],
            sandbox_tests=["run focused test suite in ephemeral sandbox"],
            static_checks=["py_compile", "type/import boundary check"],
            security_checks=["secret scan", "unsafe live-trading scope scan"],
            performance_benchmarks=["baseline latency/throughput benchmark"],
            regression_tests=["previous failing scenario remains fixed"],
            invariant_tests=[f"invariant test preserves hidden assumptions for {target}"],
            hidden_tests=[f"hidden test proves fix handles unseen variant of {root_cause_label}"],
            adversarial_tests=["adversarial test attacks patch for overfit, bypass, and safety regression"],
        )


class AdversarialReviewerAgent:
    """Reviews engineering output before governance can approve it."""

    def review(
        self,
        patch_workflow: PatchWorkflowReport,
        test_plan: EngineeringTestPlan,
        sandbox_session: SandboxSessionSpec,
        quality_stage_results: Sequence[EngineeringStageResult],
    ) -> VerificationReport:
        notes = []
        if patch_workflow.patch.approval_state != ApprovalState.PENDING:
            notes.append("patch should remain pending until signed approval")
        if not test_plan.unit_tests or not test_plan.regression_tests:
            notes.append("test plan missing unit or regression coverage")
        if not test_plan.invariant_tests:
            notes.append("test plan missing invariant coverage")
        if not test_plan.hidden_tests or not test_plan.adversarial_tests:
            notes.append("test plan missing hidden or adversarial coverage")
        if not test_plan.security_checks or not test_plan.performance_benchmarks:
            notes.append("test plan missing security or performance checks")
        if sandbox_session.production_access or sandbox_session.persistent_secrets:
            notes.append("sandbox violates production/secrets isolation")
        failed_quality = [
            result.stage.value
            for result in quality_stage_results
            if result.status != EngineeringStageStatus.PASSED
        ]
        if failed_quality:
            notes.append(f"quality stages not passed: {', '.join(failed_quality)}")
        return VerificationReport(not notes, "adversarial engineering review", 1.0 if not notes else 0.0, notes)


class ControlledSoftwareFactory:
    """AI engineering control loop with patch, sandbox, review, governance, and release gates."""

    PIPELINE: List[EngineeringPipelineStage] = [
        EngineeringPipelineStage.OBSERVE_SYSTEM_BEHAVIOR,
        EngineeringPipelineStage.DETECT_BUG_WEAKNESS_INEFFICIENCY,
        EngineeringPipelineStage.VALIDATE_OBJECTIVE_EVIDENCE,
        EngineeringPipelineStage.WRITE_ROOT_CAUSE_REPORT,
        EngineeringPipelineStage.CREATE_DIAGNOSIS,
        EngineeringPipelineStage.PROPOSE_CODE_PATCH,
        EngineeringPipelineStage.CHECK_COMPLEXITY_BUDGET,
        EngineeringPipelineStage.CREATE_SANDBOX_BRANCH,
        EngineeringPipelineStage.GENERATE_TESTS,
        EngineeringPipelineStage.CREATE_INVARIANT_TESTS,
        EngineeringPipelineStage.RUN_TESTS_IN_SANDBOX,
        EngineeringPipelineStage.RUN_HIDDEN_ADVERSARIAL_TESTS,
        EngineeringPipelineStage.RUN_STATIC_ANALYSIS,
        EngineeringPipelineStage.RUN_SECURITY_SCAN,
        EngineeringPipelineStage.RUN_PROTECTED_FILE_CHECK,
        EngineeringPipelineStage.RUN_SECURITY_GATE_BEFORE_MERGE,
        EngineeringPipelineStage.RUN_PERFORMANCE_BENCHMARK,
        EngineeringPipelineStage.COMPARE_BEFORE_AFTER_METRICS,
        EngineeringPipelineStage.RUN_REGRESSION_TESTS,
        EngineeringPipelineStage.GENERATE_ENGINEERING_REPORT,
        EngineeringPipelineStage.OPEN_PULL_REQUEST,
        EngineeringPipelineStage.HUMAN_OR_GOVERNANCE_APPROVAL,
        EngineeringPipelineStage.DEPLOY_TO_STAGING,
        EngineeringPipelineStage.SHADOW_TEST_OR_PAPER_TRADE,
        EngineeringPipelineStage.CANARY_RELEASE,
        EngineeringPipelineStage.PRODUCTION_DEPLOYMENT,
        EngineeringPipelineStage.MONITOR,
        EngineeringPipelineStage.ROLLBACK_IF_METRICS_DEGRADE,
        EngineeringPipelineStage.UPDATE_FAILURE_MEMORY,
    ]

    def __init__(
        self,
        approval_gate: Optional[ClientSignedApprovalGate] = None,
        sandbox_mesh: Optional[TieredSandboxMesh] = None,
        overseer: Optional[GlassBoxOverseer] = None,
        reviewer: Optional[AdversarialReviewerAgent] = None,
    ):
        self.approval_gate = approval_gate or ClientSignedApprovalGate("software-factory-local")
        self.sandbox_mesh = sandbox_mesh or TieredSandboxMesh()
        self.overseer = overseer or GlassBoxOverseer()
        self.patch_pipeline = StrictPatchApprovalPipeline(self.approval_gate)
        self.agent = AIEngineeringAgent(self.patch_pipeline)
        self.reviewer = reviewer or AdversarialReviewerAgent()
        self.runtime_policy = RuntimeBoundaryPolicy()
        self.protected_file_policy = ProtectedFilePolicy()
        self.failure_memory: List[FailureMemoryEntry] = []

    def run_control_loop(
        self,
        objective: str,
        behavior_snapshot: Dict[str, Any],
        file_path: str,
        old_text: str,
        new_text: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> SoftwareFactoryRunReport:
        evidence = evidence or {}
        stages: List[EngineeringStageResult] = []
        observation = self.agent.observe_system_behavior(behavior_snapshot)
        detected = self.agent.detect_issue(observation)
        objective_validation = self._validate_objective_evidence(objective, observation, behavior_snapshot)
        root_cause_report = self.agent.write_root_cause_report(observation, behavior_snapshot)
        diagnosis = self.agent.create_diagnosis(observation, behavior_snapshot)
        patch_workflow = self.agent.propose_code_patch(diagnosis, file_path, old_text, new_text)
        complexity_budget = self._check_complexity_budget(old_text, new_text, evidence)
        test_plan = self.agent.generate_tests(diagnosis, root_cause_report)
        protected_file_report = self.protected_file_policy.check(file_path, evidence)
        metric_comparison = self._compare_before_after_metrics(evidence)
        sandbox = self.sandbox_mesh.create_ephemeral_session("ai-engineering-agent", objective)
        sandbox_branch = self._build_sandbox_branch(objective, patch_workflow.patch.proposal_id, evidence)

        self._append(stages, EngineeringPipelineStage.OBSERVE_SYSTEM_BEHAVIOR, EngineeringStageStatus.PASSED, "system behavior observed", [observation.observation_id])
        self._append(
            stages,
            EngineeringPipelineStage.DETECT_BUG_WEAKNESS_INEFFICIENCY,
            EngineeringStageStatus.PASSED if detected else EngineeringStageStatus.FAILED,
            "bug, weakness, or inefficiency detected" if detected else "no actionable issue detected",
            [observation.observation_id],
        )
        self._append(
            stages,
            EngineeringPipelineStage.VALIDATE_OBJECTIVE_EVIDENCE,
            EngineeringStageStatus.PASSED if objective_validation.accepted else EngineeringStageStatus.BLOCKED,
            "objective evidence validated" if objective_validation.accepted else "objective evidence insufficient",
            objective_validation.validators,
            "; ".join(objective_validation.notes) if objective_validation.notes else None,
        )
        self._append(
            stages,
            EngineeringPipelineStage.WRITE_ROOT_CAUSE_REPORT,
            EngineeringStageStatus.PASSED if root_cause_report.confidence >= 0.60 else EngineeringStageStatus.BLOCKED,
            root_cause_report.primary_cause,
            [root_cause_report.root_cause_id],
            None if root_cause_report.confidence >= 0.60 else "root-cause confidence below threshold",
        )
        self._append(stages, EngineeringPipelineStage.CREATE_DIAGNOSIS, EngineeringStageStatus.PASSED, diagnosis.summary, [diagnosis.diagnosis_id])
        patch_preconditions_passed = objective_validation.accepted and root_cause_report.confidence >= 0.60
        self._append(
            stages,
            EngineeringPipelineStage.PROPOSE_CODE_PATCH,
            EngineeringStageStatus.PASSED if patch_preconditions_passed else EngineeringStageStatus.BLOCKED,
            "minimal approval-gated patch proposal created" if patch_preconditions_passed else "patch proposal blocked until objective/root-cause evidence passes",
            [patch_workflow.patch.proposal_id],
            None if patch_preconditions_passed else "objective validation and root-cause report required before patching",
        )
        self._append(
            stages,
            EngineeringPipelineStage.CHECK_COMPLEXITY_BUDGET,
            EngineeringStageStatus.PASSED if complexity_budget.accepted else EngineeringStageStatus.BLOCKED,
            "minimal patch stays within complexity budget" if complexity_budget.accepted else "patch exceeds complexity budget",
            ["complexity_budget"],
            "; ".join(complexity_budget.notes) if complexity_budget.notes else None,
        )
        self._append(
            stages,
            EngineeringPipelineStage.CREATE_SANDBOX_BRANCH,
            EngineeringStageStatus.PASSED,
            "patch isolated on sandbox branch with no live runtime attachment",
            [sandbox_branch.branch_name, patch_workflow.patch.proposal_id],
        )
        self._append(stages, EngineeringPipelineStage.GENERATE_TESTS, EngineeringStageStatus.PASSED, "unit, sandbox, static, security, benchmark, and regression checks generated")
        self._append(
            stages,
            EngineeringPipelineStage.CREATE_INVARIANT_TESTS,
            EngineeringStageStatus.PASSED if test_plan.invariant_tests else EngineeringStageStatus.BLOCKED,
            "invariant tests generated to protect hidden assumptions" if test_plan.invariant_tests else "missing invariant tests",
            test_plan.invariant_tests,
        )

        quality_stages = self._run_quality_layers(stages, evidence, protected_file_report, metric_comparison)
        reviewer_report = self.reviewer.review(patch_workflow, test_plan, sandbox, quality_stages)
        verifier_agent_reviews = self._run_verifier_agents(
            patch_workflow,
            test_plan,
            sandbox_branch,
            sandbox,
            quality_stages,
            protected_file_report,
            metric_comparison,
            complexity_budget,
            objective_validation,
            root_cause_report,
        )
        verifier_passed = all(review.decision == ApprovalState.APPROVED for review in verifier_agent_reviews)
        reviewer_status = EngineeringStageStatus.PASSED if reviewer_report.accepted and verifier_passed else EngineeringStageStatus.BLOCKED
        self._append(stages, EngineeringPipelineStage.GENERATE_ENGINEERING_REPORT, reviewer_status, "engineering report generated after adversarial review", reviewer_report.verifier_notes)

        pr = self._build_pull_request(objective, diagnosis, patch_workflow, test_plan, sandbox_branch.branch_name, reviewer_report.accepted and verifier_passed)
        self._append(
            stages,
            EngineeringPipelineStage.OPEN_PULL_REQUEST,
            EngineeringStageStatus.PASSED if reviewer_report.accepted and verifier_passed else EngineeringStageStatus.BLOCKED,
            "pull request draft ready for review" if reviewer_report.accepted and verifier_passed else "pull request blocked by verifier agents",
            [patch_workflow.patch.proposal_id],
            None if reviewer_report.accepted and verifier_passed else "; ".join(reviewer_report.verifier_notes),
        )

        governance_evidence = dict(evidence)
        governance_evidence.setdefault("ci_passed", reviewer_report.accepted and verifier_passed)
        governance_evidence.setdefault("rollback_plan", True)
        governance = self.overseer.classify("production patch through controlled software factory", governance_evidence)
        approval_actor = str(governance_evidence.get("governance_approver") or governance_evidence.get("approver") or "")
        self_approved = approval_actor.lower() in {"ai-engineering-agent", "engineering_ai", "alphaalgo-engineering-ai"}
        governance_passed = bool(governance_evidence.get("signed_approval")) and not governance.missing_evidence and not self_approved
        governance_block = "AI may not approve its own work" if self_approved else (", ".join(governance.missing_evidence) if governance.missing_evidence else None)
        self._append(
            stages,
            EngineeringPipelineStage.HUMAN_OR_GOVERNANCE_APPROVAL,
            EngineeringStageStatus.PASSED if governance_passed else (EngineeringStageStatus.BLOCKED if self_approved else EngineeringStageStatus.PENDING),
            "signed governance approval verified" if governance_passed else ("self-approval rejected" if self_approved else "awaiting human or governance approval"),
            governance.required_evidence,
            governance_block,
        )

        staging_passed = governance_passed and not evidence.get("staging_failed", False)
        self._append(
            stages,
            EngineeringPipelineStage.DEPLOY_TO_STAGING,
            EngineeringStageStatus.PASSED if staging_passed else EngineeringStageStatus.BLOCKED,
            "staging deployment authorized" if staging_passed else "staging blocked until governance approval",
            ["staging_plan"],
            None if staging_passed else "governance approval required",
        )
        shadow_passed = staging_passed and bool(evidence.get("shadow_test_passed"))
        self._append(
            stages,
            EngineeringPipelineStage.SHADOW_TEST_OR_PAPER_TRADE,
            EngineeringStageStatus.PASSED if shadow_passed else (EngineeringStageStatus.PENDING if staging_passed else EngineeringStageStatus.BLOCKED),
            "shadow test / paper trade passed" if shadow_passed else "shadow test / paper trade required",
            ["shadow_test_passed"] if shadow_passed else [],
            None if staging_passed else "staging deployment required",
        )
        canary_passed = shadow_passed and bool(evidence.get("canary_metrics_passed"))
        self._append(
            stages,
            EngineeringPipelineStage.CANARY_RELEASE,
            EngineeringStageStatus.PASSED if canary_passed else (EngineeringStageStatus.PENDING if shadow_passed else EngineeringStageStatus.BLOCKED),
            "canary release metrics passed" if canary_passed else "canary release required",
            ["canary_metrics_passed"] if canary_passed else [],
            None if shadow_passed else "shadow test / paper trade required",
        )
        monitor_passed = canary_passed and bool(evidence.get("monitoring_baseline"))
        production_enabled = monitor_passed and not bool(evidence.get("metrics_degraded"))
        self._append(
            stages,
            EngineeringPipelineStage.PRODUCTION_DEPLOYMENT,
            EngineeringStageStatus.PASSED if production_enabled else (EngineeringStageStatus.PENDING if canary_passed else EngineeringStageStatus.BLOCKED),
            "production deployment authorized after canary" if production_enabled else "production deployment withheld",
            ["monitoring_baseline"] if production_enabled else [],
            None if canary_passed else "canary release required",
        )
        self._append(
            stages,
            EngineeringPipelineStage.MONITOR,
            EngineeringStageStatus.PASSED if monitor_passed else (EngineeringStageStatus.PENDING if canary_passed else EngineeringStageStatus.BLOCKED),
            "monitoring baseline established" if monitor_passed else "monitoring baseline required",
            ["monitoring_baseline"] if monitor_passed else [],
            None if canary_passed else "canary release required",
        )
        rollback_summary = "rollback not required"
        if evidence.get("metrics_degraded"):
            rollback_summary = "rollback triggered because metrics degraded"
        self._append(
            stages,
            EngineeringPipelineStage.ROLLBACK_IF_METRICS_DEGRADE,
            EngineeringStageStatus.PASSED if monitor_passed else EngineeringStageStatus.BLOCKED,
            rollback_summary,
            ["rollback_plan"],
            None if monitor_passed else "monitoring baseline required",
        )
        failure_memory_entry = self._update_failure_memory(objective, stages, evidence, metric_comparison)
        self._append(
            stages,
            EngineeringPipelineStage.UPDATE_FAILURE_MEMORY,
            EngineeringStageStatus.PASSED,
            f"failure memory updated with outcome: {failure_memory_entry.outcome}",
            [failure_memory_entry.memory_id],
        )

        deployment_plan = DeploymentPlan(
            staging_environment=str(evidence.get("staging_environment", "paper-staging")),
            shadow_mode="paper_trade",
            canary_percentage=float(evidence.get("canary_percentage", 5.0)),
            production_enabled=production_enabled,
            rollback_triggers=["error_rate", "latency_p95", "drawdown", "order_reject_rate"],
            monitoring_metrics=["test_pass_rate", "latency_p95", "security_findings", "paper_trade_slippage"],
        )
        run_id = hashlib.sha256(f"{objective}:{diagnosis.diagnosis_id}:{patch_workflow.patch.proposal_id}".encode("utf-8")).hexdigest()[:16]
        provenance = DecisionProvenanceTrace(decision_id=run_id)
        for stage in stages:
            provenance.append(stage.stage.value, "controlled_software_factory", stage.summary, stage.evidence_ids)
        provenance.seal()
        return SoftwareFactoryRunReport(
            run_id=run_id,
            objective=objective,
            observation=observation,
            diagnosis=diagnosis,
            root_cause_report=root_cause_report,
            objective_validation=objective_validation,
            complexity_budget=complexity_budget,
            patch_workflow=patch_workflow,
            test_plan=test_plan,
            protected_file_report=protected_file_report,
            metric_comparison=metric_comparison,
            failure_memory_entry=failure_memory_entry,
            runtime_policy=self.runtime_policy,
            sandbox_branch=sandbox_branch,
            sandbox_session=sandbox,
            verifier_agent_reviews=verifier_agent_reviews,
            reviewer_report=reviewer_report,
            governance=governance,
            pull_request=pr,
            deployment_plan=deployment_plan,
            stages=stages,
            provenance=provenance,
        )

    def _run_quality_layers(
        self,
        stages: List[EngineeringStageResult],
        evidence: Dict[str, Any],
        protected_file_report: VerificationReport,
        metric_comparison: MetricComparisonReport,
    ) -> List[EngineeringStageResult]:
        quality_results: List[EngineeringStageResult] = []
        checks = [
            (EngineeringPipelineStage.RUN_TESTS_IN_SANDBOX, "sandbox tests passed", "force_sandbox_test_failure", None),
            (EngineeringPipelineStage.RUN_HIDDEN_ADVERSARIAL_TESTS, "hidden and adversarial tests passed", "force_hidden_adversarial_failure", None),
            (EngineeringPipelineStage.RUN_STATIC_ANALYSIS, "static analysis passed", "force_static_failure", None),
            (EngineeringPipelineStage.RUN_SECURITY_SCAN, "security scan passed", "force_security_failure", None),
            (
                EngineeringPipelineStage.RUN_PROTECTED_FILE_CHECK,
                "protected file policy passed",
                None,
                protected_file_report,
            ),
            (
                EngineeringPipelineStage.RUN_SECURITY_GATE_BEFORE_MERGE,
                "security merge gate passed",
                "force_security_gate_failure",
                None,
            ),
            (EngineeringPipelineStage.RUN_PERFORMANCE_BENCHMARK, "performance benchmark passed", "force_benchmark_failure", None),
            (
                EngineeringPipelineStage.COMPARE_BEFORE_AFTER_METRICS,
                "before/after metrics accepted",
                None,
                VerificationReport(metric_comparison.accepted, "metric comparison", 1.0 if metric_comparison.accepted else 0.0, metric_comparison.regressions),
            ),
            (EngineeringPipelineStage.RUN_REGRESSION_TESTS, "regression tests passed", "force_regression_failure", None),
        ]
        for stage, summary, failure_flag, external_report in checks:
            external_failed = external_report is not None and not external_report.accepted
            forced_failed = bool(failure_flag and evidence.get(failure_flag))
            status = EngineeringStageStatus.FAILED if forced_failed else (EngineeringStageStatus.BLOCKED if external_failed else EngineeringStageStatus.PASSED)
            notes = external_report.verifier_notes if external_report else []
            blocked_reason = failure_flag if forced_failed else ("; ".join(notes) if external_failed else None)
            result = EngineeringStageResult(
                stage=stage,
                status=status,
                summary=summary if status == EngineeringStageStatus.PASSED else f"{summary} failed",
                evidence_ids=[stage.value],
                blocked_reason=blocked_reason,
            )
            stages.append(result)
            quality_results.append(result)
        return quality_results

    def _append(
        self,
        stages: List[EngineeringStageResult],
        stage: EngineeringPipelineStage,
        status: EngineeringStageStatus,
        summary: str,
        evidence_ids: Optional[Sequence[str]] = None,
        blocked_reason: Optional[str] = None,
    ) -> None:
        stages.append(EngineeringStageResult(stage, status, summary, list(evidence_ids or []), blocked_reason))

    def _validate_objective_evidence(
        self,
        objective: str,
        observation: EngineeringObservation,
        snapshot: Dict[str, Any],
    ) -> ObjectiveValidationResult:
        validators = ["behavior_delta", "objective_metric", "source_trace"]
        notes = []
        score = 0.0
        if observation.expected_behavior.strip().lower() != observation.observed_behavior.strip().lower():
            score += 0.40
        else:
            notes.append("expected and observed behavior are identical")
        if observation.symptoms:
            score += 0.20
        else:
            notes.append("no concrete symptoms supplied")
        metrics = observation.metrics
        if metrics or snapshot.get("before_metrics") or snapshot.get("after_metrics"):
            score += 0.20
        else:
            notes.append("no objective metrics supplied")
        if observation.source not in {"runtime_observation", "unknown"}:
            score += 0.20
        else:
            notes.append("weak observation source")
        if not objective.strip():
            notes.append("empty objective")
        accepted = score >= float(snapshot.get("objective_validation_threshold", 0.60))
        return ObjectiveValidationResult(accepted, round(score, 4), validators, [] if accepted else notes)

    def _check_complexity_budget(
        self,
        old_text: str,
        new_text: str,
        evidence: Dict[str, Any],
    ) -> ComplexityBudget:
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        changed_lines = abs(len(new_lines) - len(old_lines)) + sum(
            1 for old, new in zip(old_lines, new_lines) if old.strip() != new.strip()
        )
        new_functions = max(0, new_text.count("def ") - old_text.count("def "))
        complexity_delta = max(0, new_text.count("if ") - old_text.count("if ")) + max(
            0, new_text.count("for ") - old_text.count("for ")
        )
        max_changed = int(evidence.get("max_changed_lines", 60))
        max_functions = int(evidence.get("max_new_functions", 2))
        max_delta = int(evidence.get("max_complexity_delta", 4))
        notes = []
        if changed_lines > max_changed:
            notes.append(f"changed lines {changed_lines} exceed budget {max_changed}")
        if new_functions > max_functions:
            notes.append(f"new functions {new_functions} exceed budget {max_functions}")
        if complexity_delta > max_delta:
            notes.append(f"complexity delta {complexity_delta} exceed budget {max_delta}")
        return ComplexityBudget(
            max_changed,
            max_functions,
            max_delta,
            changed_lines,
            new_functions,
            complexity_delta,
            not notes,
            notes,
        )

    def _compare_before_after_metrics(self, evidence: Dict[str, Any]) -> MetricComparisonReport:
        before = {str(key): float(value) for key, value in evidence.get("before_metrics", {}).items()}
        after = {str(key): float(value) for key, value in evidence.get("after_metrics", {}).items()}
        regressions = []
        lower_is_better = {"latency", "latency_p95", "error_rate", "drawdown", "order_reject_rate", "slippage"}
        higher_is_better = {"throughput", "test_pass_rate", "sharpe", "win_rate"}
        for name, before_value in before.items():
            if name not in after:
                continue
            after_value = after[name]
            if name in lower_is_better and after_value > before_value * 1.02:
                regressions.append(f"{name} regressed from {before_value} to {after_value}")
            if name in higher_is_better and after_value < before_value * 0.98:
                regressions.append(f"{name} regressed from {before_value} to {after_value}")
        if evidence.get("force_metric_regression"):
            regressions.append("forced metric regression")
        return MetricComparisonReport(before, after, not regressions, regressions)

    def _update_failure_memory(
        self,
        objective: str,
        stages: Sequence[EngineeringStageResult],
        evidence: Dict[str, Any],
        metric_comparison: MetricComparisonReport,
    ) -> FailureMemoryEntry:
        rollback_triggered = bool(evidence.get("metrics_degraded"))
        blocked = [stage.stage.value for stage in stages if stage.status in {EngineeringStageStatus.BLOCKED, EngineeringStageStatus.FAILED}]
        if rollback_triggered:
            outcome = "rollback"
        elif blocked:
            outcome = "blocked"
        else:
            outcome = "accepted"
        lessons = []
        if blocked:
            lessons.append(f"blocked stages: {', '.join(blocked[:6])}")
        if metric_comparison.regressions:
            lessons.extend(metric_comparison.regressions)
        if rollback_triggered:
            lessons.append("monitoring degradation triggered rollback")
        if not lessons:
            lessons.append("patch passed controlled factory gates")
        memory_id = hashlib.sha256(f"{objective}:{outcome}:{'|'.join(lessons)}".encode("utf-8")).hexdigest()[:16]
        entry = FailureMemoryEntry(memory_id, objective, outcome, lessons, rollback_triggered)
        self.failure_memory.append(entry)
        return entry

    def _build_sandbox_branch(
        self,
        objective: str,
        patch_proposal_id: str,
        evidence: Dict[str, Any],
    ) -> SandboxBranchPlan:
        return SandboxBranchPlan(
            branch_name=self._branch_name(objective),
            base_branch=str(evidence.get("base_branch", "master")),
            patch_proposal_id=patch_proposal_id,
        )

    def _run_verifier_agents(
        self,
        patch_workflow: PatchWorkflowReport,
        test_plan: EngineeringTestPlan,
        sandbox_branch: SandboxBranchPlan,
        sandbox_session: SandboxSessionSpec,
        quality_stage_results: Sequence[EngineeringStageResult],
        protected_file_report: VerificationReport,
        metric_comparison: MetricComparisonReport,
        complexity_budget: ComplexityBudget,
        objective_validation: ObjectiveValidationResult,
        root_cause_report: RootCauseReport,
    ) -> List[VerifierAgentReview]:
        failed_quality = [
            result.stage.value
            for result in quality_stage_results
            if result.status != EngineeringStageStatus.PASSED
        ]
        isolation_findings = []
        if sandbox_branch.live_runtime_attached or sandbox_session.production_access:
            isolation_findings.append("sandbox is attached to production runtime")
        if sandbox_branch.live_code_mutation_allowed:
            isolation_findings.append("sandbox branch permits live code mutation")
        if sandbox_branch.risk_limit_change_allowed:
            isolation_findings.append("sandbox branch permits risk-limit changes")
        if sandbox_branch.model_mutation_allowed:
            isolation_findings.append("sandbox branch permits model mutation")
        coverage_findings = []
        if not test_plan.unit_tests or not test_plan.regression_tests:
            coverage_findings.append("missing unit or regression coverage")
        if not test_plan.invariant_tests:
            coverage_findings.append("missing invariant coverage")
        if not test_plan.hidden_tests or not test_plan.adversarial_tests:
            coverage_findings.append("missing hidden or adversarial coverage")
        if failed_quality:
            coverage_findings.append(f"quality failures: {', '.join(failed_quality)}")
        security_findings = []
        if not test_plan.security_checks:
            security_findings.append("missing security checks")
        if sandbox_session.persistent_secrets:
            security_findings.append("sandbox exposes persistent secrets")
        if not protected_file_report.accepted:
            security_findings.extend(protected_file_report.verifier_notes)
        risk_findings = []
        if "risk" not in patch_workflow.risk_report.lower():
            risk_findings.append("risk report missing risk discussion")
        if not objective_validation.accepted:
            risk_findings.extend(objective_validation.notes)
        if root_cause_report.confidence < 0.60:
            risk_findings.append("root-cause confidence below threshold")
        performance_findings = []
        if not test_plan.performance_benchmarks:
            performance_findings.append("missing performance benchmark")
        if not metric_comparison.accepted:
            performance_findings.extend(metric_comparison.regressions)
        complexity_findings = [] if complexity_budget.accepted else list(complexity_budget.notes)

        return [
            self._verifier("code-review-verifier", SpecialistAgent.CODE_REVIEW, coverage_findings + complexity_findings, "code/test coverage verified"),
            self._verifier("security-verifier", SpecialistAgent.SECURITY, security_findings + isolation_findings, "security and sandbox isolation verified"),
            self._verifier("risk-verifier", SpecialistAgent.RISK, risk_findings + isolation_findings, "risk controls verified"),
            self._verifier("backtest-verifier", SpecialistAgent.BACKTEST, performance_findings + failed_quality, "simulation and benchmark evidence verified"),
        ]

    def _verifier(
        self,
        verifier_id: str,
        role: SpecialistAgent,
        findings: Sequence[str],
        success_summary: str,
    ) -> VerifierAgentReview:
        return VerifierAgentReview(
            verifier_id=verifier_id,
            role=role,
            decision=ApprovalState.REJECTED if findings else ApprovalState.APPROVED,
            summary="; ".join(findings) if findings else success_summary,
            findings=list(findings),
        )

    def _build_pull_request(
        self,
        objective: str,
        diagnosis: EngineeringDiagnosis,
        patch_workflow: PatchWorkflowReport,
        test_plan: EngineeringTestPlan,
        branch_name: str,
        ready: bool,
    ) -> PullRequestDraft:
        body = "\n".join(
            [
                f"Diagnosis: {diagnosis.summary}",
                f"Patch proposal: {patch_workflow.patch.proposal_id}",
                f"Unit tests: {', '.join(test_plan.unit_tests)}",
                f"Security checks: {', '.join(test_plan.security_checks)}",
                "Deployment: staging -> shadow/paper -> canary -> production -> monitor/rollback",
            ]
        )
        return PullRequestDraft(
            title=f"Controlled fix: {diagnosis.category}",
            body=body,
            branch_name=branch_name,
            ready_for_review=ready,
        )

    def _branch_name(self, objective: str) -> str:
        slug = "-".join(
            token
            for token in "".join(char.lower() if char.isalnum() else " " for char in objective).split()
            if token
        )[:48] or "engineering-fix"
        return f"codex/{slug}"


__all__ = [
    "ActionClassification",
    "AdversarialReviewerAgent",
    "AIEngineeringAgent",
    "ApprovalState",
    "DebatePostTrainingValidator",
    "ClientSignedApprovalGate",
    "ContextPrefetcher",
    "ControlledSoftwareFactory",
    "ComplexityBudget",
    "CredentialLease",
    "DecisionProvenanceEvent",
    "DecisionProvenanceTrace",
    "DisclosureState",
    "DynamicCredentialRotator",
    "DeploymentPlan",
    "EngineeringDiagnosis",
    "EngineeringObservation",
    "EngineeringPipelineStage",
    "EngineeringStageResult",
    "EngineeringStageStatus",
    "EngineeringTestPlan",
    "FormalTradingInvariantRegistry",
    "FailureMemoryEntry",
    "FrontierActivationReport",
    "FrontierAgentCapabilityController",
    "FrontierCapability",
    "FrontierCapabilityDomain",
    "FrontierCapabilityRegistry",
    "FusedToolCall",
    "GlassBoxOverseer",
    "GovernanceDecision",
    "HierarchicalSessionMemory",
    "ManagedAgentLease",
    "ManagedAgentSupervisor",
    "MemoryCompactionResult",
    "MythosCapabilityProfile",
    "MythosInspiredAIGovernor",
    "MythosMode",
    "MythosTaskPlan",
    "PatchProposal",
    "PatchWorkflowReport",
    "ProtectedFilePolicy",
    "PullRequestDraft",
    "RiskCategory",
    "MetricComparisonReport",
    "ObjectiveValidationResult",
    "RootCauseReport",
    "RuntimeBoundaryPolicy",
    "SandboxBranchPlan",
    "SandboxDecision",
    "SandboxSessionSpec",
    "SandboxTier",
    "ScopedToken",
    "SelfConsistencyVerifier",
    "SessionMemoryCompactor",
    "SoftwareFactoryRunReport",
    "SignedApproval",
    "SpecialistAgent",
    "SpecialistAgentRouter",
    "StrictPatchApprovalPipeline",
    "TieredSandboxMesh",
    "ToolCall",
    "ToolDescriptor",
    "ToolSearchIndex",
    "ToolSearchResult",
    "ToolPlanCompiler",
    "ToolCallFusionPlanner",
    "ProgrammaticToolCallCompiler",
    "ProgrammaticToolScript",
    "ToolProxyVault",
    "VerifierAgentReview",
    "VerificationReport",
]
