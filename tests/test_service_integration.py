"""
Service Integration Tests
==========================

Tests for verifying that all TIER 1 services integrate correctly
through the event bus and service registry.
"""

import asyncio
import pytest
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestServiceIntegration:
    """Test service integration"""
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus for testing"""
        from trading_bot.core.event_bus import create_event_bus
        return create_event_bus()
    
    @pytest.fixture
    def registry(self, event_bus):
        """Create service registry for testing"""
        from trading_bot.core.service_registry import create_service_registry
        reg = create_service_registry()
        reg.set_event_bus(event_bus)
        return reg
    
    @pytest.fixture
    def service_factory(self, registry, event_bus):
        """Create service factory for testing"""
        from trading_bot.core.service_factory import create_service_factory
        return create_service_factory(
            registry=registry,
            event_bus=event_bus,
            config={'services': {'enabled': True}}
        )
    
    def test_event_bus_creation(self, event_bus):
        """Test event bus can be created"""
        assert event_bus is not None
        logger.info("✓ Event bus created successfully")
    
    def test_registry_creation(self, registry):
        """Test service registry can be created"""
        assert registry is not None
        logger.info("✓ Service registry created successfully")
    
    def test_service_factory_creation(self, service_factory):
        """Test service factory can be created"""
        assert service_factory is not None
        logger.info("✓ Service factory created successfully")
    
    def test_tier1_service_creation(self, service_factory):
        """Test TIER 1 services can be created"""
        services = service_factory.create_tier1_services()
        
        assert len(services) > 0, "No TIER 1 services created"
        logger.info(f"✓ Created {len(services)} TIER 1 services")
        
        # Check for critical services
        critical = ['database', 'broker']
        for svc in critical:
            if svc in services:
                logger.info(f"  ✓ {svc} service created")
            else:
                logger.warning(f"  ✗ {svc} service NOT created")
    
    def test_service_registration(self, service_factory, registry):
        """Test services are registered in registry"""
        service_factory.create_tier1_services()
        
        all_services = registry.get_all_services()
        assert len(all_services) > 0, "No services registered"
        
        logger.info(f"✓ {len(all_services)} services registered")
        for name, info in all_services.items():
            logger.info(f"  - {name}: {info.state.value}")
    
    @pytest.mark.asyncio
    async def test_service_startup(self, service_factory, registry):
        """Test services can be started"""
        service_factory.create_tier1_services()
        
        # Start all services
        results = await registry.start_all()
        
        started = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)
        
        logger.info(f"✓ Started {started} services, {failed} failed")
        
        # Stop all services
        await registry.stop_all()
        logger.info("✓ All services stopped")
    
    @pytest.mark.asyncio
    async def test_event_publishing(self, event_bus):
        """Test events can be published and received"""
        from trading_bot.core.event_bus import Event, EventTypes
        
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        # Subscribe
        event_bus.subscribe('test', [EventTypes.MARKET_DATA_UPDATE], handler)
        
        # Publish
        await event_bus.publish(Event(
            event_type=EventTypes.MARKET_DATA_UPDATE,
            payload={'symbol': 'BTCUSDT', 'price': 50000},
            source='test'
        ))
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(received_events) > 0, "No events received"
        logger.info(f"✓ Event published and received")
        
        # Cleanup
        event_bus.unsubscribe('test')
    
    @pytest.mark.asyncio
    async def test_msos_service(self, service_factory, registry):
        """Test MSOS service specifically"""
        services = service_factory.create_tier1_services()
        
        if 'msos' not in services:
            pytest.skip("MSOS service not available")
        
        msos = services['msos']
        
        # Start service
        await msos.start()
        
        # Check health
        health = await msos.health_check()
        logger.info(f"MSOS health: {health.healthy} - {health.message}")
        
        # Check trading allowed
        is_allowed = msos.is_trading_allowed()
        logger.info(f"Trading allowed: {is_allowed}")
        
        # Stop service
        await msos.stop()
        logger.info("✓ MSOS service test complete")
    
    @pytest.mark.asyncio
    async def test_risk_service(self, service_factory, registry):
        """Test Risk service specifically"""
        services = service_factory.create_tier1_services()
        
        if 'risk' not in services:
            pytest.skip("Risk service not available")
        
        risk = services['risk']
        
        # Start service
        await risk.start()
        
        # Check health
        health = await risk.health_check()
        logger.info(f"Risk health: {health.healthy} - {health.message}")
        
        # Get risk state
        state = risk.get_risk_state()
        logger.info(f"Risk state: {state}")
        
        # Stop service
        await risk.stop()
        logger.info("✓ Risk service test complete")
    
    @pytest.mark.asyncio
    async def test_execution_service(self, service_factory, registry):
        """Test Execution service specifically"""
        services = service_factory.create_tier1_services()
        
        if 'execution' not in services:
            pytest.skip("Execution service not available")
        
        execution = services['execution']
        
        # Start service
        await execution.start()
        
        # Check health
        health = await execution.health_check()
        logger.info(f"Execution health: {health.healthy} - {health.message}")
        
        # Get stats
        stats = execution.get_execution_stats()
        logger.info(f"Execution stats: {stats}")
        
        # Stop service
        await execution.stop()
        logger.info("✓ Execution service test complete")
    
    @pytest.mark.asyncio
    async def test_signals_service(self, service_factory, registry):
        """Test Signals service specifically"""
        services = service_factory.create_tier1_services()
        
        if 'signals' not in services:
            pytest.skip("Signals service not available")
        
        signals = services['signals']
        
        # Start service
        await signals.start()
        
        # Check health
        health = await signals.health_check()
        logger.info(f"Signals health: {health.healthy} - {health.message}")
        
        # Get stats
        stats = signals.get_signal_stats()
        logger.info(f"Signal stats: {stats}")
        
        # Stop service
        await signals.stop()
        logger.info("✓ Signals service test complete")
    
    def test_creation_report(self, service_factory):
        """Test service creation report"""
        service_factory.create_tier1_services()
        
        report = service_factory.get_creation_report()
        
        assert 'created' in report
        assert 'failed' in report
        assert 'total_created' in report
        assert 'total_failed' in report
        
        logger.info(f"✓ Creation report: {report['total_created']} created, {report['total_failed']} failed")
        
        if report['failed']:
            logger.warning(f"Failed services: {list(report['failed'].keys())}")


class TestEventFlow:
    """Test event flow between services"""
    
    @pytest.fixture
    def setup(self):
        """Setup event bus and registry"""
        from trading_bot.core.event_bus import create_event_bus
        from trading_bot.core.service_registry import create_service_registry
        from trading_bot.core.service_factory import create_service_factory
        
        event_bus = create_event_bus()
        registry = create_service_registry()
        registry.set_event_bus(event_bus)
        factory = create_service_factory(registry, event_bus, {})
        
        return {
            'event_bus': event_bus,
            'registry': registry,
            'factory': factory,
        }
    
    @pytest.mark.asyncio
    async def test_signal_to_execution_flow(self, setup):
        """Test signal flows to execution"""
        from trading_bot.core.event_bus import Event, EventTypes
        
        event_bus = setup['event_bus']
        factory = setup['factory']
        registry = setup['registry']
        
        # Create services
        services = factory.create_tier1_services()
        
        # Track events
        events_received = []
        
        async def track_events(event):
            events_received.append(event.event_type)
        
        # Subscribe to track events
        event_bus.subscribe('tracker', [
            EventTypes.SIGNAL_GENERATED,
            EventTypes.TRADE_REQUEST,
            EventTypes.TRADE_APPROVED,
            EventTypes.TRADE_SIZED,
            EventTypes.ORDER_PLACED,
        ], track_events)
        
        # Start services
        await registry.start_all()
        
        # Simulate signal generation
        await event_bus.publish(Event(
            event_type=EventTypes.SIGNAL_GENERATED,
            payload={
                'symbol': 'BTCUSDT',
                'direction': 'buy',
                'confidence': 0.8,
            },
            source='test'
        ))
        
        # Wait for event processing
        await asyncio.sleep(0.5)
        
        logger.info(f"Events received: {events_received}")
        
        # Stop services
        await registry.stop_all()
        event_bus.unsubscribe('tracker')
        
        logger.info("✓ Signal to execution flow test complete")


def run_quick_test():
    """Run a quick integration test"""
    print("\n" + "=" * 60)
    print("ALPHAALGO SERVICE INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    try:
        from trading_bot.core.event_bus import create_event_bus
        from trading_bot.core.service_registry import create_service_registry
        from trading_bot.core.service_factory import create_service_factory
        
        print("1. Creating Event Bus...")
        event_bus = create_event_bus()
        print("   [OK] Event Bus created")
        
        print("\n2. Creating Service Registry...")
        registry = create_service_registry()
        registry.set_event_bus(event_bus)
        print("   [OK] Service Registry created")
        
        print("\n3. Creating Service Factory...")
        factory = create_service_factory(registry, event_bus, {})
        print("   [OK] Service Factory created")
        
        print("\n4. Creating TIER 1 Services...")
        services = factory.create_tier1_services()
        print(f"   [OK] Created {len(services)} services")
        
        for name in services:
            print(f"      - {name}")
        
        print("\n5. Checking Creation Report...")
        report = factory.get_creation_report()
        print(f"   [OK] Created: {report['total_created']}")
        print(f"   [FAIL] Failed: {report['total_failed']}")
        
        if report['failed']:
            print("\n   Failed services:")
            for name, reason in report['failed'].items():
                print(f"      - {name}: {reason}")
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST COMPLETE")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    run_quick_test()
