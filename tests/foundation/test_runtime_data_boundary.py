"""Runtime integration tests for observation normalization and rejection."""

import pytest

from trading_bot.unified_bot import UnifiedTradingBot


class _Brain:
    def __init__(self):
        self.observations = []

    async def process_market_observation(self, observation):
        self.observations.append(observation)
        return {"status": "accepted"}


@pytest.mark.asyncio
async def test_runtime_rejects_invalid_observations_before_cognition() -> None:
    bot = UnifiedTradingBot({"mode": "paper"})
    brain = _Brain()
    bot.csc = brain

    result = await bot.run_cycle({"symbol": "EURUSD", "price": -1})

    assert result is None
    assert brain.observations == []


@pytest.mark.asyncio
async def test_runtime_attaches_canonical_event_identity() -> None:
    bot = UnifiedTradingBot({"mode": "paper"})
    brain = _Brain()
    bot.csc = brain

    result = await bot.run_cycle({"symbol": "EURUSD", "price": 1.1, "timestamp": 1_700_000_000})

    assert result == {"status": "accepted"}
    assert brain.observations[0]["data_quality"] == "valid"
    assert brain.observations[0]["market_event_id"]


@pytest.mark.asyncio
async def test_runtime_attaches_strategy_advice_without_execution_authority() -> None:
    from trading_bot.foundation.contracts import Instrument, InstrumentType, Signal

    bot = UnifiedTradingBot({"mode": "paper", "strategy_id": "test_strategy"})
    brain = _Brain()

    class Strategy:
        strategy_id = "test_strategy"

        async def generate_signal(self, market):
            return [Signal(
                "signal-1",
                Instrument("EURUSD", InstrumentType.FX, "paper"),
                "buy",
                0.8,
                strategy_id="test_strategy",
            )]

    bot.register_strategy_adapter(Strategy())
    bot.csc = brain
    await bot.run_cycle({"symbol": "EURUSD", "price": 1.1, "timestamp": 1_700_000_000})

    assert brain.observations[0]["strategy_advisory_only"] is True
    assert brain.observations[0]["strategy_signals"][0]["strategy_id"] == "test_strategy"
