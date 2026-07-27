"""
UCA V5 Scientific Benchmarks & Validation
========================================

Implements validation metrics from the 2026 research package:
- CL-Bench 'Gain Metric' (arXiv:2606.05661)
- HORIZON Failure Attribution (arXiv:2604.11978)
- VFE Minimization Performance (Active Inference)
"""

import pytest
import asyncio
import numpy as np
from typing import Dict, Any, List
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.governance.evolution_gate import EvolutionGate, EvolutionMetrics

class MockValidationEngine:
    def run_benchmark(self, config: Dict[str, Any], mode: str = "stateless") -> Dict[str, Any]:
        # Return mock results for testing the gate logic
        if mode == "stateless":
            return {"reward": 1.0, "safety_score": 1.0, "ece": 0.1, "latency": 10.0, "robustness": 0.8}
        else:
            # Stateful should perform significantly better (Gain > 0.01 + 2*sigma)
            return {
                "reward": 1.2,
                "safety_score": 1.0,
                "ece": 0.08,
                "latency": 12.0,
                "robustness": 0.85,
                "std_dev": 0.001
            }

@pytest.fixture
def mock_csc():
    from trading_bot.core.csc.router import SkillRouter
    from trading_bot.core.hms.memory import HierarchicalMemorySystem
    from trading_bot.core.verification.swarm import VerificationSwarm

    mock = type('Mock', (), {'retrieve_evidence_chain': lambda *a, **k: [], 'propose_action': lambda *a, **k: None})()

    return CognitiveSystemController(
        world_model=mock,
        hms=HierarchicalMemorySystem(base_path="tests/temp_hms_bench"),
        skill_router=SkillRouter(),
        verifier_swarm=VerificationSwarm(),
        risk_engine=mock,
        consensus_engine=mock,
        execution_planner=mock,
        evolution_gate=mock,
        shield=mock
    )

@pytest.mark.asyncio
async def test_cl_bench_gain_metric():
    """
    Validates the CL-Bench 'Gain Metric' logic in the Evolution Gate.
    Gain = Perf(stateful) - Perf(stateless).
    """
    engine = MockValidationEngine()
    gate = EvolutionGate(validation_engine=engine)

    baseline = {"id": "baseline", "mode": "stateless"}
    candidate = {"id": "candidate", "mode": "stateful", "logic_shard": {"halt": False}}

    # Validation is now async in UCA V5
    is_promoted = await gate.validate_evolution("test_v5", candidate, baseline)
    assert is_promoted is True

    # Verify provenance in report
    report = gate.get_evolution_report()[0]
    assert report["provenance"]["signatures"]["governance"] == "APPROVED_UCA_V5"

@pytest.mark.asyncio
async def test_vfe_minimization_loop(mock_csc):
    """
    Validates that the CSC loop correctly calculates and minimizes sensory surprise (VFE).
    """
    csc = mock_csc

    # Scenario 1: Expected observation (Low surprise)
    csc.last_prediction = {"price": 100.0}
    obs_low = {"price": 100.1, "regime": "bull", "volatility": 0.1}
    surprise_low = csc._calculate_sensory_surprise(obs_low)

    # Scenario 2: Unexpected observation (High surprise)
    obs_high = {"price": 110.0, "regime": "bull", "volatility": 0.1}
    surprise_high = csc._calculate_sensory_surprise(obs_high)

    assert surprise_high > surprise_low
    print(f"VFE Surprise - Low: {surprise_low:.4f}, High: {surprise_high:.4f}")

@pytest.mark.asyncio
async def test_hasp_invariant_checking():
    """
    Validates that HASPExecutor enforces state invariants.
    """
    from trading_bot.core.csc.router import HASPExecutor, SkillRouter, SkillArtifact, SkillType

    router = SkillRouter()
    executor = HASPExecutor(router=router)

    def mock_illegal_skill(state):
        return {"status": "success", "illegal_action": "delete_all_logs"}

    router.register_skill(SkillArtifact(
        skill_id="test_illegal",
        skill_type=SkillType.PROGRAM,
        executable=mock_illegal_skill
    ))

    # Should fail post-invariant check due to 'illegal_action' key
    result = await executor.execute("test_illegal", {})
    assert result["status"] == "invariant_fail"
