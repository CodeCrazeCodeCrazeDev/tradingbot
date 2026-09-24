"""Phase-4 hardening tests: calibration, drift detection, fat-tailed MC."""

import numpy as np
import pytest

from trading_bot.cognition.learning.calibration import ProbabilityCalibrator
from trading_bot.cognition.perception.drift import PageHinkley, DriftMonitor
from trading_bot.cognition.simulation import CounterfactualSimulator, SimulationRequest
from trading_bot.cognition.state.contracts import MarketState


def _state(trend="BULLISH", pct=0.5):
    return MarketState(
        timestamp=0.0, instrument="EURUSD", primary_timeframe="M15",
        trend_direction=trend, volatility_percentile=pct, uncertainty=0.1,
    )


def _req(rid="r1", paths=0):
    return SimulationRequest(
        request_id=rid, current_state=_state(), proposed_action="BUY",
        position_size=1.0, time_horizon_bars=5, monte_carlo_paths=paths,
    )


# ---------- calibration ----------

def test_calibrator_is_identity_without_data():
    cal = ProbabilityCalibrator()
    assert cal.predict(0.7) == 0.7


def test_platt_moves_toward_outcomes():
    cal = ProbabilityCalibrator()
    # overconfident predictor: always claims 0.9 but only 60% right
    for i in range(15):
        cal.update(0.9, 1.0 if i % 5 < 3 else 0.0)
    assert cal.predict(0.9) < 0.9  # pulled down toward ~0.6


def test_isotonic_engages_with_enough_samples():
    cal = ProbabilityCalibrator()
    rng = np.random.default_rng(0)
    # dense samples at fixed levels; high end is systematically overconfident
    for p, true_p in [(0.2, 0.2), (0.5, 0.5), (0.9, 0.6)]:
        for _ in range(40):
            cal.update(p, float(rng.random() < true_p))
    assert cal.sample_count == 120
    assert cal.predict(0.9) < 0.9  # isotonic pulls the inflated estimate down


def test_ece_is_bounded():
    cal = ProbabilityCalibrator()
    rng = np.random.default_rng(1)
    for _ in range(100):
        p = float(rng.random())
        cal.update(p, float(rng.random() < p))
    ece = cal.expected_calibration_error()
    assert 0.0 <= ece <= 1.0


# ---------- drift detection ----------

def test_page_hinkley_detects_regime_shift():
    ph = PageHinkley(delta=0.0005, threshold=0.05, min_observations=20)
    rng = np.random.default_rng(42)
    fired = False
    for i in range(60):
        x = rng.normal(0, 0.001) if i < 30 else rng.normal(0.01, 0.001)
        fired = fired or ph.update(x)
    assert fired


def test_page_hinkley_quiet_on_stationary():
    ph = PageHinkley(delta=0.0005, threshold=0.5, min_observations=10)
    rng = np.random.default_rng(7)
    for _ in range(200):
        assert not ph.update(rng.normal(0, 0.001))


def test_drift_monitor_per_instrument():
    dm = DriftMonitor(delta=0.0005, threshold=0.05, min_observations=20)
    rng = np.random.default_rng(3)
    fired = False
    for i in range(60):
        x = rng.normal(0, 0.001) if i < 30 else rng.normal(0.01, 0.001)
        fired = fired or dm.update("EURUSD", x)
        dm.update("GBPUSD", rng.normal(0, 0.001))
    assert fired
    assert dm.is_drifting("EURUSD")
    assert not dm.is_drifting("GBPUSD")


# ---------- fat-tailed Monte Carlo ----------

def test_mc_is_deterministic_per_request_id():
    sim = CounterfactualSimulator()
    a = sim.simulate(_req("same", paths=200))
    b = sim.simulate(_req("same", paths=200))
    assert a.mc_win_probability == b.mc_win_probability
    assert a.mc_p95_drawdown == b.mc_p95_drawdown


def test_mc_reports_empiricals():
    sim = CounterfactualSimulator()
    res = sim.simulate(_req("mc", paths=256))
    assert res.mc_paths == 256
    assert 0.0 <= res.mc_win_probability <= 1.0
    assert res.mc_p95_drawdown >= 0.0


def test_mc_disabled_by_default():
    sim = CounterfactualSimulator()
    res = sim.simulate(_req("plain", paths=0))
    assert res.mc_paths == 0
    assert res.mc_win_probability is None


# ---------- walk-forward evaluation ----------

def test_walk_forward_smoke():
    import pandas as pd
    from trading_bot.evaluation.walk_forward import WalkForwardEvaluator

    rng = np.random.default_rng(5)
    n = 80
    close = 1.08 + np.cumsum(rng.normal(0, 0.0008, n))
    high = close + rng.uniform(0.0002, 0.001, n)
    low = close - rng.uniform(0.0002, 0.001, n)
    open_ = np.clip(close + rng.normal(0, 0.0003, n), low, high)  # valid OHLCV
    df = pd.DataFrame({
        "timestamp": np.arange(n),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": rng.uniform(800, 1500, n),
    })
    ev = WalkForwardEvaluator(horizon_bars=3)
    rep = ev._run_split(df, "EURUSD", "SMOKE", feed_calibration=True)
    assert rep.cycles == n
    assert 0.0 <= rep.abstain_rate <= 1.0
    assert 0.0 <= rep.ece_raw <= 1.0 and 0.0 <= rep.ece_calibrated <= 1.0
    assert rep.trades == len(rep.records)
    for rec in rep.records:
        assert rec.exit > 0 and isinstance(rec.correct, bool)
