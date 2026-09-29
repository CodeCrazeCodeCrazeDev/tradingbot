"""Canonical metric registry for the multi-objective improvement contract.

Every metric the RSI evaluator can report is declared here once, with unit
and optimization direction. Contracts reference only registered names so an
evaluator change cannot silently redefine what "improvement" means.
"""

from __future__ import annotations

from typing import Dict, Tuple

# name -> (unit, direction) where direction is "max", "min", or "info".
# "info" metrics are reported but never used for constraint/Pareto decisions.
METRIC_REGISTRY: Dict[str, Tuple[str, str]] = {
    # Economic
    "net_return": ("fraction", "max"),
    "gross_return": ("fraction", "max"),
    "sharpe": ("ratio", "max"),
    "sortino": ("ratio", "max"),
    "calmar": ("ratio", "max"),
    "expectancy": ("fraction", "max"),
    "profit_factor": ("ratio", "max"),
    "alpha_vs_baseline": ("fraction", "max"),
    # Risk (all minimize)
    "max_drawdown": ("fraction", "min"),
    "drawdown_duration_bars": ("bars", "min"),
    "cvar_95": ("fraction", "min"),
    "downside_deviation": ("fraction", "min"),
    "turnover": ("fraction", "min"),
    "exposure_mean": ("fraction", "min"),
    "exposure_max": ("fraction", "min"),
    "single_bar_max_loss": ("fraction", "min"),
    # Robustness
    "regime_min_net": ("fraction", "max"),
    "regime_frac_positive": ("fraction", "max"),
    "cost_stress_min_net": ("fraction", "max"),
    "seed_spread_net": ("fraction", "min"),
    "parameter_sensitivity": ("fraction", "min"),
    # Statistical validity
    "n_bars": ("count", "info"),
    "n_instruments": ("count", "info"),
    "n_trades": ("count", "info"),
    "n_effective": ("count", "info"),
    "paired_mean_diff": ("fraction", "max"),
    "paired_ci_lower": ("fraction", "max"),
    "effect_size": ("ratio", "max"),
    "trial_count": ("count", "info"),
    "deflated_sharpe": ("ratio", "max"),
    "pbo": ("fraction", "min"),
    # Prediction quality (not applicable to direction-only strategies)
    "brier": ("fraction", "min"),
    "log_loss": ("fraction", "min"),
    "ece": ("fraction", "min"),
    # Operational
    "latency_ms": ("ms", "min"),
    "compute_seconds": ("seconds", "min"),
    # Behaviour
    "abstain_rate": ("fraction", "info"),
    "zero_trade_frac": ("fraction", "min"),
}

DEFAULT_PARETO_OBJECTIVES = ("net_return", "max_drawdown", "cvar_95", "turnover")


def direction(name: str) -> str:
    try:
        return METRIC_REGISTRY[name][1]
    except KeyError as exc:
        raise KeyError(f"unregistered metric {name!r}") from exc


def is_better(name: str, candidate: float, baseline: float, tol: float = 0.0) -> bool:
    d = direction(name)
    if d == "max":
        return candidate > baseline + tol
    if d == "min":
        return candidate < baseline - tol
    return False


def is_worse(name: str, candidate: float, baseline: float, tol: float = 0.0) -> bool:
    d = direction(name)
    if d == "max":
        return candidate < baseline - tol
    if d == "min":
        return candidate > baseline + tol
    return False
