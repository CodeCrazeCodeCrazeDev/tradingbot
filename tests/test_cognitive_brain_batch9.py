"""
Unit test suite verifying Batch 9 Research Principles Integration in AlphaAlgoCognitiveBrain.
"""

import pytest
import asyncio
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain, CognitiveState

@pytest.mark.asyncio
async def test_cognitive_brain_batch9_process_market_update():
    brain = AlphaAlgoCognitiveBrain()

    # Normal market update
    market_data = {
        "volatility": 0.02,
        "suggested_action": "BUY",
        "confidence": 0.90,
        "sentiment": 0.50
    }

    result = await brain.process_market_update(market_data)
    assert result["action"] == "BUY"
    assert result["consensus_weight"] == 1.0
    assert result["confidence"] == 0.90
    assert result["variational_free_energy"] == pytest.approx(0.03)

@pytest.mark.asyncio
async def test_cognitive_brain_batch9_vfe_preemption():
    brain = AlphaAlgoCognitiveBrain()

    # High volatility triggering VFE safety threshold preemption (F-801)
    market_data = {
        "volatility": 0.40,  # VFE = 0.60 > threshold 0.50
        "suggested_action": "BUY",
        "confidence": 0.95
    }

    result = await brain.process_market_update(market_data)
    assert result["action"] == "ABSTAIN"
    assert result["confidence"] == 0.0
    assert "safety threshold" in result["reason"]
