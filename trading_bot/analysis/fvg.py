"""Fair Value Gap (FVG) detection helper.

Very simplified implementation:
    • Bullish FVG: high of bar *i* < low of bar *i+2* (gap up)
    • Bearish FVG: low of bar *i* > high of bar *i+2* (gap down)

Returns list of *FairValueGap* dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd  # type: ignore
import pandas

import logging
logger = logging.getLogger(__name__)



@dataclass(slots=True)
class FairValueGap:
    idx_start: int  # index of first candle in gap window (i)
    idx_end: int  # index of third candle (i+2)
    direction: str  # "bull" | "bear"
    upper: float  # upper boundary of gap
    lower: float  # lower boundary


class FVGDetector:  # noqa: B024
    """Detect simple 3‐bar fair value gaps."""

    def find_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:  # noqa: D401
        try:
            gaps: list[FairValueGap] = []
            for i in range(len(df) - 2):
                h0 = float(df.iloc[i].high)
                l2 = float(df.iloc[i + 2].low)
                l0 = float(df.iloc[i].low)
                h2 = float(df.iloc[i + 2].high)
                # Bullish
                if h0 < l2:
                    gaps.append(FairValueGap(i, i + 2, "bull", upper=l2, lower=h0))
                # Bearish
                elif l0 > h2:
                    gaps.append(FairValueGap(i, i + 2, "bear", upper=l0, lower=h2))
            return gaps
        except Exception as e:
            logger.error(f"Error in find_gaps: {e}")
            raise

    def active_gaps(self, df: pd.DataFrame, min_idx: int | None = None) -> List[FairValueGap]:
        """Return gaps that are still unfilled up to last bar."""
        try:
            gaps = self.find_gaps(df)
            last_close = float(df.iloc[-1].close)
            active: list[FairValueGap] = []
            for g in gaps:
                if min_idx is not None and g.idx_end < min_idx:
                    continue
                if not (g.lower <= last_close <= g.upper):
                    # still gap – not yet filled
                    active.append(g)
            return active
        except Exception as e:
            logger.error(f"Error in active_gaps: {e}")
            raise
