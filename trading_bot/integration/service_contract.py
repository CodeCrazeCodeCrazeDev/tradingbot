"""
Unified Service Contract
========================
Standard adapter/wrapper that every promoted module must satisfy.

Any module — no matter how it was originally written — can be integrated by
creating a subclass of IntegratedService and implementing the three abstract
methods: _do_start, _do_stop, _do_health_check.

The base class handles:
  - lifecycle state machine (REGISTERED → STARTING → RUNNING → STOPPING → STOPPED)
  - dependency readiness checks
  - timeout enforcement
  - degraded-mode fallback
  - telemetry emission (structured log events)
  - rollback/isolation procedures per RollbackClass
  - thread-safe status access

Promotion contract:
  To advance from WRAPPED → VERIFIED a service must pass:
    1. successful _do_start() within start_timeout_seconds
    2. healthy _do_health_check() response within health_timeout_seconds
    3. successful _do_stop() within stop_timeout_seconds
  These are enforced by the MasterIntegrationEngine.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & data structures
# ---------------------------------------------------------------------------

class ServiceLifecycle(str, Enum):
    REGISTERED = "registered"
    STARTING   = "starting"
    RUNNING    = "running"
    DEGRADED   = "degraded"   # running but impaired
    PAUSING    = "pausing"
    PAUSED     = "paused"
    STOPPING   = "stopping"
    STOPPED    = "stopped"
    ERROR      = "error"


class HealthStatus(str, Enum):
    HEALTHY   = "healthy"
    DEGRADED  = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN   = "unknown"


@dataclass
class HealthReport:
    """Standardised health payload returned by every service."""
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @property
    def operational(self) -> bool:
        return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@dataclass
class ServiceEvent:
    """Structured telemetry event emitted during lifecycle transitions."""
    service_name: str
    event_type: str        # started | stopped | health | degraded | error | rollback
    layer: int
    tier: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Base integrated service
# ---------------------------------------------------------------------------

class IntegratedService(ABC):
    """
    Base class for every promoted service.

    Subclass this and implement _do_start / _do_stop / _do_health_check.
    Optionally override _do_degrade for graceful degradation behaviour.
    """

    # ---- class-level metadata (override in subclasses) ----
    SERVICE_NAME: str = "unnamed_service"
    SERVICE_LAYER: int = 99            # ModuleLayer value
    SERVICE_TIER: str = "?"            # ModuleTier value
    SERVICE_DOMAIN: str = ""
    CAPITAL_IMPACT: str = "none"       # none | indirect | direct
    ROLLBACK_CLASS: str = "safe_disable"
    DEPENDENCIES: List[str] = []       # service names this service needs running first

    START_TIMEOUT: float = 30.0
    STOP_TIMEOUT: float  = 15.0
    HEALTH_TIMEOUT: float = 5.0

    def __init__(self, config: Optional[Dict] = None):
        self.config: Dict = config or {}
        self._lifecycle: ServiceLifecycle = ServiceLifecycle.REGISTERED
        self._health: HealthReport = HealthReport(status=HealthStatus.UNKNOWN)
        self._started_at: Optional[datetime] = None
        self._stopped_at: Optional[datetime] = None
        self._error_count: int = 0
        self._event_handlers: List[Callable[[ServiceEvent], None]] = []
        self._lock = asyncio.Lock()
        self._engine_ref: Optional[Any] = None    # set by MasterIntegrationEngine

    # -----------------------------------------------------------------------
    # Abstract interface — every service must implement these three
    # -----------------------------------------------------------------------

    @abstractmethod
    async def _do_start(self) -> None:
        """Internal startup logic. Called once by start()."""

    @abstractmethod
    async def _do_stop(self) -> None:
        """Internal shutdown logic. Called once by stop()."""

    @abstractmethod
    async def _do_health_check(self) -> HealthReport:
        """Return current health. Must complete within HEALTH_TIMEOUT seconds."""

    async def _do_degrade(self) -> None:
        """
        Optional degradation handler — called when the service enters DEGRADED.
        Default: log a warning. Override for graceful fallback logic.
        """
        logger.warning(f"[{self.SERVICE_NAME}] entering degraded mode")

    # -----------------------------------------------------------------------
    # Lifecycle management (called by engine)
    # -----------------------------------------------------------------------

    async def start(self) -> bool:
        """Start the service. Returns True on success."""
        async with self._lock:
            if self._lifecycle == ServiceLifecycle.RUNNING:
                return True
            self._lifecycle = ServiceLifecycle.STARTING
            self._emit_event("starting")

        try:
            await asyncio.wait_for(self._do_start(), timeout=self.START_TIMEOUT)
            async with self._lock:
                self._lifecycle = ServiceLifecycle.RUNNING
                self._started_at = datetime.utcnow()
            self._emit_event("started")
            logger.info(f"[{self.SERVICE_NAME}] started (layer={self.SERVICE_LAYER} tier={self.SERVICE_TIER})")
            return True

        except asyncio.TimeoutError:
            async with self._lock:
                self._lifecycle = ServiceLifecycle.ERROR
                self._error_count += 1
            self._emit_event("error", {"reason": f"start_timeout>{self.START_TIMEOUT}s"})
            logger.error(f"[{self.SERVICE_NAME}] start timed out after {self.START_TIMEOUT}s")
            return False

        except Exception as exc:
            async with self._lock:
                self._lifecycle = ServiceLifecycle.ERROR
                self._error_count += 1
            self._emit_event("error", {"reason": str(exc)})
            logger.error(f"[{self.SERVICE_NAME}] start failed: {exc}", exc_info=True)
            return False

    async def stop(self) -> bool:
        """Stop the service. Returns True on success."""
        async with self._lock:
            if self._lifecycle in (ServiceLifecycle.STOPPED, ServiceLifecycle.REGISTERED):
                return True
            self._lifecycle = ServiceLifecycle.STOPPING
            self._emit_event("stopping")

        try:
            await asyncio.wait_for(self._do_stop(), timeout=self.STOP_TIMEOUT)
            async with self._lock:
                self._lifecycle = ServiceLifecycle.STOPPED
                self._stopped_at = datetime.utcnow()
            self._emit_event("stopped")
            logger.info(f"[{self.SERVICE_NAME}] stopped")
            return True

        except asyncio.TimeoutError:
            async with self._lock:
                self._lifecycle = ServiceLifecycle.ERROR
            self._emit_event("error", {"reason": f"stop_timeout>{self.STOP_TIMEOUT}s"})
            logger.error(f"[{self.SERVICE_NAME}] stop timed out")
            return False

        except Exception as exc:
            async with self._lock:
                self._lifecycle = ServiceLifecycle.ERROR
            self._emit_event("error", {"reason": str(exc)})
            logger.error(f"[{self.SERVICE_NAME}] stop failed: {exc}")
            return False

    async def health_check(self) -> HealthReport:
        """Run a health check and cache the result."""
        t0 = time.monotonic()
        try:
            report = await asyncio.wait_for(self._do_health_check(), timeout=self.HEALTH_TIMEOUT)
            report.latency_ms = (time.monotonic() - t0) * 1000
        except asyncio.TimeoutError:
            report = HealthReport(
                status=HealthStatus.UNHEALTHY,
                message=f"health_check_timeout>{self.HEALTH_TIMEOUT}s",
                latency_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            report = HealthReport(
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
                latency_ms=(time.monotonic() - t0) * 1000,
            )

        self._health = report
        self._emit_event("health", {"status": report.status.value, "latency_ms": report.latency_ms})

        if report.status == HealthStatus.UNHEALTHY and self._lifecycle == ServiceLifecycle.RUNNING:
            await self._enter_degraded()

        return report

    async def degrade(self) -> None:
        """Externally request degraded mode."""
        await self._enter_degraded()

    async def rollback(self) -> bool:
        """
        Execute rollback procedure according to ROLLBACK_CLASS.
        Returns True if the service is now in a safe state.
        """
        rc = self.ROLLBACK_CLASS
        logger.warning(f"[{self.SERVICE_NAME}] rollback initiated (class={rc})")
        self._emit_event("rollback", {"rollback_class": rc})

        if rc == "safe_disable":
            return await self.stop()
        if rc == "degrade":
            await self._enter_degraded()
            return True
        if rc in ("isolate", "emergency"):
            ok = await self.stop()
            if not ok:
                async with self._lock:
                    self._lifecycle = ServiceLifecycle.ERROR
            return ok
        return await self.stop()

    # -----------------------------------------------------------------------
    # Status accessors
    # -----------------------------------------------------------------------

    @property
    def lifecycle(self) -> ServiceLifecycle:
        return self._lifecycle

    @property
    def is_running(self) -> bool:
        return self._lifecycle in (ServiceLifecycle.RUNNING, ServiceLifecycle.DEGRADED)

    @property
    def last_health(self) -> HealthReport:
        return self._health

    def status_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.SERVICE_NAME,
            "layer": self.SERVICE_LAYER,
            "tier": self.SERVICE_TIER,
            "lifecycle": self._lifecycle.value,
            "health": self._health.status.value,
            "health_msg": self._health.message,
            "capital_impact": self.CAPITAL_IMPACT,
            "rollback_class": self.ROLLBACK_CLASS,
            "error_count": self._error_count,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }

    # -----------------------------------------------------------------------
    # Event / telemetry
    # -----------------------------------------------------------------------

    def register_event_handler(self, handler: Callable[[ServiceEvent], None]) -> None:
        """Register a callback for service lifecycle events."""
        self._event_handlers.append(handler)

    def _emit_event(self, event_type: str, payload: Optional[Dict] = None) -> None:
        ev = ServiceEvent(
            service_name=self.SERVICE_NAME,
            event_type=event_type,
            layer=self.SERVICE_LAYER,
            tier=self.SERVICE_TIER,
            payload=payload or {},
        )
        for handler in self._event_handlers:
            try:
                handler(ev)
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    async def _enter_degraded(self) -> None:
        async with self._lock:
            if self._lifecycle == ServiceLifecycle.DEGRADED:
                return
            self._lifecycle = ServiceLifecycle.DEGRADED
        self._emit_event("degraded")
        try:
            await self._do_degrade()
        except Exception as exc:
            logger.error(f"[{self.SERVICE_NAME}] degradation handler failed: {exc}")


# ---------------------------------------------------------------------------
# Generic legacy-module adapter
# ---------------------------------------------------------------------------

class LegacyModuleAdapter(IntegratedService):
    """
    Wraps any existing module object that does not subclass IntegratedService.

    Detects common patterns:
      - start() / stop() / health_check() methods (sync or async)
      - initialize() / shutdown() methods
      - run() method wrapped in a background task

    Usage:
        from trading_bot.risk import risk_manager
        svc = LegacyModuleAdapter.from_instance(
            instance=risk_manager.RiskManager(config),
            service_name="risk_manager",
            layer=4,
            tier="A",
        )
    """

    def __init__(
        self,
        instance: Any,
        service_name: str,
        layer: int = 99,
        tier: str = "?",
        domain: str = "",
        capital_impact: str = "none",
        rollback_class: str = "safe_disable",
        config: Optional[Dict] = None,
    ):
        super().__init__(config=config)
        self._instance = instance
        self.SERVICE_NAME = service_name
        self.SERVICE_LAYER = layer
        self.SERVICE_TIER = tier
        self.SERVICE_DOMAIN = domain
        self.CAPITAL_IMPACT = capital_impact
        self.ROLLBACK_CLASS = rollback_class
        self._bg_task: Optional[asyncio.Task] = None

    @classmethod
    def from_instance(
        cls,
        instance: Any,
        service_name: str,
        layer: int = 99,
        tier: str = "?",
        domain: str = "",
        capital_impact: str = "none",
        rollback_class: str = "safe_disable",
        config: Optional[Dict] = None,
    ) -> "LegacyModuleAdapter":
        return cls(
            instance=instance,
            service_name=service_name,
            layer=layer,
            tier=tier,
            domain=domain,
            capital_impact=capital_impact,
            rollback_class=rollback_class,
            config=config,
        )

    async def _do_start(self) -> None:
        inst = self._instance
        if hasattr(inst, "start"):
            result = inst.start()
            if asyncio.iscoroutine(result):
                await result
        elif hasattr(inst, "initialize"):
            result = inst.initialize()
            if asyncio.iscoroutine(result):
                await result
        elif hasattr(inst, "run"):
            self._bg_task = asyncio.create_task(self._run_wrapper(inst))

    async def _run_wrapper(self, inst: Any) -> None:
        try:
            result = inst.run()
            if asyncio.iscoroutine(result):
                await result
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error(f"[{self.SERVICE_NAME}] background run failed: {exc}")

    async def _do_stop(self) -> None:
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except (asyncio.CancelledError, Exception):
                pass

        inst = self._instance
        if hasattr(inst, "stop"):
            result = inst.stop()
            if asyncio.iscoroutine(result):
                await result
        elif hasattr(inst, "shutdown"):
            result = inst.shutdown()
            if asyncio.iscoroutine(result):
                await result

    async def _do_health_check(self) -> HealthReport:
        inst = self._instance
        if hasattr(inst, "health_check"):
            try:
                result = inst.health_check()
                if asyncio.iscoroutine(result):
                    result = await result
                if isinstance(result, HealthReport):
                    return result
                if isinstance(result, dict):
                    ok = result.get("healthy", result.get("status", True))
                    return HealthReport(
                        status=HealthStatus.HEALTHY if ok else HealthStatus.UNHEALTHY,
                        message=result.get("message", ""),
                        metrics=result,
                    )
                if isinstance(result, bool):
                    return HealthReport(
                        status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    )
            except Exception as exc:
                return HealthReport(status=HealthStatus.UNHEALTHY, message=str(exc))

        # No health check method — assume healthy if running
        return HealthReport(status=HealthStatus.HEALTHY, message="no_health_method")

    @property
    def underlying(self) -> Any:
        return self._instance


# ---------------------------------------------------------------------------
# Null / stub service — used for disabled or unavailable modules
# ---------------------------------------------------------------------------

class StubService(IntegratedService):
    """
    A no-op service used when a module is disabled, unavailable, or quarantined.
    Satisfies the contract without doing anything.
    """

    def __init__(self, service_name: str, reason: str = "disabled"):
        super().__init__()
        self.SERVICE_NAME = service_name
        self._reason = reason

    async def _do_start(self) -> None:
        logger.debug(f"[{self.SERVICE_NAME}] StubService started ({self._reason})")

    async def _do_stop(self) -> None:
        pass

    async def _do_health_check(self) -> HealthReport:
        return HealthReport(
            status=HealthStatus.DEGRADED,
            message=f"stub:{self._reason}",
        )
