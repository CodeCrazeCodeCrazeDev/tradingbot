import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus

@pytest.mark.asyncio
async def test_csc_hasp_intervention():
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))
    from trading_bot.core.csc.router import SkillRouter
    skill_router = SkillRouter()
    verifier_swarm = MagicMock()
    risk_engine = MagicMock()
    consensus_engine = MagicMock()
    execution_planner = MagicMock()
    evolution_gate = MagicMock()

    csc = CognitiveSystemController(
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

    # Observation triggering volatility guardrail (volatility > 0.3)
    obs = {"volatility": 0.5, "features": [0.1] * 16}

    decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Volatility exceeded HASP safety threshold" in decision.dominant_rejection_reason

@pytest.mark.asyncio
async def test_csc_pivot_loop():
    # Ensure bus is started
    from trading_bot.core.unified_event_bus import decision_bus
    await decision_bus.start()

    # Setup mocks
    world_model = MagicMock()
    world_model.simulate_intervention = AsyncMock(return_value={"failure_rate": 0.1, "expected_slippage": 0.0, "structural_impact": {}})
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))
    from trading_bot.core.csc.router import SkillRouter
    skill_router = SkillRouter()
    verifier_swarm = MagicMock()
    risk_engine = MagicMock()
    consensus_engine = MagicMock()
    execution_planner = MagicMock()
    evolution_gate = MagicMock()

    csc = CognitiveSystemController(
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

    obs = {"volatility": 0.1, "features": [0.1] * 16}

    # Mock simulation to trigger pivot
    # In V6, pivot is triggered by high failure rate in simulation
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={
        "branch_bull": {"failure_rate": 0.8},
        "branch_bear": {"failure_rate": 0.1},
        "branch_range": {"failure_rate": 0.2}
    })

    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[MagicMock(is_valid=True, confidence=0.9)])

    decision = await csc.process_market_observation(obs)
    await decision_bus.stop()

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED

@pytest.mark.asyncio
async def test_reasoning_branch_variants():
    """Verify that every ReasoningBranch variant is constructed correctly and holds valid fields."""
    from trading_bot.core.csc.hypothesis import HypothesisGenerator

    # Mock world model
    world_model = MagicMock()
    generator = HypothesisGenerator(world_model)

    # Generate branches
    market_data = {"volatility": 0.1, "features": [0.1] * 16}
    branches = await generator.generate_competing_branches(market_data)

    assert len(branches) == 3

    # Verify each branch holds valid fields
    for branch in branches:
        assert branch.branch_id in ["branch_bull", "branch_bear", "branch_range"]
        assert branch.name in ["Bull Case", "Bear Case", "Range Case"]
        assert 0.0 <= branch.probability <= 1.0
        assert 0.0 <= branch.uncertainty <= 1.0
        assert 0.0 <= branch.confidence <= 1.0
        assert len(branch.causal_explanation) > 0
        assert len(branch.hypotheses) > 0
        assert len(branch.evidence_graph.nodes) >= 5
        assert len(branch.evidence_graph.edges) >= 3
