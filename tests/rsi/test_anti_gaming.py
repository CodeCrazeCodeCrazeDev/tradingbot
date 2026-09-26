"""Mission §11 anti-reward-hacking checks, unit-tested per detection class."""

from __future__ import annotations

import pytest

from trading_bot.recursive_self_improvement.anti_gaming import (
    check_evaluator_manipulation, check_future_leakage,
    check_metric_gaming, check_regime_cherry_pick, check_risk_hiding,
    check_sample_exclusion, check_turnover_exploitation,
    check_unrealistic_costs)
from trading_bot.recursive_self_improvement.contracts import contract_hash

from tests.rsi.helpers import fixture_bars, make_contract, make_frames


def _contract():
    frames = make_frames()
    return make_contract(frames)


def test_future_leakage_perfect_foresight_flagged():
    bars = fixture_bars(n=40)
    for row in bars:
        # direction always agrees with realized outcome
        row["candidate_direction"] = 1
        row["candidate_exposure"] = 0.01
        row["candidate_gross"] = 0.001
    passed, reason = check_future_leakage(bars)
    assert not passed and "look-ahead" in reason


def test_future_leakage_normal_signals_pass():
    bars = fixture_bars(n=40)
    for i, row in enumerate(bars):
        row["candidate_direction"] = 1 if i % 2 else -1
        row["candidate_exposure"] = 0.01
        row["candidate_gross"] = 0.01 * (1 if i % 3 else -1)  # outcome independent of direction
    passed, _ = check_future_leakage(bars)
    assert passed


def test_unrealistic_costs_below_floor_flagged():
    contract = _contract()
    bars = fixture_bars(cost_bps=0.2)
    passed, reason = check_unrealistic_costs(bars, contract)
    assert not passed and "below contracted floor" in reason


def test_sample_exclusion_timestamp_gap_flagged():
    bars = fixture_bars(n=40)
    # remove a middle timestamp for one symbol
    bars = [b for b in bars if not (b["symbol"] == "EURUSD" and b["timestamp"] == 10.0)]
    passed, reason = check_sample_exclusion(bars)
    assert not passed and "exclusion" in reason


def test_risk_hiding_flagged():
    mb = {"cvar_95": 0.01, "single_bar_max_loss": 0.01, "exposure_max": 0.01}
    mc = {"cvar_95": 0.005, "single_bar_max_loss": 0.03, "exposure_max": 0.01}
    passed, reason = check_risk_hiding(mb, mc)
    assert not passed and "tail risk" in reason


def test_turnover_exploitation_flagged():
    mb = {"gross_return": 0.01, "turnover": 1.0}
    # candidate doubles turnover but gross gain does not cover 1.5x added cost
    mc = {"gross_return": 0.0112, "turnover": 3.0}
    passed, reason = check_turnover_exploitation(mb, mc, cost_bps=5.0)
    assert not passed and "transaction cost" in reason


def test_regime_cherry_pick_flagged():
    passed, reason = check_regime_cherry_pick(
        {"trend": 0.01, "mean_revert": -0.02, "crash": -0.03, "flat": -0.001})
    assert not passed and "regimes" in reason


def test_regime_diverse_wins_pass():
    passed, _ = check_regime_cherry_pick(
        {"trend": 0.01, "mean_revert": 0.02, "crash": -0.0005, "flat": 0.001})
    assert passed


def test_evaluator_manipulation_contract_drift_flagged():
    contract = _contract()
    mutated = dict(contract, minimum_net_gain=0.0)
    passed, reason = check_evaluator_manipulation(contract_hash(contract), mutated)
    assert not passed


def test_metric_gaming_returns_all_failures():
    contract = _contract()
    bars = fixture_bars(n=30)
    failures = check_metric_gaming(
        bars, contract, {}, {}, expected_contract_hash="tampered",
        mean_cost_bps=5.0)
    assert failures  # at minimum the contract-hash check fires


def test_metric_gaming_clean_passes():
    contract = _contract()
    bars = fixture_bars(n=30)
    mb = {"cvar_95": 0.01, "single_bar_max_loss": 0.01, "exposure_max": 0.01,
          "gross_return": 0.01, "turnover": 1.0}
    mc = dict(mb, gross_return=0.02)
    failures = check_metric_gaming(
        bars, contract, mb, mc,
        expected_contract_hash=contract_hash(contract), mean_cost_bps=5.0)
    assert failures == []
