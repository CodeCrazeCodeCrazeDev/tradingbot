"""
Test suite for AlphaAlgo Cognitive Brain Batch 17 integration.
Validates Active Inference VFE, Hawkes order flow intensity, split conformal prediction bounds,
and SHA-256 decision provenance hashing.
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


def test_cognitive_brain_initialization():
    brain = AlphaAlgoCognitiveBrain()
    assert isinstance(brain.state, CognitiveState)
    assert brain.state.volatility == 0.01


def test_vfe_bounds_calculation():
    brain = AlphaAlgoCognitiveBrain()
    vfe = brain.calculate_vfe_bounds(volatility=0.02, epistemic_uncertainty=0.1)
    assert pytest.approx(vfe, 0.001) == 0.08


def test_hawkes_intensity_calculation():
    brain = AlphaAlgoCognitiveBrain()
    events = [0.1, 0.2, 0.5, 0.6]
    intensity = brain.calculate_hawkes_intensity(events)
    assert intensity > 0.5


def test_conformal_bounds_calculation():
    brain = AlphaAlgoCognitiveBrain()
    lower, upper = brain.calculate_conformal_bounds(price=100.0, volatility=0.01)
    assert lower < 100.0
    assert upper > 100.0


def test_provenance_hash():
    brain = AlphaAlgoCognitiveBrain()
    payload = {"test": "data", "value": 123}
    h = brain.compute_provenance_hash(payload)
    assert len(h) == 64  # SHA-256 hex string


@pytest.mark.asyncio
async def test_process_market_update():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "price": 150.0,
        "volatility": 0.02,
        "epistemic_uncertainty": 0.05,
        "suggested_action": "BUY",
        "confidence": 0.92
    }
    decision = await brain.process_market_update(market_data)
    assert decision["action"] == "BUY"
    assert decision["confidence"] == 0.92
    assert "provenance_hash" in decision
    assert len(decision["provenance_hash"]) == 64
