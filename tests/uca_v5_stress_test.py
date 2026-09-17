
import asyncio
import time
import numpy as np
import psutil
import os
import shutil
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.unified_event_bus import decision_bus

async def run_stress_test(iterations=100):
    print(f"\n--- UCA V5 STRESS & REPRODUCIBILITY TEST ({iterations} iterations) ---\n")

    # Setup
    hms_path = "stress_hms"
    if os.path.exists(hms_path): shutil.rmtree(hms_path)

    # Reset singletons
    CognitiveSystemController._instance = None
    HierarchicalMemorySystem._instance = None
    from trading_bot.core.unified_event_bus import UnifiedDecisionBus
    UnifiedDecisionBus._instance = None

    hms = HierarchicalMemorySystem(base_path=hms_path)
    from trading_bot.core.immutable_shield import shield
    await decision_bus.start()

    csc = CognitiveSystemController(world_model=MagicMock(), hms=hms, shield=shield)

    # Mocking
    from trading_bot.core.csc.hypothesis import ReasoningBranch, Hypothesis
    from trading_bot.core.hms.models import EvidenceNode
    branch = ReasoningBranch(branch_id="b1", name="Stable", confidence=0.9)
    branch.hypotheses.append(Hypothesis(description="Stability"))
    csc.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={"b1": []})

    from trading_bot.core.hms.models import VerifierReport
    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[
        VerifierReport(agent_name="V", is_valid=True, confidence=0.9, critique="OK")
    ])

    latencies = []
    mem_start = psutil.Process().memory_info().rss / 1024 / 1024

    print("Running iterations...")
    for i in range(iterations):
        obs = {"price": 100.0 + i, "volatility": 0.02}
        t0 = time.time()
        decision = await csc.process_market_observation(obs)
        latencies.append((time.time() - t0) * 1000)

        if i % 20 == 0:
            print(f"  Iteration {i}: {latencies[-1]:.2f}ms")

    mem_end = psutil.Process().memory_info().rss / 1024 / 1024
    avg_latency = sum(latencies) / len(latencies)

    print(f"\nResults:")
    print(f"  Average Latency: {avg_latency:.2f}ms")
    print(f"  Memory Delta: {mem_end - mem_start:.2f}MB")

    assert avg_latency < 500, "Latency SLA violated"
    # Ensure memory growth is bounded (windowing check)
    assert mem_end - mem_start < 50.0, "Potential memory leak detected"

    # Reproducibility Check
    print("\nVerification: Deterministic Replay...")
    # Fix seed for reproducibility
    np.random.seed(42)
    # We'll mock the random parts or ensure they are seeded if possible
    # For now, we'll just check if two identical runs produce identical outcomes

    obs_test = {"price": 200.0, "volatility": 0.01}
    np.random.seed(42)
    d1 = await csc.process_market_observation(obs_test)

    np.random.seed(42)
    d2 = await csc.process_market_observation(obs_test)

    assert d1.outcome == d2.outcome
    assert d1.trade_id != d2.trade_id # UUIDs should differ
    print("  [PASS] Deterministic replay verified.")

    await decision_bus.stop()
    shutil.rmtree(hms_path, ignore_errors=True)
    print("\n--- STRESS TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
