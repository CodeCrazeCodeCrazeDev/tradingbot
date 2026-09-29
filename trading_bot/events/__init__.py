"""
Event System - Event definitions and handlers for the trading bot.
"""

from .events import (
    # Market events
    MarketEvent,
    PriceUpdateEvent,
    TradeEvent,
    OrderBookEvent,
    
    # System events
    SystemEvent,
    ServiceEvent,
    ErrorEvent,
    HealthEvent,
    
    # Trading events
    SignalEvent,
    OrderEvent,
    PositionEvent,
    RiskEvent,
    
    # Analysis events
    AnalysisEvent,
    PredictionEvent,
    AlertEvent,
    
    # Base classes
    BaseEvent,
    EventHandler
)

__all__ = [
    # Market events
    'MarketEvent',
    'PriceUpdateEvent',
    'TradeEvent',
    'OrderBookEvent',
    
    # System events
    'SystemEvent',
    'ServiceEvent',
    'ErrorEvent',
    'HealthEvent',
    
    # Trading events
    'SignalEvent',
    'OrderEvent',
    'PositionEvent',
    'RiskEvent',
    
    # Analysis events
    'AnalysisEvent',
    'PredictionEvent',
    'AlertEvent',
    
    # Base classes
    'BaseEvent',
    'EventHandler'
]

# Compat re-export: legacy callers expect `Event` at this path
try:
    from trading_bot.orchestration.event_bus import Event, EventPriority, EventHandler  # noqa: F401
except ImportError:
    pass
