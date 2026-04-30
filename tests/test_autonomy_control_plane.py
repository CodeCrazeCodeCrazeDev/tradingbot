#!/usr/bin/env python3
"""Tests for the autonomy control plane."""

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "core" / "autonomy_control_plane.py"
SPEC = importlib.util.spec_from_file_location("autonomy_control_plane_direct", MODULE_PATH)
control = importlib.util.module_from_spec(SPEC)
sys.modules["autonomy_control_plane_direct"] = control
SPEC.loader.exec_module(control)


def test_tiered_sandbox_mesh_blocks_live_sensitive_operations():
    mesh = control.TieredSandboxMesh()

    decision = mesh.decide("rotate credential before live broker order")

    assert not decision.allowed
    assert decision.required_approval
    assert decision.tier == control.SandboxTier.LIVE_EXECUTION


def test_dynamic_credential_rotation_versions_and_expiry():
    rotator = control.DynamicCredentialRotator(ttl_seconds=10)

    first = rotator.rotate("broker-key", "secret-a")
    second = rotator.rotate("broker-key", "secret-b")

    assert first.version == 1
    assert second.version == 2
    assert first.secret_digest != second.secret_digest
    assert rotator.is_expired(first, now=first.expires_at + 1)


def test_signed_approval_required_before_patch_can_apply():
    gate = control.ClientSignedApprovalGate("client-secret", ttl_seconds=60)
    pipeline = control.StrictPatchApprovalPipeline(gate)
    proposal = pipeline.propose("x.py", "a = 1\n", "a = 2\n", risk="high")

    assert not pipeline.can_apply(proposal.proposal_id)

    approval = gate.sign(proposal.proposal_id, "operator")
    approved = pipeline.approve(proposal.proposal_id, approval)

    assert approved.approval_state == control.ApprovalState.APPROVED
    assert pipeline.can_apply(proposal.proposal_id)


def test_session_memory_compaction_retains_recent_and_summarizes_requirements():
    compactor = control.SessionMemoryCompactor()
    messages = [
        {"role": "user", "content": "must keep strict approval"},
        {"role": "assistant", "content": "working"},
        {"role": "user", "content": "ordinary note"},
        {"role": "assistant", "content": "latest context"},
    ]

    result = compactor.compact(messages, retain_last=2)

    assert "must keep strict approval" in result.summary
    assert len(result.retained_messages) == 2
    assert result.dropped_count == 2


def test_tool_call_fusion_prefetch_and_self_consistency():
    calls = [
        control.ToolCall("read", {"path": "a.py"}),
        control.ToolCall("search", {"query": "sandbox"}),
        control.ToolCall("patch", {"path": "a.py"}, read_only=False, tier=control.SandboxTier.SIMULATED_WRITE),
    ]

    fused = control.ToolCallFusionPlanner().fuse(calls)
    prefetched = control.ContextPrefetcher().prefetch(
        "sandbox approval verifier",
        ["trading_bot/core/sandbox_approval_verifier.py", "docs/architecture/ARCHITECTURE.md"],
    )
    report = control.SelfConsistencyVerifier().verify(["approve", "approve", "reject"], threshold=0.60)

    assert any(len(batch.calls) == 2 for batch in fused)
    assert prefetched == ["trading_bot/core/sandbox_approval_verifier.py"]
    assert report.accepted


def test_glass_box_overseer_requires_signed_evidence_for_high_risk_actions():
    overseer = control.GlassBoxOverseer()

    decision = overseer.classify("live deployment to production")
    approved = overseer.classify(
        "production patch",
        {"signed_approval": True, "ci_passed": True, "rollback_plan": True},
    )

    assert decision.action_classification == control.ActionClassification.LIVE_DEPLOYMENT
    assert decision.risk_category == control.RiskCategory.CRITICAL
    assert "signed_approval" in decision.missing_evidence
    assert decision.manual_review_required
    assert approved.missing_evidence == []


def test_ephemeral_sandbox_session_has_no_secrets_or_production_access():
    mesh = control.TieredSandboxMesh()

    session = mesh.create_ephemeral_session("coordinator", "run untrusted strategy code")
    destroyed = mesh.destroy_session(session)

    assert session.ephemeral
    assert not session.persistent_secrets
    assert not session.production_access
    assert destroyed.destroyed


