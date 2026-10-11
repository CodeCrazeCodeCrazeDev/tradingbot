import pytest
import time
import numpy as np
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.mark.asyncio
async def test_cognitive_brain_active_inference_vfe():
    brain = AlphaAlgoCognitiveBrain()
    obs = {"price": 105.0, "expected_price": 100.0, "volatility": 0.02}
    vfe = brain.calculate_variational_free_energy(obs)
    assert isinstance(vfe, float)
    assert 0.0 <= vfe <= 5.0
    assert brain.state.variational_free_energy == vfe


@pytest.mark.asyncio
async def test_cognitive_brain_hawkes_order_intensity():
    brain = AlphaAlgoCognitiveBrain()
    now = time.time()
    events = [now - 10.0, now - 5.0, now - 1.0]
    intensity = brain.estimate_hawkes_order_intensity(event_timestamps=events)
    assert isinstance(intensity, float)
    assert intensity > 0.05 # Baseline mu = 0.05


@pytest.mark.asyncio
async def test_cognitive_brain_conformal_prediction_bounds():
    brain = AlphaAlgoCognitiveBrain()
    price = 150.0
    residuals = [0.5, 0.8, 1.2, 0.3, 0.9, 1.1, 0.4]
    lower, upper, width = brain.calculate_conformal_prediction_bounds(price, calibration_residuals=residuals)
    assert lower < price < upper
    assert width == upper - lower


@pytest.mark.asyncio
async def test_cognitive_brain_decision_provenance_hash():
    brain = AlphaAlgoCognitiveBrain()
    payload = {"action": "BUY", "confidence": 0.92, "symbol": "BTC/USDT"}
    hash_val = brain.compute_decision_provenance_hash(payload)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 hex string


@pytest.mark.asyncio
async def test_cognitive_brain_process_market_update():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "price": 100.0,
        "volatility": 0.015,
        "suggested_action": "BUY",
        "confidence": 0.88
    }
    res = await brain.process_market_update(market_data)
    assert res["action"] in ("BUY", "ABSTAIN", "HOLD")
    assert "variational_free_energy" in res
    assert "hawkes_intensity" in res
    assert "conformal_bounds" in res
    assert "provenance_hash" in res
    assert len(res["provenance_hash"]) == 64
