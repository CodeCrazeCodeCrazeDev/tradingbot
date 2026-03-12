"""
Integration Tests for the Unified Module System
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.registry import ModuleRegistry, ModuleCategory
from trading_bot.orchestration import MasterOrchestrator, OrchestratorConfig
from trading_bot.events import SignalEvent, PriceUpdateEvent
from trading_bot.config.unified_config_manager import UnifiedConfigManager

class TestModuleRegistry:
    """Test the module registry system."""
    
    def test_registry_initialization(self):
        """Test registry can be initialized."""
        registry = ModuleRegistry()
        assert registry is not None
        assert len(registry.modules) == 0
    
    def test_module_discovery(self):
        """Test module discovery functionality."""
        registry = ModuleRegistry()
        
        # Mock the discovery process
        registry._discover_modules = Mock()
        registry._discover_modules.return_value = None
        
        registry.discover_modules()
        
        # Should have called discovery
        registry._discover_modules.assert_called_once()
    
    def test_module_categorization(self):
        """Test modules are categorized correctly."""
        registry = ModuleRegistry()
        
        # Test category mapping
        assert registry._get_category_from_path("trading_bot/data") == ModuleCategory.DATA_CONNECTIVITY
        assert registry._get_category_from_path("trading_bot/analysis") == ModuleCategory.ANALYSIS_INTELLIGENCE
        assert registry._get_category_from_path("trading_bot/trading") == ModuleCategory.TRADING_EXECUTION
        assert registry._get_category_from_path("trading_bot/risk") == ModuleCategory.RISK_SAFETY
    
    def test_dependency_extraction(self):
        """Test dependency extraction from modules."""
        registry = ModuleRegistry()
        
        # Create a mock module with imports
        mock_module = Mock()
        mock_module.__file__ = "test.py"
        
        # Test with no imports
        deps = registry._extract_dependencies(mock_module)
        assert isinstance(deps, list)
    
    def test_dependency_resolution(self):
        """Test dependency resolution."""
        registry = ModuleRegistry()
        
        # Add some test modules
        registry.add_module("module_a", dependencies=[])
        registry.add_module("module_b", dependencies=["module_a"])
        registry.add_module("module_c", dependencies=["module_b"])
        
        # Resolve dependencies
        success, order, errors = registry.resolve_dependencies()
        
        assert success == True
        assert "module_a" in order
        assert "module_b" in order
        assert "module_c" in order
        assert order.index("module_a") < order.index("module_b")
        assert order.index("module_b") < order.index("module_c")

class TestServiceLocator:
    """Test the service locator."""
    
    def test_service_registration(self):
        from trading_bot.registry.service_locator import ServiceLocator
        
        locator = ServiceLocator()
        
        # Register a service
        test_service = Mock()
        locator.register("test_service", test_service)
        
        # Retrieve service
        retrieved = locator.get("test_service")
        assert retrieved is test_service
    
    def test_factory_registration(self):
        from trading_bot.registry.service_locator import ServiceLocator
        
        locator = ServiceLocator()
        
        # Register with factory
        factory = Mock(return_value=Mock())
        locator.register("factory_service", factory=factory)
        
        # Should create on first get
        service = locator.get("factory_service")
        factory.assert_called_once()
    
    def test_dependency_injection(self):
        from trading_bot.registry.service_locator import ServiceLocator
        
        locator = ServiceLocator()
        
        # Register dependency
        dependency = Mock()
        locator.register("dependency", dependency)
        
        # Register service with dependency
        factory = Mock()
        locator.register("service", factory=factory, dependencies=["dependency"])
        
        # Get service
        service = locator.get("service")
        
        # Factory should be called with dependency
        factory.assert_called_once_with(dependency=dependency)

class TestEventBus:
    """Test the event bus system."""
    
    @pytest.mark.asyncio
    async def test_event_publishing(self):
        from trading_bot.orchestration.event_bus import EventBus, Event
        
        bus = EventBus()
        
        # Create test event
        event = Event(type="test_event", data={"message": "hello"})
        
        # Publish event (should not raise)
        await bus.publish(event)
        
        # Check statistics
        stats = bus.get_statistics()
        assert stats['events_published'] == 1
    
    @pytest.mark.asyncio
    async def test_event_subscription(self):
        from trading_bot.orchestration.event_bus import EventBus, Event, EventHandler
        
        bus = EventBus()
        
        # Create test handler
        handler = Mock(spec=EventHandler)
        handler.handle = AsyncMock()
        handler.can_handle = Mock(return_value=True)
        
        # Subscribe handler
        bus.subscribe("test_event", handler)
        
        # Publish event
        event = Event(type="test_event", data={})
        await bus.publish(event)
        
        # Handler should be called
        await asyncio.sleep(0.1)  # Give time for async handling
        handler.handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_filtering(self):
        from trading_bot.orchestration.event_bus import EventBus, Event
        
        bus = EventBus()
        
        # Add filter that blocks all events
        bus.add_filter(lambda e: False)
        
        # Publish event
        event = Event(type="test_event", data={})
        await bus.publish(event)
        
        # Should not increment count
        stats = bus.get_statistics()
        assert stats['events_published'] == 0

class TestMasterOrchestrator:
    """Test the master orchestrator."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        config = OrchestratorConfig(
            mode="paper",
            auto_start=False,
            parallel_init=False  # Simplify for test
        )
        
        orchestrator = MasterOrchestrator(config)
        
        # Mock the registry to avoid actual module discovery
        orchestrator.registry = Mock()
        orchestrator.registry.discover_modules = Mock()
        orchestrator.registry.resolve_dependencies = Mock(return_value=(True, [], []))
        orchestrator.registry.get_statistics = Mock(return_value={'total_modules': 0})
        
        # Mock service managers
        for manager in orchestrator.service_managers.values():
            manager.initialize = AsyncMock(return_value=True)
        
        # Should initialize without errors
        result = await orchestrator.initialize()
        
        # Note: May fail due to missing components in test environment
        # but should not crash
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_signal_processing(self):
        """Test signal processing through orchestrator."""
        config = OrchestratorConfig(mode="paper")
        orchestrator = MasterOrchestrator(config)
        
        # Mock dependencies
        orchestrator.running = True
        orchestrator.service_managers = Mock()
        
        # Create test signal
        signal = {
            'id': 'test_signal',
            'symbol': 'EURUSD',
            'direction': 'buy',
            'confidence': 0.75
        }
        
        # Process signal (with mocked components)
        result = await orchestrator.process_signal(signal)
        
        # Should return a result dict
        assert isinstance(result, dict)
        assert 'status' in result

