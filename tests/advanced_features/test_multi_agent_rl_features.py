"""Tests for multi_agent_rl in advanced_features."""

from trading_bot.advanced_features.multi_agent_rl import (
    AgentType,
    MacroStrategist,
    MarketState,
    MultiAgentTradingSystem,
    RiskSentinel,
    TacticalExecutioner,
    TradingDecision,
)

class TestAgentComponents:
    """Tests for individual agent components"""

    def test_values(self):
        """Test AgentType values"""
        assert AgentType.MACRO_STRATEGIST.value == "macro_strategist"
        assert AgentType.HEAD_AI.value == "head_ai"

    def test_macro_strategist(self):
        agent = MacroStrategist()
        assert agent.agent_type == AgentType.MACRO_STRATEGIST
        assert agent.input_dim == 60

    def test_tactical_executioner(self):
        agent = TacticalExecutioner()
        assert agent.agent_type == AgentType.TACTICAL_EXECUTIONER
        assert agent.input_dim == 80

    def test_initialization(self):
        """Test TradingDecision initialization"""
        decision = TradingDecision(
            agent_type=AgentType.MACRO_STRATEGIST,
            action="buy",
            confidence=0.85,
            reasoning="Strong trend",
            risk_assessment=0.2,
            expected_return=0.05,
            time_horizon="long",
            supporting_data={}
        )
        assert decision.agent_type == AgentType.MACRO_STRATEGIST
        assert decision.action == "buy"

    def test_risk_sentinel(self):
        agent = RiskSentinel()
        assert agent.agent_type == AgentType.RISK_SENTINEL
        assert agent.input_dim == 40

class TestSystemMetrics:
    """Tests for system performance metrics"""

    def test_initialization(self):
        """Test MarketState initialization"""
        state = MarketState(
            price=1.1000,
            volume=10000.0,
            volatility=0.015,
            trend_direction="up",
            support_levels=[1.0900],
            resistance_levels=[1.1100],
            liquidity_zones=[],
            market_regime="trending",
            correlation_data={}
        )
        assert state.price == 1.1000
        assert state.trend_direction == "up"

    def test_get_system_status(self):
        system = MultiAgentTradingSystem()
        status = system.get_system_status()
        assert status['system_health'] == 'operational'
        assert status['total_decisions'] == 0
        assert 'recent_performance' in status

class TestAgents:
    """Tests for specialized agents"""

    def test_macro_strategist(self):
        """Test MacroStrategist initialization and reasoning"""
        agent = MacroStrategist()
        state = MarketState(
            price=1.1000, volume=1000.0, volatility=0.01, trend_direction="up",
            support_levels=[], resistance_levels=[], liquidity_zones=[],
            market_regime="trending", correlation_data={}
        )
        reasoning = agent._generate_reasoning(state, "buy")
        assert "MACRO BUY" in reasoning
        assert "trending" in reasoning

    def test_tactical_executioner(self):
        """Test TacticalExecutioner initialization and reasoning"""
        agent = TacticalExecutioner()
        state = MarketState(
            price=1.1000, volume=6000.0, volatility=0.01, trend_direction="up",
            support_levels=[], resistance_levels=[], liquidity_zones=[{}, {}],
            market_regime="trending", correlation_data={}
        )
        reasoning = agent._generate_reasoning(state, "sell")
        assert "TACTICAL SELL" in reasoning
        assert "High" in reasoning # Volume > 5000

    def test_risk_sentinel(self):
        """Test RiskSentinel initialization and reasoning"""
        agent = RiskSentinel()
        state = MarketState(
            price=1.1000, volume=1000.0, volatility=0.04, trend_direction="up",
            support_levels=[], resistance_levels=[], liquidity_zones=[],
            market_regime="trending", correlation_data={}
        )
        reasoning = agent._generate_reasoning(state, "sell")
        assert "RISK FORCE SELL" in reasoning
        assert "High" in reasoning # Volatility > 0.03

class TestMultiAgentTradingSystem:
    """Tests for the full Multi-Agent system"""

    def test_system_decision(self):
        """Test that the system can produce a consensus decision"""
        system = MultiAgentTradingSystem()
        state = MarketState(
            price=1.1000, volume=5000.0, volatility=0.01, trend_direction="up",
            support_levels=[1.0900], resistance_levels=[1.1100],
            liquidity_zones=[{'price': 1.0950}], market_regime="trending",
            correlation_data={}
        )

        # This will test HeadAI.make_consensus_decision as well
        decision = system.analyze_and_decide(state)

        assert decision.agent_type == AgentType.HEAD_AI
        assert decision.action in ['buy', 'sell', 'hold']
        assert "CONSENSUS" in decision.reasoning
