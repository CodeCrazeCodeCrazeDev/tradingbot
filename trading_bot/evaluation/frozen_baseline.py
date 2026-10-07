"""Frozen-baseline comparison — brain-level promotion evidence.

Compares a candidate decision stream (the CSC's settled outcomes) against a
frozen simple baseline over the same bars, net of cost, with a drawdown
budget. This is the "candidate must beat a frozen baseline" check the
promotion ladder requires before any learning-driven change is considered.

Honesty contract:
  - Both sides are scored on the SAME bars with the SAME cost model.
  - Turnover charges only when the position changes.
  - Too few comparisons -> "insufficient_evidence", never a verdict.
  - This module emits EVIDENCE_CLASS="diagnostic"; promotion eligibility is
    only ever granted by recursive_self_improvement.evaluation
    .evaluate_verified under a signed contract + sealed holdout attestation.
    A "candidate_superior" verdict here is an *input* to that process, not
    a promotion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

EVIDENCE_CLASS = "diagnostic"

# Position vocabulary: +1 long, -1 short, 0 flat.
_FLAT, _LONG, _SHORT = 0, 1, -1


@dataclass
class SideMetrics:
    """Per-side equity statistics, net of cost."""

    n_decisions: int = 0
    total_gross: float = 0.0
    total_net: float = 0.0
    total_turnover: float = 0.0
    cost_paid: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    equity_curve: List[float] = field(default_factory=list)


def _equity_metrics(net_returns: Sequence[float]) -> Dict[str, float]:
    equity = peak = 1.0
    max_dd = 0.0
    for r in net_returns:
        equity *= 1.0 + r
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
    return {"net_return": equity - 1.0, "max_drawdown": max_dd}


def score_side(
    positions: Sequence[float],
    bar_returns: Sequence[float],
    *,
    cost_bps: float,
    fraction: float = 0.01,
) -> SideMetrics:
    """Score one decision stream over the bars.

    ``positions[i]`` is the signed exposure decision taken at bar i
    (-1/0/+1, or a continuous signed fraction); the return of bar i+1 is
    what the decision earns — strictly no lookahead. Costs are charged on
    position changes only.
    """
    if not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("cost_bps must be a non-negative finite number")
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    n = min(len(positions), len(bar_returns))
    m = SideMetrics()
    prev_pos = 0.0
    net_returns: List[float] = []
    wins = 0
    for i in range(n):
        pos = float(positions[i])
        if not math.isfinite(pos):
            pos = 0.0
        pos = max(-1.0, min(1.0, pos))
        turnover = abs(pos - prev_pos) * fraction
        # gross = signed exposure * realized bar return * position fraction
        gross = pos * float(bar_returns[i]) * fraction
        cost = turnover * cost_bps / 10000.0
        net = gross - cost
        m.total_gross += gross
        m.total_net += net
        m.total_turnover += turnover
        m.cost_paid += cost
        if net > 0:
            wins += 1
        net_returns.append(net)
        prev_pos = pos
    m.n_decisions = n
    m.win_rate = wins / n if n else 0.0
    eq = _equity_metrics(net_returns)
    m.max_drawdown = eq["max_drawdown"]
    return m


def compare_candidate_vs_baseline(
    candidate_positions: Sequence[float],
    baseline_positions: Sequence[float],
    bar_returns: Sequence[float],
    *,
    cost_bps: float,
    fraction: float = 0.01,
    min_decisions: int = 20,
    max_dd_regression: float = 0.0,
    min_net_edge: float = 1e-6,
) -> Dict[str, Any]:
    """Frozen-baseline comparison report.

    verdict:
      * ``insufficient_evidence`` — too few paired decisions to say anything.
      * ``candidate_superior``   — candidate net total exceeds baseline by
        more than ``min_net_edge`` AND its max drawdown did not regress by
        more than ``max_dd_regression``.
      * ``not_superior``         — otherwise.
    """
    candidate = score_side(
        candidate_positions, bar_returns, cost_bps=cost_bps, fraction=fraction)
    baseline = score_side(
        baseline_positions, bar_returns, cost_bps=cost_bps, fraction=fraction)

    n = min(candidate.n_decisions, baseline.n_decisions)
    report: Dict[str, Any] = {
        "evidence_class": EVIDENCE_CLASS,
        "promotion_eligible": False,  # only evaluate_verified may grant this
        "cost_bps": cost_bps,
        "fraction": fraction,
        "n_decisions": n,
        "candidate": {
            "total_gross": candidate.total_gross,
            "total_net": candidate.total_net,
            "cost_paid": candidate.cost_paid,
            "turnover": candidate.total_turnover,
            "max_drawdown": candidate.max_drawdown,
            "win_rate": candidate.win_rate,
        },
        "baseline": {
            "total_gross": baseline.total_gross,
            "total_net": baseline.total_net,
            "cost_paid": baseline.cost_paid,
            "turnover": baseline.total_turnover,
            "max_drawdown": baseline.max_drawdown,
            "win_rate": baseline.win_rate,
        },
    }

    if n < min_decisions:
        report["verdict"] = "insufficient_evidence"
        report["reason"] = f"{n} paired decisions < min_decisions {min_decisions}"
        return report

    # A candidate that never traded cannot claim an edge. Zero turnover with
    # zero gross means "abstained the whole window" — that is an honest
    # no_activity verdict, not superiority over a losing baseline.
    if candidate.total_turnover == 0.0 and candidate.total_gross == 0.0:
        report["verdict"] = "no_activity"
        report["reason"] = (
            "candidate held a flat position for the entire window; "
            "abstention is not evidence of edge")
        return report

    edge = candidate.total_net - baseline.total_net
    dd_regression = candidate.max_drawdown - baseline.max_drawdown
    report["net_edge"] = edge
    report["drawdown_regression"] = dd_regression
    if edge > min_net_edge and dd_regression <= max_dd_regression:
        report["verdict"] = "candidate_superior"
        report["reason"] = (
            f"candidate net edge {edge:+.6f} with drawdown regression "
            f"{dd_regression:+.4f} within budget {max_dd_regression}")
    else:
        report["verdict"] = "not_superior"
        report["reason"] = (
            f"net edge {edge:+.6f} (needs > {min_net_edge}); "
            f"drawdown regression {dd_regression:+.4f} "
            f"(budget {max_dd_regression})")
    return report


def csc_decisions_to_positions(
    decision_records: Sequence[Dict[str, Any]],
    n_bars: int,
) -> List[float]:
    """Project CSC audit/journal records onto a per-bar position series.

    Each record needs ``bar_index`` and ``action`` (BUY/SELL else flat).
    The position persists until the next decision — 'hold preserves
    position' semantics, matching PairedFamilyReplay.
    """
    positions = [0.0] * n_bars
    pos = 0.0
    by_bar = {}
    for rec in decision_records:
        try:
            idx = int(rec["bar_index"])
        except (KeyError, TypeError, ValueError):
            continue
        action = str(rec.get("action", "")).upper()
        by_bar[idx] = _LONG if action == "BUY" else (
            _SHORT if action == "SELL" else _FLAT)
    for i in range(n_bars):
        if i in by_bar:
            pos = by_bar[i]
        positions[i] = pos
    return positions
