"""
End-to-End Tests for UnifiedDecisionBus (LogAct Backbone).
Verifies real asynchronous consensus, subscriber dispatch, timeouts, and voter logic.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from trading_bot.core.unified_event_bus import (
    UnifiedDecisionBus,
    LogAction,
    ActionStatus,
    EventPriority
)

@pytest.mark.asyncio
async def test_event_bus_e2e_approved_consensus():
    """Verifies that an action gets approved when all voters approve."""
    # Reset singleton/instance for clean test
    bus = UnifiedDecisionBus()
    bus._voters.clear()
    bus._subscribers.clear()

    # Register voters
    async def voter_alpha(action: LogAction) -> Dict[str, Any]:
        return {"decision": "APPROVE", "confidence": 0.95}

    async def voter_beta(action: LogAction) -> Dict[str, Any]:
        return {"decision": "APPROVE", "confidence": 0.9}

    bus.register_voter("voter_alpha", voter_alpha)
    bus.register_voter("voter_beta", voter_beta)

    # Subscribe to dispatch
    received_actions = []
    async def sample_handler(action: LogAction):
        received_actions.append(action)

    bus.subscribe("TRADE_EXECUTION", sample_handler)

    # Start the event loop processor
    await bus.start()

    action = LogAction(
        action_type="TRADE_EXECUTION",
        payload={"symbol": "EURUSD", "volume": 1.0},
        agent_id="TEST_AGENT"
    )

    await bus.propose_action(action)
    status = await action.wait_for_decision(timeout=2.0)

    # Verify transition to EXECUTED
    assert status == ActionStatus.EXECUTED
    assert len(received_actions) == 1
    assert received_actions[0].action_id == action.action_id
    assert action.voter_reports["voter_alpha"]["decision"] == "APPROVE"

    # Stop processor
    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_e2e_vetoed_consensus():
    """Verifies that an action gets vetoed if any voter rejects/vetoes."""
    bus = UnifiedDecisionBus()
    bus._voters.clear()
    bus._subscribers.clear()

    async def voter_alpha(action: LogAction) -> Dict[str, Any]:
        return {"decision": "APPROVE", "confidence": 0.95}

    async def voter_beta(action: LogAction) -> Dict[str, Any]:
        return {"decision": "VETO", "reason": "Risk bounds exceeded"}

    bus.register_voter("voter_alpha", voter_alpha)
    bus.register_voter("voter_beta", voter_beta)

    await bus.start()

    action = LogAction(
        action_type="TRADE_EXECUTION",
        payload={"symbol": "EURUSD", "volume": 1.0},
        agent_id="TEST_AGENT"
    )

    await bus.propose_action(action)
    status = await action.wait_for_decision(timeout=2.0)

    # Verify transition to VETOED
    assert status == ActionStatus.VETOED

    await bus.stop()
