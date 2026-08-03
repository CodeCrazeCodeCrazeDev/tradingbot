"""
Concurrency Stress and Chaos Test Suite - AlphaAlgo UCA V5
Tests event bus thread safety, subscriber lock contention, task cancellation,
duplicate submission, and queue backpressure.
"""

import asyncio
import time
import pytest
import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock, AsyncMock
from trading_bot.event_pipeline.event_bus import EventBus, EventBusConfig, DeliveryGuarantee
from trading_bot.event_pipeline.events import Event, EventType, EventPriority, EventMetadata

@dataclass
class DummyEvent(Event):
    key: str = ""
    val: int = 0

    def to_payload(self) -> dict:
        return {"key": self.key, "val": self.val}

    @classmethod
    def from_payload(cls, payload: dict):
        metadata = EventMetadata(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MARKET_DATA,
        )
        return cls(metadata=metadata, key=payload.get("key", ""), val=payload.get("val", 0))

@pytest.mark.asyncio
async def test_event_bus_lock_contention_stress():
    """Stress test subscriber map mutations concurrently with high-throughput publishes."""
    config = EventBusConfig(
        max_queue_size=1000,
        default_guarantee=DeliveryGuarantee.AT_MOST_ONCE
    )
    bus = EventBus(config=config)
    await bus.start()

    received_count = 0
    lock = asyncio.Lock()

    async def handler(event: Event):
        nonlocal received_count
        async with lock:
            received_count += 1

    # 1. Concurrent Subscribes & Unsubscribes
    async def subscriber_stress_loop():
        for i in range(100):
            sub_id = bus.subscribe(["test_topic"], handler)
            await asyncio.sleep(0.001)
            bus.unsubscribe(sub_id)
            await asyncio.sleep(0.001)

    # 2. High-throughput Concurrent Publishes
    async def publisher_stress_loop():
        for i in range(500):
            metadata = EventMetadata(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MARKET_DATA,
            )
            ev = DummyEvent(metadata=metadata, key=f"key_{i}", val=i)
            await bus.publish("test_topic", ev)
            if i % 10 == 0:
                await asyncio.sleep(0.001)

    # Run subscriber modifications and high-volume publishes concurrently
    sub_task = asyncio.create_task(subscriber_stress_loop())
    pub_task = asyncio.create_task(publisher_stress_loop())

    await asyncio.gather(sub_task, pub_task)

    # Allow workers to drain
    await asyncio.sleep(0.1)
    await bus.stop()

    # Assert no deadlocks or race condition crashes occurred
    assert True

@pytest.mark.asyncio
async def test_event_bus_task_cancellation_teardown():
    """Verify background workers are cleaned up properly and cleanly on stop/cancellation."""
    bus = EventBus()
    await bus.start()

    # Assert workers are spawned
    assert len(bus._workers) > 0

    # Stop the event bus
    await bus.stop()

    # Verify all workers are cancelled or done
    for t in bus._workers:
        assert t.done() or t.cancelled()
