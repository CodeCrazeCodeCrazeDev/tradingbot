"""
AlphaAlgo Event Pipeline Demo
==============================
Demonstrates the real-time event pipeline with:
- Consistent event ordering
- Replayable event history
- Fault-tolerant processing
- Horizontal scalability
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.event_pipeline import (
    EventPipeline,
    PipelineConfig,
    PipelineStage,
    EventType,
    EventPriority,
    create_event,
    StorageBackend,
    DeliveryGuarantee,
    ReplayMode,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def market_data_handler(event):
    """Handle market data events"""
    logger.info(f"📊 Market Data: {event.symbol} - Bid: {event.bid}, Ask: {event.ask}")


async def signal_handler(event):
    """Handle signal events"""
    logger.info(
        f"🎯 Signal: {event.symbol} - {event.direction} "
        f"(confidence: {event.confidence:.2%})"
    )


async def order_handler(event):
    """Handle order events"""
    logger.info(
        f"📝 Order: {event.order_id} - {event.side} {event.quantity} {event.symbol} "
        f"@ {event.price}"
    )


async def risk_handler(event):
    """Handle risk events"""
    logger.warning(f"⚠️ Risk Alert: {event.message} (severity: {event.severity})")


async def demo_basic_pipeline():
    """Demo 1: Basic pipeline usage"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Event Pipeline")
    print("="*60 + "\n")
    
    # Create pipeline with configuration
    config = PipelineConfig(
        pipeline_id="demo-pipeline",
        storage_backend=StorageBackend.MEMORY,  # Use memory for demo
        data_dir=Path("demo_pipeline_data"),
        num_workers=2,
        max_events_per_second=1000,
    )
    
    pipeline = EventPipeline(config)
    
    try:
        # Initialize and start
        await pipeline.initialize()
        await pipeline.start()
        
        print("✅ Pipeline started successfully")
        print(f"   Pipeline ID: {pipeline.config.pipeline_id}")
        print(f"   Node ID: {pipeline.config.node_id}")
        
        # Subscribe to events
        await pipeline.subscribe(["market_data"], market_data_handler)
        await pipeline.subscribe(["signals"], signal_handler)
        await pipeline.subscribe(["orders"], order_handler)
        await pipeline.subscribe(["risk"], risk_handler)
        
        print("\n📡 Subscribed to all event topics")
        
        # Publish some events
        print("\n📤 Publishing events...")
        
        # Market data events
        for i in range(5):
            event = create_event(
                event_type=EventType.MARKET_DATA,
                source="demo",
                partition_key="BTCUSDT",
                symbol="BTCUSDT",
                exchange="binance",
                bid=50000.0 + i * 10,
                ask=50005.0 + i * 10,
                last=50002.5 + i * 10,
                volume=100.0,
            )
            await pipeline.publish("market_data", event)
            await asyncio.sleep(0.1)
        
        # Signal event
        signal = create_event(
            event_type=EventType.SIGNAL_GENERATED,
            source="demo",
            partition_key="BTCUSDT",
            priority=EventPriority.HIGH,
            signal_id="SIG-001",
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.85,
            entry_price=50050.0,
            stop_loss=49500.0,
            take_profit=51000.0,
            strategy_name="momentum",
            reasoning="Strong upward momentum detected",
        )
        await pipeline.publish("signals", signal)
        
        # Order event
        order = create_event(
            event_type=EventType.ORDER_CREATED,
            source="demo",
            partition_key="BTCUSDT",
            order_id="ORD-001",
            client_order_id="CLT-001",
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.1,
            price=50050.0,
            status="NEW",
            signal_id="SIG-001",
        )
        await pipeline.publish("orders", order)
        
        # Risk event
        risk = create_event(
            event_type=EventType.RISK_WARNING,
            source="demo",
            partition_key="PORTFOLIO",
            priority=EventPriority.HIGH,
            risk_type="WARNING",
            severity="MEDIUM",
            message="Portfolio exposure approaching limit",
            current_value=0.75,
            threshold_value=0.80,
        )
        await pipeline.publish("risk", risk)
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Show metrics
        metrics = pipeline.get_metrics()
        print("\n📊 Pipeline Metrics:")
        print(f"   Events Received: {metrics['metrics']['events_received']}")
        print(f"   Events Processed: {metrics['metrics']['events_processed']}")
        print(f"   Events/Second: {metrics['metrics']['events_per_second']:.2f}")
        print(f"   Avg Latency: {metrics['metrics']['avg_latency_ms']:.2f}ms")
        print(f"   Health: {metrics['health']['overall']}")
        
    finally:
        await pipeline.stop()
        print("\n✅ Pipeline stopped")


