"""
Analysis Service
================

Wraps Analysis module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AnalysisService(BaseService):
    """
    Analysis Service - Market Analysis and Intelligence
    
    Provides:
    - Market intelligence system
    - HFT defense
    - Candlestick pattern system
    - Multi-timeframe analysis
    - Liquidity analysis
    """
    
    SERVICE_NAME = "analysis"
    SERVICE_TYPE = "analysis"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._market_intel = None
        self._hft_defense = None
        self._mtf_system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE, EventTypes.MARKET_CANDLE],
                self._on_market_data
            )
        logger.info("AnalysisService started")
    
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
        logger.info("AnalysisService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([
            self._market_intel is not None,
            self._hft_defense is not None,
            self._mtf_system is not None
        ])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/3 Analysis components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.analysis import MarketIntelligenceSystem
            self._market_intel = MarketIntelligenceSystem()
            logger.info("MarketIntelligenceSystem loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"MarketIntelligenceSystem not available: {e}")
        
        try:
            from trading_bot.analysis import HFTDefenseSystem
            self._hft_defense = HFTDefenseSystem()
            logger.info("HFTDefenseSystem loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"HFTDefenseSystem not available: {e}")
        
        try:
            from trading_bot.analysis import MultiTimeframeSystem
            self._mtf_system = MultiTimeframeSystem()
            logger.info("MultiTimeframeSystem loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"MultiTimeframeSystem not available: {e}")
    
    async def _on_market_data(self, event: Event) -> None:
        pass
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
