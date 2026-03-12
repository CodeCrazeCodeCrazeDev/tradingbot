"""
Risk Budget Allocator - Allocates risk budget across strategies
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RiskBudgetAllocator:
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.total_budget = 1.0
            self.allocations: Dict[str, float] = {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("RiskBudgetAllocator initialized")
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
    
    def allocate(self, strategy_id: str, budget: float):
        try:
            self.allocations[strategy_id] = budget
        except Exception as e:
            logger.error(f"Error in allocate: {e}")
            raise
    
    def get_allocation(self, strategy_id: str) -> float:
        return self.allocations.get(strategy_id, 0.0)


_allocator: Optional[RiskBudgetAllocator] = None
def get_allocator() -> RiskBudgetAllocator:
    try:
        global _allocator
        if _allocator is None:
            _allocator = RiskBudgetAllocator()
        return _allocator
    except Exception as e:
        logger.error(f"Error in get_allocator: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_allocator().initialize(config)
async def start() -> bool:
    return await get_allocator().start()
async def stop() -> bool:
    return await get_allocator().stop()
