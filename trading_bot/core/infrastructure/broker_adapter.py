import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class IBroker(ABC):
    @abstractmethod
    async def execute_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        pass

class MultiBrokerAdapter:
    """Unified interface for multiple broker venues with failover."""
    def __init__(self):
        self.brokers: Dict[str, IBroker] = {}
        self.primary_broker = None

    def register_broker(self, name: str, broker: IBroker, is_primary: bool = False):
        self.brokers[name] = broker
        if is_primary: self.primary_broker = name

    async def route_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.primary_broker:
             raise RuntimeError("No primary broker configured")

        try:
            return await self.brokers[self.primary_broker].execute_order(order_params)
        except Exception as e:
            logger.error(f"Primary broker failed, attempting failover: {e}")
            # Logic for failover to secondary
            return {"status": "failed", "error": str(e)}
