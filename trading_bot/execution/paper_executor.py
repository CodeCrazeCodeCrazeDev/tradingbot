from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""PaperExecutor – converts `Signal`s into simulated paper trades.

No orders are sent to the MT5 server; we simply compute position size via
`RiskManager`, record positions, and log the action. Useful for forward testing
and strategy validation.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from trading_bot.risk import RiskManager
from trading_bot.strategy.strategy_engine import Signal
from trading_bot.data import MT5Interface
from trading_bot.analytics import PerformanceAnalytics, Trade
import asyncio


@dataclass(slots=True)
class Position:
    ticket: int
    symbol: str
    direction: str  # "buy" | "sell"
    lot: float
    entry_price: float
    stop_loss: float
    take_profit: float
    time: float  # POSIX timestamp
    closed: bool = False
    exit_price: Optional[float] = None
    exit_time: Optional[float] = None
    profit: Optional[float] = None
    
    def to_trade(self) -> Trade:
        """Convert closed position to Trade for analytics."""
        try:
            if not self.closed or self.exit_price is None or self.exit_time is None or self.profit is None:
                raise ValueError("Cannot convert open position to Trade")
            return Trade(
                ticket=self.ticket,
                symbol=self.symbol,
                direction=self.direction,
                lot=self.lot,
                entry_price=self.entry_price,
                exit_price=self.exit_price,
                entry_time=self.time,
                exit_time=self.exit_time,
                profit=self.profit
            )
        except Exception as e:
            logger.error(f"Error in to_trade: {e}")
            raise


class PaperExecutor:  # noqa: B024 – simple executor
    """Execute signals in *paper* mode by logging simulated trades."""

    async def execute_trade(self, symbol: str = None, direction: int = None, size: float = None, signal=None, last_price=None):
        """Compatibility method for main.py: process a single trade signal.
        
        Supports two calling conventions:
        1. New: execute_trade(symbol=..., direction=..., size=...)
        2. Legacy: execute_trade(signal, last_price)
        """
        # New calling convention
        try:
            if symbol is not None and direction is not None and size is not None:
                logger.info(f"Paper trade executed: {symbol} {'BUY' if direction > 0 else 'SELL'} {size} lots")
                # Create a simulated position
                current_price = last_price if last_price else 1.0  # Fallback price
                pos = Position(
                    ticket=self._next_ticket,
                    symbol=symbol,
                    direction="buy" if direction > 0 else "sell",
                    lot=size,
                    entry_price=current_price,
                    stop_loss=current_price * 0.99 if direction > 0 else current_price * 1.01,
                    take_profit=current_price * 1.02 if direction > 0 else current_price * 0.98,
                    time=time.time()
                )
                self.positions.append(pos)
                self._next_ticket += 1
                return
        
            # Legacy calling convention
            if signal is not None:
                self.process([signal], last_price)
            else:
                logger.warning("execute_trade called with None signal.")
        except Exception as e:
            logger.error(f"Error in execute_trade: {e}")
            raise

    """Execute signals in *paper* mode by logging simulated trades."""

    def __init__(self, mt5i: MT5Interface, risk: RiskManager) -> None:
        try:
            self.mt5 = mt5i
            self.risk = risk
            self.positions: List[Position] = []
            self.closed_positions: List[Position] = []
            self._next_ticket = 1
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, signals: List[Signal], last_price: float) -> None:  # noqa: D401
        # First check existing positions for SL/TP hits
        try:
            self._update_positions(last_price)
            """Convert signals into positions using last market *price*."""
            if not signals:
                logger.debug("No signals to process.")
                return
            for sig in signals:
                if not self.risk.check_drawdown():
                    logger.warning("Trading halted due to drawdown exceeded.")
                    break
                size = self.risk.calc_position_size(sig.symbol, stop_loss_pips=sig.stop_loss_pips)
                if not hasattr(size, 'lot') or size.lot is None or size.lot <= 0:
                    logger.warning("Lot size zero – skip signal {}", sig)
                    continue
                if sig.direction == "buy":
                    sl_price = last_price - sig.stop_loss_pips * 0.0001
                    tp_price = last_price + sig.stop_loss_pips * sig.take_profit_rr * 0.0001
                else:
                    sl_price = last_price + sig.stop_loss_pips * 0.0001
                    tp_price = last_price - sig.stop_loss_pips * sig.take_profit_rr * 0.0001
                pos = Position(
                    self._next_ticket,
                    sig.symbol,
                    sig.direction,
                    size.lot,
                    last_price,
                    sl_price,
                    tp_price,
                    time.time(),
                )
                self.positions.append(pos)
                logger.success(
                    "PAPER ORDER #{:04d} {} {} lots @ {:.5f} SL {:.5f} TP {:.5f}",
                    pos.ticket,
                    pos.direction.upper(),
                    pos.lot,
                    pos.entry_price,
                    pos.stop_loss,
                    pos.take_profit,
                )
                self._next_ticket += 1
        except Exception as e:
            logger.error(f"Error in process: {e}")
            raise
            
    # ------------------------------------------------------------------
    # Position management
    # ------------------------------------------------------------------
    
    def _update_positions(self, current_price: float) -> None:
        """Check open positions against current price for SL/TP hits."""
        try:
            for pos in list(self.positions):  # Copy list as we'll modify during iteration
                # Check stop loss hit
                if (pos.direction == "buy" and current_price <= pos.stop_loss) or \
                   (pos.direction == "sell" and current_price >= pos.stop_loss):
                    self._close_position(pos, current_price, "stop loss")
                # Check take profit hit
                elif (pos.direction == "buy" and current_price >= pos.take_profit) or \
                     (pos.direction == "sell" and current_price <= pos.take_profit):
                    self._close_position(pos, current_price, "take profit")
        except Exception as e:
            logger.error(f"Error in _update_positions: {e}")
            raise
    
    def _close_position(self, position: Position, price: float, reason: str) -> None:
        """Close a position at the given price."""
        # Calculate profit
        try:
            pip_value = 0.0001
            pip_diff = abs(price - position.entry_price) / pip_value
            profit_sign = 1 if (
                (position.direction == "buy" and price > position.entry_price) or
                (position.direction == "sell" and price < position.entry_price)
            ) else -1
            # Simple profit calculation (lot size * pip difference * pip value in account currency)
            profit = profit_sign * pip_diff * position.lot * 10  # Assuming $10 per pip per lot
        
            # Update position
            position.closed = True
            position.exit_price = price
            position.exit_time = time.time()
            position.profit = profit
        
            # Move to closed positions
            self.positions.remove(position)
            self.closed_positions.append(position)
        
            logger.info(
                "PAPER CLOSE #{:04d} {} @ {:.5f} ({}) P/L: ${:.2f}",
                position.ticket,
                position.direction.upper(),
                price,
                reason,
                profit
            )
        except Exception as e:
            logger.error(f"Error in _close_position: {e}")
            raise
    
    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    
    def get_analytics(self) -> PerformanceAnalytics:
        """Return performance analytics for closed positions."""
        try:
            trades = [pos.to_trade() for pos in self.closed_positions]
            return PerformanceAnalytics(trades)
        except Exception as e:
            logger.error(f"Error in get_analytics: {e}")
            raise
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Return performance summary dictionary."""
        try:
            if not self.closed_positions:
                return {"trades": 0, "message": "No closed trades yet"}
            return self.get_analytics().summary()
        except Exception as e:
            logger.error(f"Error in get_performance_summary: {e}")
            raise
