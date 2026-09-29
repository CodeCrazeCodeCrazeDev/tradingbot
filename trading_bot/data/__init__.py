"""
Exports authoritative interfaces for MT5 connectivity, data validation, and database managers.
"""

import importlib as _importlib

# Lazy exports: .mt5 pulls connectivity/aiohttp and .validate/.adapters pull
# pandas — eager import made `trading_bot.data` cost ~14s for every consumer
# that only wanted the normalizer.
_LAZY = {
    "MT5Interface": ".mt5",
    "AccountInfo": ".mt5",
    "SymbolInfo": ".mt5",
    "DataValidator": ".validate",
    "MarketDataNormalizer": ".normalizer",
    "normalize_observation": ".normalizer",
    "LegacyMarketDataAdapter": ".adapters",
}


def __getattr__(name):
    mod = _LAZY.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(_importlib.import_module(mod, __name__), name)

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
    "MarketDataNormalizer",
    "normalize_observation",
    "LegacyMarketDataAdapter",
    "DataManager",
    "Level2Manager",
    "InsiderTradingAnalyzer",
    "quick_insider_check",
    "MarketDataStream",
    "TimeSeriesDB",
    "RealTimeProcessor",
    "PipelineMonitor"
]
