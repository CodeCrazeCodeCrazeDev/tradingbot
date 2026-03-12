"""
AlphaAlgo Core Events - STABLE EVENT SYSTEM

This module defines the event system for inter-component communication.
These events are FROZEN and should NEVER change.

Version: 1.0.0 (FROZEN)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
import asyncio
import logging
from collections import defaultdict
import uuid

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


# =============================================================================
# EVENT TYPES - FROZEN
# =============================================================================

class EventType(Enum):
    """Event type enumeration - FROZEN"""
    # Market Data Events
    TICK_UPDATE = "tick_update"
    OHLCV_UPDATE = "ohlcv_update"
    ORDERBOOK_UPDATE = "orderbook_update"
    TRADE_UPDATE = "trade_update"
    
    # Signal Events
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_VALIDATED = "signal_validated"
    SIGNAL_REJECTED = "signal_rejected"
    SIGNAL_EXPIRED = "signal_expired"
    
    # Order Events
    ORDER_CREATED = "order_created"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIAL = "order_partial"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    
    # Trade Events
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    TRADE_MODIFIED = "trade_modified"
    
    # Risk Events
    RISK_LIMIT_BREACH = "risk_limit_breach"
    DRAWDOWN_WARNING = "drawdown_warning"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    POSITION_LIMIT_REACHED = "position_limit_reached"
    
    # System Events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    
    # Evolution Events
    EVOLUTION_STARTED = "evolution_started"
    EVOLUTION_COMPLETED = "evolution_completed"
    IMPROVEMENT_PROPOSED = "improvement_proposed"
    IMPROVEMENT_APPROVED = "improvement_approved"
    IMPROVEMENT_REJECTED = "improvement_rejected"
    
    # Human Events
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    MANUAL_OVERRIDE = "manual_override"


# =============================================================================
# BASE EVENT - FROZEN
# =============================================================================

@dataclass
class Event:
    """Base event class - FROZEN STRUCTURE"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            event_id=data.get('event_id', ''),
            event_type=EventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            data=data.get('data', {}),
            metadata=data.get('metadata', {}),
        )


# =============================================================================
# SPECIFIC EVENTS - FROZEN
# =============================================================================

@dataclass
class MarketDataEvent(Event):
    """Market data event - FROZEN"""
    symbol: str = ""
    timeframe: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.event_type not in [
            EventType.TICK_UPDATE, 
            EventType.OHLCV_UPDATE,
            EventType.ORDERBOOK_UPDATE,
            EventType.TRADE_UPDATE
        ]:
            raise ValueError(f"Invalid event type for MarketDataEvent: {self.event_type}")


@dataclass
class SignalEvent(Event):
    """Signal event - FROZEN"""
    signal_id: str = ""
    symbol: str = ""
    signal_type: str = ""
    confidence: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        if self.event_type not in [
            EventType.SIGNAL_GENERATED,
            EventType.SIGNAL_VALIDATED,
            EventType.SIGNAL_REJECTED,
            EventType.SIGNAL_EXPIRED
        ]:
            raise ValueError(f"Invalid event type for SignalEvent: {self.event_type}")


@dataclass
class OrderEvent(Event):
    """Order event - FROZEN"""
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    quantity: float = 0.0
    price: float = 0.0
    status: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.event_type not in [
            EventType.ORDER_CREATED,
            EventType.ORDER_SUBMITTED,
            EventType.ORDER_FILLED,
            EventType.ORDER_PARTIAL,
            EventType.ORDER_CANCELLED,
            EventType.ORDER_REJECTED
        ]:
            raise ValueError(f"Invalid event type for OrderEvent: {self.event_type}")


@dataclass
class TradeEvent(Event):
    """Trade event - FROZEN"""
    trade_id: str = ""
    symbol: str = ""
    side: str = ""
    pnl: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        if self.event_type not in [
            EventType.TRADE_OPENED,
            EventType.TRADE_CLOSED,
            EventType.TRADE_MODIFIED
        ]:
            raise ValueError(f"Invalid event type for TradeEvent: {self.event_type}")


@dataclass
class RiskEvent(Event):
    """Risk event - FROZEN"""
    risk_level: str = ""
    current_value: float = 0.0
    limit_value: float = 0.0
    breach_type: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.event_type not in [
            EventType.RISK_LIMIT_BREACH,
            EventType.DRAWDOWN_WARNING,
            EventType.CIRCUIT_BREAKER_TRIGGERED,
            EventType.POSITION_LIMIT_REACHED
        ]:
            raise ValueError(f"Invalid event type for RiskEvent: {self.event_type}")


@dataclass
class SystemEvent(Event):
    """System event - FROZEN"""
    component: str = ""
    status: str = ""
    message: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.event_type not in [
            EventType.SYSTEM_STARTED,
            EventType.SYSTEM_STOPPED,
            EventType.SYSTEM_ERROR,
            EventType.SYSTEM_WARNING,
            EventType.CONNECTION_LOST,
            EventType.CONNECTION_RESTORED
        ]:
            raise ValueError(f"Invalid event type for SystemEvent: {self.event_type}")


# =============================================================================
# EVENT HANDLER - FROZEN
# =============================================================================

