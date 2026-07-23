"""
Unit and integration tests for Research Operating System V2 (Research OS V2).
Verifies database persistence, networkx DAG lineage tracing, DSR and FDR checks,
look-ahead and duplicate filters, immutable cryptographic governance ledgers,
and genetic closed-loop tournaments.
"""

import os
import pytest
import json
import sqlite3
import numpy as np
import pandas as pd
import networkx as nx

from trading_bot.research.research_os_v2 import ResearchWorkspaceV2

@pytest.fixture
def temp_db_path(tmp_path):
    """Provides a clean temporary SQLite database path for each test."""
    db_file = tmp_path / "research_test.db"
    return str(db_file)

@pytest.fixture
def workspace(temp_db_path):
    """Returns a fresh persistent ResearchWorkspaceV2 instance."""
    ws = ResearchWorkspaceV2(db_path=temp_db_path, target_sharpe=2.0)
    yield ws
    # Clean up the DB file and WAL files
    ws = None

@pytest.fixture
def sample_train_df():
    """Generates a clean training DataFrame."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=90, freq="h"),
        "open": np.linspace(1.1000, 1.1500, 90),
        "close": np.linspace(1.1100, 1.1600, 90),
        "volume": [1000] * 90
    })

@pytest.fixture
def sample_test_df():
    """Generates an out-of-sample testing DataFrame starting after the training set."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-05", periods=50, freq="h"),
        "open": np.linspace(1.1510, 1.1710, 50),
        "close": np.linspace(1.1610, 1.1810, 50),
        "volume": [1000] * 50
    })


