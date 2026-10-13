import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState

@pytest.mark.asyncio
async def test_cognitive_brain_batch18_integration():
    brain = AlphaAlgoCognitiveBrain()

    market_data = {
        "price": 105.0,
        "volatility": 0.02,
        "epistemic_variance": 0.01,
        "suggested_action": "BUY",
        "confidence": 0.90
    }

    res = await brain.process_market_update(market_data)

    assert res["action"] == "BUY"
    assert res["confidence"] == 0.90
    assert "variational_free_energy" in res
    assert "hawkes_intensity" in res
    assert "conformal_bounds" in res
    assert "provenance_hash" in res

    lower, upper = res["conformal_bounds"]
    assert lower < 105.0 < upper
    assert len(res["provenance_hash"]) == 64  # SHA-256 length

@pytest.mark.asyncio
async def test_cognitive_brain_vfe_safety_abstain():
    brain = AlphaAlgoCognitiveBrain()

    high_risk_data = {
        "price": 100.0,
        "volatility": 0.50,  # Spikes VFE above threshold 0.50
        "epistemic_variance": 0.20,
        "suggested_action": "BUY",
        "confidence": 0.95
    }

    res = await brain.process_market_update(high_risk_data)

    assert res["action"] == "ABSTAIN"
    assert res["confidence"] == 0.0
    assert "Free energy exceeded safety threshold" in res["reason"]
