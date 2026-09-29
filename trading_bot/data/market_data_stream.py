"""Compatibility shim — canonical implementation lives in connectivity."""
from trading_bot.connectivity.market_data_stream import (
    MarketDataStream,
    MarketTick,
    StreamStatus,
)

__all__ = ["MarketDataStream", "MarketTick", "StreamStatus"]
