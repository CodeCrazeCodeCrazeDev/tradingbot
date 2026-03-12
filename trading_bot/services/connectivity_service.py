"""
Connectivity Service
====================

Wraps Connectivity module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class ConnectivityService(BaseService):
    """
    Connectivity Service - Network and Connection Management
    
    Provides:
    - WebSocket manager
    - Auth manager
    - Cache manager
    - Proxy manager
    - Rate limit manager
    """
    
    SERVICE_NAME = "connectivity"
    SERVICE_TYPE = "connectivity"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["database"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._websocket_manager = None
        self._auth_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ConnectivityService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ConnectivityService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._websocket_manager is not None, self._auth_manager is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Connectivity components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.connectivity import WebSocketManager
            self._websocket_manager = WebSocketManager()
            logger.info("WebSocketManager loaded")
        except ImportError as e:
            logger.warning(f"WebSocketManager not available: {e}")
        
        try:
            from trading_bot.connectivity import AuthManager
            self._auth_manager = AuthManager()
            logger.info("AuthManager loaded")
        except ImportError as e:
            logger.warning(f"AuthManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
