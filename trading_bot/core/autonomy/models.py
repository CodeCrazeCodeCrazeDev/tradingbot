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


class ArchitectureAttackVector(str, Enum):
    """Red-team attack vectors for architecture evolution proposals."""

    LIVE_MUTATION_BYPASS = "live_mutation_bypass"
    RISK_LIMIT_WEAKENING = "risk_limit_weakening"
    MODEL_MUTATION = "model_mutation"
    SELF_APPROVAL = "self_approval"
    HIDDEN_INVARIANT_BREAK = "hidden_invariant_break"
    TEST_OVERFITTING = "test_overfitting"
    COMPLEXITY_ACCUMULATION = "complexity_accumulation"
    PERFORMANCE_REGRESSION = "performance_regression"
    PROTECTED_FILE_WEAKENING = "protected_file_weakening"
    DEPLOYMENT_ROLLBACK_GAP = "deployment_rollback_gap"


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
class ArchitectureEvolutionCandidate:
    """One proposed architecture mutation evaluated only inside a sandbox."""

    candidate_id: str
    objective: str
    current_architecture: Dict[str, Any]
    proposed_change: str
    target_files: List[str]
    invariants: List[str] = field(default_factory=list)
    test_plan: Optional[EngineeringTestPlan] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    allow_live_mutation: bool = False
    allow_model_mutation: bool = False
    allow_risk_limit_change: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "objective": self.objective,
            "current_architecture": dict(self.current_architecture),
            "proposed_change": self.proposed_change,
            "target_files": list(self.target_files),
            "invariants": list(self.invariants),
            "test_plan": self.test_plan.to_dict() if self.test_plan else None,
            "evidence": dict(self.evidence),
            "allow_live_mutation": self.allow_live_mutation,
            "allow_model_mutation": self.allow_model_mutation,
            "allow_risk_limit_change": self.allow_risk_limit_change,
        }


@dataclass
class RedTeamArchitectureAttack:
    """Adversarial finding against an architecture-evolution candidate."""

    attack_id: str
    vector: ArchitectureAttackVector
    severity: RiskCategory
    finding: str
    exploit_path: List[str]
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["vector"] = self.vector.value
        data["severity"] = self.severity.value
        return data


@dataclass
class BlueTeamArchitectureDefense:
    """Defensive response generated by the blue team for one red-team attack."""

    defense_id: str
    attack_id: str
    control: str
    patch_strategy: str
    tests_added: List[str]
    governance_requirements: List[str]
    resolved: bool
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RedBlueArchitectureRound:
    """One red-vs-blue simulation round over the same candidate."""

    round_id: str
    red_attacks: List[RedTeamArchitectureAttack]
    blue_defenses: List[BlueTeamArchitectureDefense]
    unresolved_attacks: List[RedTeamArchitectureAttack]
    accepted: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_id": self.round_id,
            "red_attacks": [attack.to_dict() for attack in self.red_attacks],
            "blue_defenses": [defense.to_dict() for defense in self.blue_defenses],
            "unresolved_attacks": [attack.to_dict() for attack in self.unresolved_attacks],
            "accepted": self.accepted,
        }


@dataclass
class RedBlueArchitectureEvolutionReport:
    """Complete sandboxed architecture-evolution competition report."""

    run_id: str
    candidate: ArchitectureEvolutionCandidate
    rounds: List[RedBlueArchitectureRound]
    sandbox_session: SandboxSessionSpec
    sandbox_branch: SandboxBranchPlan
    runtime_policy: RuntimeBoundaryPolicy
    governance: GovernanceDecision
    protected_file_report: VerificationReport
    complexity_budget: ComplexityBudget
    metric_comparison: MetricComparisonReport
    reviewer_report: VerificationReport
    deployment_plan: DeploymentPlan
    final_decision: ApprovalState
    blocked_reasons: List[str]
    provenance: DecisionProvenanceTrace

    @property
    def accepted(self) -> bool:
        return self.final_decision == ApprovalState.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "candidate": self.candidate.to_dict(),
            "rounds": [round_.to_dict() for round_ in self.rounds],
            "sandbox_session": self.sandbox_session.to_dict(),
            "sandbox_branch": self.sandbox_branch.to_dict(),
            "runtime_policy": self.runtime_policy.to_dict(),
            "governance": self.governance.to_dict(),
            "protected_file_report": self.protected_file_report.to_dict(),
            "complexity_budget": self.complexity_budget.to_dict(),
            "metric_comparison": self.metric_comparison.to_dict(),
            "reviewer_report": self.reviewer_report.to_dict(),
            "deployment_plan": self.deployment_plan.to_dict(),
            "final_decision": self.final_decision.value,
            "blocked_reasons": list(self.blocked_reasons),
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
