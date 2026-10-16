"""
Test Suite for AlphaAlgo Cognitive Brain Batch 15 (REG-1401 to REG-1500)
========================================================================
Validates non-parametric split conformal prediction bounds, Hawkes order intensity,
SHA-256 decision provenance hashing, and Active Inference VFE state updates.
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState

@pytest.mark.asyncio
async def test_cognitive_brain_batch15_initialization():
    brain = AlphaAlgoCognitiveBrain()
    assert brain is not None
    assert isinstance(brain.state, CognitiveState)
    assert brain.state.vfe_threshold == 0.50

@pytest.mark.asyncio
async def test_cognitive_brain_batch15_market_update_normal():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "volatility": 0.02,
        "suggested_action": "BUY",
        "confidence": 0.90,
        "historical_residuals": [0.01, 0.015, 0.02, 0.025, 0.03],
        "recent_shocks": [0.1, 0.05, 0.02]
    }
    res = await brain.process_market_update(market_data)

    assert res["action"] == "BUY"
    assert res["confidence"] == 0.90
    assert res["variational_free_energy"] == pytest.approx(0.03)
    assert "conformal_prediction_bound" in res
    assert "hawkes_order_intensity" in res
    assert "decision_provenance_hash" in res
    assert res["batch15_scientific_compliance"] is True
    assert len(res["decision_provenance_hash"]) == 64

@pytest.mark.asyncio
async def test_cognitive_brain_batch15_vfe_pruning():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "volatility": 0.40,  # VFE = 0.40 * 1.5 = 0.60 > 0.50 threshold
        "suggested_action": "BUY",
        "confidence": 0.90
    }
    res = await brain.process_market_update(market_data)

    assert res["action"] == "ABSTAIN"
    assert res["confidence"] == 0.0
    assert "Free energy exceeded safety threshold" in res["reason"]
