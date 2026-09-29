"""Tests for the legacy market-feed adapter."""

from datetime import datetime, timezone

import pytest

from trading_bot.connectivity.market_data_stream import MarketDataStream, MarketTick
from trading_bot.data.adapters import LegacyMarketDataAdapter
from trading_bot.foundation import Instrument, InstrumentType


@pytest.mark.asyncio
async def test_legacy_market_stream_adapter_normalizes_snapshot() -> None:
    stream = MarketDataStream()
    adapter = LegacyMarketDataAdapter(stream)
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    await adapter.connect()
    await stream.on_tick(MarketTick("EURUSD", 1.09, 1.10, 1.095, 1000, datetime.now(timezone.utc)))

    events = await adapter.snapshot(instrument)

    assert len(events) == 1
    assert events[0].instrument.symbol == "EURUSD"
    assert events[0].payload["last"] == 1.095
    assert events[0].provenance["source"] == "legacy_market_data_stream"
    await adapter.disconnect()
