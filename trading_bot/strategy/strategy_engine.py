from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""StrategyEngine – integrates market-structure, liquidity & risk modules.

Version 0.1 produces *signal objects* (not orders) so that higher-level
execution modules can decide whether to enter positions. Later versions will
embed multiple sub-strategies (Wyckoff, SMC, ICT, etc.).
"""

import datetime as _dt
from dataclasses import dataclass
from typing import List, Sequence

from loguru import logger

from trading_bot.analysis.liquidity import LiquidityAnalyzer, LiquidityGrab
from trading_bot.analysis.market_structure import MarketStructureAnalyzer, StructureEvent
from trading_bot.analysis.fvg import FVGDetector, FairValueGap
from trading_bot.analysis.order_block import OrderBlockDetector, OrderBlock
from trading_bot.analysis.wyckoff import WyckoffAnalyzer, WyckoffPhase
from trading_bot.data import MT5Interface
from trading_bot.risk import RiskManager

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Signal:
    """High-level trading signal produced by the strategy engine."""

    time: _dt.datetime
    symbol: str
    direction: str  # "buy" | "sell"
    rationale: str  # human-readable description
    stop_loss_pips: float
    take_profit_rr: float  # target RR (e.g., 2 = 1:2)
    confidence: float  # 0-100 scale


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class StrategyEngine:  # noqa: B024 – not for subclassing yet
    """Produce trade signals based on analyzers results."""

    def __init__(
        self,
        mt5i: MT5Interface,
        *,
        swing_len: int = 3,
        symbol: str = "EURUSD",
    ) -> None:
        self.mt5 = mt5i
        self.symbol = symbol
        self.msa = MarketStructureAnalyzer(swing_len=swing_len)
        self.lqa = LiquidityAnalyzer(swing_len=swing_len)
        self.fvg = FVGDetector()
        self.obd = OrderBlockDetector()
        self.wyckoff = WyckoffAnalyzer(lookback=50)
        self.risk = RiskManager(mt5i)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _get_bar_time(self, bars, idx: int):
        """Get timestamp from bar at index, handling both column and index-based time."""
        from datetime import datetime
        import pandas as _pd
        try:
            # Try index-based time first (DatetimeIndex)
            idx_val = bars.index[idx]
            if isinstance(idx_val, (_pd.Timestamp, datetime)):
                return idx_val.to_pydatetime() if hasattr(idx_val, 'to_pydatetime') else idx_val
            # Try 'time' column
            if 'time' in bars.columns:
                val = bars.iloc[idx]['time']
                if isinstance(val, (_pd.Timestamp, datetime)):
                    return val.to_pydatetime() if hasattr(val, 'to_pydatetime') else val
                # Handle numeric timestamps (epoch seconds)
                try:
                    return _pd.Timestamp(val, unit='s').to_pydatetime()
                except Exception:
                    pass
            # Handle numeric index as epoch timestamp
            try:
                return _pd.Timestamp(idx_val, unit='s').to_pydatetime()
            except Exception:
                pass
            # Fallback to current time
            return datetime.now()
        except Exception:
            return datetime.now()

    def analyse(self, bars) -> List[Signal]:  # noqa: ANN001 – dynamic type
        """Run analyzers on *bars* (DataFrame) and return list of *Signal* objects."""
        # Market structure
        structure_events: List[StructureEvent] = self.msa.detect_structure(bars)
        # Liquidity pools & grabs
        buy_pools, sell_pools = self.lqa.find_equal_highs_lows(bars)
        grabs: List[LiquidityGrab] = self.lqa.detect_grabs(bars, [*buy_pools, *sell_pools])
        # Extract highs and lows from structure events for Wyckoff analysis
        highs = [ev for ev in structure_events if ev.broken_swing and ev.broken_swing.kind == 'high']
        lows = [ev for ev in structure_events if ev.broken_swing and ev.broken_swing.kind == 'low']
        # Fair Value Gaps (unfilled)
        active_gaps: List[FairValueGap] = self.fvg.active_gaps(bars)
        # Order Blocks
        order_blocks: List[OrderBlock] = self.obd.from_bos(bars, structure_events)
        active_obs: List[OrderBlock] = self.obd.active_blocks(bars, order_blocks)
        # Wyckoff phase
        current_phase = self.wyckoff.detect_phase(bars)

        signals: list[Signal] = []

        # Simple heuristics for demonstration:
        for ev in structure_events[-3:]:  # look at latest few events
            if ev.event.name == "BOS" and ev.event.value == "BOS":
                direction = "buy" if ev.broken_swing.kind == "high" else "sell"
                rationale = f"BOS after {ev.broken_swing.kind} break"
                sl_pips = 15 if direction == "buy" else 20
                signals.append(
                    Signal(
                        self._get_bar_time(bars, ev.idx),
                        self.symbol,
                        direction,
                        rationale,
                        stop_loss_pips=sl_pips,
                        take_profit_rr=2,
                        confidence=70.0,
                    )
                )
        # FVG reaction trade – anticipate price returning into bullish/bearish gap boundary
        for gap in active_gaps[-2:]:
            direction = "buy" if gap.direction == "bull" else "sell"
            rationale = f"Unfilled {gap.direction} FVG ({gap.idx_start}-{gap.idx_end})"
            sl_pips = 12
            tp_rr = 2.0
            signals.append(
                Signal(
                    self._get_bar_time(bars, -1),
                    self.symbol,
                    direction,
                    rationale,
                    stop_loss_pips=sl_pips,
                    take_profit_rr=tp_rr,
                    confidence=55.0,
                )
            )

        # Order Block reaction trades – anticipate price returning to OB
        for ob in active_obs[-2:]:
            direction = "buy" if ob.direction == "bull" else "sell"
            rationale = f"Unmitigated {ob.direction} Order Block @ bar {ob.idx}"
            sl_pips = 12
            tp_rr = 2.5
            signals.append(
                Signal(
                    self._get_bar_time(bars, -1),
                    self.symbol,
                    direction,
                    rationale,
                    stop_loss_pips=sl_pips,
                    take_profit_rr=tp_rr,
                    confidence=60.0,
                )
            )

        # Wyckoff phase-based signals
        if current_phase == WyckoffPhase.ACCUMULATION:
            # Look for potential spring or test of support
            if len(lows) >= 2 and lows[-1].broken_swing.price < lows[-2].broken_swing.price * 0.9985:  # slight new low
                signals.append(
                    Signal(
                        self._get_bar_time(bars, -1),
                        self.symbol,
                        "buy",
                        f"Wyckoff Accumulation - potential spring",
                        stop_loss_pips=10,
                        take_profit_rr=3.0,
                        confidence=65.0,
                    )
                )
        elif current_phase == WyckoffPhase.DISTRIBUTION:
            # Look for potential upthrust or test of resistance
            if len(highs) >= 2 and highs[-1].broken_swing.price > highs[-2].broken_swing.price * 1.0015:  # slight new high
                signals.append(
                    Signal(
                        self._get_bar_time(bars, -1),
                        self.symbol,
                        "sell",
                        f"Wyckoff Distribution - potential upthrust",
                        stop_loss_pips=10,
                        take_profit_rr=3.0,
                        confidence=65.0,
                    )
                )

        # Liquidity grabs as contrarian scalp example
        for grab in grabs[-2:]:
            direction = "sell" if grab.pool.kind == "buy" else "buy"
            rationale = f"Liquidity grab of {grab.pool.kind}-side pool"
            sl_pips = 10
            signals.append(
                Signal(
                    self._get_bar_time(bars, grab.idx),
                    self.symbol,
                    direction,
                    rationale,
                    stop_loss_pips=sl_pips,
                    take_profit_rr=1.5,
                    confidence=60.0,
                )
            )

        logger.debug("Generated {} signals.", len(signals))
        return signals
