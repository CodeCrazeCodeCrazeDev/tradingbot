"""
AlphaAlgo Event Consumers
==========================
Fault-tolerant event consumers with dead letter queues, retries, and backpressure.
Supports consumer groups for horizontal scaling.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    Set, TypeVar, Generic
)
from collections import defaultdict

from .events import Event, EventType, EventPriority
from .event_bus import EventBus, Subscription, DeliveryGuarantee, SubscriptionType

logger = logging.getLogger(__name__)


class ConsumerState(Enum):
    """Consumer lifecycle states"""
    CREATED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 60000
    backoff_multiplier: float = 2.0
    retry_on_exceptions: List[type] = field(default_factory=list)
    
    def get_delay(self, attempt: int) -> int:
        """Calculate delay for attempt number"""
        delay = self.initial_delay_ms * (self.backoff_multiplier ** attempt)
        return min(int(delay), self.max_delay_ms)


@dataclass
class ConsumerConfig:
    """Configuration for event consumers"""
    # Identity
    consumer_id: str = ""
    group_id: str = ""
    
    # Topics
    topics: List[str] = field(default_factory=list)
    event_types: List[EventType] = field(default_factory=list)
    
    # Processing
    max_concurrent: int = 10
    batch_size: int = 1
    
    # Delivery
    guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    
    # Retry
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    
    # Timeouts
    processing_timeout_ms: int = 30000
    poll_timeout_ms: int = 1000
    
    # Backpressure
    max_pending: int = 1000
    pause_threshold: float = 0.8
    resume_threshold: float = 0.5
    
    # Health
    heartbeat_interval_ms: int = 10000


@dataclass
class ConsumerOffset:
    """Tracks consumer position in event stream"""
    topic: str
    partition: int = 0
    offset: int = 0
    timestamp_ns: int = 0
    committed: bool = False


class DeadLetterQueue:
    """Dead letter queue for failed events"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def add(
        self,
        event: Event,
        error: str,
        consumer_id: str,
        attempts: int
    ):
        """Add failed event to DLQ"""
        async with self._lock:
            entry = {
                'event': event,
                'error': error,
                'consumer_id': consumer_id,
                'attempts': attempts,
                'timestamp': time.time_ns(),
                'event_id': event.event_id,
            }
            
            if len(self._queue) >= self.max_size:
                self._queue.pop(0)
            
            self._queue.append(entry)
            logger.warning(
                f"Event {event.event_id} added to DLQ after {attempts} attempts: {error}"
            )
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all DLQ entries"""
        async with self._lock:
            return list(self._queue)
    
    async def remove(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Remove and return entry by event ID"""
        async with self._lock:
            for i, entry in enumerate(self._queue):
                if entry['event_id'] == event_id:
                    return self._queue.pop(i)
        return None
    
    async def retry_all(self) -> List[Event]:
        """Remove and return all events for retry"""
        async with self._lock:
            events = [entry['event'] for entry in self._queue]
            self._queue.clear()
            return events
    
    def size(self) -> int:
        return len(self._queue)


