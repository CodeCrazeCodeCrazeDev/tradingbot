import asyncio
import time
import logging
import random
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.world_model.causal_model import CausalWorldModel
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus

async def run_stress_test(csc, num_requests=10):
    print(f"Running Stress Test with {num_requests} requests...")
    start_time = time.time()
    results = []
    for i in range(num_requests):
        obs = {"volatility": random.uniform(0, 0.5), "features": [random.random()] * 16}
        results.append(csc.process_market_observation(obs))

    outcomes = await asyncio.gather(*results)
    elapsed = time.time() - start_time
    avg_latency = (elapsed / num_requests) * 1000
    print(f"Stress Test Complete. Avg Latency: {avg_latency:.2f}ms")
    return avg_latency

async def run_chaos_test(csc):
    print("Running Chaos Test (Injecting Faults)...")
    # Fault 1: Missing market data
    obs_missing = {"features": [0.1]*16} # No volatility
    try:
        res = await csc.process_market_observation(obs_missing)
        print("Gracefully handled missing data.")
    except Exception as e:
        print(f"Chaos Failure (Missing Data): {e}")

    # Fault 2: HMS timeout/failure
    original_retrieve = csc.hms.retrieve_evidence_chain
    csc.hms.retrieve_evidence_chain = AsyncMock(side_effect=asyncio.TimeoutError("DB Timeout"))
    res = await csc.process_market_observation({"volatility": 0.1})
    print(f"Gracefully handled HMS failure: {res.outcome}")
    csc.hms.retrieve_evidence_chain = original_retrieve

async def run_ablation_study():
    print("Running Ablation Study...")
    hms = HierarchicalMemorySystem(base_path="alphaalgo_data/test_ablation")
    world_model = CausalWorldModel(hms)
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))
    csc = CognitiveSystemController(world_model, hms, shield)
    await decision_bus.start()

    # 1. Full V6 Architecture
    latency_v6 = await run_stress_test(csc, 5)

    # 2. Ablate DiscoLoop (Set loops to 0)
    csc._max_loops = 0
    print("Ablating DiscoLoop...")
    latency_no_loop = await run_stress_test(csc, 5)

    print(f"Ablation Results: Full V6 Latency={latency_v6:.2f}ms, No-DiscoLoop Latency={latency_no_loop:.2f}ms")
    await decision_bus.stop()

if __name__ == "__main__":
    hms = HierarchicalMemorySystem(base_path="alphaalgo_data/test_stress")
    world_model = CausalWorldModel(hms)
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))
    csc = CognitiveSystemController(world_model, hms, shield)

    async def main():
        await decision_bus.start()
        await run_stress_test(csc)
        await run_chaos_test(csc)
        await run_ablation_study()
        await decision_bus.stop()

    asyncio.run(main())
    print("✅ Stress, Chaos, and Ablation Studies Complete")
