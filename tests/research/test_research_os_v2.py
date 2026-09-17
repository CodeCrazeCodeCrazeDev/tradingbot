"""
Comprehensive unit and integration test suite for the redesigned Research Operating System (V2).
Verifies:
1. SQLite persistent database structure and schemas.
2. NetworkX Lineage Graphs cycle checks and stale propagation.
3. Provenance Hashing and exact replication verification.
4. Statistical metrics correctness (DSR).
5. Baseline strategy library executions.
6. Data integrity safeguards (lookahead bias, duplicates, contamination) fail-closed triggers.
7. Full lifecycle end-to-end integration:
   Hypothesis -> Dataset -> Feature -> Experiment -> Model -> Backtest -> Validation -> Approval -> Strategy -> CSC
"""

import os
import pytest
import sqlite3
import numpy as np
import pandas as pd
import networkx as nx

from trading_bot.research.research_os_v2 import (
    ResearchOSV2,
    DatasetLineageGraph,
    FeatureLineageGraph,
    ProvenanceHasher,
    BaselineStrategyLibrary,
    StatisticalValidationFramework,
    phi_cdf,
    phi_inverse
)
from trading_bot.core.unified_registry import UnifiedComponentRegistry


@pytest.fixture
def clean_ohlcv_data():
    """Generates synthetic OHLCV data."""
    dates = pd.date_range("2026-01-01", periods=150, freq="h")
    np.random.seed(42)
    close = 1.1000 + np.cumsum(np.random.normal(0, 0.002, 150))
    open_prices = close - np.random.normal(0, 0.0005, 150)
    high = np.maximum(open_prices, close) + 0.001
    low = np.minimum(open_prices, close) - 0.001

    df = pd.DataFrame({
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(100, 1000, 150)
    }, index=dates)
    return df


def test_sqlite_persistence_and_schemas():
    """Verifies that ResearchOSV2 correctly initializes schemas and tables inside SQLite."""
    test_db = "test_research_schemas.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    ros = ResearchOSV2(test_db)

    # Query sqlite_master to verify tables exist
    with ros.backend.get_connection() as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t["name"] for t in tables]

    expected_tables = [
        "hypotheses", "datasets", "features", "experiments", "models",
        "strategies", "backtests", "ledger", "approvals", "benchmarks",
        "provenance", "research_debt"
    ]
    for table in expected_tables:
        assert table in table_names, f"Expected table '{table}' missing from database schema."

    os.remove(test_db)


def test_networkx_lineages():
    """Verifies DAG cycle prevention and stale node marking in lineages."""
    # 1. Dataset lineage DAG
    ds_dag = DatasetLineageGraph()
    ds_dag.register_dataset_node("raw_fx")
    ds_dag.register_dataset_node("clean_fx", ["raw_fx"])

    # Try adding a cycle: raw_fx depends on clean_fx
    with pytest.raises(ValueError, match="Dataset cycle detected"):
        ds_dag.register_dataset_node("raw_fx", ["clean_fx"])

    # 2. Feature lineage DAG
    feat_dag = FeatureLineageGraph()
    feat_dag.register_feature_node("returns")
    feat_dag.register_feature_node("vol", ["returns"])
    feat_dag.register_feature_node("zscore", ["vol"])

    assert feat_dag.is_stale("zscore") is False

    # Mark returns as stale; vol and zscore must become stale
    feat_dag.mark_stale("returns")
    assert feat_dag.is_stale("returns") is True
    assert feat_dag.is_stale("vol") is True
    assert feat_dag.is_stale("zscore") is True


def test_provenance_hashing():
    """Verifies that any config or parameter alteration changes the unique Provenance Hash."""
    dataset_hash = "f11a8bc8782d"
    feature_hashes = ["v1_ret", "v1_vol"]
    git_commit = "git-sha-77bc"
    config = {"stop_pips": 12.0}
    hyperparams = {"learning_rate": 0.01}
    seed = 42

    hash1 = ProvenanceHasher.calculate_hash(
        dataset_hash, feature_hashes, git_commit, config, seed, hyperparams
    )

    # Verify deterministic output
    hash2 = ProvenanceHasher.calculate_hash(
        dataset_hash, feature_hashes, git_commit, config, seed, hyperparams
    )
    assert hash1 == hash2

    # Change hyperparameter
    hash_diff_hyper = ProvenanceHasher.calculate_hash(
        dataset_hash, feature_hashes, git_commit, config, seed, {"learning_rate": 0.02}
    )
    assert hash1 != hash_diff_hyper

    # Change seed
    hash_diff_seed = ProvenanceHasher.calculate_hash(
        dataset_hash, feature_hashes, git_commit, config, 101, hyperparams
    )
    assert hash1 != hash_diff_seed


def test_statistical_metrics_and_dsr():
    """Verifies standard normal Phi proxy and Bailey and Lopez de Prado's Deflated Sharpe Ratio."""
    # Standard Phi checks
    assert abs(phi_cdf(0.0) - 0.5) < 1e-5
    assert abs(phi_cdf(1.96) - 0.975) < 0.01

    # Quantile inverse CDF checks
    assert abs(phi_inverse(0.5) - 0.0) < 1e-5
    assert abs(phi_inverse(0.975) - 1.96) < 0.01

    # DSR check
    # Given an observed Sharpe of 2.5 on 150 bars, and 100 trials with average variance
    observed_sr = 2.5
    num_trials = 100
    var_srs = 0.04
    skew = -0.1
    kurt = 3.1
    num_bars = 150

    dsr = StatisticalValidationFramework.compute_dsr(
        observed_sr, num_trials, var_srs, skew, kurt, num_bars
    )
    assert isinstance(dsr, float)
    assert 0.0 <= dsr <= 1.0


