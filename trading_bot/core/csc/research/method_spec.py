"""Method -> candidate compiler (M1 of DOCS/AUTONOMOUS_FI_INFRASTRUCTURE).

Closes the loop the architecture doc calls THE missing link: an external
claim (paper, scout distillate, operator hypothesis) enters as a
``MethodSpec`` — hypothesis text, allow-listed strategy family, bounded
numeric parameters, falsification criteria, provenance. ``compile_rule``
turns it into a concrete ``fn(closes, i) -> -1/0/+1`` the edge gate can
kill, and ``positions_triple`` maps the same rule onto the
(candidate_positions, baseline_positions, bar_returns) contract that
``ResearchEngine.evaluate_strategy`` consumes.

Hard rules (inherited from the RSI Level-1 candidate space):
  - family must be in ``FAMILIES`` — no free code, ever
  - every parameter must sit inside its declared bounds and be finite
  - a spec is declared BEFORE evaluation; the compiled artifact records
    the spec hash so post-hoc tuning is visible
  - output is advisory evidence only — promotion stays behind the
    signed RSI evaluator / OperatorAuthorization

Lookahead convention: ``positions_triple`` emits
``bar_returns[i] = closes[i+1]/closes[i] - 1`` and
``candidate_positions[i] = rule(closes, i)`` — a signal computed on
closes[..i] earns the NEXT bar's return. Position 0 = flat.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

RuleFn = Callable[[np.ndarray, int], int]


class SpecError(ValueError):
    """MethodSpec missing, malformed, or outside the candidate space."""


@dataclass
class MethodSpec:
    """A declared, bounded, falsifiable strategy claim.

    ``pair`` is required iff family == "stat_arb": the hedge leg as
    {"db", "symbol", "timeframe"} — the primary dataset supplies leg A.
    """

    spec_id: str
    hypothesis: str
    family: str
    params: Dict[str, float] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    falsification: str = ""
    required_data: str = "close"
    horizon_bars: int = 1
    pair: Optional[Dict[str, str]] = None

    def canonical(self) -> bytes:
        return json.dumps(
            {k: v for k, v in self.__dict__.items()},
            sort_keys=True, separators=(",", ":"), default=str).encode()

    @property
    def spec_hash(self) -> str:
        return hashlib.sha256(self.canonical()).hexdigest()[:16]


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) \
        and math.isfinite(x)


# ------------------------------------------------------------------
# Allow-listed parametric families. Each declares numeric bounds and a
# factory producing fn(closes, i) -> -1/0/+1.
# ------------------------------------------------------------------

def _mom_rule(lookback: int, threshold_bps: float) -> RuleFn:
    th = threshold_bps / 1e4

    def rule(closes: np.ndarray, i: int) -> int:
        if i < lookback:
            return 0
        base = closes[i - lookback]
        if base <= 0:
            return 0
        r = (closes[i] - base) / base
        if r > th:
            return 1
        if r < -th:
            return -1
        return 0
    return rule


def _meanrev_rule(window: int, z: float) -> RuleFn:
    def rule(closes: np.ndarray, i: int) -> int:
        if i < window:
            return 0
        w = closes[i - window + 1:i + 1]
        m, s = float(np.mean(w)), float(np.std(w))
        if s <= 0:
            return 0
        dev = (closes[i] - m) / s
        if dev > z:
            return -1
        if dev < -z:
            return 1
        return 0
    return rule


def _donchian_rule(channel: int) -> RuleFn:
    def rule(closes: np.ndarray, i: int) -> int:
        if i < channel + 1:
            return 0
        hi = float(np.max(closes[i - channel:i]))
        lo = float(np.min(closes[i - channel:i]))
        if closes[i] > hi:
            return 1
        if closes[i] < lo:
            return -1
        return 0
    return rule


def _volmom_rule(vol_short: int, vol_long: int, vr_min: float,
                 lookback: int) -> RuleFn:
    """Momentum gated on realized-vol expansion — the verified RV
    channel: short/long vol ratio above vr_min means the move is
    repricing, not noise."""
    def rule(closes: np.ndarray, i: int) -> int:
        if i < vol_long + 1 or i < lookback:
            return 0
        r = np.diff(np.log(closes[i - vol_long:i + 1]))
        if len(r) < vol_short:
            return 0
        s = float(np.std(r[-vol_short:]))
        l = float(np.std(r))
        if l <= 0 or s / l < vr_min:
            return 0
        base = closes[i - lookback]
        if base <= 0:
            return 0
        ret = (closes[i] - base) / base
        if ret > 0:
            return 1
        if ret < 0:
            return -1
        return 0
    return rule


PAIR_FAMILIES = {"stat_arb"}


def _statarb_rule(window: int, z: float, hedge: float):
    """Pairs rule on ALIGNED series: spread = log(a) - hedge*log(b);
    fade z-score extremes. Returns fn2(a, b, i) -> -1/0/+1 where the
    position is on the SPREAD (long spread = long a / short b)."""
    def rule2(a: np.ndarray, b: np.ndarray, i: int) -> int:
        if i < window:
            return 0
        sa = np.log(a[i - window + 1:i + 1])
        sb = np.log(b[i - window + 1:i + 1])
        if np.any(sa <= 0) or np.any(sb <= 0):
            return 0
        spread = sa - hedge * sb
        m, s = float(np.mean(spread)), float(np.std(spread))
        if s <= 0:
            return 0
        dev = (spread[-1] - m) / s
        if dev > z:
            return -1
        if dev < -z:
            return 1
        return 0
    return rule2


FAMILIES: Dict[str, Dict[str, Any]] = {
    "momentum": {
        "description": "follow w-bar return beyond threshold",
        "bounds": {"lookback": (2, 60), "threshold_bps": (1.0, 200.0)},
        "defaults": {"lookback": 10, "threshold_bps": 15.0},
        "factory": lambda p: _mom_rule(int(p["lookback"]),
                                       float(p["threshold_bps"])),
    },
    "meanrev": {
        "description": "fade close vs rolling mean by z sigma",
        "bounds": {"window": (10, 100), "z": (0.5, 4.0)},
        "defaults": {"window": 20, "z": 2.0},
        "factory": lambda p: _meanrev_rule(int(p["window"]), float(p["z"])),
    },
    "donchian": {
        "description": "follow channel breakout",
        "bounds": {"channel": (5, 60)},
        "defaults": {"channel": 20},
        "factory": lambda p: _donchian_rule(int(p["channel"])),
    },
    "stat_arb": {
        "description": "fade log-spread z-score vs hedge leg "
                       "(PAIR family — needs spec.pair)",
        "bounds": {"window": (20, 250), "z": (0.5, 4.0),
                   "hedge": (0.3, 3.0)},
        "defaults": {"window": 60, "z": 2.0, "hedge": 1.0},
        "factory": lambda p: _statarb_rule(int(p["window"]),
                                           float(p["z"]),
                                           float(p["hedge"])),
        "pair": True,
    },
    "vol_regime_momentum": {
        "description": "momentum only when short/long vol ratio expands",
        "bounds": {"vol_short": (5, 50), "vol_long": (vol_long_min := 20, 200),
                   "vr_min": (1.0, 3.0), "lookback": (2, 30)},
        "defaults": {"vol_short": 20, "vol_long": 100, "vr_min": 1.2,
                     "lookback": 8},
        "factory": lambda p: _volmom_rule(int(p["vol_short"]),
                                          int(p["vol_long"]),
                                          float(p["vr_min"]),
                                          int(p["lookback"])),
    },
}


def compile_rule(spec: MethodSpec) -> RuleFn:
    """Validate a MethodSpec and return its rule function.

    Raises SpecError on: unknown family, non-finite param, param
    outside declared bounds, missing spec_id/hypothesis.
    """
    if not spec.spec_id or not spec.hypothesis:
        raise SpecError("spec_id and hypothesis are required")
    fam = FAMILIES.get(spec.family)
    if fam is None:
        raise SpecError(
            f"family {spec.family!r} not allow-listed; "
            f"have {sorted(FAMILIES)}")
    merged = dict(fam["defaults"])
    for k, v in spec.params.items():
        if k not in fam["bounds"]:
            raise SpecError(
                f"param {k!r} not declared for family {spec.family!r}; "
                f"allowed: {sorted(fam['bounds'])}")
        if not _finite(v):
            raise SpecError(f"param {k!r} not finite: {v!r}")
        lo, hi = fam["bounds"][k]
        if not (lo <= float(v) <= hi):
            raise SpecError(
                f"param {k}={v} outside bounds [{lo}, {hi}]")
        merged[k] = v
    # cross-param sanity: windows must nest
    if spec.family == "vol_regime_momentum" and \
            merged["vol_short"] >= merged["vol_long"]:
        raise SpecError("vol_short must be < vol_long")
    if fam.get("pair"):
        if not isinstance(spec.pair, dict) or not all(
                spec.pair.get(k) for k in ("db", "symbol", "timeframe")):
            raise SpecError(
                f"family {spec.family!r} is a PAIR family — spec.pair "
                "must declare {db, symbol, timeframe} for the hedge leg")
    return fam["factory"](merged)


def positions_triple(rule_fn: RuleFn, closes: np.ndarray,
                     ) -> Tuple[List[float], List[float], List[float]]:
    """Map a rule onto the evaluate_strategy contract.

    Returns (candidate_positions, baseline_positions, bar_returns):
      candidate_positions[i] = rule(closes, i) for i < n-1 (0 flat)
      baseline_positions[i]   = 0.0  — honest flat baseline
      bar_returns[i]          = closes[i+1]/closes[i] - 1
    A signal on closes[..i] therefore earns the NEXT bar's return —
    no lookahead.
    """
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    pos: List[float] = []
    rets: List[float] = []
    for i in range(n - 1):
        pos.append(float(rule_fn(closes, i)))
        c0, c1 = closes[i], closes[i + 1]
        rets.append(float(c1 / c0 - 1.0) if c0 > 0 else 0.0)
    base = [0.0] * len(pos)
    return pos, base, rets


def align_pair(a_ts: List[str], a: np.ndarray,
               b_ts: List[str], b: np.ndarray
               ) -> Tuple[np.ndarray, np.ndarray]:
    """Inner-join two series on timestamp -> aligned close arrays.
    Both inputs must be timestamp-ordered; output preserves a's order."""
    bmap = {t: i for i, t in enumerate(b_ts)}
    ai, bi = [], []
    for i, t in enumerate(a_ts):
        j = bmap.get(t)
        if j is not None:
            ai.append(i)
            bi.append(j)
    if len(ai) < 50:
        raise SpecError(
            f"pair alignment too thin: {len(ai)} shared timestamps")
    return a[np.asarray(ai)], b[np.asarray(bi)]


