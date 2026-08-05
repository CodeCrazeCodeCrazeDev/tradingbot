"""
Provides backward and testing compatibility for MT5-connected modules.
"""

from typing import Any, Optional, Dict, List
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AccountInfo:
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    free_margin: float = 10000.0
    margin_level: float = 1000.0
    profit: float = 0.0

@dataclass
class SymbolInfo:
    point: float = 0.00001
    trade_tick_value: float = 1.0
    trade_tick_size: float = 0.00001
    volume_min: float = 0.01
    volume_max: float = 10.0
    volume_step: float = 0.01

class MT5Interface:
    """Institutional-grade MT5Interface stub for testing and system compatibility."""

    def __init__(self, *args, **kwargs):
        self.config = kwargs
        self._connected = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def account_info(self) -> Optional[AccountInfo]:
        return AccountInfo()

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        return SymbolInfo()

    def get_rates(self, symbol: str, timeframe: str, count: int) -> List[Dict[str, Any]]:
        # Dummy rates for testing
        import pandas as pd
        import numpy as np
        dates = pd.date_range(end=pd.Timestamp.now(), periods=count, freq='H')
        return [
            {
                "time": d.to_pydatetime(),
                "open": 1.1000,
                "high": 1.1050,
                "low": 1.0950,
                "close": 1.1000,
                "volume": 5000
            }
            for d in dates
        ]

    def place_order(self, *args, **kwargs) -> Dict[str, Any]:
        volume = 0.1
        price = 1.1000
        symbol = "EURUSD"
        if len(args) > 2:
            volume = args[2]
        if len(args) > 3:
            price = args[3] or price
        if len(args) > 1:
            symbol = args[1]

        # Also support single dictionary argument format: place_order(request_dict)
        if len(args) == 1 and isinstance(args[0], dict):
            req = args[0]
            volume = req.get("volume", volume)
            price = req.get("price", price)
            symbol = req.get("symbol", symbol)
        elif "request" in kwargs and isinstance(kwargs["request"], dict):
            req = kwargs["request"]
            volume = req.get("volume", volume)
            price = req.get("price", price)
            symbol = req.get("symbol", symbol)

        return {
            "order_id": 123456,
            "status": "filled",
            "volume": volume,
            "price": price,
            "symbol": symbol,
            "retcode": 10009,  # DONE
            "order": 123456,
            "comment": "Mock trade completed"
        }
