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
        # Sizing / trade-parameter vocabulary emitted by regime adapters
        # and strategy analyzers — evidence may describe a setup but must
        # never carry entry/stop/target/size instructions.
        "position_size",
        "size_adjustment",
        "size_adj",
        "stop_adjustment",
        "stop_adj",
        "target_adjustment",
        "target_adj",
        "stop_loss",
        "take_profit",
        "entry_price",
        "risk_per_trade",
        "leverage",
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
        # Normalized advisory contract: direction from the brain's market
        # state, confidence from its calibrated probability — so the CSC
        # can reliability-weight this advisor like any other.
        direction = None
        ms = evidence.get("market_state")
        if isinstance(ms, Mapping):
            direction = {"BULLISH": "BUY", "BEARISH": "SELL"}.get(
                str(ms.get("trend_direction") or "").upper())
        conf = evidence.get("calibrated_probability")
        confidence = float(conf) if isinstance(conf, (int, float)) \
            and 0.0 <= conf <= 1.0 else None
        return {
            "capability_id": self.capability_id,
            "direction": direction,
            "confidence": confidence,
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
