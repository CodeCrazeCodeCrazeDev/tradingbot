import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock
from trading_bot.recursive_improvement.recursive_core import (
    RecursiveImprovementCore, ImprovementDimension, ImprovementTier,
    ImprovementProposal, ImprovementCapability
)
from trading_bot.recursive_improvement.orchestrator import RecursiveImprovementOrchestrator
from trading_bot.recursive_improvement.infrastructure import (
    ExperimentManager, EvaluationPipeline, ImprovementMemory, GovernanceController
)
from trading_bot.recursive_improvement.validation import ImprovementValidationPipeline
from trading_bot.recursive_improvement.approvals import ApprovalWorkflow

@pytest.mark.asyncio
async def test_rsie_core_initialization():
    """Test that RSIE Core initializes with the correct registry and settings"""
    core = RecursiveImprovementCore()
    assert core.registry is not None

    # Check default capabilities
    cap = core.registry.get_capability("Trading Strategies")
    assert cap is not None
    assert cap.tier == ImprovementTier.TIER_0
    assert cap.dimension == ImprovementDimension.STRATEGY

@pytest.mark.asyncio
async def test_validation_pipeline_gates():
    """Test the unified validation pipeline gates"""
    pipeline = ImprovementValidationPipeline()

    is_results = {
        'metrics': {'sharpe_ratio': 1.5, 'win_rate': 0.6, 'p_value': 0.01}
    }
    oos_results = {
        'metrics': {'sharpe_ratio': 1.3, 'win_rate': 0.58, 'max_drawdown': 0.1}
    }

    report = await pipeline.validate(is_results, oos_results)
    assert report.passed_all is True
    assert report.gates['statistical_significance'] is True
    assert report.gates['out_of_sample'] is True
    assert report.gates['risk_check'] is True

@pytest.mark.asyncio
async def test_approval_workflow_level_7():
    """Test that Level 7 proposals are correctly routed to PENDING approval"""
    workflow = ApprovalWorkflow(storage_path="test_rsie_data")

    # Mock GovernanceController to avoid torch dependency
    workflow.gov_controller = MagicMock()
    async def mock_check_proposal(*args, **kwargs):
        return (True, [])
    workflow.gov_controller.check_proposal = mock_check_proposal

    proposal = ImprovementProposal(
        proposal_id="test_prop_l7",
        dimension=ImprovementDimension.ARCHITECTURE,
        level=7,
        description="Core architecture change",
        proposed_changes={'refactor': True},
        reasoning="Better scalability",
        expected_benefit={'speed': 0.2},
        risk_analysis={'global': 'high'},
        rollback_plan="None"
    )

    status = await workflow.submit_for_approval(proposal)
    assert status == "PENDING"

    # Check if it was written to file
    approvals = workflow._load_approvals()
    assert "test_prop_l7" in approvals
    assert approvals["test_prop_l7"]["status"] == "PENDING"

@pytest.mark.asyncio
async def test_orchestrator_loop_initialization():
    """Test that Orchestrator initializes with all Tier 0 loops"""
    orchestrator = RecursiveImprovementOrchestrator()
    assert 'evaluation' in orchestrator.loops
    assert 'strategy' in orchestrator.loops
    assert 'risk' in orchestrator.loops
    assert 'feature' in orchestrator.loops
    assert 'meta' in orchestrator.loops

    assert orchestrator.loops['strategy'].dimension == ImprovementDimension.STRATEGY

@pytest.mark.asyncio
async def test_memory_persistence():
    """Test standardized persistence for improvements"""
    memory = ImprovementMemory(storage_path="test_rsie_data")
    proposal = ImprovementProposal(
        proposal_id="test_persist",
        dimension=ImprovementDimension.FEATURE,
        level=1,
        description="Test",
        proposed_changes={},
        reasoning="Test",
        expected_benefit={},
        risk_analysis={},
        rollback_plan="Test"
    )

    await memory.store_proposal(proposal)

    # Manual reload check
    with open("test_rsie_data/proposals.json", 'r') as f:
        import json
        data = json.load(f)
        assert "test_persist" in data
        assert data["test_persist"]["status"] == "PENDING"
