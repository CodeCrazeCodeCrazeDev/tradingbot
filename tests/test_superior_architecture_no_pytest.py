import asyncio
from unittest.mock import MagicMock
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.models import ResearchLedgerEntry, EvidenceGraph, EvidenceNode, EvidenceEdge, RelationType
from trading_bot.core.csc.hypothesis import ReasoningBranch
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

async def test_csc_pipeline_success():
    print("Running test_csc_pipeline_success...")
    mock_world_model = MagicMock()
    mock_hms = MagicMock()

    csc = CognitiveSystemController(mock_world_model, mock_hms)

    async def mock_gen_branches(observation):
        branch = ReasoningBranch(branch_id="test", name="Test Branch")
        for i in range(6):
            branch.evidence_graph.add_node(EvidenceNode(node_id=f"node_{i}", content="test", node_type="EVIDENCE"))
        for i in range(4):
            branch.evidence_graph.add_edge(EvidenceEdge(source_id="node_0", target_id=f"node_{i+1}", relation=RelationType.SUPPORTS))
        return [branch]

    csc.hypothesis_gen.generate_competing_branches = mock_gen_branches

    observation = {"price": 1.1}
    decision = await csc.process_market_observation(observation)

    assert decision is not None
    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert mock_hms.store_ledger_entry.called
    print("test_csc_pipeline_success PASSED")

async def test_csc_pipeline_insufficient_evidence():
    print("Running test_csc_pipeline_insufficient_evidence...")
    mock_world_model = MagicMock()
    mock_hms = MagicMock()

    csc = CognitiveSystemController(mock_world_model, mock_hms)

    async def mock_gen_branches_weak(observation):
        branch = ReasoningBranch(branch_id="test", name="Weak Branch")
        branch.evidence_graph.add_node(EvidenceNode(node_id="node_0", content="weak", node_type="EVIDENCE"))
        return [branch]

    csc.hypothesis_gen.generate_competing_branches = mock_gen_branches_weak

    observation = {"price": 1.1}
    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Insufficient evidence" in decision.dominant_rejection_reason
    print("test_csc_pipeline_insufficient_evidence PASSED")

async def main():
    await test_csc_pipeline_success()
    await test_csc_pipeline_insufficient_evidence()
    print("All superior architecture tests PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
