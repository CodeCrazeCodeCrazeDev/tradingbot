import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.csc.router import SkillRouter
from trading_bot.agents.planner_agent import PlannerAgent
from trading_bot.governance.evolution_gate import EvolutionGate

@pytest.mark.asyncio
async def test_csc_v4_recursive_loop():
    """Verify that CSC V4 implements recursive reasoning and folding."""
    world_model = MagicMock()
    hms = MagicMock()
    csc = CognitiveSystemController(world_model, hms)

    observation = {"symbol": "EURUSD", "price": 1.0850}

    # Mock hypothesis generation
    branch = MagicMock()
    branch.branch_id = "test_branch"
    branch.reasoning_trace = [{"type": "step", "content": "thinking"}]
    branch.hypotheses = [MagicMock()]
    branch.evidence_graph = MagicMock()
    branch.evidence_graph.nodes = [1,2,3,4,5,6] # Pass density check
    branch.evidence_graph.edges = [1,2,3,4]
    branch.confidence = 0.8

    csc.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={"test_branch": [MagicMock()]})

    # Mock verifier reports
    report = MagicMock()
    report.is_valid = True
    report.confidence = 0.9
    report.detected_hallucinations = []
    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[report])

    decision = await csc.process_market_observation(observation)

    # Check if DiscoLoop and HIPIF logic were triggered
    assert len(csc.discrete_channel) > 0
    assert decision is not None

@pytest.mark.asyncio
async def test_hms_v4_actions():
    """Verify HMS V4 first-class memory actions (AutoMem)."""
    hms = HierarchicalMemorySystem()

    result = await hms.execute_memory_action("agent_007", "write", {"entity": "USD", "relation": "weakening"})
    assert result["status"] == "graph_updated"

    opt_result = await hms.execute_memory_action("agent_007", "optimize", {})
    assert opt_result["status"] == "optimized"

@pytest.mark.asyncio
async def test_skill_router_hasp_intervention():
    """Verify HASP Skill Program interventions."""
    router = SkillRouter()

    # High volatility should trigger PF
    context = {'market': {'volatility': 0.4}}
    result = await router.route_task("planner", "propose_trade", context)

    assert result["status"] == "pf_intervention"
    assert result["action"] == "override_to_hold"

@pytest.mark.asyncio
async def test_evolution_gate_v4_drift():
    """Verify EvolutionGate V4 drift and gain metrics."""
    gate = EvolutionGate(gain_threshold=0.1)

    metrics = {"sharpe_ratio": 1.5}
    baseline = {"sharpe_ratio": 1.3} # Gain = 0.2 > 0.1

    # Test 1: Good gain, good drift
    drift_good = {"kl_divergence": 0.1, "entropy": 0.8}
    assert await gate.validate_improvement("cand_1", metrics, baseline, drift_good) is True

    # Test 2: Good gain, bad drift (mode collapse)
    drift_bad = {"kl_divergence": 0.1, "entropy": 0.1}
    assert await gate.validate_improvement("cand_2", metrics, baseline, drift_bad) is False

    # Test 3: Good gain, excessive KL drift
    drift_kl = {"kl_divergence": 0.6, "entropy": 0.8}
    assert await gate.validate_improvement("cand_3", metrics, baseline, drift_kl) is False
