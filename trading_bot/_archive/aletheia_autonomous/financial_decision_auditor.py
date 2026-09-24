"""Aletheia-style audit gates for financial decisions.

This module keeps Aletheia in the research and verification lane. It does not
place trades or mutate risk limits; it evaluates whether a proposed APEX-FI
decision has enough evidence, invariants, and governance support to move to the
next deployment stage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


TRADE_ACTIONS = {"BUY", "SELL", "SHORT", "COVER", "LONG"}
PASSIVE_ACTIONS = {"HOLD", "NO_TRADE", "RESEARCH_ONLY"}
DEPLOYMENT_STAGES = {"research", "simulation", "paper", "shadow", "canary", "live"}


@dataclass(frozen=True)
class AletheiaAuditConfig:
    """Objective gates for Aletheia financial decision audits."""

    min_confidence: float = 0.85
    min_evidence_items: int = 3
    min_distinct_evidence_types: int = 2
    min_evidence_confidence: float = 0.70
    min_principle_score: float = 0.82
    max_expected_drawdown: float = 0.08
    min_paper_sharpe_for_live: float = 1.20
    max_paper_drawdown_for_live: float = 0.08
    required_risk_fields: Tuple[str, ...] = (
        "max_position_size",
        "max_daily_loss",
        "max_drawdown",
        "stop_loss",
        "take_profit",
    )
    required_validation_flags: Tuple[str, ...] = (
        "invariant_tests_passed",
        "adversarial_tests_passed",
        "hidden_tests_passed",
        "out_of_sample_passed",
        "lookahead_bias_check_passed",
        "stress_tests_passed",
    )
    self_approval_blocklist: Tuple[str, ...] = (
        "apex",
        "apex_fi",
        "aletheia",
        "ai",
        "agent",
        "auto",
        "self",
        "system",
    )


@dataclass(frozen=True)
class FinancialEvidenceItem:
    """Evidence item consumed by the Aletheia auditor."""

    source: str
    source_type: str
    confidence: float
    data_point: str = ""
    observed_at: Optional[datetime] = None


@dataclass(frozen=True)
class PrincipleCheck:
    """Single Aletheia principle check result."""

    principle_id: str
    name: str
    passed: bool
    message: str
    priority: str = "high"


@dataclass(frozen=True)
class AletheiaFinancialAudit:
    """Complete audit result for an APEX-FI decision proposal."""

    accepted: bool
    target_stage: str
    principle_score: float
    objective_score: float
    final_mode: str
    issues: Tuple[str, ...] = field(default_factory=tuple)
    recommendations: Tuple[str, ...] = field(default_factory=tuple)
    required_approvals: Tuple[str, ...] = field(default_factory=tuple)
    principle_checks: Tuple[PrincipleCheck, ...] = field(default_factory=tuple)
    objective_checks: Dict[str, bool] = field(default_factory=dict)
    evidence_count: int = 0
    distinct_evidence_types: int = 0
    audited_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the audit for reports and pull requests."""
        return {
            "accepted": self.accepted,
            "target_stage": self.target_stage,
            "principle_score": self.principle_score,
            "objective_score": self.objective_score,
            "final_mode": self.final_mode,
            "issues": list(self.issues),
            "recommendations": list(self.recommendations),
            "required_approvals": list(self.required_approvals),
            "principle_checks": [
                {
                    "principle_id": check.principle_id,
                    "name": check.name,
                    "passed": check.passed,
                    "message": check.message,
                    "priority": check.priority,
                }
                for check in self.principle_checks
            ],
            "objective_checks": dict(self.objective_checks),
            "evidence_count": self.evidence_count,
            "distinct_evidence_types": self.distinct_evidence_types,
            "audited_at": self.audited_at.isoformat(),
        }


