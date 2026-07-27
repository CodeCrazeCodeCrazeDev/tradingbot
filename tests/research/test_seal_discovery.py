"""
Unit and integration tests for SEAL Autonomous Discovery and Audit Engine.
Verifies candidate scanning, sensitivity analyses, proposal generation, and parameter self-adaptation.
"""

import os
import pytest
import numpy as np
import pandas as pd

from trading_bot.research.seal_discovery import (
    SEALDiscoveryCandidate,
    SEALSelfEditProposal,
    SEALDiscoveryEngine
)


@pytest.fixture
def sample_price_series():
    """Generates simple daily price series for returns calculations."""
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    prices = 100.0 + np.cumsum(np.random.normal(0.02, 0.3, 100))
    return pd.Series(prices, index=dates)


def test_seal_discovery_candidate_and_proposal():
    """Verifies that discovered candidates and self-edit proposals initialize correctly."""
    candidate = SEALDiscoveryCandidate(
        candidate_id="cand_test",
        component_name="risk_manager",
        parameter_name="max_drawdown_limit",
        current_value=10.0,
        recommended_bounds=(5.0, 25.0),
        falsifiable_objective="Minimize drawdown breaches"
    )
    assert candidate.current_value == 10.0

    proposal = SEALSelfEditProposal(
        proposal_id="prop_test",
        candidate=candidate,
        synthetic_augmentation_config={"noise": 0.01},
        optimization_epochs=5,
        learning_rate=0.01,
        reward_function_objective="Minimize drawdown breaches"
    )
    assert proposal.optimization_epochs == 5


def test_scan_and_prioritization(sample_price_series):
    """Verifies scanning, sensitivity analysis, and prioritization ranking of discovered candidates."""
    engine = SEALDiscoveryEngine()

    # 1. Scan
    candidates = engine.scan_platform_for_seal_candidates()
    assert len(candidates) >= 3
    assert candidates[0].component_name == "hierarchical_memory_system"

    # 2. Sensitivity analysis & Prioritization
    oos_returns = sample_price_series.pct_change().dropna()
    prioritized = engine.prioritize_candidates(oos_returns)

    assert len(prioritized) == len(candidates)
    # Ranks should have positive sensitivity scores
    for cand in prioritized:
        assert cand.sensitivity_score >= 0.0


def test_proposal_generation_and_adaptation(sample_price_series):
    """Verifies generating self-edit proposals and executing autonomous parameter adaptation."""
    engine = SEALDiscoveryEngine()
    engine.scan_platform_for_seal_candidates()

    candidate_id = "cand_hierarchical_memory_system_memory_window_size"

    # 1. Proposal Generation
    proposal = engine.generate_self_edit_proposal(candidate_id)
    assert proposal is not None
    assert proposal.candidate.candidate_id == candidate_id
    assert "stress_regime" in proposal.synthetic_augmentation_config

    # 2. Autonomous Parameter Adaptation
    train_returns = sample_price_series.pct_change().dropna()
    oos_returns = sample_price_series.pct_change().dropna()

    original_val = float(proposal.candidate.current_value)
    adapted_val = engine.execute_autonomous_parameter_adaptation(
        proposal=proposal,
        train_returns=train_returns,
        oos_returns=oos_returns
    )

    # Adapted value must remain within defined candidate recommended bounds
    assert adapted_val >= proposal.candidate.recommended_bounds[0]
    assert adapted_val <= proposal.candidate.recommended_bounds[1]
