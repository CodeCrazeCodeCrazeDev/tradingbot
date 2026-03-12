"""
Trading package for AlphaAlgo 2.0
"""

from .position_manager import PositionManager
from .order_execution import SmartExecutionEngine, OrderType

# Alias for compatibility
OrderExecutionManager = SmartExecutionEngine

try:
    from .order_fill_tracker import OrderFillTracker, FillStatus
    from .risk_calculator import RiskCalculator
    __all__ = [
        'PositionManager',
        'SmartExecutionEngine',
        'OrderExecutionManager',
        'OrderType',
        'OrderFillTracker',
        'FillStatus',
        'RiskCalculator'
    ]
except ImportError:
    __all__ = ['PositionManager', 'SmartExecutionEngine', 'OrderExecutionManager', 'OrderType']