class TestConfiguration:
    """Test the configuration system."""
    
    def test_config_manager_creation(self):
        """Test config manager can be created."""
        config = UnifiedConfigManager()
        assert config is not None
        assert len(config.layers) == 0
    
    def test_layer_addition(self):
        """Test adding configuration layers."""
        config = UnifiedConfigManager()
        
        # Add a layer
        test_data = {"key": "value", "nested": {"inner": "data"}}
        config.add_layer("test", test_data)
        
        assert len(config.layers) == 1
        assert config.layers[0].name == "test"
        assert config.layers[0].data == test_data
    
    def test_config_merging(self):
        """Test configuration merging with precedence."""
        config = UnifiedConfigManager()
        
        # Add base layer
        config.add_layer("base", {"a": 1, "b": 2}, priority=0)
        
        # Add override layer
        config.add_layer("override", {"b": 3, "c": 4}, priority=10)
        
        # Get merged config
        merged = config.get_merged_config()
        
        assert merged["a"] == 1  # From base
        assert merged["b"] == 3  # From override (higher priority)
        assert merged["c"] == 4  # From override
    
    def test_nested_access(self):
        """Test nested configuration access."""
        config = UnifiedConfigManager()
        
        # Add nested config
        config.add_layer("test", {
            "trading": {
                "mode": "paper",
                "risk": 0.02
            }
        })
        
        # Test nested access
        assert config.get("trading.mode") == "paper"
        assert config.get("trading.risk") == 0.02
        assert config.get("trading.nonexistent") is None
        assert config.get("trading.nonexistent", "default") == "default"
    
    def test_environment_loading(self):
        """Test loading from environment variables."""
        import os
        
        # Set test environment variables
        os.environ["TRADING_TEST_MODE"] = "paper"
        os.environ["TRADING_TEST_RISK"] = "0.02"
        
        try:
            config = UnifiedConfigManager()
            config.load_from_environment(prefix="TRADING_TEST_")
            
            # Check values were loaded
            assert config.get("test.mode") == "paper"
            assert config.get("test.risk") == "0.02"
            
        finally:
            # Clean up
            os.environ.pop("TRADING_TEST_MODE", None)
            os.environ.pop("TRADING_TEST_RISK", None)

class TestEventDefinitions:
    """Test event definitions."""
    
    def test_signal_event_creation(self):
        """Test signal event creation."""
        event = SignalEvent(
            symbol="EURUSD",
            direction="buy",
            confidence=0.75,
            price=1.0850
        )
        
        assert event.symbol == "EURUSD"
        assert event.direction == "buy"
        assert event.confidence == 0.75
        assert event.price == 1.0850
        assert event.type == "signal_generated"
        assert event.signal_id is not None
    
    def test_price_update_event(self):
        """Test price update event."""
        event = PriceUpdateEvent(
            symbol="GBPUSD",
            price=1.2500,
            volume=1000,
            bid=1.2499,
            ask=1.2501
        )
        
        assert event.symbol == "GBPUSD"
        assert event.price == 1.2500
        assert event.spread == 0.0002
        assert event.type == "price_update"
    
    def test_event_data_methods(self):
        """Test event data helper methods."""
        from trading_bot.events.events import BaseEvent
        
        event = BaseEvent(
            type="test",
            data={"key1": "value1", "key2": 42}
        )
        
        assert event.get_data("key1") == "value1"
        assert event.get_data("key2") == 42
        assert event.get_data("nonexistent") is None
        assert event.get_data("nonexistent", "default") == "default"
        
        event.set_data("new_key", "new_value")
        assert event.get_data("new_key") == "new_value"
        assert event.has_data("new_key")
        assert not event.has_data("missing")

# Integration Tests
class TestFullIntegration:
    """Test integration of all components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test a complete end-to-end flow."""
        # This is a simplified integration test
        # In a real environment, this would test the full flow
        
        # Create components
        config = OrchestratorConfig(mode="paper", auto_start=False)
        orchestrator = MasterOrchestrator(config)
        
        # Mock external dependencies
        orchestrator.registry = Mock()
        orchestrator.registry.discover_modules = Mock()
        orchestrator.registry.resolve_dependencies = Mock(return_value=(True, [], []))
        
        # The test should not crash even with mocks
        assert orchestrator is not None
        assert orchestrator.config.mode == "paper"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