def test_tool_proxy_vault_blocks_high_risk_scopes_without_approval():
    vault = control.ToolProxyVault()
    gate = control.ClientSignedApprovalGate("client-secret")

    try:
        vault.issue_scoped_token("agent", "broker", ["broker:trade"])
    except PermissionError:
        blocked = True
    else:
        blocked = False

    approval = gate.sign("agent:broker:broker:trade", "operator")
    token = vault.issue_scoped_token("agent", "broker", ["broker:trade"], approval)

    assert blocked
    assert vault.token_is_valid(token, "broker:trade")
    assert "broker:trade" in token.scopes


def test_hierarchical_memory_tracks_contradictions_and_filters_retrieval():
    memory = control.HierarchicalSessionMemory()

    memory.append("user", "risk limit change requires signed approval")
    memory.append("assistant", "risk limit change does not require signed approval")

    assert memory.contradictions
    assert memory.retrieve(include_terms=["risk", "signed"])


def test_tool_plan_compiler_blocks_unsafe_and_merges_repeated_calls():
    compiler = control.ToolPlanCompiler()
    calls = [
        control.ToolCall("scan market", {"symbol": "EURUSD"}),
        control.ToolCall("scan market", {"symbol": "EURUSD"}),
        control.ToolCall("deploy production patch", {}, read_only=False, tier=control.SandboxTier.LIVE_EXECUTION),
    ]

    compiled = compiler.compile(calls)

    assert compiled["blocked_calls"]
    assert "1 safe calls" in compiled["summary"]


def test_tool_search_and_programmatic_tool_script_collapse_calls():
    compiler = control.ProgrammaticToolCallCompiler()
    calls = [
        control.ToolCall("scan market", {"symbol": "EURUSD"}),
        control.ToolCall("scan market", {"symbol": "EURUSD"}),
        control.ToolCall("prefetch context", {"query": "risk"}),
        control.ToolCall(
            "place live broker order",
            {"symbol": "EURUSD"},
            read_only=False,
            tier=control.SandboxTier.LIVE_EXECUTION,
        ),
    ]

    script = compiler.compile_script("market scan and risk report without live broker order", calls)
    selected_names = {result.descriptor.name for result in script.selected_tools}

    assert {"scan_market", "risk_report"}.issubset(selected_names)
    assert script.blocked_calls
    assert script.estimated_inference_steps_saved >= 1
    assert len(script.fused_calls) == 1
    assert len(script.fused_calls[0].calls) == 2
    assert script.provenance.sealed_digest


def test_debate_validator_and_formal_invariants_cover_trading_workflows():
    debate = control.DebatePostTrainingValidator().validate(
        "trade_thesis_validation",
        ["hold", "hold", "buy"],
        ["risk is elevated"],
        ["momentum is improving"],
    )
    invariants = control.FormalTradingInvariantRegistry().validate(
        {"autonomous": True, "production_access": True, "risk_category": "critical"}
    )

    assert debate.accepted
    assert debate.winner == "hold"
    assert not invariants.accepted
    assert "violates no_direct_production_access" in invariants.verifier_notes


def test_specialist_router_and_patch_workflow_keep_submission_approval_gated():
    router = control.SpecialistAgentRouter()
    gate = control.ClientSignedApprovalGate("client-secret")
    pipeline = control.StrictPatchApprovalPipeline(gate)

    agents = router.route("security patch with regression test for credential leak")
    report = pipeline.create_bugfix_workflow(
        "bug-1",
        "secure.py",
        "token = secret\n",
        "token = scoped_token\n",
        "test_scoped_token_required",
        "high risk credential handling change",
    )

    assert control.SpecialistAgent.SECURITY in agents
    assert control.SpecialistAgent.CODE_REVIEW in agents
    assert report.approval_state == control.ApprovalState.PENDING
    assert "automatic public vulnerability disclosure" in report.blocked_next_steps


def test_managed_agent_decoupling_issues_scoped_lease_and_expires():
    supervisor = control.ManagedAgentSupervisor(default_ttl_seconds=10)

    lease = supervisor.lease_agent(
        "agent-risk-1",
        "risk and backtest validation",
        ["read:market", "research:run"],
        ttl_seconds=5,
    )
    heartbeat = supervisor.heartbeat(lease.lease_id, now=lease.issued_at + 1)
    revoked = supervisor.revoke(lease.lease_id)

    assert lease.role == control.SpecialistAgent.RISK
    assert lease.sandbox_session.ephemeral
    assert not lease.sandbox_session.production_access
    assert not lease.sandbox_session.persistent_secrets
    assert heartbeat.heartbeat_at == lease.issued_at + 1
    assert not supervisor.lease_is_active(lease.lease_id, now=lease.expires_at + 1)
    assert not revoked.active
    assert revoked.sandbox_session.destroyed


