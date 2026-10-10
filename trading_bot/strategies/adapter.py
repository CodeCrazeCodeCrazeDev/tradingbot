"""Typed strategy adapters for legacy signal engines."""

from __future__ import annotations

import inspect
from collections import deque
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
        # Institutional strategies return plain dicts — read mapping keys
        # first so direction/confidence aren't silently defaulted to
        # neutral/0.
        if isinstance(legacy_signal, Mapping):
            get_field = lambda k, d=None: legacy_signal.get(k, d)
        else:
            get_field = lambda k, d=None: getattr(legacy_signal, k, d)
        symbol = str(
            get_field("symbol") or market.get("symbol") or "UNKNOWN"
        )
        raw_confidence = float(get_field("confidence", 0.0) or 0.0)
        confidence = raw_confidence / 100.0 if raw_confidence > 1.0 else raw_confidence
        direction = str(
            get_field("direction") or get_field("action") or "neutral"
        ).lower()
        reasoning = str(
            get_field("rationale") or get_field("reason")
            or "legacy strategy signal")
        created = get_field("time") or datetime.now(timezone.utc)
        if getattr(created, "tzinfo", None) is None:
            created = created.replace(tzinfo=timezone.utc) \
                if hasattr(created, "replace") else created
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
                "stop_loss_pips": get_field("stop_loss_pips"),
                "take_profit_rr": get_field("take_profit_rr"),
            },
        )


class RollingWindowStrategyAdapter:
    """Feed a DataFrame-based strategy a rolling window of real closes.

    The institutional strategies take ``df['close']``; the observation is
    one bar. This adapter accumulates observed closes itself and emits
    **nothing** while warming — an empty list is an honest "insufficient
    history", not a fabricated neutral vote. Actions map to Signal
    directions; ``hold``/``close`` map to ``neutral`` so the vote counter
    sees a real observation-counted call, not silence.
    """

    _ACTION_TO_DIRECTION = {
        "buy": "buy", "long_spread": "buy", "buy_vol": "buy", "bullish": "buy",
        "sell": "sell", "short_spread": "sell", "sell_vol": "sell",
        "bearish": "sell",
        "hold": "neutral", "close": "neutral", "neutral": "neutral",
    }

    def __init__(self, strategy_id: str, engine: Any,
                 window: int = 128, min_bars: int = 0) -> None:
        if not callable(getattr(engine, "generate_signal", None)):
            raise ValueError("engine requires generate_signal(df)")
        self.strategy_id = strategy_id
        self.engine = engine
        self._closes: deque = deque(maxlen=window)
        # Warm-up requirement comes from the strategy's own lookback, with
        # a small buffer so the last z-score isn't computed on a boundary.
        self._min_bars = min_bars or int(
            getattr(engine, "lookback",
                    getattr(engine, "slow_period", 20)) + 5)

    async def generate_signal(self, market: Mapping[str, Any]
                              ) -> Optional[List[Signal]]:
        close = market.get("close", market.get("price"))
        if isinstance(close, (int, float)) and not isinstance(close, bool) \
                and close > 0:
            self._closes.append(float(close))
        if len(self._closes) < self._min_bars:
            return []
        import pandas as pd
        df = pd.DataFrame({"close": list(self._closes)})
        try:
            out = self.engine.generate_signal(df)
        except Exception:
            return []  # strategy failure is missing evidence, not a vote
        if inspect.isawaitable(out):
            out = await out
        if not isinstance(out, Mapping):
            return []
        action = str(out.get("action") or "hold").lower()
        direction = self._ACTION_TO_DIRECTION.get(action, "neutral")
        raw_conf = float(out.get("confidence") or 0.0)
        confidence = raw_conf / 100.0 if raw_conf > 1.0 else raw_conf
        symbol = str(market.get("symbol") or "UNKNOWN")
        extras = {k: v for k, v in out.items()
                  if k not in ("action", "confidence")}
        return [Signal(
            signal_id=f"{self.strategy_id}:{symbol}:"
                      f"{datetime.now(timezone.utc).timestamp()}",
            instrument=Instrument(symbol, InstrumentType.SYNTHETIC,
                                  str(market.get("venue") or "paper")),
            direction=direction,
            confidence=max(0.0, min(1.0, confidence)),
            strategy_id=self.strategy_id,
            reasoning=f"{self.strategy_id} action={action} {extras}",
            metadata={"raw_action": action, **extras},
        )]


def build_builtin_strategy(strategy_id: str) -> Any:
    """Factory for the RSI allow-listed strategy families.

    ``canonical`` is the single composite signal surface — it consumes the
    observation dict directly (needs measured rsi/trend_strength plus its
    own close window), so it returns a ready StrategyPort, not a
    RollingWindow adapter.

    ``stat_arb`` is deliberately absent — it prices a pair spread and the
    single-symbol observation cannot supply a second leg; registering it
    anyway would fabricate a signal from missing data.
    """
    if strategy_id == "canonical":
        from trading_bot.strategies.canonical_signal import (
            CanonicalSignalGenerator)
        return CanonicalSignalGenerator()

    from trading_bot.strategies.institutional_strategies import (
        MeanReversionStrategy, MomentumStrategy)

    engines = {
        "mean_reversion": MeanReversionStrategy,
        "momentum": MomentumStrategy,
    }
    engine_cls = engines.get(strategy_id)
    if engine_cls is None:
        raise ValueError(
            f"unknown or unfeedable builtin strategy '{strategy_id}'; "
            f"available: {sorted(engines) + ['canonical']}")
    return RollingWindowStrategyAdapter(strategy_id, engine_cls())
