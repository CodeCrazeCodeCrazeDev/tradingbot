"""Typed strategy adapters for legacy signal engines."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import Any, List, Mapping, Optional

from trading_bot.foundation.contracts import Instrument, InstrumentType, Signal
from trading_bot.foundation.ports import StrategyPort


class LegacyStrategyAdapter:
    """Adapt a legacy ``analyse``/``generate_signal`` engine to signal contracts."""

    def __init__(self, strategy_id: str, legacy_engine: Any, venue: str = "paper") -> None:
        if legacy_engine is None:
            raise ValueError("legacy_engine is required")
        self.strategy_id = strategy_id
        self.legacy_engine = legacy_engine
        self.venue = venue

    async def generate_signal(self, market: Mapping[str, Any]) -> Optional[List[Signal]]:
        method = getattr(self.legacy_engine, "generate_signal", None)
        if method is None:
            method = getattr(self.legacy_engine, "analyse", None)
        if method is None:
            raise ValueError(f"Legacy strategy '{self.strategy_id}' has no signal method")
        payload = market.get("bars", market)
        result = method(payload)
        if inspect.isawaitable(result):
            result = await result
        if result is None:
            return []
        if not isinstance(result, (list, tuple)):
            result = [result]
        return [self._convert(item, market) for item in result]

    def _convert(self, legacy_signal: Any, market: Mapping[str, Any]) -> Signal:
        symbol = str(
            getattr(legacy_signal, "symbol", None)
            or market.get("symbol")
            or "UNKNOWN"
        )
        raw_confidence = float(getattr(legacy_signal, "confidence", 0.0) or 0.0)
        confidence = raw_confidence / 100.0 if raw_confidence > 1.0 else raw_confidence
        direction = str(getattr(legacy_signal, "direction", "neutral")).lower()
        reasoning = str(getattr(legacy_signal, "rationale", "legacy strategy signal"))
        created = getattr(legacy_signal, "time", None) or datetime.now(timezone.utc)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return Signal(
            signal_id=f"{self.strategy_id}:{symbol}:{created.timestamp()}",
            instrument=Instrument(symbol, InstrumentType.SYNTHETIC, self.venue),
            direction=direction,
            confidence=max(0.0, min(1.0, confidence)),
            strategy_id=self.strategy_id,
            reasoning=reasoning,
            created_at=created,
            metadata={
                "legacy_type": type(legacy_signal).__name__,
                "stop_loss_pips": getattr(legacy_signal, "stop_loss_pips", None),
                "take_profit_rr": getattr(legacy_signal, "take_profit_rr", None),
            },
        )