def test_managed_agent_decoupling_blocks_privileged_scopes_without_approval():
    supervisor = control.ManagedAgentSupervisor()

    try:
        supervisor.lease_agent("agent-exec-1", "execution task", ["broker:trade"])
    except PermissionError:
        blocked = True
    else:
        blocked = False

    assert blocked


def test_controlled_software_factory_enforces_engineering_pipeline_order_and_gates():
    factory = control.ControlledSoftwareFactory()
    snapshot = {
        "source": "paper_trading_monitor",
        "expected_behavior": "risk gate rejects oversized orders",
        "observed_behavior": "risk gate accepted oversized orders",
        "symptoms": ["risk approval weakness"],
        "suspected_files": ["trading_bot/risk.py"],
        "severity": "high",
    }

    report = factory.run_control_loop(
        "fix risk gate oversized order acceptance",
        snapshot,
        "trading_bot/risk.py",
        "allow_order = True\n",
        "allow_order = exposure <= limit\n",
        {"protected_file_approval": True},
    )
    statuses = {stage.stage: stage.status for stage in report.stages}

    assert [stage.stage for stage in report.stages] == factory.PIPELINE
    assert report.objective_validation.accepted
    assert report.root_cause_report.confidence >= 0.60
    assert report.complexity_budget.accepted
    assert report.protected_file_report.accepted
    assert report.metric_comparison.accepted
    assert report.test_plan.invariant_tests
    assert report.test_plan.hidden_tests
    assert report.test_plan.adversarial_tests
    assert report.patch_workflow.patch.approval_state == control.ApprovalState.PENDING
    assert report.runtime_policy.production_runs_separately
    assert not report.runtime_policy.live_self_editing_allowed
    assert not report.runtime_policy.live_model_mutation_allowed
    assert not report.runtime_policy.live_direct_code_changes_allowed
    assert report.sandbox_branch.branch_name == report.pull_request.branch_name
    assert not report.sandbox_branch.live_runtime_attached
    assert not report.sandbox_branch.live_code_mutation_allowed
    assert not report.sandbox_branch.risk_limit_change_allowed
    assert not report.sandbox_branch.model_mutation_allowed
    assert report.sandbox_session.ephemeral
    assert not report.sandbox_session.production_access
    assert not report.sandbox_session.persistent_secrets
    assert all(review.decision == control.ApprovalState.APPROVED for review in report.verifier_agent_reviews)
    assert report.reviewer_report.accepted
    assert report.pull_request.ready_for_review
    assert statuses[control.EngineeringPipelineStage.HUMAN_OR_GOVERNANCE_APPROVAL] == control.EngineeringStageStatus.PENDING
    assert statuses[control.EngineeringPipelineStage.DEPLOY_TO_STAGING] == control.EngineeringStageStatus.BLOCKED
    assert statuses[control.EngineeringPipelineStage.PRODUCTION_DEPLOYMENT] == control.EngineeringStageStatus.BLOCKED
    assert not report.deployment_plan.production_enabled
    assert report.deployment_plan.rollback_available
    assert report.deployment_plan.production_runtime_separate
    assert report.failure_memory_entry.outcome == "blocked"
    assert factory.failure_memory[-1].memory_id == report.failure_memory_entry.memory_id
    assert report.provenance.sealed_digest


