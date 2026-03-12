"""
Fail Safe - System fail-safe mechanisms
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    NORMAL = "normal"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class FailSafe:
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.level = SafetyLevel.NORMAL
            self.trading_enabled = True
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("FailSafe initialized")
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
    
    def set_level(self, level: SafetyLevel):
        try:
            self.level = level
            if level in [SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY]:
                self.trading_enabled = False
        except Exception as e:
            logger.error(f"Error in set_level: {e}")
            raise
    
    def can_trade(self) -> bool:
        return self.trading_enabled and self.level in [SafetyLevel.NORMAL, SafetyLevel.CAUTION]


_failsafe: Optional[FailSafe] = None
def get_failsafe() -> FailSafe:
    try:
        global _failsafe
        if _failsafe is None:
            _failsafe = FailSafe()
        return _failsafe
    except Exception as e:
        logger.error(f"Error in get_failsafe: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_failsafe().initialize(config)
async def start() -> bool:
    return await get_failsafe().start()
async def stop() -> bool:
    return await get_failsafe().stop()
