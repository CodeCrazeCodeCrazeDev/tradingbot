"""Durable execution recovery for the canonical paper path.

``ExecutionReconciler`` closes the crash window between
``record_order(SUBMITTED)`` and the venue reply: orders persisted in a
non-terminal state are reconciled at startup via broker lookup — never by
resubmission — and every recovery leaves an ``audit_events`` row.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..foundation.contracts import (
    AuditEvent,
    OrderStatus,
    PortfolioSnapshot,
    ReconciliationResult,
)

logger = logging.getLogger(__name__)

NON_TERMINAL_STATUSES = (
    OrderStatus.CREATED.value,
    OrderStatus.SUBMITTED.value,
    OrderStatus.ACCEPTED.value,
    OrderStatus.PARTIALLY_FILLED.value,
    OrderStatus.CANCEL_PENDING.value,
    OrderStatus.UNKNOWN.value,
)

_TERMINAL = {
    OrderStatus.FILLED,
    OrderStatus.CANCELLED,
    OrderStatus.REJECTED,
    OrderStatus.EXPIRED,
}


class ExecutionReconciler:
    """Reconciles durable order state with the venue at startup/shutdown."""

    def __init__(self, service: Any, repository: Any = None,
                 account_id: str = "runtime") -> None:
        self.service = service
        self.repository = repository if repository is not None else getattr(service, "repository", None)
        self.account_id = account_id
        self._owns_repository = False

    def _ensure_repository(self) -> Any:
        """Reopen the durable store if the session's handle was closed.

        ``bot.run()`` closes the shared repository in its finally block; the
        reconciler then opens its own handle (which it owns and closes).
        """
        repo = self.repository
        if repo is not None and getattr(repo, "closed", False):
            self.repository = type(repo)(
                path=repo.path, initial_equity=getattr(repo, "initial_equity", 0.0)
            )
            self._owns_repository = True
        return self.repository

    async def aclose(self) -> None:
        if self._owns_repository and self.repository is not None:
            self.repository.close()

    async def _audit(self, action: str, outcome: str, correlation_id: str,
                     details: Optional[Dict[str, Any]] = None) -> None:
        if self.repository is None:
            return
        await self.repository.record_audit_event(AuditEvent(
            event_type="execution_recovery",
            actor="execution_reconciler",
            action=action,
            outcome=outcome,
            correlation_id=correlation_id,
            details=details or {},
        ))

    async def recover_pending_orders(self) -> Dict[str, Any]:
        """Look up every durable non-terminal order at the venue.

        Never resubmits: the venue's verdict is persisted and audited.
        Lookup failures leave the durable row untouched and are audited as
        ``lookup_failed`` so the next recovery pass retries.
        """
        repo = self._ensure_repository()
        if repo is None:
            return {"count": 0, "recovered": []}

        pending = await repo.list_orders(statuses=list(NON_TERMINAL_STATUSES))
        recovered = []
        for row in pending:
            client_order_id = row["client_order_id"]
            order = repo.decode_order(row["order_json"])
            try:
                report = await self.service.adapter.get_order(client_order_id)
            except Exception as exc:
                logger.warning("Recovery lookup failed for %s: %s", client_order_id, exc)
                await self._audit("order_recovery", "lookup_failed", client_order_id,
                                  {"error": str(exc)})
                recovered.append({"client_order_id": client_order_id, "outcome": "lookup_failed"})
                continue

            if report.status in _TERMINAL:
                await repo.record_execution(order, report)
                outcome = report.status.value
            else:
                # Venue can't confirm a terminal state — fail closed to
                # UNKNOWN rather than trusting the stale durable record.
                await repo.record_order(order, OrderStatus.UNKNOWN)
                outcome = "unknown"
            await self._audit("order_recovery", outcome, client_order_id)
            recovered.append({"client_order_id": client_order_id, "outcome": outcome})

        return {"count": len(pending), "recovered": recovered}

    async def reconcile_positions(self, account_id: Optional[str] = None) -> ReconciliationResult:
        """Compare venue positions to the durable ledger; persist + audit."""
        repo = self._ensure_repository()
        account_id = account_id or self.account_id
        positions = await self.service.adapter.get_positions()
        expected = PortfolioSnapshot(
            account_id=account_id, equity=0.0, cash=0.0, positions=list(positions),
        )
        result = await repo.reconcile(expected, venue=type(self.service.adapter).__name__)
        await self._audit(
            "reconcile_positions",
            "matched" if result.matched else "mismatch",
            account_id,
            {"venue": result.venue, "differences": list(result.position_differences)},
        )
        return result
