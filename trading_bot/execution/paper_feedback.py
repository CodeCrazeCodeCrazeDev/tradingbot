"""Read-only FIFO settlement feedback from durable paper fill receipts.

No orders are submitted here. A CSC mark-only close is NOT a fill. Only an
opposite fill closes quantity, and no credit is issued for open residuals.
The fixed benchmark is a hypothetical long over each matched fill interval,
with identical quantity, contract size, and the recorded paper cost schedule.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from trading_bot.core.csc.rewards import finite

BASELINE_ID = "always_long_same_fills_v1"


def _reference(fill: Mapping[str, Any]) -> Mapping[str, Any]:
    ref = fill.get("execution_reference") or {}
    if (ref.get("schema") != "paper_fill_v1"
            or ref.get("baseline_id") != BASELINE_ID
            or ref.get("order_type") != "market"):
        raise ValueError("missing_or_unsupported_fill_reference")
    for name in ("mark_price", "spread_bps", "slippage_bps", "commission_per_unit"):
        if not finite(ref.get(name)) or ref[name] < 0:
            raise ValueError("invalid_fill_reference")
    if ref["mark_price"] <= 0:
        raise ValueError("invalid_mark")
    adverse = (ref["spread_bps"] / 2 + ref["slippage_bps"]) / 10000
    if adverse >= 1:
        raise ValueError("invalid_cost_model")
    sign = 1 if fill["side"] == "buy" else -1
    expected = ref["mark_price"] * (1 + sign * adverse)
    if (not math.isclose(fill["price"], expected, rel_tol=1e-10, abs_tol=1e-12)
            or not math.isclose(fill["commission"],
                                fill["quantity"] * ref["commission_per_unit"],
                                rel_tol=1e-10, abs_tol=1e-12)):
        raise ValueError("receipt_cost_model_mismatch")
    return ref


def _settlement(entry: dict, exit_: dict, quantity: float) -> dict:
    opening, closing = entry["fill"], exit_["fill"]
    contract = opening["instrument"]["contract_size"]
    sign = 1 if opening["side"] == "buy" else -1
    fees = quantity * (opening["commission"] / opening["quantity"]
                       + closing["commission"] / closing["quantity"])
    fill_pnl = sign * quantity * contract * (closing["price"] - opening["price"])
    identity = hashlib.sha256(json.dumps(
        [BASELINE_ID, entry["key"], exit_["key"], quantity],
        separators=(",", ":")).encode()).hexdigest()
    result = {
        "settlement_id": identity,
        "entry_fill_key": entry["key"], "exit_fill_key": exit_["key"],
        "entry_order_id": opening["client_order_id"],
        "exit_order_id": closing["client_order_id"],
        "decision_id": entry["decision_id"],
        "symbol": opening["instrument"]["symbol"],
        "direction": opening["side"], "quantity": quantity,
        "contract_size": contract, "currency": opening["instrument"]["currency"],
        "entry_time": opening["occurred_at"], "exit_time": closing["occurred_at"],
        "entry_fill_price": opening["price"], "exit_fill_price": closing["price"],
        "entry_reference": dict(opening.get("execution_reference") or {}),
        "exit_reference": dict(closing.get("execution_reference") or {}),
        "commission": fees, "net_pnl": fill_pnl - fees,
        "sample_weight": quantity / entry["order_quantity"],
        "baseline_id": BASELINE_ID, "baseline_provenance": "counterfactual",
        "origin": "paper", "gross_return": None, "cost_return": None,
        "net_return": None, "baseline_net_return": None,
        "blockers": [],
    }
    result["market_data_source"] = (opening.get("execution_reference") or {}).get(
        "market_data_source", "unknown")
    if not entry["decision_id"] or not exit_["decision_id"]:
        result["blockers"].append("missing_order_lineage")
    try:
        er, xr = _reference(opening), _reference(closing)
        if er.get("market_data_source", "unknown") != xr.get("market_data_source", "unknown"):
            raise ValueError("incompatible_market_data_sources")
        em, xm = er["mark_price"], xr["mark_price"]
        notional = quantity * contract * em
        gross = sign * quantity * contract * (xm - em)
        # Actual fill prices ALREADY include spread/slippage. Subtract only
        # recorded commissions from fill PnL; cost is the difference to marks.
        cost = gross - result["net_pnl"]
        baseline_entry = em * (1 + (er["spread_bps"] / 2 + er["slippage_bps"]) / 10000)
        baseline_exit = xm * (1 - (xr["spread_bps"] / 2 + xr["slippage_bps"]) / 10000)
        baseline_pnl = quantity * contract * (baseline_exit - baseline_entry) - fees
        if not all(finite(v) for v in (notional, gross, cost, baseline_pnl)) or notional <= 0:
            raise ValueError("invalid_return_arithmetic")
        if cost < -1e-10:
            raise ValueError("negative_cost_outside_paper_model")
        result.update(
            entry_notional=notional, gross_return=gross / notional,
            cost_return=max(0.0, cost) / notional,
            net_return=result["net_pnl"] / notional,
            baseline_net_return=baseline_pnl / notional)
    except ValueError as exc:
        result["blockers"].append(str(exc))
    return result


def match_paper_fills(receipts: Sequence[Mapping[str, Any]]) -> list[dict]:
    """Replay stable fill order, allocating fees pro-rata on every matched lot.

    Missing reference metadata still consumes inventory so it cannot cause
    newer fills to be paired with the wrong entry; its reward stays blocked.
    """
    books = defaultdict(deque)
    seen = {}
    results = []
    for row in receipts:
        key = row["fill_key"]
        if key in seen:
            if seen[key] != row["fill_json"]:
                raise ValueError("conflicting duplicate fill")
            continue
        seen[key] = row["fill_json"]
        fill = json.loads(row["fill_json"])
        order = json.loads(row["order_json"]) if row.get("order_json") else {}
        instrument = fill["instrument"]
        if instrument["venue"] != "paper":
            continue
        if (fill["side"] not in {"buy", "sell"}
                or any(not finite(fill.get(k)) or fill[k] <= 0
                       for k in ("quantity", "price"))
                or not finite(fill.get("commission")) or fill["commission"] < 0
                or not finite(instrument.get("contract_size"))
                or instrument["contract_size"] <= 0):
            raise ValueError("invalid paper fill")
        # Do not cross currencies, contract multipliers or instrument classes.
        book_key = tuple(instrument[k] for k in
                         ("symbol", "venue", "currency", "contract_size", "instrument_type"))
        queue = books[book_key]
        order_quantity = order.get("quantity", fill["quantity"])
        if (not finite(order_quantity) or order_quantity <= 0
                or fill["quantity"] > order_quantity * (1 + 1e-12)):
            raise ValueError("invalid order/fill quantity")
        current = {"key": key, "fill": fill, "decision_id": row.get("decision_id"),
                   "remaining": float(fill["quantity"]), "order_quantity": order_quantity}
        while queue and queue[0]["fill"]["side"] != fill["side"]:
            previous = queue[0]
            quantity = min(previous["remaining"], current["remaining"])
            results.append(_settlement(previous, current, quantity))
            previous["remaining"] -= quantity
            current["remaining"] -= quantity
            # Suppress only floating-point subtraction dust, relative to each
            # fill size; do not invent another lot after e.g. 0.1 + 0.2 - 0.3.
            if previous["remaining"] <= previous["fill"]["quantity"] * 1e-12:
                previous["remaining"] = 0.0
            if current["remaining"] <= fill["quantity"] * 1e-12:
                current["remaining"] = 0.0
            if previous["remaining"] <= 0:
                queue.popleft()
            if current["remaining"] <= 0:
                break
        if current["remaining"] > 0:
            queue.append(current)
    return results


class PaperSettlementFeedback:
    """Replay persisted receipts, then deliver them through CSC's audit sink.

    SQLite's deterministic audit identity handles duplicate polls and restart;
    there is no volatile 'already rewarded' flag to lose on crash.
    """
    def __init__(self, repository: Any, csc: Any):
        self.repository = repository
        self.csc = csc

    async def sync(self) -> dict:
        settlements = match_paper_fills(await self.repository.list_fill_receipts())
        added = 0
        for settlement in settlements:
            status = await self.csc.record_paper_settlement(settlement)
            added += status["status"] == "recorded"
        complete = [s for s in settlements if not s["blockers"]]
        return {
            "matched_lots": len(settlements), "new_feedback": added,
            "costed_lots": len(complete),
            "blocked_lots": len(settlements) - len(complete),
            "baseline_id": BASELINE_ID,
            "baseline_provenance": "counterfactual",
            "origin": "paper",
        }
