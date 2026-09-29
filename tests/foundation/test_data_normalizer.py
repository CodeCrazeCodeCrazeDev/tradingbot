"""Tests for the canonical market-data normalization boundary."""

from datetime import timezone

import pytest

from trading_bot.data.normalizer import MarketDataNormalizer
from trading_bot.foundation import DataQuality, InstrumentType, MarketEventType


def test_normalizer_converts_legacy_bar_with_provenance() -> None:
    event = MarketDataNormalizer().normalize(
        {
            "symbol": "AAPL",
            "timestamp": "2026-01-01T12:00:00Z",
            "open": 100,
            "high": 105,
            "low": 99,
            "close": 104,
            "volume": 1000,
            "asset_class": "equities",
            "feed_id": "replay-1",
        },
        source="historical_replay",
    )

    assert event.event_type is MarketEventType.BAR
    assert event.instrument.instrument_type is InstrumentType.EQUITY
    assert event.quality is DataQuality.VALID
    assert event.source_timestamp.tzinfo is timezone.utc
    assert event.provenance["source"] == "historical_replay"
    assert event.provenance["feed_id"] == "replay-1"


def test_normalizer_marks_invalid_market_values() -> None:
    event = MarketDataNormalizer().normalize(
        {
            "symbol": "BTC/USDT",
            "timestamp": 1_700_000_000,
            "price": -1,
            "asset_class": "crypto",
        },
        source="test",
    )

    assert event.event_type is MarketEventType.TRADE
    assert event.instrument.instrument_type is InstrumentType.CRYPTO_SPOT
    assert event.quality is DataQuality.INVALID


def test_normalizer_requires_symbol() -> None:
    with pytest.raises(ValueError, match="symbol"):
        MarketDataNormalizer().normalize({"price": 10})
