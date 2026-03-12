"""Unit tests for MarketStructureAnalyzer."""
from __future__ import annotations

import time

import pandas as pd  # type: ignore

from trading_bot.analysis.market_structure import MarketStructureAnalyzer, StructureType
import pandas

import logging
from typing import Dict, List, Optional, Any, Tuple
logger = logging.getLogger(__name__)



def _generate_trend(n: int = 30, start_price: float = 1.1000) -> pd.DataFrame:  # noqa: D401
    """Return simple uptrend DataFrame with higher highs / lows."""
    prices = [start_price + i * 0.0005 for i in range(n)]
    return pd.DataFrame(
        {
            "time": [time.time() + i * 60 for i in range(n)],
            "open": prices,
            "high": [p + 0.0003 for p in prices],
            "low": [p - 0.0003 for p in prices],
            "close": prices,
        }
    )


def test_detect_swings() -> None:
    """Test that the MarketStructureAnalyzer can detect swing highs and lows in a trend."""
    df = _generate_trend()
    msa = MarketStructureAnalyzer(swing_len=2)
    highs, lows = msa.find_swings(df)
    # Expect at least one swing high & low in generated trend
    assert highs, "No swing highs detected"
    assert lows, "No swing lows detected"


def test_structure_events() -> None:
    """Test that the MarketStructureAnalyzer can detect Break of Structure (BOS) events in a trend."""
    df = _generate_trend()
    msa = MarketStructureAnalyzer(swing_len=2)
    events = msa.detect_structure(df)
    # We expect one or more BOS events in a clear trend
    bos = [e for e in events if e.event == StructureType.BOS]
    assert bos, "No BOS events detected in uptrend"
