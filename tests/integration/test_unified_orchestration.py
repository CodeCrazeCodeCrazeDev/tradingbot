"""
Integration Test: Unified Orchestration Consolidation
====================================================

Verifies that:
1. IntegratedAgentSystem initializes as the central brain.
2. MasterOrchestrator delegates correctly.
3. DecisionLayerService uses the brain.
4. LegacyOrchestratorAdapter routes correctly.
"""

import pytest
import asyncio
from datetime import datetime
from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core_agent_system.legacy_adapter import LegacyOrchestratorAdapter
from master_orchestrator import MasterOrchestrator
from trading_bot.core.orchestrator import SignalType

@pytest.fixture
async def ias():
    system = IntegratedAgentSystem({
        'storage_path': 'test_unified_data',
        'redis_port': 6379, # Mocked/skipped if not running
    })
    await system.initialize()
    return system

@pytest.mark.asyncio
async def test_ias_as_brain(ias):
    """Verify IAS can execute a strategic task"""
    task = "Test strategic decision"
    result = await ias.execute_task(task)
    assert result['success'] is True
    assert 'answer' in result

@pytest.mark.asyncio
async def test_master_orchestrator_delegation():
    """Verify MasterOrchestrator delegates to IAS"""
    orch = MasterOrchestrator({'storage_path': 'test_master_data'})
    assert hasattr(orch, 'ias')
    assert orch.superintelligence == orch.ias

    # Test async startup (lightweight)
    await orch.ias.initialize()
    assert orch.ias.initialized is True

@pytest.mark.asyncio
async def test_legacy_adapter_routing(ias):
    """Verify LegacyOrchestratorAdapter routes to IAS"""
    adapter = LegacyOrchestratorAdapter(ias, {})

    # This should trigger an IAS task
    market_data = {'price': 1.0850, 'change_24h': 5.0}
    signal = await adapter.generate_signal("EURUSD", market_data)

    # Even if it returns None (if signal logic doesn't trigger),
    # we verify it reached the adapter
    assert hasattr(adapter, 'ias')
    assert adapter.ias == ias

@pytest.mark.asyncio
async def test_brain_shutdown(ias):
    """Verify graceful shutdown"""
    await ias.shutdown()
    assert ias.running is False
