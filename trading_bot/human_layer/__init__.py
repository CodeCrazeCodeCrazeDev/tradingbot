"""
Human Layer Module
============================================================

Auto-generated integration file.
"""

# alerts
try:
    from .alerts import (
        AlertManager,
    )
except ImportError as e:
    # alerts not available
    pass

__all__ = [
    'AlertManager',
]


class HumanLayerOrchestrator:
    """Auto-generated stub orchestrator for human_layer."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "HumanLayerOrchestrator is a merge-generated stub and is deprecated. "
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


# Public API re-exports
try:
    from .alerts import AlertPriority, get_alert_manager
    from .approval import get_approval_gate
    from .override import get_manual_override, is_trading_allowed
    from .dashboard import get_dashboard
except ImportError:
    pass
