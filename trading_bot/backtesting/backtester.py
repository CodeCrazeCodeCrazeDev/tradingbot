from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""Simple bar-by-bar backtester for `StrategyEngine`.

This is **not** meant for high-performance research – just a functional tool to
verify logic across 5+ years of data. Replace with vectorised engine later.
"""

import datetime as _dt
from dataclasses import dataclass, field
from typing import List, Literal

import pandas as pd  # type: ignore
from loguru import logger

try:
    from trading_bot.strategy.strategy_engine import StrategyEngine
except ImportError:
    StrategyEngine = None

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


Direction = Literal["buy", "sell"]


@dataclass(slots=True)
class Trade:
    symbol: str
    direction: Direction
    entry_idx: int
    entry_time: float
    entry_price: float
    sl_price: float
    tp_price: float
    exit_idx: int | None = None
    exit_price: float | None = None
    exit_reason: str | None = None  # "tp" | "sl" | "end"

    def is_open(self) -> bool:
        return self.exit_idx is None

    def pnl(self) -> float:
        if self.exit_price is None:
            return 0.0
        delta = self.exit_price - self.entry_price
        return delta if self.direction == "buy" else -delta


@dataclass(slots=True)
class BacktestResult:
    trades: List[Trade] = field(default_factory=list)

    @property
    def n_trades(self) -> int:  # noqa: D401
        return len(self.trades)

    @property
    def win_rate(self) -> float:  # noqa: D401
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.exit_reason == "tp")
        return wins / len(self.trades) * 100

    @property
    def avg_pnl(self) -> float:  # noqa: D401
        if not self.trades:
            return 0.0
        return sum(t.pnl() for t in self.trades) / len(self.trades)


# ---------------------------------------------------------------------------
# Backtester
# ---------------------------------------------------------------------------


class Backtester:  # noqa: B024 – not for subclassing yet
    """Iterates over bar series, feeds data to StrategyEngine, simulates orders."""

    def __init__(
        self,
        bars: pd.DataFrame,
        strategy: StrategyEngine,
        lookback: int = 100,
    ) -> None:
        self.bars = bars.reset_index(drop=True)
        self.strategy = strategy
        self.lookback = lookback
        self.result = BacktestResult()
        self.open_trades: list[Trade] = []

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> BacktestResult:  # noqa: D401
        logger.info("Starting backtest – total bars: {}", len(self.bars))
        for i in range(self.lookback, len(self.bars)):
            window = self.bars.iloc[i - self.lookback : i + 1]
            signals = self.strategy.analyse(window)

            # Filter signals generated on current bar
            for sig in (s for s in signals if window.index[-1] == i):
                self._open_trade(sig, i)

            self._update_open_trades(i)
        # Close any remaining positions at last price
        last_idx = len(self.bars) - 1
        last_close = float(self.bars.iloc[last_idx].close)
        for t in self.open_trades:
            t.exit_idx = last_idx
            t.exit_price = last_close
            t.exit_reason = "end"
            self.result.trades.append(t)
        self.open_trades.clear()
        logger.success("Backtest finished – trades: {}, win-rate: {:.1f}%", self.result.n_trades, self.result.win_rate)
        return self.result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _open_trade(self, sig, idx: int) -> None:  # noqa: ANN001 – dynamic signal type
        bar = self.bars.iloc[idx]
        price = float(bar.close)
        if sig.direction == "buy":
            sl_price = price - sig.stop_loss_pips * 0.0001
            tp_price = price + sig.stop_loss_pips * sig.take_profit_rr * 0.0001
        else:
            sl_price = price + sig.stop_loss_pips * 0.0001
            tp_price = price - sig.stop_loss_pips * sig.take_profit_rr * 0.0001
        trade = Trade(
            sig.symbol,
            sig.direction,
            idx,
            float(bar.time),
            price,
            sl_price,
            tp_price,
        )
        self.open_trades.append(trade)

    def _update_open_trades(self, idx: int) -> None:
        bar = self.bars.iloc[idx]
        for trade in list(self.open_trades):
            if trade.direction == "buy":
                # SL
                if bar.low <= trade.sl_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.sl_price
                    trade.exit_reason = "sl"
                # TP
                elif bar.high >= trade.tp_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.tp_price
                    trade.exit_reason = "tp"
            else:  # sell
                if bar.high >= trade.sl_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.sl_price
                    trade.exit_reason = "sl"
                elif bar.low <= trade.tp_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.tp_price
                    trade.exit_reason = "tp"
            if not trade.is_open():
                self.open_trades.remove(trade)
                self.result.trades.append(trade)
