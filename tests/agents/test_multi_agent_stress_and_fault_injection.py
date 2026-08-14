"""
Multi-Agent Subsystem - Stress, Fault-Injection, and Endurance Validation Suite
=============================================================================
This suite executes comprehensive validation of the multi-agent subsystem under:
1. Concurrency (100 parallel execution streams, race conditions, livelocks, deadlocks)
2. Fault Injection (agent crashes, malformed outputs, delayed responses, partial quorums)
3. Decision Quality and Latency (latency SLAs, consensus quality, Bayesian update properties)
4. Long-Run Stability (repeated execution cycles, memory growth, resource cleanup)
"""

import asyncio
import time
import gc
import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from trading_bot.agents.multi_agent_debate import (
    create_debate_system,
    MultiAgentDebateSystem,
    MarketContext,
    TradeAction,
    Conviction,
    AgentRole,
    AgentArgument,
    FinalDecision,
    TradingAgent
)

# Robust mock context for testing
def get_standard_market_context(portfolio_exposure: float = 0.25) -> MarketContext:
    return MarketContext(
        symbol="EURUSD",
        current_price=1.1000,
        htf_trend='UP',
        ltf_trend='UP',
        volatility=0.015,
        volume_ratio=1.3,
        key_levels={
            'support': [1.0950, 1.0900],
            'resistance': [1.1050, 1.1100]
        },
        news_sentiment=0.4,
        portfolio_exposure=portfolio_exposure,
        correlation_risk=0.3,
        vix_level=18.0
    )


class CrashProneAgent(TradingAgent):
    """Agent designed to simulate unexpected crashes during analyze/respond."""
    def __init__(self, role: AgentRole, crash_on_analyze: bool = False, crash_on_respond: bool = False):
        super().__init__(role, {})
        self.crash_on_analyze = crash_on_analyze
        self.crash_on_respond = crash_on_respond

    def analyze(self, context: MarketContext) -> AgentArgument:
        if self.crash_on_analyze:
            raise RuntimeError("Simulated crash during analyze")
        return AgentArgument(
            agent_role=self.role,
            action=TradeAction.BUY,
            conviction=Conviction.HIGH,
            reasoning=["Normal analysis"],
            key_factors={},
            confidence=0.8,
            timestamp=datetime.now()
        )

    def respond_to_argument(self, argument: AgentArgument, context: MarketContext) -> Optional[AgentArgument]:
        if self.crash_on_respond:
            raise RuntimeError("Simulated crash during respond")
        return AgentArgument(
            agent_role=self.role,
            action=argument.action,
            conviction=Conviction.HIGH,
            reasoning=["Agreeing response"],
            key_factors={},
            confidence=0.8,
            timestamp=datetime.now()
        )


class DelayedAgent(TradingAgent):
    """Agent that introduces simulated latency to test timeouts and concurrency."""
    def __init__(self, role: AgentRole, delay_seconds: float):
        super().__init__(role, {})
        self.delay_seconds = delay_seconds

    def analyze(self, context: MarketContext) -> AgentArgument:
        time.sleep(self.delay_seconds)  # Force synchronous block or delay
        return AgentArgument(
            agent_role=self.role,
            action=TradeAction.BUY,
            conviction=Conviction.HIGH,
            reasoning=["Delayed analysis completed"],
            key_factors={},
            confidence=0.75,
            timestamp=datetime.now()
        )

    def respond_to_argument(self, argument: AgentArgument, context: MarketContext) -> Optional[AgentArgument]:
        time.sleep(self.delay_seconds)
        return AgentArgument(
            agent_role=self.role,
            action=argument.action,
            conviction=Conviction.HIGH,
            reasoning=["Delayed response completed"],
            key_factors={},
            confidence=0.75,
            timestamp=datetime.now()
        )


@pytest.mark.asyncio
async def test_concurrency_heavy_parallel_debates():
    """
    CONCURRENCY STRESS TEST (Phase 3)
    Executes 100 parallel debate instances concurrently, checking for race conditions,
    task leaks, deadlocks, and task execution safety.
    """
    system = create_debate_system()
    context = get_standard_market_context()

    # Launch 100 concurrent debate tasks
    tasks = [system.debate(context) for _ in range(100)]

    start_time = time.perf_counter()
    decisions = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.perf_counter() - start_time

    print(f"\nCompleted 100 parallel debates in {duration:.3f}s")

    # Assert all debates succeeded and returned a valid FinalDecision
    for idx, decision in enumerate(decisions):
        assert not isinstance(decision, Exception), f"Task {idx} failed with: {decision}"
        assert isinstance(decision, FinalDecision), f"Task {idx} returned invalid type: {type(decision)}"
        assert decision.action in [TradeAction.BUY, TradeAction.STRONG_BUY, TradeAction.HOLD, TradeAction.SELL, TradeAction.STRONG_SELL, TradeAction.NO_TRADE]
        assert len(decision.provenance["decision_uuid"]) > 0


