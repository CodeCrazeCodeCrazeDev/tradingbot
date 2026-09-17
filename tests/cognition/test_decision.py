"""Tests for Decision Intelligence Engine and Rigid Risk Gatekeeper."""

import time
import pytest
from trading_bot.cognition.state import MarketState
from trading_bot.cognition.verification import AdversarialAttackReport
from trading_bot.cognition.decision import (
    CognitiveAction,
    DecisionProposal,
    DecisionIntelligenceEngine,
    RiskGatekeeper,
)


def test_decision_intelligence_abstain_on_adversarial_failure():
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="BEARISH",
        uncertainty=0.15
    )

    adv_report = AdversarialAttackReport(
        hypothesis_id="hyp_001",
        vulnerabilities_found=["Counter-trend entry in strong bear trend"],
        contradictory_evidence=["H1 trend is bearish"],
        regime_destructors=[],
        overfitting_risk_level="HIGH",
        execution_erosion_pips=1.5,
        attack_passed=False,
        confidence_penalty=0.40
    )

    engine = DecisionIntelligenceEngine()
    proposal = engine.synthesize_decision(
        decision_id="dec_001",
        market_state=state,
        adversarial_report=adv_report,
        raw_signal="BUY"
    )

    assert proposal.action == CognitiveAction.ABSTAIN
    assert len(proposal.contradicting_evidence) > 0


def test_risk_gatekeeper_veto_missing_stop_loss():
    proposal = DecisionProposal(
        decision_id="dec_002",
        action=CognitiveAction.BUY,
        instrument="EURUSD",
        direction="LONG",
        proposed_position_size=1.0,
        stop_loss=None  # Missing stop loss
    )

    gatekeeper = RiskGatekeeper()
    result = gatekeeper.evaluate_proposal(proposal)

    assert not result.authorized
    assert result.authorized_action == CognitiveAction.ABSTAIN
    assert "Stop-Loss requirement missing" in result.hard_limit_violations[0]


def test_risk_gatekeeper_authorized():
    proposal = DecisionProposal(
        decision_id="dec_003",
        action=CognitiveAction.BUY,
        instrument="EURUSD",
        direction="LONG",
        proposed_position_size=1.0,
        stop_loss=1.0800
    )

    gatekeeper = RiskGatekeeper()
    result = gatekeeper.evaluate_proposal(proposal)

    assert result.authorized
    assert result.authorized_action == CognitiveAction.BUY
    assert result.authorized_size == 1.0
