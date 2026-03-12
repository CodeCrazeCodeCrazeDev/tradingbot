"""
AlphaAlgo Event Pipeline
=========================
Unified orchestrator for the real-time event pipeline.
Integrates all components into a consistent, replayable, fault-tolerant, scalable system.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    Set, TypeVar
)
from pathlib import Path

from .events import (
    Event, EventType, EventPriority, EventMetadata,
    MarketDataEvent, SignalEvent, OrderEvent, ExecutionEvent,
    RiskEvent, SystemEvent, create_event
)
from .event_store import EventStore, EventStoreConfig, StorageBackend, EventQuery
from .event_bus import EventBus, EventBusConfig, DeliveryGuarantee, Subscription
from .event_producer import (
    EventProducer, MarketDataProducer, SignalProducer,
    OrderProducer, RiskProducer, ProducerConfig
)
from .event_consumer import (
    EventConsumer, ConsumerConfig, ConsumerGroup, RetryPolicy
)
from .event_replay import EventReplay, ReplayConfig, ReplayMode
from .consistency import (
    IdempotencyGuard, TransactionManager, CausalityTracker, SequenceValidator
)
from .fault_tolerance import (
    CircuitBreaker, CircuitBreakerConfig, RetryHandler, RetryConfig,
    Bulkhead, BulkheadConfig, RateLimiter, HealthMonitor, HealthCheck, HealthStatus
)
from .scalability import (
    Partitioner, PartitionConfig, ShardManager, ShardManagerConfig,
    LoadBalancer, LoadBalancerStrategy, ClusterCoordinator, NodeInfo
)

logger = logging.getLogger(__name__)


class PipelineState(Enum):
    """Pipeline states"""
    CREATED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class PipelineConfig:
    """Configuration for event pipeline"""
    # Identity
    pipeline_id: str = ""
    node_id: str = ""
    
    # Storage
    storage_backend: StorageBackend = StorageBackend.SQLITE
    data_dir: Path = field(default_factory=lambda: Path("pipeline_data"))
    
    # Event Bus
    max_queue_size: int = 10000
    num_workers: int = 4
    
    # Delivery
    default_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    
    # Retry
    max_retries: int = 3
    retry_delay_ms: int = 1000
    
    # Partitioning
    num_partitions: int = 12
    
    # Sharding
    num_shards: int = 4
    
    # Rate limiting
    max_events_per_second: int = 10000
    
    # Health
    health_check_interval_seconds: float = 10.0
    
    # Replay
    enable_replay: bool = True
    
    # Clustering
    enable_clustering: bool = False


@dataclass
class PipelineStage:
    """Represents a processing stage in the pipeline"""
    name: str
    handler: Callable[[Event], Awaitable[Optional[Event]]]
    input_types: List[EventType] = field(default_factory=list)
    output_types: List[EventType] = field(default_factory=list)
    enabled: bool = True
    
    # Metrics
    events_processed: int = 0
    events_failed: int = 0
    avg_latency_ms: float = 0


@dataclass
class PipelineMetrics:
    """Pipeline metrics"""
    events_received: int = 0
    events_processed: int = 0
    events_failed: int = 0
    events_replayed: int = 0
    
    # Latency
    avg_latency_ms: float = 0
    p99_latency_ms: float = 0
    
    # Throughput
    events_per_second: float = 0
    
    # Health
    health_status: str = "UNKNOWN"
    
    # Uptime
    started_at: float = 0
    uptime_seconds: float = 0


class EventPipeline:
    """
    Unified event pipeline orchestrator.
    
    Provides:
    - Consistent event ordering and delivery
    - Replayable event history
    - Fault-tolerant processing
    - Horizontal scalability
    """
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        
        if not self.config.pipeline_id:
            self.config.pipeline_id = str(uuid.uuid4())[:8]
        if not self.config.node_id:
            self.config.node_id = f"node-{uuid.uuid4().hex[:8]}"
        
        # State
        self.state = PipelineState.CREATED
        self._started_at: float = 0
        
        # Core components
        self.event_store: Optional[EventStore] = None
        self.event_bus: Optional[EventBus] = None
        
        # Producers
        self.producers: Dict[str, EventProducer] = {}
        
        # Consumers
        self.consumers: Dict[str, EventConsumer] = {}
        self.consumer_groups: Dict[str, ConsumerGroup] = {}
        
        # Processing stages
        self._stages: List[PipelineStage] = []
        
        # Consistency
        self.idempotency_guard = IdempotencyGuard()
        self.transaction_manager = TransactionManager()
        self.causality_tracker = CausalityTracker()
        self.sequence_validator = SequenceValidator()
        
        # Fault tolerance
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handler = RetryHandler(RetryConfig(
            max_retries=self.config.max_retries,
            initial_delay_ms=self.config.retry_delay_ms,
        ))
        self.bulkhead = Bulkhead("pipeline", BulkheadConfig(
            max_concurrent=self.config.num_workers * 10,
        ))
        self.rate_limiter = RateLimiter(self.config.max_events_per_second)
        self.health_monitor = HealthMonitor(self.config.health_check_interval_seconds)
        
        # Scalability
        self.partitioner = Partitioner(PartitionConfig(
            num_partitions=self.config.num_partitions,
        ))
        self.shard_manager = ShardManager(ShardManagerConfig(
            num_shards=self.config.num_shards,
        ))
        self.load_balancer = LoadBalancer(LoadBalancerStrategy.ROUND_ROBIN)
        self.cluster_coordinator: Optional[ClusterCoordinator] = None
        
        # Replay
        self.replay_engine: Optional[EventReplay] = None
        
        # Metrics
        self.metrics = PipelineMetrics()
        self._latency_samples: List[float] = []
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        
        logger.info(f"EventPipeline {self.config.pipeline_id} created")
    
    async def initialize(self):
        """Initialize all pipeline components"""
        logger.info("Initializing event pipeline...")
        
        # Create data directory
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize event store
        store_config = EventStoreConfig(
            backend=self.config.storage_backend,
            data_dir=self.config.data_dir,
        )
        self.event_store = EventStore(store_config)
        await self.event_store.start()
        
        # Initialize event bus
        bus_config = EventBusConfig(
            default_guarantee=self.config.default_guarantee,
            max_queue_size=self.config.max_queue_size,
            num_workers=self.config.num_workers,
            max_retries=self.config.max_retries,
            retry_delay_ms=self.config.retry_delay_ms,
        )
        self.event_bus = EventBus(bus_config)
        
        # Initialize producers
        await self._initialize_producers()
        
        # Initialize consistency components
        await self.idempotency_guard.start()
        
        # Register health checks
        self._register_health_checks()
        
        # Initialize clustering if enabled
        if self.config.enable_clustering:
            self.cluster_coordinator = ClusterCoordinator(self.config.node_id)
        
        logger.info("Event pipeline initialized")
    
    async def _initialize_producers(self):
        """Initialize default producers"""
        producer_config = ProducerConfig(
            source_name=self.config.pipeline_id,
            max_events_per_second=self.config.max_events_per_second,
        )
        
        self.producers['market_data'] = MarketDataProducer(
            self.event_bus, producer_config
        )
        self.producers['signals'] = SignalProducer(
            self.event_bus, producer_config
        )
        self.producers['orders'] = OrderProducer(
            self.event_bus, producer_config
        )
        self.producers['risk'] = RiskProducer(
            self.event_bus, producer_config
        )
    
    def _register_health_checks(self):
        """Register health checks for all components"""
        
        async def check_event_store() -> HealthCheck:
            try:
                # Simple check - try to query
                await self.event_store.query(EventQuery(limit=1))
                return HealthCheck(
                    name="event_store",
                    status=HealthStatus.HEALTHY,
                    message="Event store operational",
                )
            except Exception as e:
                return HealthCheck(
                    name="event_store",
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                )
        
        async def check_event_bus() -> HealthCheck:
            metrics = self.event_bus.get_metrics() if self.event_bus else {}
            dlq_size = metrics.get('dlq_size', 0)
            
            if dlq_size > 1000:
                return HealthCheck(
                    name="event_bus",
                    status=HealthStatus.DEGRADED,
                    message=f"DLQ size: {dlq_size}",
                )
            return HealthCheck(
                name="event_bus",
                status=HealthStatus.HEALTHY,
                message="Event bus operational",
            )
        
        async def check_rate_limiter() -> HealthCheck:
            state = self.rate_limiter.get_state()
            rejected = state['metrics']['rejected']
            
            if rejected > 100:
                return HealthCheck(
                    name="rate_limiter",
                    status=HealthStatus.DEGRADED,
                    message=f"Rejected: {rejected}",
                )
            return HealthCheck(
                name="rate_limiter",
                status=HealthStatus.HEALTHY,
                message="Rate limiter operational",
            )
        
        self.health_monitor.register_check("event_store", check_event_store)
        self.health_monitor.register_check("event_bus", check_event_bus)
        self.health_monitor.register_check("rate_limiter", check_rate_limiter)
    
    async def start(self):
        """Start the event pipeline"""
        if self.state == PipelineState.RUNNING:
            return
        
        self.state = PipelineState.STARTING
        self._started_at = time.time()
        self.metrics.started_at = self._started_at
        
        try:
            # Initialize if needed
            if not self.event_store:
                await self.initialize()
            
            # Start event bus
            await self.event_bus.start()
            
            # Start producers
            for producer in self.producers.values():
                await producer.start()
            
            # Start consumers
            for consumer in self.consumers.values():
                await consumer.start()
            
            for group in self.consumer_groups.values():
                await group.start()
            
            # Start health monitor
            await self.health_monitor.start()
            
            # Start clustering
            if self.cluster_coordinator:
                await self.cluster_coordinator.start()
                # Register self
                await self.cluster_coordinator.register_member(NodeInfo(
                    node_id=self.config.node_id,
                    address="localhost",
                    port=8080,
                ))
            
            # Start background tasks
            self._tasks.append(asyncio.create_task(self._metrics_loop()))
            
            self.state = PipelineState.RUNNING
            logger.info(f"Event pipeline {self.config.pipeline_id} started")
            
            # Emit system event
            await self._emit_system_event("STARTED", "Pipeline started successfully")
            
        except Exception as e:
            self.state = PipelineState.ERROR
            logger.error(f"Failed to start pipeline: {e}")
            raise
    
    async def stop(self):
        """Stop the event pipeline"""
        if self.state == PipelineState.STOPPED:
            return
        
        self.state = PipelineState.STOPPING
        
        try:
            # Emit system event
            await self._emit_system_event("STOPPING", "Pipeline stopping")
            
            # Cancel background tasks
            for task in self._tasks:
                task.cancel()
            
            # Stop consumers
            for consumer in self.consumers.values():
                await consumer.stop()
            
            for group in self.consumer_groups.values():
                await group.stop()
            
            # Stop producers
            for producer in self.producers.values():
                await producer.stop()
            
            # Stop event bus
            if self.event_bus:
                await self.event_bus.stop()
            
            # Stop event store
            if self.event_store:
                await self.event_store.stop()
            
            # Stop health monitor
            await self.health_monitor.stop()
            
            # Stop idempotency guard
            await self.idempotency_guard.stop()
            
            # Stop clustering
            if self.cluster_coordinator:
                await self.cluster_coordinator.stop()
            
            self.state = PipelineState.STOPPED
            logger.info(f"Event pipeline {self.config.pipeline_id} stopped")
            
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
            self.state = PipelineState.ERROR
    
    async def _metrics_loop(self):
        """Background metrics collection"""
        last_count = 0
        last_time = time.time()
        
        while self.state == PipelineState.RUNNING:
            try:
                await asyncio.sleep(1.0)
                
                # Calculate throughput
                now = time.time()
                elapsed = now - last_time
                if elapsed > 0:
                    current_count = self.metrics.events_processed
                    self.metrics.events_per_second = (
                        (current_count - last_count) / elapsed
                    )
                    last_count = current_count
                    last_time = now
                
                # Update uptime
                self.metrics.uptime_seconds = now - self._started_at
                
                # Update health status
                self.metrics.health_status = self.health_monitor.get_overall_status().name
                
                # Calculate latency percentiles
                if self._latency_samples:
                    sorted_samples = sorted(self._latency_samples)
                    self.metrics.avg_latency_ms = sum(sorted_samples) / len(sorted_samples)
                    p99_idx = int(len(sorted_samples) * 0.99)
                    self.metrics.p99_latency_ms = sorted_samples[min(p99_idx, len(sorted_samples) - 1)]
                    
                    # Keep only recent samples
                    if len(self._latency_samples) > 10000:
                        self._latency_samples = self._latency_samples[-5000:]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
    
    async def _emit_system_event(self, event_type: str, message: str):
        """Emit a system event"""
        event = create_event(
            event_type=EventType.SYSTEM_STARTED if event_type == "STARTED" else EventType.SYSTEM_STOPPED,
            source=self.config.pipeline_id,
            partition_key="SYSTEM",
            system_type=event_type,
            component="pipeline",
            status="OK",
            message=message,
        )
        await self.publish("system", event)
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    async def publish(
        self,
        topic: str,
        event: Event,
        guarantee: DeliveryGuarantee = None
    ) -> bool:
        """
        Publish event to the pipeline.
        
        Args:
            topic: Topic name
            event: Event to publish
            guarantee: Delivery guarantee
            
        Returns:
            True if published successfully
        """
        if self.state != PipelineState.RUNNING:
            logger.warning(f"Cannot publish in state {self.state}")
            return False
        
        start_time = time.time()
        
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Idempotency check
            is_new, _ = await self.idempotency_guard.check_and_set(
                event.metadata.idempotency_key
            )
            if not is_new:
                logger.debug(f"Duplicate event: {event.event_id}")
                return True  # Already processed
            
            # Partition
            partition = self.partitioner.partition(event)
            
            # Sequence validation
            valid, reason = await self.sequence_validator.validate(event)
            if not valid:
                logger.warning(f"Sequence validation failed: {reason}")
            
            # Causality tracking
            await self.causality_tracker.register_event(event)
            
            # Store event
            await self.event_store.append(event)
            
            # Publish to bus
            success = await self.event_bus.publish(topic, event, guarantee)
            
            if success:
                self.metrics.events_received += 1
                self.metrics.events_processed += 1
                
                # Track latency
                latency_ms = (time.time() - start_time) * 1000
                self._latency_samples.append(latency_ms)
            
            return success
            
        except Exception as e:
            self.metrics.events_failed += 1
            logger.error(f"Failed to publish event: {e}")
            return False
    
    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Event], Awaitable[None]],
        consumer_id: str = None,
        group_id: str = None,
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            topics: Topics to subscribe to
            handler: Event handler
            consumer_id: Consumer identifier
            group_id: Consumer group ID (for load balancing)
            
        Returns:
            Subscription/consumer ID
        """
        if group_id:
            # Create consumer group
            if group_id not in self.consumer_groups:
                config = ConsumerConfig(
                    group_id=group_id,
                    topics=topics,
                    retry_policy=RetryPolicy(
                        max_retries=self.config.max_retries,
                    ),
                )
                group = ConsumerGroup(
                    group_id=group_id,
                    event_bus=self.event_bus,
                    handler=handler,
                    config=config,
                )
                self.consumer_groups[group_id] = group
                
                if self.state == PipelineState.RUNNING:
                    await group.start()
            
            return group_id
        else:
            # Create individual consumer
            consumer_id = consumer_id or str(uuid.uuid4())[:8]
            
            config = ConsumerConfig(
                consumer_id=consumer_id,
                topics=topics,
                retry_policy=RetryPolicy(
                    max_retries=self.config.max_retries,
                ),
            )
            consumer = EventConsumer(
                event_bus=self.event_bus,
                handler=handler,
                config=config,
            )
            self.consumers[consumer_id] = consumer
            
            if self.state == PipelineState.RUNNING:
                await consumer.start()
            
            return consumer_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        if subscription_id in self.consumers:
            consumer = self.consumers.pop(subscription_id)
            await consumer.stop()
            return True
        
        if subscription_id in self.consumer_groups:
            group = self.consumer_groups.pop(subscription_id)
            await group.stop()
            return True
        
        return False
    
    def add_stage(self, stage: PipelineStage):
        """Add a processing stage to the pipeline"""
        self._stages.append(stage)
        logger.info(f"Added pipeline stage: {stage.name}")
    
    async def process_through_stages(self, event: Event) -> Optional[Event]:
        """Process event through all pipeline stages"""
        current_event = event
        
        for stage in self._stages:
            if not stage.enabled:
                continue
            
            # Check if stage handles this event type
            if stage.input_types and event.metadata.event_type not in stage.input_types:
                continue
            
            start_time = time.time()
            
            try:
                result = await stage.handler(current_event)
                
                stage.events_processed += 1
                latency = (time.time() - start_time) * 1000
                stage.avg_latency_ms = (stage.avg_latency_ms * 0.9 + latency * 0.1)
                
                if result is None:
                    return None  # Event filtered out
                
                current_event = result
                
            except Exception as e:
                stage.events_failed += 1
                logger.error(f"Stage {stage.name} failed: {e}")
                raise
        
        return current_event
    
    async def replay(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        event_types: List[EventType] = None,
        handler: Callable[[Event], Awaitable[None]] = None,
        mode: ReplayMode = ReplayMode.FAST,
    ) -> int:
        """
        Replay historical events.
        
        Args:
            start_time: Start of replay window
            end_time: End of replay window
            event_types: Filter by event types
            handler: Event handler
            mode: Replay mode
            
        Returns:
            Number of events replayed
        """
        if not self.config.enable_replay:
            logger.warning("Replay is disabled")
            return 0
        
        config = ReplayConfig(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types or [],
            mode=mode,
            on_event=handler,
        )
        
        self.replay_engine = EventReplay(self.event_store, config)
        
        count = await self.replay_engine.load()
        await self.replay_engine.play()
        
        self.metrics.events_replayed += count
        
        return count
    
    def get_producer(self, name: str) -> Optional[EventProducer]:
        """Get a producer by name"""
        return self.producers.get(name)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline metrics"""
        return {
            'pipeline_id': self.config.pipeline_id,
            'node_id': self.config.node_id,
            'state': self.state.name,
            'metrics': {
                'events_received': self.metrics.events_received,
                'events_processed': self.metrics.events_processed,
                'events_failed': self.metrics.events_failed,
                'events_replayed': self.metrics.events_replayed,
                'avg_latency_ms': self.metrics.avg_latency_ms,
                'p99_latency_ms': self.metrics.p99_latency_ms,
                'events_per_second': self.metrics.events_per_second,
                'uptime_seconds': self.metrics.uptime_seconds,
            },
            'health': self.health_monitor.get_summary(),
            'event_store': self.event_store.get_metrics() if self.event_store else {},
            'event_bus': self.event_bus.get_metrics() if self.event_bus else {},
            'partitioner': self.partitioner.get_partition_stats(),
            'shards': self.shard_manager.get_stats(),
            'stages': [
                {
                    'name': s.name,
                    'enabled': s.enabled,
                    'processed': s.events_processed,
                    'failed': s.events_failed,
                    'avg_latency_ms': s.avg_latency_ms,
                }
                for s in self._stages
            ],
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return self.health_monitor.get_summary()


# ============================================================================
# Factory Functions
# ============================================================================

def create_pipeline(config: PipelineConfig = None) -> EventPipeline:
    """Create an event pipeline instance"""
    return EventPipeline(config)


async def quick_start(
    data_dir: str = "pipeline_data",
    storage: StorageBackend = StorageBackend.SQLITE,
) -> EventPipeline:
    """
    Quick start an event pipeline with sensible defaults.
    
    Args:
        data_dir: Data directory path
        storage: Storage backend
        
    Returns:
        Running event pipeline
    """
    config = PipelineConfig(
        data_dir=Path(data_dir),
        storage_backend=storage,
    )
    
    pipeline = EventPipeline(config)
    await pipeline.initialize()
    await pipeline.start()
    
    return pipeline
