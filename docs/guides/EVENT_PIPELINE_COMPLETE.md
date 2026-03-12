# AlphaAlgo Real-Time Event Pipeline

## Overview

A **consistent, replayable, fault-tolerant, and scalable** event-driven architecture for the trading bot.

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Consistency** | All events are ordered, versioned, and causally linked |
| **Replayability** | Complete event history enables deterministic replay |
| **Fault-Tolerance** | Dead letter queues, retries, circuit breakers |
| **Scalability** | Partitioning, sharding, horizontal scaling |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVENT PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   PRODUCERS  │───▶│   EVENT BUS  │───▶│  CONSUMERS   │       │
│  │              │    │              │    │              │       │
│  │ MarketData   │    │ Pub/Sub      │    │ Handlers     │       │
│  │ Signals      │    │ Routing      │    │ Groups       │       │
│  │ Orders       │    │ Delivery     │    │ DLQ          │       │
│  │ Risk         │    │ Guarantees   │    │ Retries      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     EVENT STORE                           │   │
│  │  Append-only │ Snapshots │ Queries │ Replay               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ CONSISTENCY  │    │FAULT TOLERANT│    │ SCALABILITY  │       │
│  │              │    │              │    │              │       │
│  │ Idempotency  │    │ CircuitBreak │    │ Partitioner  │       │
│  │ Transactions │    │ Retry        │    │ ShardManager │       │
│  │ Causality    │    │ Bulkhead     │    │ LoadBalancer │       │
│  │ Sequencing   │    │ RateLimiter  │    │ Cluster      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Events (`events.py`)
Immutable event types with versioning and causality tracking.

```python
from trading_bot.event_pipeline import create_event, EventType, EventPriority

# Create a market data event
event = create_event(
    event_type=EventType.MARKET_DATA,
    source="binance",
    partition_key="BTCUSDT",
    symbol="BTCUSDT",
    bid=50000.0,
    ask=50005.0,
)
```

**Event Types:**
- `MARKET_DATA`, `TRADE`, `QUOTE`, `BAR`, `TICK`
- `SIGNAL_GENERATED`, `SIGNAL_VALIDATED`, `SIGNAL_EXPIRED`
- `ORDER_CREATED`, `ORDER_FILLED`, `ORDER_CANCELLED`
- `EXECUTION_STARTED`, `EXECUTION_COMPLETED`, `FILL_RECEIVED`
- `RISK_LIMIT_BREACH`, `RISK_WARNING`, `DRAWDOWN_ALERT`
- `SYSTEM_STARTED`, `SYSTEM_STOPPED`, `HEALTH_CHECK`

### 2. Event Store (`event_store.py`)
Append-only storage with snapshots and queries.

```python
from trading_bot.event_pipeline import EventStore, EventStoreConfig, StorageBackend

config = EventStoreConfig(
    backend=StorageBackend.SQLITE,
    data_dir=Path("event_data"),
    snapshot_interval=1000,
)

store = EventStore(config)
await store.start()

# Append event
sequence = await store.append(event)

# Query events
events = await store.query(EventQuery(
    event_types=[EventType.MARKET_DATA],
    partition_keys=["BTCUSDT"],
    start_time_ns=start_ns,
    end_time_ns=end_ns,
))
```

**Storage Backends:**
- `MEMORY` - In-memory (testing)
- `SQLITE` - SQLite (single node)
- `POSTGRES` - PostgreSQL (production)
- `KAFKA` - Kafka as event store
- `CLICKHOUSE` - ClickHouse (analytics)

### 3. Event Bus (`event_bus.py`)
Pub/sub messaging with delivery guarantees.

```python
from trading_bot.event_pipeline import EventBus, DeliveryGuarantee

bus = EventBus()
await bus.start()

# Subscribe
subscription_id = bus.subscribe(
    topics=["market_data"],
    handler=my_handler,
    guarantee=DeliveryGuarantee.EXACTLY_ONCE,
)

# Publish
await bus.publish("market_data", event)
```

