"""
Immutable Shield - UCA-2026 Core Governance Component
===================================================

Authoritative non-bypassable safety gate for all system actions.
Enforced by the UnifiedRiskEngine.
"""

import logging
import threading
import asyncio
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
    Zero-bypass of institutional constraints.
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

        self.config = config or {}
        self._audit_log: List[ShieldReport] = []
        self._initialized = True
        logger.info("ImmutableShield initialized as singleton")

    async def validate_action(self, action_type: str, params: Dict[str, Any], context: Dict[str, Any]) -> ShieldReport:
        """
        Validate an action using the UnifiedRiskEngine as the primary evaluator.
        """
        from .risk.unified_risk_engine import risk_engine

        # 1. Institutional Risk Engine Audit
        risk_result = await risk_engine.evaluate_risk(params, context)

        # 2. Safety Heuristics (Local constraints)
        reasons = risk_result.violated_constraints

        if action_type == "self_modification":
             safety_score = params.get("safety_score", 0.0)
             if safety_score < 0.95:
                 reasons.append(f"Self-mod safety score {safety_score} < 0.95")

        # Final decision
        if not risk_result.approved or reasons:
            decision = GovernanceDecision.BLOCKED
            reason_str = " | ".join(reasons)
        else:
            decision = GovernanceDecision.APPROVED
            reason_str = "All risk checks passed"

        report = ShieldReport(
            decision=decision,
            reason=reason_str,
            risk_score=risk_result.risk_score,
            details={"risk_evidence": risk_result.evidence, "recommended_size": risk_result.recommended_position_size}
        )

        self._log_decision(report)
        return report

    def _log_decision(self, report: ShieldReport):
        self._audit_log.append(report)
        log_level = logging.INFO if report.decision == GovernanceDecision.APPROVED else logging.WARNING
        logger.log(log_level, f"Governance {report.decision.value}: {report.reason}")

    def get_audit_trail(self) -> List[ShieldReport]:
        return self._audit_log.copy()

# Global access point
shield = ImmutableShield()
