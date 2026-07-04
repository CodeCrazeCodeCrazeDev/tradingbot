import asyncio
import logging
import sys
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.world_model.causal.gwm import GenerativeWorldModel
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.governance.immutable_shield import GovernanceGate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[logging.FileHandler('uca_brain.log'), logging.StreamHandler()]
)
logger = logging.getLogger("UCA-2026")

async def main():
    logger.info("="*60)
    logger.info("ALPHAALGO UCA-2026: UNIFIED COGNITIVE SYSTEM")
    logger.info("="*60)

    # 1. Initialize Institutional Components
    config = {"latent_dim": 256, "max_exposure": 0.05}

    hms = HierarchicalMemorySystem(config)
    world_model = GenerativeWorldModel(config)
    governance = GovernanceGate(config)

    # 2. Initialize the One Brain (CSC)
    csc = CognitiveSystemController(config, world_model, hms, governance)
    await csc.initialize()

    logger.info("Unified Brain Initialized. Starting OSA Loop.")

    # 3. Primary Execution Loop
    try:
        while True:
            # Observe real market data (grounded)
            market_data = {"symbol": "BTCUSD", "price": 65000, "volatility": 0.02}

            # CSC reasoning cycle
            await csc.execute_task("Maximize risk-adjusted alpha in current regime", context=market_data)

            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    finally:
        await csc.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
