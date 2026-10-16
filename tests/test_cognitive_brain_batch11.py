"""
Tests for Batch 11 Cognitive Brain Integration (REG-1001 to REG-1100)
====================================================================
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


def test_cognitive_brain_batch11_initialization():
    brain = AlphaAlgoCognitiveBrain()
    assert brain.state.regime == "NEUTRAL"
    assert brain.state.volatility == 0.01


def test_conformal_bounds_computation():
    brain = AlphaAlgoCognitiveBrain()
    bounds = brain.compute_conformal_bounds(price=100.0, volatility=0.02)
    assert "lower_bound" in bounds
    assert "upper_bound" in bounds
    assert bounds["lower_bound"] < 100.0 < bounds["upper_bound"]


def test_hawkes_intensity_computation():
    brain = AlphaAlgoCognitiveBrain()
    events = [
        {"delta_t": 0.5, "volume": 2.0},
        {"delta_t": 1.0, "volume": 1.5},
    ]
    intensity = brain.compute_hawkes_intensity(events)
    assert intensity > 0.1


def test_provenance_hash():
    brain = AlphaAlgoCognitiveBrain()
    data = {"action": "BUY", "symbol": "BTC/USDT", "price": 50000.0}
    h1 = brain.compute_provenance_hash(data)
    h2 = brain.compute_provenance_hash(data)
    assert h1 == h2
    assert len(h1) == 64


@pytest.mark.asyncio
async def test_process_market_update():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "price": 100.0,
        "volatility": 0.01,
        "suggested_action": "BUY",
        "confidence": 0.9,
        "order_events": [{"delta_t": 0.1, "volume": 5.0}],
    }
    result = await brain.process_market_update(market_data)
    assert result["action"] == "BUY"
    assert "provenance_hash" in result
    assert "hawkes_intensity" in result
    assert "conformal_bounds" in result
