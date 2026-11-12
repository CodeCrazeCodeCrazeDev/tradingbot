"""Disaster Recovery Management
============================================================

Lifecycle monitor on top of the canonical backup/state machinery in
``trading_bot.core.backup_recovery``. Provides the surface
``elite_master_system`` imports:

- ``SystemState`` — monitor lifecycle enum
- ``StateManager`` — re-exported persistent key/value state store
- ``DisasterRecoveryManager`` — periodic component backups plus a
  registered-handler emergency close surface
- ``get_disaster_recovery_manager`` — process-wide singleton

The manager never touches the execution path itself: emergency close runs
whatever handlers the host system registered (flatten, cancel, shutdown)
in order, then forces a final state backup so a restart can reconcile the
ledger against broker state.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from trading_bot.core.backup_recovery import BackupManager, StateManager

logger = logging.getLogger(__name__)


class SystemState(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


class DisasterRecoveryManager:
    """Periodic state backup + emergency recovery coordinator.

    Monitoring is a supervised asyncio loop calling
    ``BackupManager.create_backup`` on an interval; a backup failure
    degrades the manager (state -> DEGRADED) rather than taking the
    process down. ``emergency_close_all`` runs registered close handlers
    in registration order and then forces a final backup.
    """

    def __init__(
        self,
        backup_dir: str = "state/backups",
        state_file: str = "state/dr_state.json",
        backup_interval_seconds: int = 300,
        max_backups: int = 10,
    ):
        self.state = SystemState.INITIALIZING
        self.backup_manager = BackupManager(
            backup_dir=backup_dir,
            max_backups=max_backups,
            backup_interval_seconds=backup_interval_seconds,
        )
        self.state_manager = StateManager(state_file)
        self.backup_interval = backup_interval_seconds
        self._monitor_task: Optional[asyncio.Task] = None
        self._close_handlers: List[Callable[[str], Any]] = []
        self._last_error: Optional[str] = None
        self._last_backup_at: Optional[datetime] = None
        self.state = SystemState.READY

    # ---------- wiring ----------

    def register_component(self, name: str, component: Any):
        """Register a component whose state is captured in each backup."""
        self.backup_manager.register_component(name, component)

    def register_emergency_close(self, handler: Callable[[str], Any]):
        """Register an emergency close handler.

        ``handler(reason)`` may be sync or a coroutine — both are awaited
        correctly by ``emergency_close_all``.
        """
        self._close_handlers.append(handler)

    # ---------- lifecycle ----------

    async def start_monitoring(self):
        """Start the periodic backup loop (idempotent)."""
        if self._monitor_task is not None and not self._monitor_task.done():
            return
        self.state = SystemState.RUNNING
        self._monitor_task = asyncio.ensure_future(self._monitor_loop())
        logger.info(
            "Disaster recovery monitoring started (interval=%ds, dir=%s)",
            self.backup_interval, self.backup_manager.backup_dir)

    async def _monitor_loop(self):
        try:
            while self.state == SystemState.RUNNING:
                meta = await self.backup_manager.create_backup("scheduled")
                if meta is not None:
                    self._last_backup_at = datetime.now()
                await asyncio.sleep(self.backup_interval)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 — degrade, never crash the host
            self._last_error = str(exc)
            self.state = SystemState.DEGRADED
            logger.error("Disaster recovery monitor failed: %s", exc)

    async def stop_monitoring(self):
        """Stop the monitor and take a final shutdown backup."""
        self.state = SystemState.SHUTDOWN
        task = self._monitor_task
        self._monitor_task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        await self.backup_manager.create_backup("shutdown")
        logger.info("Disaster recovery monitoring stopped")

    # ---------- emergency ----------

    async def emergency_close_all(self, reason: str = "") -> Dict[str, Any]:
        """Run every registered emergency-close handler, then back up.

        Handlers run in registration order; a failing handler is logged
        and recorded but does not block the remaining handlers or the
        final state backup.
        """
        self.state = SystemState.EMERGENCY
        logger.critical("Disaster recovery: EMERGENCY close-all (%s)", reason)
        errors: List[str] = []
        succeeded = 0
        for handler in list(self._close_handlers):
            try:
                result = handler(reason)
                if asyncio.iscoroutine(result):
                    await result
                succeeded += 1
            except Exception as exc:  # noqa: BLE001 — keep draining handlers
                errors.append(str(exc))
                logger.error("Emergency close handler failed: %s", exc)
        try:
            await self.backup_manager.create_backup("emergency")
            await self.state_manager.set("last_emergency", {
                "reason": reason,
                "at": datetime.now().isoformat(),
                "handlers_run": succeeded,
                "errors": errors,
            })
        except Exception as exc:  # noqa: BLE001
            logger.error("Emergency backup/state save failed: %s", exc)
        return {
            "reason": reason,
            "handlers_run": succeeded,
            "handlers_failed": len(errors),
            "errors": errors,
        }

    # ---------- introspection ----------

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "monitoring": self._monitor_task is not None
            and not self._monitor_task.done(),
            "registered_handlers": len(self._close_handlers),
            "last_backup_at": (
                self._last_backup_at.isoformat()
                if self._last_backup_at else None),
            "last_error": self._last_error,
            "backup_manager": self.backup_manager.get_status(),
        }


# Singleton instance
_dr_manager: Optional[DisasterRecoveryManager] = None


def get_disaster_recovery_manager(**kwargs) -> DisasterRecoveryManager:
    """Get or create the process-wide disaster recovery manager."""
    global _dr_manager
    if _dr_manager is None:
        _dr_manager = DisasterRecoveryManager(**kwargs)
    return _dr_manager


__all__ = [
    "DisasterRecoveryManager",
    "StateManager",
    "SystemState",
    "get_disaster_recovery_manager",
]
