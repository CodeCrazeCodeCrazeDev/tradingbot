"""
MetaTrader 5 (MT5) Integration Interface Stub.
Provides compatibility fallback when running on non-Windows/non-MT5 environments.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MT5Interface:
    """Stub interface for MetaTrader 5 execution."""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        logger.info("MT5Interface stub: Connected successfully")
        return True

    def disconnect(self):
        self.connected = False
        logger.info("MT5Interface stub: Disconnected")

    def execute_order(self, order_proposal: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"MT5Interface stub: Executed order {order_proposal}")
        return {
            "status": "success",
            "order_id": 99999,
            "price": order_proposal.get("price", 1.1000)
        }