class EventConsumer:
    """
    Fault-tolerant event consumer.
    Handles retries, dead letter queues, and backpressure.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        handler: Callable[[Event], Awaitable[None]],
        config: ConsumerConfig = None
    ):
        self.event_bus = event_bus
        self.handler = handler
        self.config = config or ConsumerConfig()
        
        if not self.config.consumer_id:
            self.config.consumer_id = str(uuid.uuid4())[:8]
        
        # State
        self.state = ConsumerState.CREATED
        self._subscription_id: Optional[str] = None
        
        # Dead letter queue
        self.dlq = DeadLetterQueue()
        
        # Processing tracking
        self._pending: Dict[str, asyncio.Task] = {}
        self._processing_semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # Retry tracking
        self._retry_counts: Dict[str, int] = {}
        
        # Offsets
        self._offsets: Dict[str, ConsumerOffset] = {}
        
        # Metrics
        self.metrics = {
            'events_received': 0,
            'events_processed': 0,
            'events_failed': 0,
            'events_retried': 0,
            'dlq_size': 0,
            'processing_time_ms': 0,
        }
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        
        logger.info(f"Consumer {self.config.consumer_id} created")
    
    async def start(self):
        """Start the consumer"""
        if self.state == ConsumerState.RUNNING:
            return
        
        self.state = ConsumerState.STARTING
        
        # Subscribe to topics
        self._subscription_id = self.event_bus.subscribe(
            topics=self.config.topics,
            handler=self._handle_event,
            event_types=self.config.event_types,
            subscription_type=SubscriptionType.SHARED if self.config.group_id else SubscriptionType.BROADCAST,
            guarantee=self.config.guarantee,
            subscriber_id=self.config.consumer_id,
        )
        
        # Start heartbeat
        self._tasks.append(
            asyncio.create_task(self._heartbeat_loop())
        )
        
        self.state = ConsumerState.RUNNING
        logger.info(f"Consumer {self.config.consumer_id} started")
    
    async def stop(self):
        """Stop the consumer"""
        if self.state == ConsumerState.STOPPED:
            return
        
        self.state = ConsumerState.STOPPING
        
        # Unsubscribe
        if self._subscription_id:
            self.event_bus.unsubscribe(self._subscription_id)
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for pending processing
        if self._pending:
            await asyncio.gather(*self._pending.values(), return_exceptions=True)
        
        self.state = ConsumerState.STOPPED
        logger.info(f"Consumer {self.config.consumer_id} stopped")
    
    async def pause(self):
        """Pause the consumer"""
        if self.state == ConsumerState.RUNNING:
            self.state = ConsumerState.PAUSED
            logger.info(f"Consumer {self.config.consumer_id} paused")
    
    async def resume(self):
        """Resume the consumer"""
        if self.state == ConsumerState.PAUSED:
            self.state = ConsumerState.RUNNING
            logger.info(f"Consumer {self.config.consumer_id} resumed")
    
    async def _handle_event(self, event: Event):
        """Handle incoming event"""
        if self.state != ConsumerState.RUNNING:
            return
        
        self.metrics['events_received'] += 1
        
        # Check backpressure
        pending_ratio = len(self._pending) / self.config.max_pending
        if pending_ratio >= self.config.pause_threshold:
            await self.pause()
            logger.warning(f"Consumer {self.config.consumer_id} paused due to backpressure")
        
        # Acquire semaphore
        await self._processing_semaphore.acquire()
        
        # Process in background
        task = asyncio.create_task(self._process_event(event))
        self._pending[event.event_id] = task
        task.add_done_callback(
            lambda t: self._on_processing_complete(event.event_id)
        )
    
    def _on_processing_complete(self, event_id: str):
        """Callback when processing completes"""
        self._pending.pop(event_id, None)
        self._processing_semaphore.release()
        
        # Check if we can resume
        if self.state == ConsumerState.PAUSED:
            pending_ratio = len(self._pending) / self.config.max_pending
            if pending_ratio <= self.config.resume_threshold:
                asyncio.create_task(self.resume())
    
    async def _process_event(self, event: Event):
        """Process a single event with retry logic"""
        event_id = event.event_id
        attempt = self._retry_counts.get(event_id, 0)
        
        start_time = time.time()
        
        try:
            # Apply timeout
            await asyncio.wait_for(
                self.handler(event),
                timeout=self.config.processing_timeout_ms / 1000
            )
            
            # Success
            self.metrics['events_processed'] += 1
            self._retry_counts.pop(event_id, None)
            
            # Track processing time
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics['processing_time_ms'] = (
                self.metrics['processing_time_ms'] * 0.9 + elapsed_ms * 0.1
            )
            
        except asyncio.TimeoutError:
            await self._handle_failure(event, "Processing timeout", attempt)
        except Exception as e:
            await self._handle_failure(event, str(e), attempt)
    
    async def _handle_failure(self, event: Event, error: str, attempt: int):
        """Handle processing failure"""
        self.metrics['events_failed'] += 1
        
        # Check if we should retry
        if attempt < self.config.retry_policy.max_retries:
            # Schedule retry
            delay = self.config.retry_policy.get_delay(attempt)
            self._retry_counts[event.event_id] = attempt + 1
            self.metrics['events_retried'] += 1
            
            logger.warning(
                f"Event {event.event_id} failed (attempt {attempt + 1}), "
                f"retrying in {delay}ms: {error}"
            )
            
            await asyncio.sleep(delay / 1000)
            await self._process_event(event)
        else:
            # Send to DLQ
            await self.dlq.add(
                event=event,
                error=error,
                consumer_id=self.config.consumer_id,
                attempts=attempt + 1
            )
            self.metrics['dlq_size'] = self.dlq.size()
            self._retry_counts.pop(event.event_id, None)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        interval = self.config.heartbeat_interval_ms / 1000
        
        while self.state in (ConsumerState.RUNNING, ConsumerState.PAUSED):
            try:
                await asyncio.sleep(interval)
                # Could send heartbeat to coordinator here
                logger.debug(f"Consumer {self.config.consumer_id} heartbeat")
            except asyncio.CancelledError:
                break
    
    async def retry_dlq(self) -> int:
        """Retry all events in DLQ"""
        events = await self.dlq.retry_all()
        self.metrics['dlq_size'] = 0
        
        for event in events:
            self._retry_counts[event.event_id] = 0
            await self._handle_event(event)
        
        return len(events)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get consumer metrics"""
        return {
            **self.metrics,
            'consumer_id': self.config.consumer_id,
            'state': self.state.name,
            'pending': len(self._pending),
            'subscription_id': self._subscription_id,
        }


