"""
Drawdown Manager - Manages drawdown protection
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DrawdownState:
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    peak_equity: float = 0.0
    is_in_drawdown: bool = False


class DrawdownManager:
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.max_allowed_drawdown = 0.20  # 20%
            self.state = DrawdownState()
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config and 'max_drawdown' in config:
                self.max_allowed_drawdown = config['max_drawdown']
            logger.info("DrawdownManager initialized")
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
    
    def update(self, current_equity: float) -> DrawdownState:
        try:
            if current_equity > self.state.peak_equity:
                self.state.peak_equity = current_equity
            if self.state.peak_equity > 0:
                self.state.current_drawdown = (self.state.peak_equity - current_equity) / self.state.peak_equity
                self.state.max_drawdown = max(self.state.max_drawdown, self.state.current_drawdown)
                self.state.is_in_drawdown = self.state.current_drawdown > 0
            return self.state
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def should_stop_trading(self) -> bool:
        return self.state.current_drawdown >= self.max_allowed_drawdown


_manager: Optional[DrawdownManager] = None
def get_manager() -> DrawdownManager:
    try:
        global _manager
        if _manager is None:
            _manager = DrawdownManager()
        return _manager
    except Exception as e:
        logger.error(f"Error in get_manager: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_manager().initialize(config)
async def start() -> bool:
    return await get_manager().start()
async def stop() -> bool:
    return await get_manager().stop()
