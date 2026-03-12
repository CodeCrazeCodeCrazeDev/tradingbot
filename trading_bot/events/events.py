"""
Event Definitions - Standard event types for the trading bot.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

# Import base Event from orchestration
from ..orchestration.event_bus import Event, EventPriority

class EventType(Enum):
    """Standard event types."""
    # Market events
    MARKET_DATA = "market_data"
    PRICE_UPDATE = "price_update"
    TRADE = "trade"
    ORDER_BOOK = "order_book"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SERVICE_INITIALIZED = "service_initialized"
    SERVICE_ERROR = "service_error"
    HEALTH_CHECK = "health_check"
    
    # Trading events
    SIGNAL_GENERATED = "signal_generated"
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    
    # Analysis events
    ANALYSIS_COMPLETE = "analysis_complete"
    PREDICTION_READY = "prediction_ready"
    ALERT_TRIGGERED = "alert_triggered"
    REGIME_CHANGE = "regime_change"

class BaseEvent(Event):
    """Base event with common functionality."""
    
    def __init__(self, 
                 event_type: str,
                 data: Dict[str, Any] = None,
                 source: str = "",
                 priority: EventPriority = EventPriority.NORMAL,
                 **kwargs):
        super().__init__(
            type=event_type,
            data=data or {},
            source=source,
            priority=priority,
            **kwargs
        )
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data value with default."""
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set data value."""
        self.data[key] = value
    
    def has_data(self, key: str) -> bool:
        """Check if data key exists."""
        return key in self.data

# Market Events

@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    
    def __post_init__(self):
        if self.spread is None and self.bid and self.ask:
            self.spread = self.ask - self.bid

class MarketEvent(BaseEvent):
    """Base market event."""
    
    def __init__(self, 
                 symbol: str,
                 data: Dict[str, Any] = None,
                 **kwargs):
        data = data or {}
        data['symbol'] = symbol
        super().__init__(EventType.MARKET_DATA.value, data, **kwargs)
    
    @property
    def symbol(self) -> str:
        """Get symbol."""
        return self.get_data('symbol')

class PriceUpdateEvent(MarketEvent):
    """Price update event."""
    
    def __init__(self, 
                 symbol: str,
                 price: float,
                 volume: float = 0,
                 timestamp: datetime = None,
                 bid: float = None,
                 ask: float = None,
                 **kwargs):
        
        data = {
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'timestamp': timestamp or datetime.now(),
            'bid': bid,
            'ask': ask
        }
        
        if bid and ask:
            data['spread'] = ask - bid
        
        super().__init__(symbol, data, **kwargs)
    
    @property
    def price(self) -> float:
        """Get price."""
        return self.get_data('price')
    
    @property
    def volume(self) -> float:
        """Get volume."""
        return self.get_data('volume')
    
    @property
    def timestamp(self) -> datetime:
        """Get timestamp."""
        return self.get_data('timestamp')
    
    @property
    def bid(self) -> Optional[float]:
        """Get bid price."""
        return self.get_data('bid')
    
    @property
    def ask(self) -> Optional[float]:
        """Get ask price."""
        return self.get_data('ask')
    
    @property
    def spread(self) -> Optional[float]:
        """Get spread."""
        return self.get_data('spread')

class TradeEvent(MarketEvent):
    """Trade event."""
    
    def __init__(self, 
                 symbol: str,
                 price: float,
                 size: float,
                 timestamp: datetime = None,
                 trade_id: str = None,
                 side: str = None,  # buy/sell
                 **kwargs):
        
        data = {
            'symbol': symbol,
            'price': price,
            'size': size,
            'timestamp': timestamp or datetime.now(),
            'trade_id': trade_id or str(uuid.uuid4()),
            'side': side
        }
        
        super().__init__(symbol, data, **kwargs)
    
    @property
    def price(self) -> float:
        """Get trade price."""
        return self.get_data('price')
    
    @property
    def size(self) -> float:
        """Get trade size."""
        return self.get_data('size')
    
    @property
    def side(self) -> Optional[str]:
        """Get trade side."""
        return self.get_data('side')
    
    @property
    def trade_id(self) -> str:
        """Get trade ID."""
        return self.get_data('trade_id')

class OrderBookEvent(MarketEvent):
    """Order book event."""
    
    def __init__(self, 
                 symbol: str,
                 bids: List[tuple],
                 asks: List[tuple],
                 timestamp: datetime = None,
                 **kwargs):
        
        data = {
            'symbol': symbol,
            'bids': bids,
            'asks': asks,
            'timestamp': timestamp or datetime.now()
        }
        
        super().__init__(symbol, data, **kwargs)
    
    @property
    def bids(self) -> List[tuple]:
        """Get bid levels."""
        return self.get_data('bids')
    
    @property
    def asks(self) -> List[tuple]:
        """Get ask levels."""
        return self.get_data('asks')
    
    @property
    def best_bid(self) -> Optional[tuple]:
        """Get best bid."""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[tuple]:
        """Get best ask."""
        return self.asks[0] if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        """Get spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask[0] - self.best_bid[0]
        return None

