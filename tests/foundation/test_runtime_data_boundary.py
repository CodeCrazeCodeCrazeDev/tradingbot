"""Runtime integration tests for observation normalization and rejection."""

import pytest

from trading_bot.unified_bot import UnifiedTradingBot


class _Brain:
    def __init__(self):
        self.observations = []

    async def process_market_observation(self, observation):
        self.observations.append(observation)
        return {"status": "accepted"}


def _wire_human_allow(bot: UnifiedTradingBot) -> None:
    """Attach a permissive human gate for data-boundary tests."""
    bot.layers["human"] = {"is_trading_allowed": lambda: True}


@pytest.mark.asyncio
async def test_runtime_rejects_invalid_observations_before_cognition() -> None:
    bot = UnifiedTradingBot({"mode": "paper"})
    _wire_human_allow(bot)
    brain = _Brain()
    bot.csc = brain

    result = await bot.run_cycle({"symbol": "EURUSD", "price": -1})

    assert result is None
    assert brain.observations == []


@pytest.mark.asyncio
async def test_runtime_attaches_canonical_event_identity() -> None:
    bot = UnifiedTradingBot({"mode": "paper"})
    _wire_human_allow(bot)
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
    _wire_human_allow(bot)
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


@pytest.mark.asyncio
async def test_runtime_denies_entries_when_human_layer_missing() -> None:
    """Fail-closed: without a wired human override layer the cycle must not
    reach the brain — a missing pause/emergency-stop control is not consent."""
    bot = UnifiedTradingBot({"mode": "paper"})
    brain = _Brain()
    bot.csc = brain

    result = await bot.run_cycle({"symbol": "EURUSD", "price": 1.1, "timestamp": 1_700_000_000})

    assert result is None
    assert brain.observations == []


@pytest.mark.asyncio
async def test_runtime_denies_entries_when_override_check_raises() -> None:
    """A throwing is_trading_allowed() must deny, not silently allow."""

    def _boom():
        raise RuntimeError("override store offline")

    bot = UnifiedTradingBot({"mode": "paper"})
    bot.layers["human"] = {"is_trading_allowed": _boom}
    brain = _Brain()
    bot.csc = brain

    result = await bot.run_cycle({"symbol": "EURUSD", "price": 1.1, "timestamp": 1_700_000_000})

    assert result is None
    assert brain.observations == []


@pytest.mark.asyncio
async def test_enrich_observation_populates_rsi_features() -> None:
    """Regression: once the 15-bar price window fills, enrichment must resolve
    its indicator (wilder_rsi) — a missing name here NameError-crashed runs."""
    bot = UnifiedTradingBot({"mode": "paper"})
    obs = {}
    for i in range(16):
        obs = bot.enrich_observation({"symbol": "EURUSD", "price": 1.0 + i * 0.001})

    assert isinstance(obs["rsi"], float) and 0.0 <= obs["rsi"] <= 100.0
    assert obs["rsi_signal"]["action"] in {"sell_bias", "buy_bias", "neutral"}
    assert obs["trend"] == "UP"


@pytest.mark.asyncio
async def test_runtime_denies_entries_when_trading_paused() -> None:
    bot = UnifiedTradingBot({"mode": "paper"})
    bot.layers["human"] = {"is_trading_allowed": lambda: False}
    brain = _Brain()
    bot.csc = brain

    result = await bot.run_cycle({"symbol": "EURUSD", "price": 1.1, "timestamp": 1_700_000_000})

    assert result is None
    assert brain.observations == []
