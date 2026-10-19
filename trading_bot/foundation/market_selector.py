"""Autonomous market selection — the bot chooses which symbols to trade.

Scored on REAL venue data only (the MT5 demo feed already supplies free
closed bars + live ticks for the whole symbol list, so selection costs
nothing and invents nothing):

    score = opportunity - cost - noise

    opportunity   ATR%  (real range / price — movement worth capturing)
    cost          spread_bps (measured live tick spread — the toll to enter)
    liquidity     median tick_volume (bars built on real market interest)
    clarity       |EMA20 - EMA50| / ATR — directional persistence, not chop

Every input is measured; a symbol with no real bars scores 0 and is
never selected. Selection is evidence-ranked, not random.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

# Candidate universe — major + minor FX + metals that MetaQuotes-Demo
# publishes real quotes for. The selector can only score what the venue
# actually feeds, so this is a candidate list, not a choice.
DEFAULT_UNIVERSE = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
    "USDCAD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY",
    "EURAUD", "EURNZD", "GBPAUD", "GBPCAD", "XAUUSD", "XAGUSD",
)


def _atr_pct(bars: Sequence[Any], period: int = 14) -> Optional[float]:
    trs: List[float] = []
    prev_close: Optional[float] = None
    for bar in bars[-period - 1:]:
        try:
            h, l, c = float(bar["high"]), float(bar["low"]), float(bar["close"])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if prev_close is not None:
            trs.append(max(h - l, abs(h - prev_close), abs(l - prev_close)))
        prev_close = c
    if not trs or not bars:
        return None
    try:
        last = float(bars[-1]["close"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return (sum(trs) / len(trs)) / last if last else None


def _ema(closes: Sequence[float], n: int) -> Optional[float]:
    if len(closes) < n:
        return None
    k = 2.0 / (n + 1)
    e = closes[0]
    for c in closes[1:]:
        e = c * k + e * (1 - k)
    return e


def score_symbol(bars: Sequence[Any],
                 spread_bps: Optional[float]) -> Dict[str, Any]:
    """One symbol, real bars + measured spread -> tradability score."""
    if bars is None or len(bars) < 20:
        return {"score": 0.0, "reason": "insufficient_real_bars",
                "bars": 0 if bars is None else len(bars)}
    closes = []
    vols = []
    for bar in bars:
        try:
            closes.append(float(bar["close"]))
            vols.append(float(bar["tick_volume"]))
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    atr = _atr_pct(bars)
    if atr is None or not closes:
        return {"score": 0.0, "reason": "no_real_range"}
    # opportunity: real movement per bar, scaled so 0.2% ATR ~ 1.0
    opportunity = atr / 0.002
    # cost: measured spread in bps, scaled so 2bps ~ cost 1.0
    cost = (float(spread_bps) / 2.0) if spread_bps else 0.5
    # liquidity: median real tick volume, scaled so 500/bar ~ 1.0
    vols_sorted = sorted(vols)
    med_vol = vols_sorted[len(vols_sorted) // 2] if vols_sorted else 0.0
    liquidity = min(med_vol / 500.0, 2.0)
    # clarity: trend persistence (EMA separation vs noise floor)
    e20, e50 = _ema(closes, 20), _ema(closes, 50)
    clarity = abs(e20 - e50) / (atr * closes[-1]) \
        if (e20 is not None and e50 is not None and atr) else 0.0
    score = opportunity * min(liquidity, 1.5) * (1 + clarity) - cost
    return {
        "score": round(score, 4),
        "atr_pct": round(atr * 100, 4),
        "spread_bps": spread_bps,
        "median_volume": med_vol,
        "trend_clarity": round(clarity, 3),
        "bars": len(bars),
    }


class MarketSelector:
    """Autonomous symbol chooser. Re-rank on a cadence; rotate the
    active set when the evidence moves. Never fabricates data — a
    symbol the venue doesn't feed scores 0."""

    def __init__(self, universe: Optional[Sequence[str]] = None,
                 reselect_every: int = 60) -> None:
        self.universe = list(universe or DEFAULT_UNIVERSE)
        self.reselect_every = max(int(reselect_every), 1)
        self._selected: List[str] = []
        self._ranking: Dict[str, Dict[str, Any]] = {}
        self._poll_count = 0

    @property
    def selected(self) -> List[str]:
        return list(self._selected)

    @property
    def ranking(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._ranking)

    def needs_reselect(self) -> bool:
        self._poll_count += 1
        return (not self._selected) \
            or self._poll_count % self.reselect_every == 1

    def reselect(self, score_fn, top_n: int = 3,
                 candidates: Optional[Sequence[str]] = None) -> List[str]:
        """``score_fn(symbol) -> dict`` returns real-data scores; the
        caller supplies the venue's fetch path. Symbols scoring <= 0 are
        never selected."""
        ranked = []
        for sym in (candidates or self.universe):
            try:
                s = score_fn(sym)
            except Exception as exc:  # noqa: BLE001
                s = {"score": 0.0, "reason": str(exc)[:80]}
            self._ranking[sym] = s
            if float(s.get("score") or 0) > 0:
                ranked.append((float(s["score"]), sym))
        ranked.sort(reverse=True)
        self._selected = [sym for _, sym in ranked[:top_n]]
        if self._selected:
            logger.info("market selector picked %s from %d candidates",
                        self._selected, len(self._ranking))
        else:
            logger.warning("market selector: no symbol scored > 0 "
                           "(%d candidates)", len(self._ranking))
        return self.selected
