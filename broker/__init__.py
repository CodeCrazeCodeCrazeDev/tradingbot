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
    'BrokerInterface',
    'Order',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'Position',
    'BinanceBroker',
    'IBBroker'
]
