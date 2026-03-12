"""
testing package
"""

try:
    from .continuous_validation import (
        BlackSwanEvent,
        BlackSwanScenario,
        BlackSwanSimulator,
        ContinuousBacktester,
        ContinuousValidationSystem,
        FailureMode,
        FailureModeSimulator,
        FailureScenario,
        MonteCarloSimulator,
        TestMode,
        TestResult
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in testing: {e}')

__all__ = [
    'BlackSwanEvent',
    'BlackSwanScenario',
    'BlackSwanSimulator',
    'ContinuousBacktester',
    'ContinuousValidationSystem',
    'FailureMode',
    'FailureModeSimulator',
    'FailureScenario',
    'MonteCarloSimulator',
    'TestMode',
    'TestResult',
]