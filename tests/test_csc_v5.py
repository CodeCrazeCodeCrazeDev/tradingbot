
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
    decision = await controller.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert controller.hms.store_ledger_entry.called

@pytest.mark.asyncio
async def test_csc_hasp_guardrail():
    controller = CognitiveSystemController()

    # Observation that triggers volatility guardrail
    observation = {"price_action": "BULLISH", "volatility": 0.1}

    intervention = controller._apply_hasp_guardrails(observation)
    assert intervention.get("max_leverage") == 1.0
    assert intervention.get("reasoning_context") == "CRITICAL_VOLATILITY"

@pytest.mark.asyncio
async def test_csc_pivot_refine():
    controller = CognitiveSystemController()

    from trading_bot.core.csc.hypothesis import ReasoningBranch
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)

    from trading_bot.core.hms.models import VerifierReport
    reports = [VerifierReport(agent_name="V1", is_valid=False, confidence=0.9, critique="Too high risk")]

    refined = await controller._refine_strategy(branch, reports)
    assert refined.confidence < branch.confidence
    assert "Correction: Too high risk" in refined.reasoning_trace

if __name__ == "__main__":
    import sys
    # Manual run since pytest might fail due to env
    async def run_tests():
        print("Running CSC V5 Pipeline Test...")
        await test_csc_12_step_pipeline()
        print("CSC V5 Pipeline Test PASSED")

        print("Running CSC HASP Guardrail Test...")
        await test_csc_hasp_guardrail()
        print("CSC HASP Guardrail Test PASSED")

        print("Running CSC Pivot/Refine Test...")
        await test_csc_pivot_refine()
        print("CSC Pivot/Refine Test PASSED")

    asyncio.run(run_tests())
