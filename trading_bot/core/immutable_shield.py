"""
Immutable Shield - UCA-2026 Core Governance Component
===================================================

Authoritative non-bypassable safety gate for all system actions.
Implements institutional risk limits and compliance checks.
"""

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class GovernanceDecision(Enum):
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"

@dataclass
class ShieldReport:
    decision: GovernanceDecision
    reason: str
    risk_score: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    details: Dict[str, Any] = field(default_factory=dict)

class ImmutableShield:
    """
    Singleton Safety Gate for AlphaAlgo UCA-2026.
    Ensures zero-bypass of institutional constraints.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ImmutableShield, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized:
            return

        self.config = config or {
            "max_drawdown": 0.15,
            "max_volatility": 0.6,
            "max_exposure": 1.0,
            "risk_threshold": 0.7
        }
        self._audit_log: List[ShieldReport] = []
        self._initialized = True
        self._register_with_bus()
        logger.info("ImmutableShield initialized as singleton")

    def _register_with_bus(self):
        """Register the shield as a mandatory LogAct voter."""
        try:
            from .unified_event_bus import decision_bus
            decision_bus.register_voter("GovernanceShield", self.vote_on_action)
        except ImportError:
            logger.warning("ImmutableShield: Could not register with decision_bus (import error)")

    async def vote_on_action(self, action: Any) -> Dict[str, Any]:
        """LogAct Voter Interface."""
        report = self.validate_action(
            action.action_type,
            action.payload,
            action.payload.get("context", {})
        )
        return {
            "decision": "APPROVE" if report.decision == GovernanceDecision.APPROVED else "REJECT",
            "reason": report.reason,
            "audit_id": report.audit_id
        }

    def validate_action(self, action_type: str, params: Dict[str, Any], context: Dict[str, Any]) -> ShieldReport:
        """
        Validate an action against hard constraints.
        This is the only entry point for system-level approval.
        """
        risk_score = 0.0
        reasons = []

        # 1. Market volatility check
        market = context.get("market", {})
        vol = market.get("volatility", 0.0)
        if vol > self.config["max_volatility"]:
            reasons.append(f"Market volatility ({vol}) exceeds limit ({self.config['max_volatility']})")
            risk_score += 0.5

        # 2. Portfolio drawdown check
        portfolio = context.get("portfolio", {})
        drawdown = portfolio.get("drawdown", 0.0)
        if drawdown > self.config["max_drawdown"]:
            reasons.append(f"Portfolio drawdown ({drawdown}) exceeds limit ({self.config['max_drawdown']})")
            risk_score += 0.6

        # 3. Action-specific checks
        if action_type == "trade":
            exposure = params.get("exposure", 0.0)
            if exposure > self.config["max_exposure"]:
                reasons.append(f"Trade exposure ({exposure}) exceeds limit ({self.config['max_exposure']})")
                risk_score += 0.8

        elif action_type == "self_modification":
            # Strict gate for code changes
            safety_score = params.get("safety_score", 0.0)
            if safety_score < 0.95:
                reasons.append(f"Self-modification safety score ({safety_score}) below required 0.95")
                risk_score += 1.0

        # Final decision
        if risk_score >= self.config["risk_threshold"] or reasons:
            decision = GovernanceDecision.BLOCKED
            reason_str = " | ".join(reasons)
        else:
            decision = GovernanceDecision.APPROVED
            reason_str = "All checks passed"

        report = ShieldReport(
            decision=decision,
            reason=reason_str,
            risk_score=round(risk_score, 4),
            details={"params": params, "context": context}
        )

        self._log_decision(report)
        return report

    def _log_decision(self, report: ShieldReport):
        """Append to internal audit log (in production, this goes to persistent WORM storage)."""
        self._audit_log.append(report)
        log_level = logging.INFO if report.decision == GovernanceDecision.APPROVED else logging.WARNING
        logger.log(log_level, f"Governance {report.decision.value}: {report.reason} [AuditID: {report.audit_id}]")

    def get_audit_trail(self) -> List[ShieldReport]:
        return self._audit_log.copy()

# Global access point
shield = ImmutableShield()
