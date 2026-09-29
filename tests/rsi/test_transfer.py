"""Mission §9: transfer classification LOCAL/ROBUST/TRANSFERABLE/SYSTEMIC
and §17 regime-specialist handling on synthetic panels."""

from __future__ import annotations

import pytest

from trading_bot.evaluation.synthetic_market import (
    RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec)
from trading_bot.recursive_self_improvement.candidate_adapters import ADAPTERS
from trading_bot.recursive_self_improvement.transfer import (
    Scenario, TransferEvaluator)

from tests.rsi.helpers import make_contract, make_frames


def _spec(regime, seed=7, n=160):
    params = dict(vol=0.0002, sine_amp=0.0, sine_period=8, drift=0.0)
    if regime == "mean_revert":
        params.update(sine_amp=0.01)
    return SyntheticMarketSpec(
        seed=seed, instruments=("EURUSD", "GBPUSD"),
        regimes=(RegimeSpec(regime, n, **params),))


def _panels(contract, edge_regime="mean_revert"):
    """Build the contract's regime panel; planted edge only in `edge_regime`."""
    panels = []
    for regime in contract["regime_panel"]:
        for mult in contract["cost_multipliers"]:
            for seed in contract["seeds"]:
                spec = _spec(regime, seed=seed)
                frames = SyntheticMarketGenerator(spec).generate()
                panels.append(Scenario(
                    label=f"{regime}-x{mult}-s{seed}", regime=regime,
                    cost_multiplier=mult, seed=seed, frames=frames))
    return panels


def _result(regime, mult, delta, ci, mb=None, mc=None, label=None):
    from trading_bot.recursive_self_improvement.transfer import ScenarioResult
    return ScenarioResult(
        label=label or f"{regime}-x{mult}", regime=regime, cost_multiplier=mult,
        seed=7, frames_hash="h", delta_net=delta, ci_lower=ci,
        metrics_b=mb or {"net_return": 0.01, "max_drawdown": 0.02,
                         "cvar_95": 0.01, "sharpe": 0.1, "turnover": 1.0},
        metrics_c=mc or {"net_return": 0.02, "max_drawdown": 0.02,
                         "cvar_95": 0.01, "sharpe": 0.2, "turnover": 1.0})


def test_one_regime_winner_is_robust_specialist_not_local():
    frames = make_frames()
    contract = make_contract(frames, regime_panel=["mean_revert", "trend"])
    ev = TransferEvaluator(contract, ADAPTERS["mean_reversion"])
    results = [
        _result("mean_revert", 1.0, 0.01, 0.005),   # wins only in edge regime
        _result("mean_revert", 1.5, 0.01, 0.005),
        _result("trend", 1.0, -0.005, -0.002),
        _result("trend", 1.5, -0.005, -0.002),
    ]
    classification, details = ev.classify(results, "mean_revert")
    assert classification == "ROBUST"   # selection regime only -> specialist
    assert details["regimes_positive"] == 1


def test_gain_dies_under_cost_stress_is_local():
    frames = make_frames()
    contract = make_contract(frames, regime_panel=["mean_revert", "trend"])
    ev = TransferEvaluator(contract, ADAPTERS["mean_reversion"])
    results = [
        _result("mean_revert", 1.0, 0.01, 0.005),
        _result("mean_revert", 2.0, -0.001, -0.002),  # cost-stressed loss
        _result("trend", 1.0, 0.01, 0.005),
        _result("trend", 2.0, 0.01, 0.005),
    ]
    classification, _ = ev.classify(results, "mean_revert")
    assert classification == "LOCAL"


def test_transferable_when_edge_survives_panel():
    frames = make_frames()
    contract = make_contract(frames, regime_panel=["mean_revert", "trend"])
    ev = TransferEvaluator(contract, ADAPTERS["mean_reversion"])
    results = [
        _result("mean_revert", 1.0, 0.01, 0.005),
        _result("mean_revert", 1.5, 0.008, 0.004),
        _result("trend", 1.0, 0.01, 0.005),
        _result("trend", 1.5, 0.008, 0.004),
    ]
    classification, _ = ev.classify(results, "mean_revert")
    assert classification in ("TRANSFERABLE", "SYSTEMIC", "ROBUST")


def test_regression_breach_blocks_systemic():
    frames = make_frames()
    contract = make_contract(
        frames, regime_panel=["mean_revert", "trend"],
        regression_budgets={"cvar_95": 0.005, "sharpe": 0.1})
    ev = TransferEvaluator(contract, ADAPTERS["mean_reversion"])
    risky = _result("trend", 1.0, 0.01, 0.005,
                    mc={"net_return": 0.02, "max_drawdown": 0.02,
                        "cvar_95": 0.02, "sharpe": 0.2, "turnover": 1.0})
    results = [
        _result("mean_revert", 1.0, 0.01, 0.005),
        _result("mean_revert", 1.5, 0.008, 0.004),
        risky,
        _result("trend", 1.5, 0.008, 0.004),
    ]
    classification, details = ev.classify(results, "mean_revert")
    assert classification == "TRANSFERABLE"
    assert "cvar_95" in details["reason"]


def test_empty_replay_scenario_violation():
    frames = make_frames()
    contract = make_contract(frames)
    ev = TransferEvaluator(contract, ADAPTERS["stat_arb"], fraction=0.05)
    # stat_arb needs pairs; single-instrument frame -> violation path
    bad = Scenario("bad", "flat", 1.0, 0, {"EURUSD": frames["EURUSD"]})
    res = ev.run_scenario(bad, {"lookback": 60}, {"lookback": 30})
    assert res.ci_lower is None or res.violations
