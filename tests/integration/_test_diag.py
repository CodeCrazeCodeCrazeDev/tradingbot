import asyncio
import pytest
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import SkillRouter
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.verification.swarm import VerificationSwarm
from trading_bot.core.immutable_shield import ImmutableShield
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, ActionStatus
from trading_bot.core.execution_bridge import PaperExecutionBridge


class MockWorldModel:
    async def simulate(self, *a, **k): return []
    def predict(self, *a, **k): return {"price": 100.0}
class MockRiskEngine:
    def check_risk(self, *a, **k): return True
class MockExecutionPlanner:
    def plan_execution(self, *a, **k): return {"plan": "execute_now"}
class MockEvolutionGate:
    def validate_evolution(self, *a, **k): return True


@pytest.fixture(scope="function")
def full_system(event_loop):
    hms = HierarchicalMemorySystem(base_path="tests/temp_hms_e2e")
    bus = UnifiedDecisionBus()
    shield = ImmutableShield()
    router = SkillRouter()
    swarm = VerificationSwarm()

    async def shield_voter(action):
        report = await shield.validate_action(action.action_type, action.payload, action.payload.get("context", {}))
        return {"decision": report.decision.value, "reason": report.reason}

    bus.register_voter("ImmutableShield", shield_voter)
    PaperExecutionBridge(persist_path="tests/temp_hms_e2e/paper_fills.jsonl").attach(bus)
    event_loop.run_until_complete(bus.start())

    csc = CognitiveSystemController(
        world_model=MockWorldModel(), hms=hms, skill_router=router,
        verifier_swarm=swarm, risk_engine=MockRiskEngine(),
        consensus_engine=bus, execution_planner=MockExecutionPlanner(),
        evolution_gate=MockEvolutionGate(), shield=shield)
    yield csc
    event_loop.run_until_complete(bus.stop())


@pytest.mark.asyncio
async def test_diag(full_system):
    csc = full_system
    bus = csc.consensus_engine
    print(f"\nDIAG test loop: {asyncio.get_running_loop()}")
    print(f"DIAG bus: {bus} decision_bus: {csc.decision_bus} same={bus is csc.decision_bus}")
    print(f"DIAG processor: {bus._processor_task} running={bus._running}")
    print(f"DIAG queue loop: {getattr(bus._action_queue, '_loop', 'NA')} queue={bus._action_queue}")
    print(f"DIAG voters: {list(bus._voters)}")

    async def monitor():
        for _ in range(15):
            await asyncio.sleep(0.5)
            entries = [(a.action_type, a.status.value, list(a.voter_reports)) for a in bus._log]
            print(f"DIAG LOG {entries} proc_done={bus._processor_task.done() if bus._processor_task else 'NA'}", flush=True)
            if bus._processor_task and bus._processor_task.done():
                try:
                    bus._processor_task.result()
                except Exception as e:
                    print(f"DIAG processor EXC: {e!r}", flush=True)
    mtask = asyncio.create_task(monitor())

    decision = await csc.process_market_observation(
        {"symbol": "BTC/USDT", "price": 50000.0, "volatility": 0.1, "regime": "bull"})
    mtask.cancel()
    print(f"DIAG decision: {decision.outcome} reason={decision.dominant_rejection_reason}")
    for a in bus._log:
        print(f"DIAG entry: {a.action_type} {a.status} voters={list(a.voter_reports)}")
    assert decision.outcome is not None
