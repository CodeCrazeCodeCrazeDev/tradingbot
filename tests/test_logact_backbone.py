
import asyncio
import pytest
import os
import json
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, LogAction, ActionStatus, EventPriority

@pytest.mark.asyncio
async def test_logact_backbone_ordering_and_persistence():
    # Setup
    log_path = "temp_logact_test.jsonl"
    if os.path.exists(log_path):
        os.remove(log_path)

    bus = UnifiedDecisionBus({"log_path": log_path})
    # Reset singleton state for test (though conftest should handle it)
    bus._log = []

    await bus.start()

    # Propose multiple actions
    action1 = LogAction(action_type="test", payload={"val": 1}, agent_id="agent1", priority=EventPriority.NORMAL)
    action2 = LogAction(action_type="test", payload={"val": 2}, agent_id="agent2", priority=EventPriority.HIGH)

    await bus.propose_action(action1)
    await bus.propose_action(action2)

    # Wait for processing
    for _ in range(20):
        await asyncio.sleep(0.1)
        if len(bus._log) == 2:
            break

    assert len(bus._log) == 2
    assert bus._log[0].payload["val"] == 2
    assert bus._log[1].payload["val"] == 1

    # Verify Persistence
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2
        data0 = json.loads(lines[0])
        assert data0["payload"]["val"] == 2

    await bus.stop()
    if os.path.exists(log_path):
        os.remove(log_path)

@pytest.mark.asyncio
async def test_logact_voting():
    bus = UnifiedDecisionBus()
    await bus.start()

    # Register a voter that vetoes
    async def veto_voter(action):
        return {"decision": "VETO", "reason": "Test Veto"}

    bus.register_voter("veto_agent", veto_voter)

    action = LogAction(action_type="trade", payload={}, agent_id="trader")
    await bus.propose_action(action)

    for _ in range(20):
        await asyncio.sleep(0.1)
        logged_action = bus.get_action_by_id(action.action_id)
        if logged_action and logged_action.status == ActionStatus.VETOED:
            break

    logged_action = bus.get_action_by_id(action.action_id)
    assert logged_action is not None
    assert logged_action.status == ActionStatus.VETOED
    assert "veto_agent" in logged_action.voter_reports

    await bus.stop()
