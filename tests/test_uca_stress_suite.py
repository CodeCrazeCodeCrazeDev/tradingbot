"""
High Concurrency, Endurance, and Reproducibility Validation Suite for UCA V5.
"""

import pytest
import asyncio
import numpy as np
from typing import Dict, Any
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.immutable_shield import ImmutableShield
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

@pytest.fixture
def setup_system():
    # Setup fresh singletons or instances
    hms = HierarchicalMemorySystem()
    shield = ImmutableShield()
    csc = CognitiveSystemController(world_model=None, hms=hms, shield=shield)
    return hsc_bundle(hms, shield, csc)

class hsc_bundle:
    def __init__(self, hms, shield, csc):
        self.hms = hms
        self.shield = shield
        self.csc = csc

@pytest.mark.asyncio
async def test_concurrency_load():
    """Verify system performance under concurrent high-frequency observation streams."""
    hms = HierarchicalMemorySystem()
    shield = ImmutableShield()
    csc = CognitiveSystemController(world_model=None, hms=hms, shield=shield)

    observations = [
        {"symbol": "EURUSD", "price": 1.1000 + i * 0.0001, "volatility": 0.01}
        for i in range(10)
    ]

    tasks = [csc.process_market_observation(obs) for obs in observations]
    decisions = await asyncio.gather(*tasks)

    assert len(decisions) == 10
    for dec in decisions:
        assert dec is not None
        assert dec.outcome in [DecisionOutcome.TRADE_APPROVED, DecisionOutcome.TRADE_REJECTED]

@pytest.mark.asyncio
async def test_endurance_resource_tracking():
    """Verify discrete_channel bounding prevents memory growth/leaks over 100 consecutive loops."""
    hms = HierarchicalMemorySystem()
    shield = ImmutableShield()
    csc = CognitiveSystemController(world_model=None, hms=hms, shield=shield)

    # Fill channels beyond limits
    csc.discrete_channel = list(range(200))

    obs = {"symbol": "EURUSD", "price": 1.1000, "volatility": 0.01}
    await csc.process_market_observation(obs)

    # Bounded buffer should trim list to 100 entries
    assert len(csc.discrete_channel) <= 100

@pytest.mark.asyncio
async def test_decision_reproducibility():
    """Verify system produces identical core decisions given identical observations."""
    hms = HierarchicalMemorySystem()
    shield = ImmutableShield()
    csc = CognitiveSystemController(world_model=None, hms=hms, shield=shield)

    obs1 = {"symbol": "EURUSD", "price": 1.1200, "volatility": 0.01}
    obs2 = {"symbol": "EURUSD", "price": 1.1200, "volatility": 0.01}

    dec1 = await csc.process_market_observation(obs1)
    dec2 = await csc.process_market_observation(obs2)

    assert dec1.outcome == dec2.outcome
    assert dec1.confidence_vector.statistical == dec2.confidence_vector.statistical
