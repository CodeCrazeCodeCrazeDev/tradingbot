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
