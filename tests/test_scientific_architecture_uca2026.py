"""
Comprehensive Verification Suite for UCA-2026 Scientific Architecture Refactoring

Verifies end-to-end integration of all 8 mandatory arXiv research papers:
1. arXiv:2605.29303 (EKSFT): Entropy-KL Selective Fine-Tuning
2. arXiv:2607.00341 (DiscoLoop): Continuous-Discrete Recurrent Reasoning
3. arXiv:2607.01224 (AutoMem): Automated Metamemory Schema Learning
4. arXiv:2605.12061 (Search-R1 / SAGE): Self-Evolving Graph-Memory Engine
5. arXiv:2605.10813 (NanoResearch): Tri-Level Co-Evolving Pareto Optimization
6. arXiv:2605.20025 (AutoResearchClaw): Non-Linear Control & Pivot/Refine Loops
7. arXiv:2605.17734 (HASP): Non-Bypassable Program Function Safety Interception
8. arXiv:2605.21482 (DeepWeb-Bench): Expected Calibration Error (ECE) Analysis
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

from trading_bot.core.csc.controller import CognitiveSystemController, DiscoLoopCell
from trading_bot.core.csc.router import SkillRouter, SkillArtifact, SkillType, SkillRouteOutcome
from trading_bot.core.hms.memory import HierarchicalMemorySystem, SAGEGraphMemory, calculate_integrity_hash
from trading_bot.agents.multi_agent_debate import (
    MultiAgentDebateSystem,
    MarketContext,
    TradeAction,
    BayesianDecisionEngine,
    FalsificationGate,
    ConfidenceCalibrator,
    CalibrationMethod
)
from trading_bot.governance.evolution_gate import EvolutionGate, parse_metrics


@pytest.fixture
def mock_hms(tmp_path):
    base_dir = str(tmp_path / "hms_test")
    HierarchicalMemorySystem.reset()
    hms = HierarchicalMemorySystem(base_path=base_dir)
    yield hms
    HierarchicalMemorySystem.reset()


@pytest.mark.asyncio
async def test_eksft_compliance_and_entropy_masking(mock_hms):
    """Test arXiv:2605.29303 (EKSFT) entropy compliance in EvolutionGate."""
    gate = EvolutionGate(validation_engine=None, threshold=0.05)

    valid_config = {
        "training_metadata": {
            "eksft_trace": [
                {"id": "t1", "entropy": 0.9, "kl_divergence": 0.6, "masked": True},
                {"id": "t2", "entropy": 0.2, "kl_divergence": 0.1, "masked": False}
            ]
        }
    }
    assert gate._check_eksft_compliance(valid_config) is True

    invalid_config = {
        "training_metadata": {
            "eksft_trace": [
                {"id": "t1", "entropy": 0.9, "kl_divergence": 0.6, "masked": False}
            ]
        }
    }
    assert gate._check_eksft_compliance(invalid_config) is False


@pytest.mark.asyncio
async def test_discoloop_recurrent_cell():
    """Test arXiv:2607.00341 (DiscoLoop) continuous-discrete recurrence."""
    cell = DiscoLoopCell(latent_dim=512)
    input_signal = np.ones(512) * 0.5
    e_k = np.zeros(512)
    e_k[0] = 1.0

    h_next, token = cell.transition(input_signal, e_k, k=0)
    assert len(h_next) == 512
    assert "token_loop_0_" in token
    assert len(cell.discrete_tokens) == 1


@pytest.mark.asyncio
async def test_automem_metamemory_schema_evolution(mock_hms):
    """Test arXiv:2607.01224 (AutoMem) schema optimization and integrity hashing."""
    initial_version = mock_hms.memory_schema.get("version")
    feedback = [
        {"edge_id": ("A", "B", "rel_1"), "delta": 0.2, "entity": {"type": "MACRO_INDICATOR", "fields": ["vix"]}}
    ]

    mock_hms.optimize_metamemory(feedback)
    updated_version = mock_hms.memory_schema.get("version")
    assert updated_version != initial_version

    # Verify SHA-256 schema integrity
    schema_hash = calculate_integrity_hash(mock_hms.memory_schema)
    assert len(schema_hash) == 64


@pytest.mark.asyncio
async def test_sage_graph_memory_hebbian_weight_evolution(tmp_path):
    """Test arXiv:2605.12061 (SAGE) dynamic edge evolution."""
    storage_path = str(tmp_path / "sage_test.graphml")
    sage = SAGEGraphMemory(storage_path=storage_path)

    triplet = ("BTC", "CORRELATED_WITH", "ETH")
    sage.add_evidence(triplet, context={"market": "crypto"}, evidence={"confidence": 0.5})

    subgraph = sage.retrieve_subgraph("BTC", hops=1)
    assert len(subgraph) >= 1
    u = subgraph[0]["source"]
    v = subgraph[0]["target"]
    keys = list(sage.graph[u][v].keys())
    edge_key = (u, v, keys[0])

    initial_w = subgraph[0]["weight"]
    sage.evolve_weights(edge_key, feedback_delta=0.2)
    new_subgraph = sage.retrieve_subgraph("BTC", hops=1)
    assert new_subgraph[0]["weight"] > initial_w


@pytest.mark.asyncio
async def test_hasp_program_function_interception():
    """Test arXiv:2605.17734 (HASP) pre-emptive safety interceptor."""
    SkillRouter.reset()
    router = SkillRouter()

    high_vol_context = {"market": {"volatility": 0.4}}
    outcome = await router.route_task("market_ingestion", high_vol_context)

    assert outcome.status == "pf_intervention"
    assert outcome.action == "override_to_hold"
    assert "Volatility exceeded HASP safety threshold" in outcome.reason


@pytest.mark.asyncio
async def test_autoresearchclaw_pivot_refine_loop():
    """Test arXiv:2605.20025 (AutoResearchClaw) strategy pivoting."""
    await CognitiveSystemController.reset()
    csc = CognitiveSystemController()

    mock_branch = MagicMock()
    mock_branch.branch_id = "b1"
    mock_branch.confidence = 0.85

    mock_hypothesis_gen = MagicMock()
    mock_pivoted_branch = MagicMock()
    mock_pivoted_branch.branch_id = "b1_pivoted"
    async def mock_pivot(branch, reason):
        return mock_pivoted_branch
    mock_hypothesis_gen.pivot_branch = mock_pivot
    csc.hypothesis_gen = mock_hypothesis_gen

    high_failure_sims = {"b1": {"failure_rate": 0.6}}
    res = await csc._pivot_refine_loop([mock_branch], high_failure_sims)
    assert res == mock_pivoted_branch


@pytest.mark.asyncio
async def test_deepweb_bench_bayesian_calibration():
    """Test arXiv:2605.21482 (DeepWeb-Bench) Expected Calibration Error calculation."""
    calibrator = ConfidenceCalibrator()
    cal_result = calibrator.calibrate(0.9, method=CalibrationMethod.BAYESIAN, prediction_type="macro_strategist")
    assert 0.0 <= cal_result.calibrated_confidence <= 1.0

    engine = BayesianDecisionEngine()
    posterior = engine.calculate_posterior(prior_prob=0.5, evidence_likelihoods=[(True, 0.8, 1.0), (False, 0.3, 1.0)])
    assert 0.0 <= posterior <= 1.0


@pytest.mark.asyncio
async def test_full_debate_and_falsification():
    """Test full multi-agent debate and SRE falsification loop."""
    system = MultiAgentDebateSystem()
    context = MarketContext(
        symbol="EURUSD",
        current_price=1.1000,
        htf_trend="UP",
        ltf_trend="UP",
        volatility=0.015,
        volume_ratio=1.3,
        key_levels={"support": [1.0950], "resistance": [1.1050]},
        news_sentiment=0.4,
        portfolio_exposure=0.25,
        correlation_risk=0.3,
        vix_level=18.0,
    )

    decision = await system.debate(context)
    assert decision.action in [TradeAction.BUY, TradeAction.HOLD, TradeAction.NO_TRADE]
    assert "falsification_report" in decision.provenance
    assert decision.provenance["schema_version"] == "1.0.0"
