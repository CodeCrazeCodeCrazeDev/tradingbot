"""
Comprehensive Unit and Integration Tests for the Quantitative Research Institution (AQRI).
Validates the institutional operating systems, specialized divisions,
the four advanced scientific engines, and the end-to-end 14-step quantitative research lifecycle.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from trading_bot.research.institution import (
    QuantitativeResearchInstitution,
    ResearchOS, KnowledgeOS, ExperimentOS, GovernanceOS, EvolutionOS,
    TradingResearchDivision, PortfolioResearchDivision, MarketMicrostructureDivision,
    RiskScienceDivision, AIResearchDivision, ProductionDeploymentDivision,
    AdversarialCritiqueBoard, SkepticismEngine, ContinuousReplicationPipeline, EvolutionSandbox,
    Theory
)
from trading_bot.research.research_computer import EpistemicInstruction


@pytest.fixture
def institution():
    """Returns an initialized QuantitativeResearchInstitution instance."""
    return QuantitativeResearchInstitution()


@pytest.fixture
def sample_data():
    """Generates a synthetic dataset for testing granger causality and dataset lineage."""
    np.random.seed(42)
    # Generate cointegrated/causal relation: target lags signal
    signal = np.random.randn(150)
    target = np.roll(signal, 1) + np.random.normal(0, 0.1, 150)
    target[0] = 0.0  # clean edge

    df = pd.DataFrame({
        "feature_signal": signal,
        "target_return": target
    })
    return df


def test_aqri_initialization(institution):
    """Verifies that the entire top-level institution initializes cleanly."""
    assert institution is not None
    assert isinstance(institution.ros, ResearchOS)
    assert isinstance(institution.kos, KnowledgeOS)
    assert isinstance(institution.eos, ExperimentOS)
    assert isinstance(institution.gos, GovernanceOS)
    assert isinstance(institution.evos, EvolutionOS)

    # Divisions
    assert isinstance(institution.trading_division, TradingResearchDivision)
    assert isinstance(institution.portfolio_division, PortfolioResearchDivision)
    assert isinstance(institution.microstructure_division, MarketMicrostructureDivision)
    assert isinstance(institution.risk_division, RiskScienceDivision)
    assert isinstance(institution.ai_division, AIResearchDivision)
    assert isinstance(institution.production_division, ProductionDeploymentDivision)


def test_research_os_intent_and_cycle(institution):
    """Tests project creation and instruction trace tracking on ROS."""
    project = institution.ros.register_scientific_intent(
        title="Order Book Microstructure Alpha",
        question_text="Does order book imbalance predict forward 1-minute price shifts?",
        objective="Analyze OBI Spearman correlations."
    )
    assert project is not None
    assert project.title == "Order Book Microstructure Alpha"

    trace = institution.ros.run_cpu_cycle(EpistemicInstruction.QUESTION, project.id)
    assert trace is not None
    assert trace.instruction == EpistemicInstruction.QUESTION
    assert trace.input_object_id == project.id
    assert trace.execution_success is True


def test_knowledge_os_graph_and_beliefs(institution):
    """Tests semantic storage, beliefs tracking, and Research Balance Sheet calculation on KOS."""
    # Find or verify belief
    belief_text = "Momentum is persistent under high volatility regimes"
    b = institution.kos.verify_belief_state(belief_text)
    assert b is not None
    assert b.statement == belief_text
    assert b.status == "Hypothetical"

    # Add finding to semantic graph
    node_id = "f_node_1"
    finding = {"type": "coefficient_correlation", "val": 0.35}
    institution.kos.record_finding(b.id, "verified_by", node_id, finding)

    related = institution.kos.graph.find_relations(b.id, "verified_by")
    assert node_id in related

    # Test Research Balance Sheet
    institution.kos.balance_sheet.validated_theories_count = 3
    institution.kos.balance_sheet.immutably_hashed_datasets_count = 5
    institution.kos.balance_sheet.production_ready_alphas_count = 1

    institution.kos.balance_sheet.unverified_hypotheses_count = 1
    institution.kos.balance_sheet.technical_debt_score = 2.0
    institution.kos.balance_sheet.known_data_quality_issues = 0

    equity = institution.kos.update_firm_knowledge_equity()
    # Assets: 3*1000 + 5*250 + 1*2000 = 6250
    # Liabilities: 1*300 + 2*50 + 0*400 = 400
    # Equity = 5850.0
    assert equity == 5850.0


def test_experiment_os_reproducibility_and_causality(institution, sample_data):
    """Tests reproducible dataset locking and causal tests (Granger, Chow) on EOS."""
    idea_id = "idea_momentum_test"
    params = {"seed": 42, "model_class": "LinearCausalRegressor"}

    experiment = institution.eos.register_reproducible_experiment(
        idea_id=idea_id,
        dataset_name="Synthetic_OBI_M1",
        dataset_df=sample_data,
        parameters=params
    )
    assert experiment is not None
    assert experiment.random_seed == 42
    assert experiment.dataset_name == "Synthetic_OBI_M1"

    # Granger causality test
    causal_dict = institution.eos.test_causal_soundness(
        signal=sample_data["feature_signal"],
        target=sample_data["target_return"]
    )
    assert "granger_f_stat" in causal_dict
    assert "chow_break_f_stat" in causal_dict
    assert causal_dict["granger_f_stat"] >= 0.0


def test_governance_os_compliance_and_review(institution):
    """Tests the Constitutional Layer gating and Peer Review board functionality in GOS."""
    # Constitution violation checks
    passed = institution.gos.check_constitutional_compliance(
        claim_text="Alpha yields premium",
        evidence_ids=["evidence_123"],
        seed=123,
        dataset_hash="hash_abc"
    )
    assert passed is True

    # Check that a claim with NO evidence fails
    failed = institution.gos.check_constitutional_compliance(
        claim_text="Alpha yields premium with zero evidence",
        evidence_ids=[],
        seed=123,
        dataset_hash="hash_abc"
    )
    assert failed is False

    # Review Board testing
    verdict = institution.gos.perform_peer_review_board(
        experiment_id="exp_abc",
        assumptions=["gaussian distribution", "zero latency impact"],
        metrics={"is_sharpe": 2.2, "oos_sharpe": 1.8}
    )
    assert verdict is not None
    assert verdict.methodology_valid is True
    assert verdict.verdict == "APPROVED"


def test_evolution_os_monotone_safety(institution):
    """Tests monotone-safe system self-modifications in EvOS."""
    prop_id = institution.evos.propose_system_evolution(
        subsystem_name="SAGE_Graph_Memory",
        proposed_code="class CompactedSAGE(SAGEGraphMemory): pass",
        rationale="Compacts the memory footprint to resolve Day 10 initialization overheads."
    )
    assert prop_id is not None
    assert prop_id in institution.evos.improvement_candidates

    # Evaluate safety with a regression failure: should fail
    reg_failed = institution.evos.run_monotone_safety_evaluation(
        proposal_id=prop_id,
        regression_results={"improvement_percentage": 12.5, "regression_failures_count": 2.0}
    )
    assert reg_failed is False
    assert institution.evos.improvement_candidates[prop_id]["status"] == "Rejected"

    # Evaluate safety with positive improvement and 0 regression: should succeed
    reg_success = institution.evos.run_monotone_safety_evaluation(
        proposal_id=prop_id,
        regression_results={"improvement_percentage": 5.4, "regression_failures_count": 0.0}
    )
    assert reg_success is True
    assert institution.evos.improvement_candidates[prop_id]["status"] == "Verified_Safe"


def test_scientific_divisions_computations(institution):
    """Validates math-oriented computations across the 6 scientific divisions."""
    # Trading Research
    theory = institution.trading_division.propose_alpha_theory(
        title="Microstructure Drift",
        description="OBI imbalance yields short-term mean-reverting pressures."
    )
    assert theory is not None
    assert theory.explanation == "OBI imbalance yields short-term mean-reverting pressures."

    # Portfolio Division: Fractional Kelly Allocation
    kelly = institution.portfolio_division.compute_kelly_allocation_bounds(
        win_rate=0.55,
        win_loss_ratio=1.2
    )
    # Kelly % = 0.55 - (0.45 / 1.2) = 0.55 - 0.375 = 0.175
    # Fractional Kelly (50% Kelly) = 0.0875
    assert abs(kelly - 0.0875) < 1e-5

    # Market Microstructure OBI
    obi = institution.microstructure_division.compute_order_book_imbalance(
        bid_vol=150.0,
        ask_vol=50.0
    )
    # (150 - 50) / 200 = 0.5
    assert obi == 0.5

    # Risk Science: Credal Bounds
    predictions = [1.2, 1.15, 1.25, 1.21, 1.18]
    mean, lower, upper = institution.risk_division.calculate_prediction_bounds(predictions)
    assert mean == pytest.approx(1.198, abs=1e-3)
    assert lower < mean < upper

    # AI Research Division
    institution.ai_division.challenge_institutional_assumption("Pricing signals are static over multi-year regimes.")
    assert "Pricing signals are static over multi-year regimes." in institution.ai_division.assumptions_audit

    audit = institution.ai_division.run_meta_research_audit()
    assert audit["total_assumptions_audited"] == 1

    # Production Division: Packaged runbooks
    package = institution.production_division.transition_theory_to_packaged_code(
        model_uuid="model_123",
        code_hash="sha256_hash_value"
    )
    assert package is not None
    assert package.model_uuid == "model_123"
    assert package.reversion_rollback_hash == "sha256_hash_value"


def test_adversarial_critique_board(institution):
    """Tests the institutional Red Team board for look-ahead leakage and overfitting attacks."""
    board = AdversarialCritiqueBoard()

    # 1. Attack code containing shift(-1) look-ahead leakage: should fail
    unsafe_code = "signal = df['price'].shift(-1)"
    unsafe_metrics = {"sharpe_ratio": 2.5, "num_bars": 120}
    is_safe, vulnerabilities = board.challenge_model_vigor("exp_001", unsafe_code, unsafe_metrics)
    assert is_safe is False
    assert any("look-ahead" in v.lower() for v in vulnerabilities)

    # 2. Attack code with safe implementation: should succeed
    safe_code = "signal = df['price'].shift(1)"
    safe_metrics = {"sharpe_ratio": 2.1, "num_bars": 150}
    is_safe_2, vulnerabilities_2 = board.challenge_model_vigor("exp_002", safe_code, safe_metrics)
    assert is_safe_2 is True
    assert len(vulnerabilities_2) == 0


def test_skepticism_engine_groupthink(institution):
    """Tests detection of Groupthink/Cognitive Clustering in active firm theories."""
    engine = SkepticismEngine(kos=institution.kos)

    # State with no theories is diversified
    res_empty = engine.audit_cognitive_diversity()
    assert res_empty["status"] == "DIVERSIFIED"

    # Add three clustered momentum theories
    t1 = Theory(explanation="momentum trends in pricing")
    t2 = Theory(explanation="momentum SMA breakouts")
    t3 = Theory(explanation="momentum breakouts with RSI indicators")

    institution.kos.graph.add_node("t1", t1)
    institution.kos.graph.add_node("t2", t2)
    institution.kos.graph.add_node("t3", t3)

    res_clustered = engine.audit_cognitive_diversity()
    assert res_clustered["status"] == "CLUSTERED"
    assert res_clustered["recommendation"] == "FORCE_DIVERSIFICATION"


def test_continuous_replication_pipeline(institution, sample_data):
    """Tests retrospective replication study of older accepted theories."""
    # Seed theory in graph
    t = Theory(explanation="Causal imbalance theory", confidence_score=0.90)
    institution.kos.graph.add_node("theory_c1", t)

    pipeline = ContinuousReplicationPipeline(kos=institution.kos)

    # Replicate theory: should perform replication run and append to audit log
    replicated, replicated_sharpe = pipeline.replicate_theory("theory_c1", sample_data)
    assert replicated in [True, False]
    assert len(pipeline.replication_audit_log) == 1
    assert pipeline.replication_audit_log[0]["theory_id"] == "theory_c1"


def test_evolution_sandbox_ablation():
    """Tests N-Dimensional Ablation studies on self-evolution candidates."""
    sandbox = EvolutionSandbox()
    proposal_id = "ev_prop_lr_resets"
    components = ["lr_scheduler_decay", "adam_optimizer_weight_decay"]

    ablation_matrix = sandbox.execute_ablation_study(proposal_id, components)
    assert "baseline" in ablation_matrix
    assert "full_integration" in ablation_matrix
    assert "only_lr_scheduler_decay" in ablation_matrix

    # Verify attribution history is captured
    history = sandbox.ablation_matrix_history[proposal_id]
    assert len(history["attribution"]) == 2
    assert pytest.approx(sum(history["attribution"].values()), 1e-5) == 1.0


def test_end_to_end_institutional_research_lifecycle(institution, sample_data):
    """Runs a complete 14-step continuous research-and-evolution cycle in the integrated AQRI."""
    result = institution.run_full_research_cycle(
        project_title="Order Book Imbalance Predictive Alpha",
        research_question="Does L2 order book imbalance have causal granger-predictive influence on EURUSD?",
        data_feed=sample_data,
        hypothesis_text="Momentum persists when order book imbalance > 0.4"
    )

    assert result is not None
    assert result["promoted"] is True
    assert result["reproducible"] is True
    assert result["validation"].deflated_sharpe == 2.45
    assert result["package"] is not None
    assert result["package"].model_uuid == result["experiment"].id
    assert result["knowledge_equity"] > 0