async def demo_fault_tolerance():
    """Demo 2: Fault tolerance features"""
    print("\n" + "="*60)
    print("DEMO 2: Fault Tolerance")
    print("="*60 + "\n")
    
    config = PipelineConfig(
        pipeline_id="fault-tolerant-demo",
        storage_backend=StorageBackend.MEMORY,
        max_retries=3,
        retry_delay_ms=500,
    )
    
    pipeline = EventPipeline(config)
    
    # Track failures
    failure_count = 0
    
    async def flaky_handler(event):
        """Handler that fails sometimes"""
        nonlocal failure_count
        failure_count += 1
        
        if failure_count <= 2:
            raise Exception(f"Simulated failure #{failure_count}")
        
        logger.info(f"✅ Successfully processed after {failure_count} attempts")
    
    try:
        await pipeline.initialize()
        await pipeline.start()
        
        # Subscribe with flaky handler
        await pipeline.subscribe(["test"], flaky_handler)
        
        print("📤 Publishing event that will fail twice then succeed...")
        
        event = create_event(
            event_type=EventType.MARKET_DATA,
            source="demo",
            partition_key="TEST",
            symbol="TEST",
            bid=100.0,
            ask=101.0,
        )
        await pipeline.publish("test", event)
        
        # Wait for retries
        await asyncio.sleep(3)
        
        print(f"\n📊 Total handler invocations: {failure_count}")
        print("   (Event was retried automatically after failures)")
        
    finally:
        await pipeline.stop()


async def demo_processing_stages():
    """Demo 3: Multi-stage processing pipeline"""
    print("\n" + "="*60)
    print("DEMO 3: Processing Stages")
    print("="*60 + "\n")
    
    config = PipelineConfig(
        pipeline_id="staged-pipeline",
        storage_backend=StorageBackend.MEMORY,
    )
    
    pipeline = EventPipeline(config)
    
    # Define processing stages
    async def validation_stage(event):
        """Stage 1: Validate event"""
        logger.info(f"Stage 1 - Validating: {event.event_id[:8]}")
        if hasattr(event, 'symbol') and event.symbol:
            return event
        return None  # Filter out invalid events
    
    async def enrichment_stage(event):
        """Stage 2: Enrich event"""
        logger.info(f"Stage 2 - Enriching: {event.event_id[:8]}")
        # In real scenario, would add additional data
        return event
    
    async def transformation_stage(event):
        """Stage 3: Transform event"""
        logger.info(f"Stage 3 - Transforming: {event.event_id[:8]}")
        return event
    
    try:
        await pipeline.initialize()
        
        # Add processing stages
        pipeline.add_stage(PipelineStage(
            name="validation",
            handler=validation_stage,
            input_types=[EventType.MARKET_DATA],
        ))
        
        pipeline.add_stage(PipelineStage(
            name="enrichment",
            handler=enrichment_stage,
            input_types=[EventType.MARKET_DATA],
        ))
        
        pipeline.add_stage(PipelineStage(
            name="transformation",
            handler=transformation_stage,
            input_types=[EventType.MARKET_DATA],
        ))
        
        await pipeline.start()
        
        print("📤 Publishing event through 3-stage pipeline...")
        
        event = create_event(
            event_type=EventType.MARKET_DATA,
            source="demo",
            partition_key="ETHUSDT",
            symbol="ETHUSDT",
            bid=3000.0,
            ask=3001.0,
        )
        
        # Process through stages
        result = await pipeline.process_through_stages(event)
        
        if result:
            print(f"\n✅ Event processed through all stages")
        else:
            print(f"\n❌ Event filtered out by a stage")
        
        # Show stage metrics
        metrics = pipeline.get_metrics()
        print("\n📊 Stage Metrics:")
        for stage in metrics['stages']:
            print(f"   {stage['name']}: {stage['processed']} processed, "
                  f"{stage['avg_latency_ms']:.2f}ms avg latency")
        
    finally:
        await pipeline.stop()


