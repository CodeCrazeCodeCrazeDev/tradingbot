"""Venue-parity grading — does the simulator match the execution venue?

Algory's parity passport analog: a strategy's simulated equity path is
replayed through the venue's own tester (MT5 Strategy Tester, paper
runner, or any independent fill model) and the two per-bar net series are
compared bar-by-bar. The agreement rate maps to Algory's published grades:

    A >= 0.85   B >= 0.70   C >= 0.55   D >= 0.40   F < 0.40

This is a *bar-level proxy* for trade-level parity: it catches gross
simulation/venue divergence (different fills, costs, or logic) but cannot
see intra-bar ordering. Per-instrument grading is expected — the same
strategy can grade A on one market and F on another.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

GRADE_BANDS = (("A", 0.85), ("B", 0.70), ("C", 0.55), ("D", 0.40))


def _grade(score: float) -> str:
    for letter, floor in GRADE_BANDS:
        if score >= floor:
            return letter
    return "F"


@dataclass(frozen=True)
class ParityResult:
    grade: str
    score: float                 # fraction of bars in agreement, 0..1
    n_bars: int
    matched: int
    rel_tol: float
    abs_tol: float
    mean_abs_diff: float
    note: str = ("bar-level parity proxy: sign+magnitude agreement per bar; "
                 "not a substitute for trade-level matching")

    def to_dict(self) -> Dict[str, Any]:
        return {"grade": self.grade, "score": self.score, "n_bars": self.n_bars,
                "matched": self.matched, "rel_tol": self.rel_tol,
                "abs_tol": self.abs_tol, "mean_abs_diff": self.mean_abs_diff,
                "note": self.note}


def parity_grade(
    sim_nets: Sequence[float],
    venue_nets: Sequence[float],
    *,
    rel_tol: float = 0.5,
    abs_tol: float = 1e-9,
) -> ParityResult:
    """Grade agreement between two aligned per-bar net series.

    A bar matches when both series have the same sign (flat==flat counts)
    and the absolute difference is within ``max(abs_tol, rel_tol *
    max(|sim|, |venue|))``. Timestamps are not required — callers align
    series upstream; mismatched lengths are refused, not truncated.
    """
    sim = [float(x) for x in sim_nets]
    ven = [float(x) for x in venue_nets]
    if len(sim) != len(ven):
        raise ValueError(
            f"parity series length mismatch: sim={len(sim)} venue={len(ven)}")
    n = len(sim)
    if n == 0:
        return ParityResult(grade="F", score=0.0, n_bars=0, matched=0,
                            rel_tol=rel_tol, abs_tol=abs_tol,
                            mean_abs_diff=0.0)
    matched = 0
    total_diff = 0.0
    for s, v in zip(sim, ven):
        if not (math.isfinite(s) and math.isfinite(v)):
            continue
        total_diff += abs(s - v)
        tol = max(abs_tol, rel_tol * max(abs(s), abs(v)))
        same_sign = (s > 0) == (v > 0) and (s < 0) == (v < 0)
        if same_sign and abs(s - v) <= tol:
            matched += 1
    evaluated = sum(1 for s, v in zip(sim, ven)
                    if math.isfinite(s) and math.isfinite(v))
    score = matched / evaluated if evaluated else 0.0
    return ParityResult(
        grade=_grade(score), score=score, n_bars=evaluated, matched=matched,
        rel_tol=rel_tol, abs_tol=abs_tol,
        mean_abs_diff=total_diff / evaluated if evaluated else 0.0)


def parity_from_bar_rows(
    sim_rows: Sequence[Mapping[str, Any]],
    venue_rows: Sequence[Mapping[str, Any]],
    *,
    net_field: str = "net",
    ts_field: str = "timestamp",
    symbol_field: str = "symbol",
    rel_tol: float = 0.5,
    abs_tol: float = 1e-9,
) -> Dict[str, Any]:
    """Grade parity per symbol from paired bar-row lists.

    Rows must carry ``symbol``, ``timestamp`` and a net field (default
    ``"net"``). Rows are aligned on (symbol, timestamp); venue rows
    missing a sim counterpart are counted as mismatches. Returns a
    passport dict: overall grade = worst symbol grade (conservative —
    deployment decisions are per-market).
    """
    def index(rows):
        out: Dict[Tuple[Any, Any], float] = {}
        for r in rows:
            key = (r.get(symbol_field), r.get(ts_field))
            val = r.get(net_field)
            if key[0] is not None and key[1] is not None \
                    and isinstance(val, (int, float)):
                out[key] = float(val)
        return out

    sim_idx, ven_idx = index(sim_rows), index(venue_rows)
    keys = sorted(set(sim_idx) | set(ven_idx), key=lambda k: (str(k[0]), k[1]))
    by_symbol: Dict[str, List[Tuple[float, float]]] = {}
    for key in keys:
        sym = str(key[0])
        by_symbol.setdefault(sym, []).append(
            (sim_idx.get(key, float("nan")), ven_idx.get(key, float("nan"))))

    symbols: Dict[str, Any] = {}
    worst = "A"
    order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
    for sym, pairs in sorted(by_symbol.items()):
        res = parity_grade([p[0] for p in pairs], [p[1] for p in pairs],
                           rel_tol=rel_tol, abs_tol=abs_tol)
        # A counterpart missing on either side is a mismatch, not a skip —
        # parity_grade only scores finite pairs, so fold the missing count
        # back into the denominator here.
        total_pairs = len(pairs)
        missing = sum(1 for s, v in pairs
                      if not (math.isfinite(s) and math.isfinite(v)))
        if missing and total_pairs:
            score = res.matched / total_pairs
            res = ParityResult(
                grade=_grade(score), score=score, n_bars=total_pairs,
                matched=res.matched, rel_tol=res.rel_tol,
                abs_tol=res.abs_tol, mean_abs_diff=res.mean_abs_diff)
        symbols[sym] = res.to_dict()
        if order[res.grade] > order[worst]:
            worst = res.grade
    total = sum(s["n_bars"] for s in symbols.values())
    matched = sum(s["matched"] for s in symbols.values())
    overall = matched / total if total else 0.0
    return {
        "grade": worst if total else "F",
        "score": overall,
        "n_bars": total,
        "matched": matched,
        "symbols": symbols,
        "note": ("worst-symbol grade governs; bar-level proxy, "
                 "per-instrument results may diverge"),
    }
