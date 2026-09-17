"""Tests for Canonical Orchestrator and Unified AI Brain compatibility."""

import time
import pytest
from trading_bot.cognition import AlphaAlgoCognitiveBrain
from trading_bot.unified_ai_brain import UnifiedAIBrain, get_unified_brain


def test_alphaalgo_cognitive_brain_cycle():
    brain = AlphaAlgoCognitiveBrain()

    raw_data = {
        "M15": {"open": 1.0800, "high": 1.0850, "low": 1.0790, "close": 1.0840, "volume": 1000.0},
        "H1": {"open": 1.0780, "high": 1.0860, "low": 1.0770, "close": 1.0850, "volume": 5000.0}
    }

    res = brain.process_cycle(
        instrument="EURUSD",
        raw_market_data=raw_data,
        proposed_trade_signal="BUY",
        stop_loss_price=1.0780
    )

    assert res["instrument"] == "EURUSD"
    assert res["risk_authorized"]
    assert res["authorized_action"] == "BUY"
    assert res["authorized_size"] == 1.0
    assert res["market_state"]["trend"] == "BULLISH"


def test_backward_compatibility_wrapper():
    legacy_brain = get_unified_brain()
    raw_data = {
        "M15": {"open": 1.0800, "high": 1.0850, "low": 1.0790, "close": 1.0840, "volume": 1000.0}
    }
    res = legacy_brain.process_cycle(
        instrument="EURUSD",
        raw_market_data=raw_data,
        proposed_trade_signal="BUY",
        stop_loss_price=1.0780
    )
    assert res["authorized_action"] == "BUY"
