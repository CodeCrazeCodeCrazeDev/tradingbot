"""
Strategies Module
============================================================

Auto-generated integration file.
"""

from .adapter import LegacyStrategyAdapter
from .registry import StrategyRegistry, StrategyRegistration

# cross_exchange_arbitrage
try:
    from .cross_exchange_arbitrage import (
        CrossExchangeArbitrageSystem,
    )
except ImportError as e:
    # cross_exchange_arbitrage not available
    pass

__all__ = [
    'LegacyStrategyAdapter',
    'StrategyRegistry',
    'StrategyRegistration',
    'CrossExchangeArbitrageSystem',
]


class StrategiesOrchestrator:
    """Auto-generated stub orchestrator for strategies."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "StrategiesOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
