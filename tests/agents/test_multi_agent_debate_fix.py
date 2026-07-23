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

    @pytest.mark.asyncio
    async def test_agent_failure_resilience(self):
        """Test that the system degrades gracefully when an agent raises an exception"""
        system = MultiAgentDebateSystem()

        # Patch macro_strategist.analyze to raise an exception
        system.macro_strategist.analyze = MagicMock(side_effect=ValueError("Simulated Agent Failure"))

        context = MarketContext(
            symbol="EURUSD", current_price=1.1, htf_trend="UP", ltf_trend="UP",
            volatility=0.01, volume_ratio=1.0, key_levels={}, news_sentiment=0.0,
            portfolio_exposure=0.0, correlation_risk=0.0
        )

        # The debate should still run successfully and produce a decision (by falling back to the remaining agents)
        decision = await system.debate(context)
        assert decision is not None
        assert decision.action in [TradeAction.BUY, TradeAction.STRONG_BUY, TradeAction.HOLD]
        assert "macro_strategist" not in decision.agent_votes

    @pytest.mark.asyncio
    async def test_debate_determinism(self):
        """Test that identical inputs to the debate system yield identical decisions"""
        system1 = MultiAgentDebateSystem()
        system2 = MultiAgentDebateSystem()

        context = MarketContext(
            symbol="EURUSD", current_price=1.1000, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.3, key_levels={"support": [1.0950]},
            news_sentiment=0.4, portfolio_exposure=0.25, correlation_risk=0.3, vix_level=18.0
        )

        decision1 = await system1.debate(context)
        decision2 = await system2.debate(context)

        assert decision1.action == decision2.action
        assert decision1.confidence == pytest.approx(decision2.confidence)
        assert decision1.position_size_pct == pytest.approx(decision2.position_size_pct)
        assert decision1.agent_votes == decision2.agent_votes

    def test_agent_state_isolation(self):
        """Test that agents maintain strict state isolation and do not share mutable state"""
        system = MultiAgentDebateSystem()

        # Ensure separate config dictionaries
        assert system.macro_strategist.config is not system.tactical_executioner.config
        assert system.macro_strategist.config is not system.risk_sentinel.config

        # Check weights are isolated
        system.macro_strategist.weight = 2.0
        assert system.tactical_executioner.weight == 1.0
        assert system.risk_sentinel.weight == 1.0

    @pytest.mark.asyncio
    async def test_multi_agent_debate_scaling_performance(self):
        """Measure performance and verify latency characteristics under scaling simulation"""
        import time
        system = MultiAgentDebateSystem()

        context = MarketContext(
            symbol="EURUSD", current_price=1.1000, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.3, key_levels={"support": [1.0950]},
            news_sentiment=0.4, portfolio_exposure=0.25, correlation_risk=0.3, vix_level=18.0
        )

        # Run 50 sequential debates to measure latency characteristics and throughput
        start_time = time.perf_counter()
        iterations = 50
        for _ in range(iterations):
            await system.debate(context)
        end_time = time.perf_counter()

        total_latency = end_time - start_time
        avg_latency_ms = (total_latency / iterations) * 1000

        print(f"Scaling Performance: {iterations} debates completed in {total_latency:.4f}s (Avg: {avg_latency_ms:.2f}ms/debate)")

        # High-performance threshold assertion (e.g. sub-50ms average)
        assert avg_latency_ms < 50.0
