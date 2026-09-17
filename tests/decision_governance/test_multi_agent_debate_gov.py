"""
Tests for decision governance multi_agent_debate
"""

import pytest
import asyncio
from trading_bot.decision_governance.multi_agent_debate import (
    create_debate_system, DebateRole, DebateStatus
)

@pytest.mark.asyncio
async def test_governance_debate():
    system = create_debate_system(max_rounds=3)
    context = {
        'symbol': 'AAPL',
        'confidence': 0.8,
        'volatility': 0.2,
        'regime': 'trending',
        'backtest_results': 'Positive expectancy'
    }

    debate_id = await system.initiate_debate(context)
    assert debate_id is not None

    result = await system.conduct_debate(debate_id)
    assert result is not None
    assert result.status in [DebateStatus.CONSENSUS, DebateStatus.ARBITRATED]
    assert result.rounds_conducted <= 3
    assert len(result.audit_trail) > 0
