import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

@pytest.mark.asyncio
async def test_csc_12_step_pipeline():
    # Mock dependencies
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    # Mock Shield to approve
    shield_report = MagicMock()
    from trading_bot.core.immutable_shield import GovernanceDecision
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    controller = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    # Mock Hypothesis Gen using AsyncMock
    from trading_bot.core.csc.hypothesis import ReasoningBranch, Hypothesis
    from trading_bot.core.hms.models import EvidenceNode, EvidenceEdge, RelationType
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)
    branch.hypotheses.append(Hypothesis(description="Test Hypothesis"))
    for i in range(6):
        branch.evidence_graph.add_node(EvidenceNode(node_id=f"node_{i}", content="test", node_type="EVIDENCE"))
    for i in range(4):
        branch.evidence_graph.add_edge(EvidenceEdge(source_id="node_0", target_id=f"node_{i+1}", relation=RelationType.SUPPORTS))

    controller.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    controller.hypothesis_gen.simulate_branches = AsyncMock(return_value={"test_b": []})

    # Mock Verifier Swarm
    from trading_bot.core.hms.models import VerifierReport
    report = VerifierReport(agent_name="V1", is_valid=True, confidence=0.9, critique="Looks good")
    controller.verifier_swarm.run_swarm = AsyncMock(return_value=[report])

    observation = {"price_action": "BULLISH", "volatility": 0.01}

    with patch("trading_bot.core.unified_event_bus.decision_bus.propose_action", new_callable=AsyncMock) as mock_propose:
        async def side_effect(act):
            act.status = ActionStatus.EXECUTED
        mock_propose.side_effect = side_effect

        decision = await controller.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert controller.hms.store_ledger_entry.called

@pytest.mark.asyncio
async def test_csc_hasp_guardrail():
    controller = CognitiveSystemController()

    # Observation that triggers volatility guardrail
    observation = {"price_action": "BULLISH", "volatility": 0.5}

    intervention = controller._apply_hasp_guardrails(observation)
    assert intervention.get("status") == "pf_intervention"
    assert intervention.get("result", {}).get("action") == "override_to_hold"

@pytest.mark.asyncio
async def test_csc_pivot_refine():
    controller = CognitiveSystemController()

    from trading_bot.core.csc.hypothesis import ReasoningBranch
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)

    from trading_bot.core.hms.models import VerifierReport
    reports = [VerifierReport(agent_name="V1", is_valid=False, confidence=0.9, critique="Too high risk")]

    refined = await controller._refine_strategy(branch, reports)
    assert refined.confidence < branch.confidence
    assert "Refinement: Too high risk" in refined.reasoning_trace