class AletheiaFinancialDecisionAuditor:
    """Objective, principle-grounded reviewer for proposed financial actions."""

    def __init__(self, config: Optional[AletheiaAuditConfig] = None):
        self.config = config or AletheiaAuditConfig()

    def audit_decision(
        self,
        proposal: Mapping[str, Any],
        target_stage: str = "paper",
        governance_approved: bool = False,
        approved_by: Optional[str] = None,
        paper_trade_metrics: Optional[Mapping[str, float]] = None,
        verifier_reports: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> AletheiaFinancialAudit:
        """Audit a financial decision proposal.

        The proposal is a mapping on purpose: Aletheia can audit APEX dataclasses,
        strategy hypotheses, or serialized pull-request evidence without taking
        ownership of the live trading runtime.
        """
        normalized_stage = (target_stage or "paper").lower()
        issues: List[str] = []
        recommendations: List[str] = []
        required_approvals: List[str] = []

        objective_checks = self._run_objective_checks(
            proposal=proposal,
            target_stage=normalized_stage,
            governance_approved=governance_approved,
            approved_by=approved_by,
            paper_trade_metrics=paper_trade_metrics,
            verifier_reports=verifier_reports or (),
            issues=issues,
            recommendations=recommendations,
            required_approvals=required_approvals,
        )

        principle_checks = self._run_principle_checks(
            proposal=proposal,
            target_stage=normalized_stage,
            governance_approved=governance_approved,
            approved_by=approved_by,
            paper_trade_metrics=paper_trade_metrics,
            objective_checks=objective_checks,
        )

        for check in principle_checks:
            if not check.passed:
                issues.append(f"{check.principle_id}: {check.message}")

        principle_score = _ratio(check.passed for check in principle_checks)
        objective_score = _ratio(objective_checks.values())
        accepted = (
            normalized_stage in DEPLOYMENT_STAGES
            and not issues
            and principle_score >= self.config.min_principle_score
            and objective_score >= self.config.min_principle_score
        )

        evidence = self._evidence_items(proposal)
        final_mode = normalized_stage if accepted else "blocked"

        return AletheiaFinancialAudit(
            accepted=accepted,
            target_stage=normalized_stage,
            principle_score=principle_score,
            objective_score=objective_score,
            final_mode=final_mode,
            issues=tuple(dict.fromkeys(issues)),
            recommendations=tuple(dict.fromkeys(recommendations)),
            required_approvals=tuple(dict.fromkeys(required_approvals)),
            principle_checks=tuple(principle_checks),
            objective_checks=objective_checks,
            evidence_count=len(evidence),
            distinct_evidence_types=len({item.source_type for item in evidence if item.source_type}),
        )

    def _run_objective_checks(
        self,
        proposal: Mapping[str, Any],
        target_stage: str,
        governance_approved: bool,
        approved_by: Optional[str],
        paper_trade_metrics: Optional[Mapping[str, float]],
        verifier_reports: Sequence[Mapping[str, Any]],
        issues: List[str],
        recommendations: List[str],
        required_approvals: List[str],
    ) -> Dict[str, bool]:
        action = str(proposal.get("action", "NO_TRADE")).upper()
        confidence = _float(proposal.get("confidence"), 0.0)
        evidence = self._evidence_items(proposal)
        risk_parameters = _mapping(proposal.get("risk_parameters"))
        validation = _mapping(proposal.get("validation"))
        expected_drawdown = _float(
            proposal.get("expected_drawdown", proposal.get("max_expected_drawdown")),
            0.0,
        )
        rationale = str(proposal.get("rationale", "") or "")

        objective_checks = {
            "known_stage": target_stage in DEPLOYMENT_STAGES,
            "known_action": action in TRADE_ACTIONS | PASSIVE_ACTIONS,
            "confidence_floor": confidence >= self.config.min_confidence or action in PASSIVE_ACTIONS,
            "evidence_count": len(evidence) >= self.config.min_evidence_items or action in PASSIVE_ACTIONS,
            "evidence_diversity": (
                len({item.source_type for item in evidence if item.source_type})
                >= self.config.min_distinct_evidence_types
                or action in PASSIVE_ACTIONS
            ),
            "evidence_confidence": (
                all(item.confidence >= self.config.min_evidence_confidence for item in evidence)
                if evidence
                else action in PASSIVE_ACTIONS
            ),
            "risk_plan_complete": all(field in risk_parameters for field in self.config.required_risk_fields)
            or action in PASSIVE_ACTIONS,
            "expected_drawdown_within_limit": expected_drawdown <= self.config.max_expected_drawdown,
            "rationale_documented": len(rationale.strip()) >= 24,
        }

        for flag in self.config.required_validation_flags:
            objective_checks[flag] = bool(validation.get(flag))

        objective_checks["verifier_reports_passed"] = all(
            bool(report.get("passed", report.get("accepted", False))) for report in verifier_reports
        )

        if target_stage == "live":
            paper_metrics = _mapping(paper_trade_metrics)
            objective_checks["live_governance_approved"] = governance_approved
            objective_checks["live_approved_by_human"] = bool(approved_by) and not self._is_self_approval(
                approved_by,
                proposal,
            )
            objective_checks["live_paper_sharpe_passed"] = (
                _float(paper_metrics.get("sharpe_ratio"), 0.0) >= self.config.min_paper_sharpe_for_live
            )
            objective_checks["live_paper_drawdown_passed"] = (
                _float(paper_metrics.get("max_drawdown"), 1.0) <= self.config.max_paper_drawdown_for_live
            )
            required_approvals.append("G0_HUMAN_LIVE_TRADING_APPROVAL")
        elif target_stage in {"canary", "shadow"}:
            objective_checks["paper_trade_metrics_present"] = bool(paper_trade_metrics)
            required_approvals.append("G1_STAGING_OR_CANARY_APPROVAL")

        self._append_objective_feedback(objective_checks, issues, recommendations)
        return objective_checks

    def _run_principle_checks(
        self,
        proposal: Mapping[str, Any],
        target_stage: str,
        governance_approved: bool,
        approved_by: Optional[str],
        paper_trade_metrics: Optional[Mapping[str, float]],
        objective_checks: Mapping[str, bool],
    ) -> List[PrincipleCheck]:
        risk_parameters = _mapping(proposal.get("risk_parameters"))
        validation = _mapping(proposal.get("validation"))
        evidence = self._evidence_items(proposal)

        return [
            PrincipleCheck(
                "RM002",
                "Reasoning trace documented",
                objective_checks.get("rationale_documented", False),
                "proposal must include a meaningful rationale and reasoning trace",
                "critical",
            ),
            PrincipleCheck(
                "RM014",
                "Risk perspective applied",
                bool(risk_parameters) and objective_checks.get("risk_plan_complete", False),
                "risk parameters must be complete before promotion",
                "critical",
            ),
            PrincipleCheck(
                "RM025",
                "Out-of-sample validation",
                bool(validation.get("out_of_sample_passed")),
                "out-of-sample validation is required to avoid test overfitting",
                "critical",
            ),
            PrincipleCheck(
                "VS005",
                "Stress testing",
                bool(validation.get("stress_tests_passed")),
                "stress testing is required before paper or live promotion",
                "critical",
            ),
            PrincipleCheck(
                "VS009",
                "Lookahead bias check",
                bool(validation.get("lookahead_bias_check_passed")),
                "lookahead bias checks must pass before deployment",
                "critical",
            ),
            PrincipleCheck(
                "VS038",
                "Adversarial validation",
                bool(validation.get("adversarial_tests_passed")),
                "adversarial tests must pass to avoid brittle correctness",
                "high",
            ),
            PrincipleCheck(
                "HC009",
                "Human approval for live deployment",
                target_stage != "live"
                or (governance_approved and bool(approved_by) and not self._is_self_approval(approved_by, proposal)),
                "live deployment requires independent human or governance approval",
                "critical",
            ),
            PrincipleCheck(
                "HC013",
                "Approval history preserved",
                target_stage != "live" or bool(proposal.get("approval_evidence")),
                "live deployment must preserve approval evidence",
                "high",
            ),
            PrincipleCheck(
                "TI030",
                "Monitoring and rollback",
                bool(proposal.get("rollback_plan")) or target_stage in {"research", "simulation", "paper"},
                "canary/live promotion requires monitoring and rollback plan",
                "critical",
            ),
            PrincipleCheck(
                "RM031",
                "Data provenance",
                len(evidence) >= self.config.min_evidence_items,
                "evidence and data provenance must be attached to the proposal",
                "high",
            ),
        ]

    def _append_objective_feedback(
        self,
        objective_checks: Mapping[str, bool],
        issues: List[str],
        recommendations: List[str],
    ) -> None:
        messages = {
            "known_stage": "unknown target deployment stage",
            "known_action": "unknown or unsupported trading action",
            "confidence_floor": "decision confidence is below the objective floor",
            "evidence_count": "proposal has too few evidence items",
            "evidence_diversity": "proposal needs distinct evidence source types",
            "evidence_confidence": "one or more evidence items are below confidence floor",
            "risk_plan_complete": "risk plan is missing required fields",
            "expected_drawdown_within_limit": "expected drawdown exceeds Aletheia audit limit",
            "rationale_documented": "rationale is missing or too thin",
            "invariant_tests_passed": "invariant tests must pass",
            "adversarial_tests_passed": "adversarial tests must pass",
            "hidden_tests_passed": "hidden tests must pass",
            "out_of_sample_passed": "out-of-sample validation must pass",
            "lookahead_bias_check_passed": "lookahead bias check must pass",
            "stress_tests_passed": "stress tests must pass",
            "verifier_reports_passed": "one or more verifier reports rejected the proposal",
            "live_governance_approved": "live promotion lacks governance approval",
            "live_approved_by_human": "live promotion lacks independent human approval",
            "live_paper_sharpe_passed": "paper trading Sharpe is below live gate",
            "live_paper_drawdown_passed": "paper trading drawdown exceeds live gate",
            "paper_trade_metrics_present": "shadow or canary promotion requires paper-trade metrics",
        }

        for name, passed in objective_checks.items():
            if passed:
                continue
            message = messages.get(name, f"objective check failed: {name}")
            issues.append(message)
            recommendations.append(f"Fix objective gate: {name}")

    def _evidence_items(self, proposal: Mapping[str, Any]) -> List[FinancialEvidenceItem]:
        raw_items = proposal.get("evidence", proposal.get("citations", ())) or ()
        items = []
        for raw in raw_items:
            if isinstance(raw, FinancialEvidenceItem):
                items.append(raw)
                continue
            if not isinstance(raw, Mapping):
                continue
            items.append(
                FinancialEvidenceItem(
                    source=str(raw.get("source", raw.get("source_name", ""))),
                    source_type=str(raw.get("source_type", raw.get("type", ""))),
                    confidence=_float(raw.get("confidence"), 0.0),
                    data_point=str(raw.get("data_point", raw.get("summary", ""))),
                    observed_at=raw.get("observed_at") if isinstance(raw.get("observed_at"), datetime) else None,
                )
            )
        return items

    def _is_self_approval(self, approved_by: str, proposal: Mapping[str, Any]) -> bool:
        approver = approved_by.lower().strip()
        generated_by = str(proposal.get("generated_by", "")).lower()
        if generated_by and approver == generated_by:
            return True
        return any(token in approver for token in self.config.self_approval_blocklist)


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _ratio(values: Iterable[bool]) -> float:
    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(1 for value in materialized if value) / len(materialized)
