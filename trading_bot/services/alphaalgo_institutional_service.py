"""
AlphaAlgo Institutional Service
===============================

Wraps AlphaAlgo Institutional module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlphaAlgoInstitutionalService(BaseService):
    """
    AlphaAlgo Institutional Service - Institutional-Grade Trading
    
    Provides 7-layer institutional framework:
    - Layer 1: Market selection
    - Layer 2: Regime detection
    - Layer 3: Quantitative research
    - Layer 4: Portfolio allocation
    - Layer 5: Risk governance
    - Layer 6: Execution
    - Layer 7: Monitoring & evolution
    """
    
    SERVICE_NAME = "alphaalgo_institutional"
    SERVICE_TYPE = "institutional"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["alphaalgo_core"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._var_engine = None
        self._drawdown_controller = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AlphaAlgoInstitutionalService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlphaAlgoInstitutionalService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([
            self._var_engine is not None,
            self._drawdown_controller is not None
        ])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Institutional components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alphaalgo_institutional import VaREngine
            self._var_engine = VaREngine()
            logger.info("VaREngine loaded")
        except ImportError as e:
            logger.warning(f"VaREngine not available: {e}")
        
        try:
            from trading_bot.alphaalgo_institutional import DrawdownController
            self._drawdown_controller = DrawdownController()
            logger.info("DrawdownController loaded")
        except ImportError as e:
            logger.warning(f"DrawdownController not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
