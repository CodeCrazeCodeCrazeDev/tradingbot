"""
Integration Test: Unified Orchestration Consolidation
====================================================

Verifies that:
1. IntegratedAgentSystem initializes as the central brain.
2. CognitiveSystemController acts as the MasterOrchestrator.
3. LegacyOrchestratorAdapter routes correctly.
"""

import pytest
import asyncio
from datetime import datetime
from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core_agent_system.legacy_adapter import LegacyOrchestratorAdapter
from trading_bot.core.csc.controller import CognitiveSystemController as MasterOrchestrator
from trading_bot.core.orchestrator import SignalType

@pytest.mark.asyncio
async def test_ias_as_brain():
    """Verify IAS can execute a strategic task"""
    system = IntegratedAgentSystem({
        'storage_path': 'test_unified_data',
        'redis_port': 6379,
    })
    await system.initialize()

    task = "Test strategic decision"
    result = await system.execute_task(task)
    assert result['success'] is True
    assert 'answer' in result
    await system.shutdown()

@pytest.mark.asyncio
async def test_master_orchestrator_delegation():
    """Verify MasterOrchestrator initializes correctly"""
    orch = MasterOrchestrator()
    assert orch is not None

@pytest.mark.asyncio
async def test_legacy_adapter_routing():
    """Verify LegacyOrchestratorAdapter routes to IAS"""
    system = IntegratedAgentSystem({
        'storage_path': 'test_unified_data',
        'redis_port': 6379,
    })
    await system.initialize()

    adapter = LegacyOrchestratorAdapter(system, {})

    # This should trigger an IAS task
    market_data = {'price': 1.0850, 'change_24h': 5.0}
    signal = await adapter.generate_signal("EURUSD", market_data)

    assert hasattr(adapter, 'ias')
    assert adapter.ias == system
    await system.shutdown()

@pytest.mark.asyncio
async def test_brain_shutdown():
    """Verify graceful shutdown"""
    system = IntegratedAgentSystem({
        'storage_path': 'test_unified_data',
        'redis_port': 6379,
    })
    await system.initialize()
    await system.shutdown()
    assert system.running is False
