"""Governed bridge between APEX-FI decisions and Aletheia verification.

APEX-FI can produce financial proposals. Aletheia can audit the reasoning,
evidence, invariants, and deployment readiness. This bridge keeps those
responsibilities separate so the live runtime remains deterministic and unable
to self-approve or self-deploy.
"""

from dataclasses import dataclass, field
from datetime import datetime
import importlib.util
from pathlib import Path
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


CONSTITUTIONAL_LIMITS = {
    "MAX_BOOK_DRAWDOWN": 0.08,
    "MAX_STRATEGY_DRAWDOWN": 0.15,
    "MAX_POSITION_CONCENTRATION": 0.03,
    "MAX_MARKET_IMPACT": 0.05,
    "MIN_VALIDATION_TSTAT": 2.0,
    "MIN_SANDBOX_DAYS": 30,
}

TRADE_ACTIONS = {"BUY", "SELL", "SHORT", "COVER", "LONG"}


@dataclass(frozen=True)
class ApexEvidence:
    """Evidence attached to an APEX proposal."""

    source: str
    source_type: str
    confidence: float
    data_point: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "data_point": self.data_point,
        }


@dataclass(frozen=True)
class ApexRiskEnvelope:
    """Constitutional risk inputs for a proposed APEX action."""

    position_value: float = 0.0
    portfolio_nav: float = 1.0
    order_quantity: float = 0.0
    avg_daily_volume_20d: float = 1.0
    expected_drawdown: float = 0.0
    leverage: float = 1.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "position_value": self.position_value,
            "portfolio_nav": self.portfolio_nav,
            "order_quantity": self.order_quantity,
            "avg_daily_volume_20d": self.avg_daily_volume_20d,
            "expected_drawdown": self.expected_drawdown,
            "leverage": self.leverage,
        }


@dataclass(frozen=True)
class ApexProposal:
    """APEX-FI decision proposal awaiting Aletheia and governance review."""

    proposal_id: str
    symbol: str
    action: str
    confidence: float
    rationale: str
    risk_parameters: Dict[str, Any]
    validation: Dict[str, bool]
    evidence: Tuple[ApexEvidence, ...] = field(default_factory=tuple)
    risk_envelope: ApexRiskEnvelope = field(default_factory=ApexRiskEnvelope)
    expected_return: float = 0.0
    generated_by: str = "apex_fi"
    strategy_id: Optional[str] = None
    approval_evidence: Optional[str] = None
    rollback_plan: Optional[str] = None
    protected_risk_changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_audit_payload(self) -> Dict[str, Any]:
        """Return a serializable payload for the Aletheia auditor."""
        payload = {
            "proposal_id": self.proposal_id,
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "risk_parameters": dict(self.risk_parameters),
            "validation": dict(self.validation),
            "evidence": [item.to_dict() for item in self.evidence],
            "expected_return": self.expected_return,
            "expected_drawdown": self.risk_envelope.expected_drawdown,
            "generated_by": self.generated_by,
            "strategy_id": self.strategy_id,
            "approval_evidence": self.approval_evidence,
            "rollback_plan": self.rollback_plan,
            "metadata": dict(self.metadata),
        }
        return payload


@dataclass(frozen=True)
class ApexAletheiaBridgeConfig:
    """Configuration for the APEX to Aletheia control bridge."""

    max_position_concentration: float = CONSTITUTIONAL_LIMITS["MAX_POSITION_CONCENTRATION"]
    max_market_impact: float = CONSTITUTIONAL_LIMITS["MAX_MARKET_IMPACT"]
    max_book_drawdown: float = CONSTITUTIONAL_LIMITS["MAX_BOOK_DRAWDOWN"]
    max_leverage: float = 5.0
    require_rollback_for_live: bool = True
    protected_max_fields: Tuple[str, ...] = (
        "MAX_BOOK_DRAWDOWN",
        "MAX_STRATEGY_DRAWDOWN",
        "MAX_POSITION_CONCENTRATION",
        "MAX_MARKET_IMPACT",
    )
    protected_min_fields: Tuple[str, ...] = (
        "MIN_VALIDATION_TSTAT",
        "MIN_SANDBOX_DAYS",
    )


