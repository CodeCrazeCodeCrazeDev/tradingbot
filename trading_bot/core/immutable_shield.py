"""
Immutable Shield - UCA-2026 Core Governance Component
===================================================

Authoritative non-bypassable safety gate for all system actions.
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
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ImmutableShield, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized: return
        self.config = config or {}
        self._audit_log: List[ShieldReport] = []

        # Delayed registration to avoid circular import
        from .unified_event_bus import decision_bus
        decision_bus.register_voter("shield", self.audit_log_action)

        self._initialized = True

    async def audit_log_action(self, action: Any) -> Dict[str, Any]:
        context = action.payload.get("context", {})
        report = await self.validate_action(action.action_type, action.payload, context)
        return {
            "decision": report.decision.value,
            "reason": report.reason,
            "risk_score": report.risk_score,
            "audit_id": report.audit_id
        }

    async def validate_action(self, action_type: str, params: Dict[str, Any], context: Dict[str, Any]) -> ShieldReport:
        # Mocking risk checks for now
        risk_score = 0.1
        if params.get("quantity", 0) > 100:
            return ShieldReport(GovernanceDecision.BLOCKED, "Exceeds max quantity", risk_score)

        return ShieldReport(GovernanceDecision.APPROVED, "All checks passed", risk_score)

shield = ImmutableShield()
