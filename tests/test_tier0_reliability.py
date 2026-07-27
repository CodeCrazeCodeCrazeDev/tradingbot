
import asyncio
import logging
import sys
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, LogAction, ActionStatus, EventPriority
from trading_bot.core.immutable_shield import shield, GovernanceDecision

# Configure logging to see the output
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def run_tier0_verification():
    print("Starting Tier 0 Reliability Verification (LogAct Backbone)")
    bus = UnifiedDecisionBus()
    await bus.start()

    # 1. Propose an action that should be approved
    print("Case 1: Valid Trade Action")
    action_ok = LogAction(
        action_type="trade",
        payload={"exposure": 0.5},
        agent_id="test_agent"
    )
    await bus.propose_action(action_ok)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify approval and execution
    print(f"Action Status: {action_ok.status}")
    print(f"Voter Reports: {action_ok.voter_reports.keys()}")

    if action_ok.status == ActionStatus.EXECUTED:
        print("PASS: Valid trade executed")
    else:
        print(f"FAIL: Valid trade status is {action_ok.status}")
        sys.exit(1)

    # 2. Propose an action that should be VETOED by the Shield
    print("\nCase 2: Invalid Trade Action (High Exposure)")
    action_bad = LogAction(
        action_type="trade",
        payload={"exposure": 5.0}, # Exceeds max_exposure=1.0
        agent_id="test_agent"
    )
    await bus.propose_action(action_bad)

    await asyncio.sleep(0.5)

    # Verify veto
    print(f"Action Status: {action_bad.status}")
    if action_bad.status == ActionStatus.VETOED:
        print("PASS: Invalid trade vetoed")
    else:
        print(f"FAIL: Invalid trade status is {action_bad.status}")
        sys.exit(1)

    await bus.stop()
    print("\nTier 0 Reliability Verification COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_tier0_verification())
