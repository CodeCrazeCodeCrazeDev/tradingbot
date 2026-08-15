import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock
from trading_bot.core.csc.controller import CognitiveSystemController

@pytest.mark.asyncio
async def test_csc_discoloop_reasoning():
    world_model = MagicMock()
    # Mock encode with small values so it doesn't trigger pivot on step 0
    world_model.encode.return_value = np.random.randn(512) * 0.1
    world_model.transition.side_effect = lambda h, e: h + np.random.randn(512)*0.01
    hms = MagicMock()
    shield = MagicMock()

    csc = CognitiveSystemController(world_model, hms, shield)
    csc.discrete_channel = []

    observation = {"price": 1.10, "volatility": 0.2}

    await csc._run_discoloop_reasoning(observation, k=3)

    assert len(csc.discrete_channel) == 3
    assert any("token_loop_" in t for t in csc.discrete_channel)
    assert "latent" in csc.continuous_state
    assert len(csc.continuous_state["latent"]) == 512

@pytest.mark.asyncio
async def test_csc_vfe_calculation():
    csc = CognitiveSystemController()
    surprise = csc._calculate_vfe_surprise({"market": "test"})
    assert 0 <= surprise <= 1.0