class EventHandler:
    """Event handler wrapper - FROZEN INTERFACE"""
    
    def __init__(
        self, 
        callback: Callable[[Event], Any],
        event_types: Optional[List[EventType]] = None,
        priority: int = 0,
        async_handler: bool = False
    ):
        self.callback = callback
        self.event_types = event_types or []
        self.priority = priority
        self.async_handler = async_handler
        self.handler_id = str(uuid.uuid4())
    
    async def handle(self, event: Event) -> Any:
        """Handle event"""
        if self.event_types and event.event_type not in self.event_types:
            return None
        try:
        
            if self.async_handler:
                return await self.callback(event)
            else:
                return self.callback(event)
        except Exception as e:
            logger.error(f"Error in event handler {self.handler_id}: {e}")
            raise


# =============================================================================
# EVENT BUS - FROZEN INTERFACE
# =============================================================================

class EventBus:
    """
    Central event bus for pub/sub communication - FROZEN INTERFACE
    
    This is a singleton that manages all event subscriptions and publishing.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._max_history: int = 10000
        self._lock = asyncio.Lock()
        self._initialized = True
        
        logger.info("EventBus initialized")
    
    def subscribe(
        self, 
        event_types: List[EventType],
        callback: Callable[[Event], Any],
        priority: int = 0,
        async_handler: bool = False
    ) -> str:
        """
        Subscribe to specific event types
        
        Returns handler_id for unsubscription
        """
        handler = EventHandler(
            callback=callback,
            event_types=event_types,
            priority=priority,
            async_handler=async_handler
        )
        
        for event_type in event_types:
            self._handlers[event_type].append(handler)
            # Sort by priority (higher priority first)
            self._handlers[event_type].sort(key=lambda h: -h.priority)
        
        logger.debug(f"Subscribed handler {handler.handler_id} to {event_types}")
        return handler.handler_id
    
    def subscribe_all(
        self,
        callback: Callable[[Event], Any],
        priority: int = 0,
        async_handler: bool = False
    ) -> str:
        """Subscribe to all events"""
        handler = EventHandler(
            callback=callback,
            event_types=[],
            priority=priority,
            async_handler=async_handler
        )
        
        self._global_handlers.append(handler)
        self._global_handlers.sort(key=lambda h: -h.priority)
        
        logger.debug(f"Subscribed global handler {handler.handler_id}")
        return handler.handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe handler by ID"""
        # Remove from specific handlers
        for event_type in list(self._handlers.keys()):
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] 
                if h.handler_id != handler_id
            ]
        
        # Remove from global handlers
        self._global_handlers = [
            h for h in self._global_handlers 
            if h.handler_id != handler_id
        ]
        
        logger.debug(f"Unsubscribed handler {handler_id}")
        return True
    
    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers"""
        async with self._lock:
            # Store in history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        # Get handlers for this event type
        handlers = self._handlers.get(event.event_type, []) + self._global_handlers
        
        # Execute handlers
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Error publishing event {event.event_id}: {e}")
    
    def publish_sync(self, event: Event) -> None:
        """Synchronous publish (creates new event loop if needed)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.publish(event))
            else:
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            asyncio.run(self.publish(event))
    
    def get_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history"""
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
    
    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of subscribers"""
        if event_type:
            return len(self._handlers.get(event_type, []))
        return sum(len(handlers) for handlers in self._handlers.values()) + len(self._global_handlers)


# =============================================================================
# HELPER FUNCTIONS - FROZEN
# =============================================================================

def create_event(
    event_type: EventType,
    source: str,
    data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Event:
    """Create a new event"""
    return Event(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        source=source,
        data=data or {},
        metadata=metadata or {}
    )


def create_market_data_event(
    event_type: EventType,
    source: str,
    symbol: str,
    timeframe: str = "",
    data: Optional[Dict[str, Any]] = None
) -> MarketDataEvent:
    """Create a market data event"""
    return MarketDataEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        data=data or {}
    )


def create_signal_event(
    event_type: EventType,
    source: str,
    signal_id: str,
    symbol: str,
    signal_type: str,
    confidence: float,
    data: Optional[Dict[str, Any]] = None
) -> SignalEvent:
    """Create a signal event"""
    return SignalEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        source=source,
        signal_id=signal_id,
        symbol=symbol,
        signal_type=signal_type,
        confidence=confidence,
        data=data or {}
    )


def create_risk_event(
    event_type: EventType,
    source: str,
    risk_level: str,
    current_value: float,
    limit_value: float,
    breach_type: str = "",
    data: Optional[Dict[str, Any]] = None
) -> RiskEvent:
    """Create a risk event"""
    return RiskEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        source=source,
        risk_level=risk_level,
        current_value=current_value,
        limit_value=limit_value,
        breach_type=breach_type,
        data=data or {}
    )


def create_system_event(
    event_type: EventType,
    source: str,
    component: str,
    status: str,
    message: str = "",
    data: Optional[Dict[str, Any]] = None
) -> SystemEvent:
    """Create a system event"""
    return SystemEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        source=source,
        component=component,
        status=status,
        message=message,
        data=data or {}
    )
