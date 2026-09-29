"""
Compliance Service
==================

Wraps Compliance module capabilities as an event-driven service.
"""

import warnings
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class ComplianceService(BaseService):
    """
    Compliance Service - Regulatory Compliance Monitoring
    
    Provides:
    - Compliance monitor
    - Trade surveillance
    """
    
    SERVICE_NAME = "compliance"
    SERVICE_TYPE = "compliance"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["database"]
    
    def __init__(self, config: Optional[Dict] = None):
        warnings.warn("ComplianceService is a legacy/quarantined component: loop/capital surface outside the canonical runtime. It carries no production authority.", DeprecationWarning, stacklevel=2)
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._monitor = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        # Worker disabled: governance/compliance loops run inside the
        # canonical runtime only.
        self._task = None
        logger.warning(
            "ComplianceService run-loop worker disabled; canonical runtime "
            "owns compliance scheduling"
        )
        logger.info("ComplianceService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ComplianceService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._monitor else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Compliance components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.compliance import ComplianceMonitor
            self._monitor = ComplianceMonitor()
            logger.info("ComplianceMonitor loaded")
        except ImportError as e:
            logger.warning(f"ComplianceMonitor not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
