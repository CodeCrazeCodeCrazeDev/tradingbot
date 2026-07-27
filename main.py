"""
AlphaAlgo UCA-2026 Authoritative Entry Point
==========================================

Minimal bootstrapper responsible for initializing the Unified Cognitive System.
All business logic is delegated to the Cognitive System Controller (CSC).
"""

import asyncio
import logging
import sys
import argparse
from typing import Dict, Any

from trading_bot.core.unified_registry import registry
from trading_bot.core.unified_event_bus import decision_bus
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.immutable_shield import shield
from trading_bot.world_model.v2_core import WorldModelV2

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("alphaalgo_runtime.log")
    ]
)
logger = logging.getLogger("AlphaAlgo.Main")

async def bootstrap(args: argparse.Namespace):
    """
    Initializes the UCA-2026 core components in the authoritative startup order.
    """
    logger.info("🚀 Bootstrapping AlphaAlgo UCA-2026 Unified Intelligence System")

    try:
        # 1. Start Decision Bus
        await decision_bus.start()
        registry.register("decision_bus", decision_bus, "Infrastructure")

        # 2. Initialize Hierarchical Memory System (HMS)
        hms = HierarchicalMemorySystem()
        registry.register("hms", hms, "Core")

        # 3. Initialize Immutable Shield (Governance)
        registry.register("shield", shield, "Governance")

        # 4. Initialize World Model (Predictive Core)
        # Note: asset_dims should ideally come from config
        asset_dims = {"FX": 64, "Equities": 128}
        world_model = WorldModelV2(asset_dims=asset_dims)
        registry.register("world_model", world_model, "Intelligence")

        # 5. Initialize Cognitive System Controller (CSC) - The One Brain
        csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)
        registry.register("csc", csc, "Controller")

        logger.info("✅ All core components registered and initialized")

        # 6. Start the Main Loop via CSC
        logger.info("🎬 Starting Cognitive System Controller main loop")

        # Placeholder for real market data ingestion
        while True:
            # In a real scenario, this would be fed by a MarketDataFeeder
            mock_observation = {"timestamp": "2026-07-24T12:00:00Z", "symbol": args.symbol}
            await csc.process_market_observation(mock_observation)
            await asyncio.sleep(args.interval)

    except asyncio.CancelledError:
        logger.info("System shutdown initiated...")
    except Exception as e:
        logger.critical(f"💥 Fatal system error during bootstrap: {e}", exc_info=True)
    finally:
        await decision_bus.stop()
        logger.info("System shutdown complete")

def parse_args():
    parser = argparse.ArgumentParser(description="AlphaAlgo UCA-2026 Main Entry Point")
    parser.add_argument("--symbol", type=str, default="EURUSD", help="Primary trading symbol")
    parser.add_argument("--interval", type=int, default=60, help="Observation interval in seconds")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(bootstrap(args))
    except KeyboardInterrupt:
        pass
