"""
Tests for multi_agent_debate

Aligned with Hivemind-controlled agent architecture.
"""

import pytest
import asyncio
from datetime import datetime
from trading_bot.agents.multi_agent_debate import (
    AgentRole, Conviction, TradeAction, MarketContext,
    AgentArgument, DebateTopic, MultiAgentDebateSystem,
    create_debate_system
)

class TestAgentRole:
    """Tests for AgentRole"""

    def test_values(self):
        """Test AgentRole values"""
        assert AgentRole.MACRO_STRATEGIST.value == "macro_strategist"
        assert AgentRole.TACTICAL_EXECUTIONER.value == "tactical_executioner"
        assert AgentRole.RISK_SENTINEL.value == "risk_sentinel"
        assert AgentRole.HEAD_AI.value == "head_ai"

class TestConviction:
    """Tests for Conviction"""

    def test_values(self):
        """Test Conviction values"""
        assert Conviction.VERY_LOW.value == 1
        assert Conviction.VERY_HIGH.value == 5

class TestTradeAction:
    """Tests for TradeAction"""

    def test_values(self):
        """Test TradeAction values"""
        assert TradeAction.STRONG_BUY.value == "strong_buy"
        assert TradeAction.NO_TRADE.value == "no_trade"

class TestMarketContext:
    """Tests for MarketContext"""

    def test_initialization(self):
        """Test MarketContext initialization"""
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.015,
            volume_ratio=1.3,
            key_levels={'support': [1.0950], 'resistance': [1.1050]},
            news_sentiment=0.4,
            portfolio_exposure=0.25,
            correlation_risk=0.3
        )
        assert context.symbol == "EURUSD"
        assert context.current_price == 1.1000

class TestMultiAgentDebateSystem:
    """Tests for MultiAgentDebateSystem"""

    @pytest.mark.asyncio
    async def test_debate_execution(self):
        """Test the full debate cycle"""
        system = create_debate_system()
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.015,
            volume_ratio=1.3,
            key_levels={'support': [1.0950], 'resistance': [1.1050]},
            news_sentiment=0.4,
            portfolio_exposure=0.25,
            correlation_risk=0.3,
            vix_level=18.0
        )

        decision = await system.debate(context)

        assert decision is not None
        assert decision.symbol == "EURUSD"
        assert isinstance(decision.action, TradeAction)
        assert 0 <= decision.confidence <= 1.0
        assert decision.debate_rounds >= 1
        assert len(decision.agent_votes) == 3

    @pytest.mark.asyncio
    async def test_debate_with_topic(self):
        """Test debate with a specific topic"""
        system = create_debate_system()
        topic = DebateTopic(id="123", content="Should we buy EURUSD?")
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='DOWN',
            ltf_trend='DOWN',
            volatility=0.02,
            volume_ratio=0.8,
            key_levels={'support': [1.0900], 'resistance': [1.1100]},
            news_sentiment=-0.5,
            portfolio_exposure=0.1,
            correlation_risk=0.2
        )

        decision = await system.debate(topic, context)

        assert decision is not None
        assert decision.action in [TradeAction.SELL, TradeAction.STRONG_SELL, TradeAction.HOLD]

    @pytest.mark.asyncio
    async def test_risk_veto(self):
        """Test that Risk Sentinel can veto aggressive positions"""
        system = create_debate_system()
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.05,  # Extreme volatility
            volume_ratio=1.3,
            key_levels={'support': [1.0950], 'resistance': [1.1050]},
            news_sentiment=0.4,
            portfolio_exposure=0.9,  # High exposure
            correlation_risk=0.8,    # High correlation
            vix_level=45.0           # Extreme VIX
        )

        decision = await system.debate(context)

        assert decision.action == TradeAction.NO_TRADE
        # The reasoning now includes "Decision: NO_TRADE" and the risk sentinel's reasoning
        assert "Decision: NO_TRADE" in decision.reasoning
        assert "exceeds limit" in decision.reasoning or "recommending NO TRADE" in decision.reasoning

    @pytest.mark.asyncio
    async def test_risk_veto_provenance_validation(self):
        """Test that the vetoes list is populated and falsification_report is validated in provenance"""
        system = create_debate_system()
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.05,
            volume_ratio=1.3,
            key_levels={'support': [1.0950], 'resistance': [1.1050]},
            news_sentiment=0.4,
            portfolio_exposure=0.9,
            correlation_risk=0.8,
            vix_level=45.0
        )

        decision = await system.debate(context)

        assert decision.action == TradeAction.NO_TRADE
        # Verify the structure-preserving provenance schema
        assert 'schema_version' in decision.provenance
        assert decision.provenance['schema_version'] == "1.0.0"
        assert 'falsification_report' in decision.provenance
        assert isinstance(decision.provenance['falsification_report'], dict)
        assert 'is_falsified' in decision.provenance['falsification_report']
