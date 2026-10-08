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
        self.ai_stack = None
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
        self._wire_csc_persistence()
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

    def _wire_csc_persistence(self) -> None:
        """Wire the CSC decision journal to the durable repository and attach
        the optional advisory cognition service.

        The advisory brain is disabled by default — it only attaches when
        ``enable_cognitive_advisory`` is explicitly configured, and even then
        it can only emit provenance-tagged evidence (its authority fields are
        stripped by the advisory adapter; the CSC remains sole authority).
        """
        csc = getattr(self.bot, "csc", None)
        if csc is None:
            return
        repository = getattr(self.bot, "trading_repository", None)
        if repository is not None and hasattr(csc, "configure_decision_sink"):
            csc.configure_decision_sink(repository)
        config = getattr(self.bot, "config", {}) or {}
        if config.get("enable_cognitive_advisory") and hasattr(
                csc, "configure_cognition"):
            try:
                from trading_bot.cognition.advisory_adapter import (
                    AdvisoryCognitiveBrain)

                csc.configure_cognition(AdvisoryCognitiveBrain())
            except Exception as exc:
                logger.warning(
                    "Cognitive advisory unavailable: %s", exc)
        # Read-only AI-stack projection (DOCS/CANONICAL_RUNTIME_DATAFLOW §4):
        # dashboards/tests get state/evidence/selection planes without
        # touching authority paths.
        try:
            from trading_bot.ai_stack import AIStack

            self.ai_stack = AIStack(csc)
        except Exception as exc:
            logger.warning("AI-stack projection unavailable: %s", exc)

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
            await self._block_on_reconciliation_failure(f"startup: {exc}")
        else:
            await self._check_reconciliation_result("startup")

    async def _block_on_reconciliation_failure(self, detail: str) -> None:
        """A failed or mismatched reconciliation means venue and ledger
        disagree or the venue state is unknown — either way new entries must
        stop until an operator inspects and resets the emergency stop."""
        logger.error("Reconciliation failure — blocking new entries: %s", detail)
        try:
            from trading_bot.human_layer.override import get_manual_override

            override = get_manual_override()
            await override.emergency_stop.trigger(
                f"reconciliation failure ({detail})", user="system:reconciler"
            )
        except Exception:
            logger.error(
                "Could not raise emergency stop after reconciliation failure",
                exc_info=True,
            )

    async def _check_reconciliation_result(self, context: str) -> None:
        """Trigger the entry block when the last reconciliation did not match."""
        result = self.last_reconciliation
        if result is not None and not getattr(result, "matched", False):
            await self._block_on_reconciliation_failure(
                f"{context}: mismatched venue/ledger state "
                f"{getattr(result, 'position_differences', None)}"
            )

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
        if self.ai_stack is not None:
            components["ai_stack"] = self.ai_stack
        metadata = {"read_only": True, "capital_path": "none"}
        for name, component in components.items():
            registry.register(
                f"interface_{name}",
                component,
                "Interface",
                dependencies=([] if name == "ai_stack"
                              else ["trading_repository"]),
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
            await self._block_on_reconciliation_failure(f"post-run: {exc}")
        else:
            await self._check_reconciliation_result("post-run")

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
                await self._block_on_reconciliation_failure(f"pre-stop: {exc}")
            else:
                await self._check_reconciliation_result("pre-stop")
        await self.bot.stop()
        if self._reconciler is not None:
            await self._reconciler.aclose()

    def component_graph(self) -> list:
        return self.bot.component_graph()

    async def health_check(self) -> Dict[str, Any]:
        return await self.bot.health_check()
