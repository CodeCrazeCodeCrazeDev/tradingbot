"""
MT5 Interface definition to satisfy imports.
"""
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("AlphaAlgo.DataMT5InterfaceStub")

class MT5Interface:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("MT5Interface initialized (stub)")

    def initialize(self) -> bool:
        return True

    def get_rates(self, symbol: str, timeframe: Any, count: int) -> Optional[List[Dict[str, Any]]]:
        # Return mock rates for testing
        return []
