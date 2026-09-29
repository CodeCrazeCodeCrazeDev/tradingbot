"""Tests for Independent Adversarial Intelligence Subsystem."""

import time
import pytest
from trading_bot.cognition.state import MarketState
from trading_bot.cognition.verification import (
    AdversarialAttackReport,
    AdversarialSubsystem,
)


def test_adversarial_attack_on_counter_trend_trade():
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="BEARISH",
        uncertainty=0.15
    )

    adv = AdversarialSubsystem()
    report = adv.attack_trade_hypothesis(
        hypothesis_id="hyp_buy_001",
        proposed_action="BUY",  # Counter-trend
        market_state=state
    )

    assert not report.attack_passed
    assert report.overfitting_risk_level in ("HIGH", "CRITICAL")
    assert report.confidence_penalty >= 0.30
    assert len(report.vulnerabilities_found) > 0


def test_adversarial_attack_on_aligned_trade():
    state = MarketState(
        timestamp=time.time(),
        instrument="EURUSD",
        primary_timeframe="M15",
        trend_direction="BULLISH",
        uncertainty=0.10
    )

    adv = AdversarialSubsystem()
    report = adv.attack_trade_hypothesis(
        hypothesis_id="hyp_buy_002",
        proposed_action="BUY",  # Trend aligned
        market_state=state
    )

    assert report.attack_passed
    assert report.confidence_penalty == 0.0