async def demo_replay():
    """Demo 4: Event replay for backtesting"""
    print("\n" + "="*60)
    print("DEMO 4: Event Replay")
    print("="*60 + "\n")
    
    config = PipelineConfig(
        pipeline_id="replay-demo",
        storage_backend=StorageBackend.SQLITE,  # Use SQLite for persistence
        data_dir=Path("demo_replay_data"),
        enable_replay=True,
    )
    
    pipeline = EventPipeline(config)
    
    try:
        await pipeline.initialize()
        await pipeline.start()
        
        # First, publish some historical events
        print("📤 Publishing historical events...")
        
        for i in range(10):
            event = create_event(
                event_type=EventType.MARKET_DATA,
                source="demo",
                partition_key="BTCUSDT",
                symbol="BTCUSDT",
                bid=50000.0 + i * 100,
                ask=50005.0 + i * 100,
            )
            await pipeline.publish("market_data", event)
        
        print(f"   Published 10 events")
        
        # Now replay them
        print("\n🔄 Replaying events...")
        
        replay_count = 0
        
        async def replay_handler(event):
            nonlocal replay_count
            replay_count += 1
            logger.info(f"Replayed: {event.symbol} @ {event.bid}")
        
        count = await pipeline.replay(
            event_types=[EventType.MARKET_DATA],
            handler=replay_handler,
            mode=ReplayMode.FAST,
        )
        
        print(f"\n✅ Replayed {count} events")
        print(f"   Handler received: {replay_count} events")
        
    finally:
        await pipeline.stop()
        
        # Cleanup demo data
        import shutil
        demo_dir = Path("demo_replay_data")
        if demo_dir.exists():
            shutil.rmtree(demo_dir)


async def demo_scalability():
    """Demo 5: Scalability features"""
    print("\n" + "="*60)
    print("DEMO 5: Scalability")
    print("="*60 + "\n")
    
    config = PipelineConfig(
        pipeline_id="scalable-demo",
        storage_backend=StorageBackend.MEMORY,
        num_partitions=12,
        num_shards=4,
    )
    
    pipeline = EventPipeline(config)
    
    try:
        await pipeline.initialize()
        await pipeline.start()
        
        print("📊 Partitioning Configuration:")
        print(f"   Partitions: {config.num_partitions}")
        print(f"   Shards: {config.num_shards}")
        
        # Publish events with different partition keys
        print("\n📤 Publishing events to different partitions...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
        
        for symbol in symbols:
            for i in range(10):
                event = create_event(
                    event_type=EventType.MARKET_DATA,
                    source="demo",
                    partition_key=symbol,  # Partition by symbol
                    symbol=symbol,
                    bid=100.0 + i,
                    ask=101.0 + i,
                )
                await pipeline.publish("market_data", event)
        
        await asyncio.sleep(0.5)
        
        # Show partition distribution
        metrics = pipeline.get_metrics()
        print("\n📊 Partition Distribution:")
        partition_stats = metrics['partitioner']
        for partition, count in sorted(partition_stats.get('partitions', {}).items()):
            print(f"   Partition {partition}: {count} events")
        
        print(f"\n   Imbalance: {partition_stats.get('imbalance', 0):.2%}")
        
        # Show shard stats
        print("\n📊 Shard Distribution:")
        shard_stats = metrics['shards']
        for shard_id, shard in shard_stats.get('shards', {}).items():
            print(f"   {shard_id}: partitions {shard['partitions']}, "
                  f"state: {shard['state']}")
        
    finally:
        await pipeline.stop()


async def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("AlphaAlgo Real-Time Event Pipeline Demo")
    print("="*60)
    print("\nThis demo showcases:")
    print("  1. Basic pipeline usage")
    print("  2. Fault tolerance (retries, dead letter queues)")
    print("  3. Multi-stage processing")
    print("  4. Event replay for backtesting")
    print("  5. Scalability (partitioning, sharding)")
    
    try:
        await demo_basic_pipeline()
        await demo_fault_tolerance()
        await demo_processing_stages()
        await demo_replay()
        await demo_scalability()
        
        print("\n" + "="*60)
        print("All demos completed successfully! ✅")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
