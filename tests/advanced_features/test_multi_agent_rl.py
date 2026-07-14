"""
Tests for multi_agent_rl in advanced_features

This tests the Multi-Agent Reinforcement Learning system.
"""

import pytest
from trading_bot.advanced_features.multi_agent_rl import (
    AgentType, TradingDecision, MarketState, MultiAgentTradingSystem,
    MacroStrategist, TacticalExecutioner, RiskSentinel
)

class TestAgentComponents:
    """Tests for individual agent components"""

    def test_macro_strategist(self):
        agent = MacroStrategist()
        assert agent.agent_type == AgentType.MACRO_STRATEGIST
        assert agent.input_dim == 60

    def test_tactical_executioner(self):
        agent = TacticalExecutioner()
        assert agent.agent_type == AgentType.TACTICAL_EXECUTIONER
        assert agent.input_dim == 80

    def test_risk_sentinel(self):
        agent = RiskSentinel()
        assert agent.agent_type == AgentType.RISK_SENTINEL
        assert agent.input_dim == 40

class TestSystemMetrics:
    """Tests for system performance metrics"""

    def test_get_system_status(self):
        system = MultiAgentTradingSystem()
        status = system.get_system_status()
        assert status['system_health'] == 'operational'
        assert status['total_decisions'] == 0
        assert 'recent_performance' in status
