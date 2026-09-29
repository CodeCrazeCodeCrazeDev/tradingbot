"""Advisory-only adapter for AlphaAlgoCognitiveBrain.

The brain's ``process_cycle`` returns ``authorized_action`` /
``authorized_size`` produced by its internal ``RiskGatekeeper`` — a shadow
risk authority. This adapter strips every authorization field and re-emits
the cycle output as capability evidence matching ``AgentCapabilityPort``,
so the brain can never approve, size, or order. Only ``CanonicalRiskService``
sizes; only the governance/shield path authorizes.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Mapping

from trading_bot.cognition.orchestrator import AlphaAlgoCognitiveBrain

# Fields the brain emits that imply approval, sizing, or execution authority.
# Stripped unconditionally — advisory evidence must not carry them.
AUTHORITY_FIELDS = frozenset(
    {
        "authorized_action",
        "authorized_size",
        "risk_authorized",
        "rejection_reason",
        "approval",
        "approve",
        "veto",
        "quantity",
        "order",
        "execution",
    }
)


class AdvisoryCognitiveBrain:
    """Wrap AlphaAlgoCognitiveBrain as capability evidence (advisory only)."""

    capability_id = "alphaalgo_cognitive_brain"

    def __init__(self, brain: AlphaAlgoCognitiveBrain = None) -> None:
        self.brain = brain or AlphaAlgoCognitiveBrain()

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        result = self.brain.process_cycle(
            instrument=str(context.get("instrument") or context.get("symbol") or "UNKNOWN"),
            raw_market_data=context.get("raw_market_data", {}),
            proposed_trade_signal=str(context.get("signal", "NEUTRAL")),
            stop_loss_price=context.get("stop_loss_price"),
        )
        if inspect.isawaitable(result):
            result = await result
        evidence = self._strip_authority(result if isinstance(result, Mapping) else {})
        return {
            "capability_id": self.capability_id,
            "evidence": evidence,
            "advisory_only": True,
        }

    @staticmethod
    def _strip_authority(payload: Mapping[str, Any]) -> Dict[str, Any]:
        evidence: Dict[str, Any] = {}
        for key, value in payload.items():
            if key in AUTHORITY_FIELDS or key.startswith(("authorized", "risk_")):
                continue
            evidence[key] = (
                AdvisoryCognitiveBrain._strip_authority(value)
                if isinstance(value, Mapping)
                else value
            )
        return evidence
