"""Authoritative typed repositories for trading state and audit history.

This module intentionally has no in-memory fallback. Orders, fills, positions,
and audit events are capital-accounting records; persistence failure must be
visible to the caller rather than silently losing state.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from trading_bot.foundation.contracts import (
    AuditEvent,
    ExecutionReport,
    Fill,
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderStatus,
    PortfolioSnapshot,
    Position,
    ReconciliationResult,
)


class SqliteTradingRepository:
    """Single-source repository for orders, fills, positions, and audit events."""

    def __init__(self, path: str = "alphaalgo_data/trading_state.db",
                 initial_equity: float = 10000.0) -> None:
        self.path = path
        # Base capital for snapshot accounting: cash/equity are derived from
        # the persisted fill ledger, never fabricated.
        self.initial_equity = float(initial_equity)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._lock:
            self._connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS orders (
                    client_order_id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    order_json TEXT NOT NULL,
                    report_json TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fills (
                    fill_key TEXT PRIMARY KEY,
                    client_order_id TEXT NOT NULL,
                    venue_order_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    commission REAL NOT NULL,
                    fill_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    quantity REAL NOT NULL,
                    average_price REAL NOT NULL,
                    instrument_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    audit_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reconciliation_runs (
                    reconciliation_id TEXT PRIMARY KEY,
                    venue TEXT NOT NULL,
                    matched INTEGER NOT NULL,
                    result_json TEXT NOT NULL,
                    checked_at TEXT NOT NULL
                );
                """
            )
            self._connection.commit()

    async def record_order(self, order: OrderRequest, status: OrderStatus = OrderStatus.CREATED) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(order.to_dict(), sort_keys=True)
        with self._lock:
            self._connection.execute(
                """INSERT INTO orders
                   (client_order_id, decision_id, symbol, status, order_json, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(client_order_id) DO UPDATE SET
                     status=excluded.status, order_json=excluded.order_json,
                     updated_at=excluded.updated_at""",
                (order.client_order_id, order.decision_id, order.instrument.symbol,
                 status.value, payload, now),
            )
            self._connection.commit()

    async def record_execution(self, order: OrderRequest, report: ExecutionReport) -> None:
        await self.record_order(order, report.status)
        now = datetime.now(timezone.utc).isoformat()
        report_json = json.dumps(report.to_dict(), sort_keys=True)
        with self._lock:
            self._connection.execute(
                "UPDATE orders SET report_json=?, status=?, updated_at=? WHERE client_order_id=?",
                (report_json, report.status.value, now, order.client_order_id),
            )
            for fill in report.fills:
                self._record_fill_locked(fill)
            self._connection.commit()

    async def record_fill(self, fill: Fill) -> None:
        with self._lock:
            self._record_fill_locked(fill)
            self._connection.commit()

    def _record_fill_locked(self, fill: Fill) -> None:
        fill_key = f"{fill.client_order_id}:{fill.venue_order_id or fill.occurred_at.isoformat()}"
        existing = self._connection.execute(
            "SELECT 1 FROM fills WHERE fill_key=?", (fill_key,)
        ).fetchone()
        if existing:
            return
        current = self._connection.execute(
            "SELECT quantity, average_price, instrument_json FROM positions WHERE symbol=?",
            (fill.instrument.symbol,),
        ).fetchone()
        signed_quantity = fill.quantity if fill.side.value == "buy" else -fill.quantity
        if current is None:
            quantity, average_price = signed_quantity, fill.price
        else:
            quantity = float(current["quantity"]) + signed_quantity
            average_price = fill.price if quantity == 0 else float(current["average_price"])
        instrument_json = json.dumps(fill.instrument.to_dict(), sort_keys=True)
        self._connection.execute(
            """INSERT INTO fills
               (fill_key, client_order_id, venue_order_id, symbol, side,
                quantity, price, commission, fill_json, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fill_key, fill.client_order_id, fill.venue_order_id, fill.instrument.symbol,
             fill.side.value, fill.quantity, fill.price, fill.commission,
             json.dumps(fill.to_dict(), sort_keys=True), fill.occurred_at.isoformat()),
        )
        self._connection.execute(
            """INSERT INTO positions(symbol, quantity, average_price, instrument_json, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(symbol) DO UPDATE SET
                 quantity=excluded.quantity, average_price=excluded.average_price,
                 instrument_json=excluded.instrument_json, updated_at=excluded.updated_at""",
            (fill.instrument.symbol, quantity, average_price, instrument_json,
             datetime.now(timezone.utc).isoformat()),
        )

    async def list_fills(self) -> List[Dict[str, Any]]:
        """Return all recorded fills in execution order (read-only)."""
        with self._lock:
            rows = self._connection.execute(
                """SELECT client_order_id, venue_order_id, symbol, side,
                          quantity, price, commission, occurred_at
                   FROM fills ORDER BY occurred_at ASC, rowid ASC"""
            ).fetchall()
        return [dict(row) for row in rows]

    async def record_audit_event(self, event: AuditEvent) -> str:
        audit_id = str(uuid4())
        with self._lock:
            self._connection.execute(
                """INSERT INTO audit_events
                   (audit_id, event_type, actor, action, outcome, correlation_id,
                    event_json, occurred_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (audit_id, event.event_type, event.actor, event.action, event.outcome,
                 event.correlation_id, json.dumps(event.to_dict(), sort_keys=True),
                 event.occurred_at.isoformat()),
            )
            self._connection.commit()
        return audit_id

    async def snapshot(self, account_id: str) -> PortfolioSnapshot:
        with self._lock:
            rows = self._connection.execute(
                "SELECT symbol, quantity, average_price, instrument_json FROM positions"
            ).fetchall()
        positions = []
        for row in rows:
            data = json.loads(row["instrument_json"])
            instrument = Instrument(
                symbol=data["symbol"],
                instrument_type=InstrumentType(data["instrument_type"]),
                venue=data["venue"],
                currency=data.get("currency", "USD"),
                contract_size=data.get("contract_size", 1.0),
                price_increment=data.get("price_increment"),
                quantity_increment=data.get("quantity_increment"),
                metadata=data.get("metadata", {}),
            )
            positions.append(Position(instrument, row["quantity"], row["average_price"]))

        # Derive cash and equity from the fill ledger instead of returning
        # zeroed placeholders. Unrealized value is at cost basis — mark
        # pricing belongs to the risk state provider which has market prices.
        fills = await self.list_fills()
        cash = self.initial_equity
        for fill in fills:
            quantity = float(fill["quantity"])
            price = float(fill["price"])
            commission = float(fill["commission"] or 0.0)
            if fill["side"] == "buy":
                cash -= quantity * price + commission
            else:
                cash += quantity * price - commission
        position_value = sum(
            float(position.quantity) * float(position.average_price)
            for position in positions
        )
        return PortfolioSnapshot(
            account_id=account_id,
            equity=cash + position_value,
            cash=cash,
            positions=positions,
        )

    async def reconcile(self, expected: PortfolioSnapshot, venue: str = "repository") -> ReconciliationResult:
        actual = await self.snapshot(expected.account_id)
        expected_quantities = {position.instrument.symbol: position.quantity for position in expected.positions}
        actual_quantities = {position.instrument.symbol: position.quantity for position in actual.positions}
        differences = [
            symbol for symbol in sorted(set(expected_quantities) | set(actual_quantities))
            if expected_quantities.get(symbol, 0.0) != actual_quantities.get(symbol, 0.0)
        ]
        result = ReconciliationResult(
            venue=venue,
            checked_at=datetime.now(timezone.utc),
            matched=not differences,
            position_differences=differences,
        )
        with self._lock:
            self._connection.execute(
                """INSERT INTO reconciliation_runs
                   (reconciliation_id, venue, matched, result_json, checked_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid4()), venue, int(result.matched),
                 json.dumps(result.to_dict(), sort_keys=True), result.checked_at.isoformat()),
            )
            self._connection.commit()
        return result

    def close(self) -> None:
        with self._lock:
            self._connection.close()