class ConsumerGroup:
    """
    Consumer group for horizontal scaling.
    Coordinates multiple consumers for load balancing.
    """
    
    def __init__(
        self,
        group_id: str,
        event_bus: EventBus,
        handler: Callable[[Event], Awaitable[None]],
        config: ConsumerConfig = None
    ):
        self.group_id = group_id
        self.event_bus = event_bus
        self.handler = handler
        self.config = config or ConsumerConfig()
        self.config.group_id = group_id
        
        self.consumers: Dict[str, EventConsumer] = {}
        self._lock = asyncio.Lock()
        
        # Shared DLQ
        self.dlq = DeadLetterQueue()
        
        logger.info(f"ConsumerGroup {group_id} created")
    
    async def add_consumer(self) -> str:
        """Add a consumer to the group"""
        async with self._lock:
            consumer_config = ConsumerConfig(
                consumer_id=f"{self.group_id}-{len(self.consumers)}",
                group_id=self.group_id,
                topics=self.config.topics,
                event_types=self.config.event_types,
                max_concurrent=self.config.max_concurrent,
                guarantee=self.config.guarantee,
                retry_policy=self.config.retry_policy,
            )
            
            consumer = EventConsumer(
                event_bus=self.event_bus,
                handler=self.handler,
                config=consumer_config,
            )
            consumer.dlq = self.dlq  # Share DLQ
            
            await consumer.start()
            self.consumers[consumer.config.consumer_id] = consumer
            
            logger.info(f"Added consumer {consumer.config.consumer_id} to group {self.group_id}")
            return consumer.config.consumer_id
    
    async def remove_consumer(self, consumer_id: str) -> bool:
        """Remove a consumer from the group"""
        async with self._lock:
            if consumer_id in self.consumers:
                consumer = self.consumers.pop(consumer_id)
                await consumer.stop()
                logger.info(f"Removed consumer {consumer_id} from group {self.group_id}")
                return True
            return False
    
    async def start(self, num_consumers: int = 1):
        """Start the consumer group with specified number of consumers"""
        for _ in range(num_consumers):
            await self.add_consumer()
        logger.info(f"ConsumerGroup {self.group_id} started with {num_consumers} consumers")
    
    async def stop(self):
        """Stop all consumers in the group"""
        async with self._lock:
            for consumer in self.consumers.values():
                await consumer.stop()
            self.consumers.clear()
        logger.info(f"ConsumerGroup {self.group_id} stopped")
    
    async def scale(self, target_count: int):
        """Scale to target number of consumers"""
        current = len(self.consumers)
        
        if target_count > current:
            for _ in range(target_count - current):
                await self.add_consumer()
        elif target_count < current:
            to_remove = list(self.consumers.keys())[target_count:]
            for consumer_id in to_remove:
                await self.remove_consumer(consumer_id)
        
        logger.info(f"ConsumerGroup {self.group_id} scaled to {target_count} consumers")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get group metrics"""
        consumer_metrics = {
            cid: c.get_metrics() for cid, c in self.consumers.items()
        }
        
        total_processed = sum(
            m['events_processed'] for m in consumer_metrics.values()
        )
        total_failed = sum(
            m['events_failed'] for m in consumer_metrics.values()
        )
        
        return {
            'group_id': self.group_id,
            'num_consumers': len(self.consumers),
            'total_processed': total_processed,
            'total_failed': total_failed,
            'dlq_size': self.dlq.size(),
            'consumers': consumer_metrics,
        }
