"""Tests for advisory-only legacy agent capability adaptation."""

import pytest

from trading_bot.agents.capability_adapter import DebateCapabilityAdapter
from trading_bot.foundation import AgentCapabilityPort


@pytest.mark.asyncio
async def test_debate_adapter_returns_advisory_evidence_only() -> None:
    class Debate:
        async def debate(self, topic, context):
            return {"action": "hold", "consensus": 0.8, "topic": topic}

    adapter = DebateCapabilityAdapter(Debate())
    result = await adapter.analyze({"topic": "EURUSD", "market_context": {"price": 1.1}})

    assert isinstance(adapter, AgentCapabilityPort)
    assert result["advisory_only"] is True
    assert result["evidence"]["action"] == "hold"
