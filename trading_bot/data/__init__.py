"""
Data management module initialization.
"""

from .validate import DataValidator
from .mt5 import MT5Interface

# Expose additional components for full system and test compatibility
from trading_bot.connectivity.market_data_stream import MarketDataStream
from trading_bot.database.timeseries_db import TimeSeriesDB
from trading_bot.database.real_time_processor import DataProcessor as RealTimeProcessor
from trading_bot.database.pipeline_monitor import PipelineMonitor

__all__ = [
    "DataValidator",
    "MT5Interface",
    "MarketDataStream",
    "TimeSeriesDB",
    "RealTimeProcessor",
    "PipelineMonitor"
]
