"""
Execution Bridge - Paper execution consumer for the LogAct decision bus.

Subscribes to TRADE_EXECUTION actions approved by the consensus layer and
simulates fills locally. This closes the decision->execution dead-end on the
CSC path: without a subscriber, approved trade actions were dispatched to
zero handlers and silently marked EXECUTED.

Replace this bridge with a real broker adapter for live trading.
"""

import asyncio
import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Order statuses that are final — a durable record in one of these states is
# authoritative and never re-submitted. Anything else is non-terminal: the
# venue may have received the order, so the only safe move is a broker lookup.
_TERMINAL_STATUS_VALUES = frozenset({"filled", "cancelled", "rejected", "expired"})


@dataclass
class PaperFill:
    """Record of a simulated order fill."""

    fill_id: str
    trade_id: str
    symbol: str
    action: str
    quantity: float
    price: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SlippageRecord:
    """Expected-vs-filled price record for slippage analytics."""

    symbol: str
    side: str
    expected_price: float
    fill_price: float
    quantity: float
    venue: str  # "paper" or broker name
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def slippage_bps(self) -> float:
        """Signed slippage in basis points; positive = adverse to the taker."""
        if not self.expected_price:
            return 0.0
        direction = 1.0 if self.side in ("BUY", "STRONG_BUY") else -1.0
        return direction * (self.fill_price - self.expected_price) / self.expected_price * 1e4


class SlippageRecorder:
    """Shared expected-vs-fill recorder used by every execution bridge.

    Appends one SlippageRecord per fill to a JSONL file and keeps running
    stats — this is the measurement plumbing for live slippage validation
    once a real broker adapter supplies fills.
    """

    def __init__(self, persist_path: str = "alphaalgo_data/slippage.jsonl"):
        self.persist_path = persist_path
        self.records: List[SlippageRecord] = []

    def record(self, rec: SlippageRecord) -> None:
        self.records.append(rec)
        try:
            os.makedirs(os.path.dirname(self.persist_path) or ".", exist_ok=True)
            with open(self.persist_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({**rec.__dict__, "slippage_bps": rec.slippage_bps}) + "\n")
        except Exception as e:
            logger.error(f"SlippageRecorder: persist failed: {e}")

    def stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        recs = [r for r in self.records if symbol is None or r.symbol == symbol]
        bps = [r.slippage_bps for r in recs]
        if not bps:
            return {"fills": 0}
        bps_sorted = sorted(bps)
        p95 = bps_sorted[min(int(0.95 * len(bps_sorted)), len(bps_sorted) - 1)]
        return {
            "fills": len(bps),
            "mean_bps": sum(bps) / len(bps),
            "max_bps": max(bps),
            "p95_bps": p95,
        }


