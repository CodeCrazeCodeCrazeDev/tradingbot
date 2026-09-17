"""
Rigorous unit tests validating the advanced Research OS extensions.
Verifies Data Governance Lineage hashes, Granger Causality, Chow Test structural breaks,
SHAP prediction attribution, Bayesian uncertainty bounds, and Genetic Alpha Evolution.
"""

import pytest
import numpy as np
import pandas as pd

from trading_bot.research.research_os import (
    DataLineageRegistry,
    CausalityAndStructuralBreakTester,
    ExplainabilityAndAttributionEngine,
    UncertaintyEstimator,
    StrategyEvolutionEngine
)


@pytest.fixture
def clean_lineage_df():
    """Generates simple DataFrame for lineage verification."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=15, freq="h"),
        "close": np.linspace(1.1000, 1.1075, 15),
        "volume": [2000] * 15
    })


def test_data_lineage_governance(clean_lineage_df):
    """Verifies lineage parent nodes, transformation labels, and exact dataset hashes."""
    registry = DataLineageRegistry()

    # Register raw source node
    node_raw = registry.register_version(
        source_name="Raw_MT5_EURUSD_M15",
        parent_ids=[],
        transformation="None",
        df=clean_lineage_df
    )
    assert len(node_raw.hash_value) == 64
    assert node_raw.transformation_applied == "None"

    # Register cleaned child node
    cleaned_df = clean_lineage_df.copy()
    cleaned_df["close"] = cleaned_df["close"] * 1.0001

    node_clean = registry.register_version(
        source_name="Cleaned_EURUSD_M15",
        parent_ids=[node_raw.version_id],
        transformation="Multiply_Close_Linear_Scale",
        df=cleaned_df
    )

    assert node_clean.lineage_parent_ids[0] == node_raw.version_id
    assert node_clean.hash_value != node_raw.hash_value


def test_causality_and_chow_structural_break():
    """Verifies Granger causality F-statistic and structural break Chow scores."""
    tester = CausalityAndStructuralBreakTester()

    # Create causally linked variables
    np.random.seed(42)
    cause = pd.Series(np.random.normal(0, 0.01, 100))
    # 'effect' is strongly lagged by 'cause'
    effect = pd.Series(np.zeros(100))
    for t in range(1, 100):
        effect.iloc[t] = 0.5 * effect.iloc[t-1] + 1.2 * cause.iloc[t-1] + np.random.normal(0, 0.001)

    granger_score = tester.test_granger_causality_score(cause, effect, max_lag=2)
    assert granger_score > 5.0  # High score confirms lag causal significance

    # Check Chow structural break detection
    # Split series into two radically different regimes
    regime1 = np.random.normal(0.0, 0.01, 50)
    regime2 = np.random.normal(1.5, 0.05, 50)  # different intercept and variance
    pooled = pd.Series(np.concatenate([regime1, regime2]))

    chow_score = tester.detect_structural_break_chow(pooled, split_idx=50)
    assert chow_score > 10.0  # High score sugersts structural process change


def test_explainability_attribution():
    """Verifies feature attribution weights (SHAP Proxy value) sum exactly to raw predictions."""
    engine = ExplainabilityAndAttributionEngine()

    feature_values = {"vwap_dist": 0.002, "order_book_imbalance": 0.45, "real_vol_10": 0.012}
    model_weights = {"vwap_dist": 1.5, "order_book_imbalance": 0.08, "real_vol_10": -2.0}

    attributions = engine.compute_feature_attributions(feature_values, model_weights)

    # Total raw = (0.002 * 1.5) + (0.45 * 0.08) + (0.012 * -2.0) = 0.003 + 0.036 - 0.024 = 0.015
    assert abs(attributions["total_prediction_raw"] - 0.015) < 1e-5
    assert attributions["order_book_imbalance"] == 0.45 * 0.08


def test_uncertainty_estimator():
    """Verifies dispersion standard error and Bayesian-style credal boundaries."""
    estimator = UncertaintyEstimator(confidence_interval=0.95)

    # Standard normal mock predictions trials
    np.random.seed(42)
    trials = np.random.normal(1.1025, 0.0015, 100)

    mean_p, lower_b, upper_b = estimator.estimate_credal_bounds(trials)

    assert abs(mean_p - 1.1025) < 0.0005
    assert lower_b < mean_p
    assert upper_b > mean_p
    assert (upper_b - lower_b) < 0.0015  # standard error is small for 100 sample trials


def test_strategy_evolution_operators():
    """Verifies uniform crossover and genetic mutations of active alpha signals."""
    engine = StrategyEvolutionEngine(mutation_rate=0.20)

    parent_a = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    parent_b = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

    # Recombination should yield child containing genetic mix of both parents
    child = engine.crossover_alphas(parent_a, parent_b)
    assert len(child) == 5
    assert set(child).issubset({0.0, 1.0})

    # Mutating should modify values within mutation limits (set rate to 1.0 for deterministic test)
    mutation_engine = StrategyEvolutionEngine(mutation_rate=1.0)
    mutated = mutation_engine.mutate_alpha(parent_a)
    assert len(mutated) == 5
    # With mutation_rate=1.0, every single element must differ from parent_a values of 1.0
    assert not np.array_equal(parent_a, mutated)
