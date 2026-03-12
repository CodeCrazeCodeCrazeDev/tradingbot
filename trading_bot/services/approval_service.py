"""
Approval Service
================

Wraps Approval module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class ApprovalService(BaseService):
    """
    Approval Service - Human-in-the-Loop Approval
    
    Provides:
    - Human approval system
    - Trade approval workflow
    """
    
    SERVICE_NAME = "approval"
    SERVICE_TYPE = "governance"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 10.0) if config else 10.0
        self._task: Optional[asyncio.Task] = None
        self._approval_system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.TRADE_REQUESTED],
                self._on_trade_request
            )
        logger.info("ApprovalService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        logger.info("ApprovalService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._approval_system else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Approval components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.approval import HumanApprovalSystem
            self._approval_system = HumanApprovalSystem()
            logger.info("HumanApprovalSystem loaded")
        except ImportError as e:
            logger.warning(f"HumanApprovalSystem not available: {e}")
    
    async def _on_trade_request(self, event: Event) -> None:
        """Handle trade approval requests"""
        pass
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
