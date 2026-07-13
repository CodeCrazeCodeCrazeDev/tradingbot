import pytest
import asyncio
import os
import shutil
import time
from datetime import datetime
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_event_bus import decision_bus, LogAction, ActionStatus, EventPriority
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.immutable_shield import shield, GovernanceDecision
from trading_bot.governance.evolution_gate import EvolutionGate

def reset_singletons():
    CognitiveSystemController._instance = None
    HierarchicalMemorySystem._instance = None

@pytest.mark.asyncio
async def test_uca_v5_pipeline_integration():
    """
    Test the full UCA V5 12-step pipeline with consensus sync.
    """
    reset_singletons()
    if os.path.exists("temp_hms_test"): shutil.rmtree("temp_hms_test")

    hms = HierarchicalMemorySystem(base_path="temp_hms_test")
    csc = CognitiveSystemController(hms=hms, shield=shield)

    await decision_bus.start()

    # Simulate a valid trade that should be approved
    observation = {
        "symbol": "BTCUSD",
        "market": {"volatility": 0.1, "trend": "up"},
        "portfolio": {"drawdown": 0.02}
    }

    decision = await csc.process_market_observation(observation)

    assert decision is not None
    assert decision.outcome.name == "TRADE_APPROVED"

    await decision_bus.stop()
    if os.path.exists("temp_hms_test"): shutil.rmtree("temp_hms_test")

@pytest.mark.asyncio
async def test_logact_timeout_handling():
    """
    Test that the bus handles slow/hanging voters via timeouts.
    """
    reset_singletons()
    await decision_bus.start()

    # Register a hanging voter
    async def hanging_voter(action):
        await asyncio.sleep(10)
        return {"decision": "APPROVED"}

    decision_bus.register_voter("HangingVoter", hanging_voter)
    decision_bus.config["voter_timeout"] = 0.5 # Fast timeout

    action = LogAction(
        action_type="test_timeout",
        payload={"data": "test"},
        agent_id="test_agent"
    )

    await decision_bus.propose_action(action)
    status = await action.wait_for_decision(timeout=2.0)

    assert action.voter_reports["HangingVoter"]["decision"] == "TIMEOUT"

    await decision_bus.stop()

@pytest.mark.asyncio
async def test_csc_memory_windowing():
    """
    Test that CSC channels don't grow indefinitely.
    """
    reset_singletons()
    # Mock HMS and Shield
    hms = HierarchicalMemorySystem(base_path="temp_mem_test")
    csc = CognitiveSystemController(hms=hms, shield=shield)
    csc.max_channel_history = 10

    # Run many observations
    for i in range(20):
        await csc.process_market_observation({"symbol": "TEST"})

    assert len(csc.discrete_channel) <= 10
    assert len(csc.continuous_state) <= 10
    if os.path.exists("temp_mem_test"): shutil.rmtree("temp_mem_test")

@pytest.mark.asyncio
async def test_high_event_rate_concurrency():
    """
    Stress test the LogAct backbone with simultaneous submissions.
    """
    await decision_bus.start()

    num_actions = 20 # Reduced for CI speed
    actions = [
        LogAction(action_type="stress_test", payload={"i": i}, agent_id="stress_agent", priority=EventPriority.NORMAL)
        for i in range(num_actions)
    ]

    # Propose all simultaneously
    await asyncio.gather(*[decision_bus.propose_action(a) for a in actions])

    # Wait for all to complete
    results = await asyncio.gather(*[a.wait_for_decision(timeout=10.0) for a in actions])

    assert all(r == ActionStatus.EXECUTED for r in results)

    await decision_bus.stop()

if __name__ == "__main__":
    import shutil
    for d in ["temp_hms_test", "temp_sage_test", "temp_mem_test"]:
        if os.path.exists(d): shutil.rmtree(d)

    import sys
    pytest.main([__file__, "-v", "-c", "/dev/null"])
