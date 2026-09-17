import logging
from typing import Any, Dict, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

class MOSEFSOrchestrator:
    """Compatibility shim for legacy MOSEFSOrchestrator. Delegates to CSC."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.csc = CognitiveSystemController()
        logger.info("MOSEFSOrchestrator (Shim) initialized. Routing to CSC.")

    async def initialize(self):
        await self.csc.initialize()

    async def start(self):
        logger.info("MOSEFSOrchestrator (Shim) started.")

    async def stop(self):
        logger.info("MOSEFSOrchestrator (Shim) stopped.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "mode": "shim", "delegated_to": "CSC"}

def create_mosefs(config: Optional[Any] = None) -> MOSEFSOrchestrator:
    return MOSEFSOrchestrator(config)

async def quick_start(config: Optional[Any] = None) -> MOSEFSOrchestrator:
    orch = create_mosefs(config)
    await orch.start()
    return orch