**Delivery Guarantees:**
- `AT_MOST_ONCE` - Fire and forget (fastest)
- `AT_LEAST_ONCE` - Retry until ack (default)
- `EXACTLY_ONCE` - Idempotent delivery (slowest)

### 4. Producers (`event_producer.py`)
Event generation from various sources.

```python
from trading_bot.event_pipeline import MarketDataProducer, SignalProducer

# Market data producer
market_producer = MarketDataProducer(event_bus)
await market_producer.produce_tick(
    symbol="BTCUSDT",
    bid=50000.0,
    ask=50005.0,
)

# Signal producer
signal_producer = SignalProducer(event_bus)
await signal_producer.produce_signal(
    symbol="BTCUSDT",
    direction="LONG",
    confidence=0.85,
)
```

### 5. Consumers (`event_consumer.py`)
Fault-tolerant event processing.

```python
from trading_bot.event_pipeline import EventConsumer, ConsumerGroup, RetryPolicy

# Individual consumer
consumer = EventConsumer(
    event_bus=bus,
    handler=my_handler,
    config=ConsumerConfig(
        topics=["signals"],
        retry_policy=RetryPolicy(max_retries=3),
    ),
)
await consumer.start()

# Consumer group (for scaling)
group = ConsumerGroup(
    group_id="signal-processors",
    event_bus=bus,
    handler=my_handler,
)
await group.start(num_consumers=4)
```

### 6. Replay (`event_replay.py`)
Deterministic replay for backtesting and recovery.

```python
from trading_bot.event_pipeline import EventReplay, ReplayMode

replay = EventReplay(event_store, ReplayConfig(
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    event_types=[EventType.MARKET_DATA],
    mode=ReplayMode.TIME_SCALED,
    speed_multiplier=10.0,  # 10x speed
    on_event=my_handler,
))

await replay.load()
await replay.play()
```

**Replay Modes:**
- `REALTIME` - Original speed
- `FAST` - As fast as possible
- `STEPPED` - Manual stepping
- `TIME_SCALED` - Configurable speed

### 7. Consistency (`consistency.py`)
Exactly-once semantics and data integrity.

```python
from trading_bot.event_pipeline import (
    IdempotencyGuard,
    TransactionManager,
    CausalityTracker,
    SequenceValidator,
)

# Idempotency
guard = IdempotencyGuard()
is_new, result = await guard.check_and_set(event.idempotency_key)

# Transactions
tx_manager = TransactionManager()
tx_id = await tx_manager.begin()
await tx_manager.add_event(tx_id, event)
await tx_manager.commit(tx_id)

# Causality tracking
tracker = CausalityTracker()
await tracker.register_event(event)
can_process = await tracker.can_process(event)

# Sequence validation
validator = SequenceValidator()
valid, reason = await validator.validate(event)
```

### 8. Fault Tolerance (`fault_tolerance.py`)
Resilience under failure conditions.

```python
from trading_bot.event_pipeline import (
    CircuitBreaker,
    RetryHandler,
    Bulkhead,
    RateLimiter,
    HealthMonitor,
)

# Circuit breaker
breaker = CircuitBreaker("external-api")
result = await breaker.call(external_api_call)

# Retry handler
retry = RetryHandler(RetryConfig(max_retries=3))
result = await retry.execute(flaky_operation)

# Bulkhead (isolation)
bulkhead = Bulkhead("order-processing", BulkheadConfig(max_concurrent=10))
result = await bulkhead.execute(process_order)

# Rate limiter
limiter = RateLimiter(rate=1000)  # 1000/sec
await limiter.acquire()

# Health monitoring
monitor = HealthMonitor()
monitor.register_check("database", db_health_check)
await monitor.start()
```

### 9. Scalability (`scalability.py`)
Horizontal scaling capabilities.

```python
from trading_bot.event_pipeline import (
    Partitioner,
    ShardManager,
    LoadBalancer,
    ClusterCoordinator,
)

# Partitioning
partitioner = Partitioner(PartitionConfig(num_partitions=12))
partition = partitioner.partition(event)

# Sharding
shard_manager = ShardManager(ShardManagerConfig(num_shards=4))
shard = await shard_manager.get_shard_for_partition(partition)

# Load balancing
balancer = LoadBalancer(LoadBalancerStrategy.LEAST_CONNECTIONS)
node = await balancer.get_node()

# Cluster coordination
coordinator = ClusterCoordinator(node_id="node-1")
await coordinator.start()
is_leader = coordinator.is_leader()
```

