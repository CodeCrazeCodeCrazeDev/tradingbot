"""
Risk Budget Allocator - Allocates risk budget across strategies
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RiskBudgetAllocator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.total_budget = 1.0
        self.allocations: Dict[str, float] = {}
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        logger.info("RiskBudgetAllocator initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        return True
    
    async def stop(self) -> bool:
        self._running = False
        return True
    
    def allocate(self, strategy_id: str, budget: float):
        self.allocations[strategy_id] = budget
    
    def get_allocation(self, strategy_id: str) -> float:
        return self.allocations.get(strategy_id, 0.0)


_allocator: Optional[RiskBudgetAllocator] = None
def get_allocator() -> RiskBudgetAllocator:
    global _allocator
    if _allocator is None:
        _allocator = RiskBudgetAllocator()
    return _allocator

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_allocator().initialize(config)
async def start() -> bool:
    return await get_allocator().start()
async def stop() -> bool:
    return await get_allocator().stop()
