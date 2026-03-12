"""
Backtesting Service
===================

Wraps Backtesting module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class BacktestingService(BaseService):
    """
    Backtesting Service - Strategy Backtesting
    
    Provides:
    - Advanced backtester
    - Rigorous backtester
    - Strategy backtester
    - Walk-forward analysis
    - Monte Carlo simulation
    """
    
    SERVICE_NAME = "backtesting"
    SERVICE_TYPE = "testing"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 300.0) if config else 300.0
        self._task: Optional[asyncio.Task] = None
        self._backtester = None
        self._rigorous = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("BacktestingService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BacktestingService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._backtester is not None, self._rigorous is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Backtesting components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.backtesting import AdvancedBacktester
            self._backtester = AdvancedBacktester
            logger.info("AdvancedBacktester loaded")
        except ImportError as e:
            logger.warning(f"AdvancedBacktester not available: {e}")
        
        try:
            from trading_bot.backtesting import RigorousBacktester
            self._rigorous = RigorousBacktester
            logger.info("RigorousBacktester loaded")
        except ImportError as e:
            logger.warning(f"RigorousBacktester not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
