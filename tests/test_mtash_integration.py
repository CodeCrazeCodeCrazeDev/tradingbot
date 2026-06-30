import asyncio
import time
import logging
from datetime import datetime
from trading_bot.core.event_bus import get_event_bus, Event, EventTypes
from trading_bot.services.mtash_service import MTASHService
from trading_bot.core.service_registry import get_service_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

async def test_mtash_event_flow():
    logger.info("Starting MTASH Event Flow Validation...")

    event_bus = get_event_bus()
    await event_bus.start()

    registry = get_service_registry()

    # Configure MTASH Service
    config = {
        'total_capital': 100000.0,
        'max_agents': 5,
        'safety_enabled': True,
        'storage_path': 'test_mtash_data'
    }

    mtash_service = MTASHService(config)
    mtash_service.set_event_bus(event_bus)

    # Track predictions
    predictions = []
    async def on_prediction(event):
        predictions.append(event)
        logger.info(f"Received Prediction Event from MTASH: {event.payload['symbol']}")

    event_bus.subscribe("test_listener", [EventTypes.AI_PREDICTION_READY], on_prediction)

    # Start service
    logger.info("Initializing and starting MTASH Service...")
    await mtash_service.start()

    # Simulate MARKET_DATA_UPDATE event
    logger.info("Simulating market data flow...")
    start_time = time.time()

    # Payload must contain 'trend' etc for systems_ai to produce signal > 0.1
    await event_bus.publish(Event(
        event_type=EventTypes.MARKET_DATA_UPDATE,
        payload={
            'symbol': 'EURUSD',
            'data': {'price': 1.0850, 'volatility': 0.012, 'rsi': 45, 'trend': 0.5, 'momentum': 0.5, 'mean_reversion': 0.5}
        },
        source="test_generator"
    ))

    # Wait for prediction (with timeout)
    timeout = 15
    while len(predictions) == 0 and (time.time() - start_time) < timeout:
        await asyncio.sleep(0.5)

    latency = time.time() - start_time

    # Cleanup
    await mtash_service.stop()
    await event_bus.stop()

    # Validate
    if len(predictions) > 0:
        logger.info(f"✅ Event Flow Validated. Latency: {latency:.4f}s")
        assert predictions[0].payload['source'] == 'mtash'
        assert predictions[0].payload['symbol'] == 'EURUSD'
    else:
        logger.error("❌ Event Flow Failed: No prediction received within timeout")
        raise TimeoutError("MTASH failed to respond to market data")

    logger.info("MTASH Integration Test Completed.")

if __name__ == "__main__":
    asyncio.run(test_mtash_event_flow())