def test_controlled_software_factory_rolls_forward_only_after_release_evidence():
    factory = control.ControlledSoftwareFactory()
    snapshot = {
        "source": "latency_benchmark",
        "expected_behavior": "analysis completes under threshold",
        "observed_behavior": "analysis exceeded threshold",
        "symptoms": ["slow benchmark inefficiency"],
        "suspected_files": ["trading_bot/analysis.py"],
        "severity": "medium",
    }

    report = factory.run_control_loop(
        "optimize analysis hot path",
        snapshot,
        "trading_bot/analysis.py",
        "for row in rows: compute(row)\n",
        "compute_batch(rows)\n",
        {
            "signed_approval": True,
            "shadow_test_passed": True,
            "canary_metrics_passed": True,
            "monitoring_baseline": True,
        },
    )
    statuses = {stage.stage: stage.status for stage in report.stages}

    assert statuses[control.EngineeringPipelineStage.HUMAN_OR_GOVERNANCE_APPROVAL] == control.EngineeringStageStatus.PASSED
    assert statuses[control.EngineeringPipelineStage.DEPLOY_TO_STAGING] == control.EngineeringStageStatus.PASSED
    assert statuses[control.EngineeringPipelineStage.SHADOW_TEST_OR_PAPER_TRADE] == control.EngineeringStageStatus.PASSED
    assert statuses[control.EngineeringPipelineStage.CANARY_RELEASE] == control.EngineeringStageStatus.PASSED
    assert statuses[control.EngineeringPipelineStage.PRODUCTION_DEPLOYMENT] == control.EngineeringStageStatus.PASSED
    assert statuses[control.EngineeringPipelineStage.MONITOR] == control.EngineeringStageStatus.PASSED
    assert statuses[control.EngineeringPipelineStage.ROLLBACK_IF_METRICS_DEGRADE] == control.EngineeringStageStatus.PASSED
    assert report.deployment_plan.production_enabled
    assert report.deployment_plan.canary_enabled
    assert report.deployment_plan.paper_trading_required
    assert report.failure_memory_entry.outcome == "accepted"


def test_controlled_software_factory_triggers_rollback_when_metrics_degrade():
    factory = control.ControlledSoftwareFactory()
    snapshot = {
        "source": "canary_monitor",
        "expected_behavior": "canary maintains baseline metrics",
        "observed_behavior": "canary latency degraded",
        "symptoms": ["canary benchmark degraded"],
        "suspected_files": ["trading_bot/execution_manager.py"],
    }

    report = factory.run_control_loop(
        "repair canary regression",
        snapshot,
        "trading_bot/execution_manager.py",
        "route = slow_path\n",
        "route = fast_path\n",
        {
            "signed_approval": True,
            "shadow_test_passed": True,
            "canary_metrics_passed": True,
            "monitoring_baseline": True,
            "metrics_degraded": True,
        },
    )
    rollback_stage = [
        stage
        for stage in report.stages
        if stage.stage == control.EngineeringPipelineStage.ROLLBACK_IF_METRICS_DEGRADE
    ][0]

    assert rollback_stage.status == control.EngineeringStageStatus.PASSED
    assert "rollback triggered" in rollback_stage.summary
    assert not report.deployment_plan.production_enabled
    assert report.failure_memory_entry.rollback_triggered
    assert report.failure_memory_entry.outcome == "rollback"


def test_controlled_software_factory_rejects_ai_self_approval_and_live_mutation():
    factory = control.ControlledSoftwareFactory()
    boundary = factory.runtime_policy.validate_engineering_action(
        "approve and deploy production while changing risk limits",
        actor="ai-engineering-agent",
    )
    snapshot = {
        "source": "runtime_logs",
        "expected_behavior": "production remains deterministic",
        "observed_behavior": "engineering change requested",
        "symptoms": ["approval weakness"],
        "suspected_files": ["trading_bot/main.py"],
    }

    report = factory.run_control_loop(
        "block engineering AI self approval",
        snapshot,
        "trading_bot/main.py",
        "mode = 'live'\n",
        "mode = 'paper'\n",
        {
            "signed_approval": True,
            "governance_approver": "ai-engineering-agent",
            "shadow_test_passed": True,
            "canary_metrics_passed": True,
            "monitoring_baseline": True,
        },
    )
    statuses = {stage.stage: stage for stage in report.stages}

    assert not boundary.accepted
    assert "violates self-approval ban" in boundary.verifier_notes
    assert statuses[control.EngineeringPipelineStage.HUMAN_OR_GOVERNANCE_APPROVAL].status == control.EngineeringStageStatus.BLOCKED
    assert "self-approval" in statuses[control.EngineeringPipelineStage.HUMAN_OR_GOVERNANCE_APPROVAL].summary
    assert statuses[control.EngineeringPipelineStage.DEPLOY_TO_STAGING].status == control.EngineeringStageStatus.BLOCKED
    assert not report.deployment_plan.production_enabled


