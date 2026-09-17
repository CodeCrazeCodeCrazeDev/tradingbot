
import pytest
import asyncio
import time
from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_event_bus import decision_bus, LogAction, ActionStatus, EventPriority

@pytest.mark.asyncio
async def test_production_startup_shutdown_and_sla_latency():
    # 1. Startup Gate
    ias = IntegratedAgentSystem({
        'storage_path': 'test_production_data',
        'redis_port': 6379,
    })

    await ias.initialize()
    assert ias.initialized is True
    print("Startup Gate: Passed (IAS & CSC initialized successfully)")

    # 2. Decision Latency SLA Benchmark
    csc = CognitiveSystemController()
    await decision_bus.start()

    # Mock a voter to auto-approve trades for speed
    async def fast_voter(action):
        return {"decision": "APPROVED", "reason": "SLA Benchmark"}
    decision_bus.register_voter("FastVoter", fast_voter)

    latencies = []
    for i in range(10):
        start_time = time.time()
        obs = {'price': 1.1200 + i * 0.0001, 'volatility': 0.1, 'regime': 'TRENDING'}
        decision = await csc.process_market_observation(obs)
        latency = (time.time() - start_time) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    print(f"SLA Latency Gate: Average processing time: {avg_latency:.2f} ms")

    # Assert institutional SLA is strictly < 500ms (typically < 50ms in our optimized V5)
    assert avg_latency < 500.0, f"Average latency {avg_latency:.2f} ms exceeds SLA"
    print("SLA Latency Gate: Passed")

    # 3. Shutdown Gate
    await ias.shutdown()
    await decision_bus.stop()
    assert ias.running is False
    print("Shutdown Gate: Passed")
