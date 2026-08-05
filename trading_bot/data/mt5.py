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

    def place_order(self, order_type: Any = None, symbol: Optional[str] = None, volume: Optional[float] = None, price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        if isinstance(order_type, dict):
            # It's the request dict signature!
            request = order_type
            logger.info(f"MT5Interface: Order placed successfully -> {request}")
            return {
                "retcode": 10009,  # DONE
                "order": 123456,
                "volume": request.get("volume", 0.1),
                "price": request.get("price", 1.0),
                "comment": "Mock trade completed"
            }

        # It's the standard signature!
        return {
            "order_id": 123456,
            "status": "filled",
            "volume": volume,
            "price": price or 1.1000,
            "symbol": symbol
        }
