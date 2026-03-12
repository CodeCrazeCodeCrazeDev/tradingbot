"""Performance analytics – summarise executed trades & equity curve."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd  # type: ignore
import datetime
import pandas

import logging
logger = logging.getLogger(__name__)



@dataclass(slots=True)
class Trade:
    """Represents a completed trade with entry and exit information.
    
    This class stores all relevant information about a trade including ticket number,
    symbol, direction, lot size, prices, timestamps, and profit/loss.
    """
    ticket: int
    symbol: str
    direction: str  # "buy" | "sell"
    lot: float
    entry_price: float
    exit_price: float
    entry_time: float  # POSIX
    exit_time: float  # POSIX
    profit: float  # profit in account currency

    @property
    def rr(self) -> float:
        """Return reward / risk ratio (absolute risk assumed at entry)."""
        try:
            risk = abs(self.entry_price - self.exit_price)
            if risk == 0:
                return 0.0
            return abs(self.profit) / risk
        except Exception as e:
            logger.error(f"Error in rr: {e}")
            raise


class PerformanceAnalytics:  # noqa: B024 – static helper
    """Compute summary statistics & equity curve from closed trades."""

    def __init__(self, trades: List[Trade]) -> None:
        try:
            self.trades = trades
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:  # noqa: D401
        """Return key metrics dict."""
        try:
            if not self.trades:
                return {}
            wins = [t for t in self.trades if t.profit > 0]
            losses = [t for t in self.trades if t.profit <= 0]
            gross_profit = sum(t.profit for t in wins)
            gross_loss = sum(t.profit for t in losses)
            total_net = gross_profit + gross_loss
            expectancy = total_net / len(self.trades)
            win_rate = len(wins) / len(self.trades) * 100.0
            avg_rr = sum(t.rr for t in self.trades) / len(self.trades)
            max_dd = self._max_drawdown()
            return {
                "trades": len(self.trades),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": round(win_rate, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_loss": round(gross_loss, 2),
                "net_profit": round(total_net, 2),
                "expectancy": round(expectancy, 2),
                "avg_rr": round(avg_rr, 2),
                "max_drawdown": round(max_dd, 2),
            }
        except Exception as e:
            logger.error(f"Error in summary: {e}")
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def equity_curve(self, start_balance: float = 10000) -> pd.DataFrame:
        """Return DataFrame with time & equity columns representing equity curve."""
        try:
            times = [t.exit_time for t in self.trades]
            pnl_cumsum = 0.0
            equities = []
            for t in self.trades:
                pnl_cumsum += t.profit
                equities.append(start_balance + pnl_cumsum)
            return pd.DataFrame({"time": times, "equity": equities})
        except Exception as e:
            logger.error(f"Error in equity_curve: {e}")
            raise

    def _max_drawdown(self) -> float:
        try:
            equity = 0.0
            peak = 0.0
            max_dd = 0.0
            for t in self.trades:
                equity += t.profit
                if equity > peak:
                    peak = equity
                dd = peak - equity
                if dd > max_dd:
                    max_dd = dd
            return max_dd
        except Exception as e:
            logger.error(f"Error in _max_drawdown: {e}")
            raise
