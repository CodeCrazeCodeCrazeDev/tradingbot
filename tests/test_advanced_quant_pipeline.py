"""
Rigorous statistical tests for invisible institutional pipeline stages.
Verifies DSR, Market Microstructure Imbalance, Orthogonality correlation,
Square-root Impact capacity scaling, and PSI Drift detection.
"""

import pytest
import numpy as np
import pandas as pd

from trading_bot.research.quant_pipeline import (
    LiteratureReviewBacklog,
    RegimeAndMicrostructureAnalyzer,
    FeatureSelectionSuite,
    AlphaValidatorAndOrthogonality,
    AdvancedStatisticalValidation,
    CapacityAnalyzer,
    ShadowTradingEnvironment,
    PerformanceAttribution,
    AdvancedDriftDetection,
    Signal
)


def test_literature_review_backlog():
    """Verifies indexing and matching of existing internal/external literature reviews."""
    backlog = LiteratureReviewBacklog()
    match = backlog.verify_topic("EMA Crossover")
    assert match["result"] == "FAIL"
    assert "wipe out small edge" in match["reason"]

    unknown = backlog.verify_topic("Non-linear Quantum Wavelet")
    assert unknown["result"] == "UNKNOWN"


def test_regime_and_microstructure_analysis():
    """Verifies high-fidelity regime classification and Order Book Imbalance."""
    analyzer = RegimeAndMicrostructureAnalyzer()

    # Check Order Book Imbalance (OBI)
    # Bid=1000, Ask=500 -> OBI = (1000 - 500) / 1500 = +0.333
    obi = analyzer.calculate_order_book_imbalance(1000.0, 500.0)
    assert abs(obi - 0.3333) < 1e-3

    # Check execution fill probability decay
    # Wide spread, large limit distance -> lower fill probability
    prob_near = analyzer.estimate_fill_probability(spread_pips=1.0, limit_distance_pips=0.2)
    prob_far = analyzer.estimate_fill_probability(spread_pips=1.0, limit_distance_pips=2.5)
    assert prob_near > prob_far
    assert prob_near > 0.0 and prob_near <= 1.0


def test_feature_selection_suite():
    """Verifies Mutual Information and SHAP feature selection scores."""
    suite = FeatureSelectionSuite()
    feature = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    target = pd.Series([1.2, 1.8, 3.1, 3.9, 5.2])

    mi = suite.calculate_mutual_information_score(feature, target)
    assert mi > 0.8  # Strong linear correlation yields high MI proxy score

    shap = suite.calculate_shap_proxy(feature, target)
    assert shap > 0.0


def test_alpha_orthogonality():
    """Verifies alignment and correlation checking against active portfolio alphas."""
    checker = AlphaValidatorAndOrthogonality()

    # Case 1: No active alphas -> passes
    candidate = pd.Series([0.01, -0.005, 0.02, 0.012, -0.003])
    is_orthogonal, max_corr = checker.check_orthogonality(candidate)
    assert is_orthogonal == True
    assert max_corr == 0.0

    # Case 2: Aligned highly correlated alpha -> fails orthogonality (max corr > 0.40)
    checker.active_alphas.append(candidate)
    correlated_candidate = candidate * 1.5 + np.random.normal(0, 0.0001, 5)
    is_orthogonal, max_corr = checker.check_orthogonality(correlated_candidate)
    assert is_orthogonal == False
    assert max_corr > 0.90


def test_deflated_sharpe_ratio():
    """Verifies Bailey and Lopez de Prado's Deflated Sharpe Ratio (DSR) calculation."""
    validator = AdvancedStatisticalValidation()

    # We ran 100 trials, observed Sharpe is 2.5, but trails standard deviation is wide.
    # High observed Sharpe relative to expected maximum yields high DSR.
    dsr_high = validator.calculate_deflated_sharpe_ratio(
        observed_sr=3.2,
        num_trials=50,
        variance_of_srs=0.1,
        skewness=-0.2,
        kurtosis=3.5,
        num_bars=252
    )

    # Low observed Sharpe with high trials (multiple testing inflation) yields low DSR.
    dsr_low = validator.calculate_deflated_sharpe_ratio(
        observed_sr=0.5,
        num_trials=500,
        variance_of_srs=0.4,
        skewness=-0.2,
        kurtosis=3.5,
        num_bars=252
    )

    assert dsr_high > dsr_low
    assert dsr_high >= 0.0 and dsr_high <= 1.0


def test_capacity_scaling_square_root_law():
    """Verifies square-root law of market impact capacity scaling."""
    analyzer = CapacityAnalyzer(impact_coefficient=0.15)

    # Large trade size relative to daily volume escalates slippage pips
    impact_small = analyzer.estimate_market_impact_pips(
        trade_size_usd=10000.0,
        avg_daily_volume_usd=10000000.0,
        vol_annualized=0.15
    )

    impact_large = analyzer.estimate_market_impact_pips(
        trade_size_usd=1000000.0,
        avg_daily_volume_usd=10000000.0,
        vol_annualized=0.15
    )

    assert impact_large > impact_small
    # Verify square-root ratio: size increases 100x -> impact increases approx 10x
    ratio = impact_large / impact_small
    assert abs(ratio - 10.0) < 1.0


def test_shadow_trading_environment():
    """Verifies shadow logging and spread-slippage reconciliation."""
    env = ShadowTradingEnvironment()
    signal = Signal(
        time=pd.Timestamp("2026-07-24"),
        symbol="EURUSD",
        direction="buy",
        rationale="Microstructure imbalance",
        stop_loss_pips=10.0,
        take_profit_rr=2.0,
        confidence=80.0
    )

    log = env.record_shadow_execution(signal, actual_spread=0.8)
    assert log["symbol"] == "EURUSD"
    assert log["expected_pips"] == 20.0
    assert log["actual_slippage_pips"] > 0.0
    assert len(env.shadow_log) == 1


def test_performance_attribution():
    """Verifies return deconstruction into Alpha, Beta, and transaction costs."""
    attrib = PerformanceAttribution()

    results = attrib.attribute_performance(
        total_pnl_usd=5000.0,
        market_return_pnl=2000.0,
        transaction_cost_drag=450.0,
        beta=1.2
    )

    # Beta return = 1.2 * 2000 = $2400
    assert results["beta_attribution_usd"] == 2400.0
    # Net edge before fees = 5000 - 2400 = $2600. Alpha is net edge before transaction drag: 2600 + 450 = $3050
    assert results["alpha_attribution_usd"] == 3050.0
    assert results["transaction_cost_drag_usd"] == 450.0


def test_drift_detection_psi():
    """Verifies Population Stability Index (PSI) distribution drift detection."""
    detector = AdvancedDriftDetection()

    # Distributions match perfectly -> PSI near 0
    base = np.random.normal(0, 1, 1000)
    actual_stable = np.random.normal(0, 1, 1000)
    psi_stable = detector.calculate_psi(base, actual_stable)
    assert psi_stable < 0.1

    # Distributions heavily drifted -> PSI high (>0.25)
    actual_drifted = np.random.normal(1.5, 1.2, 1000)
    psi_drifted = detector.calculate_psi(base, actual_drifted)
    assert psi_drifted > 0.25
