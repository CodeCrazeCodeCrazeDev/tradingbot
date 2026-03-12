"""
Broker integration package for AlphaAlgo 2.0
"""

from .broker_interface import (
    BrokerInterface,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position
)

from .binance_broker import BinanceBroker

# Optional broker integrations
try:
    from .ib_broker import IBBroker
    _ib_available = True
except ImportError:
    IBBroker = None
    _ib_available = False

__all__ = [
    'BrokerOrchestrator',
    'BrokerInterface',
    'Order',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'Position',
    'BinanceBroker',
    'IBBroker'
]

class BrokerManager:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
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



class BrokerOrchestrator:
    """Stub for BrokerOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
