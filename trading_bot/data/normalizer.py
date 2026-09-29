"""Normalize legacy observations into the foundation market-event contract."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from trading_bot.foundation.contracts import (
    DataQuality,
    Instrument,
    InstrumentType,
    MarketEvent,
    MarketEventType,
)


class MarketDataNormalizer:
    """Convert replay, paper, and venue payloads into canonical market events."""

    def normalize(
        self,
        observation: Mapping[str, Any],
        *,
        symbol: Optional[str] = None,
        venue: Optional[str] = None,
        source: str = "unknown",
        correlation_id: Optional[str] = None,
    ) -> MarketEvent:
        if not isinstance(observation, Mapping):
            raise TypeError("Market observations must be mappings")

        resolved_symbol = str(symbol or observation.get("symbol") or "").strip()
        if not resolved_symbol:
            raise ValueError("Market observations require a symbol")

        instrument = Instrument(
            symbol=resolved_symbol,
            instrument_type=self._instrument_type(observation),
            venue=str(venue or observation.get("venue") or "unknown"),
            currency=str(observation.get("currency") or "USD"),
            metadata={
                "asset_class": observation.get("asset_class"),
                "feed_id": observation.get("feed_id"),
            },
        )
        payload = dict(observation)
        payload.pop("symbol", None)
        payload.pop("timestamp", None)
        payload.pop("time", None)
        payload.pop("venue", None)

        quality = self._quality(payload)
        return MarketEvent(
            instrument=instrument,
            event_type=self._event_type(payload),
            source_timestamp=self._timestamp(observation.get("timestamp", observation.get("time"))),
            payload=payload,
            quality=quality,
            provenance={
                "source": source,
                "feed_id": observation.get("feed_id"),
                "normalizer": "MarketDataNormalizer",
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def _instrument_type(observation: Mapping[str, Any]) -> InstrumentType:
        raw = str(observation.get("instrument_type", observation.get("asset_class", "synthetic"))).lower()
        aliases = {
            "stock": InstrumentType.EQUITY,
            "stocks": InstrumentType.EQUITY,
            "equities": InstrumentType.EQUITY,
            "crypto": InstrumentType.CRYPTO_SPOT,
            "forex": InstrumentType.FX,
            "fx": InstrumentType.FX,
            "future": InstrumentType.FUTURE,
            "futures": InstrumentType.FUTURE,
            "option": InstrumentType.OPTION,
            "options": InstrumentType.OPTION,
            "etf": InstrumentType.ETF,
            "index": InstrumentType.INDEX,
        }
        return aliases.get(raw, InstrumentType(raw) if raw in InstrumentType._value2member_map_ else InstrumentType.SYNTHETIC)

    @staticmethod
    def _event_type(payload: Mapping[str, Any]) -> MarketEventType:
        if {"open", "high", "low", "close"}.issubset(payload):
            return MarketEventType.BAR
        if "bid" in payload or "ask" in payload:
            return MarketEventType.QUOTE
        if "last" in payload or "price" in payload or "close" in payload:
            return MarketEventType.TRADE
        return MarketEventType.TICK

    @staticmethod
    def _timestamp(value: Any) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _quality(payload: Mapping[str, Any]) -> DataQuality:
        numeric_keys = {"price", "open", "high", "low", "close", "volume", "bid", "ask", "last"}
        values = [payload[key] for key in numeric_keys if key in payload]
        try:
            if any(not math.isfinite(float(value)) for value in values):
                return DataQuality.INVALID
        except (TypeError, ValueError):
            return DataQuality.INVALID

        if all(key in payload for key in ("open", "high", "low", "close")):
            try:
                open_, high, low, close = (float(payload[key]) for key in ("open", "high", "low", "close"))
            except (TypeError, ValueError):
                return DataQuality.INVALID
            if min(open_, high, low, close) <= 0 or high < max(open_, close) or low > min(open_, close) or high < low:
                return DataQuality.INVALID
        elif "price" in payload:
            try:
                if float(payload["price"]) <= 0:
                    return DataQuality.INVALID
            except (TypeError, ValueError):
                return DataQuality.INVALID
        return DataQuality.VALID


def normalize_observation(
    observation: Mapping[str, Any],
    *,
    source: str = "unknown",
    correlation_id: Optional[str] = None,
) -> MarketEvent:
    """Convenience adapter for legacy dictionary-based callers."""
    return MarketDataNormalizer().normalize(
        observation,
        source=source,
        correlation_id=correlation_id,
    )
