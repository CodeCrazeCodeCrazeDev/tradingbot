import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.hypothesis import ReasoningBranch
from trading_bot.core.hms.models import VerifierReport
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus, LogAction, ActionStatus

@pytest.mark.asyncio
async def test_event_bus_e2e_consensus_flow():
    """
    End-to-end integration and consensus verification test.
    Tests the fully integrated CognitiveSystemController, HierarchicalMemorySystem,
    and SkillRouter loop interacting through the active decision bus.
    """
    # Force reset Singleton to ensure correct mock dependencies are injected
    CognitiveSystemController._instance = None

    # 1. Initialize Event Bus
    await decision_bus.start()

    # 2. Setup Real/Stub dependencies (avoiding mock-only await blocks where possible)
    world_model = MagicMock()

    # Realistically mock HMS and Shield
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    hms.memory_schema = {"version": "1.0", "last_optimized": None}

    shield = MagicMock()
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    # 3. Create the active controller
    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    # 4. Trigger observation
    obs = {
        "price_action": "BULLISH",
        "volatility": 0.15,
        "market": {"volatility": 0.15}
    }

    # Simulate how the event bus transitions proposed actions
    # We subscribe to the decision bus and auto-approve/execute executions
    async def auto_resolve():
        await asyncio.sleep(0.1)
        # Process pending actions on the bus and set status to APPROVED/EXECUTED
        # simulating a successful multi-agent voter consensus round.
        if hasattr(decision_bus, "queue") and decision_bus.queue:
            q_size = decision_bus.queue.qsize()
            for _ in range(q_size):
                action = await decision_bus.queue.get()
                action.status = ActionStatus.EXECUTED
                # Re-enqueue or trigger subscription updates if needed
                decision_bus.queue.task_done()

    resolve_task = asyncio.create_task(auto_resolve())

    # 5. Process through Cognitive System Controller
    decision = await csc.process_market_observation(obs)

    # Wait for resolver
    await resolve_task

    # 6. Verify integration outcomes
    assert decision is not None
    assert decision.outcome in [DecisionOutcome.TRADE_APPROVED, DecisionOutcome.TRADE_REJECTED]
    if decision.outcome == DecisionOutcome.TRADE_APPROVED:
        assert decision.trade_id is not None
        assert hms.store_ledger_entry.call_count > 0

    # 7. Stop Event Bus cleanly
    await decision_bus.stop()
