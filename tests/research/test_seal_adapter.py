"""
Unit and integration tests for SEAL: Self-Adapting Alpha Loop framework.
Verifies inner and outer adaptation loops, REINFORCE policy gradients, and Research OS integration.
"""

import os
import pytest
import json
import sqlite3
import numpy as np
import pandas as pd

from trading_bot.research.research_os_v2 import ResearchWorkspaceV2
from trading_bot.research.seal_adapter import SEALSelfEdit, SEALInnerLoop, SEALOuterLoop, SEALSystem

@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "research_seal_test.db")

@pytest.fixture
def workspace(temp_db_path):
    return ResearchWorkspaceV2(db_path=temp_db_path, target_sharpe=2.0)


def test_seal_self_edit_dataclass():
    """Verifies that the SEALSelfEdit dataclass initializes correctly with standard fields."""
    weights = np.array([0.1, 0.2, 0.3])
    edit = SEALSelfEdit(
        id="test_edit_1",
        synthetic_noise_std=0.01,
        synthetic_imbalance_scale=1.2,
        learning_rate=0.05,
        epochs=10,
        l2_regularization=0.05,
        adapted_weights=weights
    )
    assert edit.id == "test_edit_1"
    assert edit.epochs == 10
    assert np.array_equal(edit.adapted_weights, weights)


def test_seal_inner_loop(sample_price_series):
    """Verifies that the inner SFT-style update loop performs synthetic augmentation and persistent weight updates."""
    edit = SEALSelfEdit(
        id="inner_test",
        synthetic_noise_std=0.01,
        synthetic_imbalance_scale=1.5,
        learning_rate=0.1,
        epochs=5,
        l2_regularization=0.01
    )

    train_returns = sample_price_series.pct_change().dropna()
    base_weights = np.array([0.5, 0.5])

    # 1. Synthetic data generation
    synth = SEALInnerLoop.generate_synthetic_data(train_returns, edit)
    assert len(synth) == len(train_returns)
    assert not synth.isnull().any()

    # 2. Persistent update execution
    adapted_w = SEALInnerLoop.execute_persistent_update(base_weights, train_returns, edit)
    assert len(adapted_w) == 2
    # Weights must have shifted in response to optimization
    assert not np.array_equal(base_weights, adapted_w)


def test_seal_outer_loop_and_policy_gradient(sample_price_series):
    """Verifies that the outer RL loop samples edits, computes downstream rewards, and trains policy parameters."""
    outer = SEALOuterLoop(action_dim=5)

    # 1. Sample Self-Edit
    edit = outer.sample_self_edit("outer_test")
    assert edit.synthetic_noise_std > 0
    assert edit.learning_rate > 0
    assert edit.epochs >= 1

    # 2. Downstream performance evaluator (Sharpe Ratio)
    adapted_weights = np.array([0.8, 0.8])
    oos_returns = sample_price_series.pct_change().dropna()
    reward = outer.evaluate_downstream_performance(adapted_weights, oos_returns)
    assert isinstance(reward, float)

    # 3. Policy update (REINFORCE)
    original_means = outer.policy_means.copy()

    # Simulate sampling 3 edits and computing their rewards
    edits = [outer.sample_self_edit(f"batch_{i}") for i in range(3)]
    rewards = [1.5, -0.5, 2.0]

    outer.update_policy(edits, rewards)

    # Policy means must shift in direction of positive rewards
    assert not np.array_equal(original_means, outer.policy_means)


def test_seal_system_end_to_end(sample_price_series):
    """Tests the full SEAL system executing both loops to produce optimized, adapted strategy weights."""
    seal = SEALSystem()
    base_weights = np.array([0.2, 0.2, 0.2])
    train_returns = sample_price_series.pct_change().dropna()
    oos_returns = sample_price_series.pct_change().dropna() * 1.1  # slightly different

    adapted, best_edit = seal.self_adapt_alpha(
        base_weights=base_weights,
        train_returns=train_returns,
        oos_returns=oos_returns,
        num_iterations=3
    )

    assert len(adapted) == 3
    assert best_edit is not None
    assert best_edit.adapted_weights is not None
    assert not np.array_equal(base_weights, adapted)


def test_research_os_seal_integration(workspace, sample_price_series):
    """Verifies that the persistent Research Workspace correctly triggers and logs SEAL adaptations to the ledger."""
    base_weights = np.array([0.5, 0.5])
    train_returns = sample_price_series.pct_change().dropna()
    oos_returns = sample_price_series.pct_change().dropna()

    adapted, directive = workspace.run_seal_adaptation_loop(
        base_weights=base_weights,
        train_returns=train_returns,
        oos_returns=oos_returns,
        num_iterations=2
    )

    assert len(adapted) == 2
    assert directive["self_edit_id"] != "unknown"
    assert directive["learning_rate"] > 0

    # Verify that the adaptation event was cryptographically linked and stored in the governance log
    assert workspace.verify_governance_ledger() is True

    with sqlite3.connect(workspace.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT event_type, payload FROM governance_log WHERE event_type = 'SEAL_SELF_ADAPTATION'")
        row = cursor.fetchone()
        assert row is not None
        payload = json.loads(row[1])
        assert payload["edit_directive"]["self_edit_id"] == directive["self_edit_id"]


@pytest.fixture
def sample_price_series():
    """Generates simple daily price series series for returns calculations."""
    dates = pd.date_range("2026-01-01", periods=150, freq="D")
    prices = 100.0 + np.cumsum(np.random.normal(0.05, 0.5, 150))
    return pd.Series(prices, index=dates)