@dataclass(frozen=True)
class ApexAletheiaGovernedDecision:
    """Combined APEX risk and Aletheia audit decision."""

    proposal_id: str
    accepted: bool
    target_stage: str
    final_action: str
    audit: Any
    constitutional_issues: Tuple[str, ...] = field(default_factory=tuple)
    protected_risk_issues: Tuple[str, ...] = field(default_factory=tuple)
    promotion_path: Tuple[str, ...] = field(default_factory=tuple)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def issues(self) -> Tuple[str, ...]:
        audit_issues = tuple(getattr(self.audit, "issues", ()))
        return audit_issues + self.constitutional_issues + self.protected_risk_issues

    def to_engineering_report(self) -> Dict[str, Any]:
        """Serialize the decision for PRs, governance, and monitoring."""
        audit_payload = self.audit.to_dict() if hasattr(self.audit, "to_dict") else self.audit
        return {
            "proposal_id": self.proposal_id,
            "accepted": self.accepted,
            "target_stage": self.target_stage,
            "final_action": self.final_action,
            "issues": list(self.issues),
            "constitutional_issues": list(self.constitutional_issues),
            "protected_risk_issues": list(self.protected_risk_issues),
            "promotion_path": list(self.promotion_path),
            "audit": audit_payload,
            "generated_at": self.generated_at.isoformat(),
        }


