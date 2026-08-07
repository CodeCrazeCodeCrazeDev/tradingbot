"""
Provides backward and testing compatibility for MT5-connected modules.
Provides direct integration or fallback mocks for MT5 and brokers.
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
        config = kwargs.get("config") or {}
        if args and isinstance(args[0], dict):
            config = args[0]
        self.config = config
        self.connected = True

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self) -> bool:
        logger.info("MT5Interface: Connected (Mocked mode).")
        self.connected = True
        return True

    def disconnect(self) -> None:
        logger.info("MT5Interface: Disconnected.")
        self.connected = False

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
        """Supports both single-dictionary requests and legacy multi-positional parameters."""
        request = {}
        if args and isinstance(args[0], dict):
            request = args[0]
        elif "request" in kwargs and isinstance(kwargs["request"], dict):
            request = kwargs["request"]
        else:
            # Handle positional parameters: place_order(self, order_type, symbol, volume, price=None, **kwargs)
            if len(args) >= 1:
                request["order_type"] = args[0]
            if len(args) >= 2:
                request["symbol"] = args[1]
            if len(args) >= 3:
                request["volume"] = args[2]
            if len(args) >= 4:
                request["price"] = args[3]

            # Merge any remaining keyword args
            for k, v in kwargs.items():
                if k not in request:
                    request[k] = v

        volume = request.get("volume", request.get("volume", 0.1))
        price = request.get("price", 1.1000)
        symbol = request.get("symbol", "EURUSD")

        logger.info(f"MT5Interface: Order placed successfully -> {request}")
        return {
            "retcode": 10009,  # DONE
            "order": 123456,
            "order_id": 123456,
            "status": "filled",
            "volume": volume,
            "price": price,
            "symbol": symbol,
            "comment": "Mock trade completed"
        }