## Quick Start

```python
from trading_bot.event_pipeline import quick_start, EventType, create_event

async def main():
    # Start pipeline with defaults
    pipeline = await quick_start()
    
    # Subscribe to events
    async def handle_signal(event):
        print(f"Signal: {event.symbol} {event.direction}")
    
    await pipeline.subscribe(["signals"], handle_signal)
    
    # Publish events
    event = create_event(
        event_type=EventType.SIGNAL_GENERATED,
        source="strategy",
        partition_key="BTCUSDT",
        symbol="BTCUSDT",
        direction="LONG",
        confidence=0.85,
    )
    await pipeline.publish("signals", event)
    
    # Get metrics
    metrics = pipeline.get_metrics()
    print(f"Events processed: {metrics['metrics']['events_processed']}")
    
    # Replay historical events
    await pipeline.replay(
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 31),
        handler=handle_signal,
    )
    
    await pipeline.stop()

asyncio.run(main())
```

## Processing Stages

Add multi-stage processing pipelines:

```python
from trading_bot.event_pipeline import PipelineStage

async def validation_stage(event):
    if not event.symbol:
        return None  # Filter out
    return event

async def enrichment_stage(event):
    # Add additional data
    return event

pipeline.add_stage(PipelineStage(
    name="validation",
    handler=validation_stage,
    input_types=[EventType.MARKET_DATA],
))

pipeline.add_stage(PipelineStage(
    name="enrichment",
    handler=enrichment_stage,
))
```

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `events.py` | ~650 | Event definitions and factory |
| `event_store.py` | ~550 | Append-only storage |
| `event_bus.py` | ~500 | Pub/sub messaging |
| `event_producer.py` | ~450 | Event producers |
| `event_consumer.py` | ~400 | Fault-tolerant consumers |
| `event_replay.py` | ~350 | Deterministic replay |
| `consistency.py` | ~450 | Consistency guarantees |
| `fault_tolerance.py` | ~500 | Resilience patterns |
| `scalability.py` | ~550 | Horizontal scaling |
| `pipeline.py` | ~600 | Unified orchestrator |
| `__init__.py` | ~350 | Module exports |
| **Total** | **~5,350** | Production-ready code |

## Demo

Run the demo to see all features:

```bash
python examples/event_pipeline_demo.py
```

## Integration with Trading Bot

The event pipeline integrates with all trading bot components:

```python
from trading_bot.event_pipeline import EventPipeline, PipelineConfig

# Create pipeline
pipeline = EventPipeline(PipelineConfig(
    storage_backend=StorageBackend.SQLITE,
    enable_clustering=True,
))

# Connect to existing systems
await pipeline.subscribe(["market_data"], market_analyzer.process)
await pipeline.subscribe(["signals"], signal_validator.validate)
await pipeline.subscribe(["orders"], order_manager.handle)
await pipeline.subscribe(["risk"], risk_manager.check)

# Use producers from existing code
market_producer = pipeline.get_producer("market_data")
await market_producer.produce_tick(symbol, bid, ask)
```

## Performance Targets

- **Throughput**: 100,000+ events/second
- **Latency**: <1ms p99 for in-memory
- **Durability**: Zero data loss with SQLite/Postgres
- **Scalability**: Linear with partition count

## Status

✅ **100% COMPLETE** - Production-ready real-time event pipeline

All components implemented:
- [x] Immutable events with versioning
- [x] Append-only event store with snapshots
- [x] Pub/sub with delivery guarantees
- [x] Fault-tolerant consumers with DLQ
- [x] Deterministic replay
- [x] Consistency guarantees (exactly-once)
- [x] Circuit breakers and retries
- [x] Partitioning and sharding
- [x] Load balancing
- [x] Cluster coordination
- [x] Health monitoring
- [x] Comprehensive demo
