"""Tests for the canonical signal-only strategy registry."""

import pytest

from trading_bot.strategies.adapter import LegacyStrategyAdapter
from trading_bot.strategies.registry import StrategyRegistry


@pytest.mark.asyncio
async def test_strategy_registry_registers_and_emits_signals_only() -> None:
    class Legacy:
        def generate_signal(self, market):
            return []

    registry = StrategyRegistry()
    registration = registry.register(
        LegacyStrategyAdapter("legacy_signal", Legacy()),
        metadata={"evidence": "paper_fixture"},
    )
    result = await registry.generate_signals("legacy_signal", {"symbol": "EURUSD"})

    assert registration.strategy_id == "legacy_signal"
    assert result == []
    assert registry.list()[0].metadata["evidence"] == "paper_fixture"


def test_strategy_registry_rejects_non_strategy_authority() -> None:
    class NotAStrategy:
        pass

    registry = StrategyRegistry()
    with pytest.raises(TypeError, match="generate_signal"):
        registry.register(NotAStrategy(), strategy_id="invalid")
