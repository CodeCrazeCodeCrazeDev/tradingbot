import logging
from typing import Any, Dict, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

# self_discovery_engine
try:
    from .self_discovery_engine import (
        SelfDiscoveryEngine,
    )
except ImportError as e:
    SelfDiscoveryEngine = None

# superpowerful_orchestrator
try:
    from .superpowerful_orchestrator import (
        SuperPowerfulAI,
    )
except ImportError as e:
    SuperPowerfulAI = None

__all__ = [
    'SelfDiscoveryEngine',
    'SuperPowerfulAI',
    'SuperpowerfulOrchestrator',
]

class SuperpowerfulOrchestrator:
    """Compatibility shim for legacy SuperpowerfulOrchestrator. Delegates to CSC."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.csc = CognitiveSystemController()
        logger.info("SuperpowerfulOrchestrator (Shim) initialized. Routing to CSC.")

    async def start(self):
        logger.info("SuperpowerfulOrchestrator (Shim) started.")

    async def stop(self):
        logger.info("SuperpowerfulOrchestrator (Shim) stopped.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "mode": "shim", "delegated_to": "CSC"}
