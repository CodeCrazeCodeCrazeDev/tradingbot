"""
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
