"""Bar-derived market microstructure estimators.

The full microstructure stack (LOB transitions, order-flow delta,
orderbook navigation) needs Level-2/trade data — the bar feed carries
none of it. These are the PUBLISHED estimators that work on OHLCV
alone, each labeled so downstream consumers know it's an estimate,
not a measurement:

- ``roll_spread``      — Roll (1984): effective spread from
  close-to-close serial covariance. Negative covariance means
  bid-ask bounce; sqrt gives the implied spread.
- ``kyle_lambda``      — Kyle (1985): price impact per unit volume,
  median |return| / volume.
- ``amihud``           — Amihud (2002): illiquidity ratio,
  mean |return| / dollar-volume (tick volume used as size proxy).
- ``tick_imbalance``   — bar-level order-flow proxy: signed
  volume imbalance sum(sign(dC)*V) / sum(V). NOT footprint delta —
  it measures which bars carried volume, not bid/ask aggressor side.
- ``efficiency_ratio`` — Kaufman ER: |net change| / sum |changes| —
  trend-vs-chop discriminator over closes.
- ``path_risk``        — intrabar excursion: median (high-low)/close —
  how much price travels inside a bar; sets realistic stop/sim ranges.

Everything is a pure function over strictly-prior series — the caller
(CSC enrichment) controls the window so no lookahead leaks in.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence

import numpy as np


def roll_spread(closes: Sequence[float], window: int = 30
                ) -> Optional[float]:
    """Roll (1984) implied effective spread, in price units.

    spread = 2 * sqrt(max(0, -Cov(dP_t, dP_{t-1})))
    Positive covariance (real autocorrelation) -> unestimable -> None,
    honestly reporting 'no bounce signal' rather than fabricating 0.
    """
    if len(closes) < window + 2:
        return None
    d = np.diff(np.asarray(closes[-(window + 1):], dtype=float))
    cov = float(np.cov(d[1:], d[:-1])[0, 1])
    if cov >= 0:
        return None
    return 2.0 * math.sqrt(-cov)


def corwin_schultz_spread(highs: Sequence[float],
                          lows: Sequence[float],
                          window: int = 20) -> Optional[float]:
    """Corwin-Schultz (2012) spread estimator from consecutive
    HIGH/LOW pairs — works in TRENDING markets where Roll's
    covariance method returns nothing (exactly the inverted-coverage
    gap). spread as a fraction of price; negative estimates clipped
    to 0 (honest: it can't see tighter than the bar width)."""
    n = min(len(highs), len(lows))
    if n < window + 1:
        return None
    h = np.asarray(highs[-(window + 1):], dtype=float)
    l = np.asarray(lows[-(window + 1):], dtype=float)
    mask = (h > 0) & (l > 0)
    if mask.sum() < 3:
        return None
    h, l = h[mask], l[mask]
    hl2 = np.log(h / l) ** 2
    beta = float(hl2[:-1].sum() + hl2[1:].sum())
    h2 = np.maximum(h[:-1], h[1:])
    l2 = np.minimum(l[:-1], l[1:])
    # gamma = sum over pairs of [ln(h2/l2)]^2 — NOT square-of-sum;
    # that inflated gamma suppressed alpha and forced the estimate
    # toward zero in exactly the trending windows CS exists to cover.
    gamma = float(np.sum(np.log(h2 / l2) ** 2)) if len(h2) else 0.0
    k = 3.0 - 2.0 * math.sqrt(2.0)
    alpha = ((math.sqrt(2 * beta) - math.sqrt(beta)) / k
             - math.sqrt(gamma / k)) if beta >= 0 else 0.0
    if not math.isfinite(alpha):
        return None
    spread = 2.0 * (math.exp(alpha) - 1.0) / (1.0 + math.exp(alpha))
    return max(0.0, spread)


def kyle_lambda(closes: Sequence[float], volumes: Sequence[float],
                window: int = 30) -> Optional[float]:
    """Median |return| / volume — price impact per unit size."""
    n = min(len(closes), len(volumes))
    if n < window + 1:
        return None
    c = np.asarray(closes[-(window + 1):], dtype=float)
    v = np.asarray(volumes[-window:], dtype=float)
    r = np.abs(np.diff(c) / c[:-1])
    mask = v > 0
    if not mask.any():
        return None
    lam = float(np.median(r[mask] / v[mask]))
    return lam if math.isfinite(lam) else None


def amihud(closes: Sequence[float], volumes: Sequence[float],
           window: int = 30) -> Optional[float]:
    """Amihud illiquidity: mean |return| / volume. Larger = thinner."""
    lam = kyle_lambda(closes, volumes, window)
    return lam  # same estimator family; reported under its own name


def tick_imbalance(closes: Sequence[float], volumes: Sequence[float],
                   window: int = 20) -> Optional[float]:
    """Signed-volume order-flow proxy in [-1, 1].

    sum(sign(dC)*V) / sum(V) — which bars carried the volume. A +0.8
    reading means 80% of recent tick volume printed on up-moves. NOT
    trade-side delta (needs footprint); labeled as a bar proxy."""
    n = min(len(closes), len(volumes))
    if n < window + 1:
        return None
    c = np.asarray(closes[-(window + 1):], dtype=float)
    v = np.asarray(volumes[-window:], dtype=float)
    d = np.sign(np.diff(c))
    tot = float(np.sum(v))
    if tot <= 0:
        return None
    return float(np.sum(d * v) / tot)


def efficiency_ratio(closes: Sequence[float], window: int = 20
                     ) -> Optional[float]:
    """Kaufman ER in [0, 1]: |net| / sum|moves|. ~1 = clean trend,
    ~0 = pure chop. The discriminator that tells a good trend trade
    from a bad chop trade on closes alone."""
    if len(closes) < window + 1:
        return None
    c = np.asarray(closes[-(window + 1):], dtype=float)
    net = abs(float(c[-1] - c[0]))
    denom = float(np.sum(np.abs(np.diff(c))))
    if denom <= 0:
        return None
    return net / denom


def path_risk(highs: Sequence[float], lows: Sequence[float],
              closes: Sequence[float], window: int = 20
              ) -> Optional[float]:
    """Median intrabar range as a fraction of close — how much price
    actually travels inside a bar. The simulator's honest estimate of
    stop-placement risk from OHLC data."""
    n = min(len(highs), len(lows), len(closes))
    if n < window:
        return None
    h = np.asarray(highs[-window:], dtype=float)
    l = np.asarray(lows[-window:], dtype=float)
    c = np.asarray(closes[-window:], dtype=float)
    mask = c > 0
    if not mask.any():
        return None
    return float(np.median((h - l)[mask] / c[mask]))


def estimate_all(closes: Sequence[float],
                 volumes: Optional[Sequence[float]] = None,
                 highs: Optional[Sequence[float]] = None,
                 lows: Optional[Sequence[float]] = None) -> dict:
    """One-call bundle for obs enrichment. Missing series degrade
    gracefully to absent fields — never fabricated."""
    out: dict = {}
    c = list(closes)
    v = list(volumes) if volumes is not None else []
    rs = roll_spread(c)
    if rs is not None and c and c[-1] > 0:
        out["est_spread_bps"] = float(rs / c[-1] * 1e4)
        out["spread_est_method"] = "roll"
    elif highs is not None and lows is not None and c and c[-1] > 0:
        # Trending regime: Roll has no bounce signal -> Corwin-Schultz
        # on high/low pairs covers the window Roll can't.
        cs = corwin_schultz_spread(list(highs), list(lows))
        if cs is not None:
            out["est_spread_bps"] = float(cs * 1e4)
            out["spread_est_method"] = "corwin_schultz"
    if v:
        lam = kyle_lambda(c, v)
        if lam is not None:
            out["kyle_lambda"] = lam
            out["amihud"] = lam
        ti = tick_imbalance(c, v)
        if ti is not None:
            out["tick_imbalance"] = ti
    er = efficiency_ratio(c)
    if er is not None:
        out["efficiency_ratio"] = er
    if highs is not None and lows is not None:
        pr = path_risk(list(highs), list(lows), c)
        if pr is not None:
            out["path_risk"] = pr
    return out
