"""
Audit Service
=============

Wraps Audit module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AuditService(BaseService):
    """
    Audit Service - Trade Journal and Audit Trail
    
    Provides:
    - Trade journal
    - Audit events
    - System event logging
    """
    
    SERVICE_NAME = "audit"
    SERVICE_TYPE = "audit"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._trade_journal = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.TRADE_EXECUTED, EventTypes.ORDER_PLACED, EventTypes.SYSTEM_ERROR],
                self._on_audit_event
            )
        logger.info("AuditService started")
    
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
        logger.info("AuditService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._trade_journal else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Audit components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.audit import TradeJournal
            self._trade_journal = TradeJournal()
            logger.info("TradeJournal loaded")
        except ImportError as e:
            logger.warning(f"TradeJournal not available: {e}")
    
    async def _on_audit_event(self, event: Event) -> None:
        """Log audit events"""
        pass
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
