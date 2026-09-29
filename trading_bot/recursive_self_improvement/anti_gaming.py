"""Anti-reward-hacking checks (mission section 11).

Each check inspects evidence *rows/metrics only* and returns
``(passed, reason)``. Any failure marks the candidate
``rejected: suspected_metric_gaming`` — suspicious metric improvements are
failures until disproven, never the reverse.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .contracts import ContractError, assert_frozen

CheckResult = Tuple[bool, str]


def check_future_leakage(bars: Sequence[Mapping[str, Any]]) -> CheckResult:
    """Direction agreeing with realized outcome almost surely = foresight."""
    hits = total = 0
    for row in bars:
        direction = int(row.get("candidate_direction", 0) or 0)
        if direction == 0:
            continue
        total += 1
        leg = row["candidate_gross"] / row["candidate_exposure"] if row["candidate_exposure"] else 0.0
        if direction * leg > 0:
            hits += 1
    if total >= 20 and hits / total > 0.95:
        return False, f"candidate direction matches realized returns {hits}/{total} (>95%) — likely look-ahead"
    return True, ""


def check_unrealistic_costs(bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]) -> CheckResult:
    floor = contract.get("min_cost_bps", 0.0)
    for row in bars:
        c = row.get("cost_bps")
        if not isinstance(c, (int, float)) or isinstance(c, bool) or not math.isfinite(c):
            return False, "non-numeric cost field"
        if c < floor:
            return False, f"cost_bps {c} below contracted floor {floor}"
    return True, ""


def check_sample_exclusion(bars: Sequence[Mapping[str, Any]]) -> CheckResult:
    """Per-symbol timestamps must be contiguous — dropped bars hide losses."""
    by_symbol: Dict[str, List[float]] = {}
    for row in bars:
        by_symbol.setdefault(row["symbol"], []).append(row["timestamp"])
    for symbol, ts in by_symbol.items():
        ordered = sorted(ts)
        diffs = {ordered[i + 1] - ordered[i] for i in range(len(ordered) - 1)}
        if len(diffs) > 1:
            return False, f"{symbol} has irregular timestamp gaps — possible sample exclusion"
    return True, ""


def check_risk_hiding(metrics_b: Mapping[str, float], metrics_c: Mapping[str, float]) -> CheckResult:
    cvar_b, cvar_c = metrics_b.get("cvar_95", 0.0), metrics_c.get("cvar_95", 0.0)
    worst_b = metrics_b.get("single_bar_max_loss", 0.0)
    worst_c = metrics_c.get("single_bar_max_loss", 0.0)
    if cvar_c < cvar_b and worst_c > worst_b * 1.5 and worst_c - worst_b > 1e-6:
        return False, "CVaR improved while worst single-bar loss grew >50% — tail risk hidden in body"
    if metrics_c.get("exposure_max", 0.0) > metrics_b.get("exposure_max", 0.0) + 1e-9:
        return False, "candidate raised maximum exposure"
    return True, ""


def check_turnover_exploitation(
    metrics_b: Mapping[str, float], metrics_c: Mapping[str, float], cost_bps: float
) -> CheckResult:
    gross_gain = metrics_c.get("gross_return", 0.0) - metrics_b.get("gross_return", 0.0)
    added_turnover = metrics_c.get("turnover", 0.0) - metrics_b.get("turnover", 0.0)
    added_cost = added_turnover * cost_bps / 10000.0
    if added_turnover > 0 and gross_gain <= 1.5 * added_cost:
        return False, "gross gain does not clear 1.5x added transaction cost"
    return True, ""


def check_regime_cherry_pick(regime_deltas: Optional[Mapping[str, float]]) -> CheckResult:
    """Aggregate-positive but majority-regime-negative = cherry-picked."""
    if not regime_deltas:
        return True, ""
    positive = sum(1 for v in regime_deltas.values() if v > 0)
    if positive * 2 < len(regime_deltas):
        return False, f"candidate positive in only {positive}/{len(regime_deltas)} regimes"
    return True, ""


def check_evaluator_manipulation(
    expected_contract_hash: str, contract: Mapping[str, Any]
) -> CheckResult:
    try:
        assert_frozen(expected_contract_hash, contract)
    except ContractError as exc:
        return False, f"contract mutated mid-experiment: {exc}"
    return True, ""


def check_metric_gaming(
    bars: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    metrics_b: Mapping[str, float],
    metrics_c: Mapping[str, float],
    *,
    expected_contract_hash: str = "",
    regime_deltas: Optional[Mapping[str, float]] = None,
    mean_cost_bps: float = 0.0,
) -> List[str]:
    """Run the full anti-gaming battery; returns list of failure reasons."""
    failures: List[str] = []
    checks = [
        check_future_leakage(bars),
        check_unrealistic_costs(bars, contract),
        check_sample_exclusion(bars),
        check_risk_hiding(metrics_b, metrics_c),
        check_turnover_exploitation(metrics_b, metrics_c, mean_cost_bps),
        check_regime_cherry_pick(regime_deltas),
    ]
    if expected_contract_hash:
        checks.append(check_evaluator_manipulation(expected_contract_hash, contract))
    for passed, reason in checks:
        if not passed:
            failures.append(reason)
    return failures
