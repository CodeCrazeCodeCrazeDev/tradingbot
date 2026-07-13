"""
Tests for multi_agent_rl in advanced_analysis

This tests the Multi-Agent Reinforcement Learning system.
"""

import pytest
import numpy as np
from trading_bot.advanced_features.multi_agent_rl import (
    AgentType, TradingDecision, MarketState, MultiAgentTradingSystem
)

class TestAgentType:
    """Tests for AgentType"""

    def test_values(self):
        """Test AgentType enum values"""
        assert AgentType.MACRO_STRATEGIST.value == "macro_strategist"
        assert AgentType.TACTICAL_EXECUTIONER.value == "tactical_executioner"
        assert AgentType.RISK_SENTINEL.value == "risk_sentinel"
        assert AgentType.HEAD_AI.value == "head_ai"

class TestMultiAgentTradingSystem:
    """Tests for MultiAgentTradingSystem"""

    def test_initialization(self):
        """Test system initialization"""
        system = MultiAgentTradingSystem()
        assert system.macro_strategist is not None
        assert system.tactical_executioner is not None
        assert system.risk_sentinel is not None
        assert system.head_ai is not None

    def test_analyze_and_decide(self):
        """Test the full analysis and decision cycle"""
        system = MultiAgentTradingSystem()
        market_state = MarketState(
            price=1.1000,
            volume=10000.0,
            volatility=0.015,
            trend_direction='up',
            support_levels=[1.0950, 1.0900],
            resistance_levels=[1.1050, 1.1100],
            liquidity_zones=[{'level': 1.0980, 'strength': 0.8}],
            market_regime='trending',
            correlation_data={}
        )

        decision = system.analyze_and_decide(market_state)

        assert isinstance(decision, TradingDecision)
        assert decision.agent_type == AgentType.HEAD_AI
        assert decision.action in ['buy', 'sell', 'hold']
        assert 0 <= decision.confidence <= 1.0
        assert len(system.decision_history) == 1

    def test_risk_override(self):
        """Test that Risk Sentinel can override decisions"""
        system = MultiAgentTradingSystem()
        # High volatility should trigger Risk Sentinel's high risk assessment
        market_state = MarketState(
            price=1.1000,
            volume=10000.0,
            volatility=0.9,  # Extremely high volatility
            trend_direction='up',
            support_levels=[1.0950],
            resistance_levels=[1.1050],
            liquidity_zones=[],
            market_regime='volatile',
            correlation_data={}
        )

        decision = system.analyze_and_decide(market_state)

        # If risk_assessment > 0.8, HeadAI should force 'hold'
        assert decision.action == 'hold'
        assert "RISK OVERRIDE" in decision.reasoning
