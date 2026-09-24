"""
Core Api Module
============================================================

Auto-generated integration file.
"""

# events
try:
    from .events import (
        SystemEvent,
    )
except ImportError as e:
    # events not available
    pass

# exceptions
try:
    from .exceptions import (
        SystemError,
    )
except ImportError as e:
    # exceptions not available
    pass

# interfaces
try:
    from .interfaces import (
        IEvolutionEngine,
        IRiskManager,
    )
except ImportError as e:
    # interfaces not available
    pass

# types
try:
    from .types import (
        SystemStatus,
        TradingMode,
        HealthStatus,
    )
except ImportError as e:
    # types not available
    pass

__all__ = [
    'IEvolutionEngine',
    'IRiskManager',
    'SystemError',
    'SystemEvent',
    'SystemStatus',
]

class CoreAPIOrchestrator:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "CoreAPIOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
    
    def get_status(self):
        """Get orchestrator status."""
        return {"running": self.running, "initialized": self._initialized}



# EventBus/EventType live in core_api.events — re-export for legacy callers.
try:
    from .events import EventBus, EventType, create_system_event
except ImportError:
    EventBus = EventType = create_system_event = None
