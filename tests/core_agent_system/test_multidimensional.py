"""
Unit tests for Multidimensional Intelligence system.
"""

import asyncio
import pytest
from datetime import datetime
from trading_bot.core_agent_system.multidimensional_intelligence.orchestrator import MultidimensionalIntelligenceLayer
from trading_bot.core_agent_system.multidimensional_intelligence.agent import MultidimensionalResearchAgent
from trading_bot.core_agent_system.multidimensional_intelligence.base import IntelligenceDomain

@pytest.mark.asyncio
async def test_intelligence_layer_initialization():
    layer = MultidimensionalIntelligenceLayer()
    await layer.initialize()
    status = layer.get_status()
    assert status["total_hypotheses"] == 0
    assert status["validated_insights"] == 0

@pytest.mark.asyncio
async def test_multidimensional_agent_full_cycle():
    agent = MultidimensionalResearchAgent(config={'storage_path': 'test_multidim_data'})
    await agent.initialize()

    # Run scientific improvement cycle
    result = await agent.execute({
        'operation': 'scientific_improvement',
        'context': {'market_trend': 'bullish', 'volatility': 0.015}
    })

    assert result['success'] is True
    assert 'knowledge_graph' in result
    assert result['status']['total_hypotheses'] > 0

    # Since we have mock successes in the orchestrator, we should have validated insights
    assert result['status']['validated_insights'] > 0

@pytest.mark.asyncio
async def test_hypothesis_generation():
    agent = MultidimensionalResearchAgent()
    await agent.initialize()

    hypotheses = await agent.intelligence_layer.process_market_context({'test': True})

    domains = [h.domain for h in hypotheses]
    assert IntelligenceDomain.BIOLOGY in domains
    assert IntelligenceDomain.PHYSICS in domains
    assert IntelligenceDomain.CHEMISTRY in domains
    assert IntelligenceDomain.MATHEMATICS in domains
    assert IntelligenceDomain.NATURE in domains

    assert len(hypotheses) >= 15 # Based on my module implementations

if __name__ == "__main__":
    asyncio.run(test_multidimensional_agent_full_cycle())
