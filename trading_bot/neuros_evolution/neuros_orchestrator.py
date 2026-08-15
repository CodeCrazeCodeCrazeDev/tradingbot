import logging
import warnings
from typing import Dict, Any, Optional
from trading_bot.core.csc.controller import CognitiveSystemController

logger = logging.getLogger(__name__)

class NeurosEvolutionOrchestrator:
    """
    DEPRECATED: Legacy NEUROS Evolution Orchestrator.
    Delegates strategic and evolutionary coordination to CognitiveSystemController.
    """
    def __init__(self, config: Optional[Any] = None):
        warnings.warn(
            "NeurosEvolutionOrchestrator is deprecated and has been consolidated into CognitiveSystemController.",
            DeprecationWarning,
            stacklevel=2
        )
        self.config = config
        self.csc = CognitiveSystemController()
        self.initialized = True
        self.running = False

    async def initialize(self):
        self.initialized = True

    async def start(self):
        self.running = True

    async def stop(self):
        self.running = False

    async def run_research_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        decision = await self.csc.process_market_observation(market_data)
        return {
            "success": decision is not None,
            "decision": str(decision),
            "insights": []
        }

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "initialized": self.initialized,
            "running": self.running,
            "status": "delegated_to_csc"
        }

    def get_performance_report(self) -> Dict[str, Any]:
        return {
            "status": "delegated_to_csc"
        }

def quick_start(config: Optional[Dict[str, Any]] = None) -> NeurosEvolutionOrchestrator:
    return NeurosEvolutionOrchestrator(config)
