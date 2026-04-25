"""
Integration Test Base Classes and Utilities
Provides infrastructure for integration testing
"""

import asyncio
import tempfile
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio


class IntegrationTestBase:
    """Base class for integration tests."""
    
    @pytest.fixture(autouse=True)
    def setup_test_env(self, tmp_path):
        """Set up test environment."""
        self.test_dir = tmp_path
        self.setup_fixtures()
        yield
        self.teardown_fixtures()
    
    def setup_fixtures(self):
        """Override to set up test fixtures."""
        pass
    
    def teardown_fixtures(self):
        """Override to clean up test fixtures."""
        pass


class AsyncIntegrationTestBase:
    """Base class for async integration tests."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_async_test_env(self, tmp_path):
        """Set up async test environment."""
        self.test_dir = tmp_path
        await self.async_setup()
        yield
        await self.async_teardown()
    
    async def async_setup(self):
        """Override to set up async fixtures."""
        pass
    
    async def async_teardown(self):
        """Override to clean up async fixtures."""
        pass


class DatabaseIntegrationTest(IntegrationTestBase):
    """Base class for database integration tests."""
    
    def setup_fixtures(self):
        """Set up test database."""
        self.db_path = self.test_dir / "test.db"
        self.db_url = f"sqlite:///{self.db_path}"
        self.init_database()
    
    def init_database(self):
        """Override to initialize database schema."""
        pass
    
    def teardown_fixtures(self):
        """Clean up test database."""
        if self.db_path.exists():
            self.db_path.unlink()


class BrokerIntegrationTest(AsyncIntegrationTestBase):
    """Base class for broker integration tests."""
    
    async def async_setup(self):
        """Set up mock broker."""
        self.broker_config = {
            'type': 'mock',
            'initial_balance': 10000.0,
            'leverage': 100,
            'paper_trading': True
        }
        self.broker = await self.create_broker()
        await self.broker.connect()
    
    async def async_teardown(self):
        """Disconnect broker."""
        if hasattr(self, 'broker') and self.broker:
            await self.broker.disconnect()
    
    async def create_broker(self):
        """Override to create broker instance."""
        from trading_bot.brokers import MockBrokerAdapter
        return MockBrokerAdapter(self.broker_config)


class MarketDataIntegrationTest(IntegrationTestBase):
    """Base class for market data integration tests."""
    
    def setup_fixtures(self):
        """Set up market data fixtures."""
        import pandas as pd
        import numpy as np
        
        # Generate sample data
        dates = pd.date_range(start="2024-01-01", periods=1000, freq="1min")
        self.sample_data = pd.DataFrame({
            "timestamp": dates,
            "open": np.random.uniform(100, 110, 1000),
            "high": np.random.uniform(110, 115, 1000),
            "low": np.random.uniform(95, 100, 1000),
            "close": np.random.uniform(100, 110, 1000),
            "volume": np.random.randint(1000, 10000, 1000)
        })


class SignalFlowIntegrationTest(IntegrationTestBase):
    """Base class for signal flow integration tests."""
    
    def setup_fixtures(self):
        """Set up signal flow test fixtures."""
        self.signals_received = []
        self.orders_placed = []
    
    def on_signal_generated(self, signal: Dict[str, Any]):
        """Callback for signal generation."""
        self.signals_received.append(signal)
    
    def on_order_placed(self, order: Dict[str, Any]):
        """Callback for order placement."""
        self.orders_placed.append(order)


@pytest.fixture
def mock_redis():
    """Provide a mock Redis client for integration tests."""
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.exists.return_value = False
    redis_mock.publish.return_value = 1
    redis_mock.subscribe.return_value = MagicMock()
    redis_mock.pubsub.return_value = MagicMock()
    return redis_mock


@pytest.fixture
def mock_postgres():
    """Provide a mock PostgreSQL connection for integration tests."""
    pg_mock = MagicMock()
    pg_mock.execute.return_value = []
    pg_mock.fetchone.return_value = None
    pg_mock.fetchall.return_value = []
    pg_mock.commit.return_value = None
    pg_mock.rollback.return_value = None
    pg_mock.close.return_value = None
    return pg_mock


@pytest.fixture
def temp_database(tmp_path) -> Generator[Path, None, None]:
    """Create a temporary database file."""
    db_path = tmp_path / "integration_test.db"
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_websocket():
    """Provide a mock WebSocket connection."""
    ws_mock = MagicMock()
    ws_mock.send.return_value = asyncio.Future()
    ws_mock.send.return_value.set_result(None)
    ws_mock.recv.return_value = asyncio.Future()
    ws_mock.recv.return_value.set_result('{"type": "tick", "price": 1.0850}')
    ws_mock.close.return_value = asyncio.Future()
    ws_mock.close.return_value.set_result(None)
    return ws_mock


@pytest.fixture
def mock_http_client():
    """Provide a mock HTTP client."""
    client_mock = MagicMock()
    
    async def mock_get(*args, **kwargs):
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {"status": "ok"}
        response_mock.text.return_value = "OK"
        return response_mock
    
    async def mock_post(*args, **kwargs):
        response_mock = MagicMock()
        response_mock.status_code = 201
        response_mock.json.return_value = {"id": "test-123"}
        return response_mock
    
    client_mock.get = mock_get
    client_mock.post = mock_post
    
    return client_mock


@pytest.fixture
def integration_config(tmp_path) -> Dict[str, Any]:
    """Provide integration test configuration."""
    return {
        "environment": "test",
        "paper_trading": True,
        "database": {
            "url": f"sqlite:///{tmp_path}/test.db"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 1  # Use different DB for tests
        },
        "broker": {
            "type": "mock",
            "initial_balance": 10000.0
        },
        "logging": {
            "level": "DEBUG",
            "file": str(tmp_path / "test.log")
        }
    }


@asynccontextmanager
async def managed_resource(resource, setup_func, teardown_func):
    """Context manager for managing async resources in tests."""
    try:
        await setup_func(resource)
        yield resource
    finally:
        await teardown_func(resource)


class BridgeTestMixin:
    """Mixin for testing bridges between components."""
    
    def assert_bridge_data_integrity(self, source_data, target_data, fields):
        """Assert that data integrity is maintained across bridge."""
        for field in fields:
            assert field in target_data, f"Field {field} missing in target data"
            assert source_data[field] == target_data[field], \
                f"Field {field} changed from {source_data[field]} to {target_data[field]}"
    
    def assert_bridge_error_handling(self, bridge_func, error_scenarios):
        """Test bridge error handling."""
        for scenario_name, scenario in error_scenarios.items():
            with pytest.raises(scenario['exception']):
                bridge_func(**scenario['args'])
