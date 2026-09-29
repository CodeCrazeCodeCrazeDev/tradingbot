"""Authoritative portfolio-state provider for canonical risk evaluation.

Derives cash, equity, exposure, open positions, daily PnL, and drawdown from
the typed trading repository (fills + positions) instead of letting
``CanonicalRiskService.evaluate_action`` fabricate ``equity=1.0`` /
``exposure=0.0`` defaults. There is intentionally no in-memory fallback:
if the repository cannot supply state the provider raises and the risk
service fails closed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from trading_bot.persistence.repositories import SqliteTradingRepository


class PortfolioStateProvider:
    """Compute a ``RiskState``-compatible mapping from persisted fills.

    Accounting model (average-cost, deterministic, side-agnostic):

    - ``cash`` = ``initial_equity`` - sum(buy cost) + sum(sell proceeds)
      - commissions.
    - ``equity`` = ``cash`` + sum(position market value). Positions are
      marked at the observation's ``price``/``close`` for the observed symbol;
      unmarked positions fall back to their average cost (neutral mark).
    - ``portfolio_exposure`` = sum(|qty| * mark) / equity. Returns 1.0 when
      equity <= 0 so the exposure check vetoes a bankrupt book.
    - ``daily_pnl`` = realized PnL from today's sell fills + unrealized PnL
      on open positions.
    - ``drawdown_fraction`` = (session peak - equity) / session peak.
    """

    def __init__(
        self,
        repository: SqliteTradingRepository,
        initial_equity: float = 10000.0,
        account_id: str = "runtime",
    ) -> None:
        self.repository = repository
        self.initial_equity = float(initial_equity)
        self.account_id = account_id
        self._peak_equity: Optional[float] = None

    async def portfolio_state(
        self, observation: Optional[Mapping[str, Any]] = None
    ) -> Dict[str, Any]:
        fills = await self.repository.list_fills()
        snapshot = await self.repository.snapshot(self.account_id)

        marks = self._marks(observation)
        today = datetime.now(timezone.utc).date().isoformat()

        cash = self.initial_equity
        daily_realized = 0.0
        book: Dict[str, list] = {}  # symbol -> [net_qty, avg_cost]
        for fill in fills:
            symbol = str(fill["symbol"])
            quantity = float(fill["quantity"])
            price = float(fill["price"])
            commission = float(fill.get("commission") or 0.0)
            qty, cost = book.get(symbol, [0.0, 0.0])
            if fill["side"] == "buy":
                cash -= quantity * price + commission
                net = qty + quantity
                book[symbol] = [
                    net,
                    (qty * cost + quantity * price) / net if net else price,
                ]
            else:
                cash += quantity * price - commission
                realized = quantity * (price - cost)
                if str(fill.get("occurred_at") or "").startswith(today):
                    daily_realized += realized
                book[symbol] = [qty - quantity, cost]

        position_value = 0.0
        exposure_notional = 0.0
        unrealized_pnl = 0.0
        open_positions = 0
        for position in snapshot.positions:
            symbol = position.instrument.symbol
            quantity = float(position.quantity)
            if quantity == 0:
                continue
            open_positions += 1
            # Prefer the provider's running average-cost basis (the
            # repository's stored average_price is first-fill semantics and
            # only resets at flat).
            cost = book.get(symbol, [None, float(position.average_price)])[1]
            mark = marks.get(symbol, float(cost))
            position_value += quantity * mark
            exposure_notional += abs(quantity) * mark
            unrealized_pnl += quantity * (mark - float(cost))

        equity = cash + position_value
        peak = self._peak_equity or self.initial_equity
        if equity > peak:
            peak = equity
        self._peak_equity = peak

        return {
            "account_id": self.account_id,
            "equity": equity,
            "cash": cash,
            "portfolio_exposure": (
                exposure_notional / equity if equity > 0 else 1.0
            ),
            "daily_pnl": daily_realized + unrealized_pnl,
            "drawdown_fraction": (
                (peak - equity) / peak if peak > 0 else 0.0
            ),
            "open_positions": open_positions,
        }

    @staticmethod
    def _marks(observation: Optional[Mapping[str, Any]]) -> Dict[str, float]:
        if not isinstance(observation, Mapping):
            return {}
        symbol = observation.get("symbol")
        price = observation.get("price", observation.get("close"))
        try:
            if symbol and price and float(price) > 0:
                return {str(symbol): float(price)}
        except (TypeError, ValueError):
            return {}
        return {}
