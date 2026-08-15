"""
Unit tests validating Research Governance, Portfolio Management, and Meta-Learning.
Verifies Strategic Mandates, Portfolio Resource Allocation, Scientific Experiment Designs,
Outcome Decisions, Immutable Audit Trails, and Meta-Learning process analytics.
"""

import pytest
import pandas as pd
import numpy as np

from trading_bot.research.research_governance import (
    StrategicMandate,
    ResearchStrategy,
    ResourceAllocation,
    ResearchPortfolioManager,
    ScienceExperimentDesign,
    ExperimentDesigner,
    DecisionRecord,
    DecisionManager,
    AuditTrace,
    GovernanceAuditTrail,
    MetaLearningEngine,
    AlphaAlgoQuantitativePlatform
)
from trading_bot.research.research_os import ResearchProject, QuantExperiment


def test_research_strategy_and_mandate():
    """Verifies that strategic mandates validate project alignment correctly."""
    mandate = StrategicMandate(
        target_markets=["EURUSD"],
        acceptable_drawdown_limit=5.0,
        core_edge_focus="Microstructure"
    )
    strategy = ResearchStrategy(mandate)

    project = ResearchProject(title="Order Flow Dynamics", objective="Extract OBI alphas.")
    is_aligned, msg = strategy.validate_project_alignment(project)

    assert is_aligned is True
    assert "strategic mandate" in msg


def test_research_portfolio_manager():
    """Verifies resource scheduling across competing quantitative research lines."""
    manager = ResearchPortfolioManager()

    alloc = manager.allocate_resources(
        project_id="proj-obi-2026",
        cores=32,
        dev_days=12.5,
        capital=75000.0
    )

    assert alloc.project_id == "proj-obi-2026"
    assert alloc.compute_cores_allocated == 32
    assert alloc.developer_days_budget == 12.5
    assert alloc.trading_capital_limit_usd == 75000.0
    assert alloc.status == "Active"

    # Verify deallocation suspension
    manager.deallocate_resources("proj-obi-2026")
    assert manager.allocations["proj-obi-2026"].status == "Suspended"


def test_experiment_designer_scientific_method():
    """Verifies scientific Experiment Design enforcement containing null/alt hypotheses."""
    designer = ExperimentDesigner()

    design = designer.create_design(
        null_h="Order Book Imbalance has no predictive correlation with forward 3-hour returns.",
        alt_h="Order Book Imbalance correlates positively with forward 3-hour returns.",
        datasets=["OBI_Stream_Tick_Data"],
        tests=["Granger_Causality", "DSR_Bailey_LopedePrado"],
        target_sharpe=2.5,
        max_drawdown=6.0
    )

    assert design.success_criteria_sharpe == 2.5
    assert design.failure_criteria_drawdown == 6.0
    assert len(design.required_datasets) == 1
    assert "Granger_Causality" in design.statistical_tests


def test_decision_manager_experiment_outcomes():
    """Verifies definitive outcome decisions logging (REJECT, DEPLOY, repeat)."""
    manager = DecisionManager()

    # Record standard deployment decision
    dec = manager.record_decision(
        experiment_id="exp-fvg-99",
        outcome="DEPLOY",
        rationale="Deflated Sharpe is 2.85. Passed Independent review checklist. Highly orthogonal."
    )

    assert dec.experiment_id == "exp-fvg-99"
    assert dec.outcome == "DEPLOY"
    assert "Passed Independent review" in dec.rationale

    # Verifies that invalid decision outcomes are safely rejected
    with pytest.raises(ValueError):
        manager.record_decision("exp-fvg-99", "INVALID_ACTION", "Rationale")


def test_governance_audit_trails():
    """Verifies immutable audit trail logging and rollback tracking."""
    audit = GovernanceAuditTrail()

    trace = audit.commit_audit_trail(
        experiment_id="exp-ob-88",
        approvers=["Independent_Risk_Committee_V5", "Lead_Quant_Officer"],
        gates=["DSR_Bailey_LopedePrado", "OOS_WalkForward_Robustness"],
        risks=["High volatility regime tail risk accepted"],
        rollback_hash="abc998124ef1296ba"
    )

    assert trace.experiment_id == "exp-ob-88"
    assert "Lead_Quant_Officer" in trace.approver_signatures
    assert "OOS_WalkForward_Robustness" in trace.validation_gates_passed
    assert trace.rollback_code_hash == "abc998124ef1296ba"


def test_meta_learning_and_platform_unification():
    """Verifies meta-learning process analytics and 6-layer platform unification."""
    # 1. Instantiate the Master Quantitative Platform (Layer 1 to 6)
    platform = AlphaAlgoQuantitativePlatform()
    assert platform is not None

    # 2. Setup mock decisions and experiment registry metadata to test meta-learning
    workspace = platform.workspace
    decision_manager = platform.decision_manager

    # Register 2 successful experiments
    exp1 = workspace.experiments.register_experiment(
        idea_id="idea-1",
        dataset_name="Microstructure_Features",
        dataset_df=pd.DataFrame({"close": [1, 2]}),
        parameters={"model_class": "XGBoost"},
    )
    decision_manager.record_decision(exp1.id, "DEPLOY", "High Sharpe")

    exp2 = workspace.experiments.register_experiment(
        idea_id="idea-2",
        dataset_name="Microstructure_Features",
        dataset_df=pd.DataFrame({"close": [1, 2]}),
        parameters={"model_class": "XGBoost"},
    )
    decision_manager.record_decision(exp2.id, "MERGE", "Complementary Alpha")

    # Register 1 failed experiment
    exp3 = workspace.experiments.register_experiment(
        idea_id="idea-3",
        dataset_name="Technical_Indicators_Lag",
        dataset_df=pd.DataFrame({"close": [1, 2]}),
        parameters={"model_class": "RandomForest"},
    )
    decision_manager.record_decision(exp3.id, "REJECT", "Fails cost drag")

    # 3. Generate Meta-Learning Insights
    insights = platform.meta_learning.generate_research_meta_insights()

    assert insights["total_research_trials_analyzed"] == 3
    # XGBoost should be recommended since both successful trials utilized it
    assert "XGBoost" in insights["recommended_model_classes"]
    # Microstructure features should be recommended
    assert "Microstructure_Features" in insights["recommended_feature_categories"]
    assert "66.67%" in platform.meta_learning.generate_research_meta_insights()["overall_research_success_rate"]