def test_controlled_software_factory_blocks_protected_file_without_approval():
    factory = control.ControlledSoftwareFactory()
    snapshot = {
        "source": "security_scan",
        "expected_behavior": "approval rules stay immutable",
        "observed_behavior": "approval bypass detected",
        "symptoms": ["security approval weakness"],
        "suspected_files": ["trading_bot/governance.py"],
    }

    report = factory.run_control_loop(
        "repair governance bypass",
        snapshot,
        "trading_bot/governance.py",
        "approval_required = True\n",
        "approval_required = verify_signature()\n",
    )
    statuses = {stage.stage: stage for stage in report.stages}

    assert not report.protected_file_report.accepted
    assert statuses[control.EngineeringPipelineStage.RUN_PROTECTED_FILE_CHECK].status == control.EngineeringStageStatus.BLOCKED
    assert statuses[control.EngineeringPipelineStage.OPEN_PULL_REQUEST].status == control.EngineeringStageStatus.BLOCKED
    assert any(review.decision == control.ApprovalState.REJECTED for review in report.verifier_agent_reviews)


def test_controlled_software_factory_blocks_complexity_and_metric_regression():
    factory = control.ControlledSoftwareFactory()
    snapshot = {
        "source": "performance_monitor",
        "expected_behavior": "execution latency stays stable",
        "observed_behavior": "execution latency regressed",
        "symptoms": ["slow benchmark inefficiency"],
        "suspected_files": ["trading_bot/execution_manager.py"],
        "metrics": {"latency_p95": 100.0},
    }
    old_text = "def route(order):\n    return fast_path(order)\n"
    new_text = "\n".join(
        [
            "def route(order):",
            "    if order:",
            "        for venue in venues:",
            "            if venue.enabled:",
            "                return slow_path(order, venue)",
            "    return fallback(order)",
            "def extra_helper(order):",
            "    return order",
        ]
    )

    report = factory.run_control_loop(
        "repair execution latency regression",
        snapshot,
        "trading_bot/execution_manager.py",
        old_text,
        new_text,
        {
            "max_changed_lines": 2,
            "max_new_functions": 0,
            "max_complexity_delta": 0,
            "before_metrics": {"latency_p95": 100.0},
            "after_metrics": {"latency_p95": 130.0},
        },
    )
    statuses = {stage.stage: stage for stage in report.stages}

    assert not report.complexity_budget.accepted
    assert not report.metric_comparison.accepted
    assert statuses[control.EngineeringPipelineStage.CHECK_COMPLEXITY_BUDGET].status == control.EngineeringStageStatus.BLOCKED
    assert statuses[control.EngineeringPipelineStage.COMPARE_BEFORE_AFTER_METRICS].status == control.EngineeringStageStatus.BLOCKED
    assert statuses[control.EngineeringPipelineStage.OPEN_PULL_REQUEST].status == control.EngineeringStageStatus.BLOCKED
    assert report.failure_memory_entry.outcome == "blocked"


def test_mythos_inspired_governor_contains_defensive_security_work():
    governor = control.MythosInspiredAIGovernor()

    plan = governor.plan("research vulnerability in generated strategy code", {"patch_ready": True})

    assert plan.mode == control.MythosMode.DEFENSIVE_SECURITY
    assert plan.sandbox_session is not None
    assert plan.sandbox_session.ephemeral
    assert not plan.sandbox_session.production_access
    assert control.SpecialistAgent.SECURITY in plan.specialists
    assert "public exploit details" in plan.blocked_outputs
    assert plan.disclosure_state == control.DisclosureState.PATCH_REVIEW
    assert plan.provenance.sealed_digest


def test_frontier_controller_activates_approximately_70_percent_safely():
    controller = control.FrontierAgentCapabilityController()

    report = controller.activate("upgrade trading agents with frontier reasoning and coding")
    activated_ids = {capability.capability_id for capability in report.activated}
    deferred_ids = {item["capability"]["capability_id"] for item in report.deferred}

    assert 0.69 <= report.achieved_coverage <= 0.73
    assert "recurrent_reasoning_vlk" in activated_ids
    assert "tool_search_index" in activated_ids
    assert "programmatic_tool_scripts" in activated_ids
    assert "managed_agent_decoupling" in activated_ids
    assert "approval_gated_patch_pipeline" in activated_ids
    assert "sandboxed_research_agents" in activated_ids
    assert "strategy_promotion" in deferred_ids
    assert "broker_tool_tokens" in deferred_ids
    assert "capital_scaling_control" in deferred_ids
    assert report.invariant_report.accepted
    assert report.sandbox_sessions
    assert all(not session.production_access for session in report.sandbox_sessions)
    assert report.provenance.sealed_digest


