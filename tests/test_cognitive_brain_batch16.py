"""
Tests for Batch 16 Cognitive Brain Capabilities (REG-1501 to REG-1600)
========================================================================
"""

import pytest
import asyncio
import numpy as np
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.mark.asyncio
async def test_batch16_cognitive_brain_process_market_update():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "timestamp": "2026-12-11T12:00:00Z",
        "volatility": 0.02,
        "epistemic_uncertainty": 0.08,
        "suggested_action": "BUY",
        "confidence": 0.88,
        "order_arrivals": [1.0, 1.2, 1.4, 1.5],
        "predicted_return": 0.015,
        "residuals": [0.001, 0.002, -0.001, 0.003]
    }

    res = await brain.process_market_update(market_data)

    assert res["action"] == "BUY"
    assert res["confidence"] == 0.88
    assert res["variational_free_energy"] > 0
    assert "hawkes_intensity" in res
    assert "conformal_bounds" in res
    assert len(res["provenance_hash"]) == 64


def test_batch16_conformal_bounds():
    brain = AlphaAlgoCognitiveBrain()
    lb, ub = brain.compute_conformal_bounds(0.02, [0.001, 0.003, -0.002, 0.004], alpha_significance=0.05)
    assert lb < 0.02
    assert ub > 0.02


def test_batch16_hawkes_intensity():
    brain = AlphaAlgoCognitiveBrain()
    intensity = brain.calculate_hawkes_intensity([1.0, 1.1, 1.15, 1.18])
    assert intensity > 0.1
