"""Local operator control channel and console for the canonical runtime.

Two pieces:

- ``ControlChannel`` — a filesystem command queue (one JSON file per
  command) so a separate CLI process can reach a running bot. Commands are
  validated against ``CONTROL_ACTIONS``; anything else is quarantined.
- ``OperatorConsole`` — applies drained commands inside the bot process.
  Pause/resume/emergency-stop route through the human ``ManualOverride``
  singleton (the same object ``UnifiedTradingBot.trading_allowed`` consults),
  so the override history captures every action. Capital-moving actions
  (``flatten``, ``cancel_all``) go through the canonical execution service —
  this surface cannot bypass risk/governance, it only ever restricts or
  unwinds exposure.

There is deliberately no order-entry command here: operators may stop,
pause, cancel and flatten, never open a new position.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from trading_bot.foundation.contracts import (
    AuditEvent,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
)

logger = logging.getLogger(__name__)

CONTROL_ACTIONS = frozenset(
    {"pause", "resume", "emergency_stop", "reset_emergency",
     "flatten", "cancel_all"}
)

NON_TERMINAL_ORDER_STATUSES = (
    "created", "submitted", "accepted", "partially_filled",
    "cancel_pending", "unknown",
)


class ControlChannel:
    """Filesystem command queue; atomic publish via temp-file rename."""

    def __init__(self, directory: Any) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def send(self, action: str, user: str = "operator",
             reason: str = "") -> Dict[str, Any]:
        if action not in CONTROL_ACTIONS:
            raise ValueError(
                f"unknown control action {action!r}; allowed: {sorted(CONTROL_ACTIONS)}")
        command = {
            "id": uuid.uuid4().hex,
            "action": action,
            "user": user or "operator",
            "reason": reason,
            "ts": time.time(),
        }
        tmp = self.dir / f".{command['id']}.tmp"
        tmp.write_text(json.dumps(command), encoding="utf-8")
        target = self.dir / f"cmd-{command['ts']:.6f}-{command['id'][:8]}.json"
        tmp.rename(target)
        return command

    def drain(self) -> List[Dict[str, Any]]:
        """Read and remove every pending command file, oldest first."""
        commands: List[Dict[str, Any]] = []
        for path in sorted(self.dir.glob("cmd-*.json")):
            try:
                commands.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                bad = path.with_suffix(".bad")
                try:
                    path.rename(bad)
                except OSError:
                    pass
                continue
            finally:
                try:
                    if path.exists():
                        path.unlink()
                except OSError:
                    pass
        return commands


class OperatorConsole:
    """Applies operator commands to a live UnifiedTradingBot instance."""

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        from trading_bot.human_layer.override import get_manual_override
        self.override = get_manual_override(getattr(bot, "config", None))
        self.last_price: Dict[str, float] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        from trading_bot.human_layer.override import OverrideAction
        self.override.register_handler(
            OverrideAction.CLOSE_ALL_POSITIONS, self._flatten_positions)
        self.override.register_handler(
            OverrideAction.CANCEL_ALL_ORDERS, self._cancel_all_orders)

    # -- command routing -------------------------------------------------
    async def apply(self, command: Dict[str, Any]) -> Dict[str, Any]:
        from trading_bot.human_layer.override import OverrideAction

        action = str(command.get("action", ""))
        user = str(command.get("user") or "operator")
        reason = str(command.get("reason") or "")
        if action not in CONTROL_ACTIONS:
            return {"action": action, "applied": False,
                    "error": f"unknown action {action!r}"}

        params: Dict[str, Any] = {"reason": reason} if reason else {}
        if action == "pause":
            result = await self.override.execute(
                OverrideAction.PAUSE_TRADING, user, params)
        elif action == "resume":
            result = await self.override.execute(
                OverrideAction.RESUME_TRADING, user, params)
        elif action == "emergency_stop":
            result = await self.override.execute(
                OverrideAction.EMERGENCY_STOP, user,
                params or {"reason": "operator emergency stop"})
        elif action == "reset_emergency":
            # Operator acknowledgement of an emergency stop — the only
            # sanctioned way to clear the flag, including one raised by the
            # reconciliation gate.
            from trading_bot.human_layer.override import (
                OverrideAction as _OA, OverrideResult)
            from datetime import datetime
            ok = self.override.emergency_stop.reset(user)
            result = OverrideResult(
                success=ok, action=_OA.EMERGENCY_STOP, user=user,
                timestamp=datetime.utcnow(),
                details={"emergency_cleared": ok},
                error=None if ok else "no emergency stop active")
        elif action == "flatten":
            result = await self.override.execute(
                OverrideAction.CLOSE_ALL_POSITIONS, user, params)
        else:  # cancel_all
            result = await self.override.execute(
                OverrideAction.CANCEL_ALL_ORDERS, user, params)

        outcome = {
            "action": action,
            "applied": bool(result.success),
            "error": getattr(result, "error", None),
            "details": getattr(result, "details", {}),
        }
        if outcome["applied"]:
            await self._persist_control_state()
        await self._audit(command, outcome)
        return outcome

    async def _persist_control_state(self) -> None:
        """Persist pause/emergency flags so a restart does not silently
        resume trading the operator deliberately stopped."""
        repository = getattr(self.bot, "trading_repository", None)
        if repository is None or not hasattr(repository, "set_account_state"):
            return
        try:
            await repository.set_account_state(
                "control:paused",
                "1" if self.override._trading_paused else "0")
            await repository.set_account_state(
                "control:emergency",
                "1" if self.override.emergency_stop.is_triggered else "0")
        except Exception:  # noqa: BLE001
            logger.exception("control-state persistence failed")

    async def restore_state(self) -> None:
        """Re-apply persisted pause/emergency state after a restart."""
        repository = getattr(self.bot, "trading_repository", None)
        if repository is None or not hasattr(repository, "get_account_state"):
            return
        from trading_bot.human_layer.override import OverrideAction
        try:
            emergency = await repository.get_account_state("control:emergency")
            paused = await repository.get_account_state("control:paused")
        except Exception:  # noqa: BLE001
            logger.exception("control-state restore failed closed: pausing")
            paused = "1"
            emergency = None
        if emergency == "1":
            await self.override.emergency_stop.trigger(
                "emergency stop persisted across restart",
                user="system:control-restore")
        if paused == "1":
            await self.override.execute(
                OverrideAction.PAUSE_TRADING, "system:control-restore",
                {"reason": "pause state persisted across restart"})

    async def _audit(self, command: Dict[str, Any],
                     outcome: Dict[str, Any]) -> None:
        repository = getattr(self.bot, "trading_repository", None)
        if repository is None or not hasattr(repository, "record_audit_event"):
            return
        try:
            await repository.record_audit_event(AuditEvent(
                event_type="operator_control",
                actor=str(command.get("user") or "operator"),
                action=str(command.get("action")),
                outcome="applied" if outcome.get("applied") else "failed",
                correlation_id=str(command.get("id") or uuid.uuid4().hex),
                details={"command": dict(command), "outcome": dict(outcome)},
            ))
        except Exception:  # noqa: BLE001 - audit must not break control
            logger.exception("operator control audit write failed")

    # -- capital-moving handlers (canonical execution service only) ------
    async def _flatten_positions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        service = getattr(self.bot, "execution_service", None)
        if service is None or getattr(service, "adapter", None) is None:
            return {"error": "no canonical execution service wired"}
        positions = await service.adapter.get_positions()
        closed: List[Dict[str, Any]] = []
        for position in positions:
            quantity = float(position.quantity)
            if quantity == 0.0:
                continue
            side = OrderSide.SELL if quantity > 0 else OrderSide.BUY
            price = (self.last_price.get(position.instrument.symbol)
                     or position.average_price)
            order = OrderRequest(
                instrument=position.instrument,
                side=side,
                order_type=OrderType.MARKET,
                quantity=abs(quantity),
                client_order_id=f"flatten-{uuid.uuid4().hex[:12]}",
                decision_id="operator-flatten",
                price=price,
                metadata={"operator_action": "flatten"},
            )
            report = await service.submit(order)
            closed.append({
                "symbol": position.instrument.symbol,
                "quantity": abs(quantity),
                "status": report.status.value,
            })
        return {"closed": closed, "count": len(closed)}

    async def _cancel_all_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        service = getattr(self.bot, "execution_service", None)
        repository = getattr(self.bot, "trading_repository", None)
        cancelled: List[str] = []
        pending = getattr(service, "_reports", {}) or {}
        for client_order_id, report in pending.items():
            if getattr(report, "status", None) in (
                OrderStatus.SUBMITTED, OrderStatus.ACCEPTED,
                OrderStatus.PARTIALLY_FILLED, OrderStatus.CANCEL_PENDING,
            ):
                if await service.cancel(client_order_id):
                    cancelled.append(client_order_id)
        if repository is not None and hasattr(repository, "list_orders"):
            try:
                rows = await repository.list_orders(
                    statuses=list(NON_TERMINAL_ORDER_STATUSES))
                for row in rows:
                    cid = row.get("client_order_id")
                    if cid and cid not in cancelled and cid not in pending:
                        if await service.cancel(cid):
                            cancelled.append(cid)
            except Exception:  # noqa: BLE001
                logger.exception("repository order scan failed during cancel_all")
        return {"cancelled": cancelled, "count": len(cancelled)}

    # -- state -----------------------------------------------------------
    def control_state(self) -> Dict[str, Any]:
        return self.override.get_status()