# System Events

class SystemEvent(BaseEvent):
    """Base system event."""
    
    def __init__(self, 
                 event_type: str,
                 message: str = "",
                 data: Dict[str, Any] = None,
                 **kwargs):
        data = data or {}
        data['message'] = message
        super().__init__(event_type, data, priority=EventPriority.HIGH, **kwargs)
    
    @property
    def message(self) -> str:
        """Get message."""
        return self.get_data('message')

class ServiceEvent(SystemEvent):
    """Service-related event."""
    
    def __init__(self, 
                 service_name: str,
                 event_type: str,
                 status: str = "",
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'service_name': service_name,
            'status': status
        })
        
        super().__init__(event_type, data=data, **kwargs)
    
    @property
    def service_name(self) -> str:
        """Get service name."""
        return self.get_data('service_name')
    
    @property
    def status(self) -> str:
        """Get status."""
        return self.get_data('status')

class ErrorEvent(SystemEvent):
    """Error event."""
    
    def __init__(self, 
                 error: str,
                 component: str = "",
                 exception: Exception = None,
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'error': error,
            'component': component,
            'exception_type': type(exception).__name__ if exception else None,
            'exception_message': str(exception) if exception else None
        })
        
        super().__init__(
            EventType.SERVICE_ERROR.value,
            message=error,
            data=data,
            priority=EventPriority.CRITICAL,
            **kwargs
        )
    
    @property
    def error(self) -> str:
        """Get error message."""
        return self.get_data('error')
    
    @property
    def component(self) -> str:
        """Get component name."""
        return self.get_data('component')

