"""Public modular-monolith application boundary for AlphaAlgo."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterator, Optional

from trading_bot.unified_bot import UnifiedTradingBot

logger = logging.getLogger(__name__)


class ModularMonolithRuntime:
    """Stable application boundary; delegates decisions to the canonical bot."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.bot = UnifiedTradingBot(config or {})
        self.read_model = None
        self.dashboard_adapter = None
        self.reporting_adapter = None
        self.notification_adapter = None
        self._reconciler = None
        self.recovery_report = None
        self.last_reconciliation = None

    @property
    def running(self) -> bool:
        return self.bot.running

    async def start(self) -> None:
        self._configure_decision_audit()
        await self.bot.start()
        self._reconciler = self._build_reconciler()
        await self._recover_execution_state()
        await self._register_interface_projections()

    def _configure_decision_audit(self) -> None:
        """Give the LogAct bus a durable audit path before it starts.

        Shielded (capital-moving) actions veto when the audit log is not
        writable, so a configured path is a safety requirement, not a nicety.
        ``decision_log_path`` config overrides; an explicit falsy value opts
        out (in-memory decisions only — never for real capital movement).
        """
        config = getattr(self.bot, "config", {}) or {}
        if "decision_log_path" in config:
            log_path = config["decision_log_path"]
            if not log_path:
                logger.warning(
                    "decision_log_path disabled — LogAct decisions will be "
                    "in-memory only"
                )
                return
        else:
            state_path = str(
                config.get("trading_state_path", "alphaalgo_data/trading_state.db")
            )
            log_path = os.path.join(
                os.path.dirname(state_path) or ".", "decision_log.jsonl"
            )
        from trading_bot.core.unified_event_bus import UnifiedDecisionBus

        UnifiedDecisionBus({"log_path": log_path})

    def _build_reconciler(self) -> Any:
        """Reconciler over the canonical execution boundary, when wired."""
        service = getattr(self.bot, "execution_service", None)
        repository = getattr(self.bot, "trading_repository", None)
        if service is None or repository is None:
            return None
        from trading_bot.execution.recovery import ExecutionReconciler

        config = getattr(self.bot, "config", {}) or {}
        return ExecutionReconciler(
            service,
            repository,
            account_id=str(config.get("account_id", "runtime")),
        )

    async def _recover_execution_state(self) -> None:
        """Crash recovery: pending durable orders are reconciled via broker
        lookup (never resubmitted), then the venue book is compared against
        the persisted ledger. Repository failures propagate — there is no
        in-memory fallback for capital state."""
        if self._reconciler is None:
            return
        self.recovery_report = await self._reconciler.recover_pending_orders()
        if self.recovery_report.get("count"):
            logger.info(
                "Startup recovery reconciled %d pending orders: %s",
                self.recovery_report["count"],
                self.recovery_report["recovered"],
            )
        try:
            self.last_reconciliation = await self._reconciler.reconcile_positions()
        except Exception as exc:
            logger.error("Startup position reconciliation failed: %s", exc)

    async def _register_interface_projections(self) -> None:
        """Register read-only projections in the canonical component graph."""
        from trading_bot.core.unified_registry import registry
        from trading_bot.interfaces.adapters import (
            DashboardRuntimeAdapter,
            NotificationRuntimeAdapter,
            ReportingRuntimeAdapter,
        )
        from trading_bot.interfaces.read_models import ModularMonolithReadModel

        self.read_model = ModularMonolithReadModel(self)
        self.dashboard_adapter = DashboardRuntimeAdapter(self.read_model)
        self.reporting_adapter = ReportingRuntimeAdapter(self.read_model)
        self.notification_adapter = NotificationRuntimeAdapter(self.read_model)

        components = {
            "read_model": self.read_model,
            "dashboard_adapter": self.dashboard_adapter,
            "reporting_adapter": self.reporting_adapter,
            "notification_adapter": self.notification_adapter,
        }
        metadata = {"read_only": True, "capital_path": "none"}
        for name, component in components.items():
            registry.register(
                f"interface_{name}",
                component,
                "Interface",
                dependencies=["trading_repository"],
                metadata=metadata,
                overwrite=True,
            )

    async def _reconcile_after_run(self) -> None:
        """Post-run venue-vs-ledger check. ``bot.run()`` closes the shared
        repository handle in its finally block; the reconciler reopens the
        state file itself, so this is also the crash-consistency check that
        proves the ledger survived the session."""
        if self._reconciler is None:
            return
        try:
            self.last_reconciliation = await self._reconciler.reconcile_positions()
        except Exception as exc:
            logger.error("Post-run reconciliation failed: %s", exc)

    async def run(
        self,
        observations: Iterator[Dict[str, Any]],
        cycles: int = 0,
        interval: float = 1.0,
    ) -> None:
        await self.start()
        try:
            await self.bot.run(observations, cycles=cycles, interval=interval)
        finally:
            await self._reconcile_after_run()

    async def stop(self) -> None:
        if self._reconciler is not None and getattr(self.bot, "running", False):
            try:
                self.last_reconciliation = await self._reconciler.reconcile_positions()
            except Exception as exc:
                logger.error("Pre-stop reconciliation failed: %s", exc)
        await self.bot.stop()
        if self._reconciler is not None:
            await self._reconciler.aclose()

    def component_graph(self) -> list:
        return self.bot.component_graph()

    async def health_check(self) -> Dict[str, Any]:
        return await self.bot.health_check()