def test_baseline_strategy_library(clean_ohlcv_data):
    """Verifies outperforming baselines inside the library."""
    lib = BaselineStrategyLibrary()

    b_h = lib.run_buy_and_hold(clean_ohlcv_data)
    assert len(b_h) == len(clean_ohlcv_data)

    ma_cross = lib.run_moving_average_crossover(clean_ohlcv_data)
    assert len(ma_cross) == len(clean_ohlcv_data)

    lin_reg = lib.run_linear_regression_baseline(clean_ohlcv_data)
    assert len(lin_reg) == len(clean_ohlcv_data)


def test_fail_closed_leakage_detector(clean_ohlcv_data):
    """Verifies that lookahead and duplication check correctly flags data contamination."""
    df = clean_ohlcv_data.copy()

    # Add a clean feature
    df["clean_feature"] = df["close"].rolling(5).mean()
    assert StatisticalValidationFramework.detect_lookahead_bias(df, "clean_feature") is False

    # Add a leaky feature looking directly into the future close
    df["leaky_feature"] = df["close"].shift(-2)
    assert StatisticalValidationFramework.detect_lookahead_bias(df, "leaky_feature") is True

    # Identify duplicate samples
    df_dups = df.copy()
    df_dups = pd.concat([df_dups, df_dups.iloc[:10]])
    assert StatisticalValidationFramework.identify_duplicate_samples(df_dups) > 0


def test_end_to_end_research_lifecycle_integration(clean_ohlcv_data):
    """
    Verifies the complete quantitative research lifecycle:
    Hypothesis -> Dataset -> Feature -> Experiment -> Model -> Backtest -> Validation -> Approval -> Strategy -> CSC
    """
    test_db = "test_research_lifecycle.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    # Initialize Research OS
    ros = ResearchOSV2(test_db)

    # Phase 1: Propose Hypothesis
    hyp = ros.hypotheses.record_hypothesis(
        name="Order Book Shift Reversion",
        motivation="Does localized imbalance revert in range regimes?",
        expected_outcome=2.2,
        falsifications=["reversion_fails_high_vol", "slippage_exceeds_profit"]
    )
    assert hyp["status"] == "Proposed"

    # Phase 2: Register Clean Dataset
    ds = ros.datasets.register_dataset(
        name="EURUSD_15m_2026",
        source="MT5_clean",
        version_tag="v1.0.0",
        df=clean_ohlcv_data,
        regime="NORMAL"
    )
    assert len(ds["hash"]) == 64

    # Phase 3: Register Feature Columns
    feat1 = ros.features.register_feature(
        name="VWAP_Distance",
        expression="close - vwap",
        lookback=20,
        mi=0.15,
        psi=0.02,
        version_tag="f_v1.0"
    )

    # Phase 4: Execute Experiment Pipeline
    # 4.1 Safe Clean Run (DSR high, no leakage)
    trial_sharpes = [1.2, 1.5, 0.8, 1.9, 1.4, 2.1]
    success, verdict, res = ros.execute_experiment_pipeline(
        hypothesis_id=hyp["id"],
        dataset_id=ds["id"],
        feature_ids=[feat1["id"]],
        git_sha="git-commit-abc1234",
        config={"target_pips": 10.0, "stop_pips": 15.0},
        hyperparams={"depth": 4},
        seed=123,
        model_type="RandomForestRegressor",
        param_count=500,
        weights_path="/models/rf_weights.pkl",
        df=clean_ohlcv_data,
        nominal_sharpe=3.5,
        max_dd=8.5,
        num_bars=150,
        trial_sharpes=trial_sharpes
    )

    # Safe backtest with Sharpe 3.5 and low trial variance should pass validation!
    assert success is True
    assert verdict == "APPROVED"
    assert "strategy_id" in res

    # Verify Strategy was approved in SQLite
    strat = ros.strategies.get_strategy(res["strategy_id"])
    assert strat["status"] == "APPROVED"

    # Verify CSC can query approved strategies read-only
    registered_ros = UnifiedComponentRegistry().get("research_operating_system")
    assert registered_ros is ros

    # Read approved strategies from database
    with ros.backend.get_connection() as conn:
        approved_strats = conn.execute("SELECT * FROM strategies WHERE status = 'APPROVED'").fetchall()
        assert len(approved_strats) > 0

    # 4.2 Leakage Fail-Closed Run
    leaky_df = clean_ohlcv_data.copy()
    leaky_df["leaky_feat"] = leaky_df["close"].shift(-5)

    success_leak, verdict_leak, res_leak = ros.execute_experiment_pipeline(
        hypothesis_id=hyp["id"],
        dataset_id=ds["id"],
        feature_ids=[feat1["id"]],
        git_sha="git-commit-abc1234",
        config={"target_pips": 10.0, "stop_pips": 15.0},
        hyperparams={"depth": 4},
        seed=123,
        model_type="LeakyModel",
        param_count=500,
        weights_path="/models/leaky_weights.pkl",
        df=leaky_df,
        nominal_sharpe=4.8,
        max_dd=1.0,
        num_bars=150,
        trial_sharpes=trial_sharpes
    )

    assert success_leak is False
    assert verdict_leak == "REJECTED_INTEGRATION_LEAK"

    os.remove(test_db)
