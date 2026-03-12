"""
Standalone test runner for orchestrator tests
Avoids heavy imports from main trading_bot package
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to skip heavy imports
os.environ['SKIP_HEAVY_IMPORTS'] = '1'

import pytest
from typing import Set

if __name__ == "__main__":
    # Run orchestrator tests
    test_files = [
        "tests/test_orchestrator_master.py",
        "tests/test_orchestrator_execution.py",
        "tests/test_orchestrator_ml_predictor.py",
        "tests/test_orchestrator_risk_manager.py",
        "tests/test_orchestrator_performance.py",
        "tests/test_orchestrator_integration.py"
    ]
    
    # Run with verbose output
    exit_code = pytest.main(["-v", "--tb=short", "--timeout=120"] + test_files)
    sys.exit(exit_code)
