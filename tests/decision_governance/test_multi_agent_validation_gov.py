"""
Tests for decision governance multi_agent_validation
"""

import pytest
from trading_bot.decision_governance.multi_agent_validation import (
    MultiAgentValidationSystem, AgentType
)

def test_multi_agent_validation():
    system = MultiAgentValidationSystem()
    signal = {'direction': 'buy', 'confidence': 0.8, 'size': 1.0}
    symbol = 'AAPL'
    market_data = {
        'price': 150.0,
        'ma_50': 140.0,
        'ma_200': 130.0,
        'rsi': 55.0,
        'volatility': 0.2,
        'z_score': 2.5,
        'momentum': 0.5,
        'sentiment': 0.6,
        'volume': 1000000,
        'avg_volume': 800000,
        'spread_bps': 5
    }

    consensus = system.validate_signal(signal, symbol, market_data)
    assert consensus is not None
    assert consensus.overall_approved is True
    assert consensus.approval_rate >= 0.7
    assert len(consensus.agent_validations) == 5
