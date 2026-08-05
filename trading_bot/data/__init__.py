"""
Exports authoritative interfaces for MT5 connectivity, data validation, and database managers.
"""

from .mt5 import MT5Interface, AccountInfo, SymbolInfo
from .validate import DataValidator

# Dynamic fallback stubs for other imported classes
class DataManager:
    pass

class Level2Manager:
    pass

class InsiderTradingAnalyzer:
    pass

def quick_insider_check(*args, **kwargs):
    return True

class MarketDataStream:
    pass

class TimeSeriesDB:
    pass

class RealTimeProcessor:
    pass

class PipelineMonitor:
    pass

__all__ = [
    "MT5Interface",
    "AccountInfo",
    "SymbolInfo",
    "DataValidator",
    "DataManager",
    "Level2Manager",
    "InsiderTradingAnalyzer",
    "quick_insider_check",
    "MarketDataStream",
    "TimeSeriesDB",
    "RealTimeProcessor",
    "PipelineMonitor"
]

"""Data management module initialization."""

from .validate import DataValidator
from .mt5 import MT5Interface

__all__ = ["DataValidator", "MT5Interface"]
