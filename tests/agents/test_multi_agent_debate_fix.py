"""
Tests for Multi-Agent Debate System Fixes

Verifies:
1. Double-counting prevention (only latest argument per agent used)
2. ConfidenceCalibrator integration (Bayesian calibration applied)
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch
from trading_bot.agents.multi_agent_debate import (
    AgentRole, Conviction, TradeAction, MarketContext,
    AgentArgument, DebateRound, HeadAI, MultiAgentDebateSystem
)
from trading_bot.verification.confidence_calibrator import CalibrationResult, CalibrationMethod

class TestMultiAgentDebateFixes:
    """Tests for Multi-Agent Debate System fixes"""

    def test_double_counting_fix(self):
        """Test that only the latest argument from each agent is used"""
        # Create mock HeadAI
        head_ai = HeadAI()

        context = MarketContext(
            symbol="EURUSD", current_price=1.1, htf_trend="UP", ltf_trend="UP",
            volatility=0.01, volume_ratio=1.0, key_levels={}, news_sentiment=0.0,
            portfolio_exposure=0.0, correlation_risk=0.0
        )

        # Round 1 arguments
        arg1_v1 = AgentArgument(
            agent_role=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.BUY,
            conviction=Conviction.HIGH,
            reasoning=["Macro Buy"],
            key_factors={},
            confidence=0.8,
            timestamp=datetime.now()
        )

        # Round 2 arguments (Macro Strategist changes mind)
        arg1_v2 = AgentArgument(
            agent_role=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.SELL,
            conviction=Conviction.HIGH,
            reasoning=["Macro Sell"],
            key_factors={},
            confidence=0.9,
            timestamp=datetime.now()
        )

        arguments = [arg1_v1, arg1_v2]

        # Synthesize decision
        decision = head_ai.synthesize_decision(arguments, context, [])

        # Only arg1_v2 should be counted. If arg1_v1 was counted, there might be a conflict or different confidence.
        # Given only one agent (effectively), action should be SELL.
        assert decision.action == TradeAction.SELL
        assert "macro_strategist" in decision.agent_votes
        assert decision.agent_votes["macro_strategist"] == TradeAction.SELL.value

        # Ensure only 1 vote recorded
        assert len(decision.agent_votes) == 1

    @pytest.mark.asyncio
    async def test_confidence_calibration_integration(self):
        """Test that ConfidenceCalibrator is called and its result is used"""
        # Create mock calibrator
        mock_calibrator = MagicMock()
        mock_calibrator.calibrate.return_value = CalibrationResult(
            original_confidence=0.8,
            calibrated_confidence=0.5, # Significant reduction
            calibration_method=CalibrationMethod.BAYESIAN,
            calibration_status="overconfident",
            calibration_error=0.3,
            historical_accuracy_at_confidence=0.5,
            adjustment_factor=0.625,
            uncertainty_bounds=(0.4, 0.6),
            recommendations=[]
        )

        # Initialize HeadAI with mock calibrator
        head_ai = HeadAI(calibrator=mock_calibrator)

        context = MarketContext(
            symbol="EURUSD", current_price=1.1, htf_trend="UP", ltf_trend="UP",
            volatility=0.01, volume_ratio=1.0, key_levels={}, news_sentiment=0.0,
            portfolio_exposure=0.0, correlation_risk=0.0
        )

        arg = AgentArgument(
            agent_role=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.BUY,
            conviction=Conviction.HIGH,
            reasoning=["Macro Buy"],
            key_factors={},
            confidence=0.8,
            timestamp=datetime.now()
        )

        decision = head_ai.synthesize_decision([arg], context, [])

        # Verify calibrator was called
        mock_calibrator.calibrate.assert_called()

        # The winning_score (confidence) in FinalDecision is the aggregate score.
        # score = weight (0.35) * conviction_mult (4/5 = 0.8) * calibrated_confidence (0.5)
        # score = 0.35 * 0.8 * 0.5 = 0.14

        assert decision.confidence == pytest.approx(0.14)

    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test that MultiAgentDebateSystem initializes with a calibrator"""
        system = MultiAgentDebateSystem()
        assert system.calibrator is not None
        assert system.head_ai.calibrator == system.calibrator
