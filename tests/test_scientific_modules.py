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
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import SkillRouter, SkillArtifact, SkillType
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.governance.evolution_gate import EvolutionGate

# Mock dependencies
class MockWorldModel:
    pass

class MockValidationEngine:
    def run_benchmark(self, config):
        return {"reward": config.get("perf", 0.5), "calibration": 0.9, "robustness": 0.8, "latency": 50, "safety_score": 1.0}

@pytest.fixture(autouse=True)
def reset_csc_singleton():
    """Reset the CognitiveSystemController singleton before/after each test."""
    CognitiveSystemController._instance = None
    yield
    CognitiveSystemController._instance = None

@pytest.mark.asyncio
async def test_discoloop_internalization():
    """Verify DiscoLoop dual-channel state updates."""
    csc = CognitiveSystemController(world_model=MockWorldModel())
    obs = {"latent_embedding": {"v": 1.0}, "semantic_tokens": ["initial"]}

    await csc._run_discoloop_reasoning(obs)

    # In DiscoLoop, weTransition and append token_loop_...
    assert len(csc.discrete_channel) > 0
    assert "latent" in csc.continuous_state

@pytest.mark.asyncio
async def test_pivot_refine_logic():
    """Verify Pivot/Refine severity detection and logic."""
    csc = CognitiveSystemController()
    from trading_bot.core.hms.models import VerifierReport

    # In UCA V5, Pivot/Refine loops and checks EvidenceGraphGate.verify_evidence_first.
    # Refinement degrades confidence via a factor of 0.9.
    from trading_bot.core.csc.hypothesis import ReasoningBranch
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)
    reports = [VerifierReport(agent_name="V1", is_valid=False, confidence=0.9, critique="Too high risk")]

    refined = await csc._refine_strategy(branch, reports)
    assert refined.confidence < branch.confidence
    assert "Correction: Too high risk" in refined.reasoning_trace

@pytest.mark.asyncio
async def test_hasp_guardrail_interception():
    """Verify HASP executable program intervention."""
    router = SkillRouter()
    context = {"market": {"volatility": 0.4}} # Exceeds 0.3 threshold

    result = await router.route_task("execution", context)

    assert result.status == "pf_intervention"
    assert result.action == "override_to_hold"

@pytest.mark.asyncio
async def test_s2l_behavioral_routing():
    """Verify S2L adapter routing based on task text."""
    router = SkillRouter()
    context = {"market": {"volatility": 0.1}}

    result = await router.route_task("I need to hedge my EURUSD position", context)

    assert result.status == "s2l_routed"
    assert result.adapter_id == "lora_hedging_v1"

@pytest.mark.asyncio
async def test_eksft_compliance_verification():
    """Verify EKSFT selective masking check in EvolutionGate."""
    gate = EvolutionGate(validation_engine=MockValidationEngine(), improvement_threshold=0.1)

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
    gate = EvolutionGate(validation_engine=MockValidationEngine(), improvement_threshold=0.1)

    baseline = {"perf": 0.5}
    candidate_good = {"perf": 0.65, "training_metadata": {}} # Gain 0.15 > 0.1
    candidate_bad = {"perf": 0.55, "training_metadata": {}}  # Gain 0.05 < 0.1

    assert gate.validate_evolution("C1", candidate_good, baseline) is True
    assert gate.validate_evolution("C2", candidate_bad, baseline) is False
