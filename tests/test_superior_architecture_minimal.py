import asyncio
from unittest.mock import MagicMock
import logging
import sys
import os

# Minimal mock for dependencies that are causing issues during import
class MockObj:
    def __getattr__(self, name):
        return MockObj()
    def __call__(self, *args, **kwargs):
        return MockObj()

# Mocking modules that are failing due to missing dependencies or complex circular imports
sys.modules['trading_bot.advanced_features.quantum_computing'] = MockObj()
sys.modules['trading_bot.advanced_features'] = MockObj()
sys.modules['trading_bot.elite_system.regime_detection'] = MockObj()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Now try to import our components
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.models import ResearchLedgerEntry, EvidenceGraph, EvidenceNode, EvidenceEdge, RelationType
from trading_bot.core.csc.hypothesis import ReasoningBranch
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

async def test_csc_pipeline_success():
    print("Running test_csc_pipeline_success...")
    mock_world_model = MagicMock()
    mock_hms = MagicMock()

    # We need to mock the ImmutableShield because it's a singleton and might have complex init
    mock_shield = MagicMock()
    mock_report = MagicMock()
    from trading_bot.core.immutable_shield import GovernanceDecision
    mock_report.decision = GovernanceDecision.APPROVED
    mock_shield.validate_action.return_value = mock_report
    mock_shield.GovernanceDecision = GovernanceDecision

    csc = CognitiveSystemController(mock_world_model, mock_hms, shield=mock_shield)

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
    mock_shield = MagicMock()

    csc = CognitiveSystemController(mock_world_model, mock_hms, shield=mock_shield)

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

async def test_deterministic_validation():
    print("Running test_deterministic_validation...")
    # This test verifies that we can take a stored ledger entry and re-run verification
    mock_world_model = MagicMock()
    mock_hms = MagicMock()
    csc = CognitiveSystemController(mock_world_model, mock_hms)

    # Create a dummy entry
    from trading_bot.core.hms.models import ResearchLedgerEntry, EvidenceGraph, EvidenceNode, EvidenceEdge, RelationType
    entry = ResearchLedgerEntry()
    for i in range(6):
        entry.evidence_graph_snapshot.add_node(EvidenceNode(node_id=f"node_{i}", content="test", node_type="EVIDENCE"))
    for i in range(4):
        entry.evidence_graph_snapshot.add_edge(EvidenceEdge(source_id="node_0", target_id=f"node_{i+1}", relation=RelationType.SUPPORTS))

    # Re-run verification swarm
    reports = await csc.verifier_swarm.run_swarm(entry)

    assert len(reports) == 3
    assert all(r.is_valid for r in reports)
    print("test_deterministic_validation PASSED")

async def main():
    await test_csc_pipeline_success()
    await test_csc_pipeline_insufficient_evidence()
    await test_deterministic_validation()
    print("All superior architecture minimal tests PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
