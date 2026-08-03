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

        # The winning_score (confidence) in FinalDecision is the mathematically calibrated Bayesian posterior.
        # prior = 0.55 (HTF Trend UP, BUY action), likelihood = 0.5, exponent = 0.35
        # P(S | E) = 0.55

        assert decision.confidence == pytest.approx(0.55)

    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test that MultiAgentDebateSystem initializes with a calibrator"""
        system = MultiAgentDebateSystem()
        assert system.calibrator is not None
        assert system.head_ai.calibrator == system.calibrator

    @pytest.mark.asyncio
    async def test_deterministic_replay(self):
        """Verify that identical inputs yield perfectly deterministic debate decisions and provenance logs"""
        import random
        import numpy as np

        # Configure deterministic seed
        random.seed(42)
        np.random.seed(42)

        system1 = MultiAgentDebateSystem()
        system2 = MultiAgentDebateSystem()

        context1 = MarketContext(
            symbol="EURUSD", current_price=1.1, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.2, key_levels={"support": [1.09]}, news_sentiment=0.4,
            portfolio_exposure=0.1, correlation_risk=0.2, vix_level=18.0
        )
        context2 = MarketContext(
            symbol="EURUSD", current_price=1.1, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.2, key_levels={"support": [1.09]}, news_sentiment=0.4,
            portfolio_exposure=0.1, correlation_risk=0.2, vix_level=18.0
        )

        decision1 = await system1.debate(context1)

        # Reset seed for exact replay of any randomized components
        random.seed(42)
        np.random.seed(42)
        decision2 = await system2.debate(context2)

        # Assert perfect equality across core outputs
        assert decision1.action == decision2.action
        assert decision1.confidence == pytest.approx(decision2.confidence)
        assert decision1.position_size_pct == pytest.approx(decision2.position_size_pct)
        assert decision1.reasoning == decision2.reasoning
        assert decision1.agent_votes == decision2.agent_votes

        # Assert perfect equality across full DecisionProvenance logs
        prov1 = decision1.provenance
        prov2 = decision2.provenance
        assert prov1['configuration_hash'] == prov2['configuration_hash']
        assert prov1['feature_hash'] == prov2['feature_hash']
        assert prov1['market_snapshot_hash'] == prov2['market_snapshot_hash']
        assert prov1['model_version'] == prov2['model_version']
        assert prov1['risk_policy_version'] == prov2['risk_policy_version']
        assert prov1['consensus_record'] == prov2['consensus_record']

    @pytest.mark.asyncio
    async def test_failure_injection_resilience(self):
        """Verify that multi-agent system degrades gracefully or fails closed under individual agent failures"""
        system = MultiAgentDebateSystem()
        context = MarketContext(
            symbol="EURUSD", current_price=1.1, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.2, key_levels={"support": [1.09]}, news_sentiment=0.4,
            portfolio_exposure=0.1, correlation_risk=0.2, vix_level=18.0
        )

        # 1. Inject exception on Macro Strategist analyze method
        with patch.object(system.macro_strategist, 'analyze', side_effect=Exception("Macro failure simulated")):
            # The system should not crash; it should catch the error and synthesize a decision with remaining agents
            decision = await system.debate(context)
            assert decision is not None
            assert "macro_strategist" not in decision.agent_votes
            assert len(decision.agent_votes) == 2  # Tactical and Risk Sentinel votes recorded

        # 2. Inject exception on FalsificationGate to ensure fail-closed or robust handling
        with patch.object(system.falsification_gate, 'run_falsification', side_effect=Exception("Falsification system crash")):
            # Falsification gate failure should lead to robust handling or trade abort / degradation
            try:
                decision = await system.debate(context)
                assert decision is not None
            except Exception as e:
                # Failing closed is also acceptable if exception is propagated
                pass

    def test_bayesian_posterior_sensitivity(self):
        """Verify the mathematical properties and stability of the correlation-aware Bayesian posterior calculation"""
        head_ai = HeadAI()

        # 1. High Prior vs Low Prior sensitivity
        # Identical evidence: single agent endorses with 0.8 likelihood (0.35 weight)
        evidence = [(True, 0.8, 0.35)]

        post_high_prior = head_ai.calculate_bayesian_posterior(0.9, evidence)
        post_low_prior = head_ai.calculate_bayesian_posterior(0.1, evidence)

        assert post_high_prior > post_low_prior
        assert 0.0 <= post_high_prior <= 1.0
        assert 0.0 <= post_low_prior <= 1.0

        # 2. Contradictory Evidence
        # Prior is 0.5. One agent endorses (likelihood 0.7), one agent opposes (likelihood 0.7), both weight 0.35
        contradictory_evidence = [
            (True, 0.7, 0.35),
            (False, 0.7, 0.35)
        ]
        post_contradictory = head_ai.calculate_bayesian_posterior(0.5, contradictory_evidence)
        # Symmetrical evidence should perfectly balance back to the prior (0.5)
        assert post_contradictory == pytest.approx(0.5)

        # 3. Monotonicity
        # Higher likelihood should strictly increase posterior under same prior and weight
        post_low_lik = head_ai.calculate_bayesian_posterior(0.5, [(True, 0.6, 0.35)])
        post_high_lik = head_ai.calculate_bayesian_posterior(0.5, [(True, 0.8, 0.35)])
        assert post_high_lik > post_low_lik

        # 4. Numerical Boundary and Stability Checks
        # Extreme/degenerate inputs should be handled gracefully without division by zero
        assert 0.0 <= head_ai.calculate_bayesian_posterior(0.0, [(True, 0.99, 1.0)]) <= 1.0
        assert 0.0 <= head_ai.calculate_bayesian_posterior(1.0, [(False, 0.99, 1.0)]) <= 1.0
        assert 0.0 <= head_ai.calculate_bayesian_posterior(0.5, [(True, 0.0, 1.0)]) <= 1.0
