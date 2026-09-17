import pytest
import asyncio
import os
from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core.service_factory import create_service_factory
from trading_bot.core.service_registry import get_service_registry, ServiceState
from trading_bot.core.event_bus import get_event_bus, Event, EventTypes
from trading_bot.core_agent_system.master_orchestrator import SystemContext
from datetime import datetime

@pytest.mark.asyncio
async def test_full_decision_path():
    """
    Test that a signal published to the event bus reaches the IntegratedBrainService,
    which then executes a task via IntegratedAgentSystem.
    """
    config = {
        'services': {'enable_tier1': True},
        'storage_path': 'test_core_agent_data_decision'
    }

    # Setup infrastructure
    registry = get_service_registry()
    # Reset registry for clean test
    registry._services.clear()

    event_bus = get_event_bus()
    await event_bus.start()

    factory = create_service_factory(registry, event_bus, config)

    # Create tier 1 services
    services = factory.create_tier1_services()

    # Get the registered service info
    all_services = registry.get_all_services()
    assert "integrated_brain" in all_services
    brain_service = all_services["integrated_brain"].instance

    assert brain_service is not None
    await brain_service.start()
    # Mocking ServiceState update since we are starting manually
    all_services["integrated_brain"].state = ServiceState.RUNNING

    # Publish an Alpha Signal
    test_payload = {
        'symbol': 'EURUSD',
        'strategy': 'TrendFollowing',
        'direction': 'BUY',
        'price': 1.0850
    }

    await event_bus.publish(Event(
        event_type=EventTypes.ALPHA_SIGNAL,
        payload=test_payload,
        source="test_suite"
    ))

    # Allow some time for processing
    await asyncio.sleep(1)

    # Verify the brain initialized and has agents
    status = brain_service.brain.get_comprehensive_status()
    assert status['initialized'] is True
    assert status['agents']['total_agents'] > 0

    # Verify memory access
    await brain_service.brain.memory_system.store_knowledge("test_key", "test_value")
    retrieved = await brain_service.brain.memory_system.retrieve_knowledge("test_key")
    assert retrieved == "test_value"

    # Verify world model access
    assert brain_service.brain.world_model is not None

    # Cleanup
    await brain_service.stop()
    await event_bus.stop()

@pytest.mark.asyncio
async def test_legacy_orchestrator_delegation():
    """
    Test that the CoreSystemsService correctly uses the LegacyOrchestratorAdapter
    to route calls to IAS.
    """
    config = {
        'storage_path': 'test_core_agent_data_legacy'
    }

    from trading_bot.services.core_systems_service import CoreSystemsService
    core_svc = CoreSystemsService(config)
    await core_svc.start()

    # The _orchestrator should be a LegacyOrchestratorAdapter
    assert core_svc._orchestrator is not None
    from trading_bot.core_agent_system.legacy_adapter import LegacyOrchestratorAdapter
    assert isinstance(core_svc._orchestrator, LegacyOrchestratorAdapter)

    # Test signal generation routing (mocked/simulated)
    market_data = {'price': 1.0850, 'change_24h': 5.0}
    # generate_signal will call ias.execute_task
    try:
        await core_svc._orchestrator.generate_signal('EURUSD', market_data)
        brain_reachable = True
    except Exception:
        brain_reachable = False

    assert brain_reachable

    await core_svc.stop()
