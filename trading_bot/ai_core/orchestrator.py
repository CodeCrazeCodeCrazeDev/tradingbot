import logging
from typing import Any, Dict, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """Compatibility shim for legacy AIOrchestrator. Delegates to CSC."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.csc = CognitiveSystemController()
        logger.info("AIOrchestrator (Shim) initialized. Routing to CSC.")

    async def start(self):
        logger.info("AIOrchestrator (Shim) started.")

    async def stop(self):
        logger.info("AIOrchestrator (Shim) stopped.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "mode": "shim", "delegated_to": "CSC"}
