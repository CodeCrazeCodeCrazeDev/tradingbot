"""
Multidimensional Research Agent
Specialized agent for discovering and testing cross-domain scientific concepts.
"""

import logging
from typing import Any, Dict, List, Optional
from ..agent_registry import BaseAgent, AgentRole, AgentCapability, AgentStatus
from .orchestrator import MultidimensionalIntelligenceLayer
from .base import IntelligenceDomain

logger = logging.getLogger(__name__)

class MultidimensionalResearchAgent(BaseAgent):
    """
    Multidimensional Research Agent
    Discovers new cross-domain concepts and manages the scientific self-improvement loop.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="MultidimensionalResearchAgent",
            role=AgentRole.RESEARCHER,
            config=config
        )
        self.intelligence_layer = MultidimensionalIntelligenceLayer(config)

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="cross_domain_research",
            description="Discover and model cross-domain scientific concepts for trading",
            input_schema={"market_context": "Dict"},
            output_schema={"discoveries": "List[Dict]"}
        ))
        self.add_capability(AgentCapability(
            name="hypothesis_generation",
            description="Generate scientific hypotheses based on Biology, Physics, Chemistry, Math, and Nature",
            input_schema={"domain": "str", "context": "Dict"},
            output_schema={"hypotheses": "List[Dict]"}
        ))
        self.add_capability(AgentCapability(
            name="scientific_improvement",
            description="Run the full scientific self-improvement cycle",
            input_schema={"market_data": "Dict"},
            output_schema={"improvements": "List[Dict]"}
        ))

    async def initialize(self):
        """Initialize agent and intelligence layer."""
        await super().initialize()
        await self.intelligence_layer.initialize()

        # Import modules and register them
        from .modules.biology import BiologyModule
        from .modules.physics import PhysicsModule
        from .modules.chemistry import ChemistryModule
        from .modules.mathematics import MathematicsModule
        from .modules.nature import NatureModule

        self.intelligence_layer.register_module(BiologyModule(self.config))
        self.intelligence_layer.register_module(PhysicsModule(self.config))
        self.intelligence_layer.register_module(ChemistryModule(self.config))
        self.intelligence_layer.register_module(MathematicsModule(self.config))
        self.intelligence_layer.register_module(NatureModule(self.config))

        logger.info("Multidimensional Research Agent fully initialized with all modules")

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multidimensional research actions."""
        operation = action.get('operation', 'research')

        if operation == 'research' or operation == 'scientific_improvement':
            market_context = action.get('context', {}) or action.get('data', {})
            await self.intelligence_layer.run_improvement_cycle(market_context)

            status = self.intelligence_layer.get_status()
            return {
                "success": True,
                "result": f"Completed multidimensional improvement cycle. Validated insights: {status['validated_insights']}",
                "status": status,
                "knowledge_graph": self.intelligence_layer.memory.knowledge_graph
            }

        elif operation == 'generate_hypotheses':
            market_context = action.get('context', {})
            hypotheses = await self.intelligence_layer.process_market_context(market_context)
            return {
                "success": True,
                "hypotheses": [h.__dict__ for h in hypotheses]
            }

        return {"success": False, "error": f"Unknown operation: {operation}"}

    def get_status(self) -> Dict[str, Any]:
        """Override status to include intelligence layer stats."""
        base_status = super().get_status()
        base_status['intelligence_layer'] = self.intelligence_layer.get_status()
        return base_status
