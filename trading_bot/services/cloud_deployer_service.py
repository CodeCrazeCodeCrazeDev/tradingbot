"""
Cloud Deployer Service
======================

Wraps Cloud Deployer module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class CloudDeployerService(BaseService):
    """
    Cloud Deployer Service - Auto-Deploy to Cloud
    
    Provides:
    - Cloud auto deployer
    - Server discovery
    - Deployment status monitoring
    """
    
    SERVICE_NAME = "cloud_deployer"
    SERVICE_TYPE = "deployment"
    PRIORITY = ServicePriority.LOW
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 300.0) if config else 300.0
        self._task: Optional[asyncio.Task] = None
        self._deployer = None
        self._discovery = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("CloudDeployerService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CloudDeployerService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._deployer is not None, self._discovery is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Cloud Deployer components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.cloud_deployer import CloudAutoDeployer
            self._deployer = CloudAutoDeployer()
            logger.info("CloudAutoDeployer loaded")
        except ImportError as e:
            logger.warning(f"CloudAutoDeployer not available: {e}")
        
        try:
            from trading_bot.cloud_deployer import ServerDiscovery
            self._discovery = ServerDiscovery()
            logger.info("ServerDiscovery loaded")
        except ImportError as e:
            logger.warning(f"ServerDiscovery not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
