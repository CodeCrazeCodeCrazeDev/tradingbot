"""
Intelligence Directorate Service
================================

Event-service wrapper for AlphaAlgo's source-provenance and signal
counterintelligence controls.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority
from trading_bot.core.signal_counterintelligence import (
    AlphaAlgoIntelligenceDirectorate,
    CounterintelligenceMode,
)

logger = logging.getLogger(__name__)


class IntelligenceDirectorateService(BaseService):
    """Governance service for legal-source validation and signal CI review."""

    SERVICE_NAME = "intelligence_directorate"
    SERVICE_TYPE = "governance"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["audit", "approval", "compliance"]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._task: Optional[asyncio.Task] = None
        self._directorate: Optional[AlphaAlgoIntelligenceDirectorate] = None
        self._mode = self._coerce_mode(
            self.config.get("counterintelligence_mode", CounterintelligenceMode.HARD_GATE)
        )

    async def start(self) -> None:
        self._running = True
        self._directorate = AlphaAlgoIntelligenceDirectorate(mode=self._mode)
        self._task = asyncio.create_task(self._run_loop())
        logger.info("IntelligenceDirectorateService started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("IntelligenceDirectorateService stopped")

    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            healthy=self._running and self._directorate is not None,
            last_check=datetime.utcnow(),
            message=f"directorate mode={self._mode.value}",
        )

    def evaluate_signal(self, signal: Any, **kwargs):
        if not self._directorate:
            raise RuntimeError("IntelligenceDirectorateService is not running")
        return self._directorate.evaluate_raw_signal(signal, mode=self._mode, **kwargs)

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break

    def _coerce_mode(self, value: Any) -> CounterintelligenceMode:
        if isinstance(value, CounterintelligenceMode):
            return value
        try:
            return CounterintelligenceMode(str(value))
        except ValueError:
            return CounterintelligenceMode.HARD_GATE
