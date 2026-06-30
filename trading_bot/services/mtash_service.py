"""
MTASH Service - MetaTrader Alpha Superintelligence Hub
======================================================
Wraps the MTASH Hub as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority
from trading_bot.ai.hub import MTASH

logger = logging.getLogger(__name__)

class MTASHService(BaseService):
    """
    MTASH Service
    The 'Master Brain' of the AlphaAlgo system, integrating Tactical AI,
    Strategic Superintelligence, and Agent Coordination.
    """

    SERVICE_NAME = "mtash"
    SERVICE_TYPE = "intelligence"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["data", "risk", "msos"]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.hub: Optional[MTASH] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start MTASH Hub"""
        self._running = True
        self.hub = MTASH(self.config)
        await self.hub.initialize()
        await self.hub.start()

        # Subscribe to market events for real-time thinking
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE],
                self._on_market_data
            )

        logger.info("MTASHService started and Hub initialized")

    async def stop(self) -> None:
        """Stop MTASH Hub"""
        self._running = False
        if self.hub:
            await self.hub.shutdown()

        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)

        logger.info("MTASHService stopped")

    async def health_check(self) -> ServiceHealth:
        """Check hub health"""
        is_healthy = self._running and self.hub and self.hub.initialized
        return ServiceHealth(
            healthy=is_healthy,
            last_check=datetime.utcnow(),
            message="MTASH Hub is active" if is_healthy else "MTASH Hub is offline",
            metrics={'initialized': self.hub.initialized if self.hub else False}
        )

    async def _on_market_data(self, event: Event) -> None:
        """Process incoming market data via the Hub's thinking loop"""
        if not self.hub or not self._running:
            return

        market_data = event.payload.get('data', {})
        symbol = event.payload.get('symbol', 'EURUSD')

        logger.info(f"MTASHService: Received market data for {symbol}, triggering Hub thinking...")

        # Run Hub Thinking
        try:
            decision = await self.hub.think(symbol, market_data)

            # Publish Decision/Signal to Event Bus
            if self._event_bus and decision.get('signal'):
                logger.info(f"MTASHService: Hub produced signal for {symbol}, publishing prediction...")
                await self._event_bus.publish(Event(
                    event_type=EventTypes.AI_PREDICTION_READY,
                    payload={
                        'source': 'mtash',
                        'symbol': symbol,
                        'decision': decision
                    },
                    source=self.SERVICE_NAME
                ))
            else:
                logger.warning(f"MTASHService: Hub produced no signal for {symbol}")
        except Exception as e:
            logger.error(f"MTASHService: Error during Hub thinking for {symbol}: {e}", exc_info=True)
