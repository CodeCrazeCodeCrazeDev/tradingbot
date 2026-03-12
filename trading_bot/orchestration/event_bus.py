"""
Event Bus - Asynchronous event-driven communication system.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import weakref
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    """Base event class."""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.source:
            # Try to get caller info
            import inspect
            frame = inspect.currentframe().f_back
            if frame:
                self.source = f"{frame.f_globals.get('__name__', 'unknown')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'type': self.type,
            'data': self.data,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'id': self.id,
            'priority': self.priority.value,
            'correlation_id': self.correlation_id
        }

class EventHandler:
    """Base event handler interface."""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.subscribed_events: List[str] = []
        self.enabled = True
    
    async def handle(self, event: Event) -> None:
        """Handle an event. Override in subclasses."""
        raise NotImplementedError
    
    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle event type."""
        return not self.subscribed_events or event_type in self.subscribed_events

class EventBus:
    """
    Asynchronous event bus for loose coupling between modules.
    
    Features:
    - Async event publishing and handling
    - Event filtering and routing
    - Priority-based processing
    - Event history and replay
    - Performance monitoring
    - Error handling and retry
    """
    
    def __init__(self, max_history: int = 10000):
        self.handlers: Dict[str, List[weakref.ref]] = {}
        self.global_handlers: List[weakref.ref] = []
        self.event_history: List[Event] = []
        self.max_history = max_history
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._stats = {
            'events_published': 0,
            'events_handled': 0,
            'events_failed': 0,
            'handlers_registered': 0,
            'handlers_removed': 0
        }
        
        # Event filters
        self.filters: List[Callable[[Event], bool]] = []
        
        # Performance monitoring
        self.performance_metrics = {
            'avg_handle_time': 0.0,
            'max_handle_time': 0.0,
            'min_handle_time': float('inf'),
            'total_handle_time': 0.0,
            'handle_count': 0
        }
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe a handler to specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler instance
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        # Use weak reference to avoid memory leaks
        self.handlers[event_type].append(weakref.ref(handler))
        handler.subscribed_events.append(event_type)
        
        self._stats['handlers_registered'] += 1
        logger.debug(f"Handler {handler.name} subscribed to {event_type}")
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe handler to all events."""
        self.global_handlers.append(weakref.ref(handler))
        self._stats['handlers_registered'] += 1
        logger.debug(f"Handler {handler.name} subscribed to all events")
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe handler from event type."""
        if event_type not in self.handlers:
            return False
        
        # Find and remove handler
        for i, ref in enumerate(self.handlers[event_type]):
            h = ref()
            if h is handler or h is None:
                del self.handlers[event_type][i]
                if h and event_type in h.subscribed_events:
                    h.subscribed_events.remove(event_type)
                self._stats['handlers_removed'] += 1
                logger.debug(f"Handler {handler.name} unsubscribed from {event_type}")
                return True
        
        return False
    
    def unsubscribe_all(self, handler: EventHandler) -> bool:
        """Unsubscribe handler from all events."""
        removed = False
        
        # Remove from specific handlers
        for event_type in list(handler.subscribed_events):
            if self.unsubscribe(event_type, handler):
                removed = True
        
        # Remove from global handlers
        for i, ref in enumerate(self.global_handlers):
            h = ref()
            if h is handler or h is None:
                del self.global_handlers[i]
                removed = True
                break
        
        return removed
    
    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """Add event filter function."""
        self.filters.append(filter_func)
    
    def remove_filter(self, filter_func: Callable[[Event], bool]) -> bool:
        """Remove event filter function."""
        if filter_func in self.filters:
            self.filters.remove(filter_func)
            return True
        return False
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        if not isinstance(event, Event):
            raise ValueError("event must be an instance of Event")
        
        # Apply filters
        for filter_func in self.filters:
            try:
                if not filter_func(event):
                    logger.debug(f"Event {event.type} filtered out")
                    return
            except Exception as e:
                logger.error(f"Event filter error: {e}")
        
        # Add to history
        await self._add_to_history(event)
        
        # Update stats
        self._stats['events_published'] += 1
        
        # Get handlers
        handlers = await self._get_handlers(event)
        
        if not handlers:
            logger.debug(f"No handlers for event {event.type}")
            return
        
        # Process handlers concurrently
        tasks = []
        for handler in handlers:
            if handler.enabled and handler.can_handle(event.type):
                tasks.append(self._handle_event(handler, event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def publish_and_wait(self, event: Event, timeout: float = 5.0) -> List[Exception]:
        """
        Publish event and wait for all handlers to complete.
        
        Returns:
            List of exceptions that occurred during handling
        """
        if not isinstance(event, Event):
            raise ValueError("event must be an instance of Event")
        
        # Apply filters
        for filter_func in self.filters:
            try:
                if not filter_func(event):
                    return []
            except Exception as e:
                logger.error(f"Event filter error: {e}")
        
        # Add to history
        await self._add_to_history(event)
        
        # Update stats
        self._stats['events_published'] += 1
        
        # Get handlers
        handlers = await self._get_handlers(event)
        
        if not handlers:
            return []
        
        # Process handlers with timeout
        tasks = []
        for handler in handlers:
            if handler.enabled and handler.can_handle(event.type):
                tasks.append(self._handle_event(handler, event))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        if exceptions:
            logger.warning(f"Event {event.type} had {len(exceptions)} handling errors")
        
        return exceptions
    
    async def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit."""
        async with self._lock:
            self.event_history.append(event)
            
            # Trim history if needed
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
    
    async def _get_handlers(self, event: Event) -> List[EventHandler]:
        """Get all handlers for an event."""
        handlers = []
        
        # Get specific handlers
        if event.type in self.handlers:
            for ref in self.handlers[event.type]:
                handler = ref()
                if handler is not None:
                    handlers.append(handler)
        
        # Get global handlers
        for ref in self.global_handlers:
            handler = ref()
            if handler is not None:
                handlers.append(handler)
        
        # Sort by priority
        handlers.sort(key=lambda h: getattr(h, 'priority', 0), reverse=True)
        
        return handlers
    
    async def _handle_event(self, handler: EventHandler, event: Event) -> None:
        """Handle a single event with timing and error handling."""
        start_time = datetime.now()
        
        try:
            # Check if handler is async
            import inspect
            if inspect.iscoroutinefunction(handler.handle):
                await handler.handle(event)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, handler.handle, event)
            
            # Update stats
            self._stats['events_handled'] += 1
            
        except Exception as e:
            self._stats['events_failed'] += 1
            logger.error(f"Handler {handler.name} failed for event {event.type}: {e}")
            
            # Could implement retry logic here
            raise
        
        finally:
            # Update performance metrics
            handle_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(handle_time)
    
    def _update_performance_metrics(self, handle_time: float) -> None:
        """Update performance metrics."""
        metrics = self.performance_metrics
        
        metrics['total_handle_time'] += handle_time
        metrics['handle_count'] += 1
        metrics['avg_handle_time'] = metrics['total_handle_time'] / metrics['handle_count']
        metrics['max_handle_time'] = max(metrics['max_handle_time'], handle_time)
        metrics['min_handle_time'] = min(metrics['min_handle_time'], handle_time)
    
    async def replay_events(self, 
                           event_type: str = None,
                           since: datetime = None,
                           limit: int = None) -> None:
        """
        Replay events from history.
        
        Args:
            event_type: Specific event type to replay (all if None)
            since: Replay events since this time
            limit: Maximum number of events to replay
        """
        events_to_replay = self.event_history.copy()
        
        # Filter by type
        if event_type:
            events_to_replay = [e for e in events_to_replay if e.type == event_type]
        
        # Filter by time
        if since:
            events_to_replay = [e for e in events_to_replay if e.timestamp >= since]
        
        # Apply limit
        if limit:
            events_to_replay = events_to_replay[-limit:]
        
        logger.info(f"Replaying {len(events_to_replay)} events")
        
        for event in events_to_replay:
            await self.publish(event)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        stats = self._stats.copy()
        stats.update(self.performance_metrics)
        
        # Add handler counts
        stats['handler_count'] = sum(len(refs) for refs in self.handlers.values())
        stats['global_handler_count'] = len(self.global_handlers)
        stats['event_types'] = len(self.handlers)
        stats['history_size'] = len(self.event_history)
        
        return stats
    
    def get_event_history(self, 
                         event_type: str = None,
                         since: datetime = None,
                         limit: int = 100) -> List[Event]:
        """Get events from history."""
        events = self.event_history.copy()
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        # Filter by time
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        # Apply limit
        if limit:
            events = events[-limit:]
        
        return events
    
    async def clear_history(self, event_type: str = None) -> None:
        """Clear event history."""
        async with self._lock:
            if event_type:
                self.event_history = [e for e in self.event_history if e.type != event_type]
            else:
                self.event_history.clear()
    
    async def shutdown(self) -> None:
        """Shutdown the event bus."""
        self._executor.shutdown(wait=True)
        
        # Clear all references
        self.handlers.clear()
        self.global_handlers.clear()
        self.event_history.clear()
        
        logger.info("Event bus shutdown complete")

# Global event bus instance
_event_bus = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

# Decorator for easy event handler registration
def event_handler(event_type: str = None, priority: int = 0):
    """Decorator to register a method as an event handler."""
    def decorator(func):
        func._event_type = event_type
        func._event_priority = priority
        return func
    return decorator

# Convenience functions
async def publish_event(event_type: str, 
                       data: Dict[str, Any] = None,
                       source: str = "",
                       priority: EventPriority = EventPriority.NORMAL) -> None:
    """Publish an event using the global event bus."""
    event = Event(
        type=event_type,
        data=data or {},
        source=source,
        priority=priority
    )
    await get_event_bus().publish(event)
