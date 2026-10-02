"""
Comprehensive Unit & Integration Test Suite for Batch 9 (REG-801 to REG-900)
=============================================================================
"""

import pytest
import asyncio
from scipy.stats import norm
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.mark.asyncio
async def test_batch9_conformal_bounds_calculation():
    brain = AlphaAlgoCognitiveBrain()
    bounds = brain.calculate_conformal_bounds(volatility=0.02, confidence_level=0.95)
    assert bounds["coverage"] == 0.95
    assert bounds["z_score"] == pytest.approx(norm.ppf(0.975), rel=1e-5)
    assert bounds["lower_bound"] < 0.02
    assert bounds["upper_bound"] > 0.02


@pytest.mark.asyncio
async def test_batch9_epistemic_variance_computation():
    brain = AlphaAlgoCognitiveBrain()
    preds = [0.1, 0.9, 0.5]
    variance = brain.compute_epistemic_variance(preds)
    assert variance > 0.0


@pytest.mark.asyncio
async def test_batch9_provenance_hashing_chain():
    brain = AlphaAlgoCognitiveBrain()
    payload1 = {"data": "test1"}
    hash1 = brain.generate_provenance_hash(payload1)
    assert len(hash1) == 64

    payload2 = {"data": "test2"}
    hash2 = brain.generate_provenance_hash(payload2)
    assert len(hash2) == 64
    assert hash1 != hash2
    assert brain.state.state_provenance_hash == hash2


@pytest.mark.asyncio
async def test_batch9_full_market_update_pipeline():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "volatility": 0.02,
        "suggested_action": "BUY",
        "confidence": 0.95,
        "agent_predictions": [0.85, 0.86, 0.84]
    }

    result = await brain.process_market_update(market_data)
    assert result["action"] == "BUY"
    assert result["batch9_integrated"] is True
    assert "provenance_hash" in result
    assert result["epistemic_uncertainty"] < 0.05

    # High uncertainty trigger abstain
    uncertain_market = {
        "volatility": 0.02,
        "suggested_action": "BUY",
        "confidence": 0.95,
        "agent_predictions": [0.0, 1.0, 0.5]  # High variance
    }
    uncertain_result = await brain.process_market_update(uncertain_market)
    assert uncertain_result["action"] == "ABSTAIN"
    assert uncertain_result["confidence"] == 0.0
