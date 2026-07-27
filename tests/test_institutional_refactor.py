"""
Tests validating Institutional Quantitative Refactoring.
Verifies data pre-flight validation, spread/slippage costs, and hard risk limits.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from trading_bot.data.validate import DataValidator
from trading_bot.backtesting.advanced_backtester import InstitutionalBacktester, InstitutionalTrade
from trading_bot.strategy.strategy_engine import StrategyEngine, Signal


@pytest.fixture
def sample_ohlcv_data():
    """Generates a clean synthetic DatetimeIndex OHLCV DataFrame."""
    dates = [datetime(2026, 1, 1) + timedelta(minutes=15 * i) for i in range(100)]
    np.random.seed(42)
    close_prices = 1.1000 + np.cumsum(np.random.normal(0, 0.001, 100))
    open_prices = close_prices - np.random.normal(0, 0.0002, 100)
    high_prices = np.maximum(open_prices, close_prices) + 0.0005
    low_prices = np.minimum(open_prices, close_prices) - 0.0005
    volume = np.random.randint(1000, 5000, 100)

    df = pd.DataFrame({
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volume
    }, index=pd.DatetimeIndex(dates))

    # Mock technical indicator columns expected by StrategyEngine TIA
    df["sma_20"] = df["close"].rolling(20).mean()
    df["ema_20"] = df["close"].rolling(20).mean()
    df["rsi_14"] = 50.0
    return df


def test_data_pre_flight_validation_clean(sample_ohlcv_data):
    """Verifies that a correct and clean DataFrame passes validation."""
    validator = DataValidator()
    is_valid, report = validator.validate_dataframe(sample_ohlcv_data)
    assert is_valid is True
    assert report["total_records"] == 100
    assert report["bad_ticks_count"] == 0


def test_data_pre_flight_validation_look_ahead(sample_ohlcv_data):
    """Verifies that validation flags leaky columns / look-ahead bias."""
    leaky_df = sample_ohlcv_data.copy()
    leaky_df["future_close"] = leaky_df["close"].shift(-1)

    validator = DataValidator()
    is_valid, report = validator.validate_dataframe(leaky_df)
    assert is_valid is False
    assert report["look_ahead_violations"] > 0
    assert "Possible look-ahead bias" in report["errors"][0]


def test_data_pre_flight_validation_bad_ticks(sample_ohlcv_data):
    """Verifies that bad ticks (negative values or high < low) are flagged."""
    corrupted_df = sample_ohlcv_data.copy()
    corrupted_df.iloc[5, corrupted_df.columns.get_loc("high")] = 0.5  # lower than low

    validator = DataValidator()
    is_valid, report = validator.validate_dataframe(corrupted_df)
    assert is_valid is False
    assert report["bad_ticks_count"] > 0


def test_volatility_circuit_breaker(sample_ohlcv_data):
    """Verifies that the strategy engine blocks signals if volatility exceeds threshold."""
    # Create high-volatility dataset
    np.random.seed(1234)
    dates = [datetime(2026, 1, 1) + timedelta(minutes=15 * i) for i in range(50)]
    high_vol_closes = 1.1000 + np.cumsum(np.random.normal(0, 0.05, 50))  # extremely volatile
    high_vol_df = pd.DataFrame({
        "open": high_vol_closes - 0.01,
        "high": high_vol_closes + 0.02,
        "low": high_vol_closes - 0.02,
        "close": high_vol_closes,
        "volume": 2000
    }, index=pd.DatetimeIndex(dates))

    # Instantiate engine with standard config
    config = {
        "risk_limits": {
            "max_volatility_threshold": 0.03,  # Strict threshold
            "max_spread_pips_limit": 2.5
        }
    }

    # We pass None as MT5 interface because we aren't using live functions during pure analysis
    engine = StrategyEngine(None, swing_len=3, symbol="EURUSD", config=config)
    signals = engine.analyse(high_vol_df)

    # High volatility triggers circuit breaker, so output should be empty list
    assert len(signals) == 0


def test_institutional_backtester_costs(sample_ohlcv_data):
    """Verifies that InstitutionalBacktester applies execution costs correctly."""
    # Define custom high-cost config
    config = {
        "execution_cost": {
            "commission_per_million_usd": 15.0,
            "fixed_commission_per_trade": 10.0,  # $10 high fixed fee
            "default_spread_pips": 2.0,           # Wide 2 pip spread
            "default_slippage_pips": 1.0          # High slippage
        },
        "risk_limits": {
            "max_positions": 5,
            "max_spread_pips_limit": 5.0
        },
        "objectives": {
            "target_sharpe": 1.5,
            "max_drawdown_pct": 15.0
        }
    }

    engine = StrategyEngine(None, swing_len=3, symbol="EURUSD", config=config)
    backtester = InstitutionalBacktester(sample_ohlcv_data, engine, config=config, lookback=20)

    result = backtester.run()

    # Ensure performance and objective metrics were populated
    assert isinstance(result.max_drawdown_pct, float)
    assert isinstance(result.sharpe_ratio, float)

    # Check that cost tracking was applied
    if len(result.trades) > 0:
        first_trade = result.trades[0]
        assert first_trade.spread_paid_pips == 2.0
        assert first_trade.slippage_paid_pips >= 1.0
        assert first_trade.commission_paid_usd == 10.0
        assert result.total_commission_paid >= 10.0
