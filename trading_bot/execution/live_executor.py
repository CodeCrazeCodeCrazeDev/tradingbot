from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""LiveExecutor – sends real orders to MT5 via `MT5Interface`.

!!! USE WITH CAUTION !!!

Orders are sent using `MT5Interface.place_order()`. The executor relies on the
configuration in `config.yaml` and the risk-manager for position sizing.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from trading_bot.data import MT5Interface
from trading_bot.analytics import PerformanceAnalytics, Trade
from trading_bot.risk import RiskManager
from trading_bot.strategy.strategy_engine import Signal
from trading_bot.validation.trade_validator import TradeValidator, ValidationError


@dataclass(slots=True)
class LivePosition:
    ticket: int
    symbol: str
    direction: str
    lot: float
    entry_price: float
    sl: float
    tp: float
    time_open: float


class LiveExecutor:  # noqa: B024 – simple orchestrator
    """Convert `Signal`s into market/limit orders on the real account."""

    def __init__(self, mt5i: MT5Interface, risk: RiskManager) -> None:
        self.mt5 = mt5i
        self.risk = risk
        self.validator = TradeValidator()  # Add trade validator
        self.closed_positions: List[Dict[str, Any]] = []
        self.positions: List[LivePosition] = []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_position_status(self) -> None:
        """Check status of open positions."""
        # Get all positions from MT5
        positions = self.mt5.get_positions()
        
        # Check for closed positions
        for pos in positions:
            if pos.ticket in [p["ticket"] for p in self.closed_positions]:
                continue  # Already processed
                
            if pos.profit != 0:  # Position closed with profit/loss
                # Record the closed position
                self.closed_positions.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "direction": "buy" if pos.type == 0 else "sell",
                    "lot": pos.volume,
                    "entry_price": pos.price_open,
                    "exit_price": pos.price_current,
                    "entry_time": pos.time,
                    "exit_time": time.time(),
                    "profit": pos.profit
                })
                
                logger.info(
                    "LIVE CLOSE #{} {} @ {:.5f} P/L: ${:.2f}",
                    pos.ticket,
                    "BUY" if pos.type == 0 else "SELL",
                    pos.price_current,
                    pos.profit
                )

    def _track_position(self, ticket: int, symbol: str, direction: str, 
                       lot: float, price: float, sl: float, tp: float) -> None:
        """Track a new position for analytics."""
        # Add to tracked positions
        self.positions.append(LivePosition(
            ticket=ticket,
            symbol=symbol,
            direction=direction,
            lot=lot,
            price=price,
            sl=sl,
            tp=tp,
            time_open=time.time()
        ))

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    
    def get_analytics(self) -> PerformanceAnalytics:
        """Return performance analytics for closed positions."""
        trades = []
        for pos in self.closed_positions:
            trades.append(Trade(
                ticket=pos["ticket"],
                symbol=pos["symbol"],
                direction=pos["direction"],
                lot=pos["lot"],
                entry_price=pos["entry_price"],
                exit_price=pos["exit_price"],
                entry_time=pos["entry_time"],
                exit_time=pos["exit_time"],
                profit=pos["profit"]
            ))
        return PerformanceAnalytics(trades)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Return performance summary dictionary."""
        if not self.closed_positions:
            return {"trades": 0, "message": "No closed trades yet"}
        return self.get_analytics().summary()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, signals: List[Signal], last_price: float) -> None:  # noqa: D401
        # Check existing positions first
        self._check_position_status()
        
        if not signals:
            logger.debug("No live signals to process.")
            return
        for sig in signals:
            if not self.risk.check_drawdown():
                logger.warning("Trading halted due to drawdown limit.")
                break
            size = self.risk.calc_position_size(sig.symbol, stop_loss_pips=sig.stop_loss_pips)
            if size.lot <= 0:
                logger.warning("Lot size <=0. Skip live order for {}", sig)
                continue
            if sig.direction == "buy":
                sl_price = last_price - sig.stop_loss_pips * 0.0001
                tp_price = last_price + sig.stop_loss_pips * sig.take_profit_rr * 0.0001
                order_type = 0  # mt5.ORDER_TYPE_BUY
                direction = "buy"
            else:
                pass
            try:
                sl_price = last_price + sig.stop_loss_pips * 0.0001
                tp_price = last_price - sig.stop_loss_pips * sig.take_profit_rr * 0.0001
                direction = "sell"
            
            # CRITICAL: Validate trade parameters before execution
                acc = self.mt5.account_info()
                self.validator.validate_trade(
                    symbol=sig.symbol,
                    lot=size.lot,
                    price=last_price,
                    sl=sl_price,
                    tp=tp_price,
                    account_equity=acc.equity if acc else 10000,
                    current_market_price=last_price
                )
            except ValidationError as e:
                logger.error(f"Trade validation failed: {e}")
                continue  # Skip this trade

            # Send order to MT5
            ticket = self.mt5.place_order(
                symbol=sig.symbol,
                order_type=direction,
                lot=size.lot,
                price=last_price,
                sl_price=sl_price,
                tp_price=tp_price,
            )

            logger.success(
                "LIVE ORDER {} {} lots @ {:.5f} SL {:.5f} TP {:.5f} (ticket: {})",
                direction.upper(),
                size.lot,
                last_price,
                sl_price,
                tp_price,
                ticket,
            )
            
            # Track the position for analytics
            self._track_position(ticket, sig.symbol, direction, size.lot, last_price, sl_price, tp_price)
