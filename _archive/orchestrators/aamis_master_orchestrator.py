import logging
from typing import Any, Dict, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

class AAMISMasterOrchestrator:
    """Compatibility shim for legacy AAMISMasterOrchestrator. Delegates to CSC."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.csc = CognitiveSystemController()
        logger.info("AAMISMasterOrchestrator (Shim) initialized. Routing to CSC.")

    async def initialize(self):
        await self.csc.initialize()

    async def start(self):
        logger.info("AAMISMasterOrchestrator (Shim) started.")

    async def stop(self):
        logger.info("AAMISMasterOrchestrator (Shim) stopped.")

    async def process_task(self, task: str, context: Optional[Dict] = None):
        return await self.csc.execute_task(task, context or {})

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "mode": "shim", "delegated_to": "CSC"}
