"""
Pytest Configuration and Fixtures
=================================
Shared fixtures and configuration for all tests.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, AsyncMock
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# ASYNC SUPPORT
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='h')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': prices - np.random.rand(1000) * 0.3,
        'high': prices + np.random.rand(1000) * 0.5,
        'low': prices - np.random.rand(1000) * 0.5,
        'close': prices,
        'volume': np.random.randint(1000, 100000, 1000)
    })


@pytest.fixture
def sample_tick_data() -> pd.DataFrame:
    """Generate sample tick data for testing."""
    np.random.seed(42)
    timestamps = pd.date_range(start='2024-01-01', periods=10000, freq='100ms')
    base_price = 1.1000
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'bid': base_price + np.cumsum(np.random.randn(10000) * 0.0001),
        'ask': base_price + np.cumsum(np.random.randn(10000) * 0.0001) + 0.0002,
        'bid_size': np.random.randint(100, 10000, 10000),
        'ask_size': np.random.randint(100, 10000, 10000)
    })


@pytest.fixture
def sample_signal() -> Dict[str, Any]:
    """Generate sample trading signal."""
    return {
        'signal_id': 'SIG_TEST_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'confidence': 0.85,
        'entry_price': 1.1000,
        'stop_loss': 1.0950,
        'take_profit': 1.1100,
        'timestamp': datetime.now(),
        'source': 'test_strategy',
        'metadata': {
            'timeframe': 'H1',
            'indicators': ['RSI', 'MACD', 'BB']
        }
    }


@pytest.fixture
def sample_order() -> Dict[str, Any]:
    """Generate sample order."""
    return {
        'order_id': 'ORD_TEST_001',
        'symbol': 'EURUSD',
        'side': 'BUY',
        'quantity': 0.1,
        'order_type': 'LIMIT',
        'price': 1.1000,
        'stop_loss': 1.0950,
        'take_profit': 1.1100,
        'timestamp': datetime.now()
    }


@pytest.fixture
def sample_position() -> Dict[str, Any]:
    """Generate sample position."""
    return {
        'position_id': 'POS_TEST_001',
        'symbol': 'EURUSD',
        'side': 'LONG',
        'quantity': 0.1,
        'entry_price': 1.1000,
        'current_price': 1.1050,
        'unrealized_pnl': 50.0,
        'open_time': datetime.now() - timedelta(hours=2)
    }


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_broker():
    """Create mock broker for testing."""
    broker = MagicMock()
    broker.connect = AsyncMock(return_value=True)
    broker.disconnect = AsyncMock(return_value=True)
    broker.get_account_info = AsyncMock(return_value={
        'balance': 10000.0,
        'equity': 10500.0,
        'margin': 500.0,
        'free_margin': 10000.0
    })
    broker.place_order = AsyncMock(return_value={
        'order_id': 'ORD_001',
        'status': 'FILLED',
        'filled_price': 1.1000,
        'filled_quantity': 0.1
    })
    broker.close_position = AsyncMock(return_value=True)
    broker.get_positions = AsyncMock(return_value=[])
    return broker


@pytest.fixture
def mock_data_feed():
    """Create mock data feed for testing."""
    feed = MagicMock()
    feed.connect = AsyncMock(return_value=True)
    feed.subscribe = AsyncMock(return_value=True)
    feed.get_latest_price = MagicMock(return_value={
        'bid': 1.1000,
        'ask': 1.1002,
        'timestamp': datetime.now()
    })
    return feed


# ============================================================================
# COMPONENT FIXTURES
# ============================================================================

@pytest.fixture
def risk_manager():
    """Create risk manager instance for testing."""
    from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
    return MasterRiskManager(config={'mode': 'paper', 'equity': 10000})


@pytest.fixture
def execution_engine():
    """Create execution engine instance for testing."""
    from trading_bot.execution import ExecutionEngine
    return ExecutionEngine()


@pytest.fixture
def signal_system():
    """Create signal system instance for testing."""
    from trading_bot.signals import CompleteSignalSystem
    return CompleteSignalSystem()


# ============================================================================
# TEST MARKERS
# ============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow tests (>1s)")
    config.addinivalue_line("markers", "requires_mt5: Requires MT5 connection")
    config.addinivalue_line("markers", "requires_api: Requires external API")


# ============================================================================
# TEST UTILITIES
# ============================================================================

@pytest.fixture
def assert_valid_signal():
    """Fixture to validate signal structure."""
    def _validate(signal: Dict[str, Any]) -> bool:
        required_fields = ['signal_id', 'symbol', 'direction', 'confidence']
        return all(field in signal for field in required_fields)
    return _validate


@pytest.fixture
def assert_valid_order():
    """Fixture to validate order structure."""
    def _validate(order: Dict[str, Any]) -> bool:
        required_fields = ['order_id', 'symbol', 'side', 'quantity']
        return all(field in order for field in required_fields)
    return _validate
