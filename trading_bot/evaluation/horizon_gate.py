"""Expansion-readiness gates for new horizons, instruments, and venues.

Each expansion target (swing horizon, additional FX pairs, crypto/equities,
scalping) must clear its own evidence gate before it may enter even paper
evaluation. The gate is a pure function of measured prerequisites — it
returns what is missing, never grants readiness on intent.

Gate contract (all required):
  * dataset_bars >= min_bars        — real history exists for the target
  * paired OOS comparison exists    — frozen-baseline evidence was produced
    for the target's regime (frozen_baseline.compare_candidate_vs_baseline)
  * cost model present for target   — net-of-cost evaluation is possible
  * drawdown within contract budget — measured, not assumed
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Deliberately conservative floors. An expansion with less evidence than
# this is "insufficient evidence", not a failure to try.
MIN_BARS_BY_HORIZON = {
    "scalp": 50_000,      # microstructure; smallest bars, biggest sample need
    "intraday": 5_000,
    "swing": 2_000,       # multi-day bars are scarce — highest per-bar value
}


def check_expansion_readiness(
    target: str,
    *,
    dataset_bars: int,
    horizon: str,
    has_paired_oos_evidence: bool,
    has_cost_model: bool,
    measured_max_drawdown: Optional[float] = None,
    drawdown_budget: Optional[float] = None,
) -> Dict[str, Any]:
    """Return {"ready": bool, "unmet": [...], "evidence_class": ...}.

    ``ready=True`` only means the target may enter *paper* evaluation — it
    is not authorization and never will be from this module."""
    unmet: List[str] = []

    min_bars = MIN_BARS_BY_HORIZON.get(horizon)
    if min_bars is None:
        unmet.append(f"unknown horizon class '{horizon}'")
    elif dataset_bars < min_bars:
        unmet.append(
            f"dataset too small: {dataset_bars} bars < {min_bars} required "
            f"for {horizon}")

    if not has_paired_oos_evidence:
        unmet.append(
            "no paired out-of-sample frozen-baseline comparison for target")

    if not has_cost_model:
        unmet.append("no cost model for target venue/instrument")

    if drawdown_budget is not None:
        if measured_max_drawdown is None:
            unmet.append("drawdown budget set but no measured drawdown")
        elif measured_max_drawdown > drawdown_budget:
            unmet.append(
                f"measured drawdown {measured_max_drawdown:.4f} exceeds "
                f"budget {drawdown_budget:.4f}")

    return {
        "target": target,
        "horizon": horizon,
        "ready": not unmet,
        "unmet": unmet,
        "evidence_class": "readiness_check",
        "note": "ready=True authorizes paper evaluation only — promotion "
                "still requires evaluate_verified under a sealed contract",
    }
