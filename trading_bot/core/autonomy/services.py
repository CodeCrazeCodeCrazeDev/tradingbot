from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence
from .models import *

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


class ArchitectureRedTeamAgent:
    """Attacker agent that tries to break architecture-evolution proposals."""

    def attack(
        self,
        candidate: ArchitectureEvolutionCandidate,
        protected_file_report: VerificationReport,
        complexity_budget: ComplexityBudget,
        metric_comparison: MetricComparisonReport,
    ) -> List[RedTeamArchitectureAttack]:
        text = f"{candidate.objective} {candidate.proposed_change}".lower()
        attacks: List[RedTeamArchitectureAttack] = []

        if candidate.allow_live_mutation or any(token in text for token in ("live code", "modify live", "production self-edit", "direct production")):
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.LIVE_MUTATION_BYPASS,
                RiskCategory.CRITICAL,
                "candidate creates a path for architecture evolution to mutate live trading code",
                ["architecture_evolution", "live_runtime", "code_mutation"],
            ))
        if candidate.allow_risk_limit_change or ("risk limit" in text and any(token in text for token in ("change", "raise", "lower", "modify", "bypass"))):
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.RISK_LIMIT_WEAKENING,
                RiskCategory.CRITICAL,
                "candidate may let the evolving system change risk limits",
                ["architecture_evolution", "risk_controls", "limit_mutation"],
            ))
        if candidate.allow_model_mutation or any(token in text for token in ("model mutation", "mutate model", "self-train production", "rewrite weights")):
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.MODEL_MUTATION,
                RiskCategory.CRITICAL,
                "candidate may mutate production model behavior outside the sandbox",
                ["architecture_evolution", "model_registry", "live_model_mutation"],
            ))
        if any(token in text for token in ("self approve", "self-approve", "approve its own", "auto approve")):
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.SELF_APPROVAL,
                RiskCategory.CRITICAL,
                "candidate may let an AI approve its own architecture change",
                ["architecture_evolution", "governance", "self_approval"],
            ))
        if not candidate.invariants:
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.HIDDEN_INVARIANT_BREAK,
                RiskCategory.HIGH,
                "candidate lacks invariant tests for hidden production assumptions",
                ["candidate_patch", "missing_invariants", "hidden_assumption_break"],
            ))
        if not candidate.test_plan or not candidate.test_plan.hidden_tests or not candidate.test_plan.adversarial_tests:
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.TEST_OVERFITTING,
                RiskCategory.HIGH,
                "candidate can optimize for visible tests instead of correctness",
                ["candidate_patch", "visible_tests_only", "test_overfit"],
            ))
        if not complexity_budget.accepted:
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.COMPLEXITY_ACCUMULATION,
                RiskCategory.HIGH,
                "candidate exceeds the architecture complexity budget",
                ["candidate_patch", "complexity_growth", "maintenance_risk"],
                complexity_budget.notes,
            ))
        if not candidate.test_plan or not candidate.test_plan.performance_benchmarks or not metric_comparison.accepted:
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.PERFORMANCE_REGRESSION,
                RiskCategory.HIGH if metric_comparison.regressions else RiskCategory.MEDIUM,
                "candidate lacks convincing performance-regression evidence",
                ["candidate_patch", "benchmark_gap", "runtime_regression"],
                metric_comparison.regressions,
            ))
        if not protected_file_report.accepted:
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.PROTECTED_FILE_WEAKENING,
                RiskCategory.CRITICAL,
                "candidate touches protected safety, risk, governance, or broker files without approval",
                ["candidate_patch", "protected_file", "silent_guardrail_weakening"],
                protected_file_report.verifier_notes,
            ))
        if not candidate.evidence.get("rollback_plan"):
            attacks.append(self._attack(
                candidate,
                ArchitectureAttackVector.DEPLOYMENT_ROLLBACK_GAP,
                RiskCategory.HIGH,
                "candidate has no rollback plan for failed architecture evolution",
                ["candidate_patch", "deployment", "rollback_missing"],
            ))
        return attacks

    def _attack(
        self,
        candidate: ArchitectureEvolutionCandidate,
        vector: ArchitectureAttackVector,
        severity: RiskCategory,
        finding: str,
        exploit_path: List[str],
        extra_evidence: Optional[Sequence[str]] = None,
    ) -> RedTeamArchitectureAttack:
        evidence = [candidate.candidate_id, vector.value]
        evidence.extend(str(item) for item in extra_evidence or [])
        attack_id = hashlib.sha256(f"{candidate.candidate_id}:{vector.value}:{finding}".encode("utf-8")).hexdigest()[:16]
        return RedTeamArchitectureAttack(attack_id, vector, severity, finding, exploit_path, evidence)


