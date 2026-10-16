"""
Tests for AlphaAlgoCognitiveBrain (Batch 6: REG-501..600).
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.mark.asyncio
async def test_cognitive_brain_initialization():
    brain = AlphaAlgoCognitiveBrain()
    assert brain.state.regime == "NEUTRAL"
    assert brain.state.vfe_threshold == 0.50


@pytest.mark.asyncio
async def test_hawkes_intensity_calculation():
    brain = AlphaAlgoCognitiveBrain()
    intensity1 = brain.calculate_hawkes_intensity(1.0)
    assert intensity1 >= 0.10

    intensity2 = brain.calculate_hawkes_intensity(1.1)
    assert intensity2 > intensity1


@pytest.mark.asyncio
async def test_conformal_bounds_computation():
    brain = AlphaAlgoCognitiveBrain()
    lower, upper = brain.compute_conformal_bounds(100.0)
    assert lower < 100.0
    assert upper > 100.0


@pytest.mark.asyncio
async def test_process_market_update_normal():
    brain = AlphaAlgoCognitiveBrain()
    res = await brain.process_market_update({
        "volatility": 0.02,
        "price": 100.0,
        "timestamp": 1.0,
        "suggested_action": "BUY",
        "confidence": 0.90
    })

    assert res["action"] == "BUY"
    assert res["confidence"] == 0.90
    assert "hawkes_intensity" in res
    assert "conformal_bounds" in res


@pytest.mark.asyncio
async def test_process_market_update_vfe_pruning():
    brain = AlphaAlgoCognitiveBrain()
    res = await brain.process_market_update({
        "volatility": 0.40,  # VFE = 0.60 > threshold 0.50
        "price": 100.0,
        "timestamp": 1.0,
        "suggested_action": "BUY"
    })

    assert res["action"] == "ABSTAIN"
    assert res["confidence"] == 0.0
    assert "exceeded threshold" in res["reason"]
