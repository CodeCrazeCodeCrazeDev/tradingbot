"""
Brokers Module
============================================================

Auto-generated integration file.
"""

from .adapter_bridge import FoundationBrokerAdapter

# broker_adapter / mt5_adapter — canonical enum + MT5 bridge.
# NOTE: ``trading_bot.brokers.mt5_adapter`` resolves to the mt5_adapter/
# PACKAGE (MT5.py SDK wrapper), which shadows the mt5_adapter.py module that
# also defined an MT5BrokerAdapter. The canonical adapter lives in
# broker_adapter.py and lazy-imports MetaTrader5 inside connect().
try:
    from .broker_adapter import OrderSide, MT5BrokerAdapter
except ImportError:
    try:
        from .broker_adapter import OrderSide
    except ImportError:
        pass

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
    'FoundationBrokerAdapter',
    'BrokerConnectionManager',
    'MultiBrokerConnectionManager',
    'UnifiedBrokerManager',
    'OrderSide',
    'MT5BrokerAdapter',
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
    from .broker_adapter import (  # noqa: F401
        BrokerAdapter,
        MockBrokerAdapter,
        AlpacaBrokerAdapter,
        BinanceBrokerAdapter,
        OrderStatus,
        OrderType,
        Position,
        OrderResponse,
        get_broker_adapter,
    )
except ImportError:
    pass
