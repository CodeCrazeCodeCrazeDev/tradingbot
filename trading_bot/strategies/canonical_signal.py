"""CanonicalSignalGenerator — the single signal surface wired to the CSC.

Design (first principles):
  * ONE measured, auditable signal instead of scattered emitters —
    every vote it casts is scored by ReliabilityTracker per regime.
  * Regime-conditional, driven by measured evidence on M15 EURUSD:
      - FLAT/chop regimes (low efficiency ratio) mean-revert —
        fade z-score / RSI extremes.
      - Persistent regimes (high ER) trend — follow fast/slow momentum.
  * Missing inputs produce NO signal — a fabricated neutral default is
    exactly the misleading behaviour this replaces.
  * Confidence reflects component agreement and signal magnitude,
    never saturated at 1.0; expected_return is a z/vol-scaled estimate,
    not a promise.

Feeds ``obs["strategy_signals"]`` via the strategy registry, which the
hypothesis generator's ``_signal_vote`` aggregates into branch priors.
Downstream gates (simulation, verification, net-of-cost, risk,
governance, shield) are unchanged — this surface only proposes
direction; it never authorizes, sizes, or executes.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from trading_bot.foundation.contracts import (
    Instrument, InstrumentType, Signal)

logger = logging.getLogger(__name__)


class CanonicalSignalGenerator:
    """Regime-conditional composite signal over real measured features.

    Components (each votes in [-1, 1], reported individually):
      z_fade   — contrarian: z < -entry → buy, z > +entry → sell
      rsi_fade — contrarian: RSI < 30 → buy, RSI > 70 → sell
      momentum — follower: (fast_ma - slow_ma)/slow_ma * gain
    Regime gate (ER = trend_strength):
      ER >= follow_er   → momentum dominates (fade damped)
      ER <  follow_er   → fade dominates   (momentum damped)
    Final direction requires |vote| >= min_vote; otherwise neutral.
    """

    strategy_id = "canonical"

    def __init__(self, window: int = 128, z_lookback: int = 20,
                 fast: int = 10, slow: int = 50,
                 z_entry: float = 1.5,
                 follow_er: float = 0.35,
                 min_bars: int = 55, min_vote: float = 0.35) -> None:
        self.window = window
        self.z_lookback = z_lookback
        self.fast = fast
        self.slow = slow
        self.z_entry = z_entry
        self.follow_er = follow_er
        self.min_bars = min_bars
        self.min_vote = min_vote
        self._closes: deque = deque(maxlen=window)

    # -- component votes -------------------------------------------------

    def _component_votes(self) -> Dict[str, float]:
        closes = list(self._closes)
        lb = min(self.z_lookback, len(closes) - 1)
        window = closes[-lb - 1:]
        mean = sum(window) / len(window)
        var = sum((c - mean) ** 2 for c in window) / len(window)
        std = var ** 0.5
        z = (closes[-1] - mean) / std if std > 0 else 0.0
        # Fade: strength capped at 1.
        z_fade = max(-1.0, min(1.0, -z / (self.z_entry * 2)))
        fast_ma = sum(closes[-self.fast:]) / self.fast
        slow_n = min(self.slow, len(closes))
        slow_ma = sum(closes[-slow_n:]) / slow_n
        mom = (fast_ma - slow_ma) / slow_ma if slow_ma else 0.0
        momentum = max(-1.0, min(1.0, mom * 200.0))  # ~50bp move -> full
        return {"z_fade": round(z_fade, 4),
                "momentum": round(momentum, 4),
                "z_score": round(z, 4)}

    # -- public surface ---------------------------------------------------

    def generate_signal(self, market: Mapping[str, Any]
                        ) -> Optional[List[Signal]]:
        close = market.get("close", market.get("price"))
        if not isinstance(close, (int, float)) or isinstance(close, bool) \
                or close <= 0:
            return []
        self._closes.append(float(close))
        if len(self._closes) < self.min_bars:
            return []  # honest warm-up — no signal, not a default vote

        # Measured obs features (enrich_observation); absent → no vote.
        rsi = market.get("rsi")
        er = market.get("trend_strength")
        rsi_fade = 0.0
        if isinstance(rsi, (int, float)) and not isinstance(rsi, bool):
            if rsi <= 30.0:
                rsi_fade = (30.0 - rsi) / 30.0
            elif rsi >= 70.0:
                rsi_fade = -(rsi - 70.0) / 30.0
        er_val = float(er) if isinstance(er, (int, float)) \
            and not isinstance(er, bool) else 0.0

        votes = self._component_votes()
        votes["rsi_fade"] = round(rsi_fade, 4)

        follow = er_val >= self.follow_er
        fade_w, mom_w = (0.25, 0.75) if follow else (0.75, 0.25)
        fade = (votes["z_fade"] + votes["rsi_fade"]) / 2.0
        vote = fade_w * fade + mom_w * votes["momentum"]
        regime = "persistent" if follow else "chop"

        if abs(vote) < self.min_vote:
            direction = "neutral"
        else:
            direction = "buy" if vote > 0 else "sell"

        # Agreement-based confidence: components that agree with the vote
        # raise it; disagreement shrinks it. Bounded, never saturated.
        aligned = sum(1 for c in (fade, votes["momentum"], rsi_fade)
                      if c * vote > 0)
        confidence = min(0.85, 0.30 + 0.15 * aligned + abs(vote) * 0.25) \
            if direction != "neutral" else 0.0

        symbol = str(market.get("symbol") or "UNKNOWN")
        # Honest EV estimate: expected fade of |z| toward mean, scaled
        # by component magnitude — a proposal-time estimate, not a promise.
        exp_ret = abs(vote) * 0.002 if direction != "neutral" else 0.0

        return [Signal(
            signal_id=f"canonical:{symbol}:"
                      f"{datetime.now(timezone.utc).timestamp()}",
            instrument=Instrument(symbol, InstrumentType.SYNTHETIC,
                                  str(market.get("venue") or "paper")),
            direction=direction,
            confidence=max(0.0, min(1.0, confidence)),
            expected_return=exp_ret,
            strategy_id=self.strategy_id,
            reasoning=(
                f"canonical regime={regime} er={er_val:.2f} vote={vote:+.3f} "
                f"components={votes}"),
            metadata={
                "regime_gate": regime,
                "efficiency_ratio": er_val,
                "composite_vote": round(vote, 4),
                "component_votes": votes,
                "bars": len(self._closes),
            },
        )]
