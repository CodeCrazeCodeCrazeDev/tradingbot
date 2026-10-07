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


def test_normalizer_preserves_instrument_specifications() -> None:
    event = MarketDataNormalizer().normalize(
        {
            "symbol": "EURUSD", "timestamp": "2026-01-01T00:00:00Z",
            "close": 1.10, "contract_size": 100000,
            "tick_size": 0.00001, "lot_step": 0.01,
            "asset_class": "forex",
        },
        source="test",
    )

    assert event.instrument.contract_size == 100000
    assert event.instrument.price_increment == 0.00001
    assert event.instrument.quantity_increment == 0.01


def test_normalizer_missing_timestamp_is_degraded_not_fabricated() -> None:
    event = MarketDataNormalizer().normalize(
        {"symbol": "EURUSD", "close": 1.10}, source="test"
    )

    assert event.quality is DataQuality.DEGRADED


def test_normalizer_flags_out_of_order_events() -> None:
    normalizer = MarketDataNormalizer()
    normalizer.normalize(
        {"symbol": "EURUSD", "timestamp": "2026-01-02T00:00:00Z",
         "close": 1.10}
    )
    late = normalizer.normalize(
        {"symbol": "EURUSD", "timestamp": "2026-01-01T00:00:00Z",
         "close": 1.09}
    )

    assert late.quality is DataQuality.STALE


def test_normalizer_rejects_crossed_quotes_and_contentless_ticks() -> None:
    normalizer = MarketDataNormalizer()
    crossed = normalizer.normalize(
        {"symbol": "EURUSD", "timestamp": "2026-01-01T00:00:00Z",
         "bid": 1.11, "ask": 1.10}
    )
    assert crossed.quality is DataQuality.INVALID

    empty = MarketDataNormalizer().normalize(
        {"symbol": "EURUSD", "timestamp": "2026-01-01T00:00:00Z"}
    )
    assert empty.quality is DataQuality.UNKNOWN
