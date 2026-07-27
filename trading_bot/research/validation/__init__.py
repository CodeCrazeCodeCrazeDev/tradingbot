"""
Validation and Backtesting Sub-package for Research OS.
Hosts realistic trade simulators and multi-regime robustness checkers.
"""

from .backtest import RealisticResearchBacktester
from .robustness import RobustnessTester

__all__ = [
    'RealisticResearchBacktester',
    'RobustnessTester'
]
