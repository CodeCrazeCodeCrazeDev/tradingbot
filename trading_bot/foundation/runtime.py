"""Public modular-monolith application boundary for AlphaAlgo."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Iterator, Optional

from trading_bot.unified_bot import UnifiedTradingBot

logger = logging.getLogger(__name__)


class _ExternalFeedBridge:
    """internet_access DataAcquisitionEngine -> observation enrichment.

    Only real fetched data is injected: each source is pulled only when
    its API key is configured, and mock-fallback fields are never added.
    When a fetch fails or no key exists the key simply stays absent and
    the conditional advisory adapters emit their honest no-data status.
    """

    def __init__(self, engine: Any, cfg: Dict[str, Any]) -> None:
        self.engine = engine
        self.cfg = cfg
        self.symbols = list(cfg.get("symbols")
                            or [cfg.get("symbol", "EURUSD")])
        self.refresh_s = float(cfg.get("refresh_seconds", 300))
        self.keys = set(engine.api_keys or {})
        self._snapshot: Dict[str, Any] = {}
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while True:
            try:
                await self._refresh()
            except Exception as exc:  # noqa: BLE001 - feed must not kill run
                logger.debug("external feed refresh failed: %s", exc)
            await asyncio.sleep(self.refresh_s)

    async def _refresh(self) -> None:
        feeds: Dict[str, Any] = {}
        if "news" in self.keys:
            feeds["news_items"] = await self.engine.fetch_news_headlines(
                self.symbols)
        if "sentiment" in self.keys:
            feeds["sentiment"] = await self.engine.fetch_sentiment_metrics(
                self.symbols)
        if "macro" in self.keys:
            macro = await self.engine.fetch_macro_data()
            feeds["macro"] = macro
            # FRED interest-rate series -> cb_rates map for the CB adapter
            ir = macro.get("interest_rate") if isinstance(macro, dict) else None
            if isinstance(ir, dict) and ir.get("value") is not None:
                feeds["cb_rates"] = {"FED": ir["value"]}
        # Free public regulatory data — keyless, gated on config flags.
        alt = await self.engine.fetch_alt_data(
            self.symbols,
            cik=self.cfg.get("sec_13f_cik"),
            cot_market=self.cfg.get("cot_market"))
        feeds.update({k: v for k, v in alt.items() if v})
        # market_data fetch is same-symbol multi-TF (not a second venue),
        # so venue_prices/order_flow stay absent until a real feed exists.
        if feeds:
            self._snapshot = feeds

    def enrich(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        if self._snapshot and isinstance(obs, dict):
            obs.update(self._snapshot)
        return obs


def _build_feed_bridge(bot: Any) -> Optional[_ExternalFeedBridge]:
    """Construct the feed bridge when config['external_feeds'].enabled."""
    config = getattr(bot, "config", {}) or {}
    cfg = config.get("external_feeds") or {}
    if not cfg.get("enabled"):
        return None
    try:
        from trading_bot.internet_access.data_acquisition import (
            DataAcquisitionEngine)

        engine = DataAcquisitionEngine(
            dict(cfg), cache_dir=str(cfg.get("cache_dir", "data_cache")))
        return _ExternalFeedBridge(engine, cfg)
    except Exception as exc:  # noqa: BLE001 - optional feed
        logger.warning("External feed bridge unavailable: %s", exc)
        return None


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
        self.rsi_bridge = None
        self.rsi_memory = None

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
        the requested cognitive assembly or advisory cognition service.

        ``cognitive_assembly`` requests the canonical ``build_cognitive_system``
        path (advisors plus research). ``enable_cognitive_advisory`` remains as
        the narrower legacy switch for only ``AdvisoryCognitiveBrain``. All
        outputs are provenance-tagged evidence; the CSC remains sole authority.
        """
        csc = getattr(self.bot, "csc", None)
        if csc is None:
            return
        repository = getattr(self.bot, "trading_repository", None)
        if repository is not None and hasattr(csc, "configure_decision_sink"):
            csc.configure_decision_sink(repository)
        config = getattr(self.bot, "config", {}) or {}
        assembly_config = config.get("cognitive_assembly")
        if isinstance(assembly_config, dict):
            assembly_enabled = bool(assembly_config.get("enabled", True))
            assembly_options = assembly_config
        else:
            assembly_enabled = bool(assembly_config)
            assembly_options = {}
        if assembly_enabled:
            try:
                from trading_bot.core.csc.assembly import (
                    build_cognitive_system)

                build_cognitive_system(
                    csc,
                    research_interval=assembly_options.get(
                        "research_interval"),
                    advisory_brain=assembly_options.get(
                        "advisory_brain", True),
                    discover_advisors=assembly_options.get(
                        "discover_advisors", False))
            except Exception as exc:
                logger.warning("Cognitive assembly unavailable: %s", exc)
        elif config.get("enable_cognitive_advisory") and hasattr(
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
        self._wire_rsi_reflection()

    def _wire_rsi_reflection(self) -> None:
        """Couple the RSI substrate to the HMS reflective stores.

        The durable ImprovementMemory ledger and the RSIHMSBridge live
        beside the trading state so the recursive loop observes *this*
        runtime's failures and writes its verdicts back into HMS
        self-improvement memory. Nothing here runs a cycle by itself or
        promotes a candidate — the bridge is operator-invoked evidence
        plumbing; promotion still requires a signed OperatorAuthorization
        at the PromotionLadder (research-only per AGENTS.md).
        """
        hms = getattr(self.bot, "hms", None)
        if hms is None:
            return
        config = getattr(self.bot, "config", {}) or {}
        state_path = str(
            config.get("trading_state_path", "alphaalgo_data/trading_state.db"))
        rsi_dir = os.path.join(os.path.dirname(state_path) or ".", "rsi")
        try:
            from trading_bot.recursive_self_improvement.hms_bridge import (
                RSIHMSBridge)
            from trading_bot.recursive_self_improvement.memory import (
                ImprovementMemory)

            self.rsi_memory = ImprovementMemory(
                os.path.join(rsi_dir, "improvement_memory.db"))
            self.rsi_bridge = RSIHMSBridge(hms=hms, memory=self.rsi_memory)
            from trading_bot.core.unified_registry import registry

            registry.register(
                "rsi_bridge", self.rsi_bridge, "Intelligence",
                dependencies=["hms"],
                metadata={"read_only": True, "capital_path": "none",
                          "authority": "research_only"},
                overwrite=True)
        except Exception as exc:  # noqa: BLE001 - reflection is advisory
            logger.warning("RSI reflection wiring unavailable: %s", exc)
            self.rsi_bridge = None
            self.rsi_memory = None

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
        bridge = _build_feed_bridge(self.bot)
        if bridge is not None:
            await bridge.start()

            def _enriched():
                for obs in observations:
                    yield bridge.enrich(obs)

            observations = _enriched()
        try:
            await self.bot.run(observations, cycles=cycles, interval=interval)
        finally:
            if bridge is not None:
                await bridge.stop()
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
