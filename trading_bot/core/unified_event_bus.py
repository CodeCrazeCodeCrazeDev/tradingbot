"""
Unified Decision Bus - UCA-2026 Core Component
=============================================

Exactly one authoritative event bus for all internal system communication.
Implements the Singleton pattern and priority-based async dispatch.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union
from uuid import uuid4
import threading

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class UnifiedEvent:
    event_type: str
    payload: Dict[str, Any]
    source: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

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

class UnifiedDecisionBus:
    """
    Authoritative Singleton Event Bus for AlphaAlgo UCA-2026.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UnifiedDecisionBus, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict] = None):
        if self._initialized:
            return

        self.config = config or {}
        self._subscribers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._event_queue: Optional[asyncio.PriorityQueue] = None
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._initialized = True
        logger.info("UnifiedDecisionBus initialized as singleton")

    async def start(self):
        """Start the event processing loop."""
        if self._running:
            return

        self._event_queue = asyncio.PriorityQueue()
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("UnifiedDecisionBus started")

    async def stop(self):
        """Stop the event processing loop."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("UnifiedDecisionBus stopped")

    def subscribe(
        self,
        subscriber_id: str,
        event_types: Union[str, List[str]],
        handler: Callable[[UnifiedEvent], Coroutine[Any, Any, None]],
        priority: int = 0
    ):
        """Subscribe to event types."""
        if isinstance(event_types, str):
            event_types = [event_types]

        for etype in event_types:
            self._subscribers[etype].append({
                "id": subscriber_id,
                "handler": handler,
                "priority": priority
            })
            # Sort by priority descending
            self._subscribers[etype].sort(key=lambda x: x["priority"], reverse=True)

        logger.debug(f"Subscriber {subscriber_id} registered for {event_types}")

    async def publish(self, event: UnifiedEvent):
        """Publish an event to the queue."""
        if not self._running:
            logger.warning("Attempted to publish to stopped UnifiedDecisionBus")
            return

        # Use negative priority for max-priority behavior in PriorityQueue
        await self._event_queue.put((-event.priority.value, event.timestamp, event))

    async def _process_events(self):
        """Internal processing loop."""
        while self._running:
            try:
                _, _, event = await self._event_queue.get()
                await self._dispatch(event)
                self._event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in UnifiedDecisionBus processor: {e}")

    async def _dispatch(self, event: UnifiedEvent):
        """Dispatch event to relevant subscribers."""
        handlers = self._subscribers.get(event.event_type, [])
        # Also check for wildcard subscriptions
        handlers.extend(self._subscribers.get("*", []))

        if not handlers:
            return

        tasks = []
        for h in handlers:
            tasks.append(h["handler"](event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global access point
decision_bus = UnifiedDecisionBus()
