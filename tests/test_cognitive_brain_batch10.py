"""
Test Suite for AlphaAlgoCognitiveBrain Batch 10 Integration (REG-901 to REG-1000)
=================================================================================
Validates conformal prediction bounds, Hawkes order process intensity estimation,
SHA-256 decision provenance hashing, and VFE active inference safety gates.
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.fixture
def cognitive_brain():
    return AlphaAlgoCognitiveBrain()


def test_conformal_bounds_calculation(cognitive_brain):
    alpha_est = 0.002
    alpha_std = 0.0005
    lower, upper = cognitive_brain.calculate_conformal_bounds(alpha_est, alpha_std, coverage_level=0.95)

    assert lower < alpha_est < upper
    assert cognitive_brain.state.conformal_lower_bound == lower
    assert cognitive_brain.state.conformal_upper_bound == upper


def test_hawkes_intensity_estimation(cognitive_brain):
    events = [1.0, 1.1, 1.15, 1.18, 1.20]
    intensity = cognitive_brain.calculate_hawkes_intensity(events)

    assert intensity > 0.5
    assert cognitive_brain.state.hawkes_intensity == intensity


def test_provenance_hash_generation(cognitive_brain):
    market_data = {"volatility": 0.02, "alpha_est": 0.001}
    h1 = cognitive_brain.compute_provenance_hash(market_data, "BUY")
    h2 = cognitive_brain.compute_provenance_hash(market_data, "BUY")
    h3 = cognitive_brain.compute_provenance_hash(market_data, "SELL")

    assert len(h1) == 64
    assert h1 == h2
    assert h1 != h3


@pytest.mark.asyncio
async def test_process_market_update_normal(cognitive_brain):
    market_data = {
        "volatility": 0.01,
        "suggested_action": "BUY",
        "confidence": 0.90,
        "alpha_est": 0.002,
        "alpha_std": 0.0005,
        "order_timestamps": [1.0, 1.2, 1.3]
    }
    result = await cognitive_brain.process_market_update(market_data)

    assert result["action"] == "BUY"
    assert result["confidence"] == 0.90
    assert "provenance_hash" in result
    assert "conformal_bounds" in result
    assert result["hawkes_intensity"] > 0.0


@pytest.mark.asyncio
async def test_process_market_update_vfe_exceeded(cognitive_brain):
    market_data = {
        "volatility": 0.40,  # High volatility triggers VFE > 0.50
        "suggested_action": "BUY",
        "confidence": 0.90
    }
    result = await cognitive_brain.process_market_update(market_data)

    assert result["action"] == "ABSTAIN"
    assert result["confidence"] == 0.0
    assert "Free energy exceeded safety threshold" in result["reason"]


@pytest.mark.asyncio
async def test_process_market_update_conformal_tail_risk(cognitive_brain):
    market_data = {
        "volatility": 0.01,
        "suggested_action": "BUY",
        "confidence": 0.90,
        "alpha_est": -0.02,
        "alpha_std": 0.02  # Lower bound = -0.02 - 1.96 * 0.02 = -0.0592 < -0.05
    }
    result = await cognitive_brain.process_market_update(market_data)

    assert result["action"] == "ABSTAIN"
    assert result["confidence"] == 0.0
    assert "Conformal downside risk bound" in result["reason"]
