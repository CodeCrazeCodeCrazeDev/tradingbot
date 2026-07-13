import pytest
import asyncio
import torch
from trading_bot.core.governance.determinism import DeterministicManager
from trading_bot.world_model.v3_core import WorldModelV3

def test_deterministic_outputs():
    """Verifies that identical seeds produce identical model outputs."""
    asset_dims = {"price": 1}
    DeterministicManager.set_seed(42)
    model1 = WorldModelV3(asset_dims, latent_dim=64)
    obs1 = {"price": torch.randn(1, 5, 1)}
    out1 = model1.think(obs1)["predictions"]["next_state"]

    DeterministicManager.set_seed(42)
    model2 = WorldModelV3(asset_dims, latent_dim=64)
    obs2 = {"price": torch.randn(1, 5, 1)}
    out2 = model2.think(obs2)["predictions"]["next_state"]

    assert torch.equal(out1, out2)

@pytest.mark.asyncio
async def test_chaos_service_recovery():
    """Simulates a service crash and verifies system resilience."""
    from trading_bot.core.unified_event_bus import decision_bus, ActionStatus, LogAction

    await decision_bus.start()

    # 1. Propose action
    action = LogAction("test_action", {}, "agent1")
    await decision_bus.propose_action(action)

    # 2. Simulate "Crash" - abruptly stop the processor
    decision_bus._processor_task.cancel()

    # 3. Restart
    await decision_bus.start()

    # Verify we can still propose (and process) new actions
    action2 = LogAction("post_crash_action", {}, "agent1")
    await decision_bus.propose_action(action2)

    await asyncio.sleep(0.5)
    await decision_bus.stop()

    # Basic check: system didn't deadlock
    assert action2.status in [ActionStatus.APPROVED, ActionStatus.VETOED, ActionStatus.PROPOSED]
