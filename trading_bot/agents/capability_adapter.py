"""Capability-only adapter for legacy multi-agent debate systems."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

from trading_bot.foundation.ports import AgentCapabilityPort


class DebateCapabilityAdapter:
    """Expose legacy debate as advisory evidence, never as an order authority."""

    def __init__(self, debate_system: Any, capability_id: str = "multi_agent_debate") -> None:
        if debate_system is None or not hasattr(debate_system, "debate"):
            raise ValueError("debate_system must implement debate()")
        self.debate_system = debate_system
        self.capability_id = capability_id

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        result = self.debate_system.debate(context.get("topic", context), context.get("market_context"))
        if inspect.isawaitable(result):
            result = await result
        if hasattr(result, "to_dict"):
            result = result.to_dict()
        if isinstance(result, Mapping):
            return {
                "capability_id": self.capability_id,
                "evidence": dict(result),
                "advisory_only": True,
            }
        return {
            "capability_id": self.capability_id,
            "evidence": {"result": result},
            "advisory_only": True,
        }
