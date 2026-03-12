"""Unit tests for LiquidityAnalyzer."""
from __future__ import annotations

import time

import pandas as pd  # type: ignore

from trading_bot.analysis.liquidity import LiquidityAnalyzer, LiquidityPool
import pandas

import logging
from typing import Dict, List, Optional, Any, Tuple
logger = logging.getLogger(__name__)



def _make_equal_high_df() -> pd.DataFrame:  # noqa: D401
    now = time.time()
    prices = [1.2000, 1.2005, 1.2004, 1.2005, 1.2003]  # two equal-ish highs at 1.2005
    highs = [p + 0.0002 for p in prices]
    lows = [p - 0.0002 for p in prices]
    return pd.DataFrame(
        {
            "time": [now + i * 60 for i in range(len(prices))],
            "open": prices,
            "high": highs,
            "low": lows,
            "close": prices,
        }
    )


def test_equal_high_detection() -> None:
    df = _make_equal_high_df()
    lqa = LiquidityAnalyzer(swing_len=1, tolerance_pct=0.05)
    buy_pools, sell_pools = lqa.find_equal_highs_lows(df)
    assert buy_pools, "No buy-side liquidity pools detected"
    assert isinstance(buy_pools[0], LiquidityPool)


def test_liquidity_grab() -> None:
    df = _make_equal_high_df()
    # Manually add sweep bar that crosses above equal highs then closes below
    sweep_bar = {
        "time": time.time() + 6 * 60,
        "open": 1.2004,
        "high": 1.2010,
        "low": 1.1990,
        "close": 1.1995,
    }
    df = pd.concat([df, pd.DataFrame([sweep_bar])], ignore_index=True)

    lqa = LiquidityAnalyzer(swing_len=1, tolerance_pct=0.05)
    buy_pools, _ = lqa.find_equal_highs_lows(df)
    grabs = lqa.detect_grabs(df, buy_pools)
    assert grabs, "Liquidity grab not detected"
