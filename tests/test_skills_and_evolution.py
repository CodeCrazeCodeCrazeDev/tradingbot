import pytest
import asyncio
from trading_bot.core.csc.router import SkillRouter, SkillArtifact, SkillType, HASPExecutor
from trading_bot.governance.evolution_gate import EvolutionGate, EvolutionMetrics

@pytest.mark.asyncio
async def test_skill_router_mapping():
    router = SkillRouter()
    # High volatility context
    context = {"market_volatility": 0.4}
    artifact = await router.route_task("execution", context)
    # Should map to risk_averse_hasp in high vol
    assert artifact is None # Since we didn't register it yet

    # Standard context
    context_std = {"market_volatility": 0.1}
    # vwap_hasp_v1 (unregistered)
    assert await router.route_task("execution", context_std) is None

def test_hasp_execution():
    executor = HASPExecutor()
    def mock_program(state): return {"action": "buy", "size": state["size"]}
    artifact = SkillArtifact("test_hasp", SkillType.HASP_PROGRAM, mock_program, {})

    result = executor.execute(artifact, {"size": 0.5})
    assert result["status"] == "success"
    assert result["result"]["action"] == "buy"

def test_evolution_gate_multi_dim():
    class MockBench:
        def run_benchmark(self, config):
            return {"reward": 1.2, "calibration": 0.9, "robustness": 0.8, "latency": 50, "safety_score": 1.0}

    gate = EvolutionGate(MockBench())
    baseline = EvolutionMetrics(reward=1.0, calibration=0.8, robustness=0.7, latency=60, safety_score=1.0)

    # Improved across board
    assert gate.validate_evolution("v2", {}, baseline) is True

    # Regression in safety
    class FailBench:
        def run_benchmark(self, config):
            return {"reward": 2.0, "calibration": 0.9, "robustness": 0.8, "latency": 50, "safety_score": 0.9}

    gate_fail = EvolutionGate(FailBench())
    assert gate_fail.validate_evolution("v3", {}, baseline) is False
