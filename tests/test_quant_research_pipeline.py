"""
Tests validating Institutional Continuous Quant Research Loop components.
Verifies all 10 stages: Idea Proposal, Ingestion, Feature Calculations,
Alpha rank-IC Evaluation, Strategy Assembly, Walk-Forward backtests,
Risk-Parity Optimizer, Paper simulation, and Production monitoring.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from trading_bot.research.quant_pipeline import (
    ResearchLab,
    IngestionPipeline,
    FeatureFactory,
    AlphaDiscoveryEngine,
    StrategyBuilder,
    ValidationLab,
    PortfolioOptimizer,
    SimulatedPaperEnvironment,
    ProductionMonitor
)
from trading_bot.backtesting.advanced_backtester import InstitutionalBacktester


@pytest.fixture
def clean_synthetic_dataset():
    """Generates clean synthetic OHLCV data for testing."""
    dates = [datetime(2026, 1, 1) + timedelta(minutes=15 * i) for i in range(150)]
    np.random.seed(42)
    close_prices = 1.1000 + np.cumsum(np.random.normal(0, 0.001, 150))
    open_prices = close_prices - np.random.normal(0, 0.0002, 150)
    high_prices = np.maximum(open_prices, close_prices) + 0.0005
    low_prices = np.minimum(open_prices, close_prices) - 0.0005
    volume = np.random.randint(1000, 5000, 150)

    df = pd.DataFrame({
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volume
    }, index=pd.DatetimeIndex(dates))

    # Pre-calculate mock indicators expected by TIA inside StrategyEngine
    df["sma_20"] = df["close"].rolling(20).mean()
    df["ema_20"] = df["close"].rolling(20).mean()
    df["rsi_14"] = 50.0
    return df


def test_phase1_research_lab():
    """Verifies proposing and retrieving hypotheses in the Research Lab."""
    lab = ResearchLab()
    hyp = lab.propose_hypothesis(
        name="EURUSD Mean Reversion",
        description="After unusually high selling pressure, EUR/USD tends to mean-revert",
        rationale="Frictions and overnight liquidity constraints cause short-term momentum exhaustion.",
        counterparty="Aggressive retail margin liquidation flow.",
        falsifications=["Fails under structural regime transitions", "Does not survive transaction cost drag"]
    )

    assert hyp.name == "EURUSD Mean Reversion"
    assert hyp.status == "Proposed"
    assert len(hyp.falsification_conditions) == 2

    retrieved = lab.get_hypothesis(hyp.id)
    assert retrieved is not None
    assert retrieved.id == hyp.id


def test_phase2_data_pipeline(clean_synthetic_dataset):
    """Verifies that the IngestionPipeline processes, cleans, and validates data."""
    pipeline = IngestionPipeline()
    cleaned_df, report = pipeline.process_and_clean_data(clean_synthetic_dataset)

    assert report["is_valid"] is True
    assert len(cleaned_df) == 150
    assert report["bad_ticks_count"] == 0


def test_phase3_feature_factory(clean_synthetic_dataset):
    """Verifies that FeatureFactory computes microstructure and statistical features."""
    factory = FeatureFactory()
    features_df = factory.compute_features(clean_synthetic_dataset)

    # Factory drops rows during rolling indicators, so verify length and columns
    assert len(features_df) > 100
    assert "log_ret" in features_df.columns
    assert "real_vol_10" in features_df.columns
    assert "vwap_dist" in features_df.columns
    assert "hurst_proxy" in features_df.columns

    # Hurst proxy should stay within bounds
    assert features_df["hurst_proxy"].iloc[-1] >= 0.0


def test_phase4_alpha_discovery(clean_synthetic_dataset):
    """Verifies that AlphaDiscoveryEngine ranks feature correlation via IC."""
    factory = FeatureFactory()
    features_df = factory.compute_features(clean_synthetic_dataset)

    # Intentionally test correlation of Close VWAP distance with forward returns
    engine = AlphaDiscoveryEngine(min_ic_threshold=0.01)
    alpha = engine.evaluate_feature_as_alpha(features_df, feature_col="vwap_dist")

    assert alpha.name == "Alpha_vwap_dist"
    assert isinstance(alpha.information_coefficient, float)
    assert alpha.status in ["Approved", "Rejected"]


def test_phase5_to_8_strategy_builder_and_walk_forward_lab(clean_synthetic_dataset):
    """Verifies strategy building, realistic backtesting, and walk-forward validation splits."""
    config = {
        "execution_cost": {
            "commission_per_million_usd": 15.0,
            "fixed_commission_per_trade": 1.0,
            "default_spread_pips": 0.5,
            "default_slippage_pips": 0.2
        },
        "risk_limits": {
            "max_positions": 5,
            "max_spread_pips_limit": 2.5,
            "max_volatility_threshold": 0.05
        },
        "objectives": {
            "target_sharpe": 1.0,
            "max_drawdown_pct": 10.0
        }
    }

    builder = StrategyBuilder(default_config=config)
    strategy = builder.assemble_strategy(symbol="EURUSD", swing_len=3)

    backtester = InstitutionalBacktester(clean_synthetic_dataset, strategy, config=config, lookback=20)
    validation_lab = ValidationLab(backtester)

    # Run out-of-sample walk-forward analysis
    oos_results = validation_lab.run_walk_forward_backtest(oos_splits=2)
    assert len(oos_results) == 2
    for res in oos_results:
        assert isinstance(res.total_return_pct, float)
        assert isinstance(res.max_drawdown_pct, float)


def test_phase9_portfolio_optimizer():
    """Verifies Risk Parity allocations calculated by PortfolioOptimizer."""
    optimizer = PortfolioOptimizer(target_portfolio_vol=0.12)

    # Mock trailing volatilities of three strategy lines
    strategy_vols = {
        "Trend_SMC": 0.15,
        "MeanRev_Wyckoff": 0.08,
        "HFT_Liquidity": 0.22
    }

    allocations = optimizer.calculate_allocations(strategy_vols)

    assert "Trend_SMC" in allocations
    assert "MeanRev_Wyckoff" in allocations
    assert "HFT_Liquidity" in allocations

    # Risk-parity allocates higher weights to lower volatility strategies
    assert allocations["MeanRev_Wyckoff"] > allocations["Trend_SMC"]
    assert allocations["Trend_SMC"] > allocations["HFT_Liquidity"]

    # Sum of weights should equal approximately 1.0
    assert abs(sum(allocations.values()) - 1.0) < 1e-5


def test_phase10_paper_environment(clean_synthetic_dataset):
    """Verifies that SimulatedPaperEnvironment measures latency and processes feeds."""
    builder = StrategyBuilder()
    strategy = builder.assemble_strategy(symbol="EURUSD")
    env = SimulatedPaperEnvironment(strategy)

    # Mock a real-time observation feed row
    observation = {
        "open": 1.1020,
        "high": 1.1035,
        "low": 1.1015,
        "close": 1.1025,
        "volume": 2500,
        "sma_20": 1.1010,
        "ema_20": 1.1012,
        "rsi_14": 50.0
    }

    signal, latency = env.simulate_signal_execution(observation)
    assert latency >= 5.0
    assert len(env.latency_buffer) == 1


def test_phase11_and_12_production_monitor():
    """Verifies that ProductionMonitor detects drawdown thresholds and triggers retirement."""
    monitor = ProductionMonitor(drawdown_retirement_limit=10.0)

    # Safe Strategy
    snapshot_safe = monitor.track_metrics(
        strategy_id="Strategy_Safe",
        new_trades=5,
        current_drawdown=3.5,
        sharpe=2.4,
        drift=0.01
    )
    assert snapshot_safe.status == "Active"

    # Failing Strategy exceeding max drawdown limit of 10.0%
    snapshot_failed = monitor.track_metrics(
        strategy_id="Strategy_Bleeding",
        new_trades=2,
        current_drawdown=11.2,
        sharpe=-1.5,
        drift=0.85
    )
    assert snapshot_failed.status == "Retired"
