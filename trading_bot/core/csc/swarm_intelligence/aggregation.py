"""Voting mechanisms for the advisory swarm.

Pure functions over SwarmVote lists. Four mechanisms — majority,
performance-weighted, Bayesian sensor fusion, and Borda ranked ballots —
each returning a MethodResult. Agreement across methods is itself an
emergent confidence signal computed by the service.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from .models import DIRECTIONS, MethodResult, SwarmVote, VotingMethod

_DIRECTIONAL = ("BUY", "SELL")
_MIN_RELIABILITY = 0.51   # a node is never trusted below chance
_MAX_RELIABILITY = 0.99   # nor fully — one node can never dominate alone


def _signed(vote: SwarmVote) -> float:
    return {"BUY": 1.0, "SELL": -1.0}.get(vote.direction, 0.0)


def majority(votes: List[SwarmVote]) -> MethodResult:
    """Simple plurality; ties fall to HOLD (no conviction to break them)."""
    tally = {d: 0 for d in DIRECTIONS}
    conf_by_dir = {d: 0.0 for d in DIRECTIONS}
    for v in votes:
        d = v.direction if v.direction in DIRECTIONS else "HOLD"
        tally[d] += 1
        conf_by_dir[d] += v.confidence
    best = max(tally, key=lambda d: (tally[d], conf_by_dir[d]))
    if tally[best] == 0:
        return MethodResult(VotingMethod.MAJORITY.value, "HOLD", 0.0,
                            {"tally": tally})
    direction = best if tally[best] > len(votes) / 2 else "HOLD"
    confidence = tally[best] / max(1, len(votes))
    return MethodResult(VotingMethod.MAJORITY.value, direction, confidence,
                        {"tally": tally})


def weighted(votes: List[SwarmVote]) -> MethodResult:
    """Performance-weighted directional mass."""
    net = den = 0.0
    for v in votes:
        mass = v.weight * v.confidence
        net += _signed(v) * mass
        den += mass
    if den <= 0:
        return MethodResult(VotingMethod.WEIGHTED.value, "HOLD", 0.0)
    direction = "BUY" if net > 0 else ("SELL" if net < 0 else "HOLD")
    return MethodResult(VotingMethod.WEIGHTED.value, direction,
                        abs(net) / den, {"net": net, "total_mass": den})


def bayesian(
    votes: List[SwarmVote],
    reliabilities: Optional[Dict[str, float]] = None,
) -> MethodResult:
    """Sensor fusion: each node is a noisy channel on the true direction.

    ``reliabilities[node_id]`` is the learned per-node skill (Beta mean,
    clipped to [_MIN, _MAX]); an unmeasured node defaults to the floor so
    it informs but never carries the posterior alone. HOLD votes are
    direction-uninformative and contribute nothing.
    """
    llr = 0.0
    used = 0
    for v in votes:
        if v.direction not in _DIRECTIONAL:
            continue
        r = (reliabilities or {}).get(v.node_id, _MIN_RELIABILITY)
        r = min(_MAX_RELIABILITY, max(_MIN_RELIABILITY, float(r)))
        step = math.log(r / (1.0 - r)) * v.confidence
        llr += step if v.direction == "BUY" else -step
        used += 1
    if used == 0:
        return MethodResult(VotingMethod.BAYESIAN.value, "HOLD", 0.0,
                            {"llr": llr, "sensors": used})
    p_buy = 1.0 / (1.0 + math.exp(-llr))
    direction = "BUY" if p_buy > 0.5 else "SELL"
    return MethodResult(VotingMethod.BAYESIAN.value, direction,
                        abs(p_buy - 0.5) * 2.0,
                        {"p_buy": p_buy, "sensors": used})


def borda(votes: List[SwarmVote]) -> MethodResult:
    """Ranked ballot: a directional vote ranks its direction first and
    HOLD second (conviction c vs 1-c); a HOLD vote ranks HOLD first and
    the directions tied last."""
    scores = {d: 0.0 for d in DIRECTIONS}
    for v in votes:
        w = v.weight
        c = v.confidence
        d = v.direction if v.direction in DIRECTIONS else "HOLD"
        if d == "HOLD":
            scores["HOLD"] += w * c
            scores["BUY"] += w * (1.0 - c) * 0.5
            scores["SELL"] += w * (1.0 - c) * 0.5
        else:
            scores[d] += w * c
            scores["HOLD"] += w * (1.0 - c)
    total = sum(scores.values())
    if total <= 0:
        return MethodResult(VotingMethod.BORDA.value, "HOLD", 0.0)
    best = max(scores, key=scores.get)
    return MethodResult(VotingMethod.BORDA.value, best,
                        scores[best] / total, {"scores": scores})


def aggregate_all(
    votes: List[SwarmVote],
    reliabilities: Optional[Dict[str, float]] = None,
) -> Dict[str, MethodResult]:
    """Run every mechanism on the same ballots."""
    results = {}
    for fn in (majority, weighted, borda):
        results[fn.__name__] = fn(votes)
    results["bayesian"] = bayesian(votes, reliabilities)
    return results
