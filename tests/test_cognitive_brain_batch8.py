"""
Tests for AlphaAlgoCognitiveBrain (Batch 8 / UCA 2026 V7).
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState


@pytest.mark.asyncio
async def test_cognitive_brain_batch8_normal_operation():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "volatility": 0.01,
        "order_imbalance": 0.05,
        "spread": 0.0001,
        "suggested_action": "BUY_LIMIT",
        "confidence": 0.90
    }
    result = await brain.process_market_update(market_data)
    assert result["action"] == "BUY_LIMIT"
    assert result["confidence"] > 0.80
    assert result["counterfactual_rollout_score"] > 0.80
    assert result["hawkes_intensity"] > 0.0


@pytest.mark.asyncio
async def test_cognitive_brain_batch8_abstain_on_high_vfe():
    brain = AlphaAlgoCognitiveBrain()
    market_data = {
        "volatility": 0.40,
        "order_imbalance": 0.50,
        "spread": 0.0050,
        "suggested_action": "BUY_LIMIT",
        "confidence": 0.90
    }
    result = await brain.process_market_update(market_data)
    assert result["action"] == "ABSTAIN"
    assert "safety threshold" in result["reason"] or "falsification" in result["reason"]
