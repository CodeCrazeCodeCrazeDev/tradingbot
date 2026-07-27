"""
Tests for multi_agent_rl (Advanced Analysis)

Aligned with specialized trading personas and consensus decision making.
"""

import pytest
from datetime import datetime
from trading_bot.advanced_analysis.multi_agent_rl import (
    AgentRole, TradeAction, Confidence, AgentArgument,
    ConsensusDecision, MacroStrategist, TacticalExecutioner,
    RiskSentinel, HeadAI, MultiAgentTradingSystem, create_multi_agent_system
)

class TestAgentRole:
    """Tests for AgentRole"""

    def test_values(self):
        """Test AgentRole values"""
        assert AgentRole.MACRO_STRATEGIST.value == "macro_strategist"
        assert AgentRole.TACTICAL_EXECUTIONER.value == "tactical_executioner"
        assert AgentRole.RISK_SENTINEL.value == "risk_sentinel"
        assert AgentRole.HEAD_AI.value == "head_ai"

class TestTradeAction:
    """Tests for TradeAction"""

    def test_values(self):
        """Test TradeAction values"""
        assert TradeAction.STRONG_BUY.value == "strong_buy"
        assert TradeAction.EXIT_ALL.value == "exit_all"

class TestConfidence:
    """Tests for Confidence"""

    def test_values(self):
        """Test Confidence values"""
        assert Confidence.VERY_HIGH.value == 0.9
        assert Confidence.VERY_LOW.value == 0.1

class TestAgentArgument:
    """Tests for AgentArgument"""

    def test_initialization(self):
        """Test AgentArgument initialization"""
        arg = AgentArgument(
            agent=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.BUY,
            confidence=0.8,
            reasoning="Test reasoning",
            supporting_evidence=["Evidence 1"],
            risk_assessment=0.3,
            timeframe="H4"
        )
        assert arg.agent == AgentRole.MACRO_STRATEGIST
        assert arg.confidence == 0.8
        assert "Evidence 1" in arg.supporting_evidence

class TestConsensusDecision:
    """Tests for ConsensusDecision"""

    def test_initialization(self):
        """Test ConsensusDecision initialization"""
        decision = ConsensusDecision(
            action=TradeAction.BUY,
            confidence=0.75,
            position_size_pct=0.02,
            entry_price=1.1000,
            stop_loss=1.0900,
            take_profit=1.1200,
            arguments=[],
            dissenting_views=[],
            reasoning="Consensus reasoning"
        )
        assert decision.action == TradeAction.BUY
        assert decision.position_size_pct == 0.02

class TestMultiAgentTradingSystem:
    """Tests for MultiAgentTradingSystem"""

    def test_system_flow(self):
        """Test the full analysis and decision flow"""
        system = create_multi_agent_system()
        market_data = {
            'prices_htf': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0],
            'prices_ltf': [2.9, 2.95, 3.0],
            'regime': 'trending',
            'trend': 'bullish',
            'order_flow': {'delta': 0.5, 'absorption': 0.6},
            'liquidity': {'above': 100, 'below': 50},
            'portfolio': {'drawdown': 0.02},
            'volatility': {'current': 0.01, 'average': 0.015},
            'correlations': {'max_correlation': 0.4},
            'vix': 15
        }

        decision = system.analyze_and_decide(market_data, current_price=3.0)

        assert decision is not None
        assert isinstance(decision.action, TradeAction)
        assert len(decision.arguments) == 3
