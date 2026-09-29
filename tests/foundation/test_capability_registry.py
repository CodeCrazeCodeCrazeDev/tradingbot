"""Tests for the non-authoritative AI capability registry."""

import pytest

from trading_bot.foundation.capability_registry import CapabilityRegistry


@pytest.mark.asyncio
async def test_capability_registry_analyzes_without_execution_authority() -> None:
    class Capability:
        capability_id = "test_capability"

        async def analyze(self, context):
            return {"evidence": {"symbol": context["symbol"]}, "advisory_only": True}

    registry = CapabilityRegistry()
    registry.register(Capability(), domain="test")
    result = await registry.analyze("test_capability", {"symbol": "EURUSD"})

    assert result["advisory_only"] is True
    assert result["evidence"]["symbol"] == "EURUSD"
