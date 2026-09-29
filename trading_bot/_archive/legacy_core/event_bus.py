"""
Event Bus - Bridged to UnifiedDecisionBus (UCA V5)
================================================

Compatibility layer for legacy service communication.
Redirects all traffic to the authoritative UnifiedDecisionBus (LogAct Backbone).
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union
from uuid import uuid4

from .unified_event_bus import decision_bus, UnifiedEvent, EventPriority as UnifiedEventPriority

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Event:
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

class EventBus:
    def __init__(self, config: Optional[Dict] = None):
        self.unified_bus = decision_bus
        logger.info("Legacy EventBus wrapper initialized (Bridged to UnifiedDecisionBus)")

    def subscribe(self, subscriber_id: str, event_types: List[str], handler: Callable, **kwargs):
        self.unified_bus.subscribe(subscriber_id, event_types, handler, **kwargs)

    async def publish(self, event: Event):
        unified_event = UnifiedEvent(
            event_type=event.event_type,
            payload=event.payload,
            source=event.source,
            event_id=event.event_id,
            timestamp=event.timestamp,
            priority=UnifiedEventPriority[event.priority.name],
            correlation_id=event.correlation_id,
            metadata=event.metadata
        )
        await self.unified_bus.publish(unified_event)

    async def start(self):
        await self.unified_bus.start()

    async def stop(self):
        await self.unified_bus.stop()

_event_bus = None

def get_event_bus():
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

def create_event_bus(config=None):
    return EventBus(config)

class EventTypes:
    MARKET_DATA_UPDATE = "market.data.update"
    TRADE_APPROVED = "trade.approved"
    TRADE_REJECTED = "trade.rejected"
    SYSTEM_ERROR = "system.error"
    # ... more can be added as needed or referenced from standard
