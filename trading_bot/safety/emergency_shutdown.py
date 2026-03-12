"""
Emergency Shutdown - Emergency shutdown mechanisms
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmergencyShutdown:
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.is_shutdown = False
            self.shutdown_time: Optional[datetime] = None
            self.shutdown_reason: Optional[str] = None
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("EmergencyShutdown initialized")
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
    
    def trigger(self, reason: str):
        try:
            self.is_shutdown = True
            self.shutdown_time = datetime.utcnow()
            self.shutdown_reason = reason
            logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
        except Exception as e:
            logger.error(f"Error in trigger: {e}")
            raise
    
    def reset(self):
        try:
            self.is_shutdown = False
            self.shutdown_time = None
            self.shutdown_reason = None
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def can_trade(self) -> bool:
        return not self.is_shutdown


_shutdown: Optional[EmergencyShutdown] = None
def get_shutdown() -> EmergencyShutdown:
    try:
        global _shutdown
        if _shutdown is None:
            _shutdown = EmergencyShutdown()
        return _shutdown
    except Exception as e:
        logger.error(f"Error in get_shutdown: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_shutdown().initialize(config)
async def start() -> bool:
    return await get_shutdown().start()
async def stop() -> bool:
    return await get_shutdown().stop()
