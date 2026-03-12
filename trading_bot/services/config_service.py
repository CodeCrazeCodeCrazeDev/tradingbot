"""
Config Service
==============

Wraps Config module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class ConfigService(BaseService):
    """
    Config Service - Configuration Management
    
    Provides:
    - Config manager
    - Feature flags
    - Dynamic config
    """
    
    SERVICE_NAME = "config"
    SERVICE_TYPE = "config"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._config_manager = None
        self._feature_flags = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ConfigService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ConfigService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._config_manager is not None, self._feature_flags is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Config components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.config import ConfigManager
            self._config_manager = ConfigManager()
            logger.info("ConfigManager loaded")
        except ImportError as e:
            logger.warning(f"ConfigManager not available: {e}")
        
        try:
            from trading_bot.config import FeatureFlagManager
            self._feature_flags = FeatureFlagManager()
            logger.info("FeatureFlagManager loaded")
        except ImportError as e:
            logger.warning(f"FeatureFlagManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
