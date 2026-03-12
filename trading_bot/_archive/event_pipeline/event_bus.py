"""
AlphaAlgo Event Bus
====================
Pub/sub messaging with delivery guarantees, backpressure, and fault tolerance.
Supports multiple delivery semantics: at-most-once, at-least-once, exactly-once.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    Set, TypeVar, Generic, Union
)
from collections import defaultdict, deque
import threading

from .events import Event, EventType, EventEnvelope, EventPriority

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Event)


class DeliveryGuarantee(Enum):
    """Message delivery guarantees"""
    AT_MOST_ONCE = auto()   # Fire and forget (fastest)
    AT_LEAST_ONCE = auto()  # Retry until ack (default)
    EXACTLY_ONCE = auto()   # Idempotent delivery (slowest)


class BackpressureStrategy(Enum):
    """Backpressure handling strategies"""
    DROP_OLDEST = auto()    # Drop oldest messages when full
    DROP_NEWEST = auto()    # Drop new messages when full
    BLOCK = auto()          # Block producer until space available
    SAMPLE = auto()         # Sample messages (drop random)


class SubscriptionType(Enum):
    """Subscription types"""
    EXCLUSIVE = auto()      # Only one subscriber per topic
    SHARED = auto()         # Round-robin among subscribers
    BROADCAST = auto()      # All subscribers receive all messages


@dataclass
class EventBusConfig:
    """Configuration for event bus"""
    # Delivery
    default_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    
    # Queues
    max_queue_size: int = 10000
    backpressure_strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST
    
    # Timeouts
    delivery_timeout_ms: int = 30000
    ack_timeout_ms: int = 5000
    
    # Retries
    max_retries: int = 3
    retry_delay_ms: int = 1000
    retry_backoff_multiplier: float = 2.0
    
    # Batching
    batch_size: int = 100
    batch_timeout_ms: int = 50
    
    # Workers
    num_workers: int = 4
    
    # Monitoring
    enable_metrics: bool = True
    metrics_interval_ms: int = 10000


@dataclass
class Subscription:
    """Represents a subscription to events"""
    subscription_id: str
    subscriber_id: str
    
    # Topic/type filtering
    topics: List[str] = field(default_factory=list)
    event_types: List[EventType] = field(default_factory=list)
    partition_keys: List[str] = field(default_factory=list)
    
    # Subscription type
    subscription_type: SubscriptionType = SubscriptionType.BROADCAST
    
    # Handler
    handler: Optional[Callable[[Event], Awaitable[None]]] = None
    
    # Delivery
    guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    
    # State
    active: bool = True
    created_at_ns: int = 0
    last_event_ns: int = 0
    events_received: int = 0
    events_processed: int = 0
    events_failed: int = 0
    
    def matches(self, event: Event, topic: str = "") -> bool:
        """Check if event matches subscription filters"""
        if not self.active:
            return False
        
        if self.topics and topic not in self.topics:
            return False
        
        if self.event_types and event.metadata.event_type not in self.event_types:
            return False
        
        if self.partition_keys and event.metadata.partition_key not in self.partition_keys:
            return False
        
        return True


@dataclass
class PendingDelivery:
    """Tracks pending message delivery"""
    envelope: EventEnvelope
    topic: str
    subscription_id: str
    attempts: int = 0
    next_retry_ns: int = 0
    created_at_ns: int = field(default_factory=time.time_ns)


class DeadLetterQueue:
    """Queue for failed messages"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: deque = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
    
    async def add(self, envelope: EventEnvelope, reason: str):
        """Add failed message to DLQ"""
        async with self._lock:
            envelope.to_dead_letter(reason)
            self._queue.append({
                'envelope': envelope,
                'reason': reason,
                'timestamp': time.time_ns(),
            })
            logger.warning(f"Event {envelope.event.event_id} sent to DLQ: {reason}")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all messages in DLQ"""
        async with self._lock:
            return list(self._queue)
    
    async def retry(self, event_id: str) -> Optional[EventEnvelope]:
        """Remove and return message for retry"""
        async with self._lock:
            for i, item in enumerate(self._queue):
                if item['envelope'].event.event_id == event_id:
                    self._queue.remove(item)
                    return item['envelope']
        return None
    
    def size(self) -> int:
        return len(self._queue)


class TopicQueue:
    """Queue for a specific topic"""
    
    def __init__(
        self,
        topic: str,
        max_size: int = 10000,
        backpressure: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST
    ):
        self.topic = topic
        self.max_size = max_size
        self.backpressure = backpressure
        
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._overflow: deque = deque(maxlen=1000)
        
        # Metrics
        self.enqueued = 0
        self.dequeued = 0
        self.dropped = 0
    
    async def put(self, envelope: EventEnvelope) -> bool:
        """Put message in queue, handle backpressure"""
        try:
            if self.backpressure == BackpressureStrategy.BLOCK:
                await self._queue.put(envelope)
            else:
                self._queue.put_nowait(envelope)
            self.enqueued += 1
            return True
        except asyncio.QueueFull:
            if self.backpressure == BackpressureStrategy.DROP_OLDEST:
                try:
                    self._queue.get_nowait()
                    self._queue.put_nowait(envelope)
                    self.dropped += 1
                    return True
                except Exception as e:
                    logger.error(f"Error dropping oldest: {e}")
            elif self.backpressure == BackpressureStrategy.DROP_NEWEST:
                self.dropped += 1
                return False
            elif self.backpressure == BackpressureStrategy.SAMPLE:
                try:
                    import random
                    if random.random() < 0.5:
                        self._queue.get_nowait()
                        self._queue.put_nowait(envelope)
                        return True
                except Exception as e:
                    logger.error(f"Error sampling: {e}")
                self.dropped += 1
                return False
        return False
    
    async def get(self, timeout: float = None) -> Optional[EventEnvelope]:
        """Get message from queue"""
        try:
            if timeout:
                envelope = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=timeout
                )
            else:
                envelope = await self._queue.get()
            self.dequeued += 1
            return envelope
        except asyncio.TimeoutError:
            return None
    
    def size(self) -> int:
        return self._queue.qsize()


class EventBus:
    """
    Central event bus for pub/sub messaging.
    Supports multiple delivery guarantees and fault tolerance.
    """
    
    def __init__(self, config: EventBusConfig = None):
        self.config = config or EventBusConfig()
        
        # Subscriptions by topic
        self._subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self._subscription_by_id: Dict[str, Subscription] = {}
        
        # Topic queues
        self._queues: Dict[str, TopicQueue] = {}
        
        # Dead letter queue
        self.dlq = DeadLetterQueue()
        
        # Pending deliveries for retry
        self._pending: Dict[str, PendingDelivery] = {}
        
        # Idempotency tracking (for exactly-once)
        self._processed_ids: Set[str] = set()
        self._processed_ids_max = 100000
        
        # Workers
        self._workers: List[asyncio.Task] = []
        self._running = False
        
        # Metrics
        self.metrics = {
            'published': 0,
            'delivered': 0,
            'failed': 0,
            'retried': 0,
            'dlq_size': 0,
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("EventBus initialized")
    
    async def start(self):
        """Start the event bus"""
        self._running = True
        
        # Start worker tasks
        for i in range(self.config.num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)
        
        # Start retry task
        self._retry_task = asyncio.create_task(self._retry_loop())
        
        logger.info(f"EventBus started with {self.config.num_workers} workers")
    
    async def stop(self):
        """Stop the event bus"""
        self._running = False
        
        # Cancel workers
        for task in self._workers:
            task.cancel()
        
        if hasattr(self, '_retry_task'):
            self._retry_task.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("EventBus stopped")
    
    def _get_or_create_queue(self, topic: str) -> TopicQueue:
        """Get or create queue for topic"""
        if topic not in self._queues:
            self._queues[topic] = TopicQueue(
                topic=topic,
                max_size=self.config.max_queue_size,
                backpressure=self.config.backpressure_strategy,
            )
        return self._queues[topic]
    
    async def publish(
        self,
        topic: str,
        event: Event,
        guarantee: DeliveryGuarantee = None
    ) -> bool:
        """
        Publish event to topic.
        
        Args:
            topic: Topic name
            event: Event to publish
            guarantee: Delivery guarantee (uses default if None)
            
        Returns:
            True if published successfully
        """
        guarantee = guarantee or self.config.default_guarantee
        
        # Create envelope
        envelope = EventEnvelope(
            event=event,
            destination=topic,
            max_attempts=self.config.max_retries,
        )
        envelope.mark_sent()
        
        # Get queue
        queue = self._get_or_create_queue(topic)
        
        # Enqueue
        success = await queue.put(envelope)
        
        if success:
            self.metrics['published'] += 1
        
        return success
    
    async def publish_batch(
        self,
        topic: str,
        events: List[Event],
        guarantee: DeliveryGuarantee = None
    ) -> int:
        """Publish batch of events, return count published"""
        count = 0
        for event in events:
            if await self.publish(topic, event, guarantee):
                count += 1
        return count
    
    def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Event], Awaitable[None]],
        event_types: List[EventType] = None,
        subscription_type: SubscriptionType = SubscriptionType.BROADCAST,
        guarantee: DeliveryGuarantee = None,
        subscriber_id: str = None,
    ) -> str:
        """
        Subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
            handler: Async handler function
            event_types: Filter by event types
            subscription_type: Subscription type
            guarantee: Delivery guarantee
            subscriber_id: Subscriber identifier
            
        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        
        subscription = Subscription(
            subscription_id=subscription_id,
            subscriber_id=subscriber_id or subscription_id,
            topics=topics,
            event_types=event_types or [],
            subscription_type=subscription_type,
            handler=handler,
            guarantee=guarantee or self.config.default_guarantee,
            created_at_ns=time.time_ns(),
        )
        
        # Register subscription
        for topic in topics:
            self._subscriptions[topic].append(subscription)
            # Ensure queue exists
            self._get_or_create_queue(topic)
        
        self._subscription_by_id[subscription_id] = subscription
        
        logger.info(f"Subscription {subscription_id} created for topics: {topics}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe by subscription ID"""
        if subscription_id not in self._subscription_by_id:
            return False
        
        subscription = self._subscription_by_id[subscription_id]
        subscription.active = False
        
        # Remove from topic lists
        for topic in subscription.topics:
            if topic in self._subscriptions:
                self._subscriptions[topic] = [
                    s for s in self._subscriptions[topic]
                    if s.subscription_id != subscription_id
                ]
        
        del self._subscription_by_id[subscription_id]
        
        logger.info(f"Subscription {subscription_id} removed")
        return True
    
    async def _worker_loop(self, worker_id: int):
        """Worker loop for processing messages"""
        logger.debug(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Round-robin through queues
                for topic, queue in list(self._queues.items()):
                    envelope = await queue.get(timeout=0.1)
                    if envelope:
                        await self._deliver(topic, envelope)
                
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _deliver(self, topic: str, envelope: EventEnvelope):
        """Deliver message to subscribers"""
        event = envelope.event
        subscriptions = self._subscriptions.get(topic, [])
        
        # Filter matching subscriptions
        matching = [s for s in subscriptions if s.matches(event, topic)]
        
        if not matching:
            return
        
        # Handle subscription types
        if matching[0].subscription_type == SubscriptionType.EXCLUSIVE:
            matching = matching[:1]
        elif matching[0].subscription_type == SubscriptionType.SHARED:
            # Round-robin
            idx = envelope.attempt % len(matching)
            matching = [matching[idx]]
        
        # Deliver to each subscriber
        for subscription in matching:
            await self._deliver_to_subscriber(topic, envelope, subscription)
    
    async def _deliver_to_subscriber(
        self,
        topic: str,
        envelope: EventEnvelope,
        subscription: Subscription
    ):
        """Deliver to a specific subscriber"""
        event = envelope.event
        
        # Check idempotency for exactly-once
        if subscription.guarantee == DeliveryGuarantee.EXACTLY_ONCE:
            try:
                idempotency_key = f"{subscription.subscription_id}:{event.metadata.idempotency_key}"
                if idempotency_key in self._processed_ids:
                    logger.debug(f"Skipping duplicate: {idempotency_key}")
                    return

                envelope.attempt += 1
                subscription.events_received += 1

                # Call handler
                if subscription.handler:
                    await asyncio.wait_for(
                        subscription.handler(event),
                        timeout=self.config.delivery_timeout_ms / 1000
                    )

                # Mark delivered
                envelope.mark_delivered()
                subscription.events_processed += 1
                subscription.last_event_ns = time.time_ns()
                self.metrics['delivered'] += 1

                # Track for exactly-once
                if subscription.guarantee == DeliveryGuarantee.EXACTLY_ONCE:
                    idempotency_key = f"{subscription.subscription_id}:{event.metadata.idempotency_key}"
                    self._processed_ids.add(idempotency_key)

                    # Limit size
                    if len(self._processed_ids) > self._processed_ids_max:
                        # Remove oldest (approximate)
                        to_remove = len(self._processed_ids) - self._processed_ids_max // 2
                        for _ in range(to_remove):
                            self._processed_ids.pop()

            except asyncio.TimeoutError:
                await self._handle_delivery_failure(
                    topic, envelope, subscription, "Timeout"
                )
            except Exception as e:
                await self._handle_delivery_failure(
                    topic, envelope, subscription, str(e)
                )

    async def _handle_delivery_failure(
        self,
        topic: str,
        envelope: EventEnvelope,
        subscription: Subscription,
        reason: str
    ):
        """Handle delivery failure"""
        subscription.events_failed += 1
        self.metrics['failed'] += 1
        
        if subscription.guarantee == DeliveryGuarantee.AT_MOST_ONCE:
            # Don't retry
            logger.warning(f"Delivery failed (no retry): {reason}")
            return
        
        if envelope.attempt >= envelope.max_attempts:
            # Send to DLQ
            await self.dlq.add(envelope, reason)
            self.metrics['dlq_size'] = self.dlq.size()
            return
        
        # Schedule retry
        delay_ms = self.config.retry_delay_ms * (
            self.config.retry_backoff_multiplier ** (envelope.attempt - 1)
        )
        next_retry = time.time_ns() + int(delay_ms * 1_000_000)
        
        pending = PendingDelivery(
            envelope=envelope,
            topic=topic,
            subscription_id=subscription.subscription_id,
            attempts=envelope.attempt,
            next_retry_ns=next_retry,
        )
        
        self._pending[envelope.envelope_id] = pending
        self.metrics['retried'] += 1
        
        logger.debug(f"Scheduled retry for {envelope.event.event_id} in {delay_ms}ms")
    
    async def _retry_loop(self):
        """Retry pending deliveries"""
        while self._running:
            try:
                now = time.time_ns()
                
                # Find ready retries
                ready = [
                    (pid, p) for pid, p in self._pending.items()
                    if p.next_retry_ns <= now
                ]
                
                for pending_id, pending in ready:
                    del self._pending[pending_id]
                    
                    subscription = self._subscription_by_id.get(pending.subscription_id)
                    if subscription and subscription.active:
                        await self._deliver_to_subscriber(
                            pending.topic,
                            pending.envelope,
                            subscription
                        )
                
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Retry loop error: {e}")
                await asyncio.sleep(1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bus metrics"""
        queue_metrics = {
            topic: {
                'size': q.size(),
                'enqueued': q.enqueued,
                'dequeued': q.dequeued,
                'dropped': q.dropped,
            }
            for topic, q in self._queues.items()
        }
        
        subscription_metrics = {
            sid: {
                'topics': s.topics,
                'received': s.events_received,
                'processed': s.events_processed,
                'failed': s.events_failed,
            }
            for sid, s in self._subscription_by_id.items()
        }
        
        return {
            **self.metrics,
            'queues': queue_metrics,
            'subscriptions': subscription_metrics,
            'pending_retries': len(self._pending),
        }
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self._subscription_by_id.get(subscription_id)
    
    def list_topics(self) -> List[str]:
        """List all topics"""
        return list(self._queues.keys())
    
    def list_subscriptions(self, topic: str = None) -> List[Subscription]:
        """List subscriptions, optionally filtered by topic"""
        if topic:
            return self._subscriptions.get(topic, [])
        return list(self._subscription_by_id.values())
