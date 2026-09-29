"""Shared fixtures/helpers for the RSI v2 test-suite."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from trading_bot.evaluation.synthetic_market import (
    RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec, fingerprint_all)
from trading_bot.recursive_self_improvement.candidate_adapters import (
    ADAPTERS, candidate_code_hash, dependencies_hash)
from trading_bot.recursive_self_improvement.contracts import canonical, contract_hash
from trading_bot.recursive_self_improvement.improvement_genome import (
    ImprovementDomain, ImprovementGenome)
from trading_bot.recursive_self_improvement.protected_control_plane import (
    DEFAULT_PROTECTED_PATHS)


def make_frames(seed: int = 7, n_bars: int = 160,
                instruments: Sequence[str] = ("EURUSD", "GBPUSD"),
                regimes: Optional[Sequence[RegimeSpec]] = None):
    regs = tuple(regimes) if regimes else (
        RegimeSpec("mean_revert", n_bars, vol=0.0002, sine_amp=0.01, sine_period=8),)
    spec = SyntheticMarketSpec(seed=seed, instruments=tuple(instruments), regimes=regs)
    return SyntheticMarketGenerator(spec).generate()


def make_contract(frames: Mapping[str, Any], n_bars: int = 160,
                  **overrides: Any) -> Dict[str, Any]:
    contract: Dict[str, Any] = {
        "schema_version": 2,
        "contract_id": "rsi-v2-test-contract",
        "baseline_hash": "incumbent-mr-100",
        "dataset_hash": fingerprint_all(frames),
        "strategy_family": "mean_reversion",
        "allowed_parameters": {"lookback": [2, 200], "entry_threshold": [0.5, 4.0]},
        "min_bars": 20, "min_instruments": 2, "block_size": 4,
        "max_trials": 10, "minimum_net_gain": 1e-6,
        "economic_materiality_min": 1e-6,
        "max_drawdown": 0.5, "max_drawdown_regression": 0.05,
        "confidence": 0.95,
        "min_cost_bps": 1.0, "max_cost_bps": 10.0,
        "max_latency_ms": 60000.0, "max_exposure": 0.05,
        "max_cvar_95": 0.5, "max_turnover": 20.0,
        "cost_model_id": "synthetic-costs-v1",
        "code_hash": candidate_code_hash(),
        "dependencies_hash": dependencies_hash(),
        "metric_directions": {"net_return": "max", "max_drawdown": "min",
                              "cvar_95": "min", "turnover": "min"},
        "pareto_objectives": ["net_return", "max_drawdown", "cvar_95", "turnover"],
        "regression_budgets": {"sharpe": 5.0, "turnover": 50.0},
        "regime_panel": ["trend", "mean_revert"],
        "holdout_query_budget": 10, "max_recursion_depth": 1,
        "protected_paths": list(DEFAULT_PROTECTED_PATHS),
        "seeds": [7], "cost_multipliers": [1.0, 1.5],
        "train_end": -30, "validation_start": -20, "validation_end": -10,
        "holdout_start": 0, "holdout_end": float(n_bars),
        "expiry": 4102444800.0,
    }
    contract.update(overrides)
    return contract


def sign(key: Ed25519PrivateKey, payload: Mapping[str, Any]) -> str:
    return key.sign(canonical(payload)).hex()


def make_genome(contract: Mapping[str, Any], param: str = "lookback",
                value: float = 50, domain: ImprovementDomain = ImprovementDomain.TRADING_POLICY,
                metadata: Optional[Mapping[str, Any]] = None) -> ImprovementGenome:
    return ImprovementGenome(
        domain=domain,
        objective="test hypothesis",
        change_set={param: value},
        evaluation_plan={"contract_id": contract["contract_id"]},
        safety_constraints={},
        parent_id=contract["baseline_hash"],
        metadata=dict(metadata or {}),
    )


def fixture_bars(symbols: Sequence[str] = ("EURUSD", "GBPUSD"), n: int = 64,
                 baseline_net: float = 0.0001, candidate_net: float = 0.0003,
                 candidate_pattern: Optional[Sequence[float]] = None,
                 baseline_pattern: Optional[Sequence[float]] = None,
                 cost_bps: float = 5.0, exposure: float = 0.01,
                 turnover: float = 0.001) -> List[Dict[str, Any]]:
    """Deterministic paired rows for gate tests (valid cost arithmetic).

    Default patterns mix positive and negative legs (~75% winners) so a
    superior candidate is distinguishable from perfect foresight; direction
    is decoupled from outcome sign like a real signal stream.
    """
    if baseline_pattern is None:
        baseline_pattern = [baseline_net if i % 4 else -abs(baseline_net) * 2
                            for i in range(n)]
    if candidate_pattern is None:
        candidate_pattern = [candidate_net if i % 4 else -abs(baseline_net)
                             for i in range(n)]
    rows: List[Dict[str, Any]] = []
    for sym in symbols:
        for i in range(n):
            bn = baseline_pattern[i]
            cn = candidate_pattern[i]
            bg = bn + turnover * cost_bps / 10000.0
            cg = cn + turnover * cost_bps / 10000.0
            rows.append({
                "symbol": sym, "timestamp": float(i), "cost_bps": cost_bps,
                "baseline_gross": bg, "candidate_gross": cg,
                "baseline_turnover": turnover, "candidate_turnover": turnover,
                "baseline_exposure": exposure, "candidate_exposure": exposure,
                "baseline_net": bn, "candidate_net": cn,
                "baseline_direction": 1,
                "candidate_direction": 1,
            })
    return rows


def make_report(contract: Mapping[str, Any], genome: ImprovementGenome,
                bars: List[Dict[str, Any]], trial_count: int = 1,
                **overrides: Any) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "schema_version": 2,
        "contract_id": contract["contract_id"],
        "baseline_hash": contract["baseline_hash"],
        "dataset_hash": contract["dataset_hash"],
        "candidate_hash": genome.fingerprint,
        "trial_id": "trial-1",
        "trial_count": trial_count,
        "latency_ms": 12.0,
        "candidate_parameters": dict(genome.change_set),
        "holdout_attested": True,
        "verifier_id": "test-verifier",
        "cost_model_id": contract["cost_model_id"],
        "code_hash": contract["code_hash"],
        "dependencies_hash": contract["dependencies_hash"],
        "risk_invariants_passed": True,
        "parameter_effect_verified": True,
        "bars": bars,
    }
    report.update(overrides)
    return report
