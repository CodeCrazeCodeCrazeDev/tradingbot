"""
Tests for AlphaAlgo Cognitive Brain (Batch 12 Integration: REG-1101 to REG-1200)
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.mark.asyncio
async def test_cognitive_brain_batch12_initialization():
    brain = AlphaAlgoCognitiveBrain()
    assert brain is not None
    assert isinstance(brain.state, CognitiveState)
    assert brain.state.regime == "NEUTRAL"


@pytest.mark.asyncio
async def test_cognitive_brain_batch12_process_market_update():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "timestamp": 1700000000,
        "volatility": 0.02,
        "confidence": 0.90,
        "suggested_action": "BUY",
        "order_events": [10.0, 10.2, 10.5, 10.8]
    }

    result = await brain.process_market_update(market_data)

    assert result["action"] == "BUY"
    assert result["confidence"] == 0.90
    assert result["variational_free_energy"] == 0.03
    assert "hawkes_intensity" in result
    assert "conformal_upper_bound" in result
    assert "decision_provenance_hash" in result
    assert len(result["decision_provenance_hash"]) == 64


@pytest.mark.asyncio
async def test_cognitive_brain_batch12_vfe_pruning():
    brain = AlphaAlgoCognitiveBrain()
    high_volatility_market_data = {
        "timestamp": 1700000000,
        "volatility": 0.40,  # VFE = 0.60 > threshold 0.50
        "confidence": 0.95,
        "suggested_action": "BUY"
    }

    result = await brain.process_market_update(high_volatility_market_data)

    assert result["action"] == "ABSTAIN"
    assert result["confidence"] == 0.0
    assert "Free energy exceeded safety threshold" in result["reason"]


def test_hawkes_intensity_calculation():
    brain = AlphaAlgoCognitiveBrain()
    events = [1.0, 1.2, 1.5, 1.8]
    intensity = brain.calculate_hawkes_intensity(events)
    assert isinstance(intensity, float)
    assert intensity > 0.1


def test_conformal_risk_bound():
    brain = AlphaAlgoCognitiveBrain()
    bound = brain.calculate_conformal_risk_bound(confidence=0.90)
    assert isinstance(bound, float)
    assert round(bound, 4) == round(0.10 * 1.05, 4)
