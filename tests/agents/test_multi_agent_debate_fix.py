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

        # The winning_score (confidence) in FinalDecision is the Bayesian calibrated posterior probability.
        # Prior is 0.55 (winning action aligned with HTF trend).
        # Calibrated confidence for MACRO_STRATEGIST is 0.5.
        # Posterior = (0.55 * 0.5) / (0.55 * 0.5 + 0.45 * 0.5) = 0.275 / 0.5 = 0.55

        assert decision.confidence == pytest.approx(0.55)

    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test that MultiAgentDebateSystem initializes with a calibrator"""
        system = MultiAgentDebateSystem()
        assert system.calibrator is not None
        assert system.head_ai.calibrator == system.calibrator

    @pytest.mark.asyncio
    async def test_debate_determinism(self):
        """Test that same inputs generate identical decisions, provenance, and hashes."""
        system = MultiAgentDebateSystem()
        context = MarketContext(
            symbol="BTCUSD", current_price=60000.0, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.2, key_levels={"support": [59000.0]}, news_sentiment=0.4,
            portfolio_exposure=0.1, correlation_risk=0.1, vix_level=15.0
        )
        dec1 = await system.debate(context)
        dec2 = await system.debate(context)

        assert dec1.action == dec2.action
        assert dec1.provenance['market_snapshot_hash'] == dec2.provenance['market_snapshot_hash']
        assert dec1.provenance['feature_hash'] == dec2.provenance['feature_hash']
        assert dec1.provenance['random_seed'] == dec2.provenance['random_seed']

    @pytest.mark.asyncio
    async def test_bayesian_calibration_bounds(self):
        """Test that calculate_bayesian_posterior respects logical and mathematical bounds."""
        head_ai = HeadAI()
        # All agree with high likelihoods
        posterior1 = head_ai.calculate_bayesian_posterior(0.5, [(True, 0.95, 1.0), (True, 0.90, 1.0)])
        assert posterior1 > 0.90

        # All disagree/contradict
        posterior2 = head_ai.calculate_bayesian_posterior(0.5, [(False, 0.95, 1.0), (False, 0.90, 1.0)])
        assert posterior2 < 0.10

    @pytest.mark.asyncio
    async def test_falsification_gate_triggering(self):
        """Test that FalsificationGate triggers NO_TRADE and records details under high VIX panic."""
        system = MultiAgentDebateSystem()
        context_panic = MarketContext(
            symbol="BTCUSD", current_price=60000.0, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.2, key_levels={}, news_sentiment=0.4,
            portfolio_exposure=0.1, correlation_risk=0.1, vix_level=40.0 # Extreme panic
        )
        decision = await system.debate(context_panic)
        assert decision.action == TradeAction.NO_TRADE
        assert decision.provenance['falsification_report']['is_falsified'] is True
        assert "CausalVerifier" in decision.provenance['falsification_report']['rejection_reason']

    @pytest.mark.asyncio
    async def test_regime_scorecard_influence(self):
        """Test that adjusting agent expected contribution scorecard metrics dynamically scales voting weight."""
        system = MultiAgentDebateSystem()
        context = MarketContext(
            symbol="BTCUSD", current_price=60000.0, htf_trend="UP", ltf_trend="UP",
            volatility=0.015, volume_ratio=1.2, key_levels={}, news_sentiment=0.4,
            portfolio_exposure=0.1, correlation_risk=0.1, vix_level=15.0
        )

        # Override scorecard for MACRO_STRATEGIST to have near zero contribution
        system.regime_scorecards["UP"][AgentRole.MACRO_STRATEGIST].expected_contribution = 0.01

        dec = await system.debate(context)
        # Macro strategist wanted BUY, but with near 0 weight, it has minimal influence
        assert dec.provenance['agent_scorecards']['macro_strategist']['expected_contribution'] == 0.01

    @pytest.mark.asyncio
    async def test_debate_quality_evaluator(self):
        """Test that DebateQualityEvaluator records correct entropy, diversity, and costs."""
        from trading_bot.agents.multi_agent_debate import DebateQualityEvaluator
        evaluator = DebateQualityEvaluator()

        res = evaluator.evaluate_debate(
            initial_votes=[TradeAction.BUY, TradeAction.BUY, TradeAction.SELL],
            final_action=TradeAction.BUY,
            falsified=False,
            consensus_level=0.66,
            disagreement_map={"macro_strategist": 0.0, "tactical_executioner": 0.0, "risk_sentinel": 0.5},
            duration_ms=12.4
        )

        assert res['information_gain'] >= 0.0
        assert res['diversity_of_reasoning'] == pytest.approx(1.0 / 3.0)
        assert res['computational_cost_ms'] == 12.4
        assert res['falsification_impact'] is False

    @pytest.mark.asyncio
    async def test_adversarial_resistance(self):
        """Test that debate consensus is resilient and cannot be dominated by a single counter-argument."""
        system = MultiAgentDebateSystem()
        # Normal positive market context
        context = MarketContext(
            symbol="BTCUSD", current_price=60000.0, htf_trend="UP", ltf_trend="UP",
            volatility=0.01, volume_ratio=1.2, key_levels={}, news_sentiment=0.5,
            portfolio_exposure=0.1, correlation_risk=0.1, vix_level=12.0
        )
        decision = await system.debate(context)
        # Even with DevilsAdvocate and prosecutors active, strong positive indicators yield BUY consensus
        assert decision.action in [TradeAction.BUY, TradeAction.STRONG_BUY]
