import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.models import ResearchLedgerEntry, EvidenceGraph, EvidenceNode, EvidenceEdge, RelationType
from trading_bot.core.csc.hypothesis import ReasoningBranch
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

@pytest.fixture
def mock_world_model():
    return MagicMock()

@pytest.fixture
def mock_hms():
    return MagicMock()

@pytest.mark.asyncio
async def test_csc_pipeline_success(mock_world_model, mock_hms):
    # Setup CSC
    csc = CognitiveSystemController(mock_world_model, mock_hms)

    # Mock behavior to pass hard constraint
    # We need at least 5 nodes and 3 edges in the evidence graph
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

@pytest.mark.asyncio
async def test_csc_pipeline_insufficient_evidence(mock_world_model, mock_hms):
    csc = CognitiveSystemController(mock_world_model, mock_hms)

    # Mock behavior with ONLY 1 node (fails hard constraint)
    async def mock_gen_branches_weak(observation):
        branch = ReasoningBranch(branch_id="test", name="Weak Branch")
        branch.evidence_graph.add_node(EvidenceNode(node_id="node_0", content="weak", node_type="EVIDENCE"))
        return [branch]

    csc.hypothesis_gen.generate_competing_branches = mock_gen_branches_weak

    observation = {"price": 1.1}
    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Insufficient evidence" in decision.dominant_rejection_reason

if __name__ == "__main__":
    # This is a bit tricky to run without pytest installed in the environment but we've verified it with minimal scripts
    print("Test file updated with async fixes.")
