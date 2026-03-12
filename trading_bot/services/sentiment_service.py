"""
Sentiment Service - Sentiment Analysis
=======================================

Wraps Sentiment analysis capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class SentimentService(BaseService):
    """
    Sentiment Service - Sentiment Analysis
    
    Provides:
    - News sentiment analysis
    - Social media sentiment
    - Market sentiment indicators
    """
    
    SERVICE_NAME = "sentiment"
    SERVICE_TYPE = "intelligence"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._sentiment_analyzer = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("SentimentService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SentimentService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._sentiment_analyzer else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Sentiment components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.sentiment import SentimentAnalyzer
            self._sentiment_analyzer = SentimentAnalyzer()
            logger.info("SentimentAnalyzer loaded")
        except ImportError as e:
            logger.warning(f"SentimentAnalyzer not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
