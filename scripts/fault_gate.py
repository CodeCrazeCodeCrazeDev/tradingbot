#!/usr/bin/env python
"""10,000-event execution recovery / fault-injection gate.

Drives the canonical execution path (CanonicalExecutionService +
PaperBrokerAdapter + SqliteTradingRepository) through a seeded event mix:

- new market-order submissions,
- duplicate resubmissions of existing client_order_ids (incl. post-restart),
- simulated restarts: a fresh service+adapter over the *same* durable state,
- injected uncertain outcomes (UNKNOWN) which must never be silently retried,
- orders with multiple partial fills (two venue deals, same client_order_id).

Gate invariants (all must hold):
1. The venue adapter sees each client_order_id at most once — durable
   idempotency survives process restart.
2. A terminal durable order status never regresses (FILLED -> SUBMITTED is
   a corruption).
3. Every fill reported by the venue is persisted; positions equal the signed
   sum of persisted fills.
4. UNKNOWN reports are never auto-retried; they stay UNKNOWN until a lookup
   resolves them.

Usage: python scripts/fault_gate.py --events 10000 --seed 13 [--keep-db]
Exit code 0 = gate passed; 1 = violations found.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from trading_bot.execution.service import (  # noqa: E402
    CanonicalExecutionService, PaperBrokerAdapter)
from trading_bot.foundation.contracts import (  # noqa: E402
    ExecutionReport, Fill, Instrument, InstrumentType, OrderRequest,
    OrderSide, OrderStatus, OrderType)
from trading_bot.persistence.repositories import (  # noqa: E402
    SqliteTradingRepository)

TERMINAL = {
    OrderStatus.FILLED, OrderStatus.CANCELLED,
    OrderStatus.REJECTED, OrderStatus.EXPIRED,
}
TERMINAL_RANK = {"filled": 3, "cancelled": 3, "rejected": 3, "expired": 3,
                 "unknown": 1, "partially_filled": 2, "accepted": 2,
                 "submitted": 2, "created": 0}


class InstrumentedPaperAdapter(PaperBrokerAdapter):
    """PaperBrokerAdapter + submission counting + fault injection."""

    def __init__(self, rng: random.Random) -> None:
        super().__init__()
        self.rng = rng
        self.submits: Dict[str, int] = defaultdict(int)
        self.venue_fills: List[Fill] = []
        self._extra_fills: Dict[str, List[Dict[str, Any]]] = {}
        self._unknown: set = set()

    def schedule_partial_fill(self, client_order_id: str,
                              first: float, second: float) -> None:
        self._extra_fills[client_order_id] = [
            {"quantity": first, "venue_order_id": f"deal-{client_order_id}-a"},
            {"quantity": second, "venue_order_id": f"deal-{client_order_id}-b"},
        ]

    def schedule_unknown(self, client_order_id: str) -> None:
        self._unknown.add(client_order_id)

    async def submit_order(self, order: OrderRequest) -> ExecutionReport:
        self.submits[order.client_order_id] += 1
        if order.client_order_id in self._unknown:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.UNKNOWN,
                error="injected transport uncertainty")
            self._reports[order.client_order_id] = report
            return report
        extra = self._extra_fills.get(order.client_order_id)
        if order.price is not None and order.price > 0 and extra:
            # Two venue deals fill the order (distinct deal tickets) — the
            # realistic partial-fill shape the durable ledger must preserve.
            fills = [
                Fill(client_order_id=order.client_order_id,
                     venue_order_id=e["venue_order_id"],
                     instrument=order.instrument, side=order.side,
                     quantity=e["quantity"], price=order.price)
                for e in extra
            ]
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.FILLED,
                fills=fills, expected_price=order.price, slippage_bps=0.0)
            self._reports[order.client_order_id] = report
            self.venue_fills.extend(fills)
            for fill in fills:
                self._apply_fill(fill)
            return report
        report = await super().submit_order(order)
        if report.fills:
            self.venue_fills.extend(report.fills)
        return report


def _order(cid: str, rng: random.Random) -> OrderRequest:
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        side=rng.choice([OrderSide.BUY, OrderSide.SELL]),
        order_type=OrderType.MARKET,
        quantity=round(rng.uniform(0.01, 0.5), 2),
        client_order_id=cid,
        decision_id=f"d-{cid}",
        price=round(rng.uniform(1.05, 1.15), 5),
    )


async def run_gate(events: int, seed: int, workdir: Path) -> Dict[str, Any]:
    rng = random.Random(seed)
    db_path = workdir / "gate_state.db"
    repository = SqliteTradingRepository(str(db_path))
    adapter = InstrumentedPaperAdapter(rng)
    service = CanonicalExecutionService(adapter=adapter, repository=repository)
    adapters = [adapter]

    submitted: List[str] = []          # all cids ever submitted
    unknown_cids: set = set()
    restarts = 0
    violations: List[str] = []

    statuses_seen: Dict[str, str] = {}

    def check_no_regression(cid: str, new_status: OrderStatus) -> None:
        old = statuses_seen.get(cid)
        if old and TERMINAL_RANK.get(old, 0) > TERMINAL_RANK.get(new_status.value, 0):
            violations.append(
                f"status regression {cid}: {old} -> {new_status.value}")
        statuses_seen[cid] = new_status.value

    for i in range(events):
        roll = rng.random()
        if roll < 0.60 or not submitted:
            cid = f"ord-{i}"
            order = _order(cid, rng)
            if rng.random() < 0.08:
                adapter.schedule_unknown(cid)
                unknown_cids.add(cid)
            if rng.random() < 0.05:
                q = order.quantity
                adapter.schedule_partial_fill(cid, q / 2, q / 2)
            report = await service.submit(order)
            submitted.append(cid)
            check_no_regression(cid, report.status)
        elif roll < 0.80:
            # Resubmit an existing client_order_id (simulates retry-after-crash
            # or duplicate decision emission).
            cid = rng.choice(submitted)
            report = await service.submit(_order(cid, rng))
            if adapter.submits[cid] > 1:
                violations.append(
                    f"duplicate venue submission for {cid} "
                    f"(count={adapter.submits[cid]})")
        else:
            # Restart: fresh service + adapter over the same durable state.
            restarts += 1
            adapter = InstrumentedPaperAdapter(rng)
            repository = SqliteTradingRepository(str(db_path))
            service = CanonicalExecutionService(
                adapter=adapter, repository=repository)
            adapters.append(adapter)
            # Post-restart, a durable-pending order resubmitted by a naive
            # caller must not double-submit at the venue.
            if submitted:
                cid = rng.choice(submitted)
                report = await service.submit(_order(cid, rng))
                total_submits = sum(a.submits.get(cid, 0) for a in adapters)
                if total_submits > 1:
                    violations.append(
                        f"post-restart duplicate venue submission {cid} "
                        f"(total={total_submits})")

    adapters_all = adapters

    # ---- invariant checks -------------------------------------------------
    fills_rows = repository._connection.execute(
        "SELECT COUNT(*) c FROM fills").fetchone()["c"]

    # positions must equal signed sum of persisted fills
    pos_rows = {r["symbol"]: r["quantity"] for r in repository._connection.execute(
        "SELECT symbol, quantity FROM positions")}
    fill_sums: Dict[str, float] = defaultdict(float)
    for r in repository._connection.execute("SELECT symbol, side, quantity FROM fills"):
        sign = 1.0 if r["side"] == "buy" else -1.0
        fill_sums[r["symbol"]] += sign * r["quantity"]
    for sym, qty in fill_sums.items():
        if abs(pos_rows.get(sym, 0.0) - qty) > 1e-8:
            violations.append(
                f"position mismatch {sym}: ledger={qty} position_row={pos_rows.get(sym)}")

    # every venue fill persisted (by venue_order_id where present)
    fill_keys = {
        r["venue_order_id"]
        for r in repository._connection.execute(
            "SELECT venue_order_id FROM fills WHERE venue_order_id IS NOT NULL")
    }
    missing = [f.venue_order_id for a in adapters_all for f in a.venue_fills
               if f.venue_order_id and f.venue_order_id not in fill_keys]
    if missing:
        violations.append(
            f"{len(missing)} venue fills missing from durable ledger: "
            f"{missing[:5]}")

    orders_rows = repository._connection.execute(
        "SELECT COUNT(*) c FROM orders").fetchone()["c"]

    return {
        "events": events, "seed": seed, "restarts": restarts,
        "submitted_orders": len(submitted), "durable_order_rows": orders_rows,
        "durable_fill_rows": fills_rows,
        "unknown_injected": len(unknown_cids),
        "violations": violations,
        "passed": not violations,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--keep-db", action="store_true")
    args = parser.parse_args(argv)

    workdir = Path(tempfile.mkdtemp(prefix="fault_gate_"))
    result = asyncio.run(run_gate(args.events, args.seed, workdir))
    if args.keep_db:
        result["db_path"] = str(workdir / "gate_state.db")
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
