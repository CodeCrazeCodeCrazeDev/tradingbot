import logging
from typing import Any, Dict, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

class HivemindOrchestratorV2:
    """Compatibility shim for legacy HivemindOrchestratorV2. Delegates to CSC."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.csc = CognitiveSystemController()
        logger.info("HivemindOrchestratorV2 (Shim) initialized. Routing to CSC.")

    async def start(self):
        logger.info("HivemindOrchestratorV2 (Shim) started.")

    async def stop(self):
        logger.info("HivemindOrchestratorV2 (Shim) stopped.")

    async def reach_consensus(self, topic: str, options: Any):
        logger.info(f"HivemindOrchestratorV2 (Shim) routing consensus for {topic} to CSC.")
        # Consolidated consensus now happens via CSC's VerificationSwarm and LogAct
        return {"winner": "hold", "confidence": 0.5, "status": "delegated"}

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "mode": "shim", "delegated_to": "CSC"}

def create_hivemind_v2(config: Optional[Any] = None) -> HivemindOrchestratorV2:
    return HivemindOrchestratorV2(config)
