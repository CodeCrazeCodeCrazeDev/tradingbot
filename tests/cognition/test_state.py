"""Tests for State Estimation and Multi-Timescale Cognition."""

import time
import pytest
from trading_bot.cognition.perception import Observation, DataQualityStatus
from trading_bot.cognition.state import MarketState, StateEstimator


def test_state_estimator_bullish_trend():
    estimator = StateEstimator()
    now = time.time()

    obs_m15 = Observation(
        timestamp=now,
        instrument="EURUSD",
        timeframe="M15",
        source="mt5",
        ohlcv={"open": 1.0800, "high": 1.0850, "low": 1.0790, "close": 1.0840, "volume": 1000.0}
    )
    obs_h1 = Observation(
        timestamp=now,
        instrument="EURUSD",
        timeframe="H1",
        source="mt5",
        ohlcv={"open": 1.0780, "high": 1.0860, "low": 1.0770, "close": 1.0850, "volume": 5000.0}
    )

    state = estimator.estimate_state("EURUSD", {"M15": obs_m15, "H1": obs_h1}, current_time=now)

    assert state.instrument == "EURUSD"
    assert state.trend_direction == "BULLISH"
    assert state.trend_strength > 0.5
    assert state.regime_distribution["trending"] > state.regime_distribution["ranging"]
    assert state.get_dominant_regime() == "trending"
    assert "M15" in state.timescale_structure
    assert "H1" in state.timescale_structure


def test_state_estimator_ranging_neutral():
    estimator = StateEstimator()
    now = time.time()

    obs_m15 = Observation(
        timestamp=now,
        instrument="EURUSD",
        timeframe="M15",
        source="mt5",
        ohlcv={"open": 1.0800, "high": 1.0810, "low": 1.0790, "close": 1.0801, "volume": 1000.0}
    )

    state = estimator.estimate_state("EURUSD", {"M15": obs_m15}, current_time=now)

    assert state.trend_direction == "NEUTRAL"
    assert state.regime_distribution["ranging"] >= state.regime_distribution["trending"]
