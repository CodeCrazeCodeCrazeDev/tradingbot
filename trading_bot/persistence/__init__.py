"""
Persistence Module
============================================================

Auto-generated integration file.
"""

from .repositories import SqliteTradingRepository

# checkpoint_manager
try:
    from .checkpoint_manager import (
        CheckpointManager,
        SystemCheckpoint,
    )
except ImportError as e:
    # checkpoint_manager not available
    pass

__all__ = [
    'SqliteTradingRepository',
    'CheckpointManager',
    'SystemCheckpoint',
]


class PersistenceOrchestrator:
    """Auto-generated stub orchestrator for persistence."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "PersistenceOrchestrator is a merge-generated stub and is deprecated. "
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
