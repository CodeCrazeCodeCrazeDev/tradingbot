"""
Event Bus - Async Event-Driven Architecture
============================================

Central event bus for service communication:
- Publish/Subscribe pattern
- Event routing and filtering
- Async event processing
- Event history and replay
- Dead letter queue for failed events
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
from uuid import uuid4
import json

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventStatus(Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class Event:
    """Event data structure"""
    event_type: str
    payload: Dict[str, Any]
    source: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.name,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata,
        }


@dataclass
class Subscription:
    """Event subscription"""
    subscriber_id: str
    event_types: Set[str]
    handler: Callable[[Event], Coroutine[Any, Any, None]]
    filter_fn: Optional[Callable[[Event], bool]] = None
    priority: int = 0


class EventBus:
    """
    Async Event Bus for Service Communication
    
    Features:
    - Async publish/subscribe
    - Event filtering
    - Priority queuing
    - Dead letter queue
    - Event history
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._subscribers: Dict[str, List[Subscription]] = defaultdict(list)
        self._event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._dead_letter_queue: List[Event] = []
        self._event_history: List[Event] = []
        self._max_history = self.config.get('max_history', 1000)
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info("EventBus initialized")
    
    async def start(self) -> None:
        """Start event processing"""
        if self._running:
            return
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")
    
    async def stop(self) -> None:
        """Stop event processing"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus stopped")
    
    def subscribe(
        self,
        subscriber_id: str,
        event_types: List[str],
        handler: Callable[[Event], Coroutine[Any, Any, None]],
        filter_fn: Optional[Callable[[Event], bool]] = None,
        priority: int = 0
    ) -> None:
        """Subscribe to events"""
        subscription = Subscription(
            subscriber_id=subscriber_id,
            event_types=set(event_types),
            handler=handler,
            filter_fn=filter_fn,
            priority=priority
        )
        
        for event_type in event_types:
            self._subscribers[event_type].append(subscription)
            # Sort by priority (higher first)
            self._subscribers[event_type].sort(key=lambda s: -s.priority)
        
        logger.debug(f"Subscriber {subscriber_id} registered for {event_types}")
    
    def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe from all events"""
        for event_type in list(self._subscribers.keys()):
            self._subscribers[event_type] = [
                s for s in self._subscribers[event_type]
                if s.subscriber_id != subscriber_id
            ]
        logger.debug(f"Subscriber {subscriber_id} unsubscribed")
    
    async def publish(self, event: Event) -> None:
        """Publish an event"""
        # Add to queue with priority (negative for max-heap behavior)
        await self._event_queue.put((-event.priority.value, event.timestamp, event))
        logger.debug(f"Event published: {event.event_type} from {event.source}")
    
    async def publish_and_wait(self, event: Event, timeout: float = 30.0) -> bool:
        """Publish event and wait for processing"""
        completion_event = asyncio.Event()
        event.metadata['_completion_event'] = completion_event
        await self.publish(event)
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Event {event.event_id} timed out")
            return False
    
    async def _process_events(self) -> None:
        """Process events from queue"""
        while self._running:
            try:
                # Get event with timeout to allow checking running flag
                try:
                    _, _, event = await asyncio.wait_for(
                        self._event_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process event
                await self._dispatch_event(event)
                
                # Store in history
                async with self._lock:
                    self._event_history.append(event)
                    if len(self._event_history) > self._max_history:
                        self._event_history = self._event_history[-self._max_history:]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to subscribers"""
        subscribers = self._subscribers.get(event.event_type, [])
        # Also get wildcard subscribers
        subscribers.extend(self._subscribers.get('*', []))
        
        if not subscribers:
            logger.debug(f"No subscribers for {event.event_type}")
            return
        
        for subscription in subscribers:
            # Apply filter if present
            if subscription.filter_fn and not subscription.filter_fn(event):
                continue
            
            try:
                await subscription.handler(event)
            except Exception as e:
                logger.error(
                    f"Handler error for {subscription.subscriber_id}: {e}"
                )
                event.retry_count += 1
                
                if event.retry_count < event.max_retries:
                    # Re-queue for retry
                    await self.publish(event)
                else:
                    # Move to dead letter queue
                    self._dead_letter_queue.append(event)
                    logger.warning(f"Event {event.event_id} moved to dead letter queue")
        
        # Signal completion if waiting
        completion_event = event.metadata.get('_completion_event')
        if completion_event:
            completion_event.set()
    
    def get_dead_letters(self) -> List[Event]:
        """Get dead letter queue"""
        return self._dead_letter_queue.copy()
    
    def clear_dead_letters(self) -> int:
        """Clear dead letter queue"""
        count = len(self._dead_letter_queue)
        self._dead_letter_queue.clear()
        return count
    
    async def replay_events(
        self,
        event_types: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> int:
        """Replay events from history"""
        count = 0
        for event in self._event_history:
            if event_types and event.event_type not in event_types:
                continue
            if since and event.timestamp < since:
                continue
            await self.publish(event)
            count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            'queue_size': self._event_queue.qsize(),
            'history_size': len(self._event_history),
            'dead_letter_count': len(self._dead_letter_queue),
            'subscriber_count': sum(len(s) for s in self._subscribers.values()),
            'event_types': list(self._subscribers.keys()),
            'running': self._running,
        }


# Singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get singleton event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def create_event_bus(config: Optional[Dict] = None) -> EventBus:
    """Factory function to create EventBus instance"""
    return EventBus(config)


# Common event types
class EventTypes:
    """Standard event type constants"""
    # Market events
    MARKET_DATA_UPDATE = "market.data.update"
    MARKET_TICK = "market.tick"
    MARKET_CANDLE = "market.candle"
    MARKET_DEPTH = "market.depth"
    
    # Signal events
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_VALIDATED = "signal.validated"
    SIGNAL_REJECTED = "signal.rejected"
    
    # Trade events
    TRADE_REQUESTED = "trade.requested"
    TRADE_REQUEST = "trade.request"
    TRADE_APPROVED = "trade.approved"
    TRADE_REJECTED = "trade.rejected"
    TRADE_SIZED = "trade.sized"
    TRADE_EXECUTED = "trade.executed"
    TRADE_FAILED = "trade.failed"
    TRADE_CLOSED = "trade.closed"
    
    # Order events
    ORDER_PLACED = "order.placed"
    ORDER_FILLED = "order.filled"
    ORDER_REJECTED = "order.rejected"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_CANCEL_REQUEST = "order.cancel.request"
    
    # Position events
    POSITION_OPENED = "position.opened"
    POSITION_CLOSED = "position.closed"
    POSITION_UPDATED = "position.updated"
    
    # Alpha events
    ALPHA_SIGNAL = "alpha.signal"
    
    # Risk events
    RISK_CHECK_PASSED = "risk.check.passed"
    RISK_CHECK_FAILED = "risk.check.failed"
    RISK_LIMIT_BREACH = "risk.limit.breach"
    RISK_LIMIT_EXCEEDED = "risk.limit.exceeded"
    DRAWDOWN_WARNING = "risk.drawdown.warning"
    
    # Broker events
    BROKER_CONNECTED = "broker.connected"
    BROKER_DISCONNECTED = "broker.disconnected"
    BROKER_ERROR = "broker.error"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH_CHECK = "system.health.check"
    SYSTEM_STATUS = "system.status"
    
    # Service events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_ERROR = "service.error"
    SERVICE_HEALTH = "service.health"
    
    # AI events
    AI_ANALYSIS_COMPLETE = "ai.analysis.complete"
    AI_PREDICTION_READY = "ai.prediction.ready"
    AI_MODEL_UPDATED = "ai.model.updated"
    AI_LEARNING_CYCLE = "ai.learning.cycle"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETE = "workflow.step.complete"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
