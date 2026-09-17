"""
Rigorous platform tests validating the Quantitative Research Platform (QRP) Workspace.
Verifies Research Project setup, Feature Set bindings, Statistical Validation logging,
Independent Peer Review integration, Promotion Gate constraints, and Knowledge entries.
"""

import pytest
import pandas as pd
import numpy as np

from trading_bot.research.research_os import (
    ResearchWorkspace,
    ResearchProject,
    ResearchQuestion,
    FeatureSet,
    ValidationReport,
    Deployment,
    KnowledgeEntry,
    ReviewVerdict
)


@pytest.fixture
def clean_platform_df():
    """Generates clean simple DataFrame representing platform dataset version."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-07-01", periods=10, freq="h"),
        "close": np.linspace(1.1000, 1.1050, 10),
        "volume": [1000] * 10
    })


def test_qrp_workspace_complete_lifecycle(clean_platform_df):
    """
    Validates a complete institutional quant platform lifecycle:
    Project -> Question -> Hypothesis -> Dataset Version -> Feature Set -> Experiment -> Validation -> Review -> Promotion.
    """
    workspace = ResearchWorkspace(target_sharpe=2.0, max_drawdown=8.0)

    # 1. Create Research Project
    project = workspace.create_project(
        title="Microstructure Alpha Search 2026",
        objective="Extract short-term predictive alpha signals from FX liquidity imbalance."
    )
    assert project.title == "Microstructure Alpha Search 2026"
    assert project.status == "Active"

    # 2. Formulate Research Question
    question = workspace.formulate_question(
        project_id=project.id,
        question="Does order book imbalance predict direction on EURUSD?",
        foundation="Asymmetric information flow leads to temporary liquidity depletion."
    )
    assert question.project_id == project.id
    assert "EURUSD" in question.question_text

    # 3. Formulate Hypothesis
    hyp = workspace.record_hypothesis(
        question_id=question.id,
        name="EURUSD OBI Directional Predictive Power",
        description="High positive OBI yields positive 3-hour mean forward returns.",
        rationale="Informed market maker execution pressure.",
        counterparty="Impatient retail market-order execution.",
        falsifications=["Fails under top 1% macro news volatilities"]
    )
    assert hyp.name == "EURUSD OBI Directional Predictive Power"

    # 4. Ingest and Version Dataset
    dataset_node = workspace.lineage.register_version(
        source_name="Raw_OBI_Feed",
        parent_ids=[],
        transformation="None",
        df=clean_platform_df
    )
    assert len(dataset_node.hash_value) == 64

    # 5. Formulate Feature Set
    feature_set = workspace.create_feature_set(
        name="OBI_Microstructure_Features",
        features=["obi_score", "obi_moving_std_5"],
        dataset_version_id=dataset_node.version_id
    )
    assert feature_set.dataset_version_id == dataset_node.version_id
    assert len(feature_set.feature_names) == 2

    # 6. Register Experiment
    params = {"threshold": 0.25}
    exp = workspace.experiments.register_experiment(
        idea_id=hyp.id,
        dataset_name="OBI_Microstructure_Features",
        dataset_df=clean_platform_df,
        parameters=params,
        seed=101
    )
    assert exp.idea_id == hyp.id

    # 7. Log Statistical Validation Report
    # Sharpe exceeds target 2.0, p_value is significant (<0.05)
    report_sig = workspace.log_validation_report(
        experiment_id=exp.id,
        deflated_sharpe=2.45,
        p_value=0.012
    )
    assert report_sig.is_statistically_significant is True

    # Sharpe fails target -> should not be significant
    report_insig = workspace.log_validation_report(
        experiment_id=exp.id,
        deflated_sharpe=1.2,
        p_value=0.012
    )
    assert report_insig.is_statistically_significant is False

    # 8. Check Promotion Gate (Fails because Peer Review is missing)
    success, deployment = workspace.execute_promotion_gate(report_sig.id)
    assert success is False
    assert deployment is None

    # 9. Perform Peer Review Board Approval
    # Meets realistic metrics, passes look-ahead/overfitting checks
    review_metrics = {
        "sharpe_ratio": 2.45,
        "num_bars": 500,
        "is_sharpe": 2.5,
        "oos_sharpe": 2.1
    }
    verdict = workspace.peer_review.submit_for_peer_review(exp.id, review_metrics)
    assert verdict.verdict == "APPROVED"

    # 10. Check Promotion Gate (Success!)
    success, deployment = workspace.execute_promotion_gate(report_sig.id)
    assert success is True
    assert deployment is not None
    assert deployment.mode == "shadow"
    assert deployment.experiment_id == exp.id

    # 11. Record Knowledge Base Entry
    kb_entry = workspace.record_knowledge_entry(
        source_type="deployment",
        source_id=deployment.id,
        lessons="Successfully promoted OBI alpha. Reconciled shadow execution with 0.12 pips average slippage.",
        recommendation="Deploy small live capital."
    )
    assert kb_entry.source_type == "deployment"
    assert "reconciled shadow execution" in kb_entry.lessons_learned.lower()
