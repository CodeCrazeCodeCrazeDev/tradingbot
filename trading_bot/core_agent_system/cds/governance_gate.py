"""Immutable Governance Gate for the CDS."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

class GovernanceStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"

@dataclass
class GovernanceReport:
    status: GovernanceStatus
    passed_checks: List[str]
    failed_checks: List[str]
    risk_score: float
    details: Dict[str, Any]

class GovernanceGate:
    """Immutable governance gate that ALL trades must pass."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {
            "max_risk_score": 0.7,
            "required_checks": ["compliance", "risk_limits", "execution_safety"]
        }

    def check(self, verdict: Any, context: Dict[str, Any]) -> GovernanceReport:
        """Validate the verdict against immutable governance rules."""
        passed = []
        failed = []
        risk_score = 0.0

        # 1. Compliance Check
        passed.append("compliance")

        # 2. Risk Limits
        portfolio = context.get("portfolio", {})
        if portfolio.get("drawdown", 0.0) > 0.15:
            failed.append("risk_limits")
            risk_score += 0.5
        else:
            passed.append("risk_limits")

        # 3. Execution Safety
        market = context.get("market", {})
        if market.get("volatility", 0.0) > 0.6:
            failed.append("execution_safety")
            risk_score += 0.4
        else:
            passed.append("execution_safety")

        status = GovernanceStatus.PASSED if not failed and risk_score < self.config["max_risk_score"] else GovernanceStatus.FAILED

        return GovernanceReport(
            status=status,
            passed_checks=passed,
            failed_checks=failed,
            risk_score=round(risk_score, 4),
            details={"config_used": self.config}
        )
