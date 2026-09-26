"""
MTASH Service - MetaTrader Alpha Superintelligence Hub
=====================================================

Wraps MTASH (trading_bot.ai.hub.MTASH) as a managed service.
Unifies tactical real-time tuning, strategic autonomous research,
and the integrated agent system behind one orchestration layer.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class MTASHService(BaseService):
    """
    MTASH Service - MetaTrader Alpha Superintelligence Hub.

    CRITICAL orchestration service: coordinates autonomous tuning,
    optimization, systems AI, superintelligence, and the integrated
    agent system.
    """

    SERVICE_NAME = "mtash"
    SERVICE_TYPE = "orchestration"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["data", "risk", "msos"]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._hub = None

    async def start(self) -> None:
        """Start MTASH service"""
        self._running = True
        await self._load_components()
        logger.info("MTASHService started")

    async def stop(self) -> None:
        """Stop MTASH service"""
        self._running = False
        if self._hub is not None:
            try:
                await self._hub.shutdown()
            except Exception as e:
                logger.warning(f"MTASH shutdown error: {e}")
        logger.info("MTASHService stopped")

    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        loaded = self._hub is not None and getattr(self._hub, "initialized", True)
        return ServiceHealth(
            healthy=self._running and loaded,
            last_check=datetime.utcnow(),
            message="MTASH hub active" if loaded else "MTASH hub not initialized",
            metrics={
                "hub_loaded": self._hub is not None,
                "running": getattr(self._hub, "running", False) if self._hub else False,
            },
        )

    async def _load_components(self) -> None:
        """Instantiate and initialize the MTASH hub."""
        from trading_bot.ai.hub import create_hub

        self._hub = create_hub(self.config or {})
        await self._hub.initialize()
        if getattr(self._hub, "initialized", False) and not getattr(self._hub, "running", False):
            await self._hub.start()

    async def think(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a think cycle to the hub."""
        if self._hub is None:
            raise RuntimeError("MTASHService not started")
        return await self._hub.think(symbol, market_data)
