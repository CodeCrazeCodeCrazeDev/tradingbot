import asyncio
import logging
from trading_bot.core_agent_system.swarm.controller import SwarmController
from trading_bot.core_agent_system.swarm.models import SwarmConsensus, SwarmSignal, SwarmLayer
from trading_bot.core_agent_system.agent_registry import AgentRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SwarmVetoTest")

class MockRiskAgent:
    def __init__(self):
        self.role = 'safety'
        self.agent_id = 'risk_veto_agent'
    async def execute(self, action):
        logger.info(f"Risk Agent checking consensus: {action['consensus']['direction']}")
        # Veto if direction is bullish (test case)
        if action['consensus']['direction'] > 0:
             return {'success': True, 'is_safe': False}
        return {'success': True, 'is_safe': True}

async def test_swarm_veto():
    registry = AgentRegistry()
    risk_agent = MockRiskAgent()
    # Mock get_agents_by_role
    registry.get_agents_by_role = lambda role: [risk_agent] if role == 'safety' else []

    controller = SwarmController(registry)

    # Create a mock bullish consensus
    consensus = SwarmConsensus(
        direction=1.0,
        confidence=0.8,
        dissent_ratio=0.1,
        contributing_signals=[SwarmSignal("s1", SwarmLayer.EXPERT, 1.0, 0.8)],
        dominant_factors=["s1"]
    )

    logger.info("Running Risk Validation on Bullish Consensus (Expected Veto)")
    safe_consensus = await controller._validate_risk(consensus, {})

    print(f"Safe Consensus Direction: {safe_consensus.direction}")
    assert safe_consensus.direction == 0.0
    logger.info("✅ Veto logic verified.")

if __name__ == "__main__":
    asyncio.run(test_swarm_veto())
