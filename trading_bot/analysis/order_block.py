"""Order Block (OB) detection helper.

Simplified logic:
    • For each Break of Structure (BOS) event, locate the *last* candle in the
      opposite colour immediately prior to the break. That candle is the
      presumptive order block.
    • Bullish OB: last red/down candle before bullish BOS.
    • Bearish OB: last green/up candle before bearish BOS.

Qualification criteria (subset of advanced rules):
    1. Must be the last opposite9-direction candle before BOS.
    2. Candle body should cover at least 40% of its range (avoid dojis).
    3. FVG or imbalance is NOT enforced at this level (handled separately).

Outputs list of *OrderBlock* dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

import pandas as pd  # type: ignore

from trading_bot.analysis.market_structure import StructureEvent, StructureType, Trend, MarketStructureAnalyzer
import pandas

import logging
logger = logging.getLogger(__name__)



@dataclass(slots=True)
class OrderBlock:
    idx: int  # bar index of OB candle
    direction: str  # "bull" | "bear"
    high: float
    low: float
    bos_idx: int  # corresponding BOS bar index


class OrderBlockDetector:  # noqa: B024
    """Detect simple order blocks from BOS events."""

    def from_bos(self, df: pd.DataFrame, events: List[StructureEvent]) -> List[OrderBlock]:  # noqa: D401
        try:
            obs: list[OrderBlock] = []
            for ev in events:
                if ev.event != StructureType.BOS:
                    continue
                bos_idx = ev.idx
                if ev.broken_swing.kind == "high":  # bearish BOS (price moved down)
                    # find last green (close>open) candle before BOS
                    for j in range(bos_idx - 1, 1, -1):
                        row = df.iloc[j]
                        if row.close > row.open:  # green/up candle
                            body = abs(row.close - row.open)
                            rng = row.high - row.low
                            if rng == 0 or body / rng < 0.4:  # avoid doji
                                continue
                            obs.append(OrderBlock(j, "bear", row.high, row.low, bos_idx))
                            break
                else:  # bullish BOS (price moved up)
                    for j in range(bos_idx - 1, 1, -1):
                        row = df.iloc[j]
                        if row.close < row.open:  # red/down candle
                            body = abs(row.close - row.open)
                            rng = row.high - row.low
                            if rng == 0 or body / rng < 0.4:
                                continue
                            obs.append(OrderBlock(j, "bull", row.high, row.low, bos_idx))
                            break
            return obs
        except Exception as e:
            logger.error(f"Error in from_bos: {e}")
            raise

    def active_blocks(self, df: pd.DataFrame, obs: List[OrderBlock]) -> List[OrderBlock]:  # noqa: D401
        """Return order blocks price has not mitigated yet."""
        try:
            active: list[OrderBlock] = []
            last_close = float(df.iloc[-1].close)
            for ob in obs:
                if ob.direction == "bull" and last_close > ob.low:  # still above OB, not mitigated
                    active.append(ob)
                elif ob.direction == "bear" and last_close < ob.high:
                    active.append(ob)
            return active
        except Exception as e:
            logger.error(f"Error in active_blocks: {e}")
            raise