class ArchitectureBlueTeamAgent:
    """Defender agent that turns red-team findings into controlled defenses."""

    def defend(
        self,
        candidate: ArchitectureEvolutionCandidate,
        attacks: Sequence[RedTeamArchitectureAttack],
        metric_comparison: MetricComparisonReport,
    ) -> List[BlueTeamArchitectureDefense]:
        return [self._defense(candidate, attack, metric_comparison) for attack in attacks]

    def _defense(
        self,
        candidate: ArchitectureEvolutionCandidate,
        attack: RedTeamArchitectureAttack,
        metric_comparison: MetricComparisonReport,
    ) -> BlueTeamArchitectureDefense:
        tests_added: List[str] = []
        requirements = ["signed_approval", "pull_request_review"]
        notes: List[str] = []
        resolved = False
        control = "governance gate"
        patch_strategy = "block candidate until evidence is supplied"

        if attack.vector == ArchitectureAttackVector.HIDDEN_INVARIANT_BREAK:
            control = "generated invariant tests"
            patch_strategy = "add invariant tests before patch proposal can advance"
            tests_added = [
                "invariant: production runtime remains separate from architecture evolution",
                "invariant: risk limits cannot be changed by evolving agents",
                "invariant: model mutation remains sandbox-only",
            ]
            resolved = True
        elif attack.vector == ArchitectureAttackVector.TEST_OVERFITTING:
            control = "hidden and adversarial test harness"
            patch_strategy = "add hidden tests and adversarial architecture probes"
            tests_added = [
                "hidden: unseen architecture snapshot keeps governance boundary",
                "adversarial: red-team bypass attempt cannot reach live runtime",
            ]
            resolved = True
        elif attack.vector == ArchitectureAttackVector.PERFORMANCE_REGRESSION:
            control = "performance regression gate"
            patch_strategy = "require before/after benchmark evidence before rollout"
            tests_added = ["benchmark: architecture simulation p95 latency and decision cost"]
            resolved = bool(metric_comparison.before and metric_comparison.after and metric_comparison.accepted)
            if not resolved:
                notes.extend(metric_comparison.regressions or ["before/after benchmark evidence missing"])
        elif attack.vector == ArchitectureAttackVector.DEPLOYMENT_ROLLBACK_GAP:
            control = "rollback gate"
            patch_strategy = "require rollback trigger and paper-trading exit plan"
            requirements.append("rollback_plan")
            resolved = bool(candidate.evidence.get("rollback_plan"))
            if not resolved:
                notes.append("rollback_plan evidence missing")
        elif attack.vector == ArchitectureAttackVector.COMPLEXITY_ACCUMULATION:
            control = "complexity budget"
            patch_strategy = "delete or simplify architecture before adding new layers"
            requirements.append("complexity_budget_approval")
            notes.extend(attack.evidence_ids[2:])
        elif attack.vector == ArchitectureAttackVector.PROTECTED_FILE_WEAKENING:
            control = "protected file policy"
            patch_strategy = "require explicit protected-file approval and independent safety review"
            requirements.append("protected_file_approval")
            resolved = bool(candidate.evidence.get("protected_file_approval"))
            if not resolved:
                notes.extend(attack.evidence_ids[2:] or ["protected_file_approval evidence missing"])
        elif attack.vector in {
            ArchitectureAttackVector.LIVE_MUTATION_BYPASS,
            ArchitectureAttackVector.RISK_LIMIT_WEAKENING,
            ArchitectureAttackVector.MODEL_MUTATION,
            ArchitectureAttackVector.SELF_APPROVAL,
        }:
            control = "hard safety boundary"
            patch_strategy = "reject candidate and require a sandbox-only redesign"
            requirements.extend(["human_security_review", "governance_rejection_record"])
            notes.append("hard boundary violations are not auto-resolved by blue-team patching")

        defense_id = hashlib.sha256(f"{attack.attack_id}:{control}:{resolved}".encode("utf-8")).hexdigest()[:16]
        return BlueTeamArchitectureDefense(
            defense_id=defense_id,
            attack_id=attack.attack_id,
            control=control,
            patch_strategy=patch_strategy,
            tests_added=tests_added,
            governance_requirements=requirements,
            resolved=resolved,
            notes=notes,
        )


