"""
Tests for AlphaAlgo Cognitive Brain (Batch 16 Integration - REG-1501 to REG-1600)
=================================================================================
Verifies active inference VFE bounds, conformal prediction bounds,
Hawkes order intensity estimation, and SHA-256 decision provenance hashing.
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState

@pytest.fixture
def cognitive_brain():
    return AlphaAlgoCognitiveBrain()

def test_cognitive_brain_initialization(cognitive_brain):
    assert cognitive_brain.state.volatility == 0.01
    assert cognitive_brain.state.vfe_threshold == 0.50
    assert cognitive_brain.state.epistemic_uncertainty == 0.05

def test_conformal_bounds_calculation(cognitive_brain):
    lower, upper = cognitive_brain.calculate_conformal_bounds(alpha=0.05)
    assert lower < upper
    assert lower > 0.0

def test_hawkes_intensity_estimation(cognitive_brain):
    arrival_times = [1.0, 1.5, 1.8, 2.0]
    intensity = cognitive_brain.calculate_hawkes_intensity(arrival_times)
    assert intensity > 0.10

def test_decision_provenance_hashing(cognitive_brain):
    payload = {"action": "BUY", "confidence": 0.92, "reason": "Bullish momentum"}
    prov_hash = cognitive_brain.generate_decision_provenance_hash(payload)
    assert len(prov_hash) == 64
    assert cognitive_brain.state.provenance_hash == prov_hash

@pytest.mark.asyncio
async def test_process_market_update_normal(cognitive_brain):
    market_data = {
        "volatility": 0.02,
        "suggested_action": "BUY",
        "confidence": 0.88,
        "arrival_times": [1.0, 2.0, 2.2, 2.5]
    }
    res = await cognitive_brain.process_market_update(market_data)
    assert res["action"] == "BUY"
    assert res["confidence"] == 0.88
    assert "provenance_hash" in res
    assert "conformal_lower_bound" in res
    assert "hawkes_intensity" in res

@pytest.mark.asyncio
async def test_process_market_update_vfe_exceeded(cognitive_brain):
    market_data = {
        "volatility": 0.40,
        "suggested_action": "BUY",
        "confidence": 0.95
    }
    res = await cognitive_brain.process_market_update(market_data)
    assert res["action"] == "ABSTAIN"
    assert res["confidence"] == 0.0
    assert "safety threshold" in res["reason"]
