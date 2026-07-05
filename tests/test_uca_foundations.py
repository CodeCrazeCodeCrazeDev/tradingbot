"""
AlphaAlgo UCA-2026 Core Architecture Fitness Test
================================================

Verifies the 'One Brain', 'One Registry', and 'One Bus' principles.
"""

import pytest
import asyncio
from trading_bot.core.unified_registry import UnifiedComponentRegistry
from trading_bot.core.unified_event_bus import UnifiedDecisionBus
from trading_bot.core.immutable_shield import ImmutableShield

def test_singleton_integrity():
    """Verify that core foundations are strict singletons."""
    reg1 = UnifiedComponentRegistry()
    reg2 = UnifiedComponentRegistry()
    assert reg1 is reg2

    bus1 = UnifiedDecisionBus()
    bus2 = UnifiedDecisionBus()
    assert bus1 is bus2

    shield1 = ImmutableShield()
    shield2 = ImmutableShield()
    assert shield1 is shield2

@pytest.mark.asyncio
async def test_decision_bus_latency():
    """Verify high-performance async dispatch on the Unified Decision Bus."""
    bus = UnifiedDecisionBus()
    await bus.start()

    received = False
    async def mock_handler(event):
        nonlocal received
        received = True

    from trading_bot.core.unified_event_bus import UnifiedEvent
    bus.subscribe("test_sub", "TEST_EVENT", mock_handler)

    await bus.publish(UnifiedEvent(event_type="TEST_EVENT", payload={}, source="Test"))

    # Wait for dispatch
    await asyncio.sleep(0.1)
    assert received
    await bus.stop()

def test_registry_registration():
    """Verify the registry correctly stores and retrieves components."""
    reg = UnifiedComponentRegistry()
    reg.register("test_comp", {"data": 123}, "TestType")
    assert reg.get("test_comp")["data"] == 123
    reg.unregister("test_comp")
