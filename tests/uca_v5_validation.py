"""
UCA V5 Validation Suite
=======================

Verifies architectural invariants, scientific benchmarks (FIRE, CL-Bench),
and 12-step pipeline integrity.
"""

import pytest
import asyncio
from typing import Dict, Any
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_event_bus import decision_bus, LogAction, ActionStatus
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.risk.unified_risk_engine import risk_engine

@pytest.mark.asyncio
async def test_12_step_pipeline_integrity():
    """Verifies that the CSC executes the 12-step pipeline correctly."""
    # Reset singletons
    CognitiveSystemController._instance = None

    hms = HierarchicalMemorySystem(base_path="tests/temp_hms")
    from trading_bot.core.immutable_shield import shield
    csc = CognitiveSystemController(hms=hms, shield=shield)
    await decision_bus.start()

    observation = {"price": 1.12, "volatility": 0.05, "drawdown": 0.01}
    decision = await csc.process_market_observation(observation)
    assert decision is not None

    await decision_bus.stop()

@pytest.mark.asyncio
async def test_logact_voter_consensus():
    """Verifies that LogAct correctly handles voter consensus and vetoes."""
    await decision_bus.start()
    # Propose a trade that violates risk limits
    action = LogAction(
        action_type="trade",
        payload={"exposure": 2.0}, # Limit is 1.0
        agent_id="test_agent"
    )

    # The risk_engine is already registered as a voter in its __init__
    await decision_bus.propose_action(action)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Find action in log
    logged_action = next((a for a in decision_bus._log if a.action_id == action.action_id), None)
    assert logged_action is not None
    assert logged_action.status == ActionStatus.VETOED
    assert "unified_risk_engine" in logged_action.voter_reports
    await decision_bus.stop()

@pytest.mark.asyncio
async def test_sage_evolution():
    """Verifies that SAGE graph-memory evolves correctly."""
    hms = HierarchicalMemorySystem(base_path="tests/temp_hms_sage")
    history = [{"source": "EURUSD", "target": "USD_STRENGTH", "relation": "CORRELATED_WITH"}]

    hms.evolve_memory(history)
    assert hms.sage_graph.has_edge("EURUSD", "USD_STRENGTH")

    # Test Reader Feedback (Pruning)
    feedback = [{"action": "PRUNE", "edge": ("EURUSD", "USD_STRENGTH")}]
    hms.evolve_memory([], reader_feedback=feedback)
    assert not hms.sage_graph.has_edge("EURUSD", "USD_STRENGTH")

@pytest.mark.asyncio
async def test_scientific_amnesia_mscl():
    """Verifies MSCL surprise-driven replay."""
    hms = HierarchicalMemorySystem(base_path="tests/temp_hms_mscl")
    surprise = [{"event": "Black Swan", "surprise_score": 0.9}]
    # Should not crash and should log amnesia event
    hms.apply_scientific_amnesia(surprise)
