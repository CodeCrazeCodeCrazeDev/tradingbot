"""Canonical execution service and reference paper broker adapter."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from trading_bot.foundation.contracts import (
    ExecutionReport,
    Fill,
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderType,
    OrderStatus,
    OrderUpdate,
    PortfolioSnapshot,
    Position,
    ReconciliationResult,
)
from trading_bot.foundation.ports import BrokerAdapter


class PaperBrokerAdapter:
    """Deterministic paper adapter used by replay and local development.

    Cost model is explicit and configurable: market orders pay the quoted
    half-spread plus ``slippage_bps`` adverse shift against the reference
    mark, then ``commission_per_unit`` per quantity unit. LIMIT orders rest
    until the mark crosses the limit price (sell) or touches it (buy is
    marketable only when mark <= limit); ``on_mark`` feeds the venue book
    each cycle so resting orders fill on later bars, never retroactively.
    Unsupported order types are rejected rather than simulated incorrectly.
    """

    venue_id = "paper"

    def __init__(
        self,
        spread_bps: float = 1.0,
        slippage_bps: float = 0.0,
        commission_per_unit: float = 0.0,
        latency_cycles: int = 0,
    ) -> None:
        self.spread_bps = max(float(spread_bps), 0.0)
        self.slippage_bps = max(float(slippage_bps), 0.0)
        self.commission_per_unit = max(float(commission_per_unit), 0.0)
        # Cycles a submitted order waits before it can fill. Default 0 keeps
        # the historical same-mark fill; set 1 for next-bar execution.
        self.latency_cycles = max(int(latency_cycles), 0)
        self._reports: Dict[str, ExecutionReport] = {}
        self._positions: Dict[str, Position] = {}
        self._marks: Dict[str, float] = {}
        self._resting: Dict[str, OrderRequest] = {}
        self._pending_market: List[str] = []
        self.connected = False
        self.market_data_source = "unknown"

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    def rehydrate(self, order_rows: List[Dict[str, Any]]) -> None:
        """Rebuild venue state from the durable ledger on restart.

        The paper venue is the ledger: positions, prior reports, and still
        resting/pending orders all persist in SQLite, so a restart must
        reproduce them — otherwise reconciliation compares a fresh empty
        book against a non-flat ledger and (correctly) fails closed forever.
        """
        from trading_bot.persistence.repositories import (
            decode_order, decode_report)
        terminal = {"filled", "cancelled", "rejected", "expired"}
        for row in order_rows:
            report_payload = row.get("report_json")
            if report_payload:
                report = decode_report(report_payload)
                self._reports[report.client_order_id] = report
                for fill in report.fills or []:
                    self._apply_fill(fill)
            if str(row.get("status", "")).lower() not in terminal:
                order = decode_order(row["order_json"])
                self._resting[order.client_order_id] = order
                if order.order_type is OrderType.MARKET:
                    self._pending_market.append(order.client_order_id)

    def on_mark(self, symbol: str, mark: float) -> None:
        """Feed the venue a new price; fills resting/pending orders."""
        if mark <= 0:
            return
        self._marks[str(symbol)] = float(mark)
        for client_order_id in list(self._pending_market):
            order = self._resting.pop(client_order_id, None)
            self._pending_market.remove(client_order_id)
            if order is not None:
                report = self._fill(order, self._marks[order.instrument.symbol])
                self._reports[client_order_id] = report
        for client_order_id, order in list(self._resting.items()):
            if order.order_type != OrderType.MARKET:
                if self._limit_marketable(order, self._marks[order.instrument.symbol]):
                    report = self._fill(order, order.price)
                    self._reports[client_order_id] = report
                    del self._resting[client_order_id]

    def _limit_marketable(self, order: OrderRequest, mark: float) -> bool:
        return (order.price >= mark) if order.side is OrderSide.BUY else (order.price <= mark)

    def _fill_price(self, order: OrderRequest, mark: float) -> float:
        adverse = (self.spread_bps / 2.0 + self.slippage_bps) * 1e-4
        price = (mark * (1.0 + adverse) if order.side is OrderSide.BUY
                 else mark * (1.0 - adverse))
        if order.order_type is OrderType.LIMIT and order.price is not None:
            # A limit fill can never be worse than the limit price.
            price = (min(price, order.price) if order.side is OrderSide.BUY
                     else max(price, order.price))
        return price

    def _fill(self, order: OrderRequest, mark: float) -> ExecutionReport:
        fill_price = self._fill_price(order, mark)
        fill = Fill(
            client_order_id=order.client_order_id,
            venue_order_id=f"paper-{order.client_order_id}",
            instrument=order.instrument,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=order.quantity * self.commission_per_unit,
            execution_reference={
                "schema": "paper_fill_v1",
                "mark_price": mark,
                "spread_bps": self.spread_bps,
                "slippage_bps": self.slippage_bps,
                "commission_per_unit": self.commission_per_unit,
                "order_type": order.order_type.value,
                "baseline_id": "always_long_same_fills_v1",
                "market_data_source": self.market_data_source,
            },
        )
        update = OrderUpdate(
            client_order_id=order.client_order_id,
            status=OrderStatus.FILLED,
            venue_order_id=fill.venue_order_id,
            filled_quantity=fill.quantity,
            average_price=fill_price,
        )
        slippage = (
            (fill_price - order.price) / order.price * 1e4
            if order.price and order.price > 0 else 0.0
        )
        self._apply_fill(fill)
        return ExecutionReport(
            client_order_id=order.client_order_id,
            status=OrderStatus.FILLED,
            updates=[update],
            fills=[fill],
            expected_price=order.price,
            slippage_bps=slippage,
        )

    async def submit_order(self, order: OrderRequest) -> ExecutionReport:
        existing = self._reports.get(order.client_order_id)
        if existing is not None:
            return existing

        if order.price is None or order.price <= 0:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error="Paper execution requires a positive reference price",
            )
            self._reports[order.client_order_id] = report
            return report

        mark = self._marks.get(order.instrument.symbol, order.price)
        if order.order_type not in (OrderType.MARKET, OrderType.LIMIT):
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=f"Paper venue does not support order type {order.order_type.value}",
            )
            self._reports[order.client_order_id] = report
            return report
        if order.order_type is OrderType.LIMIT and not self._limit_marketable(order, mark):
            # Resting order: acknowledged now, filled only when the mark
            # actually reaches the limit — no fabrication of fills.
            self._resting[order.client_order_id] = order
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.ACCEPTED,
                updates=[OrderUpdate(
                    client_order_id=order.client_order_id,
                    status=OrderStatus.ACCEPTED)],
                expected_price=order.price,
            )
            self._reports[order.client_order_id] = report
            return report
        if self.latency_cycles > 0:
            self._resting[order.client_order_id] = order
            self._pending_market.append(order.client_order_id)
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.ACCEPTED,
                updates=[OrderUpdate(
                    client_order_id=order.client_order_id,
                    status=OrderStatus.ACCEPTED)],
                expected_price=order.price,
            )
            self._reports[order.client_order_id] = report
            return report
        report = self._fill(order, mark)
        self._reports[order.client_order_id] = report
        return report

    async def cancel_order(self, client_order_id: str) -> bool:
        resting = self._resting.pop(client_order_id, None)
        if resting is not None:
            if client_order_id in self._pending_market:
                self._pending_market.remove(client_order_id)
            self._reports[client_order_id] = replace(
                self._reports[client_order_id], status=OrderStatus.CANCELLED)
            return True
        report = self._reports.get(client_order_id)
        if report is None or report.status in {OrderStatus.FILLED, OrderStatus.REJECTED, OrderStatus.CANCELLED}:
            return False
        self._reports[client_order_id] = replace(report, status=OrderStatus.CANCELLED)
        return True

    async def get_order(self, client_order_id: str) -> ExecutionReport:
        return self._reports.get(
            client_order_id,
            ExecutionReport(client_order_id=client_order_id, status=OrderStatus.UNKNOWN),
        )

    async def get_positions(self) -> List[Position]:
        return list(self._positions.values())

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        expected = {position.instrument.symbol: position.quantity for position in (portfolio.positions if portfolio else [])}
        actual = {position.instrument.symbol: position.quantity for position in self._positions.values()}
        differences = [
            symbol for symbol in sorted(set(expected) | set(actual))
            if expected.get(symbol, 0.0) != actual.get(symbol, 0.0)
        ]
        return ReconciliationResult(
            venue=self.venue_id,
            checked_at=datetime.now(timezone.utc),
            matched=not differences,
            position_differences=differences,
        )

    def _apply_fill(self, fill: Fill) -> None:
        signed_quantity = fill.quantity if fill.side.value == "buy" else -fill.quantity
        current = self._positions.get(fill.instrument.symbol)
        if current is None:
            quantity = signed_quantity
            average_price = fill.price
        else:
            quantity = current.quantity + signed_quantity
            average_price = fill.price if quantity == 0 else current.average_price
        self._positions[fill.instrument.symbol] = Position(
            instrument=fill.instrument,
            quantity=quantity,
            average_price=average_price,
        )


class LegacyBrokerAdapter:
    """Adapt the legacy ``place_order`` broker API to ``BrokerAdapter``.

    This adapter is intentionally opt-in. It never creates credentials, opens a
    connection implicitly, or converts missing reconciliation data into success.
    """

    def __init__(self, broker: Any, venue_id: str = "legacy") -> None:
        if broker is None or not hasattr(broker, "place_order"):
            raise ValueError("LegacyBrokerAdapter requires a broker with place_order()")
        self.broker = broker
        self.venue_id = venue_id
        self._orders: Dict[str, Any] = {}
        self._reports: Dict[str, ExecutionReport] = {}

    async def connect(self) -> None:
        await self._invoke("connect")

    async def disconnect(self) -> None:
        await self._invoke("disconnect")

    async def submit_order(self, order: OrderRequest) -> ExecutionReport:
        existing = self._reports.get(order.client_order_id)
        if existing is not None:
            return existing
        legacy_side: Any = order.side
        legacy_type: Any = order.order_type
        try:
            module = importlib.import_module(type(self.broker).__module__)
            LegacyOrderSide = getattr(module, "OrderSide")
            LegacyOrderType = getattr(module, "OrderType")
            legacy_side = LegacyOrderSide.BUY if order.side is OrderSide.BUY else LegacyOrderSide.SELL
            legacy_type = getattr(LegacyOrderType, order.order_type.name)
        except (ImportError, AttributeError):
            try:
                from trading_bot.broker.broker_interface import (
                    OrderSide as LegacyOrderSide,
                    OrderType as LegacyOrderType,
                )

                legacy_side = LegacyOrderSide.BUY if order.side is OrderSide.BUY else LegacyOrderSide.SELL
                legacy_type = getattr(LegacyOrderType, order.order_type.name)
            except (ImportError, AttributeError) as exc:
                raise RuntimeError(
                    f"cannot resolve legacy order enums for broker "
                    f"{type(self.broker).__module__}.{type(self.broker).__name__}; "
                    "refusing to submit with an uninterpretable side/type"
                ) from exc

        result = await self._invoke(
            "place_order",
            symbol=order.instrument.symbol,
            side=legacy_side,
            type=legacy_type,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
        )
        self._orders[order.client_order_id] = result
        status = self._status(getattr(result, "status", None))
        filled_quantity = float(getattr(result, "filled_quantity", 0.0) or 0.0)
        filled_price = getattr(result, "filled_price", None) or order.price
        fills = []
        if (status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)
                and filled_quantity > 0 and filled_price is not None):
            fills.append(Fill(
                client_order_id=order.client_order_id,
                venue_order_id=getattr(result, "client_order_id", None),
                instrument=order.instrument,
                side=order.side,
                quantity=filled_quantity,
                price=float(filled_price),
                commission=float(getattr(result, "commission", 0.0) or 0.0),
            ))
        report = ExecutionReport(
            client_order_id=order.client_order_id,
            status=status,
            fills=fills,
            expected_price=order.price,
            error=None if status is not OrderStatus.REJECTED else "Legacy broker rejected order",
        )
        self._reports[order.client_order_id] = report
        return report

    async def cancel_order(self, client_order_id: str) -> bool:
        order = self._orders.get(client_order_id)
        symbol = getattr(order, "symbol", None) or getattr(getattr(order, "instrument", None), "symbol", None)
        if hasattr(self.broker, "cancel_order"):
            try:
                result = await self._invoke("cancel_order", symbol, client_order_id)
            except TypeError:
                result = await self._invoke("cancel_order", client_order_id)
            return bool(result)
        return False

    async def get_order(self, client_order_id: str) -> ExecutionReport:
        cached = self._reports.get(client_order_id)
        if cached is not None:
            return cached
        if hasattr(self.broker, "get_order_status"):
            raw = await self._invoke("get_order_status", client_order_id)
            if raw is not None:
                status = self._status(getattr(raw, "status", None) or (raw.get("status") if isinstance(raw, dict) else None))
                report = ExecutionReport(client_order_id=client_order_id, status=status)
                self._reports[client_order_id] = report
                return report
        return ExecutionReport(client_order_id=client_order_id, status=OrderStatus.UNKNOWN)

    async def get_positions(self) -> List[Position]:
        if not hasattr(self.broker, "get_positions"):
            return []
        result = await self._invoke("get_positions")
        normalized = []
        for position in result or []:
            if isinstance(position, Position):
                normalized.append(position)
                continue
            symbol = getattr(position, "symbol", None) or (position.get("symbol") if isinstance(position, dict) else None)
            quantity = getattr(position, "quantity", None) or (position.get("quantity") if isinstance(position, dict) else None)
            entry_price = getattr(position, "entry_price", None) or (position.get("entry_price") if isinstance(position, dict) else None)
            if symbol is not None and quantity is not None and entry_price is not None:
                normalized.append(Position(
                    Instrument(str(symbol), InstrumentType.SYNTHETIC, self.venue_id),
                    float(quantity),
                    float(entry_price),
                    unrealized_pnl=float(getattr(position, "unrealized_pnl", 0.0) or 0.0),
                    realized_pnl=float(getattr(position, "realized_pnl", 0.0) or 0.0),
                ))
        return normalized

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        if not hasattr(self.broker, "get_positions"):
            return ReconciliationResult(
                venue=self.venue_id,
                checked_at=datetime.now(timezone.utc),
                matched=False,
                position_differences=["legacy broker does not expose positions"],
            )
        actual_positions = await self.get_positions()
        expected = {
            position.instrument.symbol: position.quantity
            for position in (portfolio.positions if portfolio else [])
        }
        actual = {
            position.instrument.symbol: position.quantity
            for position in actual_positions
            if isinstance(position, Position)
        }
        differences = [
            symbol for symbol in sorted(set(expected) | set(actual))
            if expected.get(symbol, 0.0) != actual.get(symbol, 0.0)
        ]
        return ReconciliationResult(
            venue=self.venue_id,
            checked_at=datetime.now(timezone.utc),
            matched=not differences,
            position_differences=differences,
        )

    async def _invoke(self, method: str, *args: Any, **kwargs: Any) -> Any:
        function = getattr(self.broker, method)
        try:
            result = function(*args, **kwargs)
        except TypeError:
            if method == "place_order":
                variants = [
                    {
                        "symbol": kwargs["symbol"],
                        "side": kwargs["side"],
                        "order_type": kwargs["type"],
                        "quantity": kwargs["quantity"],
                        "price": kwargs.get("price"),
                        "stop_price": kwargs.get("stop_price"),
                    },
                    {
                        "symbol": kwargs["symbol"],
                        "side": kwargs["side"],
                        "type": kwargs["type"],
                        "quantity": kwargs["quantity"],
                    },
                ]
                last_error = None
                for variant in variants:
                    try:
                        result = function(**variant)
                        break
                    except TypeError as exc:
                        last_error = exc
                else:
                    raise last_error
            else:
                raise
        return await result if inspect.isawaitable(result) else result

    @staticmethod
    def _status(value: Any) -> OrderStatus:
        normalized = str(getattr(value, "value", value or "unknown")).lower()
        aliases = {
            "open": OrderStatus.ACCEPTED,
            "pending": OrderStatus.SUBMITTED,
            "partial": OrderStatus.PARTIALLY_FILLED,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "cancelled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        return aliases.get(normalized, OrderStatus.UNKNOWN)


class CanonicalExecutionService:
    """Idempotent execution boundary shared by paper and live adapters."""

    def __init__(
        self,
        adapter: Optional[BrokerAdapter] = None,
        mode: str = "paper",
        repository: Any = None,
    ) -> None:
        if adapter is None:
            if mode != "paper":
                raise ValueError("A broker adapter is required for non-paper execution")
            adapter = PaperBrokerAdapter()
        self.adapter = adapter
        self.mode = mode
        self.repository = repository
        self._reports: Dict[str, ExecutionReport] = {}
        self._orders: Dict[str, OrderRequest] = {}

    def _conflicts_with(self, prior: OrderRequest, order: OrderRequest) -> bool:
        return (prior.instrument.symbol != order.instrument.symbol
                or prior.side != order.side
                or prior.order_type != order.order_type
                or abs(prior.quantity - order.quantity) > 1e-9)

    async def submit(self, order: OrderRequest) -> ExecutionReport:
        existing = self._reports.get(order.client_order_id)
        if existing is not None:
            prior = self._orders.get(order.client_order_id)
            if prior is not None and self._conflicts_with(prior, order):
                return ExecutionReport(
                    client_order_id=order.client_order_id,
                    status=OrderStatus.REJECTED,
                    error="client_order_id collision with a different order")
            return existing
        if self.repository is not None:
            # Durable idempotency: a client_order_id that already has a
            # durable record is never re-sent to the venue, including after
            # restart. If a report was recorded, replay it; if the row has no
            # report yet the venue outcome is uncertain — that belongs to the
            # reconciler's broker lookup, never to a blind resubmission.
            from trading_bot.persistence.repositories import (
                decode_order, decode_report)
            durable = await self.repository.get_order(order.client_order_id)
            if durable is not None:
                stored = decode_order(durable["order_json"])
                if self._conflicts_with(stored, order):
                    return ExecutionReport(
                        client_order_id=order.client_order_id,
                        status=OrderStatus.REJECTED,
                        error="client_order_id collision with a different order")
                if durable.get("report_json"):
                    report = decode_report(durable["report_json"])
                else:
                    report = ExecutionReport(
                        client_order_id=order.client_order_id,
                        status=OrderStatus.UNKNOWN,
                        error="durable order exists without a venue outcome; "
                              "awaiting reconciliation lookup")
                self._orders[order.client_order_id] = order
                self._reports[order.client_order_id] = report
                return report
            await self.repository.record_order(order, OrderStatus.SUBMITTED)
        report = await self.adapter.submit_order(order)
        self._orders[order.client_order_id] = order
        self._reports[order.client_order_id] = report
        if self.repository is not None:
            await self.repository.record_execution(order, report)
        return report

    async def cancel(self, client_order_id: str) -> bool:
        cancelled = await self.adapter.cancel_order(client_order_id)
        if cancelled:
            report = await self.adapter.get_order(client_order_id)
            if report.status is not OrderStatus.CANCELLED:
                report = replace(report, status=OrderStatus.CANCELLED)
            self._reports[client_order_id] = report
            order = self._orders.get(client_order_id)
            if self.repository is not None and order is not None:
                await self.repository.record_execution(order, report)
        return cancelled

    async def status(self, client_order_id: str) -> OrderStatus:
        report = self._reports.get(client_order_id)
        if report is None:
            report = await self.adapter.get_order(client_order_id)
            self._reports[client_order_id] = report
        return report.status

    async def restore_state(self) -> None:
        """Rebuild in-memory service/adapter state from the durable ledger.

        Called once at startup before the first cycle: prior order reports
        become the idempotency source of truth, and the venue adapter
        rehydrates its book so ledger and venue agree at reconciliation."""
        if self.repository is None:
            return
        rows = await self.repository.list_orders()
        for row in rows:
            try:
                order = self.repository.decode_order(row["order_json"])
            except Exception:  # noqa: BLE001 - skip undecodable rows
                logger.warning("restore_state: undecodable order row %s",
                               row.get("client_order_id"))
                continue
            self._orders[order.client_order_id] = order
            if row.get("report_json"):
                report = self.repository.decode_report(row["report_json"])
                self._reports[report.client_order_id] = report
        rehydrate = getattr(self.adapter, "rehydrate", None)
        if callable(rehydrate):
            rehydrate(rows)

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        return await self.adapter.reconcile(portfolio)
