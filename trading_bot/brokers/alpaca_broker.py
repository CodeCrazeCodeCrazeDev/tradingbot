
"""
Alpaca Broker - Alpaca broker adapter
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AlpacaBroker:
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("AlpacaBroker initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise


_broker: Optional[AlpacaBroker] = None
def get_broker() -> AlpacaBroker:
    try:
        global _broker
        if _broker is None:
            _broker = AlpacaBroker()
        return _broker
    except Exception as e:
        logger.error(f"Error in get_broker: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_broker().initialize(config)
async def start() -> bool:
    return await get_broker().start()
async def stop() -> bool:
    return await get_broker().stop()
