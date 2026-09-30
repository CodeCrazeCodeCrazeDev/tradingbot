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


# Worse-than ordering: a declared quality only overrides the computed one when
# it is strictly worse. "unknown" sits above "valid" — a source that admits it
# cannot vouch for its own data is not trusted as fresh.
_QUALITY_SEVERITY = {
    DataQuality.VALID: 0,
    DataQuality.UNKNOWN: 1,
    DataQuality.DEGRADED: 2,
    DataQuality.STALE: 3,
    DataQuality.INVALID: 4,
}


class MarketDataNormalizer:
    """Convert replay, paper, and venue payloads into canonical market events."""

    def __init__(self, max_staleness_seconds: Optional[float] = None) -> None:
        # Optional freshness horizon. Wall-clock staleness is opt-in because
        # historical replay legitimately feeds old timestamps; live adapters
        # that can compute staleness should declare it (data_quality/stale)
        # or construct the normalizer with an explicit bound.
        self.max_staleness_seconds = max_staleness_seconds

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

        source_timestamp = self._timestamp(
            observation.get("timestamp", observation.get("time"))
        )
        quality = self._quality(payload)
        declared = self._declared_quality(observation)
        # Untrusted upstream labels can only ever worsen quality — a feed
        # declaring "valid" never launders malformed data, while declared
        # stale/invalid markers must fail closed downstream.
        if declared is not None and _QUALITY_SEVERITY[declared] > _QUALITY_SEVERITY[quality]:
            quality = declared
        if (
            self.max_staleness_seconds is not None
            and quality
            in (DataQuality.VALID, DataQuality.DEGRADED, DataQuality.UNKNOWN)
            and (datetime.now(timezone.utc) - source_timestamp).total_seconds()
            > self.max_staleness_seconds
        ):
            quality = DataQuality.STALE
        return MarketEvent(
            instrument=instrument,
            event_type=self._event_type(payload),
            source_timestamp=source_timestamp,
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
    def _declared_quality(observation: Mapping[str, Any]) -> Optional[DataQuality]:
        """Extract a quality the untrusted source declared about itself."""
        if observation.get("stale") is True or observation.get("is_stale") is True:
            return DataQuality.STALE
        if observation.get("data_is_fresh") is False:
            return DataQuality.STALE
        raw = observation.get("data_quality", observation.get("quality"))
        if raw is None:
            return None
        text = str(raw).strip().lower()
        return {
            "invalid": DataQuality.INVALID,
            "stale": DataQuality.STALE,
            "degraded": DataQuality.DEGRADED,
            "valid": DataQuality.VALID,
            "unknown": DataQuality.UNKNOWN,
        }.get(text)

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
