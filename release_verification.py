import asyncio
import logging
import uuid
import sys
from datetime import datetime
from trading_bot.ai.hub import create_hub
from trading_bot.core_agent_system.coordination_core import TaskType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinalReleaseVerification")

async def run_release_verification():
    logger.info("=" * 60)
    logger.info("FINAL PASS/FAIL RELEASE VERIFICATION")
    logger.info("=" * 60)

    # 1. Initialize Hub (CSC / One Brain)
    hub = create_hub({
        'storage_path': 'release_test_data',
        'safety_threshold': 0.7
    })

    await hub.initialize()
    logger.info("Gate 1: Architecture Initialization ... PASS")

    # 2. Test Deterministic Replay & Persistence
    # Write a test record
    test_key = f"release_check_{uuid.uuid4().hex[:6]}"
    test_value = {"status": "verified", "timestamp": datetime.now().isoformat()}
    await hub.agent_system.coordination_core.shared_memory.write(test_key, test_value, "RELEASE_BOT")
    await hub.agent_system.coordination_core.shared_memory.save()

    # Reload and verify
    await hub.agent_system.coordination_core.shared_memory.load()
    restored = await hub.agent_system.coordination_core.shared_memory.read(test_key, "RELEASE_BOT")

    if restored == test_value:
        logger.info("Gate 2: Persistence & Atomic Recovery ... PASS")
    else:
        logger.error("Gate 2: Persistence & Atomic Recovery ... FAIL")
        return False

    # 3. Test Integrated Decision Pipeline (Consensus -> Simulation -> Plan)
    market_data = {
        'price': 1.0850,
        'rsi': -0.5,        # Using float values for systems_ai features
        'volatility': 0.1,
        'momentum': 0.2
    }

    decision_result = await hub.think('EURUSD', market_data)

    # Verify consensus was reached
    if decision_result.get('consensus', {}).get('consensus_score', 0) > 0:
         logger.info("Gate 3: Multi-Agent Consensus ... PASS")
    else:
         logger.error("Gate 3: Multi-Agent Consensus ... FAIL")
         return False

    # Verify Production Gates check
    gate_verdict = decision_result.get('gate_result', {})
    if gate_verdict.get('passed'):
        logger.info("Gate 4: Objective Production Gates ... PASS")
    else:
        logger.error(f"Gate 4: Objective Production Gates ... FAIL (Details: {gate_verdict.get('details')})")
        return False

    # 4. Verify Immutable Audit Trail
    audit_id = f"audit_{decision_result['decision_id']}"
    audit_trail = await hub.agent_system.coordination_core.shared_memory.read(audit_id, "CSC_HUB")

    if audit_trail and audit_trail.get('decision_id') == decision_result['decision_id']:
        logger.info("Gate 5: Institutional Audit Traceability ... PASS")
        if audit_trail.get('architectural_invariants', {}).get('one_brain_pattern'):
             logger.info("Gate 6: Architectural Invariants ... PASS")
        else:
             logger.error("Gate 6: Architectural Invariants ... FAIL")
             return False
    else:
        logger.error("Gate 5: Institutional Audit Traceability ... FAIL")
        return False

    # 5. Resource Performance Check
    latency = decision_result.get('latency_ms', 9999)
    if latency < 2000:
        logger.info(f"Gate 7: Performance Latency ({latency:.2f}ms) ... PASS")
    else:
        logger.error(f"Gate 7: Performance Latency ({latency:.2f}ms) ... FAIL")
        return False

    logger.info("=" * 60)
    logger.info("RELEASE STATUS: APPROVED")
    logger.info("=" * 60)

    await hub.shutdown()
    return True

if __name__ == "__main__":
    success = asyncio.run(run_release_verification())
    sys.exit(0 if success else 1)
