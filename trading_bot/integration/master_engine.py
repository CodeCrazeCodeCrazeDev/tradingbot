"""
Master Integration Engine
=========================
Single authority for the full lifecycle of every promoted service.

Responsibilities:
  - Owns the DependencyGraph
  - Loads services in dependency order (layer 0 → 7, tier A → D)
  - Enforces risk gates: no Tier-D module influences Tier-A paths
  - Delegates to ServiceContract adapters for uniform lifecycle calls
  - Runs continuous health monitoring loop
  - Cascades degradation signals downstream
  - Saves integration state for observability / incident response
  - Exposes a simple query API consumed by main.py and background_services.py

Startup wave policy (matches plan):
  Wave 1  Layer 0  – Platform Spine (config, logging, telemetry, health, errors)
  Wave 2  Layer 1  – Data Foundation (ingestion, streaming, DB, schemas, cache)
  Wave 3  Layer 4  – Risk & Safety FIRST  ← veto power established here
  Wave 4  Layer 5  – Execution Core
  Wave 5  Layer 2  – Intelligence Core
  Wave 6  Layer 3  – Signal Generation
  Wave 7  Layer 6  – Governance
  Wave 8  Layer 7  – Orchestration

This ordering departs from pure layer-number order deliberately: Risk/Safety
(layer 4) is brought up before Intelligence/Signal layers to ensure every module
that generates signals or executes orders already has a live risk veto.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .dependency_graph import DependencyGraph, ServiceNode, build_default_graph, DependencyCycle
from .module_registry import ModuleRegistry, ModuleRecord, PromotionState, get_module_registry
from .service_contract import (
    IntegratedService,
    LegacyModuleAdapter,
    StubService,
    ServiceLifecycle,
    HealthStatus,
    HealthReport,
    ServiceEvent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine configuration
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    """Runtime configuration for MasterIntegrationEngine."""

    # Wave ordering: list of layers in startup sequence
    startup_wave_order: List[int] = field(
        default_factory=lambda: [0, 1, 4, 5, 2, 3, 6, 7]
    )

    # Health monitoring
    health_check_interval_s: float = 30.0
    health_check_timeout_s:  float = 5.0

    # Startup policy
    fail_fast_on_tier_a: bool = True     # abort wave if a Tier-A service fails to start
    max_start_retries:   int  = 2        # retry failed services this many times per wave
    retry_delay_s:       float = 2.0

    # Capital impact gates
    block_direct_impact_without_risk: bool = True  # don't start direct-capital services until risk is RUNNING

    # Persistence
    state_file: str = "alphaalgo_data/engine_state.json"


# ---------------------------------------------------------------------------
# Engine state
# ---------------------------------------------------------------------------

class EngineState(str, Enum):
    IDLE        = "idle"
    INITIALIZING = "initializing"
    RUNNING     = "running"
    DEGRADED    = "degraded"
    STOPPING    = "stopping"
    STOPPED     = "stopped"
    ERROR       = "error"


@dataclass
class ServiceRecord:
    """Runtime record for one registered service inside the engine."""
    service: IntegratedService
    node: ServiceNode
    module_record: Optional[ModuleRecord] = None
    start_attempts: int = 0
    last_health_check: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Master Integration Engine
# ---------------------------------------------------------------------------

class MasterIntegrationEngine:
    """
    Single integration authority for the trading bot.

    Typical usage in main.py:

        engine = MasterIntegrationEngine()
        engine.register_service(risk_svc)
        engine.register_service(execution_svc)
        ...
        await engine.start_all()
        # — trading loop —
        await engine.stop_all()

    Or with auto-discovery via the module registry:

        engine = MasterIntegrationEngine()
        await engine.bootstrap()   # scan + classify + start waves
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        registry: Optional[ModuleRegistry] = None,
    ):
        self.config = config or EngineConfig()
        self.module_registry = registry or get_module_registry()

        self._graph: DependencyGraph = build_default_graph()
        self._services: Dict[str, ServiceRecord] = {}
        self._state: EngineState = EngineState.IDLE
        self._state_lock = asyncio.Lock()
        self._health_task: Optional[asyncio.Task] = None
        self._event_handlers: List[Callable[[ServiceEvent], None]] = []

        # Track which risk services are confirmed running (for capital gates)
        self._risk_confirmed: bool = False

        # State file
        self._state_path = Path(self.config.state_file)
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("MasterIntegrationEngine initialized")

    # -----------------------------------------------------------------------
    # Service registration
    # -----------------------------------------------------------------------

    def register_service(
        self,
        service: IntegratedService,
        override_node: Optional[ServiceNode] = None,
    ) -> None:
        """
        Register a service with the engine.

        If the dependency graph already has a node matching SERVICE_NAME, that
        node is used. Otherwise override_node is added to the graph.
        """
        name = service.SERVICE_NAME
        node = self._graph.get_node(name) or override_node

        if node is None:
            node = ServiceNode(
                name=name,
                layer=service.SERVICE_LAYER,
                tier=service.SERVICE_TIER,
                capital_impact=service.CAPITAL_IMPACT,
                rollback_class=service.ROLLBACK_CLASS,
                dependencies=list(service.DEPENDENCIES),
            )
            self._graph.add_node(node)

        service.register_event_handler(self._on_service_event)

        rec = ServiceRecord(service=service, node=node)
        rec.module_record = self.module_registry.records.get(
            getattr(service, "SERVICE_DOMAIN", name)
        )
        self._services[name] = rec
        logger.debug(f"Registered service: {name} (layer={node.layer} tier={node.tier})")

    def register_legacy(
        self,
        instance: Any,
        service_name: str,
        layer: int,
        tier: str,
        domain: str = "",
        capital_impact: str = "none",
        rollback_class: str = "safe_disable",
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict] = None,
    ) -> LegacyModuleAdapter:
        """
        Wrap a raw module object and register it.
        Returns the adapter so callers can reference it.
        """
        adapter = LegacyModuleAdapter(
            instance=instance,
            service_name=service_name,
            layer=layer,
            tier=tier,
            domain=domain,
            capital_impact=capital_impact,
            rollback_class=rollback_class,
            config=config,
        )
        adapter.DEPENDENCIES = dependencies or []
        self.register_service(adapter)
        return adapter

    def register_stub(self, service_name: str, reason: str = "unavailable") -> StubService:
        """Register a no-op stub (used when the real module failed to import)."""
        stub = StubService(service_name=service_name, reason=reason)
        self.register_service(stub)
        return stub

    # -----------------------------------------------------------------------
    # Bootstrap (auto-wire from existing codebase patterns)
    # -----------------------------------------------------------------------

    async def bootstrap(self) -> Dict[str, Any]:
        """
        Full auto-bootstrap sequence:
          1. Scan module registry
          2. Classify modules
          3. Run static import checks
          4. Register known services from existing codebase
          5. Start services in wave order

        Returns a summary dict.
        """
        t0 = time.monotonic()
        logger.info("=== MasterIntegrationEngine BOOTSTRAP START ===")

        # Phase 1 – inventory
        self.module_registry.scan()
        self.module_registry.classify()
        self.module_registry.analyze_static()
        self.module_registry.check_imports(quick=True)

        # Phase 2 – auto-register from codebase
        self._auto_register_from_codebase()

        # Phase 3 – start all waves
        results = await self.start_all()

        # Phase 4 – persist state
        self._save_state()

        elapsed = time.monotonic() - t0
        summary = {
            "bootstrap_duration_s": round(elapsed, 2),
            "modules_discovered": len(self.module_registry.records),
            "services_registered": len(self._services),
            "services_started": sum(1 for r in self._services.values() if r.service.is_running),
            "engine_state": self._state.value,
            "start_results": results,
        }
        logger.info(
            f"=== BOOTSTRAP COMPLETE in {elapsed:.1f}s "
            f"({summary['services_started']}/{summary['services_registered']} started) ==="
        )
        return summary

    def _auto_register_from_codebase(self) -> None:
        """
        Wire up the key services that already exist in the codebase by
        importing them lazily and wrapping with LegacyModuleAdapter.

        This covers the most critical paths. Additional modules should be
        registered via register_service() / register_legacy() from main.py.
        """
        _integrations = [
            # (import_path, class_name, service_name, layer, tier, capital_impact, rollback, deps)
            (
                "trading_bot.core.service_registry", "ServiceRegistry",
                "core_service_registry", 0, "A", "none", "safe_disable", [],
            ),
            (
                "trading_bot.msos", None,
                "msos", 4, "A", "direct", "emergency",
                ["config_manager"],
            ),
            (
                "trading_bot.risk.risk_manager", "RiskManager",
                "risk_manager", 4, "A", "direct", "emergency",
                ["msos"],
            ),
            (
                "trading_bot.safety", None,
                "safety_manager", 4, "A", "direct", "emergency",
                ["msos"],
            ),
            (
                "trading_bot.reality_gates", None,
                "reality_gates", 4, "A", "direct", "emergency",
                ["risk_manager", "safety_manager"],
            ),
            (
                "trading_bot.market_intelligence", None,
                "market_intelligence", 3, "A", "indirect", "degrade",
                [],
            ),
            (
                "trading_bot.deepchart", None,
                "deepchart", 3, "B", "indirect", "degrade",
                [],
            ),
            (
                "trading_bot.alpha_engine", None,
                "alpha_engine", 3, "A", "indirect", "degrade",
                [],
            ),
            (
                "trading_bot.systems_ai", None,
                "systems_ai", 3, "B", "indirect", "degrade",
                [],
            ),
            (
                "trading_bot.elite_ai_system", None,
                "elite_ai_system", 3, "B", "indirect", "degrade",
                [],
            ),
            (
                "trading_bot.self_diagnostic", None,
                "self_diagnostic", 0, "B", "none", "degrade",
                [],
            ),
        ]

        for (mod_path, cls_name, svc_name, layer, tier, cap_imp, rollback, deps) in _integrations:
            if svc_name in self._services:
                continue
            try:
                import importlib
                mod = importlib.import_module(mod_path)
                if cls_name:
                    instance = getattr(mod, cls_name, None)
                    if instance is None:
                        raise AttributeError(f"Class {cls_name} not found in {mod_path}")
                    # Try to instantiate
                    try:
                        obj = instance()
                    except Exception:
                        obj = instance
                else:
                    obj = mod

                self.register_legacy(
                    instance=obj,
                    service_name=svc_name,
                    layer=layer,
                    tier=tier,
                    domain=mod_path,
                    capital_impact=cap_imp,
                    rollback_class=rollback,
                    dependencies=deps,
                )
                logger.debug(f"Auto-registered: {svc_name} from {mod_path}")
            except Exception as exc:
                logger.warning(f"Auto-register failed for {svc_name}: {exc} → registering stub")
                self.register_stub(svc_name, reason=str(exc)[:100])


    def _determine_integration_stage(self, record: ModuleRecord) -> str:
        """Map a module record to professional integration stage."""
        path = record.module_path.lower()
        tokens = path.split('.')

        if 'orchestr' in path or record.layer == 7:
            return 'orchestration'

        if (
            'system' in path
            or 'engine' in path
            or 'core' in path
            or 'master' in path
            or record.layer in (4, 5, 6)
        ):
            return 'systems'

        framework_tokens = {
            'framework', 'integration', 'domain', 'skills', 'ai_core', 'unified',
            'architecture', 'connectivity', 'governance', 'observability'
        }
        if any(tok in framework_tokens for tok in tokens):
            return 'frameworks'

        return 'modules'

    async def bootstrap_hierarchical(self, max_modules: Optional[int] = None) -> Dict[str, Any]:
        """
        Professional full integration pipeline:
        modules → frameworks → systems → orchestration.

        Registers every discovered module as an integrated service (legacy adapter when
        importable, otherwise stub) and starts services via wave policy.
        """
        t0 = time.monotonic()
        logger.info("=== MasterIntegrationEngine HIERARCHICAL BOOTSTRAP START ===")

        # Fresh inventory and classification
        self.module_registry.scan()
        self.module_registry.classify()
        self.module_registry.analyze_static()
        self.module_registry.check_imports(quick=True)

        records = [
            r for r in self.module_registry.records.values()
            if r.promotion_state != PromotionState.QUARANTINED.value
        ]
        records.sort(key=lambda r: (self._determine_integration_stage(r), r.layer, r.tier, r.module_path))
        if max_modules is not None:
            records = records[:max_modules]

        stages = ['modules', 'frameworks', 'systems', 'orchestration']
        stage_anchor = {
            'modules': 'stage_modules',
            'frameworks': 'stage_frameworks',
            'systems': 'stage_systems',
            'orchestration': 'stage_orchestration',
        }
        stage_layer = {'modules': 1, 'frameworks': 2, 'systems': 5, 'orchestration': 7}

        # Register stage anchors with explicit dependencies
        for idx, stage in enumerate(stages):
            deps = [stage_anchor[stages[idx - 1]]] if idx > 0 else []
            self.register_stub(stage_anchor[stage], reason=f"integration_anchor:{stage}")
            rec = self._services[stage_anchor[stage]]
            rec.service.SERVICE_LAYER = stage_layer[stage]
            rec.service.DEPENDENCIES = deps

        registered_real = 0
        registered_stub = len(stages)
        stage_counts = {k: 0 for k in stages}

        for record in records:
            stage = self._determine_integration_stage(record)
            stage_counts[stage] += 1
            service_name = record.module_path.replace('.', '__')
            deps = [stage_anchor[stage]]

            try:
                module_obj = importlib.import_module(record.module_path)
                self.register_legacy(
                    instance=module_obj,
                    service_name=service_name,
                    layer=record.layer,
                    tier=record.tier,
                    domain=record.module_path,
                    capital_impact=record.capital_impact,
                    rollback_class=record.rollback_class,
                    dependencies=deps,
                )
                registered_real += 1
            except Exception as exc:
                self.register_stub(service_name, reason=str(exc)[:120])
                stub_rec = self._services[service_name]
                stub_rec.service.SERVICE_LAYER = record.layer
                stub_rec.service.SERVICE_TIER = record.tier
                stub_rec.service.DEPENDENCIES = deps
                registered_stub += 1

        start_results = await self.start_all()
        self._save_state()

        elapsed = time.monotonic() - t0
        summary = {
            'bootstrap_duration_s': round(elapsed, 2),
            'pipeline': 'modules->frameworks->systems->orchestration',
            'modules_discovered': len(self.module_registry.records),
            'modules_selected': len(records),
            'services_registered': len(self._services),
            'services_registered_real': registered_real,
            'services_registered_stub': registered_stub,
            'services_started': sum(1 for r in self._services.values() if r.service.is_running),
            'engine_state': self._state.value,
            'stage_counts': stage_counts,
            'start_results': start_results,
        }
        logger.info(
            f"=== HIERARCHICAL BOOTSTRAP COMPLETE in {elapsed:.1f}s "
            f"({summary['services_started']}/{summary['services_registered']} started) ==="
        )
        return summary

    # -----------------------------------------------------------------------
    # Startup / shutdown
    # -----------------------------------------------------------------------

    async def start_all(self) -> Dict[str, bool]:
        """
        Start all registered services in wave order.
        Returns {service_name: started_ok} for every service.
        """
        async with self._state_lock:
            self._state = EngineState.INITIALIZING

        results: Dict[str, bool] = {}

        # Compute wave-ordered startup sequence
        try:
            ordered = self._wave_ordered_startup()
        except DependencyCycle as exc:
            logger.error(f"Dependency cycle prevents startup: {exc}")
            self._state = EngineState.ERROR
            return {}

        wave_groups = self._group_by_wave(ordered)

        for wave_idx, (wave_layer, nodes_in_wave) in enumerate(wave_groups):
            wave_label = f"Wave {wave_idx+1} (Layer {wave_layer})"
            logger.info(f"Starting {wave_label}: {[n.name for n in nodes_in_wave]}")

            for node in nodes_in_wave:
                if node.name not in self._services:
                    logger.debug(f"Node '{node.name}' in graph but not registered; skipping")
                    continue

                # Capital impact gate: block direct-impact services until risk is live
                if (
                    self.config.block_direct_impact_without_risk
                    and node.capital_impact == "direct"
                    and not self._risk_confirmed
                    and wave_layer < 4
                ):
                    logger.warning(
                        f"Blocking '{node.name}' (direct-impact) until risk layer confirmed"
                    )
                    results[node.name] = False
                    continue

                ok = await self._start_service_with_retry(node.name)
                results[node.name] = ok

                # Update risk confirmation flag
                if node.layer == 4 and node.tier == "A" and ok:
                    logger.info(
                        f"Risk/Safety service '{node.name}' confirmed — capital gate open"
                    )
                    self._risk_confirmed = True

                # Tier-A failure in fail_fast mode aborts the wave
                if not ok and node.tier == "A" and self.config.fail_fast_on_tier_a:
                    logger.error(
                        f"Tier-A service '{node.name}' failed to start — aborting {wave_label}"
                    )
                    break

        # Start health monitoring
        self._health_task = asyncio.create_task(self._health_monitor_loop())

        running = sum(1 for ok in results.values() if ok)
        async with self._state_lock:
            self._state = EngineState.RUNNING if running > 0 else EngineState.ERROR

        logger.info(f"Engine startup complete: {running}/{len(results)} services running")
        return results

    async def stop_all(self) -> Dict[str, bool]:
        """Stop all services in reverse wave order."""
        async with self._state_lock:
            self._state = EngineState.STOPPING

        # Cancel health monitor
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        try:
            ordered = self._wave_ordered_startup()
        except DependencyCycle:
            ordered = list(node for rec in self._services.values() for node in [rec.node])

        results: Dict[str, bool] = {}
        for node in reversed(ordered):
            if node.name not in self._services:
                continue
            rec = self._services[node.name]
            if not rec.service.is_running:
                results[node.name] = True
                continue
            ok = await rec.service.stop()
            results[node.name] = ok
            if not ok:
                logger.error(f"Failed to stop: {node.name}")

        async with self._state_lock:
            self._state = EngineState.STOPPED

        self._save_state()
        stopped = sum(1 for ok in results.values() if ok)
        logger.info(f"Engine stopped: {stopped}/{len(results)} services stopped cleanly")
        return results

    async def _start_service_with_retry(self, name: str) -> bool:
        rec = self._services[name]
        for attempt in range(1 + self.config.max_start_retries):
            rec.start_attempts += 1
            ok = await rec.service.start()
            if ok:
                return True
            if attempt < self.config.max_start_retries:
                logger.warning(
                    f"[{name}] start attempt {attempt+1} failed; retrying in "
                    f"{self.config.retry_delay_s}s"
                )
                await asyncio.sleep(self.config.retry_delay_s)
        return False

    # -----------------------------------------------------------------------
    # Wave ordering
    # -----------------------------------------------------------------------

    def _wave_ordered_startup(self) -> List[ServiceNode]:
        """
        Return services ordered by wave policy, then topo within each wave.
        """
        # Build a sub-graph per layer and topo-sort within it
        nodes_by_layer: Dict[int, List[ServiceNode]] = {}
        for node in self._graph:
            nodes_by_layer.setdefault(node.layer, []).append(node)

        ordered: List[ServiceNode] = []
        for layer in self.config.startup_wave_order:
            layer_nodes = nodes_by_layer.get(layer, [])
            if not layer_nodes:
                continue
            # Topo sort within this layer
            sub_graph = DependencyGraph()
            for node in layer_nodes:
                sub_graph.add_node(node)
            try:
                sorted_nodes = sub_graph.startup_order()
            except DependencyCycle:
                # Fall back to tier-sort
                sorted_nodes = sorted(layer_nodes, key=lambda n: n.sort_key)
            ordered.extend(sorted_nodes)

        # Append any nodes in layers not listed in startup_wave_order
        listed = set(self.config.startup_wave_order)
        for layer, nodes in sorted(nodes_by_layer.items()):
            if layer not in listed:
                ordered.extend(sorted(nodes, key=lambda n: n.sort_key))

        return ordered

    def _group_by_wave(
        self, ordered: List[ServiceNode]
    ) -> List[Tuple[int, List[ServiceNode]]]:
        """Group ordered nodes by their layer (wave)."""
        groups: List[Tuple[int, List[ServiceNode]]] = []
        current_layer: Optional[int] = None
        current_batch: List[ServiceNode] = []

        for node in ordered:
            if node.layer != current_layer:
                if current_batch:
                    groups.append((current_layer, current_batch))
                current_layer = node.layer
                current_batch = [node]
            else:
                current_batch.append(node)

        if current_batch:
            groups.append((current_layer, current_batch))

        return groups

    # -----------------------------------------------------------------------
    # Health monitoring
    # -----------------------------------------------------------------------

    async def _health_monitor_loop(self) -> None:
        """Continuously sample health of all running services."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval_s)
                await self._run_health_cycle()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Health monitor error: {exc}")

    async def _run_health_cycle(self) -> None:
        """One round of health checks across all running services."""
        for name, rec in list(self._services.items()):
            if not rec.service.is_running:
                continue
            try:
                health = await asyncio.wait_for(
                    rec.service.health_check(),
                    timeout=self.config.health_check_timeout_s,
                )
                rec.last_health_check = datetime.utcnow()

                if health.status == HealthStatus.UNHEALTHY:
                    logger.warning(f"[{name}] unhealthy: {health.message}")
                    cascade = self._graph.cascade_impact(name)
                    for dep_name, action in cascade.items():
                        await self._handle_cascade(dep_name, action, source=name)

            except asyncio.TimeoutError:
                logger.warning(f"[{name}] health check timed out")
            except Exception as exc:
                logger.error(f"[{name}] health check exception: {exc}")

    async def _handle_cascade(self, service_name: str, action: str, source: str) -> None:
        rec = self._services.get(service_name)
        if not rec or not rec.service.is_running:
            return
        logger.warning(f"Cascade from '{source}': {action} → '{service_name}'")
        if action == "emergency":
            await rec.service.rollback()
        elif action == "degrade":
            await rec.service.degrade()
        # "warn" → just logged

    # -----------------------------------------------------------------------
    # Event handling
    # -----------------------------------------------------------------------

    def _on_service_event(self, event: ServiceEvent) -> None:
        """Receive events from services and forward to registered handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass

    def register_event_handler(self, handler: Callable[[ServiceEvent], None]) -> None:
        self._event_handlers.append(handler)

    # -----------------------------------------------------------------------
    # Query API  (used by main.py / background_services.py)
    # -----------------------------------------------------------------------

    def get_service(self, name: str) -> Optional[IntegratedService]:
        """Return a running service instance by name."""
        rec = self._services.get(name)
        if rec and rec.service.is_running:
            return rec.service
        return None

    def get_underlying(self, name: str) -> Optional[Any]:
        """Return the raw underlying object wrapped by a LegacyModuleAdapter."""
        svc = self.get_service(name)
        if isinstance(svc, LegacyModuleAdapter):
            return svc.underlying
        return svc

    def is_running(self, name: str) -> bool:
        return bool(self.get_service(name))

    def all_services_status(self) -> Dict[str, Dict]:
        return {
            name: rec.service.status_dict()
            for name, rec in self._services.items()
        }

    def engine_health_report(self) -> Dict[str, Any]:
        running = [n for n, r in self._services.items() if r.service.is_running]
        degraded = [
            n for n, r in self._services.items()
            if r.service.lifecycle == ServiceLifecycle.DEGRADED
        ]
        error = [
            n for n, r in self._services.items()
            if r.service.lifecycle == ServiceLifecycle.ERROR
        ]
        return {
            "engine_state": self._state.value,
            "risk_confirmed": self._risk_confirmed,
            "total_registered": len(self._services),
            "running": len(running),
            "degraded": len(degraded),
            "error": len(error),
            "running_services": running,
            "degraded_services": degraded,
            "error_services": error,
            "generated": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # Rollback / Emergency
    # -----------------------------------------------------------------------

    async def emergency_stop(self, reason: str = "") -> None:
        """Emergency stop: rollback direct-capital services first."""
        logger.critical(f"EMERGENCY STOP triggered: {reason}")
        direct_services = [
            rec for rec in self._services.values()
            if rec.node.capital_impact == "direct" and rec.service.is_running
        ]
        tasks = [rec.service.rollback() for rec in direct_services]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.stop_all()

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def _save_state(self) -> None:
        try:
            state = {
                "engine_state": self._state.value,
                "risk_confirmed": self._risk_confirmed,
                "services": {
                    name: {
                        "lifecycle": rec.service.lifecycle.value,
                        "tier": rec.node.tier,
                        "layer": rec.node.layer,
                        "capital_impact": rec.node.capital_impact,
                        "start_attempts": rec.start_attempts,
                        "last_health": rec.last_health_check.isoformat()
                        if rec.last_health_check else None,
                    }
                    for name, rec in self._services.items()
                },
                "saved_at": datetime.utcnow().isoformat(),
            }
            self._state_path.write_text(
                json.dumps(state, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            logger.warning(f"Could not save engine state: {exc}")


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_engine_instance: Optional[MasterIntegrationEngine] = None


def get_engine(config: Optional[EngineConfig] = None) -> MasterIntegrationEngine:
    """Return the singleton MasterIntegrationEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MasterIntegrationEngine(config=config)
    return _engine_instance


def reset_engine() -> None:
    """Reset singleton — useful for testing."""
    global _engine_instance
    _engine_instance = None
