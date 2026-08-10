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
        return config

@pytest.fixture(autouse=True)
def reset_router_singleton():
    """Reset SkillRouter singleton before and after each test."""
    SkillRouter._instance = None
    yield
    SkillRouter._instance = None

@pytest.mark.asyncio
async def test_discoloop_internalization():
    """Verify DiscoLoop multi-hop reasoning convergence under VFE minimization."""
    csc = CognitiveSystemController()
    obs = {"latent_embedding": {"v": 1.15}}

    await csc._run_discoloop_internalization(obs, num_loops=3)
    await csc._run_discoloop_reasoning(obs)

    # In DiscoLoop, we Transition and append token_loop_...
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
    context = {"market": {"volatility": 0.5}}

    result = await router.route_task("any_task", context)

    assert result.status == "pf_intervention"
    assert result["pf_result"]["action"] == "override_to_hold"

@pytest.mark.asyncio
async def test_s2l_behavioral_routing():
    """Verify S2L adapter routing based on task text."""
    router = SkillRouter()
    context = {"market": {"volatility": 0.1}}

    result = await router.route_task("I need to hedge my EURUSD position", context)

    assert result.status == "s2l_routed"
    assert result.adapter_id == "lora_hedging_v2"

@pytest.mark.asyncio
async def test_eksft_compliance_verification():
    """Verify EKSFT selective masking check in EvolutionGate."""
    gate = EvolutionGate(validation_engine=MockValidationEngine(), threshold=0.1)

    # 1. Compliant candidate (high entropy token was masked)
    config_ok = {
        "training_metadata": {
            "eksft_trace": [{"id": "T1", "entropy": 0.9, "masked": True}]
        }
    }
    assert gate._check_eksft_compliance(config_ok) is True

    # 2. Non-compliant candidate (high entropy token not masked)
    config_fail = {
        "training_metadata": {
            "eksft_trace": [{"id": "T2", "entropy": 0.9, "masked": False}]
        }
    }
    assert gate._check_eksft_compliance(config_fail) is False

@pytest.mark.asyncio
async def test_rsea_monotone_safe_gate():
    """Verify RSEA only approves improvements > threshold."""
    gate = EvolutionGate(validation_engine=MockValidationEngine(), threshold=0.1)

    baseline = {"reward": 0.5, "calibration": 0.9, "robustness": 0.8, "latency": 10.0, "safety_score": 1.0}
    candidate_good = {"reward": 0.65, "calibration": 0.9, "robustness": 0.8, "latency": 10.0, "safety_score": 1.0, "training_metadata": {}} # Gain 0.15 > 0.1
    candidate_bad = {"reward": 0.55, "calibration": 0.9, "robustness": 0.8, "latency": 10.0, "safety_score": 1.0, "training_metadata": {}}  # Gain 0.05 < 0.1

    assert await gate.validate_evolution("C1", candidate_good, baseline) is True
    assert await gate.validate_evolution("C2", candidate_bad, baseline) is False

@pytest.mark.asyncio
async def test_rsea_multi_metric_protected_gate():
    """Verify multi-metric protected metrics prevents silent regression."""
    class MultiMetricValidationEngine:
        def run_benchmark(self, config):
            return config

    gate = EvolutionGate(validation_engine=MultiMetricValidationEngine(), threshold=0.1)

    baseline = {
        "reward": 0.5,
        "calibration": 0.9,
        "robustness": 0.8,
        "latency": 10.0,
        "safety_score": 1.0
    }

    # 1. Performance improves and no protected metric regresses -> Approve
    candidate_good = {
        "reward": 0.65,
        "calibration": 0.9,
        "robustness": 0.8,
        "latency": 10.0,
        "safety_score": 1.0,
        "training_metadata": {}
    }
    assert await gate.validate_evolution("CG", candidate_good, baseline) is True

    # 2. Performance improves but decision latency regresses significantly -> Reject
    candidate_bad_latency = {
        "reward": 0.65,
        "calibration": 0.9,
        "robustness": 0.8,
        "latency": 15.0, # Regressed (10.0 -> 15.0 > 1.2x tol)
        "safety_score": 1.0,
        "training_metadata": {}
    }
    assert await gate.validate_evolution("CB_Lat", candidate_bad_latency, baseline) is False

    # 3. Performance improves but safety regresses -> Reject
    candidate_bad_safety = {
        "reward": 0.65,
        "calibration": 0.9,
        "robustness": 0.8,
        "latency": 10.0,
        "safety_score": 0.9, # Regressed (< 1.0)
        "training_metadata": {}
    }
    assert await gate.validate_evolution("CB_Safety", candidate_bad_safety, baseline) is False

@pytest.mark.asyncio
async def test_csc_safety_and_self_improvement():
    """Verify execution correctness of the safety checking and self-improvement validation pipeline."""
    csc = CognitiveSystemController()
    obs = {"impact": 0.9, "confidence": 0.8, "cost": 0.1, "target": "execution_optimizer"}

    result = await csc.execute_self_improvement_loop(obs)

    assert result["status"] == "completed"
    assert result["promoted"] is True
    assert result["triage_score"] > 5.0
    assert "observe" in result["trace"]
    assert "archive" in result["trace"]

    # Test dropped triage path
    obs_low = {"impact": 0.1, "confidence": 0.1, "cost": 0.9}
    result_low = await csc.execute_self_improvement_loop(obs_low)
    assert result_low["status"] == "dropped"