def test_frontier_controller_keeps_strategy_promotion_paper_gated():
    controller = control.FrontierAgentCapabilityController()

    blocked = controller.activate(
        "promote strategy after research",
        {"signed_approval": True, "backtest_report": True},
    )
    approved = controller.activate(
        "promote strategy after research",
        {"signed_approval": True, "backtest_report": True, "paper_trading_report": True},
    )

    blocked_ids = {item["capability"]["capability_id"] for item in blocked.deferred}
    approved_ids = {capability.capability_id for capability in approved.activated}

    assert "strategy_promotion" in blocked_ids
    assert "strategy_promotion" in approved_ids
    assert approved.achieved_coverage > blocked.achieved_coverage


def test_red_blue_architecture_evolution_runs_sandboxed_attack_defense_round():
    factory = control.ControlledSoftwareFactory()

    report = factory.run_architecture_evolution_competition(
        "evolve architecture with red vs blue simulation",
        {"live_runtime": "deterministic", "engineering_ai": "sandboxed"},
        "Add architecture-evolution arena that proposes sandbox-only patch candidates and verifier evidence.",
        ["trading_bot/core/architecture_evolution.py"],
        evidence={
            "rollback_plan": True,
            "before_metrics": {"latency_p95": 100.0, "defense_resolution_rate": 0.80},
            "after_metrics": {"latency_p95": 98.0, "defense_resolution_rate": 0.86},
        },
    )
    first_round = report.rounds[0]
    attack_vectors = {attack.vector for attack in first_round.red_attacks}

    assert report.accepted
    assert report.final_decision == control.ApprovalState.APPROVED
    assert attack_vectors == {
        control.ArchitectureAttackVector.HIDDEN_INVARIANT_BREAK,
        control.ArchitectureAttackVector.TEST_OVERFITTING,
        control.ArchitectureAttackVector.PERFORMANCE_REGRESSION,
    }
    assert first_round.blue_defenses
    assert not first_round.unresolved_attacks
    assert report.sandbox_session.ephemeral
    assert not report.sandbox_session.production_access
    assert not report.sandbox_session.persistent_secrets
    assert not report.sandbox_branch.live_runtime_attached
    assert not report.sandbox_branch.live_code_mutation_allowed
    assert not report.sandbox_branch.risk_limit_change_allowed
    assert not report.sandbox_branch.model_mutation_allowed
    assert not report.deployment_plan.production_enabled
    assert report.deployment_plan.rollback_available
    assert report.runtime_policy.production_runs_separately
    assert report.provenance.sealed_digest


def test_red_blue_architecture_evolution_rejects_live_mutation_and_self_approval():
    arena = control.RedBlueArchitectureEvolutionArena()

    report = arena.run_competition(
        "dangerous architecture evolution",
        {"live_runtime": "deterministic"},
        "Allow production self-edit, change risk limit, mutate model, and self approve deployment.",
        ["trading_bot/governance.py", "trading_bot/risk.py"],
        evidence={
            "before_metrics": {"latency_p95": 100.0},
            "after_metrics": {"latency_p95": 140.0},
        },
        allow_live_mutation=True,
        allow_model_mutation=True,
        allow_risk_limit_change=True,
    )
    unresolved_vectors = {
        attack.vector
        for round_ in report.rounds
        for attack in round_.unresolved_attacks
    }

    assert not report.accepted
    assert report.final_decision == control.ApprovalState.REJECTED
    assert control.ArchitectureAttackVector.LIVE_MUTATION_BYPASS in unresolved_vectors
    assert control.ArchitectureAttackVector.RISK_LIMIT_WEAKENING in unresolved_vectors
    assert control.ArchitectureAttackVector.MODEL_MUTATION in unresolved_vectors
    assert control.ArchitectureAttackVector.SELF_APPROVAL in unresolved_vectors
    assert control.ArchitectureAttackVector.PROTECTED_FILE_WEAKENING in unresolved_vectors
    assert report.blocked_reasons
    assert not report.sandbox_session.production_access
    assert not report.deployment_plan.production_enabled
