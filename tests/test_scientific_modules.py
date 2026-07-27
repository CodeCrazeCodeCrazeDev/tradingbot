"""
Focused Unit Tests for AlphaAlgo Scientific Modules (UCA V5)
===========================================================
Verifies independent correctness of:
- DiscoLoop (Reasoning Convergence)
- Pivot/Refine (Self-Healing Execution)
- HASP (Executable Guardrails)
- S2L (Behavioral Routing)
- EKSFT (Selective Masking Compliance)
- RSEA (Monotone-Safe Evolution)
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController, ReasoningBranch
from trading_bot.core.csc.router import SkillRouter, SkillArtifact, SkillType
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.governance.evolution_gate import EvolutionGate

# Mock dependencies
class MockWorldModel:
    async def simulate_intervention(self, *args, **kwargs):
        return {"failure_rate": 0.1, "expected_slippage": 0.0, "structural_impact": {}}

class MockValidationEngine:
    def run_benchmark(self, config):
        return {
            "reward": config.get("perf", 0.5),
            "calibration": 0.95,
            "robustness": 0.90,
            "latency": 5.0,
            "safety_score": 1.0
        }

@pytest.fixture
def csc_instance():
    world_model = MockWorldModel()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    skill_router = SkillRouter()
    verifier_swarm = MagicMock()
    risk_engine = MagicMock()
    consensus_engine = MagicMock()
    execution_planner = MagicMock()
    evolution_gate = MagicMock()
    shield = MagicMock()
    from trading_bot.core.immutable_shield import GovernanceDecision
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    return CognitiveSystemController(
        world_model=world_model,
        hms=hms,
        skill_router=skill_router,
        verifier_swarm=verifier_swarm,
        risk_engine=risk_engine,
        consensus_engine=consensus_engine,
        execution_planner=execution_planner,
        evolution_gate=evolution_gate,
        shield=shield
    )

@pytest.mark.asyncio
async def test_discoloop_internalization(csc_instance):
    """Verify DiscoLoop dual-channel state updates."""
    obs = {"volatility": 0.1, "features": [0.1] * 16}

    await csc_instance._run_discoloop_reasoning(obs)

    assert len(csc_instance.discrete_channel) > 0
    assert "latent" in csc_instance.continuous_state

@pytest.mark.asyncio
async def test_pivot_refine_logic(csc_instance):
    """Verify Pivot/Refine severity detection and logic."""
    branch = ReasoningBranch(
        branch_id="branch_bull",
        name="Bull Case",
        confidence=0.85,
        probability=0.35,
        uncertainty=0.15,
        causal_explanation="Expansion supports mean reversion."
    )

    # 1. Low failure rate (no pivot)
    simulations_low = {"branch_bull": {"failure_rate": 0.1}}
    result_low = await csc_instance._pivot_refine_loop([branch], simulations_low)
    assert result_low.branch_id == "branch_bull"

    # 2. High failure rate (trigger pivot)
    simulations_high = {"branch_bull": {"failure_rate": 0.8}}
    result_high = await csc_instance._pivot_refine_loop([branch], simulations_high)
    assert result_high.branch_id == "pivoted_branch_bull"

@pytest.mark.asyncio
async def test_hasp_guardrail_interception():
    """Verify HASP executable program intervention."""
    router = SkillRouter()
    context = {"market": {"volatility": 0.4}} # Exceeds 0.3 threshold

    result = await router.route_task("execution", context)

    assert result["status"] == "pf_intervention"
    assert result["action"] == "override_to_hold"

@pytest.mark.asyncio
async def test_s2l_behavioral_routing():
    """Verify S2L adapter routing based on task text."""
    router = SkillRouter()
    context = {"market": {"volatility": 0.1}}

    result = await router.route_task("I need to hedge my EURUSD position", context)

    assert result["status"] == "s2l_routed"
    assert result["adapter_id"] == "lora_hedging_v2"

@pytest.mark.asyncio
async def test_eksft_compliance_verification():
    """Verify EKSFT selective masking check in EvolutionGate."""
    gate = EvolutionGate(validation_engine=MockValidationEngine())

    # 1. Compliant candidate (high entropy token was masked)
    config_ok = {
        "training_metadata": {
            "eksft_trace": [{"id": "T1", "entropy": 0.9, "masked": True}]
        }
    }
    assert gate._check_eksft_compliance(config_ok) is True

    # 2. Non-compliant candidate (high entropy token NOT masked)
    config_fail = {
        "training_metadata": {
            "eksft_trace": [{"id": "T1", "entropy": 0.9, "masked": False}]
        }
    }
    assert gate._check_eksft_compliance(config_fail) is False

@pytest.mark.asyncio
async def test_rsea_monotone_safe_gate():
    """Verify RSEA only approves improvements > threshold."""
    gate = EvolutionGate(validation_engine=MockValidationEngine(), threshold=0.1)

    baseline_config = {"perf": 0.5}
    candidate_good_config = {"perf": 0.65, "training_metadata": {}} # Gain 0.15 > 0.1
    candidate_bad_config = {"perf": 0.55, "training_metadata": {}}  # Gain 0.05 < 0.1

    assert await gate.validate_evolution("C1", candidate_good_config, baseline_config) is True
    assert await gate.validate_evolution("C2", candidate_bad_config, baseline_config) is False
