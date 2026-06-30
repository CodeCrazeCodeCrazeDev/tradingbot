import logging
from typing import Any, Dict, List, Optional
from .controller import SwarmController
from .models import SwarmConsensus

logger = logging.getLogger(__name__)

class UnifiedSwarmIntelligenceSystem:
    """
    Unified Swarm Intelligence System (USIS)

    The entry point for the hierarchical swarm intelligence.
    Integrates Micro, Expert, and Evolution layers.
    """
    def __init__(self, agent_registry: Any, config: Optional[Dict] = None):
        self.config = config or {}
        self.controller = SwarmController(agent_registry, self.config)

        logger.info("Unified Swarm Intelligence System (USIS) initialized")

    async def analyze(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute swarm analysis for a given task.
        """
        consensus = await self.controller.get_consensus(task, context)

        return {
            'success': True,
            'direction': consensus.direction,
            'confidence': consensus.confidence,
            'dissent_ratio': consensus.dissent_ratio,
            'consensus': consensus.to_dict(),
            'dominant_factors': consensus.dominant_factors,
            'reasoning': f"Swarm consensus reached with {consensus.confidence:.2f} confidence and {consensus.dissent_ratio:.2f} dissent."
        }

    async def update(self, consensus_data: Dict[str, Any], actual_outcome: float, market_context: Dict[str, Any]):
        """
        Update the system with the actual outcome of a decision.
        """
        # Reconstruct consensus object if needed or pass raw data to controller
        # For now, we assume the controller handles the memory update
        pass
