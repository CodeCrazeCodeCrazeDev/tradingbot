"""
Provides backward and testing compatibility for MT5-connected modules.
"""

from typing import Any, Optional, Dict, List
import logging
from dataclasses import dataclass

logger = logging.getLogger("AlphaAlgo.MT5Interface")

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
        self.connected = True
        self._connected = True

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self) -> bool:
        self.connected = True
        self._connected = True
        logger.info("MT5Interface: Connected (Mocked mode).")
        return True

    def disconnect(self) -> None:
        self.connected = False
        self._connected = False
        logger.info("MT5Interface: Disconnected.")

    def account_info(self) -> Optional[AccountInfo]:
        return AccountInfo()

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        return SymbolInfo()

    def get_rates(self, symbol: str, timeframe: str, count: int) -> List[Dict[str, Any]]:
        # Dummy rates for testing
        import pandas as pd
        import numpy as np
        dates = pd.date_range(end=pd.Timestamp.now(), periods=count, freq='h')
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
        """Supports positional/keyword or dict-based invocation."""
        if len(args) > 0 and isinstance(args[0], dict):
            request = args[0]
            logger.info(f"MT5Interface: Order placed successfully -> {request}")
            return {
                "retcode": 10009,  # DONE
                "order": 123456,
                "volume": request.get("volume", 0.1),
                "price": request.get("price", 1.0),
                "comment": "Mock trade completed"
            }

        # Otherwise positional/kw args
        order_type = args[0] if len(args) > 0 else kwargs.get("order_type", "buy")
        symbol = args[1] if len(args) > 1 else kwargs.get("symbol", "EURUSD")
        volume = args[2] if len(args) > 2 else kwargs.get("volume", 0.1)
        price = args[3] if len(args) > 3 else kwargs.get("price", None)

        return {
            "order_id": 123456,
            "status": "filled",
            "volume": volume,
            "price": price or 1.1000,
            "symbol": symbol,
            "retcode": 10009,
            "order": 123456,
            "comment": "Mock trade completed"
        }
