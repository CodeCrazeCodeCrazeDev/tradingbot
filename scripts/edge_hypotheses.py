#!/usr/bin/env python
"""Hypothesis registry: external claims become gatable rule_fns.

The papers/external-knowledge mechanism: any research claim is written
as a `fn(closes, i) -> -1/0/+1` here with its provenance + declared
cost assumptions recorded, then edge_gate falsifies it on OUR
venues/windows/costs. Survives → live-exploratory candidate pool.
Dies → recorded rejection. Papers inform proposals, never weights.

Add a hypothesis = one function + one entry in HYPOTHESES. Declared
BEFORE evaluation; no tuning on eval windows.
"""

from __future__ import annotations

import numpy as np


def hyp_time_of_day_momentum(closes, i):
    """'Momentum works when liquidity is deepest' — proxy: follow the
    5-bar direction only when the 20-bar tick-volume is above its
    median (needs volume; returns 0 where volume is absent/zero).
    Source class: session-liquidity literature."""
    return 0  # placeholder — needs volume arg; kept as schema example


def hyp_weekend_effect(closes, i):
    """Weekend gap-fade — needs timestamps; placeholder documenting
    that calendar hypotheses need a timestamp channel in evaluate()."""
    return 0


def hyp_vol_scaled_momentum(closes, i):
    """Position-scaled momentum: follow 10-bar direction only when
    normalized move (|ret|/sigma20) is in [0.5, 2.5] — beyond that is
    either noise or blowoff. 'Middle-strength trends persist.'"""
    if i < 30:
        return 0
    ret = (closes[i] - closes[i - 10]) / closes[i - 10]
    s = np.std(np.diff(np.log(closes[i - 19:i + 1])))
    if s <= 0:
        return 0
    z = ret / (s * np.sqrt(10))
    if 0.5 < abs(z) < 2.5:
        return 1 if ret > 0 else -1
    return 0


def hyp_range_fade_3bar(closes, i):
    """3-sigma 20-bar breakout fades faster in ranging regimes: if the
    100-bar net |move| is < 1.5x its |return| path dispersion (range),
    fade any 3-bar move > 1.5 sigma."""
    if i < 120:
        return 0
    path = np.abs(np.diff(closes[i - 99:i + 1])).sum()
    net = abs(closes[i] - closes[i - 100])
    if path <= 0 or net / path > 0.15:
        return 0  # trending — don't fade
    r3 = (closes[i] - closes[i - 3]) / closes[i - 3]
    s = np.std(np.diff(np.log(closes[i - 19:i + 1])))
    if s <= 0 or abs(r3) < 1.5 * s * np.sqrt(3):
        return 0
    return -1 if r3 > 0 else 1


def hyp_gap_cont(closes, i):
    """Large-gap continuation: a single bar move > 2.5 sigma tends to
    continue for a bar or two in crypto (momentum crash lite)."""
    if i < 25:
        return 0
    s = np.std(np.diff(np.log(closes[i - 19:i + 1])))
    if s <= 0:
        return 0
    r1 = (closes[i] - closes[i - 1]) / closes[i - 1]
    z = r1 / s
    if abs(z) < 2.5:
        return 0
    return 1 if z > 0 else -1


HYPOTHESES = {
    "vol_scaled_momentum": hyp_vol_scaled_momentum,
    "range_fade_3bar": hyp_range_fade_3bar,
    "gap_cont": hyp_gap_cont,
}