class ApexAletheiaBridge:
    """Evaluate APEX proposals through Aletheia and constitutional gates."""

    def __init__(
        self,
        config: Optional[ApexAletheiaBridgeConfig] = None,
        auditor: Optional[Any] = None,
    ):
        self.config = config or ApexAletheiaBridgeConfig()
        self.auditor = auditor or _build_default_auditor()

    def evaluate(
        self,
        proposal: ApexProposal,
        target_stage: str = "paper",
        governance_approved: bool = False,
        approved_by: Optional[str] = None,
        paper_trade_metrics: Optional[Mapping[str, float]] = None,
        verifier_reports: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> ApexAletheiaGovernedDecision:
        """Evaluate whether a proposal can move to the requested stage."""
        stage = (target_stage or "paper").lower()
        audit = self.auditor.audit_decision(
            proposal.to_audit_payload(),
            target_stage=stage,
            governance_approved=governance_approved,
            approved_by=approved_by,
            paper_trade_metrics=paper_trade_metrics,
            verifier_reports=verifier_reports,
        )
        constitutional_issues = tuple(self._constitutional_issues(proposal))
        protected_risk_issues = tuple(self._protected_risk_issues(proposal))

        accepted = bool(audit.accepted) and not constitutional_issues and not protected_risk_issues
        final_action = proposal.action.upper() if accepted else "NO_TRADE"

        return ApexAletheiaGovernedDecision(
            proposal_id=proposal.proposal_id,
            accepted=accepted,
            target_stage=stage,
            final_action=final_action,
            audit=audit,
            constitutional_issues=constitutional_issues,
            protected_risk_issues=protected_risk_issues,
            promotion_path=tuple(self._promotion_path(stage, accepted)),
        )

    def from_strategy_hypothesis(
        self,
        hypothesis: Any,
        symbol: str,
        action: str,
        evidence: Sequence[ApexEvidence],
        risk_envelope: Optional[ApexRiskEnvelope] = None,
        validation: Optional[Mapping[str, bool]] = None,
    ) -> ApexProposal:
        """Adapt an Aletheia StrategyHypothesis into an APEX proposal."""
        risk_parameters = dict(getattr(hypothesis, "risk_parameters", {}) or {})
        expected_performance = dict(getattr(hypothesis, "expected_performance", {}) or {})
        confidence = float(getattr(hypothesis, "confidence_score", 0.0) or 0.0)
        expected_drawdown = _normalize_percentage(
            expected_performance.get("expected_max_drawdown", risk_parameters.get("max_drawdown", 0.0))
        )
        envelope = risk_envelope or ApexRiskEnvelope(expected_drawdown=expected_drawdown)
        proposal_id = str(getattr(hypothesis, "hypothesis_id", "") or f"hypothesis_{id(hypothesis)}")
        rationale = " ".join(
            str(part)
            for part in (
                getattr(hypothesis, "rationale", ""),
                " ".join(getattr(hypothesis, "entry_rules", []) or ()),
                " ".join(getattr(hypothesis, "exit_rules", []) or ()),
            )
            if part
        )

        return ApexProposal(
            proposal_id=proposal_id,
            symbol=symbol,
            action=action,
            confidence=confidence,
            rationale=rationale,
            risk_parameters=risk_parameters,
            validation=dict(validation or {}),
            evidence=tuple(evidence),
            risk_envelope=envelope,
            expected_return=_normalize_percentage(expected_performance.get("expected_return", 0.0)),
            generated_by="aletheia_hypothesis",
            strategy_id=proposal_id,
        )

    def _constitutional_issues(self, proposal: ApexProposal) -> List[str]:
        action = proposal.action.upper()
        envelope = proposal.risk_envelope
        issues: List[str] = []

        if envelope.portfolio_nav <= 0:
            issues.append("portfolio NAV must be positive for constitutional risk checks")
            return issues

        concentration = abs(envelope.position_value) / envelope.portfolio_nav
        if concentration > self.config.max_position_concentration:
            issues.append(
                "position concentration "
                f"{concentration:.2%} exceeds constitutional limit "
                f"{self.config.max_position_concentration:.2%}"
            )

        if action in TRADE_ACTIONS:
            if envelope.avg_daily_volume_20d <= 0:
                issues.append("20-day average daily volume must be positive for market impact check")
            else:
                market_impact = abs(envelope.order_quantity) / envelope.avg_daily_volume_20d
                if market_impact > self.config.max_market_impact:
                    issues.append(
                        "market impact "
                        f"{market_impact:.2%} exceeds constitutional limit "
                        f"{self.config.max_market_impact:.2%}"
                    )

        if envelope.expected_drawdown > self.config.max_book_drawdown:
            issues.append(
                "expected drawdown "
                f"{envelope.expected_drawdown:.2%} exceeds book drawdown limit "
                f"{self.config.max_book_drawdown:.2%}"
            )

        if envelope.leverage > self.config.max_leverage:
            issues.append(
                f"leverage {envelope.leverage:.2f}x exceeds bridge limit {self.config.max_leverage:.2f}x"
            )

        if self.config.require_rollback_for_live and proposal.metadata.get("target_stage") == "live":
            if not proposal.rollback_plan:
                issues.append("live proposal is missing rollback plan")

        return issues

    def _protected_risk_issues(self, proposal: ApexProposal) -> List[str]:
        issues: List[str] = []
        for name, change in proposal.protected_risk_changes.items():
            old_value, new_value = _extract_change_values(name, change)
            if old_value is None or new_value is None:
                issues.append(f"protected risk change {name} is malformed")
                continue

            if name in self.config.protected_max_fields and new_value > old_value:
                issues.append(
                    f"protected risk field {name} weakens from {old_value} to {new_value}"
                )
            elif name in self.config.protected_min_fields and new_value < old_value:
                issues.append(
                    f"protected validation field {name} weakens from {old_value} to {new_value}"
                )
        return issues

    def _promotion_path(self, stage: str, accepted: bool) -> List[str]:
        if not accepted:
            return ["blocked", "root_cause_fix", "resubmit_with_evidence"]

        path = [
            "apex_proposal",
            "aletheia_principle_audit",
            "constitutional_risk_gate",
            "sandbox_simulation",
        ]
        if stage in {"paper", "shadow", "canary", "live"}:
            path.append("paper_trade_validation")
        if stage in {"shadow", "canary", "live"}:
            path.append("shadow_or_canary_monitoring")
        if stage == "live":
            path.extend(["G0_governance_approval", "rollback_armed", "production_monitoring"])
        return path


def _build_default_auditor() -> Any:
    module = _load_aletheia_auditor_module()
    return module.AletheiaFinancialDecisionAuditor()


def _load_aletheia_auditor_module() -> Any:
    module_name = "_alphaalgo_aletheia_financial_decision_auditor"
    if module_name in sys.modules:
        return sys.modules[module_name]

    auditor_path = Path(__file__).resolve().parents[1] / "aletheia_autonomous" / "financial_decision_auditor.py"
    spec = importlib.util.spec_from_file_location(module_name, auditor_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Aletheia auditor from {auditor_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _normalize_percentage(value: Any) -> float:
    raw = _float(value, 0.0)
    return raw / 100.0 if raw > 1.0 else raw


def _extract_change_values(name: str, change: Any) -> Tuple[Optional[float], Optional[float]]:
    if isinstance(change, Mapping):
        old_value = _float(change.get("old", CONSTITUTIONAL_LIMITS.get(name)), None)
        new_value = _float(change.get("new"), None)
        return old_value, new_value
    if isinstance(change, (list, tuple)) and len(change) == 2:
        return _float(change[0], None), _float(change[1], None)
    return _float(CONSTITUTIONAL_LIMITS.get(name), None), _float(change, None)


def _float(value: Any, default: Optional[float]) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
