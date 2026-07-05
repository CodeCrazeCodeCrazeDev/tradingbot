"""
Tests for planner_agent
"""

import pytest
from datetime import datetime
from trading_bot.agents.planner_agent import TradeProposal, PlannerAgent

class TestTradeProposal:
    """Tests for TradeProposal"""

    def test_initialization(self):
        """Test TradeProposal initialization"""
        obj = TradeProposal(
            proposal_id="test_1",
            timestamp=datetime.now(),
            symbol="EURUSD",
            action="long",
            lots=0.1,
            reasoning="test",
            confidence=0.8,
            expected_return=100.0,
            expected_risk=50.0,
            stop_loss_pips=50.0,
            take_profit_pips=100.0,
            technical_score=0.8,
            fundamental_score=0.5,
            sentiment_score=0.7,
            forecast_score=0.8,
            market_regime="trending",
            volatility_regime="normal",
            trend_strength=0.8,
            risk_reward_ratio=2.0,
            win_probability=0.6,
            kelly_fraction=0.1
        )
        assert obj is not None
        assert obj.proposal_id == "test_1"

class TestPlannerAgent:
    """Tests for PlannerAgent"""

    def test_initialization(self):
        """Test PlannerAgent initialization"""
        obj = PlannerAgent()
        assert obj is not None
