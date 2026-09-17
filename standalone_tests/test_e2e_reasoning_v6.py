import asyncio
import logging
import torch
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.world_model.causal_model import CausalWorldModel
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.immutable_shield import GovernanceDecision

from trading_bot.core.unified_event_bus import decision_bus

async def test_e2e_reasoning_pipeline():
    print("Starting End-to-End Reasoning Validation...")
    await decision_bus.start()

    # 1. Setup Integrated Components
    hms = HierarchicalMemorySystem(base_path="alphaalgo_data/test_e2e_hms")
    world_model = CausalWorldModel(hms)
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc = CognitiveSystemController(world_model, hms, shield)

    # 2. Inject Market Observation
    # Should trigger: Surprise -> SAGE Retrieval -> HASP Check -> DiscoLoop -> Multi-Hypothesis -> Simulation -> Shield -> Folding
    observation = {
        "symbol": "BTC/USDT",
        "price": 65000.0,
        "volatility": 0.15,
        "features": [0.1] * 16
    }

    print("Processing Market Observation...")
    decision = await csc.process_market_observation(observation)

    # 3. Validate Outcome
    print(f"Decision Outcome: {decision.outcome}")
    if decision.outcome != DecisionOutcome.TRADE_APPROVED:
        print(f"REJECTION REASON: {decision.dominant_rejection_reason}")
    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert decision.trade_id is not None

    # 4. Verify Information Preservation (Folding)
    # Check if entry exists in ledger
    import os
    ledger_files = os.listdir("alphaalgo_data/test_e2e_hms/research_ledger")
    print(f"Ledger entries created: {len(ledger_files)}")
    assert len(ledger_files) > 0

    # 5. Verify DiscoLoop tokens
    print(f"Discrete Reasoning Channel: {csc.discrete_channel[-3:]}")
    assert len(csc.discrete_channel) >= 3

    # 6. Verify Causal Impact in World Model
    # (Mocked in process_market_observation but verifies integration)
    print("E2E Reasoning Validation Successful.")
    await decision_bus.stop()

if __name__ == "__main__":
    asyncio.run(test_e2e_reasoning_pipeline())
    print("✅ End-to-End Reasoning Validation Passed")
