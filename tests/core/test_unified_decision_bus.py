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


def _trade_action() -> LogAction:
    return LogAction(
        action_type="TRADE_EXECUTION",
        payload={"symbol": "EURUSD", "action": "BUY", "quantity": 1.0},
        agent_id="csc",
        priority=EventPriority.CRITICAL,
    )


@pytest.mark.asyncio
async def test_shielded_action_vetoed_when_shield_voter_times_out():
    """A timed-out mandatory shield voter must not silently approve capital
    movement: timeout is recorded as ERROR and the action must be VETOED,
    unlike non-capital events where timeout-then-approve stays acceptable."""
    decision_bus.config = {"voter_timeout": 0.05}
    await decision_bus.start()

    async def slow_shield(action):
        await asyncio.sleep(0.3)
        return {"decision": "APPROVED"}

    async def fast_voter(action):
        return {"decision": "APPROVE", "reason": "ok"}

    decision_bus.register_voter("shield", slow_shield)
    decision_bus.register_voter("risk_check", fast_voter)

    action = _trade_action()
    await decision_bus.propose_action(action)
    await asyncio.sleep(0.6)

    assert action.voter_reports["shield"]["decision"] == "ERROR"
    assert action.status == ActionStatus.VETOED


@pytest.mark.asyncio
async def test_shielded_action_requires_affirmative_shield_decision():
    """A shield voter that abstains/errors (non-affirmative report) must veto
    TRADE_EXECUTION — absence of an explicit veto is not approval."""
    await decision_bus.start()

    async def shrug_shield(action):
        return {"decision": "OBSERVED", "reason": "advisory only"}

    decision_bus.register_voter("shield", shrug_shield)

    action = _trade_action()
    await decision_bus.propose_action(action)
    await asyncio.sleep(0.2)

    assert action.status == ActionStatus.VETOED


@pytest.mark.asyncio
async def test_shielded_action_approves_only_with_affirmative_shield():
    await decision_bus.start()

    async def approve_shield(action):
        return {"decision": "APPROVED", "reason": "within limits"}

    decision_bus.register_voter("shield", approve_shield)

    dispatched = []

    async def recorder(act):
        dispatched.append(act)

    decision_bus.subscribe("TRADE_EXECUTION", recorder, subscriber_id="rec")

    action = _trade_action()
    await decision_bus.propose_action(action)
    await asyncio.sleep(0.2)

    assert action.status == ActionStatus.APPROVED
    assert dispatched and dispatched[0].action_id == action.action_id


@pytest.mark.asyncio
async def test_shielded_action_fails_when_dispatch_handler_raises():
    """Consensus APPROVED but the execution subscriber crashed — the audit
    status must surface FAILED, not a phantom APPROVED that looks executed."""
    await decision_bus.start()

    async def approve_shield(action):
        return {"decision": "APPROVED"}

    decision_bus.register_voter("shield", approve_shield)

    async def boom(action):
        raise RuntimeError("bridge exploded")

    decision_bus.subscribe("TRADE_EXECUTION", boom, subscriber_id="broken_bridge")

    action = _trade_action()
    await decision_bus.propose_action(action)
    await asyncio.sleep(0.2)

    assert action.status == ActionStatus.FAILED


@pytest.mark.asyncio
async def test_shielded_action_fails_when_execution_returns_rejected():
    """An explicit rejection result from the execution bridge (e.g. invalid
    quantity) must not leave the action APPROVED."""
    await decision_bus.start()

    async def approve_shield(action):
        return {"decision": "APPROVED"}

    decision_bus.register_voter("shield", approve_shield)

    async def rejecting_bridge(action):
        return {"status": "rejected", "reason": "invalid_quantity"}

    decision_bus.subscribe("TRADE_EXECUTION", rejecting_bridge, subscriber_id="bridge")

    action = _trade_action()
    await decision_bus.propose_action(action)
    await asyncio.sleep(0.2)

    assert action.status == ActionStatus.FAILED
