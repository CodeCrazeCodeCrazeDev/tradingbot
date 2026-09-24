"""Canonical execution service and reference paper broker adapter."""

from __future__ import annotations

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
    """Deterministic paper adapter used by replay and local development."""

    venue_id = "paper"

    def __init__(self) -> None:
        self._reports: Dict[str, ExecutionReport] = {}
        self._positions: Dict[str, Position] = {}
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

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

        fill = Fill(
            client_order_id=order.client_order_id,
            venue_order_id=f"paper-{order.client_order_id}",
            instrument=order.instrument,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
        )
        update = OrderUpdate(
            client_order_id=order.client_order_id,
            status=OrderStatus.FILLED,
            venue_order_id=fill.venue_order_id,
            filled_quantity=fill.quantity,
            average_price=fill.price,
        )
        report = ExecutionReport(
            client_order_id=order.client_order_id,
            status=OrderStatus.FILLED,
            updates=[update],
            fills=[fill],
            expected_price=order.price,
            slippage_bps=0.0,
        )
        self._reports[order.client_order_id] = report
        self._apply_fill(fill)
        return report

    async def cancel_order(self, client_order_id: str) -> bool:
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
            from trading_bot.broker.broker_interface import (
                OrderSide as LegacyOrderSide,
                OrderType as LegacyOrderType,
            )

            legacy_side = LegacyOrderSide.BUY if order.side is OrderSide.BUY else LegacyOrderSide.SELL
            legacy_type = getattr(LegacyOrderType, order.order_type.name)
        except (ImportError, AttributeError):
            pass

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
        if status is OrderStatus.FILLED and filled_quantity > 0 and filled_price is not None:
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
                result = function(
                    symbol=kwargs["symbol"],
                    side=kwargs["side"],
                    type=kwargs["type"],
                    quantity=kwargs["quantity"],
                )
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

    async def submit(self, order: OrderRequest) -> ExecutionReport:
        existing = self._reports.get(order.client_order_id)
        if existing is not None:
            return existing
        if self.repository is not None:
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

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        return await self.adapter.reconcile(portfolio)