def pair_triple(rule2, a: np.ndarray, b: np.ndarray,
                hedge: float
                ) -> Tuple[List[float], List[float], List[float]]:
    """evaluate_strategy contract for a PAIR candidate: position is on
    the synthetic spread; bar_returns[i] = ret_a - hedge*ret_b (the
    spread's simple return). Lookahead-free: signal at i earns i->i+1.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = len(a)
    pos: List[float] = []
    rets: List[float] = []
    for i in range(n - 1):
        pos.append(float(rule2(a, b, i)))
        ra = a[i + 1] / a[i] - 1.0 if a[i] > 0 else 0.0
        rb = b[i + 1] / b[i] - 1.0 if b[i] > 0 else 0.0
        rets.append(float(ra - hedge * rb))
    return pos, [0.0] * len(pos), rets


def pair_pnl_bps(rule2, a: np.ndarray, b: np.ndarray, hedge: float,
                 cost_bps: float) -> "np.ndarray":
    """Per-bar net bps for a pair candidate on ALIGNED series.

    pos[i] = rule2(a,b,i) earns spread return i->i+1
    (ret_a - hedge*ret_b); turnover charged cost_bps PER LEG (x2).
    Index i corresponds to aligned bar i; length n-1.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = len(a)
    pos = np.array([float(rule2(a, b, i)) for i in range(n - 1)])
    ra = a[1:] / a[:-1] - 1.0
    rb = b[1:] / b[:-1] - 1.0
    spr_bps = (ra - hedge * rb) * 1e4
    dpos = np.abs(np.diff(np.concatenate([[0.0], pos])))
    return pos * spr_bps - dpos * cost_bps * 2.0


def spec_from_dict(d: Dict[str, Any]) -> MethodSpec:
    """Build a MethodSpec from a JSON-able dict; unknown keys kept in
    provenance so nothing is silently dropped."""
    known = {"spec_id", "hypothesis", "family", "params", "provenance",
             "falsification", "required_data", "horizon_bars", "pair"}
    extra = {k: v for k, v in d.items() if k not in known}
    prov = dict(d.get("provenance") or {})
    if extra:
        prov["spec_extra_keys"] = extra
    return MethodSpec(
        spec_id=str(d.get("spec_id", "")),
        hypothesis=str(d.get("hypothesis", "")),
        family=str(d.get("family", "")),
        params=dict(d.get("params") or {}),
        provenance=prov,
        falsification=str(d.get("falsification", "")),
        required_data=str(d.get("required_data", "close")),
        horizon_bars=int(d.get("horizon_bars", 1)),
        pair=dict(d.get("pair")) if d.get("pair") else None,
    )
