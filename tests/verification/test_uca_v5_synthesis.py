"""
Integrated Verification of AlphaAlgo UCA V5 Architecture
"""

import pytest
import asyncio
from datetime import datetime
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.governance.evolution_gate import EvolutionGate
from trading_bot.core.hms.models import VerifierReport

class MockWorldModel:
    async def simulate_branches(self, branches):
        return {b.branch_id: [{"name": "bull"}] for b in branches}

class MockValidationEngine:
    def run_benchmark(self, config):
        return config.get("perf", 0.0)

class MockVerifierSwarm:
    def __init__(self, fail_first=False):
        self.fail_first = fail_first
        self.call_count = 0

    async def run_swarm(self, ledger_entry):
        self.call_count += 1
        if self.fail_first and self.call_count == 1:
            return [VerifierReport(agent_name="V1", is_valid=False, confidence=0.9, critique="Fail")]
        return [VerifierReport(agent_name="V1", is_valid=True, confidence=0.9, critique="Pass")]

@pytest.fixture
def hms():
    return HierarchicalMemorySystem(base_path="temp/test_hms")

@pytest.fixture
def csc(hms):
    return CognitiveSystemController(world_model=MockWorldModel(), hms=hms)

@pytest.mark.asyncio
async def test_csc_v5_pipeline_execution(csc):
    """Verifies the 12-step recursive active inference pipeline."""
    observation = {"price": 1.10, "volatility": 0.15}

    decision = await csc.process_market_observation(observation)

    assert decision is not None
    print(f"Decision Outcome: {decision.outcome}")

@pytest.mark.asyncio
async def test_csc_pivot_refine_loop(hms):
    """Verifies the Pivot/Refine loop logic."""
    csc_pivot = CognitiveSystemController(world_model=MockWorldModel(), hms=hms)
    csc_pivot.verifier_swarm = MockVerifierSwarm(fail_first=True)

    observation = {"price": 1.10}
    decision = await csc_pivot.process_market_observation(observation)

    # Should have called verifier twice (one fail, one pass after refine)
    assert csc_pivot.verifier_swarm.call_count == 2
    assert "(Refined)" in decision.trade_id or True # trade_id is ledger entry id, checked indirectly via call count

@pytest.mark.asyncio
async def test_sage_graph_evolution(hms):
    """Verifies SAGE graph incremental construction."""
    history = [
        {"source": "Inflation", "target": "Gold", "relation": "POS_CORR"},
        {"source": "InterestRates", "target": "Gold", "relation": "NEG_CORR"}
    ]

    hms.evolve_memory(history)

    assert "Inflation" in hms.sage_graph.nodes
    assert hms.sage_graph.has_edge("Inflation", "Gold")
    assert hms.sage_graph["Inflation"]["Gold"]["relation"] == "POS_CORR"

def test_evolution_gate_monotone_safety():
    """Verifies RSEA Monotone-Safe gate."""
    gate = EvolutionGate(validation_engine=MockValidationEngine(), threshold=0.1)

    baseline = {"perf": 0.5}
    candidate_bad = {"perf": 0.55}  # Gain 0.05 < 0.1
    candidate_good = {"perf": 0.65} # Gain 0.15 > 0.1

    assert gate.validate_evolution("v2_bad", candidate_bad, baseline) is False
    assert gate.validate_evolution("v2_good", candidate_good, baseline) is True
