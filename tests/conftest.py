"""Pytest configuration and fixtures for trading bot tests."""

# Suppress TensorFlow and other deprecation warnings before imports
import warnings
import os

# Suppress TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Filter deprecation warnings from dependencies
warnings.filterwarnings('ignore', category=DeprecationWarning, module='tensorflow.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='tf_keras.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='keras.*')
warnings.filterwarnings('ignore', category=FutureWarning, module='sklearn.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='numpy.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='pandas.*')
warnings.filterwarnings('ignore', category=UserWarning, module='faiss.*')
warnings.filterwarnings('ignore', message='.*deprecated.*')
warnings.filterwarnings('ignore', message='.*will be removed.*')

import pytest
import asyncio
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def broker_config() -> Dict[str, Any]:
    """Provide broker configuration for tests."""
    return {
        'login': 97224465,
        'password': 'test_password',
        'server': 'MetaQuotes-Demo',
        'path': '',
        'mode': 'paper',
        'symbol': 'EURUSD',
        'timeframe': 'H1',
        'magic_number': 123456,
        'initial_balance': 10000.0
    }


@pytest.fixture
def mock_broker_config() -> Dict[str, Any]:
    pass
    """Provide mock broker configuration for tests."""
    return {
        'type': 'mock',
        'initial_balance': 10000.0,
        'leverage': 100,
        'commission': 0.0001
    }


@pytest.fixture
def position_sizer_config() -> Dict[str, Any]:
    pass
    """Provide position sizer configuration for tests."""
    return {
        'default_risk_pct': 0.02,
        'max_position_size': 1000000,
        'min_position_size': 1000,
        'default_kelly_fraction': 0.25
    }


@pytest.fixture
def fill_tracker_config() -> Dict[str, Any]:
    pass
    """Provide fill tracker configuration for tests."""
    return {
        'confirmation_timeout': 30,
        'max_retries': 3,
        'retry_delay': 1,
        'max_slippage_history': 1000
    }


@pytest.fixture
def correlation_config() -> Dict[str, Any]:
    pass
    """Provide correlation manager configuration for tests."""
    return {
        'max_history_length': 100,
        'auto_save_interval': 300,
        'max_state_age_hours': 24
    }


@pytest.fixture
def health_check_config() -> Dict[str, Any]:
    pass
    """Provide health check configuration for tests."""
    return {
        'check_interval': 30,
        'startup_grace_period': 0,  # No grace period for tests
        'max_component_age': 300
    }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_price_data():
    """Provide sample price data for tests."""
    return {
        'EURUSD': [1.1000 + i * 0.0001 for i in range(100)],
        'GBPUSD': [1.3000 + i * 0.00015 for i in range(100)],
        'USDJPY': [110.00 + i * 0.01 for i in range(100)]
    }


@pytest.fixture
def sample_ohlcv_data():
    """Provide sample OHLCV data for tests."""
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    data = pd.DataFrame({
        'open': np.random.uniform(1.0900, 1.1100, 100),
        'high': np.random.uniform(1.0950, 1.1150, 100),
        'low': np.random.uniform(1.0850, 1.1050, 100),
        'close': np.random.uniform(1.0900, 1.1100, 100),
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    return data


@pytest.fixture
async def mock_broker():
    """Create a mock broker instance for tests."""
    from trading_bot.brokers import MockBrokerAdapter
    
    broker = MockBrokerAdapter({'initial_balance': 10000})
    await broker.connect()
    yield broker
    await broker.disconnect()


@pytest.fixture
def mock_database():
    """Create a mock database for tests."""
    from trading_bot.persistence.database_initializer import InMemoryTimeSeriesDB
    return InMemoryTimeSeriesDB({})


@pytest.fixture
def sample_trade_data():
    """Provide sample trade data for tests."""
    return {
        'symbol': 'EURUSD',
        'side': 'buy',
        'quantity': 100000,
        'entry_price': 1.1000,
        'stop_loss': 1.0950,
        'take_profit': 1.1100,
        'timestamp': datetime.now()
    }


@pytest.fixture
def sample_signal():
    """Provide sample trading signal for tests."""
    return {
        'signal_id': 'test_signal_001',
        'symbol': 'EURUSD',
        'direction': 'buy',
        'confidence': 0.75,
        'price': 1.1000,
        'timestamp': datetime.now(),
        'indicators': {
            'rsi': 45,
            'macd': 0.0005,
            'atr': 0.0015
        }
    }


# Pytest hooks
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "critical: mark test as critical for production"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # Add unit marker to all tests by default
        if not any(marker.name in ['integration', 'end_to_end'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
