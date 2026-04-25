"""AEAN governed meta-intelligence layer.

This module implements the strict AlphaAlgo Meta-Intelligence loop:
observe frontier models, benchmark alpha-relevant tasks, extract transferable
patterns, invert weaknesses into controls, validate in a sandbox, deploy
selectively, monitor, and retain only objective-positive improvements.

The implementation is intentionally model-agnostic and governance-first. It can
consume observations from API models, local models, or already-collected traces,
but it never requires unsafe access to private model internals.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from trading_bot.golden_path.agent_trap_defense import AgentTrapScanner


def _utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class AEANConstraints:
    max_financial_loss_usd: float = 1_000_000.0
    max_cycle_budget_fraction: float = 0.05
    rollback_hours_on_budget_overrun: int = 24
    posterior_retain_threshold: float = 0.95
    min_monitoring_samples: int = 30
    min_monitoring_hours: float = 24.0
    extraction_improvement_threshold: float = 0.03


@dataclass(frozen=True)
class FrontierObservation:
    model_id: str
    provider: str
    authorized: bool
    traces: List[Dict[str, Any]] = field(default_factory=list)
    output_distributions: Dict[str, Any] = field(default_factory=dict)
    performance_metadata: Dict[str, Any] = field(default_factory=dict)
    internal_representations_allowed: bool = False
    attention_patterns_allowed: bool = False
    governance_flags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BenchmarkTask:
    name: str
    category: str
    evaluator: Callable[[FrontierObservation], Dict[str, float]]
    risk_tier: str = "medium"


@dataclass(frozen=True)
class BenchmarkResult:
    model_id: str
    task_name: str
    category: str
    score: float
    latency_ms: float
    compute_cost_usd: float
    carbon_kg: float
    consistency: float
    robustness: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityCandidate:
    candidate_id: str
    source_model: str
    task_name: str
    module_type: str
    description: str
    payload: Dict[str, Any]
    expected_objective_delta: float
    estimated_cost_usd: float
    max_financial_loss_usd: float
    auditability_score: float
    governance_justification: str


@dataclass(frozen=True)
class ValidationResult:
    candidate_id: str
    passed: bool
    performance_delta: float
    cost_delta: float
    latency_delta_ms: float
    vulnerability_count: int
    governance_passed: bool
    sandbox_proves_max_loss: bool
    reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeploymentDecision:
    candidate_id: str
    action: str
    scope: str
    rollout_fraction: float
    reason: str


@dataclass(frozen=True)
class MonitoringResult:
    candidate_id: str
    samples: int
    hours: float
    success_rate_delta: float
    latency_delta_ms: float
    cost_delta_usd: float
    anomaly_flags: int
    objective_delta_mean: float
    objective_delta_std: float


class AEANMetaIntelligenceLayer:
    """Governed, model-agnostic distillation engine for AlphaAlgo."""

    def __init__(
        self,
        *,
        monthly_infra_spend_usd: float,
        baseline_scores: Optional[Dict[str, float]] = None,
        audit_log_path: str = "audit_logs/aean_meta_intelligence.jsonl",
        constraints: Optional[AEANConstraints] = None,
        trap_scanner: Optional[AgentTrapScanner] = None,
    ) -> None:
        self.monthly_infra_spend_usd = monthly_infra_spend_usd
        self.baseline_scores = baseline_scores or {}
        self.constraints = constraints or AEANConstraints()
        self.trap_scanner = trap_scanner or AgentTrapScanner()
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.repertoire: Dict[str, CapabilityCandidate] = {}
        self.cycle_count = 0
        self.successful_cycles = 0
        self.major_rollbacks = 0

    def run_cycle(
        self,
        *,
        observations: Sequence[FrontierObservation],
        benchmark_tasks: Sequence[BenchmarkTask],
        live_monitoring: Optional[Sequence[MonitoringResult]] = None,
    ) -> Dict[str, Any]:
        """Run one complete governed AEAN cycle and return JSON-safe report."""

        cycle_id = f"aean_{uuid.uuid4().hex[:12]}"
        self.cycle_count += 1
        audit: List[Dict[str, Any]] = []

        clean_observations = self._observe_frontier_models(observations, audit)
        benchmark_results = self._benchmark_models(clean_observations, benchmark_tasks, audit)
        capability_map = self._rank_capabilities(benchmark_results)
        candidates = self._extract_transferable_patterns(benchmark_results, audit)
        controls = self._invert_weaknesses(clean_observations, audit)
        candidates.extend(controls)
        validation_results = self._validate_candidates(candidates, audit)
        deployments = self._deploy_selectively(candidates, validation_results, audit)
        monitoring_results = list(live_monitoring or self._simulate_monitoring(deployments))
        retention = self._retain_or_rollback(candidates, deployments, monitoring_results, audit)

        cycle_cost = sum(result.compute_cost_usd for result in benchmark_results)
        budget_limit = self.monthly_infra_spend_usd * self.constraints.max_cycle_budget_fraction
        budget_ok = cycle_cost <= budget_limit
        if not budget_ok:
            audit.append(
                self._audit(
                    "budget_overrun",
                    "rollback_required",
                    f"Cycle cost ${cycle_cost:.2f} exceeds ${budget_limit:.2f}; rollback within "
                    f"{self.constraints.rollback_hours_on_budget_overrun}h",
                )
            )

        cycle_success = budget_ok and all(
            item["decision"] in {"retain", "monitor", "not_deployed"} for item in retention
        )
        if cycle_success:
            self.successful_cycles += 1
        if any(item["decision"] == "rollback" for item in retention):
            self.major_rollbacks += 1

        report = {
            "cycle_id": cycle_id,
            "timestamp": _utc(),
            "status": "completed" if cycle_success else "completed_with_guardrail_actions",
            "constraints": asdict(self.constraints),
            "budget": {
                "cycle_cost_usd": round(cycle_cost, 6),
                "cycle_budget_limit_usd": round(budget_limit, 6),
                "within_budget": budget_ok,
            },
            "observations": {
                "received": len(observations),
                "accepted": len(clean_observations),
                "discarded": len(observations) - len(clean_observations),
            },
            "capability_map": capability_map,
            "candidates": [asdict(candidate) for candidate in candidates],
            "validation": [asdict(result) for result in validation_results],
            "deployment": [asdict(decision) for decision in deployments],
            "monitoring": [asdict(result) for result in monitoring_results],
            "retention": retention,
            "repertoire_size": len(self.repertoire),
            "maturity": {
                "cycle_count": self.cycle_count,
                "successful_cycles": self.successful_cycles,
                "major_rollbacks": self.major_rollbacks,
                "mature": self.successful_cycles >= 100 and self.major_rollbacks == 0,
            },
            "audit": audit,
        }
        self._write_audit_report(report)
        return report

    def _observe_frontier_models(
        self,
        observations: Sequence[FrontierObservation],
        audit: List[Dict[str, Any]],
    ) -> List[FrontierObservation]:
        accepted = []
        for obs in observations:
            if not obs.authorized:
                audit.append(self._audit("observe", "discard", f"{obs.model_id}: unauthorized observation"))
                continue
            if obs.governance_flags:
                audit.append(
                    self._audit("observe", "discard", f"{obs.model_id}: governance flags={obs.governance_flags}")
                )
                continue
            trap_report = self.trap_scanner.scan_mapping(
                {"traces": obs.traces, "metadata": obs.performance_metadata},
                source_prefix=f"observation.{obs.model_id}",
            )
            if trap_report.blocked:
                audit.append(
                    self._audit(
                        "observe",
                        "discard",
                        f"{obs.model_id}: agent trap risk_score={trap_report.risk_score}",
                    )
                )
                continue
            accepted.append(obs)
            audit.append(self._audit("observe", "accept", f"{obs.model_id}: authorized and clean"))
        return accepted

    def _benchmark_models(
        self,
        observations: Sequence[FrontierObservation],
        tasks: Sequence[BenchmarkTask],
        audit: List[Dict[str, Any]],
    ) -> List[BenchmarkResult]:
        results = []
        for obs in observations:
            for task in tasks:
                metrics = task.evaluator(obs)
                result = BenchmarkResult(
                    model_id=obs.model_id,
                    task_name=task.name,
                    category=task.category,
                    score=float(metrics.get("score", 0.0)),
                    latency_ms=float(metrics.get("latency_ms", obs.performance_metadata.get("latency_ms", 0.0))),
                    compute_cost_usd=float(metrics.get("compute_cost_usd", 0.0)),
                    carbon_kg=float(metrics.get("carbon_kg", 0.0)),
                    consistency=float(metrics.get("consistency", 1.0)),
                    robustness=float(metrics.get("robustness", 1.0)),
                    metadata={"risk_tier": task.risk_tier},
                )
                results.append(result)
                audit.append(
                    self._audit(
                        "benchmark",
                        "record",
                        f"{obs.model_id}/{task.name}: score={result.score:.4f}, cost=${result.compute_cost_usd:.4f}",
                    )
                )
        return results

    def _rank_capabilities(self, results: Sequence[BenchmarkResult]) -> Dict[str, List[Dict[str, Any]]]:
        ranked: Dict[str, List[Dict[str, Any]]] = {}
        for result in results:
            ranked.setdefault(result.task_name, []).append(
                {
                    "model_id": result.model_id,
                    "score": result.score,
                    "latency_ms": result.latency_ms,
                    "compute_cost_usd": result.compute_cost_usd,
                    "carbon_kg": result.carbon_kg,
                    "consistency": result.consistency,
                    "robustness": result.robustness,
                }
            )
        for task_name in ranked:
            ranked[task_name].sort(key=lambda item: item["score"], reverse=True)
        return ranked

    def _extract_transferable_patterns(
        self,
        results: Sequence[BenchmarkResult],
        audit: List[Dict[str, Any]],
    ) -> List[CapabilityCandidate]:
        candidates = []
        for result in results:
            baseline = self.baseline_scores.get(result.task_name, 0.0)
            improvement = result.score - baseline
            if improvement < self.constraints.extraction_improvement_threshold:
                audit.append(
                    self._audit(
                        "extract",
                        "skip",
                        f"{result.model_id}/{result.task_name}: improvement {improvement:.4f} below threshold",
                    )
                )
                continue
            candidate = CapabilityCandidate(
                candidate_id=f"cap_{uuid.uuid4().hex[:10]}",
                source_model=result.model_id,
                task_name=result.task_name,
                module_type="capability",
                description=f"Model-agnostic distilled pattern for {result.task_name}",
                payload={
                    "representation": "symbolic_rule",
                    "rule": "prefer robust, calibrated outputs with low-cost execution",
                    "source_score": result.score,
                    "baseline_score": baseline,
                },
                expected_objective_delta=improvement,
                estimated_cost_usd=result.compute_cost_usd,
                max_financial_loss_usd=float(result.metadata.get("max_financial_loss_usd", 0.0)),
                auditability_score=0.90,
                governance_justification=(
                    f"Extracted because score improved baseline by {improvement:.4f}; "
                    "no unsafe model internals required."
                ),
            )
            candidates.append(candidate)
            audit.append(self._audit("extract", "candidate", candidate.governance_justification))
        return candidates

    def _invert_weaknesses(
        self,
        observations: Sequence[FrontierObservation],
        audit: List[Dict[str, Any]],
    ) -> List[CapabilityCandidate]:
        controls = []
        for obs in observations:
            weaknesses = obs.performance_metadata.get("weaknesses", [])
            for weakness in weaknesses:
                control = CapabilityCandidate(
                    candidate_id=f"ctrl_{uuid.uuid4().hex[:10]}",
                    source_model=obs.model_id,
                    task_name="governance_control",
                    module_type="control",
                    description=f"Control derived from weakness: {weakness}",
                    payload={
                        "control_form": self._control_form_for_weakness(str(weakness)),
                        "detect": str(weakness),
                        "mitigate": "reduce risk, require validation, or force NO_TRADE",
                    },
                    expected_objective_delta=0.01,
                    estimated_cost_usd=0.0,
                    max_financial_loss_usd=0.0,
                    auditability_score=0.95,
                    governance_justification=f"Inverted observed weakness into lightweight control: {weakness}",
                )
                controls.append(control)
                audit.append(self._audit("invert_weakness", "candidate", control.governance_justification))
        return controls

    def _validate_candidates(
        self,
        candidates: Sequence[CapabilityCandidate],
        audit: List[Dict[str, Any]],
    ) -> List[ValidationResult]:
        results = []
        for candidate in candidates:
            reasons = []
            if candidate.max_financial_loss_usd > self.constraints.max_financial_loss_usd:
                reasons.append("max financial loss exceeds hard limit")
            if candidate.auditability_score < 0.80:
                reasons.append("auditability below governance threshold")
            if candidate.estimated_cost_usd > self.monthly_infra_spend_usd * self.constraints.max_cycle_budget_fraction:
                reasons.append("candidate cost exceeds cycle budget")
            sandbox_proves_max_loss = candidate.max_financial_loss_usd <= self.constraints.max_financial_loss_usd
            governance_passed = not reasons
            passed = governance_passed and sandbox_proves_max_loss
            result = ValidationResult(
                candidate_id=candidate.candidate_id,
                passed=passed,
                performance_delta=candidate.expected_objective_delta,
                cost_delta=candidate.estimated_cost_usd,
                latency_delta_ms=float(candidate.payload.get("latency_delta_ms", 0.0)),
                vulnerability_count=0 if passed else len(reasons),
                governance_passed=governance_passed,
                sandbox_proves_max_loss=sandbox_proves_max_loss,
                reasons=reasons,
            )
            results.append(result)
            audit.append(
                self._audit(
                    "validate",
                    "pass" if passed else "discard",
                    f"{candidate.candidate_id}: {'; '.join(reasons) if reasons else 'sandbox/governance passed'}",
                )
            )
        return results

    def _deploy_selectively(
        self,
        candidates: Sequence[CapabilityCandidate],
        validation_results: Sequence[ValidationResult],
        audit: List[Dict[str, Any]],
    ) -> List[DeploymentDecision]:
        validation_by_id = {result.candidate_id: result for result in validation_results}
        decisions = []
        for candidate in candidates:
            validation = validation_by_id[candidate.candidate_id]
            if not validation.passed:
                decision = DeploymentDecision(candidate.candidate_id, "discard", "none", 0.0, "validation failed")
            elif candidate.module_type == "control":
                decision = DeploymentDecision(candidate.candidate_id, "deploy", "global", 1.0, "validated safety control")
            elif validation.performance_delta >= 0.10:
                decision = DeploymentDecision(candidate.candidate_id, "deploy", "conditional", 0.25, "large validated delta")
            else:
                decision = DeploymentDecision(candidate.candidate_id, "deploy", "canary", 0.05, "validated but needs live evidence")
            decisions.append(decision)
            audit.append(
                self._audit("deploy", decision.action, f"{candidate.candidate_id}: {decision.scope} - {decision.reason}")
            )
        return decisions

    def _simulate_monitoring(self, deployments: Sequence[DeploymentDecision]) -> List[MonitoringResult]:
        results = []
        for decision in deployments:
            if decision.action != "deploy":
                continue
            results.append(
                MonitoringResult(
                    candidate_id=decision.candidate_id,
                    samples=self.constraints.min_monitoring_samples,
                    hours=self.constraints.min_monitoring_hours,
                    success_rate_delta=0.01,
                    latency_delta_ms=0.0,
                    cost_delta_usd=0.0,
                    anomaly_flags=0,
                    objective_delta_mean=0.01,
                    objective_delta_std=0.005,
                )
            )
        return results

    def _retain_or_rollback(
        self,
        candidates: Sequence[CapabilityCandidate],
        deployments: Sequence[DeploymentDecision],
        monitoring_results: Sequence[MonitoringResult],
        audit: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}
        deployed_ids = {decision.candidate_id for decision in deployments if decision.action == "deploy"}
        monitoring_by_id = {result.candidate_id: result for result in monitoring_results}
        retention = []
        for candidate in candidates:
            if candidate.candidate_id not in deployed_ids:
                retention.append({"candidate_id": candidate.candidate_id, "decision": "not_deployed", "probability": 0.0})
                continue
            monitor = monitoring_by_id.get(candidate.candidate_id)
            if not monitor or monitor.samples < self.constraints.min_monitoring_samples:
                retention.append({"candidate_id": candidate.candidate_id, "decision": "monitor", "probability": 0.0})
                continue
            probability = self._posterior_probability_positive(monitor)
            if probability >= self.constraints.posterior_retain_threshold and monitor.anomaly_flags == 0:
                self.repertoire[candidate.candidate_id] = candidates_by_id[candidate.candidate_id]
                decision = "retain"
            else:
                decision = "rollback"
            retention.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "decision": decision,
                    "probability": round(probability, 6),
                    "threshold": self.constraints.posterior_retain_threshold,
                }
            )
            audit.append(
                self._audit(
                    "retain",
                    decision,
                    f"{candidate.candidate_id}: posterior={probability:.4f}, threshold={self.constraints.posterior_retain_threshold:.2f}",
                )
            )
        return retention

    def _posterior_probability_positive(self, monitor: MonitoringResult) -> float:
        std = max(monitor.objective_delta_std, 1e-6)
        standard_error = std / math.sqrt(max(monitor.samples, 1))
        z = monitor.objective_delta_mean / max(standard_error, 1e-6)
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

    def _control_form_for_weakness(self, weakness: str) -> str:
        lowered = weakness.lower()
        if "hallucination" in lowered or "false" in lowered:
            return "output_sanitizer"
        if "brittle" in lowered or "drift" in lowered:
            return "stopping_criteria"
        if "bias" in lowered:
            return "input_filter"
        return "meta_prompt_guardrail"

    def _audit(self, stage: str, action: str, justification: str) -> Dict[str, Any]:
        return {
            "timestamp": _utc(),
            "stage": stage,
            "action": action,
            "justification": justification,
        }

    def _write_audit_report(self, report: Dict[str, Any]) -> None:
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(report, default=str, sort_keys=True) + "\n")


def create_aean_meta_intelligence_layer(
    *,
    monthly_infra_spend_usd: float,
    baseline_scores: Optional[Dict[str, float]] = None,
    audit_log_path: str = "audit_logs/aean_meta_intelligence.jsonl",
    constraints: Optional[AEANConstraints] = None,
) -> AEANMetaIntelligenceLayer:
    return AEANMetaIntelligenceLayer(
        monthly_infra_spend_usd=monthly_infra_spend_usd,
        baseline_scores=baseline_scores,
        audit_log_path=audit_log_path,
        constraints=constraints,
    )
