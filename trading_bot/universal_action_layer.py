"""Universal Action Layer (Claw).

Claw is the controlled execution side of AlphaAlgo:

    swarm generates ideas -> governance selects -> claw executes -> feedback returns

It can orchestrate digital tools at scale, but only for validated decisions.
The default stance is deny. Every action needs a governance receipt, a registered
adapter, budget/risk checks, execution limits, and an audit trail.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Protocol, Sequence, Tuple

from trading_bot.golden_path.agent_trap_defense import AgentTrapScanner


def _utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _parse_timestamp(value: str) -> datetime:
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class ActionType(str, Enum):
    COMMAND = "command"
    API_CALL = "api_call"
    TOOL_CALL = "tool_call"
    WORKFLOW = "workflow"


class ActionRiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    REJECTED = "rejected"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ActionIntent:
    intent_id: str
    action_type: ActionType
    target: str
    operation: str
    payload: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    risk_tier: ActionRiskTier = ActionRiskTier.LOW
    expected_cost_usd: float = 0.0
    timeout_seconds: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        action_type: ActionType,
        target: str,
        operation: str,
        payload: Optional[Dict[str, Any]] = None,
        rationale: str = "",
        risk_tier: ActionRiskTier = ActionRiskTier.LOW,
        expected_cost_usd: float = 0.0,
        timeout_seconds: float = 30.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ActionIntent":
        return cls(
            intent_id=f"act_{uuid.uuid4().hex[:12]}",
            action_type=action_type,
            target=target,
            operation=operation,
            payload=payload or {},
            rationale=rationale,
            risk_tier=risk_tier,
            expected_cost_usd=expected_cost_usd,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {},
        )


@dataclass(frozen=True)
class DecisionConstraints:
    max_cost_usd: float = 0.0
    max_latency_ms: int = 5_000
    required_safety_level: str = "sandbox"
    allowed_networks: Sequence[str] = ("internal",)
    expires_at: Optional[str] = None
    force: bool = False


@dataclass(frozen=True)
class GovernanceSignature:
    signer: str
    signature: str
    signed_at: str
    algorithm: str = "hmac-sha256"


@dataclass(frozen=True)
class DecisionBundle:
    decision_id: str
    origin: str
    action_type: str
    target_system: str
    parameters: Dict[str, Any]
    constraints: DecisionConstraints
    governance_signature: GovernanceSignature
    rollback_instruction: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=_utc)
    context: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DecisionBundle":
        constraints = data.get("constraints", {})
        signature = data.get("governance_signature", {})
        return cls(
            decision_id=str(data["decision_id"]),
            origin=str(data["origin"]),
            action_type=str(data["action_type"]),
            target_system=str(data["target_system"]),
            parameters=dict(data.get("parameters", {})),
            constraints=DecisionConstraints(**constraints),
            governance_signature=GovernanceSignature(**signature),
            rollback_instruction=data.get("rollback_instruction"),
            timestamp=str(data.get("timestamp", _utc())),
            context=dict(data.get("context", {})),
        )


@dataclass(frozen=True)
class FeedbackReport:
    decision_id: str
    execution_status: ExecutionStatus
    result: Dict[str, Any]
    metrics: Dict[str, Any]
    risk_observations: List[str]
    environment_state_snapshot: Dict[str, Any]
    timestamp: str = field(default_factory=_utc)


@dataclass(frozen=True)
class GovernanceReceipt:
    receipt_id: str
    intent_id: str
    approved: bool
    approver: str
    reason: str
    allowed_adapter: str
    max_cost_usd: float
    max_runtime_seconds: float
    autonomy_level: str = "supervised"
    issued_at: str = field(default_factory=_utc)
    expires_at: Optional[str] = None


@dataclass(frozen=True)
class ActionPolicy:
    monthly_budget_usd: float = 100.0
    max_action_cost_usd: float = 5.0
    max_runtime_seconds: float = 120.0
    allow_continuous_operation: bool = False
    allow_high_risk_without_human: bool = False
    sandbox_required: bool = True
    sandbox_available: bool = True
    governance_signature_secret: str = ""
    signature_max_age_seconds: int = 300
    feedback_bus_path: str = "audit_logs/universal_action_feedback.jsonl"
    allowed_command_prefixes: Sequence[Sequence[str]] = (
        ("git", "status"),
        ("git", "diff"),
        ("py", "-m", "pytest"),
        ("py", "-m", "py_compile"),
    )
    blocked_command_tokens: Sequence[str] = (
        "rm",
        "del",
        "erase",
        "format",
        "shutdown",
        "restart",
        "curl",
        "wget",
        "scp",
        "ssh",
        "Remove-Item",
        "Invoke-Expression",
    )


@dataclass(frozen=True)
class ActionResult:
    intent_id: str
    status: ActionStatus
    adapter_name: str
    started_at: str
    finished_at: str
    latency_ms: float
    cost_usd: float
    output: Any = None
    error: Optional[str] = None
    feedback: Dict[str, Any] = field(default_factory=dict)


class DecisionAdapter(Protocol):
    name: str

    def supports_bundle(self, decision: DecisionBundle) -> bool:
        ...

    def execute_bundle(self, decision: DecisionBundle, policy: ActionPolicy) -> ActionResult:
        ...


class ActionAdapter(Protocol):
    name: str

    def supports(self, intent: ActionIntent) -> bool:
        ...

    def execute(self, intent: ActionIntent, policy: ActionPolicy) -> ActionResult:
        ...


class CommandActionAdapter:
    """Restricted command adapter for approved local commands."""

    name = "command"

    def __init__(self, cwd: Optional[str] = None) -> None:
        self.cwd = cwd

    def supports(self, intent: ActionIntent) -> bool:
        return intent.action_type == ActionType.COMMAND

    def supports_bundle(self, decision: DecisionBundle) -> bool:
        return decision.target_system == "shell"

    def execute_bundle(self, decision: DecisionBundle, policy: ActionPolicy) -> ActionResult:
        intent = ActionIntent.create(
            action_type=ActionType.COMMAND,
            target=decision.target_system,
            operation=decision.action_type,
            payload={"argv": decision.parameters.get("command", decision.parameters.get("argv"))},
            rationale=f"governed decision {decision.decision_id}",
            expected_cost_usd=decision.constraints.max_cost_usd,
            timeout_seconds=decision.constraints.max_latency_ms / 1000,
            metadata={"decision_id": decision.decision_id},
        )
        return self.execute(intent, policy)

    def execute(self, intent: ActionIntent, policy: ActionPolicy) -> ActionResult:
        started = time.perf_counter()
        started_at = _utc()
        command = intent.payload.get("argv")
        if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
            return self._result(intent, started, started_at, ActionStatus.FAILED, error="payload.argv must be a string list")
        if not self._command_allowed(command, policy):
            return self._result(intent, started, started_at, ActionStatus.BLOCKED, error="command blocked by policy")

        try:
            completed = subprocess.run(
                command,
                cwd=self.cwd,
                text=True,
                capture_output=True,
                timeout=min(intent.timeout_seconds, policy.max_runtime_seconds),
                check=False,
            )
        except Exception as exc:
            return self._result(intent, started, started_at, ActionStatus.FAILED, error=str(exc))

        output = {
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
        status = ActionStatus.EXECUTED if completed.returncode == 0 else ActionStatus.FAILED
        return self._result(intent, started, started_at, status, output=output)

    def _command_allowed(self, command: Sequence[str], policy: ActionPolicy) -> bool:
        if any(token in command for token in policy.blocked_command_tokens):
            return False
        for prefix in policy.allowed_command_prefixes:
            if tuple(command[: len(prefix)]) == tuple(prefix):
                return True
        return False

    def _result(
        self,
        intent: ActionIntent,
        started: float,
        started_at: str,
        status: ActionStatus,
        *,
        output: Any = None,
        error: Optional[str] = None,
    ) -> ActionResult:
        return ActionResult(
            intent_id=intent.intent_id,
            status=status,
            adapter_name=self.name,
            started_at=started_at,
            finished_at=_utc(),
            latency_ms=(time.perf_counter() - started) * 1000,
            cost_usd=intent.expected_cost_usd,
            output=output,
            error=error,
            feedback={"success": status == ActionStatus.EXECUTED},
        )


class FunctionActionAdapter:
    """Adapter for registered in-process tools and APIs."""

    def __init__(self, name: str, action_type: ActionType, handler: Callable[[ActionIntent], Any]) -> None:
        self.name = name
        self.action_type = action_type
        self.handler = handler

    def supports(self, intent: ActionIntent) -> bool:
        return intent.action_type == self.action_type and intent.target == self.name

    def supports_bundle(self, decision: DecisionBundle) -> bool:
        return decision.target_system == self.name

    def execute_bundle(self, decision: DecisionBundle, policy: ActionPolicy) -> ActionResult:
        intent = ActionIntent.create(
            action_type=self.action_type,
            target=decision.target_system,
            operation=decision.action_type,
            payload=decision.parameters,
            rationale=f"governed decision {decision.decision_id}",
            expected_cost_usd=decision.constraints.max_cost_usd,
            timeout_seconds=decision.constraints.max_latency_ms / 1000,
            metadata={"decision_id": decision.decision_id, **decision.context},
        )
        return self.execute(intent, policy)

    def execute(self, intent: ActionIntent, policy: ActionPolicy) -> ActionResult:
        started = time.perf_counter()
        started_at = _utc()
        try:
            output = self.handler(intent)
            status = ActionStatus.EXECUTED
            error = None
        except Exception as exc:
            output = None
            status = ActionStatus.FAILED
            error = str(exc)
        return ActionResult(
            intent_id=intent.intent_id,
            status=status,
            adapter_name=self.name,
            started_at=started_at,
            finished_at=_utc(),
            latency_ms=(time.perf_counter() - started) * 1000,
            cost_usd=intent.expected_cost_usd,
            output=output,
            error=error,
            feedback={"success": status == ActionStatus.EXECUTED},
        )


class WorkflowActionAdapter:
    """Adapter that executes a sequence of already-approved child intents."""

    name = "workflow"

    def __init__(self, engine: "UniversalActionLayer") -> None:
        self.engine = engine

    def supports(self, intent: ActionIntent) -> bool:
        return intent.action_type == ActionType.WORKFLOW

    def supports_bundle(self, decision: DecisionBundle) -> bool:
        return decision.target_system == "workflow"

    def execute_bundle(self, decision: DecisionBundle, policy: ActionPolicy) -> ActionResult:
        intent = ActionIntent.create(
            action_type=ActionType.WORKFLOW,
            target="workflow",
            operation=decision.action_type,
            payload={"steps": decision.parameters.get("steps", [])},
            rationale=f"governed decision {decision.decision_id}",
            expected_cost_usd=decision.constraints.max_cost_usd,
            timeout_seconds=decision.constraints.max_latency_ms / 1000,
            metadata={"decision_id": decision.decision_id, **decision.context},
        )
        return self.execute(intent, policy)

    def execute(self, intent: ActionIntent, policy: ActionPolicy) -> ActionResult:
        started = time.perf_counter()
        started_at = _utc()
        steps = intent.payload.get("steps", [])
        if not isinstance(steps, list):
            return self._result(intent, started, started_at, ActionStatus.FAILED, error="workflow steps must be a list")

        outputs = []
        for step in steps:
            if not isinstance(step, Mapping):
                return self._result(intent, started, started_at, ActionStatus.FAILED, error="workflow step must be a mapping")
            child = ActionIntent.create(
                action_type=ActionType(step["action_type"]),
                target=str(step["target"]),
                operation=str(step["operation"]),
                payload=dict(step.get("payload", {})),
                rationale=str(step.get("rationale", intent.rationale)),
                risk_tier=ActionRiskTier(step.get("risk_tier", intent.risk_tier.value)),
                expected_cost_usd=float(step.get("expected_cost_usd", 0.0)),
                timeout_seconds=float(step.get("timeout_seconds", intent.timeout_seconds)),
                metadata=dict(step.get("metadata", {})),
            )
            receipt = GovernanceReceipt(
                receipt_id=f"rcpt_{uuid.uuid4().hex[:12]}",
                intent_id=child.intent_id,
                approved=True,
                approver="workflow_parent",
                reason=f"approved child of workflow {intent.intent_id}",
                allowed_adapter=str(step.get("allowed_adapter", child.target if child.action_type != ActionType.COMMAND else "command")),
                max_cost_usd=min(policy.max_action_cost_usd, float(step.get("max_cost_usd", policy.max_action_cost_usd))),
                max_runtime_seconds=min(policy.max_runtime_seconds, child.timeout_seconds),
                autonomy_level="workflow_child",
            )
            result = self.engine.execute(child, receipt)
            outputs.append(asdict(result))
            if result.status != ActionStatus.EXECUTED:
                return self._result(intent, started, started_at, ActionStatus.FAILED, output=outputs, error="workflow child failed")

        return self._result(intent, started, started_at, ActionStatus.EXECUTED, output=outputs)

    def _result(
        self,
        intent: ActionIntent,
        started: float,
        started_at: str,
        status: ActionStatus,
        *,
        output: Any = None,
        error: Optional[str] = None,
    ) -> ActionResult:
        return ActionResult(
            intent_id=intent.intent_id,
            status=status,
            adapter_name=self.name,
            started_at=started_at,
            finished_at=_utc(),
            latency_ms=(time.perf_counter() - started) * 1000,
            cost_usd=intent.expected_cost_usd,
            output=output,
            error=error,
            feedback={"success": status == ActionStatus.EXECUTED},
        )


class UniversalActionLayer:
    """Governed universal execution engine for validated digital actions."""

    def __init__(
        self,
        *,
        policy: Optional[ActionPolicy] = None,
        audit_log_path: str = "audit_logs/universal_action_layer.jsonl",
        trap_scanner: Optional[AgentTrapScanner] = None,
    ) -> None:
        self.policy = policy or ActionPolicy()
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_bus_path = Path(self.policy.feedback_bus_path)
        self.feedback_bus_path.parent.mkdir(parents=True, exist_ok=True)
        self.trap_scanner = trap_scanner or AgentTrapScanner()
        self.adapters: List[ActionAdapter] = []
        self.feedback_events: List[Dict[str, Any]] = []
        self.decision_cache: Dict[str, FeedbackReport] = {}
        self.metrics = {
            "decisions_received": 0,
            "decisions_executed": 0,
            "decisions_failed": 0,
            "decisions_rejected": 0,
            "feedback_emitted": 0,
            "rollbacks_executed": 0,
            "active_sandboxes": 0,
            "latencies_ms": [],
        }
        self.spent_usd = 0.0
        self.kill_switch_active = False
        self.register_adapter(WorkflowActionAdapter(self))

    def register_adapter(self, adapter: ActionAdapter) -> None:
        self.adapters.append(adapter)

    def register_function_tool(self, name: str, handler: Callable[[ActionIntent], Any]) -> None:
        self.register_adapter(FunctionActionAdapter(name, ActionType.TOOL_CALL, handler))

    def register_api(self, name: str, handler: Callable[[ActionIntent], Any]) -> None:
        self.register_adapter(FunctionActionAdapter(name, ActionType.API_CALL, handler))

    def execute(self, intent: ActionIntent, receipt: GovernanceReceipt) -> ActionResult:
        validation_error = self._validate_before_execution(intent, receipt)
        if validation_error:
            result = ActionResult(
                intent_id=intent.intent_id,
                status=ActionStatus.BLOCKED,
                adapter_name=receipt.allowed_adapter or "none",
                started_at=_utc(),
                finished_at=_utc(),
                latency_ms=0.0,
                cost_usd=0.0,
                error=validation_error,
                feedback={"success": False, "blocked": True},
            )
            self._record(intent, receipt, result)
            return result

        adapter = self._select_adapter(intent, receipt)
        if not adapter:
            result = ActionResult(
                intent_id=intent.intent_id,
                status=ActionStatus.BLOCKED,
                adapter_name=receipt.allowed_adapter or "none",
                started_at=_utc(),
                finished_at=_utc(),
                latency_ms=0.0,
                cost_usd=0.0,
                error="no adapter matched approved action",
                feedback={"success": False, "blocked": True},
            )
            self._record(intent, receipt, result)
            return result

        result = adapter.execute(intent, self.policy)
        self.spent_usd += result.cost_usd
        self._record(intent, receipt, result)
        return result

    def execute_decision_bundle(self, decision: DecisionBundle) -> FeedbackReport:
        """Primary wire contract: execute a Governance Decision Bundle."""

        self.metrics["decisions_received"] += 1
        if decision.decision_id in self.decision_cache and not decision.constraints.force:
            return self.decision_cache[decision.decision_id]

        validation_error = self._validate_decision_bundle(decision)
        if validation_error:
            feedback = self._feedback_from_error(decision, validation_error, ExecutionStatus.REJECTED)
            self.metrics["decisions_rejected"] += 1
            self._emit_feedback(feedback, decision)
            self.decision_cache[decision.decision_id] = feedback
            return feedback

        adapter = self._select_decision_adapter(decision)
        if not adapter:
            feedback = self._feedback_from_error(decision, "no installed adapter supports decision", ExecutionStatus.REJECTED)
            self.metrics["decisions_rejected"] += 1
            self._emit_feedback(feedback, decision)
            self.decision_cache[decision.decision_id] = feedback
            return feedback

        self.metrics["active_sandboxes"] += 1
        result = adapter.execute_bundle(decision, self.policy)  # type: ignore[attr-defined]
        self.metrics["active_sandboxes"] -= 1
        self.spent_usd += result.cost_usd

        status = ExecutionStatus.SUCCESS if result.status == ActionStatus.EXECUTED else ExecutionStatus.FAILED
        if status == ExecutionStatus.SUCCESS:
            self.metrics["decisions_executed"] += 1
        else:
            self.metrics["decisions_failed"] += 1

        self.metrics["latencies_ms"].append(result.latency_ms)
        feedback = self._feedback_from_result(decision, result, status)
        self._emit_feedback(feedback, decision)
        self.decision_cache[decision.decision_id] = feedback

        if status == ExecutionStatus.FAILED and decision.rollback_instruction:
            rollback_feedback = self._execute_rollback(decision)
            feedback.result["rollback"] = asdict(rollback_feedback)

        return feedback

    def run_swarm_governance_claw_cycle(
        self,
        *,
        ideas: Iterable[ActionIntent],
        governance_selector: Callable[[ActionIntent], GovernanceReceipt],
    ) -> Dict[str, Any]:
        results = []
        for idea in ideas:
            receipt = governance_selector(idea)
            results.append(asdict(self.execute(idea, receipt)))
        return {
            "timestamp": _utc(),
            "flow": "swarm_generates -> governance_selects -> claw_executes -> feedback_returns",
            "results": results,
            "feedback": list(self.feedback_events),
        }

    def dashboard_snapshot(self) -> Dict[str, Any]:
        latencies = self.metrics["latencies_ms"]
        mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
        adapter_status = {
            adapter.name: "healthy" for adapter in self.adapters
        }
        return {
            "timestamp": _utc(),
            "decisions_received": self.metrics["decisions_received"],
            "decisions_executed": self.metrics["decisions_executed"],
            "decisions_failed": self.metrics["decisions_failed"],
            "decisions_rejected": self.metrics["decisions_rejected"],
            "mean_latency_ms": round(mean_latency, 3),
            "total_cost_usd": round(self.spent_usd, 6),
            "active_sandboxes": self.metrics["active_sandboxes"],
            "adapter_status": adapter_status,
            "feedback_emitted": self.metrics["feedback_emitted"],
            "rollbacks_executed": self.metrics["rollbacks_executed"],
        }

    def _validate_decision_bundle(self, decision: DecisionBundle) -> Optional[str]:
        if self.kill_switch_active:
            return "kill switch active"
        if not self._is_fully_parameterized(decision):
            return "decision contains non-parameterized choice language"
        if self.policy.sandbox_required and not self.policy.sandbox_available:
            return "sandbox unavailable"
        if decision.constraints.required_safety_level == "sandbox" and not self.policy.sandbox_available:
            return "required sandbox unavailable"
        if decision.constraints.max_cost_usd > self.policy.max_action_cost_usd:
            return "decision max_cost_usd exceeds policy"
        if self.spent_usd + decision.constraints.max_cost_usd > self.policy.monthly_budget_usd:
            return "monthly action budget exceeded"
        if decision.constraints.max_latency_ms > self.policy.max_runtime_seconds * 1000:
            return "decision latency exceeds policy"
        if not self._signature_valid(decision):
            return "invalid governance signature"
        if decision.constraints.expires_at:
            try:
                if _parse_timestamp(decision.constraints.expires_at) < datetime.now(timezone.utc):
                    return "decision expired"
            except ValueError:
                return "invalid expiration timestamp"
        trap_report = self.trap_scanner.scan_mapping(
            {
                "parameters": decision.parameters,
                "context": decision.context,
                "rollback_instruction": decision.rollback_instruction or {},
            },
            source_prefix=f"decision.{decision.decision_id}",
        )
        if trap_report.blocked:
            return f"agent trap defense blocked decision: risk_score={trap_report.risk_score}"
        return None

    def _signature_valid(self, decision: DecisionBundle) -> bool:
        if not self.policy.governance_signature_secret:
            return bool(decision.governance_signature.signature)
        try:
            signed_at = _parse_timestamp(decision.governance_signature.signed_at)
        except ValueError:
            return False
        age = (datetime.now(timezone.utc) - signed_at).total_seconds()
        if age > self.policy.signature_max_age_seconds:
            return False
        expected = sign_decision_bundle(decision, self.policy.governance_signature_secret)
        return hmac.compare_digest(expected, decision.governance_signature.signature)

    def _is_fully_parameterized(self, decision: DecisionBundle) -> bool:
        blob = json.dumps(decision.parameters, sort_keys=True).lower()
        choice_markers = (
            "which stock",
            "choose a stock",
            "decide whether",
            "pick one",
            "select best",
            "what should",
        )
        return not any(marker in blob for marker in choice_markers)

    def _select_decision_adapter(self, decision: DecisionBundle) -> Optional[ActionAdapter]:
        for adapter in self.adapters:
            supports = getattr(adapter, "supports_bundle", None)
            if callable(supports) and supports(decision):
                return adapter
        return None

    def _feedback_from_result(
        self,
        decision: DecisionBundle,
        result: ActionResult,
        status: ExecutionStatus,
    ) -> FeedbackReport:
        risk_observations = ["no_anomaly"] if status == ExecutionStatus.SUCCESS else ["execution_failure"]
        return FeedbackReport(
            decision_id=decision.decision_id,
            execution_status=status,
            result={
                "data": result.output if status == ExecutionStatus.SUCCESS else {},
                "error": {"message": result.error, "adapter": result.adapter_name} if result.error else {},
            },
            metrics={
                "actual_cost_usd": result.cost_usd,
                "latency_ms": result.latency_ms,
                "compute_units": 1,
                "api_calls_made": 1,
            },
            risk_observations=risk_observations,
            environment_state_snapshot={
                "system": decision.target_system,
                "adapter": result.adapter_name,
            },
        )

    def _feedback_from_error(
        self,
        decision: DecisionBundle,
        error: str,
        status: ExecutionStatus,
    ) -> FeedbackReport:
        return FeedbackReport(
            decision_id=decision.decision_id,
            execution_status=status,
            result={"data": {}, "error": {"message": error}},
            metrics={
                "actual_cost_usd": 0.0,
                "latency_ms": 0.0,
                "compute_units": 0,
                "api_calls_made": 0,
            },
            risk_observations=["rejected_before_execution"],
            environment_state_snapshot={"system": decision.target_system},
        )

    def _emit_feedback(self, feedback: FeedbackReport, decision: DecisionBundle) -> None:
        self.metrics["feedback_emitted"] += 1
        self.feedback_events.append(asdict(feedback))
        event = {
            "timestamp": _utc(),
            "decision": asdict(decision),
            "feedback": asdict(feedback),
        }
        with self.feedback_bus_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(feedback), default=str, sort_keys=True) + "\n")
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=str, sort_keys=True) + "\n")

    def _execute_rollback(self, decision: DecisionBundle) -> FeedbackReport:
        rollback = dict(decision.rollback_instruction or {})
        rollback_decision = DecisionBundle(
            decision_id=f"{decision.decision_id}:rollback",
            origin="universal_action_layer",
            action_type=str(rollback.get("action_type", decision.action_type)),
            target_system=str(rollback.get("target_system", decision.target_system)),
            parameters=dict(rollback.get("parameters", {})),
            constraints=DecisionConstraints(
                max_cost_usd=decision.constraints.max_cost_usd,
                max_latency_ms=decision.constraints.max_latency_ms,
                required_safety_level=decision.constraints.required_safety_level,
                allowed_networks=decision.constraints.allowed_networks,
                force=True,
            ),
            governance_signature=decision.governance_signature,
            timestamp=_utc(),
            context={"rollback_for": decision.decision_id},
        )
        self.metrics["rollbacks_executed"] += 1
        return self.execute_decision_bundle(rollback_decision)

    def _validate_before_execution(self, intent: ActionIntent, receipt: GovernanceReceipt) -> Optional[str]:
        if self.kill_switch_active:
            return "kill switch active"
        if not receipt.approved:
            return f"governance rejected action: {receipt.reason}"
        if receipt.intent_id != intent.intent_id:
            return "governance receipt does not match intent"
        if intent.expected_cost_usd > min(receipt.max_cost_usd, self.policy.max_action_cost_usd):
            return "action cost exceeds receipt or policy limit"
        if self.spent_usd + intent.expected_cost_usd > self.policy.monthly_budget_usd:
            return "monthly action budget exceeded"
        if intent.timeout_seconds > min(receipt.max_runtime_seconds, self.policy.max_runtime_seconds):
            return "action timeout exceeds receipt or policy limit"
        if intent.risk_tier in {ActionRiskTier.HIGH, ActionRiskTier.CRITICAL} and not self.policy.allow_high_risk_without_human:
            if receipt.autonomy_level != "human_approved":
                return "high-risk action requires human-approved receipt"

        trap_report = self.trap_scanner.scan_mapping(
            {"payload": intent.payload, "metadata": intent.metadata, "rationale": intent.rationale},
            source_prefix=f"action.{intent.intent_id}",
        )
        if trap_report.blocked:
            return f"agent trap defense blocked action context: risk_score={trap_report.risk_score}"
        return None

    def _select_adapter(self, intent: ActionIntent, receipt: GovernanceReceipt) -> Optional[ActionAdapter]:
        for adapter in self.adapters:
            if adapter.name == receipt.allowed_adapter and adapter.supports(intent):
                return adapter
        return None

    def _record(self, intent: ActionIntent, receipt: GovernanceReceipt, result: ActionResult) -> None:
        event = {
            "timestamp": _utc(),
            "intent": asdict(intent),
            "receipt": asdict(receipt),
            "result": asdict(result),
        }
        self.feedback_events.append(
            {
                "timestamp": event["timestamp"],
                "intent_id": intent.intent_id,
                "status": result.status.value,
                "success": result.status == ActionStatus.EXECUTED,
                "cost_usd": result.cost_usd,
                "latency_ms": result.latency_ms,
                "error": result.error,
            }
        )
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=str, sort_keys=True) + "\n")


def create_universal_action_layer(
    *,
    policy: Optional[ActionPolicy] = None,
    audit_log_path: str = "audit_logs/universal_action_layer.jsonl",
) -> UniversalActionLayer:
    return UniversalActionLayer(policy=policy, audit_log_path=audit_log_path)


def canonical_decision_payload(decision: DecisionBundle) -> str:
    data = {
        "decision_id": decision.decision_id,
        "origin": decision.origin,
        "action_type": decision.action_type,
        "target_system": decision.target_system,
        "parameters": decision.parameters,
        "constraints": asdict(decision.constraints),
        "rollback_instruction": decision.rollback_instruction,
        "timestamp": decision.timestamp,
        "context": decision.context,
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def sign_decision_bundle(decision: DecisionBundle, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        canonical_decision_payload(decision).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
