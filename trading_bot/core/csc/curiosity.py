"""Curiosity engine — hypothesis generation from measured surprise.

The doc-specified `foundation_agents/curiosity_engine` never existed;
this is the canonical implementation on the CSC path. Every emitted
hypothesis traces to a measured trigger — return z-score anomalies,
level breaks, or volume-price coupling shifts over the observed window.
No hypothesis is generated without a measured cause.

Output is a payload for ``SRE.ingest_external`` — the SRE owns the
hypothesis lifecycle; the curiosity engine only proposes.
"""
from __future__ import annotations

import logging
from collections import deque
from typing import Any, Deque, Dict, List, Mapping, Optional

import numpy as np

logger = logging.getLogger(__name__)

_ANOMALY_Z = 2.5          # return z-score trigger
_CORR_SHIFT = 0.4         # |corr(recent) - corr(prior)| trigger
_REEMIT_GAP = 50          # min observations between same-named emits
_MIN_HISTORY = 20         # warm-up before any mechanism can fire


class CuriosityEngine:
    """Measured-surprise hypothesis generator.

    Maintains rolling close/return/volume windows; emits at most a few
    hypothesis payloads per observation, each carrying the measured
    statistic that produced it.
    """

    _MAX_SYMBOLS = 32

    def __init__(self) -> None:
        # Per-symbol state — a global window would concatenate different
        # instruments into one nonsense series (same conflation bug as
        # the advisor _BarHistory). Bounded symbol count evicts the
        # oldest-inserted entry.
        self._state: Dict[str, Dict[str, Any]] = {}
        self._cur: Optional[Dict[str, Any]] = None
        self.emitted_total = 0

    def _st(self, symbol: str) -> Dict[str, Any]:
        st = self._state.get(symbol)
        if st is None:
            if len(self._state) >= self._MAX_SYMBOLS:
                self._state.pop(next(iter(self._state)))
            st = self._state[symbol] = {
                "closes": deque(maxlen=240),
                "volumes": deque(maxlen=240),
                "emitted": {}, "seq": 0}
        return st

    def observe(self, obs: Mapping[str, Any]) -> List[Dict[str, Any]]:
        symbol = str(obs.get("symbol") or "UNKNOWN")
        st = self._st(symbol)
        self._cur = st
        st["seq"] += 1
        close = obs.get("close") or obs.get("price")
        vol = obs.get("volume_ratio") or obs.get("volume")
        if isinstance(close, (int, float)) and np.isfinite(close) \
                and close > 0:
            st["closes"].append(float(close))
        if isinstance(vol, (int, float)) and np.isfinite(vol):
            st["volumes"].append(float(vol))
        if len(st["closes"]) < _MIN_HISTORY:
            return []

        out: List[Dict[str, Any]] = []
        for cand in (self._anomaly(), self._level_break(),
                     self._corr_shift()):
            if cand and self._fresh(cand["name"]):
                st["emitted"][cand["name"]] = st["seq"]
                self.emitted_total += 1
                out.append(cand)
        return out

    # -- mechanisms ------------------------------------------------------

    def _returns(self) -> np.ndarray:
        c = np.asarray(self._cur["closes"], dtype=float)
        return np.diff(c) / np.where(c[:-1] == 0, 1.0, c[:-1])

    def _anomaly(self) -> Optional[Dict[str, Any]]:
        """Return z-score spike vs the observed window."""
        rets = self._returns()
        if len(rets) < _MIN_HISTORY - 1:
            return None
        hist, last = rets[:-1], rets[-1]
        mu, sd = float(np.nanmean(hist)), float(np.nanstd(hist))
        if sd <= 0:
            # Degenerate window: a nonzero return against a perfectly
            # flat history is the strongest possible anomaly.
            z = 100.0 if abs(last - mu) > 1e-12 else 0.0
        else:
            z = abs(last - mu) / sd
        if z <= _ANOMALY_Z:
            return None
        return {
            "name": "return_shock",
            "description": (f"Return z-score {z:.2f} exceeds "
                            f"{_ANOMALY_Z} — regime shock hypothesis"),
            "confidence": float(min(0.9, 0.4 + z / 10.0)),
            "measured_zscore": round(z, 4),
            "falsification": "z-score decays below 1.0 within 20 obs",
        }

    def _level_break(self) -> Optional[Dict[str, Any]]:
        """Close clears the rolling window's range."""
        c = list(self._cur["closes"])
        prior = c[:-1]
        if max(prior) > c[-1] > min(prior):
            return None
        span = (max(prior) - min(prior)) / max(min(prior), 1e-12)
        if span <= 0:
            return None
        return {
            "name": "level_break",
            "description": ("Close exited the observed window's range "
                            f"(span {span:.4%}) — level break"),
            "confidence": 0.55,
            "measured_span": round(span, 6),
            "falsification": "price re-enters prior range within 10 obs",
        }

    def _corr_shift(self) -> Optional[Dict[str, Any]]:
        """Rolling price/volume coupling changed regime."""
        n = min(len(self._cur["closes"]), len(self._cur["volumes"]))
        if n < _MIN_HISTORY:
            return None
        c = np.asarray(self._cur["closes"])[-n:]
        v = np.asarray(self._cur["volumes"])[-n:]
        rets = np.diff(c) / np.where(c[:-1] == 0, 1.0, c[:-1])
        vol = v[1:]
        half = len(rets) // 2
        if half < 8:
            return None
        try:
            r_prior = float(np.corrcoef(rets[:half], vol[:half])[0, 1])
            r_recent = float(np.corrcoef(rets[half:], vol[half:])[0, 1])
        except Exception:  # noqa: BLE001
            return None
        if not (np.isfinite(r_prior) and np.isfinite(r_recent)):
            return None
        shift = abs(r_recent - r_prior)
        if shift <= _CORR_SHIFT:
            return None
        return {
            "name": "volume_price_decoupling",
            "description": (f"price/volume correlation shifted "
                            f"{r_prior:.2f} -> {r_recent:.2f} — coupling "
                            f"regime change"),
            "confidence": float(min(0.85, 0.4 + shift / 2.0)),
            "measured_corr_shift": round(shift, 4),
            "falsification": "coupling reverts within 30 obs",
        }

    def _fresh(self, name: str) -> bool:
        return self._cur["seq"] - self._cur["emitted"].get(name, -10**9) > _REEMIT_GAP
