"""
AlphaAlgo Event Router
======================
Routes normalized events to Redpanda/Kafka topics.
Handles partitioning, batching, compression, delivery guarantees.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import uuid
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from collections import deque
from enum import Enum, auto

from .schema import (
    MarketEvent, MarketEventType, EventEnvelope, QualityFlag
)

logger = logging.getLogger(__name__)


class DeliveryGuarantee(Enum):
    """Message delivery guarantees"""
    AT_MOST_ONCE = auto()   # Fire and forget
    AT_LEAST_ONCE = auto()  # Retry until ack
    EXACTLY_ONCE = auto()   # Idempotent + transactions


class CompressionType(Enum):
    """Compression algorithms"""
    NONE = 'none'
    GZIP = 'gzip'
    SNAPPY = 'snappy'
    LZ4 = 'lz4'
    ZSTD = 'zstd'


@dataclass
class TopicConfig:
    """Configuration for a Kafka/Redpanda topic"""
    name: str
    partitions: int = 12
    replication_factor: int = 3
    retention_ms: int = 7 * 24 * 60 * 60 * 1000  # 7 days
    retention_bytes: int = -1  # Unlimited
    segment_ms: int = 60 * 60 * 1000  # 1 hour
    segment_bytes: int = 1073741824  # 1GB
    cleanup_policy: str = 'delete'  # 'delete', 'compact', 'compact,delete'
    compression_type: str = 'lz4'
    min_insync_replicas: int = 2
    max_message_bytes: int = 10485760  # 10MB
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'num.partitions': self.partitions,
            'replication.factor': self.replication_factor,
            'retention.ms': self.retention_ms,
            'retention.bytes': self.retention_bytes,
            'segment.ms': self.segment_ms,
            'segment.bytes': self.segment_bytes,
            'cleanup.policy': self.cleanup_policy,
            'compression.type': self.compression_type,
            'min.insync.replicas': self.min_insync_replicas,
            'max.message.bytes': self.max_message_bytes,
        }


@dataclass
class RouterConfig:
    """Configuration for event router"""
    # Kafka/Redpanda connection
    bootstrap_servers: List[str] = field(default_factory=lambda: ['localhost:9092'])
    client_id: str = 'alphaalgo-router'
    
    # Producer settings
    acks: str = 'all'  # 'all', '1', '0'
    retries: int = 10
    retry_backoff_ms: int = 100
    max_in_flight_requests: int = 5
    enable_idempotence: bool = True
    transactional_id: Optional[str] = None
    
    # Batching
    batch_size: int = 100
    batch_timeout_ms: int = 50
    linger_ms: int = 5
    buffer_memory: int = 33554432  # 32MB
    
    # Compression
    compression_type: CompressionType = CompressionType.LZ4
    compression_level: int = 6
    
    # Delivery
    delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    delivery_timeout_ms: int = 120000  # 2 minutes
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_sample_window_ms: int = 30000


# Topic definitions for AlphaAlgo
TOPIC_CONFIGS = {
    # Raw events by type
    'alphaalgo.trades.raw': TopicConfig(
        name='alphaalgo.trades.raw',
        partitions=24,
        retention_ms=7 * 24 * 60 * 60 * 1000,  # 7 days
        compression_type='lz4',
    ),
    'alphaalgo.quotes.raw': TopicConfig(
        name='alphaalgo.quotes.raw',
        partitions=24,
        retention_ms=24 * 60 * 60 * 1000,  # 1 day (high volume)
        compression_type='lz4',
    ),
    'alphaalgo.l2.raw': TopicConfig(
        name='alphaalgo.l2.raw',
        partitions=48,  # High volume
        retention_ms=12 * 60 * 60 * 1000,  # 12 hours
        compression_type='zstd',  # Better compression for L2
    ),
    
    # Aggregated/processed
    'alphaalgo.trades.normalized': TopicConfig(
        name='alphaalgo.trades.normalized',
        partitions=24,
        retention_ms=30 * 24 * 60 * 60 * 1000,  # 30 days
        compression_type='lz4',
    ),
    'alphaalgo.quotes.normalized': TopicConfig(
        name='alphaalgo.quotes.normalized',
        partitions=24,
        retention_ms=7 * 24 * 60 * 60 * 1000,  # 7 days
        compression_type='lz4',
    ),
    'alphaalgo.orderbook.snapshots': TopicConfig(
        name='alphaalgo.orderbook.snapshots',
        partitions=24,
        retention_ms=7 * 24 * 60 * 60 * 1000,
        compression_type='zstd',
    ),
    
    # Compacted topics for state
    'alphaalgo.orderbook.state': TopicConfig(
        name='alphaalgo.orderbook.state',
        partitions=24,
        cleanup_policy='compact',
        retention_ms=-1,  # Keep forever (compacted)
        compression_type='lz4',
    ),
    'alphaalgo.symbols.metadata': TopicConfig(
        name='alphaalgo.symbols.metadata',
        partitions=1,
        cleanup_policy='compact',
        retention_ms=-1,
        compression_type='gzip',
    ),
    
    # System topics
    'alphaalgo.heartbeats': TopicConfig(
        name='alphaalgo.heartbeats',
        partitions=4,
        retention_ms=60 * 60 * 1000,  # 1 hour
        compression_type='none',
    ),
    'alphaalgo.errors': TopicConfig(
        name='alphaalgo.errors',
        partitions=4,
        retention_ms=7 * 24 * 60 * 60 * 1000,
        compression_type='gzip',
    ),
    'alphaalgo.metrics': TopicConfig(
        name='alphaalgo.metrics',
        partitions=4,
        retention_ms=24 * 60 * 60 * 1000,
        compression_type='gzip',
    ),
}


class TopicResolver:
    """
    Resolves which topic(s) an event should be routed to.
    """
    
    def __init__(self):
        self._custom_rules: List[Callable[[MarketEvent], Optional[str]]] = []
    
    def resolve(self, event: MarketEvent) -> List[str]:
        """
        Resolve target topics for an event.
        Returns list of topic names.
        """
        topics = []
        
        # Primary topic based on event type
        if event.event_type == MarketEventType.TRADE:
            topics.append('alphaalgo.trades.normalized')
        elif event.event_type == MarketEventType.QUOTE:
            topics.append('alphaalgo.quotes.normalized')
        elif event.event_type in (MarketEventType.L2_SNAPSHOT, MarketEventType.L2_DELTA):
            topics.append('alphaalgo.orderbook.snapshots')
        elif event.event_type == MarketEventType.HEARTBEAT:
            topics.append('alphaalgo.heartbeats')
        
        # Apply custom rules
        for rule in self._custom_rules:
            custom_topic = rule(event)
            if custom_topic:
                topics.append(custom_topic)
        
        return topics
    
    def add_rule(self, rule: Callable[[MarketEvent], Optional[str]]):
        """Add custom routing rule"""
        self._custom_rules.append(rule)
    
    @staticmethod
    def get_partition_key(event: MarketEvent) -> str:
        """
        Generate partition key for consistent ordering.
        Events for same symbol go to same partition.
        """
        return f"{event.exchange}:{event.symbol}"


class PartitionStrategy:
    """
    Partition assignment strategies.
    """
    
    @staticmethod
    def by_symbol(event: MarketEvent, num_partitions: int) -> int:
        """Partition by symbol hash"""
        key = f"{event.exchange}:{event.symbol}"
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % num_partitions
    
    @staticmethod
    def by_exchange(event: MarketEvent, num_partitions: int) -> int:
        """Partition by exchange"""
        return int(hashlib.md5(event.exchange.encode()).hexdigest(), 16) % num_partitions
    
    @staticmethod
    def round_robin(counter: int, num_partitions: int) -> int:
        """Round-robin partition assignment"""
        return counter % num_partitions
    
    @staticmethod
    def by_time(event: MarketEvent, num_partitions: int) -> int:
        """Partition by time bucket (for time-ordered replay)"""
        # 1-minute buckets
        bucket = event.exchange_ts // (60 * 1_000_000_000)
        return int(bucket % num_partitions)


class EventRouter:
    """
    Routes normalized events to Kafka/Redpanda topics.
    Handles batching, compression, delivery guarantees.
    """
    
    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig()
        self.topic_resolver = TopicResolver()
        
        # Producer (lazy init)
        self._producer = None
        self._admin_client = None
        
        # Batching
        self._batches: Dict[str, List[MarketEvent]] = {}
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        
        # Stats
        self._events_routed: int = 0
        self._events_failed: int = 0
        self._bytes_sent: int = 0
        self._batches_sent: int = 0
        
        # Callbacks
        self._on_success: List[Callable] = []
        self._on_error: List[Callable] = []
        
        # Pending deliveries for exactly-once
        self._pending: Dict[str, MarketEvent] = {}
        
        logger.info("EventRouter initialized")
    
    async def initialize(self):
        """Initialize Kafka producer and create topics"""
        try:
            from confluent_kafka import Producer
            from confluent_kafka.admin import AdminClient, NewTopic
            
            # Producer config
            producer_config = {
                'bootstrap.servers': ','.join(self.config.bootstrap_servers),
                'client.id': self.config.client_id,
                'acks': self.config.acks,
                'retries': self.config.retries,
                'retry.backoff.ms': self.config.retry_backoff_ms,
                'max.in.flight.requests.per.connection': self.config.max_in_flight_requests,
                'enable.idempotence': self.config.enable_idempotence,
                'linger.ms': self.config.linger_ms,
                'batch.size': 16384,
                'buffer.memory': self.config.buffer_memory,
                'compression.type': self.config.compression_type.value,
                'delivery.timeout.ms': self.config.delivery_timeout_ms,
            }
            
            if self.config.transactional_id:
                producer_config['transactional.id'] = self.config.transactional_id
            
            self._producer = Producer(producer_config)
            
            # Admin client for topic management
            admin_config = {
                'bootstrap.servers': ','.join(self.config.bootstrap_servers),
            }
            self._admin_client = AdminClient(admin_config)
            
            # Create topics if they don't exist
            await self._ensure_topics()
            
            # Start batch flusher
            self._batch_task = asyncio.create_task(self._batch_flusher())
            
            logger.info("EventRouter initialized with Kafka producer")
            
        except ImportError:
            logger.warning("confluent-kafka not installed, using mock producer")
            self._producer = MockProducer()
    
    async def _ensure_topics(self):
        """Create topics if they don't exist"""
        if not self._admin_client:
            return
        try:
        
            from confluent_kafka.admin import NewTopic
            
            # Get existing topics
            metadata = self._admin_client.list_topics(timeout=10)
            existing = set(metadata.topics.keys())
            
            # Create missing topics
            new_topics = []
            for topic_name, topic_config in TOPIC_CONFIGS.items():
                if topic_name not in existing:
                    new_topics.append(NewTopic(
                        topic_name,
                        num_partitions=topic_config.partitions,
                        replication_factor=topic_config.replication_factor,
                        config={
                            'retention.ms': str(topic_config.retention_ms),
                            'cleanup.policy': topic_config.cleanup_policy,
                            'compression.type': topic_config.compression_type,
                            'min.insync.replicas': str(topic_config.min_insync_replicas),
                        }
                    ))
            
            if new_topics:
                futures = self._admin_client.create_topics(new_topics)
                for topic, future in futures.items():
                    try:
                        future.result()
                        logger.info(f"Created topic: {topic}")
                    except Exception as e:
                        logger.error(f"Failed to create topic {topic}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to ensure topics: {e}")
    
    async def route(self, event: MarketEvent):
        """
        Route a single event to appropriate topics.
        """
        topics = self.topic_resolver.resolve(event)
        
        for topic in topics:
            await self._add_to_batch(topic, event)
    
    async def route_batch(self, events: List[MarketEvent]):
        """
        Route a batch of events.
        """
        for event in events:
            await self.route(event)
    
    async def _add_to_batch(self, topic: str, event: MarketEvent):
        """Add event to batch for topic"""
        async with self._batch_lock:
            if topic not in self._batches:
                self._batches[topic] = []
            
            self._batches[topic].append(event)
            
            if len(self._batches[topic]) >= self.config.batch_size:
                await self._flush_topic(topic)
    
    async def _batch_flusher(self):
        """Periodic batch flusher"""
        while True:
            await asyncio.sleep(self.config.batch_timeout_ms / 1000)
            await self._flush_all()
    
    async def _flush_all(self):
        """Flush all batches"""
        async with self._batch_lock:
            for topic in list(self._batches.keys()):
                await self._flush_topic(topic)
    
    async def _flush_topic(self, topic: str):
        """Flush batch for a specific topic"""
        if topic not in self._batches or not self._batches[topic]:
            return
        
        events = self._batches[topic]
        self._batches[topic] = []
        
        # Create envelope
        envelope = EventEnvelope(
            batch_id=str(uuid.uuid4()),
            source_id=self.config.client_id,
            partition_key=events[0].symbol if events else '',
            events=events,
            created_ts=time.time_ns(),
            compressed=self.config.compression_type != CompressionType.NONE,
            compression_algo=self.config.compression_type.value
        )
        
        try:
            # Serialize
            # Use binary serialization
            value = envelope.to_bytes()
            key = envelope.partition_key.encode('utf-8')
            
            # Determine partition
            partition = PartitionStrategy.by_symbol(
                events[0],
                TOPIC_CONFIGS.get(topic, TopicConfig(name=topic)).partitions
            )
            
            # Send to Kafka
            self._producer.produce(
                topic=topic,
                key=key,
                value=value,
                partition=partition,
                callback=self._delivery_callback
            )
            
            self._producer.poll(0)  # Trigger callbacks
            
            self._events_routed += len(events)
            self._bytes_sent += len(value)
            self._batches_sent += 1
            
        except Exception as e:
            logger.error(f"Failed to send batch to {topic}: {e}")
            self._events_failed += len(events)
            
            for callback in self._on_error:
                try:
                    callback(events, e)
                except Exception:
                    pass
    
    def _delivery_callback(self, err, msg):
        """Kafka delivery callback"""
        if err:
            logger.error(f"Delivery failed: {err}")
            self._events_failed += 1
        else:
            # Success
            for callback in self._on_success:
                try:
                    callback(msg)
                except Exception:
                    pass
    
    async def flush(self):
        """Flush all pending messages"""
        await self._flush_all()
        if self._producer:
            self._producer.flush(timeout=30)
    
    async def close(self):
        """Close the router"""
        if self._batch_task:
            self._batch_task.cancel()
        
        await self.flush()
        
        if self._producer:
            self._producer.flush(timeout=10)
        
        logger.info("EventRouter closed")
    
    def on_success(self, callback: Callable):
        """Register success callback"""
        self._on_success.append(callback)
    
    def on_error(self, callback: Callable):
        """Register error callback"""
        self._on_error.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            'events_routed': self._events_routed,
            'events_failed': self._events_failed,
            'bytes_sent': self._bytes_sent,
            'batches_sent': self._batches_sent,
            'pending_batches': sum(len(b) for b in self._batches.values()),
            'topics': list(self._batches.keys()),
        }


