"""Tests for Counterfactual Simulator and World Model."""

import time
import pytest
from trading_bot.cognition.state import MarketState
from trading_bot.cognition.simulation import (
    SimulationRequest,
    CounterfactualSimulator,
)


def test_counterfactual_simulator_trend_aligned():
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="BULLISH",
        trend_strength=0.8,
        uncertainty=0.15
    )

    req = SimulationRequest(
        request_id="sim_001",
        current_state=state,
        proposed_action="BUY",
        position_size=1.0,
        time_horizon_bars=5,
        scenario_adjustments={"volatility_multiplier": 1.0, "spread_expansion": 1.0}
    )

    sim = CounterfactualSimulator()
    res = sim.simulate(req)

    assert res.request_id == "sim_001"
    assert res.proposed_action == "BUY"
    assert res.win_probability > 0.50
    assert len(res.trajectories) == 5
    assert res.expected_value > 0.0


def test_counterfactual_simulator_high_volatility_scenario():
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="BEARISH",
        trend_strength=0.8,
        uncertainty=0.20
    )

    req = SimulationRequest(
        request_id="sim_002",
        current_state=state,
        proposed_action="BUY",  # Opposed to trend in high volatility
        position_size=1.0,
        time_horizon_bars=5,
        scenario_adjustments={"volatility_multiplier": 2.5, "spread_expansion": 2.0}
    )

    sim = CounterfactualSimulator()
    res = sim.simulate(req)

    assert res.win_probability < 0.40
    assert len(res.invalidation_triggers) > 0

def test_feature_priors_make_ev_discriminate():
    # no_discrimination regression: EV used to be a pure function of
    # trend alignment, so candidates in different market states got
    # identical scores and nothing was rankable. feature_priors must
    # move EV monotonically with the signed feature evidence.
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="NEUTRAL",
        trend_strength=0.0,
        uncertainty=0.2)

    def _ev(feats=None):
        scen = {"feature_priors": feats} if feats else {}
        return CounterfactualSimulator().simulate(SimulationRequest(
            request_id="fd_1", current_state=state,
            proposed_action="BUY", position_size=1.0,
            scenario_adjustments=scen))

    base = _ev()
    favorable = _ev({
        "momentum_x_action": {"value": 1.0, "weight": 0.25},
        "rsi_fade": {"value": 1.0, "weight": 0.2}})
    adverse = _ev({
        "momentum_x_action": {"value": -1.0, "weight": 0.25},
        "rsi_fade": {"value": -1.0, "weight": 0.2}})

    assert favorable.expected_value > base.expected_value \
        > adverse.expected_value
    assert favorable.feature_contributions == \
        {"momentum_x_action": 0.25, "rsi_fade": 0.2}
    assert favorable.feature_drift_source == "assumed"
    assert base.feature_drift_source == "none"


def test_measured_alignment_prior_flips_drift_sign():
    # The injectable prior exists so measured regime evidence (lag-1
    # return autocorrelation) can invert the trend-continuation
    # assumption — negative autocorr markets made aligned trades
    # net-negative in measurement.
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="BULLISH",
        trend_strength=0.8,
        uncertainty=0.2)

    def _ev(prior):
        return CounterfactualSimulator().simulate(SimulationRequest(
            request_id="ap_1", current_state=state,
            proposed_action="BUY", position_size=1.0,
            scenario_adjustments={"alignment_prior": prior}))

    assert _ev(1.0).expected_value > 0.0 > _ev(-1.0).expected_value
    assert _ev(1.0).alignment_prior_source == "measured"
    assert CounterfactualSimulator().simulate(SimulationRequest(
        request_id="ap_2", current_state=state, proposed_action="BUY",
        position_size=1.0)).alignment_prior_source == "assumed"

