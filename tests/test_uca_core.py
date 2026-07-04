import pytest
import asyncio
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.world_model.causal.gwm import GenerativeWorldModel
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.governance.immutable_shield import GovernanceGate

@pytest.mark.asyncio
async def test_uca_brain_initialization():
    config = {"latent_dim": 256, "max_exposure": 0.05}
    hms = HierarchicalMemorySystem(config)
    world_model = GenerativeWorldModel(config)
    governance = GovernanceGate(config)

    csc = CognitiveSystemController(config, world_model, hms, governance)
    await csc.initialize()

    assert csc.running is True
    assert csc.state.epistemic_uncertainty == 1.0

@pytest.mark.asyncio
async def test_csc_execution_cycle():
    config = {"latent_dim": 256, "max_exposure": 0.05}
    hms = HierarchicalMemorySystem(config)
    world_model = GenerativeWorldModel(config)
    governance = GovernanceGate(config)

    csc = CognitiveSystemController(config, world_model, hms, governance)
    await csc.initialize()

    task = "Test strategic task"
    context = {"symbol": "BTCUSD", "price": 60000}

    result = await csc.execute_task(task, context)

    assert result["status"] == "completed"
    assert len(csc.state.folded_history) > 0
    # Epistemic uncertainty should have decreased after observation
    assert csc.state.epistemic_uncertainty < 1.0
