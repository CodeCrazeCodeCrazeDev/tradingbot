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
    # Canonical CS: one alpha per CONSECUTIVE PAIR, then average the
    # spreads — summing betas/gammas over the whole window inflates
    # the estimate ~sqrt(N)x.
    betas = hl2[:-1] + hl2[1:]
    h2 = np.maximum(h[:-1], h[1:])
    l2 = np.minimum(l[:-1], l[1:])
    gammas = np.log(h2 / l2) ** 2
    k = 3.0 - 2.0 * math.sqrt(2.0)
    alphas = (np.sqrt(2.0 * betas) - np.sqrt(betas)) / k \
        - np.sqrt(gammas / k)
    alphas = alphas[np.isfinite(alphas)]
    if not len(alphas):
        return None
    spreads = 2.0 * (np.exp(alphas) - 1.0) / (1.0 + np.exp(alphas))
    return max(0.0, float(np.mean(spreads)))


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
    """Amihud (2002) illiquidity: mean |return| / dollar-volume.
    Tick volume x price approximates traded value on FX feeds."""
    n = min(len(closes), len(volumes))
    if n < window + 1:
        return None
    c = np.asarray(closes[-(window + 1):], dtype=float)
    v = np.asarray(volumes[-window:], dtype=float)
    r = np.abs(np.diff(c) / c[:-1])
    dv = v * c[1:]
    mask = dv > 0
    if not mask.any():
        return None
    out = float(np.mean(r[mask] / dv[mask]))
    return out if math.isfinite(out) else None


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
        if cs is not None and cs > 1e-8:
            out["est_spread_bps"] = float(cs * 1e4)
            out["spread_est_method"] = "corwin_schultz"
        elif cs is not None:
            # CS clipped to zero = 'below estimator resolution', NOT
            # 'free to trade' — a 0.0 cost estimate would let every
            # EV sail through the net-cost gate.
            out["spread_est_method"] = "cs_below_resolution"
    if v:
        lam = kyle_lambda(c, v)
        if lam is not None:
            out["kyle_lambda"] = lam
        am = amihud(c, v)
        if am is not None:
            out["amihud"] = am
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
