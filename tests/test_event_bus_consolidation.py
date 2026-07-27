import unittest
import asyncio
from trading_bot.core.unified_event_bus import decision_bus, UnifiedEvent
from trading_bot.core.event_bus import EventBus, Event, EventPriority

class TestEventBusConsolidation(unittest.TestCase):
    def test_event_bus_bridge(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Start unified bus
        loop.run_until_complete(decision_bus.start())

        # Handler for unified bus
        received = []
        async def handler(event):
            received.append(event)

        decision_bus.subscribe("test_sub", "test.event", handler)

        # Publish via legacy bus
        eb = EventBus()
        event = Event(
            event_type="test.event",
            payload={"data": "test"},
            source="legacy_source",
            priority=EventPriority.HIGH
        )

        loop.run_until_complete(eb.publish(event))

        # Give it a moment to process
        loop.run_until_complete(asyncio.sleep(0.1))

        self.assertTrue(len(received) > 0)
        self.assertEqual(received[0].event_type, "test.event")
        self.assertEqual(received[0].source, "legacy_source")

        loop.run_until_complete(decision_bus.stop())
        loop.close()

if __name__ == "__main__":
    unittest.main()
