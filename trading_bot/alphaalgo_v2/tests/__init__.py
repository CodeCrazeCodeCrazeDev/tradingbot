"""
Tests Module
============================================================

Auto-generated integration file.
"""

# test_execution
try:
    from .test_execution import (
        TestExecutionEngine,
    )
except ImportError as e:
    # test_execution not available
    pass

# test_integration
try:
    from .test_integration import (
        TestAlphaAlgoOrchestrator,
    )
except ImportError as e:
    # test_integration not available
    pass

# test_risk
try:
    from .test_risk import (
        TestPortfolioRiskManager,
        TestRiskEngine,
    )
except ImportError as e:
    # test_risk not available
    pass

__all__ = [
    'TestAlphaAlgoOrchestrator',
    'TestExecutionEngine',
    'TestPortfolioRiskManager',
    'TestRiskEngine',
]