def test_qrp_database_crud_persistence(workspace, sample_train_df):
    """Verifies that all entities are successfully created and stored inside the SQLite database."""
    # 1. Project
    proj = workspace.create_project(title="Trend Reversion Alpha", objective="Detect trend exhaustion at FVG zones")
    assert proj["id"] is not None
    assert proj["title"] == "Trend Reversion Alpha"

    # 2. Question
    q = workspace.formulate_question(project_id=proj["id"], question="Are price returns mean-reverting after FVG spikes?", foundation="Market structure order blocks")
    assert q["id"] is not None
    assert q["project_id"] == proj["id"]

    # 3. Hypothesis
    hyp = workspace.record_hypothesis(
        question_id=q["id"],
        name="FVG Spikes Revert",
        description="High volatility FVG gaps exhibit a high probability of reverting back to the origin source",
        rationale="Smart Money Concept imbalance mitigation",
        counterparty="Retail breakout traders chasing momentum",
        falsifications=["reversal_fails_to_materialize", "spread_drag_exceeds_profit"]
    )
    assert hyp["id"] is not None
    assert hyp["status"] == "Proposed"

    # 4. Dataset
    dataset = workspace.register_dataset(name="EURUSD_M15_2026", path="data/eurusd_m15.csv", df=sample_train_df)
    assert dataset["id"] is not None
    assert len(dataset["hash_value"]) == 64

    # 5. Feature
    feat = workspace.create_feature(name="fvg_distance", dataset_id=dataset["id"], formula="close - fvg_mid")
    assert feat["id"] is not None
    assert feat["dataset_id"] == dataset["id"]

    # 6. Experiment
    exp = workspace.register_experiment(
        hypothesis_id=hyp["id"],
        dataset_id=dataset["id"],
        parameters={"lookback": 24, "rr_target": 2.5},
        is_sharpe=2.4,
        oos_sharpe=2.1,
        num_bars=1000
    )
    assert exp["id"] is not None
    assert exp["is_sharpe"] == 2.4

    # Let's verify manual querying directly from SQLite
    with sqlite3.connect(workspace.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM projects WHERE id = ?", (proj["id"],))
        assert cursor.fetchone()[0] == "Trend Reversion Alpha"

        cursor.execute("SELECT name FROM hypotheses WHERE id = ?", (hyp["id"],))
        assert cursor.fetchone()[0] == "FVG Spikes Revert"

        cursor.execute("SELECT parameters FROM experiments WHERE id = ?", (exp["id"],))
        params_fetched = json.loads(cursor.fetchone()[0])
        assert params_fetched["lookback"] == 24


def test_deterministic_lineage_dag(workspace, sample_train_df):
    """Verifies that the complete research lineage is traced correctly via Directed Acyclic Graphs."""
    # Build complete lineage structure
    proj = workspace.create_project(title="Arbitrage Core", objective="Cross-symbol cointegration")
    q = workspace.formulate_question(project_id=proj["id"], question="Is there stable co-integration between pairs?", foundation="Arbitrage pricing theory")
    hyp = workspace.record_hypothesis(
        question_id=q["id"],
        name="USD Pairs Cointegrate",
        description="EURUSD and GBPUSD returns co-integrate over long periods",
        rationale="Economic parity",
        counterparty="Unhedged retail",
        falsifications=["cointegration_breaks_down"]
    )
    dataset = workspace.register_dataset(name="Arbitrage_Pair_Set", path="data/pairs.csv", df=sample_train_df)
    feat = workspace.create_feature(name="spread_zscore", dataset_id=dataset["id"], formula="zscore(spread)")
    exp = workspace.register_experiment(
        hypothesis_id=hyp["id"],
        dataset_id=dataset["id"],
        parameters={"z_threshold": 2.0},
        is_sharpe=2.2,
        oos_sharpe=1.8,
        num_bars=1200
    )
    val = workspace.log_validation_report(
        experiment_id=exp["id"],
        observed_sr=1.8,
        num_trials=20,
        variance_of_srs=0.15,
        skewness=-0.2,
        kurtosis=3.2,
        num_bars=1200
    )
    review = workspace.submit_for_peer_review(
        experiment_id=exp["id"],
        metrics={"sharpe_ratio": 2.2, "num_bars": 500, "is_sharpe": 2.2, "oos_sharpe": 1.8}
    )

    # Reconstruct lineage graph
    lineage = workspace.get_lineage_graph()
    assert isinstance(lineage, nx.DiGraph)

    # Assert node tracking
    assert dataset["id"] in lineage.nodes
    assert feat["id"] in lineage.nodes
    assert exp["id"] in lineage.nodes
    assert val["id"] in lineage.nodes
    assert review["id"] in lineage.nodes

    # Assert directed edges represent correct workflow directionality
    assert lineage.has_edge(dataset["id"], feat["id"])
    assert lineage.has_edge(dataset["id"], exp["id"])
    assert lineage.has_edge(hyp["id"], exp["id"])

    # Verify reproducibility hashes
    assert workspace.verify_reproducibility_hash(dataset["id"], sample_train_df) is True
    corrupted_df = sample_train_df.copy()
    corrupted_df.iloc[0, 1] = 999.9
    assert workspace.verify_reproducibility_hash(dataset["id"], corrupted_df) is False


def test_deflated_sharpe_ratio_check(workspace):
    """Verifies that the Deflated Sharpe Ratio correctly penalizes multiple testing selection bias."""
    # High observed Sharpe with 1 trial (no selection bias penalty)
    dsr_single = workspace.calculate_dsr(observed_sr=2.0, num_trials=1, variance_of_srs=0.0, skewness=0.0, kurtosis=3.0, num_bars=500)
    # Observed Sharpe 2.0 but with 100 random trials (severe selection bias penalty)
    dsr_many = workspace.calculate_dsr(observed_sr=2.0, num_trials=100, variance_of_srs=0.5, skewness=0.0, kurtosis=3.0, num_bars=500)

    assert dsr_single > 0.95
    assert dsr_many < dsr_single  # Severe penalty applied

    # Log report and verify significance logic
    rep_sig = workspace.log_validation_report("exp-001", observed_sr=2.5, num_trials=1, variance_of_srs=0.0, skewness=0.0, kurtosis=3.0, num_bars=500)
    assert rep_sig["is_statistically_significant"] is True

    rep_insig = workspace.log_validation_report("exp-002", observed_sr=2.0, num_trials=500, variance_of_srs=0.9, skewness=-0.5, kurtosis=4.5, num_bars=200)
    assert rep_insig["is_statistically_significant"] is False


def test_temporal_leakage_and_duplicate_sample_filters(sample_train_df, sample_test_df):
    """Asserts that temporal look-ahead and overlapping training-test data leakage are correctly flagged."""
    # 1. Temporal look-ahead verification (clean)
    assert ResearchWorkspaceV2.validate_temporal_leakage(sample_train_df, sample_test_df) is True

    # Corrupt with leak: train row starts during/after test set
    leaky_train_df = sample_train_df.copy()
    leaky_train_df.iloc[-1, leaky_train_df.columns.get_loc("timestamp")] = pd.to_datetime("2026-02-01")
    assert ResearchWorkspaceV2.validate_temporal_leakage(leaky_train_df, sample_test_df) is False

    # 2. Overlapping duplicate filter (clean)
    assert ResearchWorkspaceV2.filter_duplicate_samples(sample_train_df, sample_test_df) is True

    # Inject duplicate overlapping rows
    duplicate_train_df = sample_train_df.copy()
    duplicate_train_df.iloc[-5:] = sample_test_df.iloc[:5].values
    assert ResearchWorkspaceV2.filter_duplicate_samples(duplicate_train_df, sample_test_df) is False


def test_benjamini_hochberg_fdr_control():
    """Verifies that false discoveries are controlled using the Benjamini-Hochberg procedure."""
    # List of p-values: 3 highly significant, 1 marginally, 1 insignificant
    p_values = [0.0001, 0.001, 0.005, 0.04, 0.65]

    significant_bh = ResearchWorkspaceV2.apply_benjamini_hochberg(p_values, q=0.05)

    assert significant_bh[0] is True  # 0.0001 -> Significant
    assert significant_bh[1] is True  # 0.001  -> Significant
    assert significant_bh[2] is True  # 0.005  -> Significant
    assert significant_bh[4] is False # 0.65   -> Insignificant


def test_immutable_cryptographic_governance_ledger(workspace):
    """Verifies that peer reviews are signed, link-hashed, and resistant to database tampering."""
    # Submit peer review (auto-appends to the immutable log)
    workspace.create_project(title="Genesis Project", objective="Build core portfolio")
    workspace.formulate_question(project_id="gen", question="Genesis?", foundation="Foundation")
    workspace.record_hypothesis("q-gen", "GenHyp", "Desc", "Rat", "Count", [])
    workspace.register_dataset("dataset", "data", pd.DataFrame({"close": [1, 2, 3]}))
    workspace.register_experiment("hyp-gen", "dataset", {}, 2.0, 1.8, 100)

    rev1 = workspace.submit_for_peer_review(experiment_id="exp-gen", metrics={"sharpe_ratio": 2.2, "num_bars": 200, "is_sharpe": 2.2, "oos_sharpe": 1.9})
    rev2 = workspace.submit_for_peer_review(experiment_id="exp-gen", metrics={"sharpe_ratio": 1.9, "num_bars": 300, "is_sharpe": 1.9, "oos_sharpe": 1.7})

    # Validate ledger is crytographically continuous and undamaged
    assert workspace.verify_governance_ledger() is True

    # Simulate malicious database tampering (alter verdict payload)
    with sqlite3.connect(workspace.db_path) as conn:
        conn.execute("UPDATE governance_log SET payload = ? WHERE id = 1", (json.dumps({"tampered": "hacked_data"}),))

    # Assert ledger integrity verification detects structural disruption
    assert workspace.verify_governance_ledger() is False


def test_bidirectional_feedback_and_regime_tournament(workspace):
    """Verifies feedback anomaly creation, GA chromosome mutation, and tournament simulation."""
    # 1. Anomaly trigger
    alert = workspace.trigger_anomaly_alert(strategy_id="Strategy_OB_Mitigation", anomaly_type="SLIPPAGE_DEGRADATION", observed=4.8, limit=2.5)
    assert alert["project"] is not None
    assert "Post-Mortem: Strategy_OB_Mitigation SLIPPAGE_DEGRADATION" in alert["project"]["title"]

    # 2. GA Mutation & Crossover of weights
    parent_a = np.array([0.5, 0.2, 0.8, -0.4])
    parent_b = np.array([0.1, -0.3, 0.9, 0.2])
    child = ResearchWorkspaceV2.mutate_and_crossover_alpha_weights(parent_a, parent_b, mutation_rate=0.5)

    assert len(child) == 4
    # All elements must be within logical numeric limits
    assert not np.isnan(child).any()

    # 3. Regime Tournament Sandbox Playbacks
    np.random.seed(42)
    # Generate 200 daily returns (mock data)
    champion_returns = pd.Series(np.random.normal(0.001, 0.01, 200))
    # Challenger 1: Excellent returns
    challenger_1 = pd.Series(np.random.normal(0.002, 0.008, 200))
    # Challenger 2: Terrible returns
    challenger_2 = pd.Series(np.random.normal(-0.001, 0.015, 200))

    tournament = workspace.run_regime_tournament(champion_returns, [challenger_1, challenger_2], min_oos_bars=100)

    assert tournament["status"] == "COMPLETED"
    assert len(tournament["challengers"]) == 2
    # Challenger 1 has higher mean return and lower std -> must outperform champion
    assert tournament["challengers"][0]["challenger_idx"] == 0
    assert tournament["challengers"][0]["outperformed_champion"] == True
    assert tournament["challengers"][1]["outperformed_champion"] == False
