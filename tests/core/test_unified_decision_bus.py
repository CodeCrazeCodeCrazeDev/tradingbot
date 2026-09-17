import asyncio
import pytest
from datetime import datetime
from trading_bot.core.unified_event_bus import (
    decision_bus, LogAction, ActionStatus, EventPriority, UnifiedEvent
)

@pytest.fixture(autouse=True)
async def reset_decision_bus():
    # Stop if running
    await decision_bus.stop()
    # Reset internal structures
    decision_bus._voters = {}
    decision_bus._subscribers.clear()
    decision_bus._log.clear()
    decision_bus.config = {}
    yield
    await decision_bus.stop()

@pytest.mark.asyncio
async def test_decision_bus_consensus_and_timeout():
    # Inject config for testing timeout
    decision_bus.config = {"voter_timeout": 0.05}
    await decision_bus.start()

    # Create dummy voter reports
    async def fast_voter(action: LogAction):
        return {"decision": "APPROVE", "reason": "Fast checks passed"}

    async def slow_voter(action: LogAction):
        await asyncio.sleep(0.3)  # Exceeds the 0.05s timeout
        return {"decision": "APPROVE", "reason": "Slow checks passed"}

    decision_bus.register_voter("fast", fast_voter)
    decision_bus.register_voter("slow", slow_voter)

    # Propose an action
    action = LogAction(
        action_type="test_trade",
        payload={"symbol": "BTC/USD"},
        agent_id="test_agent",
        priority=EventPriority.HIGH
    )

    # Track if the action is dispatched
    dispatched_actions = []
    async def handle_dispatched(act):
        dispatched_actions.append(act)

    decision_bus.subscribe("test_trade", handle_dispatched)

    await decision_bus.propose_action(action)
    await asyncio.sleep(0.6)  # Wait for LogAct processor to complete audit phase

    # Verify slow voter timed out but fast voter report succeeded
    assert "fast" in action.voter_reports
    assert action.voter_reports["fast"]["decision"] == "APPROVE"

    assert "slow" in action.voter_reports
    assert "Timeout" in action.voter_reports["slow"]["reason"]

    # Since neither voter vetoed (Timeout is treated as ERROR, not VETO/REJECT in our basic consensus),
    # the action should still be APPROVED
    assert action.status == ActionStatus.APPROVED
    assert len(dispatched_actions) == 1
    assert dispatched_actions[0].action_id == action.action_id

@pytest.mark.asyncio
async def test_decision_bus_consensus_veto():
    await decision_bus.start()

    async def veto_voter(action: LogAction):
        return {"decision": "VETO", "reason": "Risk limits exceeded"}

    decision_bus.register_voter("vetoer", veto_voter)

    action = LogAction(
        action_type="risky_trade",
        payload={"size": 1000},
        agent_id="agent_1"
    )

    await decision_bus.propose_action(action)
    await asyncio.sleep(0.1)

    # Action should be vetoed and not approved
    assert action.status == ActionStatus.VETOED
