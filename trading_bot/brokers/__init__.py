"""
Brokers Module
============================================================

Auto-generated integration file.
"""

# connection_manager
try:
    from .connection_manager import (
        BrokerConnectionManager,
        MultiBrokerConnectionManager,
    )
except ImportError as e:
    # connection_manager not available
    pass

# real_broker_integration
try:
    from .real_broker_integration import (
        UnifiedBrokerManager,
    )
except ImportError as e:
    # real_broker_integration not available
    pass

__all__ = [
    'BrokerConnectionManager',
    'MultiBrokerConnectionManager',
    'UnifiedBrokerManager',
]

class BrokersOrchestrator:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "BrokersOrchestrator is a merge-generated stub and is deprecated. "
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


# Compat re-exports
try:
    from .broker_adapter import BrokerAdapter, MockBrokerAdapter  # noqa: F401
except ImportError:
    pass
