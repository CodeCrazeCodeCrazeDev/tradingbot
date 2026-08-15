import asyncio
import numpy as np
import networkx as nx
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem, SAGEGraphMemory
from trading_bot.governance.evolution_gate import EvolutionGate

async def test_scientific_correctness():
    print("Starting Scientific Correctness Verification...")

    # 1. Verify SAGE Graph Consistency
    print("\n[1/3] Verifying SAGE Graph Consistency...")
    sage = SAGEGraphMemory()
    sage.add_evidence(("A", "CAUSES", "B"), {"regime": "bull"}, {"confidence": 0.9})
    sage.add_evidence(("B", "CORRELATES", "C"), {"regime": "bull"}, {"confidence": 0.8})

    # Repeated updates/evolution
    feedback = [{"action": "STRENGTHEN", "source": "A", "target": "B"}]
    sage.evolve(feedback)

    assert sage.graph.has_edge("A", "B")
    assert sage.graph.has_edge("B", "C")
    assert nx.is_weakly_connected(sage.graph)
    print("✅ SAGE Consistency Verified.")

    # 2. Verify Evolution Gate Monotonicity
    print("\n[2/3] Verifying Evolution Gate Monotonicity...")
    class MockValidation:
        def run_benchmark(self, config):
            return {"score": config.get("val", 0.0), "ece": 0.1}

    gate = EvolutionGate(MockValidation(), threshold=0.1)

    # Case: Improvement > threshold
    assert gate.validate_evolution("c1", {"val": 0.8}, {"val": 0.6}) == True
    # Case: Improvement < threshold
    assert gate.validate_evolution("c2", {"val": 0.65}, {"val": 0.6}) == False
    print("✅ Evolution Gate Monotonicity Verified.")

    # 3. Verify Active Inference (VFE) Logic
    print("\n[3/3] Verifying Active Inference Logic...")
    # Mocking components for CSC
    class MockWorldModel: pass
    hms = HierarchicalMemorySystem("temp_hms")
    csc = CognitiveSystemController(MockWorldModel(), hms)

    # Run observation processing
    obs = {"symbol": "EURUSD", "volatility": 0.02, "equity_history": [100, 102, 98]}
    decision = await csc.process_market_observation(obs)

    assert len(csc.discrete_channel) > 0
    assert len(csc.continuous_state) > 0
    print("✅ Active Inference/DiscoLoop reasoning hooks verified.")

if __name__ == "__main__":
    asyncio.run(test_scientific_correctness())
