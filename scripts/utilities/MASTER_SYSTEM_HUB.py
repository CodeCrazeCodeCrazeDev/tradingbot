import logging
from typing import Any, Dict, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

class MasterSystemHub:
    """Compatibility shim for legacy MasterSystemHub. Delegates to CSC."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.csc = CognitiveSystemController()
        logger.info("MasterSystemHub (Shim) initialized. Routing to CSC.")

    async def initialize(self):
        await self.csc.initialize()

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "mode": "shim", "delegated_to": "CSC"}

    def get_component(self, name: str):
        # Delegate to Unified Registry
        from trading_bot.core.unified_registry import registry
        return registry.get(name)
