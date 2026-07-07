"""
AAMIS V3 Service - REDIRECTED
ARCH-01: Consolidated into IntegratedAgentSystem.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority
from trading_bot.core_agent_system.legacy_adapter import LegacyOrchestratorAdapter
from trading_bot.core_agent_system import IntegratedAgentSystem

logger = logging.getLogger(__name__)

class AAMISService(BaseService):
    SERVICE_NAME = "aamis_v3"
    SERVICE_TYPE = "ai"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._orchestrator = None
        
    async def start(self) -> None:
        self._running = True
        try:
            ias = IntegratedAgentSystem(self.config)
            self._orchestrator = LegacyOrchestratorAdapter(ias, self.config)
            logger.info("AAMISService (IAS Adapter) started")
        except Exception as e:
            logger.error(f"Failed to initialize IAS for AAMIS: {e}")
    
    async def stop(self) -> None:
        self._running = False
        logger.info("AAMISService stopped")
    
    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            healthy=self._running and self._orchestrator is not None,
            last_check=datetime.utcnow(),
            message="IAS-Adapter Active"
        )

    async def analyze_symbol(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._orchestrator:
            return {'error': 'IAS not loaded'}
        return await self._orchestrator.generate_signal(symbol, data)