class RedBlueArchitectureEvolutionArena:
    """
    Sandboxed red-vs-blue framework for evolving AlphaAlgo architecture.

    Red team attacks a proposed architecture mutation, blue team proposes
    controls/tests, and unresolved attacks block the proposal before any PR,
    staging, or production gate.
    """

    def __init__(
        self,
        sandbox_mesh: Optional[TieredSandboxMesh] = None,
        overseer: Optional[GlassBoxOverseer] = None,
        runtime_policy: Optional[RuntimeBoundaryPolicy] = None,
        protected_file_policy: Optional[ProtectedFilePolicy] = None,
        red_team: Optional[ArchitectureRedTeamAgent] = None,
        blue_team: Optional[ArchitectureBlueTeamAgent] = None,
    ):
        self.sandbox_mesh = sandbox_mesh or TieredSandboxMesh()
        self.overseer = overseer or GlassBoxOverseer()
        self.runtime_policy = runtime_policy or RuntimeBoundaryPolicy()
        self.protected_file_policy = protected_file_policy or ProtectedFilePolicy()
        self.red_team = red_team or ArchitectureRedTeamAgent()
        self.blue_team = blue_team or ArchitectureBlueTeamAgent()

    def create_candidate(
        self,
        objective: str,
        current_architecture: Dict[str, Any],
        proposed_change: str,
        target_files: Sequence[str],
        invariants: Optional[Sequence[str]] = None,
        test_plan: Optional[EngineeringTestPlan] = None,
        evidence: Optional[Dict[str, Any]] = None,
        allow_live_mutation: bool = False,
        allow_model_mutation: bool = False,
        allow_risk_limit_change: bool = False,
    ) -> ArchitectureEvolutionCandidate:
        seed = json.dumps(
            {
                "objective": objective,
                "current_architecture": current_architecture,
                "proposed_change": proposed_change,
                "target_files": list(target_files),
            },
            sort_keys=True,
        )
        candidate_id = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
        return ArchitectureEvolutionCandidate(
            candidate_id=candidate_id,
            objective=objective,
            current_architecture=dict(current_architecture),
            proposed_change=proposed_change,
            target_files=list(target_files),
            invariants=list(invariants or []),
            test_plan=test_plan,
            evidence=dict(evidence or {}),
            allow_live_mutation=allow_live_mutation,
            allow_model_mutation=allow_model_mutation,
            allow_risk_limit_change=allow_risk_limit_change,
        )

    def run_competition(
        self,
        objective: str,
        current_architecture: Dict[str, Any],
        proposed_change: str,
        target_files: Sequence[str],
        invariants: Optional[Sequence[str]] = None,
        test_plan: Optional[EngineeringTestPlan] = None,
        evidence: Optional[Dict[str, Any]] = None,
        max_rounds: int = 1,
        allow_live_mutation: bool = False,
        allow_model_mutation: bool = False,
        allow_risk_limit_change: bool = False,
    ) -> RedBlueArchitectureEvolutionReport:
        candidate = self.create_candidate(
            objective,
            current_architecture,
            proposed_change,
            target_files,
            invariants,
            test_plan,
            evidence,
            allow_live_mutation,
            allow_model_mutation,
            allow_risk_limit_change,
        )
        return self.evaluate_candidate(candidate, max_rounds=max_rounds)

    def evaluate_candidate(
        self,
        candidate: ArchitectureEvolutionCandidate,
        max_rounds: int = 1,
    ) -> RedBlueArchitectureEvolutionReport:
        sandbox = self.sandbox_mesh.create_ephemeral_session(
            "red-blue-architecture-arena",
            "simulate architecture evolution generated patch",
        )
        sandbox_branch = SandboxBranchPlan(
            branch_name=self._branch_name(candidate.objective),
            base_branch=str(candidate.evidence.get("base_branch", "master")),
            patch_proposal_id=candidate.candidate_id,
        )
        protected_file_report = self._protected_file_report(candidate)
        complexity_budget = self._complexity_budget(candidate)
        metric_comparison = self._metric_comparison(candidate.evidence)
        governance = self.overseer.classify("architecture evolution generated patch", candidate.evidence)

        rounds: List[RedBlueArchitectureRound] = []
        unresolved: List[RedTeamArchitectureAttack] = []
        for index in range(max(1, max_rounds)):
            attacks = self.red_team.attack(candidate, protected_file_report, complexity_budget, metric_comparison)
            defenses = self.blue_team.defend(candidate, attacks, metric_comparison)
            resolved_attack_ids = {defense.attack_id for defense in defenses if defense.resolved}
            unresolved = [attack for attack in attacks if attack.attack_id not in resolved_attack_ids]
            round_id = hashlib.sha256(f"{candidate.candidate_id}:round:{index}".encode("utf-8")).hexdigest()[:16]
            rounds.append(RedBlueArchitectureRound(round_id, attacks, defenses, unresolved, not unresolved))
            if not unresolved:
                break

        blocked_reasons = [attack.finding for attack in unresolved]
        boundary_report = self._boundary_report(candidate)
        if not boundary_report.accepted:
            blocked_reasons.extend(boundary_report.verifier_notes)
        if sandbox.production_access or sandbox.persistent_secrets:
            blocked_reasons.append("red-vs-blue arena sandbox has production access or secrets")
        if governance.missing_evidence:
            blocked_reasons.extend(governance.missing_evidence)

        accepted = not blocked_reasons
        reviewer_report = VerificationReport(
            accepted,
            "red-vs-blue architecture evolution review",
            1.0 if accepted else 0.0,
            blocked_reasons,
        )
        deployment_plan = DeploymentPlan(
            staging_environment=str(candidate.evidence.get("staging_environment", "architecture-simulation")),
            shadow_mode="paper_trade",
            canary_percentage=float(candidate.evidence.get("canary_percentage", 1.0)),
            production_enabled=False,
            rollback_triggers=["red_team_unresolved_attack", "benchmark_regression", "paper_trade_degradation"],
            monitoring_metrics=["unresolved_attacks", "defense_resolution_rate", "latency_p95", "drawdown"],
        )
        run_id = hashlib.sha256(f"{candidate.candidate_id}:{len(rounds)}:{accepted}".encode("utf-8")).hexdigest()[:16]
        provenance = DecisionProvenanceTrace(run_id)
        provenance.append("candidate_created", "architecture-evolution-arena", candidate.objective, [candidate.candidate_id])
        for round_ in rounds:
            provenance.append(
                "red_vs_blue_round",
                "red-blue-agents",
                f"{len(round_.red_attacks)} attacks, {len(round_.unresolved_attacks)} unresolved",
                [round_.round_id],
            )
        provenance.append(
            "governance_gate",
            "glass-box-overseer",
            "architecture evolution stays sandboxed; production deployment disabled",
            governance.required_evidence,
        )
        provenance.seal()
        return RedBlueArchitectureEvolutionReport(
            run_id=run_id,
            candidate=candidate,
            rounds=rounds,
            sandbox_session=sandbox,
            sandbox_branch=sandbox_branch,
            runtime_policy=self.runtime_policy,
            governance=governance,
            protected_file_report=protected_file_report,
            complexity_budget=complexity_budget,
            metric_comparison=metric_comparison,
            reviewer_report=reviewer_report,
            deployment_plan=deployment_plan,
            final_decision=ApprovalState.APPROVED if accepted else ApprovalState.REJECTED,
            blocked_reasons=blocked_reasons,
            provenance=provenance,
        )

    def _boundary_report(self, candidate: ArchitectureEvolutionCandidate) -> VerificationReport:
        action = candidate.proposed_change
        if candidate.allow_live_mutation:
            action += " modify live code"
        if candidate.allow_model_mutation:
            action += " mutate model"
        if candidate.allow_risk_limit_change:
            action += " change risk limit"
        return self.runtime_policy.validate_engineering_action(action, actor="architecture-evolution-agent")

    def _protected_file_report(self, candidate: ArchitectureEvolutionCandidate) -> VerificationReport:
        reports = [self.protected_file_policy.check(path, candidate.evidence) for path in candidate.target_files]
        notes = [note for report in reports for note in report.verifier_notes]
        accepted = all(report.accepted for report in reports)
        return VerificationReport(accepted, "architecture protected file policy", 1.0 if accepted else 0.0, notes)

    def _complexity_budget(self, candidate: ArchitectureEvolutionCandidate) -> ComplexityBudget:
        text = candidate.proposed_change
        lines = [line for line in text.splitlines() if line.strip()]
        changed_lines = len(lines)
        new_functions = text.count("def ")
        complexity_delta = text.count(" if ") + text.count("\nif ") + text.count(" for ") + text.count("\nfor ")
        evidence = candidate.evidence
        max_changed = int(evidence.get("max_changed_lines", 80))
        max_functions = int(evidence.get("max_new_functions", 4))
        max_delta = int(evidence.get("max_complexity_delta", 6))
        notes = []
        if changed_lines > max_changed:
            notes.append(f"changed lines {changed_lines} exceed budget {max_changed}")
        if new_functions > max_functions:
            notes.append(f"new functions {new_functions} exceed budget {max_functions}")
        if complexity_delta > max_delta:
            notes.append(f"complexity delta {complexity_delta} exceed budget {max_delta}")
        return ComplexityBudget(max_changed, max_functions, max_delta, changed_lines, new_functions, complexity_delta, not notes, notes)

    def _metric_comparison(self, evidence: Dict[str, Any]) -> MetricComparisonReport:
        before = {str(key): float(value) for key, value in evidence.get("before_metrics", {}).items()}
        after = {str(key): float(value) for key, value in evidence.get("after_metrics", {}).items()}
        regressions = []
        lower_is_better = {"latency", "latency_p95", "error_rate", "drawdown", "order_reject_rate", "slippage"}
        higher_is_better = {"throughput", "test_pass_rate", "sharpe", "win_rate", "defense_resolution_rate"}
        for name, before_value in before.items():
            if name not in after:
                continue
            after_value = after[name]
            if name in lower_is_better and after_value > before_value * 1.02:
                regressions.append(f"{name} regressed from {before_value} to {after_value}")
            if name in higher_is_better and after_value < before_value * 0.98:
                regressions.append(f"{name} regressed from {before_value} to {after_value}")
        return MetricComparisonReport(before, after, not regressions, regressions)

    def _branch_name(self, objective: str) -> str:
        slug = "-".join(
            token
            for token in "".join(char.lower() if char.isalnum() else " " for char in objective).split()
            if token
        )[:48] or "architecture-evolution"
        return f"codex/red-blue-{slug}"
