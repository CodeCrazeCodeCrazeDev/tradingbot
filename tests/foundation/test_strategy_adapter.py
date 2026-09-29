"""Tests for typed legacy strategy/signal adaptation."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from trading_bot.foundation import StrategyPort
from trading_bot.strategies.adapter import LegacyStrategyAdapter


@dataclass
class LegacySignal:
    symbol: str = "EURUSD"
    direction: str = "buy"
    confidence: float = 75.0
    rationale: str = "legacy signal"
    time: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc)
    stop_loss_pips: float = 15.0
    take_profit_rr: float = 2.0


@pytest.mark.asyncio
async def test_legacy_strategy_emits_typed_signal_without_order_authority() -> None:
    class Engine:
        def analyse(self, bars):
            assert bars == ["bar"]
            return [LegacySignal()]

    adapter = LegacyStrategyAdapter("legacy_strategy", Engine())
    result = await adapter.generate_signal({"symbol": "EURUSD", "bars": ["bar"]})

    assert isinstance(adapter, StrategyPort)
    assert len(result) == 1
    assert result[0].strategy_id == "legacy_strategy"
    assert result[0].confidence == 0.75
    assert result[0].instrument.symbol == "EURUSD"
    assert result[0].metadata["stop_loss_pips"] == 15.0
