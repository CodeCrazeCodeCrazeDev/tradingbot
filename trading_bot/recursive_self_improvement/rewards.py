"""Reward projection of the canonical evaluator's verdict, not an evaluator.

Called only after the independent evaluator in engine_v2. Does not alter the
contract, Pareto objectives, anti-gaming checks or promotion ladder.
"""
from typing import Any, Mapping

from trading_bot.core.csc.rewards import Objective, RewardRecord, finite
from .metric_registry import METRIC_REGISTRY


def reward_from_verdict(trial_id: str, verdict: Mapping[str, Any]) -> RewardRecord:
    status = verdict.get("status", "insufficient_evidence")
    blockers = [] if status == "eligible_for_operator_review" else [str(status)]
    metrics = verdict.get("metrics") or {}
    objectives = []
    for name, (unit, direction) in METRIC_REGISTRY.items():
        if direction == "info":
            continue
        candidate, baseline = (metrics.get("candidate_" + name),
                               metrics.get("baseline_" + name))
        if finite(candidate) and finite(baseline):
            # Orient deltas so positive always means improvement; retain units.
            gain = candidate - baseline if direction == "max" else baseline - candidate
            if finite(gain):
                objectives.append(Objective(name + "_improvement", gain, unit))
    if not objectives:
        blockers.append("missing_paired_metrics")
    # Success credit is separate from the objective vector. A rejected but
    # profitable candidate has zero success credit, never compensating risk.
    objectives.append(Objective("evaluation_credit", float(not blockers), "fraction"))
    # The evaluator may have replayed synthetic or historical frames; its
    # verdict alone does not establish which. Never label toy data real.
    return RewardRecord("rsi", trial_id, "unknown", tuple(objectives),
                        tuple(blockers))
