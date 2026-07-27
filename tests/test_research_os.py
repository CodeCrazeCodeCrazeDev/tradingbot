"""
Unit tests validating Research Operating System (Research OS) core modules.
Verifies Idea Prioritization, Experiment Tracking, Reproducibility Lineage,
Peer Review Governance checklists, and Production-to-Research Feedback loops.
"""

import pytest
import pandas as pd
import numpy as np

from trading_bot.research.research_os import (
    IdeaRegistry,
    ExperimentRegistry,
    ReproducibilityAssurer,
    PeerReviewBoard,
    KnowledgeArchive,
    ProductionFeedbackLoop
)


@pytest.fixture
def sample_dataset():
    """Generates simple mock DataFrame representing an experiment target dataset."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=10, freq="h"),
        "open": np.linspace(1.10, 1.15, 10),
        "close": np.linspace(1.11, 1.16, 10),
        "volume": [1000] * 10
    })


def test_research_intake_and_prioritization():
    """Verifies intake and prioritization scoring inside IdeaRegistry."""
    registry = IdeaRegistry()

    # Idea 1: High Sharpe, Low Cost, High Feasibility -> High Priority
    idea_high = registry.record_idea(
        title="SMC Fair Value Gaps Reversion",
        question="Do EURUSD price gaps revert under low volume regimes?",
        target_asset_class="FX",
        expected_sharpe=2.4,
        cost_days=3.0,
        feasibility=9.0
    )

    # Idea 2: Low Sharpe, High Cost, Low Feasibility -> Low Priority
    idea_low = registry.record_idea(
        title="Lagged Triple EMA Cross",
        question="Does lagged technical cross yield edge?",
        target_asset_class="FX",
        expected_sharpe=0.8,
        cost_days=15.0,
        feasibility=3.0
    )

    assert idea_high.priority_score > idea_low.priority_score
    assert idea_high.status == "Prioritized"
    assert idea_low.status == "Intake"


def test_experiment_registry_and_lineage_assurance(sample_dataset):
    """Verifies dataset hashing, experiment registration, and lineage verification."""
    registry = ExperimentRegistry()
    parameters = {"lookback": 20, "stop_pips": 12.0}

    exp = registry.register_experiment(
        idea_id="idea-fv-123",
        dataset_name="clean_ohlcv_2026",
        dataset_df=sample_dataset,
        parameters=parameters,
        seed=101
    )

    assert exp.dataset_name == "clean_ohlcv_2026"
    assert exp.random_seed == 101
    assert len(exp.dataset_hash) == 64  # Valid SHA-256 hex string

    # Verify mathematically identical lineage
    assert ReproducibilityAssurer.verify_lineage(exp, sample_dataset) is True

    # Modify dataset slightly and verify lineage check flags it
    corrupted_dataset = sample_dataset.copy()
    corrupted_dataset.iloc[0, 1] = 99.0
    assert ReproducibilityAssurer.verify_lineage(exp, corrupted_dataset) is False


def test_peer_review_board_checklist():
    """Verifies that the Peer Review Board flags look-ahead overfitting and small samples."""
    board = PeerReviewBoard()

    # Case 1: Excellent realistic metrics -> Approved
    metrics_safe = {"sharpe_ratio": 2.2, "num_bars": 500, "is_sharpe": 2.0, "oos_sharpe": 1.9}
    verdict_safe = board.submit_for_peer_review("exp-001", metrics_safe)
    assert verdict_safe.verdict == "APPROVED"
    assert verdict_safe.checklist_passed is True

    # Case 2: Overfit Sharpe (> 4.5) -> Rejected/Revision
    metrics_overfit = {"sharpe_ratio": 5.1, "num_bars": 50, "is_sharpe": 4.8, "oos_sharpe": 1.2}
    verdict_overfit = board.submit_for_peer_review("exp-002", metrics_overfit)
    assert verdict_overfit.verdict == "REJECTED"
    assert verdict_overfit.checklist_passed is False
    assert len(verdict_overfit.challenges_documented) >= 2


def test_knowledge_archive_failures():
    """Verifies indexing and searching of failed ideas inside the KnowledgeArchive."""
    archive = KnowledgeArchive()

    archive.archive_failed_idea(
        idea_id="idea-009",
        title="Double Bollinger Bands breakout",
        reason="Does not survive 0.8 pip transaction spread and commission drag."
    )

    match = archive.search_archive("Bollinger")
    assert match is not None
    assert match.idea_id == "idea-009"
    assert "commission drag" in match.rejection_reason


def test_production_feedback_loop():
    """Verifies that live anomalies trigger auto-intake of prioritized post-mortem tasks."""
    idea_reg = IdeaRegistry()
    loop = ProductionFeedbackLoop(idea_reg)

    # Simulate a production drawdown breach alert
    remedial_idea = loop.trigger_anomaly_alert(
        strategy_id="Strategy_SMC_V5",
        anomaly_type="DRAWDOWN_BREACH",
        observed=14.5,
        limit=10.0
    )

    assert remedial_idea.title == "Post-Mortem: Strategy_SMC_V5 DRAWDOWN_BREACH"
    assert remedial_idea.status == "Prioritized"
    assert "How can we evolve strategy" in remedial_idea.research_question
    assert len(loop.alerts) == 1