class MockProducer:
    """Mock producer for testing without Kafka"""
    
    def __init__(self):
        self.messages: List[Dict] = []
        self._callback = None
    
    def produce(self, topic: str, key: bytes, value: bytes, partition: int = 0, callback=None):
        self.messages.append({
            'topic': topic,
            'key': key,
            'value': value,
            'partition': partition,
            'timestamp': time.time_ns()
        })
        self._callback = callback
    
    def poll(self, timeout: float = 0):
        if self._callback and self.messages:
            self._callback(None, self.messages[-1])
    


# Consumer for reading from topics
class EventConsumer:
    """
    Consumes events from Kafka/Redpanda topics.
    Used by replay engine and downstream processors.
    """
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        group_id: str,
        topics: List[str],
        auto_offset_reset: str = 'earliest'
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.auto_offset_reset = auto_offset_reset
        
        self._consumer = None
        self._running = False
    
    async def initialize(self):
        """Initialize consumer"""
        try:
            from confluent_kafka import Consumer
            
            config = {
                'bootstrap.servers': ','.join(self.bootstrap_servers),
                'group.id': self.group_id,
                'auto.offset.reset': self.auto_offset_reset,
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 5000,
            }
            
            self._consumer = Consumer(config)
            self._consumer.subscribe(self.topics)
            
            logger.info(f"Consumer initialized for topics: {self.topics}")
            
        except ImportError:
            logger.warning("confluent-kafka not installed")
            self._consumer = MockConsumer()
    
    async def consume(self, timeout: float = 1.0) -> Optional[EventEnvelope]:
        """Consume next message"""
        if not self._consumer:
            return None
        
        msg = self._consumer.poll(timeout)
        
        if msg is None:
            return None
        
        if msg.error():
            logger.error(f"Consumer error: {msg.error()}")
            return None
        try:
        
            envelope = EventEnvelope.from_bytes(msg.value())
            return envelope
        except Exception as e:
            logger.error(f"Failed to deserialize message: {e}")
            return None
    
    async def consume_batch(
        self,
        max_messages: int = 100,
        timeout: float = 1.0
    ) -> List[EventEnvelope]:
        """Consume batch of messages"""
        envelopes = []
        deadline = time.time() + timeout
        
        while len(envelopes) < max_messages and time.time() < deadline:
            envelope = await self.consume(timeout=0.1)
            if envelope:
                envelopes.append(envelope)
        
        return envelopes
    
    def commit(self):
        """Commit offsets"""
        if self._consumer:
            self._consumer.commit()
    
    async def close(self):
        """Close consumer"""
        if self._consumer:
            self._consumer.close()


class MockConsumer:
    """Mock consumer for testing"""
    
    def __init__(self):
        pass
    
    def subscribe(self, topics):
        pass
    
    def commit(self):
        pass
    
    def close(self):
        pass
