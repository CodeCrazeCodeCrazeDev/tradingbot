"""Pytest configuration for orchestrator tests - lightweight version."""

import warnings
import os

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

import pytest
import asyncio
import sys
from pathlib import Path

# Note: pytest_plugins moved to root conftest.py

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest hooks
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "critical: mark test as critical for production"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
