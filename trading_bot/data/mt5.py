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

    def place_order(self, order_type: str, symbol: str, volume: float, price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        return {
            "order_id": 123456,
            "status": "filled",
            "volume": volume,
            "price": price or 1.1000,
            "symbol": symbol
MT5Interface class.
Provides direct integration or fallback mocks for MT5 and brokers.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AlphaAlgo.MT5Interface")

class MT5Interface:
    """Interacts with MetaTrader 5 terminal or provides standard mock wrappers when offline."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self) -> bool:
        logger.info("MT5Interface: Connected (Mocked mode).")
        self.connected = True
        return True

    def disconnect(self):
        logger.info("MT5Interface: Disconnected.")
        self.connected = False

    def place_order(self, request: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"MT5Interface: Order placed successfully -> {request}")
        return {
            "retcode": 10009,  # DONE
            "order": 123456,
            "volume": request.get("volume", 0.1),
            "price": request.get("price", 1.0),
            "comment": "Mock trade completed"
        }
