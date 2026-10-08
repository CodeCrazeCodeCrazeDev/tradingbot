"""
Test suite for AlphaAlgoCognitiveBrain (Batch 14: REG-1301 to REG-1400)
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.fixture
def cognitive_brain():
    return AlphaAlgoCognitiveBrain()


@pytest.mark.asyncio
async def test_cognitive_brain_process_market_update(cognitive_brain):
    market_data = {
        "volatility": 0.02,
        "volume": 250.0,
        "suggested_action": "BUY",
        "confidence": 0.88
    }

    result = await cognitive_brain.process_market_update(market_data)

    assert result["action"] in ["BUY", "ABSTAIN", "HOLD", "SELL"]
    assert "variational_free_energy" in result
    assert "epistemic_uncertainty" in result
    assert "hawkes_intensity" in result
    assert "conformal_bounds" in result
    assert "provenance_hash" in result
    assert len(result["provenance_hash"]) == 64


@pytest.mark.asyncio
async def test_cognitive_brain_free_energy_abstain(cognitive_brain):
    # High volatility triggers high VFE and abstain action
    market_data = {
        "volatility": 0.85,
        "volume": 1000.0,
        "suggested_action": "BUY",
        "confidence": 0.95
    }

    result = await cognitive_brain.process_market_update(market_data)

    assert result["action"] == "ABSTAIN"
    assert result["confidence"] == 0.0
    assert "exceeded safety threshold" in result["reason"]


def test_conformal_interval_calculation(cognitive_brain):
    bounds = cognitive_brain.calculate_conformal_interval(0.80, alpha=0.05)
    assert bounds["coverage_guarantee"] == 0.95
    assert bounds["lower_bound"] <= 0.80
    assert bounds["upper_bound"] >= 0.80


def test_hawkes_intensity_calculation(cognitive_brain):
    intensity = cognitive_brain.calculate_hawkes_intensity(order_volume=500.0, time_delta=0.1)
    assert intensity > 0.5
