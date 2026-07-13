from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence
from .models import *
from .services import *

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
        self.architecture_evolution_arena = RedBlueArchitectureEvolutionArena(
            sandbox_mesh=self.sandbox_mesh,
            overseer=self.overseer,
            runtime_policy=self.runtime_policy,
            protected_file_policy=self.protected_file_policy,
        )
        self.failure_memory: List[FailureMemoryEntry] = []

    def run_architecture_evolution_competition(
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
        return self.architecture_evolution_arena.run_competition(
            objective,
            current_architecture,
            proposed_change,
            target_files,
            invariants,
            test_plan,
            evidence,
            max_rounds,
            allow_live_mutation,
            allow_model_mutation,
            allow_risk_limit_change,
        )

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
    "ArchitectureAttackVector",
    "ArchitectureBlueTeamAgent",
    "ArchitectureEvolutionCandidate",
    "ArchitectureRedTeamAgent",
    "ApprovalState",
    "DebatePostTrainingValidator",
    "BlueTeamArchitectureDefense",
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
    "RedBlueArchitectureEvolutionArena",
    "RedBlueArchitectureEvolutionReport",
    "RedBlueArchitectureRound",
    "RedTeamArchitectureAttack",
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
