import asyncio
import logging
import sys
import os

# Standard library and third-party imports
from datetime import datetime

# Local imports
from trading_bot.core.unified_event_bus import decision_bus
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.immutable_shield import shield

logging.basicConfig(level=logging.INFO)

async def test_boot():
    print("Testing UCA V5 components...")

    # Test HMS
    if not os.path.exists("temp_hms"):
        os.makedirs("temp_hms")
    hms = HierarchicalMemorySystem("temp_hms")
    print("✅ HMS initialized")

    # Test CSC
    csc = CognitiveSystemController(world_model=None, hms=hms, shield=shield)
    csc2 = CognitiveSystemController()
    assert csc is csc2, "CSC Singleton failed"
    print("✅ CSC initialized and singleton verified")

    # Test observation
    obs = {"symbol": "EURUSD", "volatility": 0.1}
    decision = await csc.process_market_observation(obs)
    if decision:
        print(f"✅ CSC processed observation: {decision.outcome}")
    else:
        print("❌ CSC failed to process observation")

    print("Verification complete!")

if __name__ == "__main__":
    asyncio.run(test_boot())
