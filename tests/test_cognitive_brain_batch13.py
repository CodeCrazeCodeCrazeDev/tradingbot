"""
Unit tests for AlphaAlgo Cognitive Brain (Batch 13: REG-1201 to REG-1300)
========================================================================
Verifies Active Inference VFE calculations, Hawkes process order intensity estimation,
conformal prediction bounds computation, and SHA-256 decision provenance hashing.
"""

import pytest
import pytest_asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.fixture
def brain():
    return AlphaAlgoCognitiveBrain()


def test_calculate_variational_free_energy(brain):
    obs = {"price": 105.0, "volatility": 0.02}
    vfe = brain.calculate_variational_free_energy(obs, prior_mean=100.0, prior_var=1.0)
    assert isinstance(vfe, float)
    assert brain.state.variational_free_energy == vfe


def test_estimate_hawkes_intensity(brain):
    timestamps = [1.0, 1.2, 1.5, 1.8, 2.0]
    intensity = brain.estimate_hawkes_intensity(timestamps, baseline_mu=0.1, alpha=0.5, beta=1.0)
    assert isinstance(intensity, float)
    assert intensity > 0.1
    assert brain.state.hawkes_intensity == intensity


def test_compute_conformal_bounds(brain):
    predictions = [100.0, 101.0, 99.5, 102.0, 98.5]
    lower, upper = brain.compute_conformal_bounds(predictions, alpha_significance=0.05)
    assert isinstance(lower, float)
    assert isinstance(upper, float)
    assert lower < upper
    assert brain.state.conformal_lower_bound == lower
    assert brain.state.conformal_upper_bound == upper


def test_generate_provenance_hash(brain):
    payload = {"action": "BUY", "confidence": 0.92, "symbol": "BTC/USDT"}
    p_hash = brain.generate_provenance_hash(payload)
    assert isinstance(p_hash, str)
    assert len(p_hash) == 64
    assert brain.state.provenance_hash == p_hash


@pytest.mark.asyncio
async def test_process_market_update(brain):
    market_data = {
        "price": 105.0,
        "volatility": 0.02,
        "suggested_action": "BUY",
        "confidence": 0.88,
        "recent_prices": [100.0, 102.0, 104.0, 105.0],
        "timestamps": [1.0, 1.2, 1.5]
    }
    result = await brain.process_market_update(market_data)
    assert isinstance(result, dict)
    assert "action" in result
    assert "provenance_hash" in result
    assert "variational_free_energy" in result
    assert "hawkes_intensity" in result
    assert "conformal_bounds" in result
