"""Maker-capable paper venue: passive LIMIT orders + mark-TTL + bps fees.

Subclass of the canonical ``PaperBrokerAdapter`` —
``trading_bot/execution/service.py`` is protected, so this module EXTENDS
it without modification:

- ``resting_ttl_marks``: resting orders expire (EXPIRED) after N venue
  marks instead of lingering forever — a limit posted on a stale signal
  must die with the signal, not fill whenever the mark happens to cross.
- ``maker_fee_bps``: commission charged as bps-of-notional per side,
  replacing the per-unit fee model for fee-tier experiments.
- Mark-stream convention: callers may feed low -> high -> close per bar
  so resting limits fill on intra-bar touches; pending market orders
  still settle at the last mark (the close) either way.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict

from trading_bot.execution.service import PaperBrokerAdapter
from trading_bot.foundation.contracts import OrderStatus


class MakerPaperAdapter(PaperBrokerAdapter):
    """Paper venue with resting-order expiry and maker fee model."""

    venue_id = "paper_maker"

    def __init__(self, *args: Any, resting_ttl_marks: int = 0,
                 maker_fee_bps: float = 0.0, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.resting_ttl_marks = max(int(resting_ttl_marks), 0)
        self.maker_fee_bps = max(float(maker_fee_bps), 0.0)
        self._resting_since: Dict[str, int] = {}
        self._mark_seq = 0

    async def submit_order(self, order):
        report = await super().submit_order(order)
        if (report.status is OrderStatus.ACCEPTED
                and order.client_order_id in self._resting):
            self._resting_since[order.client_order_id] = self._mark_seq
        return report

    def on_mark(self, symbol: str, mark: float) -> None:
        self._mark_seq += 1
        super().on_mark(symbol, mark)
        if not self.resting_ttl_marks:
            return
        for coid in list(self._resting):
            since = self._resting_since.get(coid, self._mark_seq)
            if self._mark_seq - since >= self.resting_ttl_marks:
                self._resting.pop(coid, None)
                self._resting_since.pop(coid, None)
                rep = self._reports.get(coid)
                if rep is not None:
                    self._reports[coid] = replace(
                        rep, status=OrderStatus.EXPIRED,
                        error="resting order expired by mark TTL")

    async def cancel_order(self, client_order_id: str) -> bool:
        ok = await super().cancel_order(client_order_id)
        self._resting_since.pop(client_order_id, None)
        return ok

    def _fill(self, order, mark):
        report = super()._fill(order, mark)
        self._resting_since.pop(order.client_order_id, None)
        if self.maker_fee_bps and report.fills:
            fills = [replace(
                f, commission=(f.quantity * f.price
                               * self.maker_fee_bps * 1e-4))
                for f in report.fills]
            report = replace(report, fills=fills)
        return report
