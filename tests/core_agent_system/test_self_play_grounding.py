import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading_bot.core_agent_system.self_play_loop import SelfPlayLoop

def create_valid_dataset():
    timestamps = [datetime(2026, 7, 30, 9, 0) + timedelta(minutes=i) for i in range(60)]
    return pd.DataFrame({
        "open": np.linspace(100, 105, 60),
        "high": np.linspace(101, 106, 60),
        "low": np.linspace(99, 104, 60),
        "close": np.linspace(100.5, 105.2, 60)
    }, index=timestamps)

def test_self_play_loop_valid_data_passes():
    loop = SelfPlayLoop()
    df = create_valid_dataset()
    # Should run without raising any exceptions
    loop.validate_market_data(df)

def test_self_play_loop_rejects_empty_data():
    loop = SelfPlayLoop()
    with pytest.raises(ValueError) as exc:
        loop.validate_market_data(pd.DataFrame())
    assert "Dataset is empty" in str(exc.value)

def test_self_play_loop_rejects_unsorted_timestamps():
    loop = SelfPlayLoop()
    df = create_valid_dataset()
    # Unsort index
    unsorted_idx = list(df.index)
    unsorted_idx[0], unsorted_idx[-1] = unsorted_idx[-1], unsorted_idx[0]
    df.index = unsorted_idx

    with pytest.raises(ValueError) as exc:
        loop.validate_market_data(df)
    assert "not sorted monotonically" in str(exc.value)

def test_self_play_loop_rejects_nan_heavy_data():
    loop = SelfPlayLoop()
    df = create_valid_dataset()
    # Inject heavy NaNs into close column (e.g. 50%)
    df.loc[df.index[:30], "close"] = np.nan

    with pytest.raises(ValueError) as exc:
        loop.validate_market_data(df)
    assert "High NaN density in column" in str(exc.value)

def test_self_play_loop_rejects_impossible_prices():
    loop = SelfPlayLoop()
    df = create_valid_dataset()
    # Inject a zero price
    df.loc[df.index[5], "close"] = 0.0

    with pytest.raises(ValueError) as exc:
        loop.validate_market_data(df)
    assert "Impossible prices" in str(exc.value)

def test_self_play_loop_rejects_unrealistic_spreads():
    loop = SelfPlayLoop()
    df = create_valid_dataset()
    # High price less than low price
    df.loc[df.index[5], "high"] = 90.0
    df.loc[df.index[5], "low"] = 100.0

    with pytest.raises(ValueError) as exc:
        loop.validate_market_data(df)
    assert "Unrealistic spreads" in str(exc.value)
