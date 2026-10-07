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
    - ``daily_pnl`` = realized PnL from today's position-reducing fills
      (either direction) + unrealized PnL on open positions.
    - ``drawdown_fraction`` = (peak equity - equity) / peak equity. Peak is
      persisted in the repository so drawdown survives restarts.
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

    async def _peak(self, equity: float) -> float:
        """Durable peak-equity high-water mark (survives process restarts)."""
        if self._peak_equity is None:
            stored = await self.repository.get_account_state(
                f"peak_equity:{self.account_id}")
            try:
                self._peak_equity = (
                    max(float(stored), self.initial_equity)
                    if stored is not None else self.initial_equity
                )
            except (TypeError, ValueError):
                self._peak_equity = self.initial_equity
        if equity > self._peak_equity:
            self._peak_equity = equity
            await self.repository.set_account_state(
                f"peak_equity:{self.account_id}", repr(equity))
        return self._peak_equity

    async def portfolio_state(
        self, observation: Optional[Mapping[str, Any]] = None
    ) -> Dict[str, Any]:
        fills = await self.repository.list_fills()
        snapshot = await self.repository.snapshot(self.account_id)

        marks = self._marks(observation)
        today = datetime.now(timezone.utc).date().isoformat()

        cash = self.initial_equity
        daily_realized = 0.0
        book: Dict[str, list] = {}  # symbol -> [signed_qty, avg_cost]
        for fill in fills:
            symbol = str(fill["symbol"])
            quantity = float(fill["quantity"])
            price = float(fill["price"])
            commission = float(fill.get("commission") or 0.0)
            qty, cost = book.get(symbol, [0.0, 0.0])
            signed = quantity if fill["side"] == "buy" else -quantity
            realized = 0.0
            if qty == 0:
                book[symbol] = [signed, price]
            elif qty * signed > 0:
                net = qty + signed
                book[symbol] = [net, (qty * cost + signed * price) / net]
            else:
                # Reducing or flipping: realized PnL on the closed portion,
                # computed symmetrically for long and short books.
                closed = min(abs(signed), abs(qty))
                realized = closed * (price - cost) * (1.0 if qty > 0 else -1.0)
                net = qty + signed
                book[symbol] = [
                    net,
                    cost if (qty * net > 0) else (price if net != 0 else 0.0),
                ]
            if signed > 0:
                cash -= quantity * price + commission
            else:
                cash += quantity * price - commission
            if realized and str(fill.get("occurred_at") or "").startswith(today):
                daily_realized += realized

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
            # The repository's positions row already carries the corrected
            # average-cost basis (weighted add / keep-on-reduce / reset on
            # flip), so the provider folds only the cash and realized-PnL
            # streams above rather than duplicating the basis rule.
            cost = float(position.average_price)
            mark = marks.get(symbol, cost)
            position_value += quantity * mark
            exposure_notional += abs(quantity) * mark
            unrealized_pnl += quantity * (mark - cost)

        equity = cash + position_value
        peak = await self._peak(equity)

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


class VenueBackedStateProvider(PortfolioStateProvider):
    """Portfolio state sourced from the connected venue's account.

    The ledger cash model (``cash -= qty * price``) is a spot-equity model;
    margin venues like MT5 move cash only on realized PnL and carry positions
    at full notional * contract_size. For ``mt5_demo`` this provider takes
    equity/balance/margin/positions from the venue account and applies the
    contract spec when computing exposure, while still deriving daily
    realized PnL and the peak-equity watermark from the durable ledger.
    """

    def __init__(self, repository: SqliteTradingRepository,
                 adapter: Any, **kwargs: Any) -> None:
        super().__init__(repository, **kwargs)
        self._adapter = adapter

    async def portfolio_state(
        self, observation: Optional[Mapping[str, Any]] = None
    ) -> Dict[str, Any]:
        client = getattr(self._adapter, "_client", None)
        info = client.account_info() if client is not None else None
        if info is None:
            raise RuntimeError("venue account_info unavailable — fail closed")
        equity = float(getattr(info, "equity", 0.0))
        balance = float(getattr(info, "balance", equity))

        marks = self._marks(observation)
        positions = await self._adapter.get_positions()
        exposure_notional = 0.0
        unrealized_pnl = 0.0
        open_positions = 0
        for position in positions:
            qty = float(position.quantity)
            if qty == 0:
                continue
            open_positions += 1
            cs = float(position.instrument.contract_size or 1.0)
            mark = marks.get(position.instrument.symbol,
                             float(position.average_price))
            exposure_notional += abs(qty) * mark * cs
            unrealized_pnl += float(position.unrealized_pnl or 0.0)

        # Daily realized PnL still folds from the durable ledger — the venue
        # does not expose a daily cutoff without a history query.
        fills = await self.repository.list_fills()
        today = datetime.now(timezone.utc).date().isoformat()
        book: Dict[str, list] = {}
        daily_realized = 0.0
        for fill in fills:
            symbol = str(fill["symbol"])
            quantity = float(fill["quantity"])
            price = float(fill["price"])
            qty, cost = book.get(symbol, [0.0, 0.0])
            signed = quantity if fill["side"] == "buy" else -quantity
            realized = 0.0
            if qty == 0:
                book[symbol] = [signed, price]
            elif qty * signed > 0:
                net = qty + signed
                book[symbol] = [net, (qty * cost + signed * price) / net]
            else:
                closed = min(abs(signed), abs(qty))
                realized = closed * (price - cost) * (1.0 if qty > 0 else -1.0)
                net = qty + signed
                book[symbol] = [
                    net,
                    cost if (qty * net > 0) else (price if net != 0 else 0.0),
                ]
            if realized and str(fill.get("occurred_at") or "").startswith(today):
                daily_realized += realized

        peak = await self._peak(equity)
        return {
            "account_id": self.account_id,
            "equity": equity,
            "cash": balance,
            "portfolio_exposure": (
                exposure_notional / equity if equity > 0 else 1.0),
            "daily_pnl": daily_realized + unrealized_pnl,
            "drawdown_fraction": (
                (peak - equity) / peak if peak > 0 else 0.0),
            "open_positions": open_positions,
        }
        price = observation.get("price", observation.get("close"))
        try:
            if symbol and price and float(price) > 0:
                return {str(symbol): float(price)}
        except (TypeError, ValueError):
            return {}
        return {}
