"""Governance policy adapters behind the canonical shield and human gate."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from trading_bot.foundation.contracts import ApprovalDecision


class HumanApprovalPolicy:
    """Adapt the legacy human gate to the typed GovernanceGate contract."""

    def __init__(self, approval_gate: Any):
        self.approval_gate = approval_gate

    async def authorize(
        self,
        action: str,
        payload: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> ApprovalDecision:
        request_id = str(uuid4())
        gate = self.approval_gate
        if gate is None:
            return ApprovalDecision(False, request_id, "Human approval gate unavailable")
        if getattr(gate, "is_action_forbidden", lambda _action: False)(action):
            return ApprovalDecision(False, request_id, f"Action '{action}' is forbidden")
        required = getattr(gate, "is_approval_required", lambda _action: True)(action)
        if not required:
            return ApprovalDecision(True, request_id, "Approval policy does not require human review", approver="policy")
        requester = getattr(gate, "request_approval", None)
        if requester is None:
            return ApprovalDecision(False, request_id, "Human approval API unavailable")
        approved = requester(
            action,
            description=f"AlphaAlgo governance approval for {action}",
            details={**dict(payload), "context": dict(context)},
            risk_assessment=str(context.get("risk_assessment", "UNKNOWN")),
        )
        if hasattr(approved, "__await__"):
            approved = await approved
        return ApprovalDecision(
            bool(approved),
            request_id,
            "Human approval granted" if approved else "Human approval rejected",
            approver="human_gate",
            evaluated_at=datetime.now(timezone.utc),
        )
