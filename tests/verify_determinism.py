
import asyncio
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_event_bus import decision_bus
from unittest.mock import MagicMock
import logging

async def run_trajectory():
    from trading_bot.core.governance.determinism import determinism
    determinism.reset()
    determinism.enable(seed=42)

    world_model = MagicMock()
    hms = MagicMock()
    shield = MagicMock()

    # Ensure a fresh CSC
    await CognitiveSystemController.reset()
    csc = CognitiveSystemController(world_model, hms, shield)

    # Mock hypothesis generation and simulation with fixed results for determinism
    async def mock_branches(obs):
        branch = MagicMock(branch_id='b1')
        branch.hypotheses = [MagicMock(description='test hypothesis')]
        branch.reasoning_trace = []
        branch.evidence_graph = MagicMock()
        return [branch]
    csc.hypothesis_gen.generate_competing_branches = mock_branches

    async def mock_sim(branches): return {'b1': [MagicMock(name='scenario1')]}
    csc.hypothesis_gen.simulate_branches = mock_sim

    # Standard voter
    async def mock_voter(action):
        return {"decision": "APPROVED", "reason": "System Test"}

    decision_bus.reset()
    decision_bus.register_voter("GovernanceShield", mock_voter)
    await decision_bus.start()

    obs = {'price': 1.1234, 'volatility': 0.1}
    decision = await csc.process_market_observation(obs)

    await decision_bus.stop()
    return decision.outcome, decision.trade_id

async def test_determinism():
    print("Running trajectory 1...")
    res1 = await run_trajectory()
    print(f"Trajectory 1 result: {res1}")

    print("Running trajectory 2...")
    res2 = await run_trajectory()
    print(f"Trajectory 2 result: {res2}")

    assert res1 == res2
    print("Determinism verified: Both trajectories produced identical decisions.")

if __name__ == '__main__':
    asyncio.run(test_determinism())
