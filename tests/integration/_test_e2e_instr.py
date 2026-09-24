import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import SkillRouter
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.verification.swarm import VerificationSwarm
from trading_bot.core.immutable_shield import ImmutableShield
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, ActionStatus, LogAction
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.execution_bridge import PaperExecutionBridge

class MockWorldModel:
    async def simulate(self, *args, **kwargs): return []
    def predict(self, *args, **kwargs): return {"price": 100.0}
class MockRiskEngine:
    def check_risk(self, *args, **kwargs): return True
class MockExecutionPlanner:
    def plan_execution(self, *args, **kwargs): return {"plan": "execute_now"}
class MockEvolutionGate:
    def validate_evolution(self, *args, **kwargs): return True

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
        world_model=MockWorldModel(),
        hms=hms,
        skill_router=router,
        verifier_swarm=swarm,
        risk_engine=MockRiskEngine(),
        consensus_engine=bus,
        execution_planner=MockExecutionPlanner(),
        evolution_gate=MockEvolutionGate(),
        shield=shield
    )
    yield csc
    event_loop.run_until_complete(bus.stop())

@pytest.mark.asyncio
async def test_e2e_successful_trade_pipeline(full_system):
    csc = full_system
    bus = csc.consensus_engine
    print(f"\nINSTR bus id={id(bus)} csc.decision_bus id={id(csc.decision_bus)} same={bus is csc.decision_bus}")
    print(f"INSTR test loop={asyncio.get_running_loop()}")

    async def monitor():
        for _ in range(30):
            await asyncio.sleep(0.25)
            entries = [(a.action_type, a.status.value, sorted(a.voter_reports)) for a in bus._log]
            pt = bus._processor_task
            print(f"INSTR LOG {entries} proc={'dead' if pt is None or pt.done() else 'alive'}", flush=True)
    m = asyncio.create_task(monitor())

    observation = {"symbol": "BTC/USDT", "price": 50000.0, "volatility": 0.1, "regime": "bull"}
    decision = await csc.process_market_observation(observation)
    m.cancel()
    print(f"INSTR decision={decision.outcome} reason={decision.dominant_rejection_reason}")
    for a in bus._log:
        print(f"INSTR FINAL {a.action_type} {a.status} {sorted(a.voter_reports)}")

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert decision.trade_id is not None
    assert decision.confidence_vector.statistical > 0
    assert len(csc.consensus_engine._log) > 0
    last_log = csc.consensus_engine._log[-1]
    assert last_log.status == ActionStatus.EXECUTED
    assert "ImmutableShield" in last_log.voter_reports