class PaperExecutionBridge:
    """
    Minimal paper executor for the CSC decision pipeline.

    Attach to the shared ``UnifiedDecisionBus`` and it consumes every approved
    TRADE_EXECUTION action and delegates to ``CanonicalExecutionService``.
    The typed service + ``SqliteTradingRepository`` are the authoritative
    record; ``self.fills``/``self.positions`` are in-memory projections for
    diagnostics only — the bridge never writes a parallel durable ledger and
    fails closed when no service is attached. No real money is touched.
    """

    def __init__(self, persist_path: str = "alphaalgo_data/paper_fills.jsonl",
                 slippage: Optional[SlippageRecorder] = None,
                 execution_service: Any = None,
                 submit_timeout: Optional[float] = 30.0):
        self.persist_path = persist_path  # legacy arg; no longer written
        self.fills: List[PaperFill] = []
        self.positions: Dict[str, float] = {}
        self.attached = False
        self.slippage = slippage or SlippageRecorder()
        self.execution_service = execution_service
        # Broker-call deadline: a hung submit resolves to a durable UNKNOWN
        # report reconciled later via broker lookup — never a silent retry.
        self.submit_timeout = submit_timeout
        self._processed_trade_ids: Dict[str, Dict[str, Any]] = {}

    def attach(self, decision_bus: Any) -> None:
        """Subscribe this bridge to TRADE_EXECUTION actions on the bus."""
        decision_bus.subscribe(
            "TRADE_EXECUTION",
            self.execute,
            subscriber_id="paper_execution_bridge",
        )
        self.attached = True
        logger.info("PaperExecutionBridge attached to decision bus")

    async def execute(self, action: Any) -> Dict[str, Any]:
        """Handle an approved TRADE_EXECUTION LogAction."""
        payload = action.payload if isinstance(getattr(action, "payload", None), dict) else {}

        symbol = payload.get("symbol", "UNKNOWN")
        side = payload.get("action", "WAIT")
        quantity = payload.get("quantity", 0.0)
        price = payload.get("price") or payload.get("mark_price") or 0.0

        if not isinstance(quantity, (int, float)) or quantity <= 0:
            logger.warning(f"PaperExecutionBridge: rejecting fill with invalid quantity {quantity}")
            return {"status": "rejected", "reason": "invalid_quantity"}

        if side in ("WAIT", "HOLD", "NO_TRADE"):
            logger.info(f"PaperExecutionBridge: no-op for side={side}")
            # The executor ran and reached a terminal verdict (deliberate
            # no-op) — the shared-log action completed the execution stage.
            self._mark_executed(action)
            return {"status": "skipped", "reason": f"side={side}"}

        trade_id = str(payload.get("trade_id", getattr(action, "action_id", "n/a")))
        if trade_id in self._processed_trade_ids:
            return dict(self._processed_trade_ids[trade_id])

        if self.execution_service is None:
            # No canonical execution service: fail closed. The bridge is a
            # facade, not an executor — it must not write fills outside the
            # typed service + repository path.
            logger.error(
                "PaperExecutionBridge: no execution service configured; refusing "
                f"to fill trade_id={trade_id}"
            )
            result = {"status": "rejected", "reason": "no_execution_service"}
            self._processed_trade_ids[trade_id] = result
            return result

        repository = getattr(self.execution_service, "repository", None)

        # Durable idempotency: the repository is the persistent order
        # identity. A row for this client_order_id means the order already
        # reached the boundary once — reconcile it by venue lookup, never by
        # resubmitting (a resend could duplicate a fill the venue booked).
        if repository is not None:
            try:
                existing = await repository.get_order(trade_id)
            except Exception as exc:
                logger.error(
                    f"PaperExecutionBridge: durable lookup failed for {trade_id}: "
                    f"{exc}; refusing to submit without durable state"
                )
                result = {"status": "error", "reason": "durable_lookup_failed"}
                self._processed_trade_ids[trade_id] = result
                return result
            if existing is not None:
                result = await self._resolve_persisted_order(trade_id, existing, action, repository)
                self._processed_trade_ids[trade_id] = result
                return result

        # Audit the authorization before submission: reaching this bridge
        # means the action passed shield + governance + LogAct consensus.
        if not await self._record_audit(
            repository, action="order_authorized", outcome="approved",
            correlation_id=trade_id,
            details={
                "action_id": getattr(action, "action_id", None),
                "governance_receipt": payload.get("governance_receipt"),
                "voters": self._voter_summary(action),
            },
        ):
            result = {"status": "error", "reason": "audit_unavailable"}
            self._processed_trade_ids[trade_id] = result
            return result
        if not await self._record_audit(
            repository, action="order_submit_attempt", outcome="attempted",
            correlation_id=trade_id,
            details={"symbol": symbol, "side": side,
                     "quantity": float(quantity), "price": float(price)},
        ):
            result = {"status": "error", "reason": "audit_unavailable"}
            self._processed_trade_ids[trade_id] = result
            return result

        from trading_bot.foundation.contracts import (
            ExecutionReport,
            Instrument,
            InstrumentType,
            OrderRequest,
            OrderSide,
            OrderStatus,
            OrderType,
        )

        typed_order = OrderRequest(
            instrument=Instrument(symbol, InstrumentType.SYNTHETIC, "paper"),
            side=OrderSide.BUY if side in ("BUY", "STRONG_BUY") else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=float(quantity),
            price=float(price) if float(price) > 0 else None,
            client_order_id=trade_id,
            decision_id=trade_id,
        )
        try:
            report = await self._submit_with_timeout(typed_order)
        except asyncio.TimeoutError:
            # The venue may have received the order — its fate is UNKNOWN.
            # Record that durably; the next recovery pass reconciles it via
            # broker lookup. Never resubmit in place.
            report = ExecutionReport(
                client_order_id=trade_id,
                status=OrderStatus.UNKNOWN,
                error=f"submit timed out after {self.submit_timeout}s",
            )
            if repository is not None:
                try:
                    await repository.record_execution(typed_order, report)
                except Exception as exc:
                    logger.error(
                        f"PaperExecutionBridge: failed to persist UNKNOWN "
                        f"report for {trade_id}: {exc}"
                    )
            await self._record_audit(
                repository, action="order_broker_response",
                outcome="timeout_unknown", correlation_id=trade_id,
                details={"error": report.error},
            )
            result = {"status": "unknown", "reason": "submit_timeout"}
            self._processed_trade_ids[trade_id] = result
            return result

        await self._record_audit(
            repository, action="order_broker_response",
            outcome=report.status.value, correlation_id=trade_id,
            details={
                "venue_order_id": report.fills[0].venue_order_id
                if report.fills else None,
                "fill_count": len(report.fills),
                "error": report.error,
            },
        )
        if report.status.value != "filled":
            result = {"status": report.status.value, "reason": report.error}
            self._processed_trade_ids[trade_id] = result
            return result

        fill_price = report.fills[0].price if report.fills else float(price)
        fill = PaperFill(
            fill_id=report.fills[0].venue_order_id if report.fills else str(uuid.uuid4()),
            trade_id=trade_id,
            symbol=symbol,
            action=side,
            quantity=float(quantity),
            price=float(fill_price),
        )
        self.fills.append(fill)
        signed_qty = fill.quantity if side in ("BUY", "STRONG_BUY") else -fill.quantity
        self.positions[symbol] = round(self.positions.get(symbol, 0.0) + signed_qty, 8)
        self.slippage.record(SlippageRecord(
            symbol=symbol, side=side,
            expected_price=float(price), fill_price=fill.price,
            quantity=fill.quantity, venue="paper",
        ))
        self._mark_executed(action)
        result = {"status": "filled", "fill_id": fill.fill_id}
        self._processed_trade_ids[trade_id] = result
        return result

    async def _submit_with_timeout(self, order: Any) -> Any:
        """Submit through the single execution boundary under a deadline."""
        if self.submit_timeout is None:
            return await self.execution_service.submit(order)
        return await asyncio.wait_for(
            self.execution_service.submit(order), timeout=self.submit_timeout
        )

    async def _resolve_persisted_order(
        self,
        trade_id: str,
        row: Dict[str, Any],
        action: Any,
        repository: Any,
    ) -> Dict[str, Any]:
        """Resolve a durable order record without resubmitting.

        Terminal records are authoritative — return the stored verdict.
        Non-terminal records go through ``adapter.get_order`` (broker lookup)
        and the outcome is re-persisted; UNKNOWN stays UNKNOWN until the
        venue can prove otherwise.
        """
        stored = str(row.get("status") or "unknown")
        if stored in _TERMINAL_STATUS_VALUES:
            await self._record_audit(
                repository, action="order_dedup", outcome=stored,
                correlation_id=trade_id,
                details={"reason": "durable_terminal_record"},
            )
            if stored == "filled":
                self._mark_executed(action)
            return {"status": stored, "reason": "durable_terminal_record",
                    "recovered": True}

        adapter = getattr(self.execution_service, "adapter", None)
        try:
            report = await adapter.get_order(trade_id)
        except Exception as exc:
            await self._record_audit(
                repository, action="order_recovery", outcome="lookup_failed",
                correlation_id=trade_id, details={"error": str(exc)},
            )
            return {"status": "unknown", "reason": "broker_lookup_failed",
                    "recovered": False}
        order = repository.decode_order(row["order_json"])
        await repository.record_execution(order, report)
        await self._record_audit(
            repository, action="order_recovery", outcome=report.status.value,
            correlation_id=trade_id,
            details={"previous_status": stored},
        )
        if report.status.value == "filled":
            self._mark_executed(action)
        return {"status": report.status.value,
                "reason": "reconciled_via_broker_lookup", "recovered": True}

    async def _record_audit(
        self,
        repository: Any,
        *,
        action: str,
        outcome: str,
        correlation_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Append an audit row; False when there is no repository or the write
        failed (callers decide whether to fail closed)."""
        if repository is None:
            return True  # in-memory mode: nothing durable to write
        try:
            from trading_bot.foundation.contracts import AuditEvent

            await repository.record_audit_event(AuditEvent(
                event_type="execution",
                actor="paper_execution_bridge",
                action=action,
                outcome=outcome,
                correlation_id=correlation_id,
                details=details or {},
            ))
            return True
        except Exception as exc:
            logger.error(f"PaperExecutionBridge: audit write failed: {exc}")
            return False

    @staticmethod
    def _voter_summary(action: Any) -> Dict[str, Any]:
        """JSON-safe subset of voter reports for the audit record."""
        summary: Dict[str, Any] = {}
        for voter_id, report in (getattr(action, "voter_reports", None) or {}).items():
            if isinstance(report, dict):
                summary[str(voter_id)] = {
                    key: report.get(key)
                    for key in ("decision", "reason", "audit_id")
                    if key in report
                }
            else:
                summary[str(voter_id)] = str(report)
        return summary

    @staticmethod
    def _mark_executed(action: Any) -> None:
        """The execution layer owns the EXECUTED status: flip the shared-log
        action once a fill is recorded so the audit trail shows the action was
        carried out, not merely approved."""
        try:
            from trading_bot.core.unified_event_bus import ActionStatus
            action.status = ActionStatus.EXECUTED
        except Exception:
            pass

    def get_summary(self) -> Dict[str, Any]:
        return {
            "fills": len(self.fills),
            "positions": dict(self.positions),
            "attached": self.attached,
            "slippage": self.slippage.stats(),
        }


class BrokerExecutionBridge:
    """
    Live-execution consumer for the LogAct decision bus.

    Same attach()/execute() contract as PaperExecutionBridge, but delegates
    approved TRADE_EXECUTION actions to a real ``BrokerInterface`` adapter.
    Only reachable through ``make_execution_bridge(mode="broker", broker=...)``
    — never constructed without an explicit broker adapter, and every fill is
    recorded for slippage analytics against the approved expected price.
    """

    def __init__(self, broker: Any, slippage: Optional[SlippageRecorder] = None):
        if broker is None or not hasattr(broker, "place_order"):
            raise ValueError("BrokerExecutionBridge requires a broker with place_order()")
        self.broker = broker
        self.slippage = slippage or SlippageRecorder()
        self.orders: List[Any] = []
        self.attached = False

    def attach(self, decision_bus: Any) -> None:
        decision_bus.subscribe(
            "TRADE_EXECUTION",
            self.execute,
            subscriber_id="broker_execution_bridge",
        )
        self.attached = True
        logger.info("BrokerExecutionBridge attached to decision bus")

    async def execute(self, action: Any) -> Dict[str, Any]:
        payload = action.payload if isinstance(getattr(action, "payload", None), dict) else {}

        symbol = payload.get("symbol", "UNKNOWN")
        side_raw = payload.get("action", "WAIT")
        quantity = payload.get("quantity", 0.0)
        expected = float(payload.get("price") or payload.get("mark_price") or 0.0)

        if side_raw in ("WAIT", "HOLD", "NO_TRADE"):
            return {"status": "skipped", "reason": f"side={side_raw}"}
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return {"status": "rejected", "reason": "invalid_quantity"}

        # Lazy import: broker package pulls aiohttp; don't cost the paper path.
        from trading_bot.broker.broker_interface import OrderSide, OrderType

        side = OrderSide.BUY if side_raw in ("BUY", "STRONG_BUY") else OrderSide.SELL
        try:
            order = await self.broker.place_order(
                symbol=symbol, side=side, type=OrderType.MARKET,
                quantity=float(quantity),
            )
        except Exception as e:
            logger.error(f"BrokerExecutionBridge: order failed: {e}")
            return {"status": "error", "reason": str(e)}

        self.orders.append(order)
        fill_px = float(getattr(order, "filled_price", None) or expected)
        self.slippage.record(SlippageRecord(
            symbol=symbol, side=side_raw,
            expected_price=expected, fill_price=fill_px,
            quantity=float(quantity),
            venue=type(self.broker).__name__,
        ))
        logger.info(
            f"BrokerExecutionBridge: submitted {side_raw} {quantity} {symbol} "
            f"-> status={getattr(order, 'status', '?')} fill={fill_px}"
        )
        return {"status": "submitted", "order_id": getattr(order, "client_order_id", None)}

    def get_summary(self) -> Dict[str, Any]:
        return {
            "orders": len(self.orders),
            "attached": self.attached,
            "venue": type(self.broker).__name__,
            "slippage": self.slippage.stats(),
        }


def make_execution_bridge(mode: str = "paper", broker: Any = None,
                          persist_path: str = "alphaalgo_data/paper_fills.jsonl",
                          slippage: Optional[SlippageRecorder] = None) -> Any:
    """Execution-bridge factory: 'paper' (default) or 'broker'.

    'broker' requires a connected BrokerInterface adapter; it fails loudly
    rather than silently degrading to paper execution.
    """
    if mode == "paper":
        return PaperExecutionBridge(persist_path=persist_path, slippage=slippage)
    if mode == "broker":
        return BrokerExecutionBridge(broker=broker, slippage=slippage)
    raise ValueError(f"Unknown execution mode: {mode!r} (expected 'paper' or 'broker')")
