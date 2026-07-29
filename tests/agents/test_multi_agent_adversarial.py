"""
Adversarial and Replay Tests for the Multi-Agent Trading Debate System

Verifies:
1. Byzantine agents sending contradictory/anomalous evidence
2. Silent/non-responsive agents and quorum boundaries
3. Malformed evidence / pricing anomaly vetoes
4. Delayed / duplicated messages (double-counting prevention)
5. Network partition simulations (safe failover holds)
6. Deterministic replay of identical debates
7. Consensus behavior under varying quorum sizes
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from trading_bot.agents.multi_agent_debate import (
    AgentRole, Conviction, TradeAction, MarketContext,
    AgentArgument, DebateRound, HeadAI, MultiAgentDebateSystem,
    create_debate_system
)

class TestMultiAgentAdversarial:
    """Rigorous adversarial and replay verification suite."""

    @pytest.mark.asyncio
    async def test_byzantine_contradictory_evidence(self):
        """Verify that Byzantine contradictory evidence is isolated and doesn't bypass safety gates."""
        system = create_debate_system()

        # Bullish macro structure but risk indices are extremely stressed
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.015,
            volume_ratio=1.3,
            key_levels={'support': [1.0950], 'resistance': [1.1050]},
            news_sentiment=0.8,
            portfolio_exposure=0.95, # Extreme exposure violating limits
            correlation_risk=0.9,    # Extreme correlation violating limits
            vix_level=42.0           # Black swan VIX level
        )

        decision = await system.debate(context)

        # Risk sentinel must veto the bullish bias, enforcing safe hold/no_trade
        assert decision.action == TradeAction.NO_TRADE

        # Let's verify that the RiskVerifier returns invalid if we propose a BUY under these parameters
        from trading_bot.agents.multi_agent_debate import RiskVerifier
        verifier = RiskVerifier()
        res = verifier.verify(TradeAction.BUY, context)
        assert res.is_valid is False

    @pytest.mark.asyncio
    async def test_silent_non_responsive_agents_and_degradation(self):
        """Verify that the system gracefully degrades and uses fallbacks when an agent is completely silent."""
        system = create_debate_system()

        # Force risk_sentinel to crash during analyze
        with patch.object(system.risk_sentinel, 'analyze', side_effect=RuntimeError("Connection timeout to Risk Database")):
            context = MarketContext(
                symbol="EURUSD",
                current_price=1.1000,
                htf_trend='UP',
                ltf_trend='UP',
                volatility=0.01,
                volume_ratio=1.0,
                key_levels={'support': [1.09], 'resistance': [1.11]},
                news_sentiment=0.0,
                portfolio_exposure=0.2,
                correlation_risk=0.1
            )

            decision = await system.debate(context)

            # Risk sentinel crashed, but the system must fall back to a defensive default argument for RiskSentinel
            assert decision is not None
            assert "risk_sentinel" in decision.agent_votes
            # The risk_sentinel fallback action is TradeAction.NO_TRADE (enforcing absolute safety on sentinel failure)
            assert decision.action == TradeAction.NO_TRADE

    @pytest.mark.asyncio
    async def test_malformed_evidence_and_hallucination_veto(self):
        """Verify that HallucinationDetector vetoes a trade if market prices are malformed/anomalous."""
        system = create_debate_system()

        context = MarketContext(
            symbol="EURUSD",
            current_price=-1.1000,  # Malformed negative current price!
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.01,
            volume_ratio=1.0,
            key_levels={'support': [1.09], 'resistance': [1.11]},
            news_sentiment=0.0,
            portfolio_exposure=0.2,
            correlation_risk=0.1
        )

        decision = await system.debate(context)

        # Hallucination verifier must flag this as invalid and veto the trade completely to TradeAction.NO_TRADE
        assert decision.action == TradeAction.NO_TRADE
        assert decision.provenance['verification_results']['hallucination_detector']['is_valid'] is False
        assert "Invalid current price detected" in decision.reasoning

    @pytest.mark.asyncio
    async def test_duplicated_delayed_messages(self):
        """Verify that HeadAI latest-only filter prevents double-counting duplicate/stale messages."""
        head_ai = HeadAI()
        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.01,
            volume_ratio=1.0,
            key_levels={'support': [1.09], 'resistance': [1.11]},
            news_sentiment=0.0,
            portfolio_exposure=0.2,
            correlation_risk=0.1
        )

        arg_old = AgentArgument(
            agent_role=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.BUY,
            conviction=Conviction.LOW,
            reasoning=["Old trend buy"],
            key_factors={},
            confidence=0.4,
            timestamp=datetime.now() - timedelta(minutes=5)
        )

        arg_new = AgentArgument(
            agent_role=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.SELL,
            conviction=Conviction.HIGH,
            reasoning=["New trend sell"],
            key_factors={},
            confidence=0.9,
            timestamp=datetime.now()
        )

        # Send both duplicate arguments (representing duplicated or delayed messages from past rounds)
        decision = head_ai.synthesize_decision([arg_old, arg_new, arg_old], context, [])

        # Only the latest argument should dictate the vote and action
        assert decision.action == TradeAction.SELL
        assert len(decision.agent_votes) == 1
        assert decision.agent_votes['macro_strategist'] == 'sell'

    @pytest.mark.asyncio
    async def test_network_partition_simulation(self):
        """Verify that under total network partition (all agents failing), the system fails safe."""
        system = create_debate_system()

        # Force all agents to crash
        with patch.object(system.macro_strategist, 'analyze', side_effect=RuntimeError("No route to host")):
            with patch.object(system.tactical_executioner, 'analyze', side_effect=RuntimeError("No route to host")):
                with patch.object(system.risk_sentinel, 'analyze', side_effect=RuntimeError("No route to host")):

                    context = MarketContext(
                        symbol="EURUSD",
                        current_price=1.1000,
                        htf_trend='UP',
                        ltf_trend='UP',
                        volatility=0.01,
                        volume_ratio=1.0,
                        key_levels={'support': [1.09], 'resistance': [1.11]},
                        news_sentiment=0.0,
                        portfolio_exposure=0.2,
                        correlation_risk=0.1
                    )

                    decision = await system.debate(context)

                    # Responsive count is 0, must trigger the emergency safe NO_TRADE fallback
                    assert decision.action == TradeAction.NO_TRADE
                    assert "EMERGENCY VETO" in decision.reasoning

    @pytest.mark.asyncio
    async def test_deterministic_replay_consistency(self):
        """Verify that replay is fully deterministic under identical context parameters."""
        system = create_debate_system()

        context = MarketContext(
            symbol="EURUSD",
            current_price=1.1000,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.015,
            volume_ratio=1.3,
            key_levels={'support': [1.0950, 1.0900], 'resistance': [1.1050, 1.1100]},
            news_sentiment=0.4,
            portfolio_exposure=0.25,
            correlation_risk=0.3,
            vix_level=18.0
        )

        decision_1 = await system.debate(context)

        # Reset and run identical debate
        system_replay = create_debate_system()
        decision_2 = await system_replay.debate(context)

        # Assert full identical matching
        assert decision_1.action == decision_2.action
        assert decision_1.confidence == decision_2.confidence
        assert decision_1.position_size_pct == decision_2.position_size_pct
        assert decision_1.entry_price == decision_2.entry_price
        assert decision_1.stop_loss == decision_2.stop_loss
        assert decision_1.take_profit == decision_2.take_profit

        # Verify provenance determinism (hashes are identical)
        assert decision_1.provenance['market_snapshot_hash'] == decision_2.provenance['market_snapshot_hash']
        assert decision_1.provenance['feature_hash'] == decision_2.provenance['feature_hash']
        assert decision_1.provenance['configuration_hash'] == decision_2.provenance['configuration_hash']

    @pytest.mark.asyncio
    async def test_consensus_under_varying_quorum_sizes(self):
        """Verify that consensus scores and agreement align gracefully across varying quorum configurations."""
        head_ai = HeadAI()
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

        arg_1 = AgentArgument(
            agent_role=AgentRole.MACRO_STRATEGIST,
            action=TradeAction.BUY,
            conviction=Conviction.HIGH,
            reasoning=["Macro buy"],
            key_factors={},
            confidence=0.8,
            timestamp=datetime.now()
        )

        arg_2 = AgentArgument(
            agent_role=AgentRole.TACTICAL_EXECUTIONER,
            action=TradeAction.BUY,
            conviction=Conviction.HIGH,
            reasoning=["Tactical buy"],
            key_factors={},
            confidence=0.9,
            timestamp=datetime.now()
        )

        # Quorum size 2 (Macro + Tactical)
        decision_quorum_2 = head_ai.synthesize_decision([arg_1, arg_2], context, [])
        assert decision_quorum_2.consensus_level == 1.0  # Perfect agreement

        arg_3 = AgentArgument(
            agent_role=AgentRole.RISK_SENTINEL,
            action=TradeAction.HOLD,
            conviction=Conviction.MODERATE,
            reasoning=["Risk hold"],
            key_factors={},
            confidence=0.6,
            timestamp=datetime.now()
        )

        # Quorum size 3 (Macro + Tactical + Risk)
        decision_quorum_3 = head_ai.synthesize_decision([arg_1, arg_2, arg_3], context, [])
        assert decision_quorum_3.consensus_level == pytest.approx(2 / 3)  # 2/3 agree
        assert decision_quorum_3.action == TradeAction.BUY
