"""
Smoke Tests for Trading Bot
Fast tests to verify basic system functionality
"""

import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    try:
        import pandas, numpy, MetaTrader5
        return True
    except Exception as e:
        print(f"Import test failed: {e}")
        return False

def test_config():
    try:
        import yaml
        with open('config/config.yaml') as f:
            cfg = yaml.safe_load(f)
        assert 'mt5' in cfg
        return True
    except Exception as e:
        print(f"Config test failed: {e}")
        return False

def test_api():
    try:
        import MetaTrader5 as mt5
        mt5.initialize()
        assert mt5.version() is not None
        mt5.shutdown()
        return True
    except Exception as e:
        print(f"API test failed: {e}")
        return False

@pytest.mark.smoke
@pytest.mark.unit
class TestBasicFunctionality:
    """Pytest-compatible smoke tests."""
    
    def test_critical_imports(self):
        """Test critical imports work."""
        assert test_imports() is True
    
    def test_config_loading(self):
        """Test configuration can be loaded."""
        assert test_config() is True
    
    def test_api_connectivity(self):
        """Test API connectivity."""
        # Skip if MT5 not available
        pytest.importorskip("MetaTrader5")
        assert test_api() is True
    
    def test_python_version(self):
        """Test Python version compatibility."""
        import sys
        assert sys.version_info.major == 3
        assert sys.version_info.minor >= 9


def run_smoke_tests():
    results = [test_imports(), test_config(), test_api()]
    if all(results):
        print("All smoke tests passed.")
        return True
    else:
        print("One or more smoke tests failed.")
        return False

if __name__ == '__main__':
    sys.exit(0 if run_smoke_tests() else 1)
