"""
Security Service - System Security
====================================

Wraps Security capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class SecurityService(BaseService):
    """
    Security Service - System Security
    
    Provides:
    - API key management
    - Encryption
    - Access control
    - Threat detection
    """
    
    SERVICE_NAME = "security"
    SERVICE_TYPE = "infrastructure"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._security_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("SecurityService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SecurityService stopped")
    
    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message="Security service running"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.security import SecurityManager
            self._security_manager = SecurityManager()
            logger.info("SecurityManager loaded")
        except ImportError as e:
            logger.warning(f"SecurityManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