class HealthEvent(SystemEvent):
    """Health check event."""
    
    def __init__(self, 
                 component: str,
                 healthy: bool,
                 metrics: Dict[str, Any] = None,
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'component': component,
            'healthy': healthy,
            'metrics': metrics or {}
        })
        
        super().__init__(
            EventType.HEALTH_CHECK.value,
            data=data,
            **kwargs
        )
    
    @property
    def component(self) -> str:
        """Get component name."""
        return self.get_data('component')
    
    @property
    def healthy(self) -> bool:
        """Get health status."""
        return self.get_data('healthy')
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get metrics."""
        return self.get_data('metrics')

# Trading Events

class SignalEvent(BaseEvent):
    """Trading signal event."""
    
    def __init__(self, 
                 symbol: str,
                 direction: str,  # buy/sell
                 confidence: float,
                 price: float = None,
                 strategy: str = "",
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'price': price,
            'strategy': strategy,
            'signal_id': str(uuid.uuid4())
        })
        
        super().__init__(
            EventType.SIGNAL_GENERATED.value,
            data=data,
            priority=EventPriority.HIGH,
            **kwargs
        )
    
    @property
    def symbol(self) -> str:
        """Get symbol."""
        return self.get_data('symbol')
    
    @property
    def direction(self) -> str:
        """Get direction."""
        return self.get_data('direction')
    
    @property
    def confidence(self) -> float:
        """Get confidence."""
        return self.get_data('confidence')
    
    @property
    def price(self) -> Optional[float]:
        """Get price."""
        return self.get_data('price')
    
    @property
    def strategy(self) -> str:
        """Get strategy name."""
        return self.get_data('strategy')
    
    @property
    def signal_id(self) -> str:
        """Get signal ID."""
        return self.get_data('signal_id')

class OrderEvent(BaseEvent):
    """Order event."""
    
    def __init__(self, 
                 order_id: str,
                 symbol: str,
                 side: str,  # buy/sell
                 order_type: str,  # market/limit
                 quantity: float,
                 price: float = None,
                 status: str = "",  # pending/filled/cancelled
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'order_type': order_type,
            'quantity': quantity,
            'price': price,
            'status': status,
            'timestamp': datetime.now()
        })
        
        super().__init__(
            EventType.ORDER_PLACED.value,
            data=data,
            priority=EventPriority.HIGH,
            **kwargs
        )
    
    @property
    def order_id(self) -> str:
        """Get order ID."""
        return self.get_data('order_id')
    
    @property
    def symbol(self) -> str:
        """Get symbol."""
        return self.get_data('symbol')
    
    @property
    def side(self) -> str:
        """Get side."""
        return self.get_data('side')
    
    @property
    def status(self) -> str:
        """Get status."""
        return self.get_data('status')

class PositionEvent(BaseEvent):
    """Position event."""
    
    def __init__(self, 
                 symbol: str,
                 quantity: float,
                 entry_price: float,
                 current_price: float = None,
                 pnl: float = 0,
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'symbol': symbol,
            'quantity': quantity,
            'entry_price': entry_price,
            'current_price': current_price,
            'pnl': pnl,
            'timestamp': datetime.now()
        })
        
        event_type = EventType.POSITION_OPENED.value if quantity != 0 else EventType.POSITION_CLOSED.value
        
        super().__init__(
            event_type,
            data=data,
            priority=EventPriority.HIGH,
            **kwargs
        )
    
    @property
    def symbol(self) -> str:
        """Get symbol."""
        return self.get_data('symbol')
    
    @property
    def quantity(self) -> float:
        """Get quantity."""
        return self.get_data('quantity')
    
    @property
    def pnl(self) -> float:
        """Get P&L."""
        return self.get_data('pnl')

class RiskEvent(BaseEvent):
    """Risk management event."""
    
    def __init__(self, 
                 risk_type: str,
                 level: str,  # low/medium/high/critical
                 message: str = "",
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'risk_type': risk_type,
            'level': level,
            'message': message
        })
        
        priority = {
            'critical': EventPriority.CRITICAL,
            'high': EventPriority.HIGH,
            'medium': EventPriority.NORMAL,
            'low': EventPriority.LOW
        }.get(level, EventPriority.NORMAL)
        
        super().__init__(
            EventType.RISK_LIMIT_BREACH.value,
            data=data,
            priority=priority,
            **kwargs
        )
    
    @property
    def risk_type(self) -> str:
        """Get risk type."""
        return self.get_data('risk_type')
    
    @property
    def level(self) -> str:
        """Get risk level."""
        return self.get_data('level')

# Analysis Events

class AnalysisEvent(BaseEvent):
    """Analysis event."""
    
    def __init__(self, 
                 analysis_type: str,
                 symbol: str,
                 result: Dict[str, Any],
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'analysis_type': analysis_type,
            'symbol': symbol,
            'result': result,
            'timestamp': datetime.now()
        })
        
        super().__init__(
            EventType.ANALYSIS_COMPLETE.value,
            data=data,
            **kwargs
        )
    
    @property
    def analysis_type(self) -> str:
        """Get analysis type."""
        return self.get_data('analysis_type')
    
    @property
    def symbol(self) -> str:
        """Get symbol."""
        return self.get_data('symbol')
    
    @property
    def result(self) -> Dict[str, Any]:
        """Get analysis result."""
        return self.get_data('result')

class PredictionEvent(BaseEvent):
    """Prediction event."""
    
    def __init__(self, 
                 symbol: str,
                 prediction: float,
                 confidence: float,
                 model: str = "",
                 horizon: str = "1h",
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'symbol': symbol,
            'prediction': prediction,
            'confidence': confidence,
            'model': model,
            'horizon': horizon,
            'timestamp': datetime.now()
        })
        
        super().__init__(
            EventType.PREDICTION_READY.value,
            data=data,
            **kwargs
        )
    
    @property
    def symbol(self) -> str:
        """Get symbol."""
        return self.get_data('symbol')
    
    @property
    def prediction(self) -> float:
        """Get prediction value."""
        return self.get_data('prediction')
    
    @property
    def confidence(self) -> float:
        """Get confidence."""
        return self.get_data('confidence')

class AlertEvent(BaseEvent):
    """Alert event."""
    
    def __init__(self, 
                 alert_type: str,
                 message: str,
                 severity: str = "medium",  # low/medium/high/critical
                 data: Dict[str, Any] = None,
                 **kwargs):
        
        data = data or {}
        data.update({
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now()
        })
        
        priority = {
            'critical': EventPriority.CRITICAL,
            'high': EventPriority.HIGH,
            'medium': EventPriority.NORMAL,
            'low': EventPriority.LOW
        }.get(severity, EventPriority.NORMAL)
        
        super().__init__(
            EventType.ALERT_TRIGGERED.value,
            data=data,
            priority=priority,
            **kwargs
        )
    
    @property
    def alert_type(self) -> str:
        """Get alert type."""
        return self.get_data('alert_type')
    
    @property
    def message(self) -> str:
        """Get message."""
        return self.get_data('message')
    
    @property
    def severity(self) -> str:
        """Get severity."""
        return self.get_data('severity')

# Event Handler Base Class

class EventHandler(ABC):
    """Base event handler class."""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.subscribed_events: List[str] = []
        self.enabled = True
    
    @abstractmethod
    async def handle(self, event: BaseEvent) -> None:
        """Handle an event. Must be implemented by subclasses."""
        pass
    
    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle event type."""
        return not self.subscribed_events or event_type in self.subscribed_events
    
    async def __call__(self, event: BaseEvent) -> None:
        """Make handler callable."""
        if self.enabled and self.can_handle(event.type):
            await self.handle(event)
