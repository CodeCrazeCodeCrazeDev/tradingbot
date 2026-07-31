"""
Data management module initialization.
"""

from .validate import DataValidator
from .mt5 import MT5Interface

# Backward-compatibility imports for central data components
try:
    from trading_bot.connectivity.market_data_stream import MarketDataStream
except ImportError:
    # Check fallback or stub
    class MarketDataStream:
        pass

try:
    from trading_bot.database.timeseries_db import TimeSeriesDB
except ImportError:
    class TimeSeriesDB:
        pass

try:
    from trading_bot.database.real_time_processor import RealTimeProcessor
except ImportError:
    class RealTimeProcessor:
        pass

try:
    from trading_bot.database.pipeline_monitor import PipelineMonitor
except ImportError:
    class PipelineMonitor:
        pass

__all__ = [
    "DataValidator",
    "MT5Interface",
    "MarketDataStream",
    "TimeSeriesDB",
    "RealTimeProcessor",
    "PipelineMonitor"
]