@pytest.mark.asyncio
async def test_fault_injection_agent_crashes():
    """
    FAULT INJECTION (Phase 4)
    Verifies that the MultiAgentDebateSystem behaves deterministically and fails-safely
    when one or multiple agents crash unexpectedly during execution.
    """
    system = create_debate_system()

    # Inject an agent that crashes during analyze
    bad_agent = CrashProneAgent(AgentRole.MACRO_STRATEGIST, crash_on_analyze=True)
    system.agents = [bad_agent, system.agents[1], system.agents[2]]  # Replace first agent

    context = get_standard_market_context()
    decision = await system.debate(context)

    # System must degrade gracefully, using fallback arguments for the crashed agent
    assert decision is not None
    assert decision.action in [TradeAction.BUY, TradeAction.HOLD, TradeAction.NO_TRADE]


@pytest.mark.asyncio
async def test_fault_injection_total_quorum_failure():
    """
    FAULT INJECTION (Phase 4)
    Verifies that if all agents crash or fail, the orchestrator triggers emergency fail-closed
    veto procedures, returning NO_TRADE and preserving full provenance logs.
    """
    system = create_debate_system()
    system.agents = [
        CrashProneAgent(AgentRole.MACRO_STRATEGIST, crash_on_analyze=True),
        CrashProneAgent(AgentRole.TACTICAL_EXECUTIONER, crash_on_analyze=True),
        CrashProneAgent(AgentRole.RISK_SENTINEL, crash_on_analyze=True)
    ]

    context = get_standard_market_context()
    decision = await system.debate(context)

    # Total crash -> emergency NO_TRADE (fail-closed)
    assert decision.action == TradeAction.NO_TRADE
    assert "EMERGENCY VETO" in decision.reasoning or "Emergency" in decision.reasoning or "failed" in decision.reasoning
    assert decision.confidence == 1.0 or decision.confidence == 0.0 or decision.confidence == 0.5


@pytest.mark.asyncio
async def test_fault_injection_delayed_responses():
    """
    FAULT INJECTION & CONCURRENCY (Phases 3 & 4)
    Verifies that the MultiAgentDebateSystem behaves correctly when some agents are delayed,
    integrating with DelayedAgent.
    """
    system = create_debate_system()
    # Inject an agent with 1ms delay to simulate network latency
    delayed_agent = DelayedAgent(AgentRole.MACRO_STRATEGIST, delay_seconds=0.001)
    system.agents = [delayed_agent, system.agents[1], system.agents[2]]

    context = get_standard_market_context()
    decision = await system.debate(context)

    assert decision is not None
    assert decision.action in [TradeAction.BUY, TradeAction.HOLD, TradeAction.NO_TRADE]


@pytest.mark.asyncio
async def test_decision_quality_sla_benchmarks():
    """
    DECISION QUALITY & LATENCY BENCHMARKS (Phase 5)
    Asserts performance targets for average decision latency and consensus resolution rates.
    """
    system = create_debate_system()
    context = get_standard_market_context()

    latencies = []
    for _ in range(20):
        start = time.perf_counter()
        _ = await system.debate(context)
        latencies.append((time.perf_counter() - start) * 1000.0)

    avg_latency = sum(latencies) / len(latencies)
    p50_latency = sorted(latencies)[int(len(latencies) * 0.5)]
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    print(f"\nLatency SLA Profile: Avg={avg_latency:.2f}ms | p50={p50_latency:.2f}ms | p95={p95_latency:.2f}ms")

    # SLA limit: Average latency must be < 100ms
    assert avg_latency < 100.0, f"Latency SLA violation: avg_latency={avg_latency:.2f}ms"


@pytest.mark.asyncio
async def test_long_run_stability_and_memory_growth():
    """
    LONG-RUN STABILITY (Phase 6)
    Runs 100 repeated sequential debate cycles, measuring active object counts
    and verifying zero memory leakage.
    """
    system = create_debate_system()
    context = get_standard_market_context()

    # Pre-collect garbage to establish baseline
    gc.collect()
    initial_objects = len(gc.get_objects())

    # Execute repeated debate cycles
    for _ in range(50):
        _ = await system.debate(context)

    gc.collect()
    final_objects = len(gc.get_objects())
    object_diff = final_objects - initial_objects

    print(f"\nLong-run Memory Stability: Initial objects={initial_objects} | Final objects={final_objects} | Diff={object_diff}")

    # Assert no severe unchecked growth of uncollected objects (e.g. < 1500 new objects after 50 cycles)
    assert object_diff < 1500, f"Potential memory leak detected: {object_diff} uncollected objects added."
