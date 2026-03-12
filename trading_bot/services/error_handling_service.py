"""Error Handling Service - System error management"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)

class ErrorHandlingService(BaseService):
    SERVICE_NAME = "error_handling"
    SERVICE_TYPE = "infrastructure"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._task: Optional[asyncio.Task] = None
        self._error_manager = None
        
    async def start(self) -> None:
        self._running = True
        try:
            from trading_bot.error_handling import ErrorManager
            self._error_manager = ErrorManager()
        except ImportError:
            pass
        logger.info("ErrorHandlingService started")
    
    async def stop(self) -> None:
        self._running = False
        logger.info("ErrorHandlingService stopped")
    
    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(healthy=self._running, last_check=datetime.utcnow(), message="Running")
