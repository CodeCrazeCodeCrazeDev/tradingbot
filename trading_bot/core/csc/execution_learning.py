"""Execution-learning service: real venue-performance evidence.

Wraps the venue-tracking *kernel* from
``trading_bot/execution/smart_order_router.py`` (EMA venue scores +
per-venue performance windows) and feeds it **real** fill records
produced by the canonical execution path — not the router's simulated
fills (``execute_routed_order`` fabricates outcomes with np.random and
ships a hardcoded venue list including defunct venues; it must never be
an execution path).

Design:
- ``record_fill()`` — called by the canonical executor/reconciliation
  layer with measured outcomes (fill rate, realized spread, latency,
  fees). Non-finite values rejected.
- ``advisory_report()`` — emits venue rankings, reliability, and a
  shortfall summary as advisory evidence. Carries no routing or sizing
  authority: the canonical execution service remains the only order
  dispatcher.
- Bounded state: per-venue deques capped; venue count capped.

Venue universe comes from ``BrokerRegistry`` (real registered brokers)
when supplied; otherwise only venues that actually produce fills are
tracked — no phantom venues.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional

import numpy as np


def _finite(v: Any) -> bool:
    try:
        return bool(np.isfinite(float(v)))
    except (TypeError, ValueError):
        return False


class ExecutionLearningService:
    """Bounded per-venue execution-performance tracker (advisory only)."""

    MAX_VENUES = 32
    HISTORY = 100          # per-venue outcome window
    EMA_ALPHA = 0.1        # matches SmartOrderRouter's update rate

    def __init__(self, venues: Optional[List[str]] = None) -> None:
        self._venues: List[str] = [str(v) for v in (venues or [])]
        self._perf: Dict[str, Deque[float]] = {
            v: deque(maxlen=self.HISTORY) for v in self._venues}
        self._scores: Dict[str, float] = {v: 0.5 for v in self._venues}
        self._fills: int = 0
        self._shortfalls: Deque[float] = deque(maxlen=1024)

    # ---------------------------------------------------------------
    def _ensure_venue(self, venue: str) -> None:
        if venue in self._perf:
            return
        if len(self._perf) >= self.MAX_VENUES:
            # Evict the least-used venue (fewest recorded outcomes).
            oldest = min(self._perf, key=lambda v: len(self._perf[v]))
            del self._perf[oldest]
            self._scores.pop(oldest, None)
            self._venues.remove(oldest)
        self._perf[venue] = deque(maxlen=self.HISTORY)
        self._scores[venue] = 0.5
        self._venues.append(venue)

    # ---------------------------------------------------------------
    def record_fill(self, venue: str, *, fill_rate: float,
                    spread: float = 0.0, latency_ms: float = 0.0,
                    shortfall_bps: Optional[float] = None,
                    ts: Optional[float] = None) -> bool:
        """Record a *measured* execution outcome from the canonical path.

        ``fill_rate``: fraction of the intended quantity filled [0,1].
        ``spread``: realized half-spread paid (fraction of price).
        ``shortfall_bps``: implementation shortfall vs arrival price.
        Returns False when inputs are non-finite — nothing learned.
        """
        venue = str(venue or "unknown")
        if not _finite(fill_rate):
            return False
        fill_rate = float(np.clip(fill_rate, 0.0, 1.0))
        spread = float(np.clip(spread, 0.0, 1.0)) if _finite(spread) else 0.0
        self._ensure_venue(venue)
        # Same score kernel as SmartOrderRouter._update_venue_performance
        perf = fill_rate * (1.0 - spread)
        self._perf[venue].append(perf)
        self._scores[venue] = (
            (1 - self.EMA_ALPHA) * self._scores[venue]
            + self.EMA_ALPHA * float(np.mean(self._perf[venue])))
        if _finite(shortfall_bps):
            self._shortfalls.append(float(shortfall_bps))
        self._fills += 1
        return True

    # ---------------------------------------------------------------
    def advisory_report(self, symbol: Optional[str] = None
                        ) -> Dict[str, Any]:
        """Venue-performance evidence for the CSC. No authority fields —
        rankings inform, the canonical executor dispatches."""
        if self._fills == 0:
            return {"available": False,
                    "reason": "no measured execution outcomes yet",
                    "venues": [], "n_fills": 0}

        venues = []
        for v in self._venues:
            hist = list(self._perf[v])
            if not hist:
                continue
            venues.append({
                "venue": v,
                "score": float(self._scores[v]),
                "avg_performance": float(np.mean(hist)),
                "executions": len(hist),
                "recent_performance": float(np.mean(hist[-10:])),
            })
        venues.sort(key=lambda x: x["score"], reverse=True)

        sf = list(self._shortfalls)
        report = {
            "available": True,
            "n_fills": self._fills,
            "venues": venues,
            "top_venue": venues[0]["venue"] if venues else None,
            "mean_shortfall_bps": float(np.mean(sf)) if sf else None,
            "p95_shortfall_bps": float(np.percentile(sf, 95)) if sf else None,
            "advisory_only": True,
            "note": "venue evidence — canonical execution service owns "
                    "dispatch; these scores inform, never route",
            "generated_ts": time.time(),
        }
        if symbol:
            report["symbol"] = symbol
        return report


__all__ = ["ExecutionLearningService"]
