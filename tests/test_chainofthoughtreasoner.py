#!/usr/bin/env python3
"""Tests for chainofthoughtreasoner"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.core.chainofthoughtreasoner import (
    ChainOfThoughtReasoner,
    ChainOfThoughtReasonerConfig,
    MythosReasoningResult,
    ReasoningMode,
)


class TestChainofthoughtreasoner:
    """Test suite for chainofthoughtreasoner"""
    
    def test_import(self):
        """Test that module can be imported"""
        try:
            import trading_bot
            assert True
        except ImportError as e:
            pytest.skip(f"Module not importable: {e}")
    
    def test_placeholder(self):
        """Placeholder test - implement actual tests"""
        # TODO: Implement actual tests for chainofthoughtreasoner
        assert True


def test_mythos_recurrent_loop_converges_and_returns_trace():
    reasoner = ChainOfThoughtReasoner(ChainOfThoughtReasonerConfig(max_reasoning_loops=5))

    result = reasoner.process(
        "Analyze whether evidence supports a cautious trade",
        {"rsi": 28, "macd": 0.2, "sma_20": 105, "sma_50": 100, "volatility": 0.8, "drawdown": 0.01},
        ReasoningMode.TRADE,
        analysis_only=True,
    )

    assert isinstance(result, MythosReasoningResult)
    assert 1 <= len(result.trace.states) <= 5
    assert result.trace.steps
    assert result.logic_kernel_result.premises
    assert result.decision in {"BUY", "SELL", "HOLD"}


def test_mythos_defaults_uncertain_trade_to_hold():
    reasoner = ChainOfThoughtReasoner(ChainOfThoughtReasonerConfig(max_reasoning_loops=3, min_settledness=0.95))

    result = reasoner.process(
        "Should Mythos allow a trade?",
        {"rsi": 50, "macd": 0.0, "volatility": 3.5, "drawdown": 0.2, "operator_calm": "critical"},
        ReasoningMode.TRADE,
    )

    assert result.decision == "HOLD"
    assert result.confidence <= 0.49


def test_mythos_vlk_rejects_circular_reasoning():
    reasoner = ChainOfThoughtReasoner()

    result = reasoner.verify_conclusion(["action is BUY"], "action is BUY")

    assert not result.verified
    assert result.status in {"fallacious", "invalid", "uncertain"}
    assert result.fallacies or result.recommendations


def test_mythos_vulnerability_mode_runs_red_blue_and_expert_lock():
    reasoner = ChainOfThoughtReasoner(ChainOfThoughtReasonerConfig(max_reasoning_loops=4))

    result = reasoner.process(
        "Assess whether evidence indicates a vulnerability.",
        {"source": "security review", "citations": ["audit-1"], "finding": "auth bypass vulnerability"},
        ReasoningMode.VULNERABILITY,
    )

    review = result.trace.red_blue_review
    assert result.trace.locked_expert == "software_vulnerability"
    assert review is not None
    assert review.exploit_verification.premises
    assert review.verdict in {"risk_confirmed", "risk_mitigated", "needs_more_evidence"}


def test_mythos_reset_and_status_track_history():
    reasoner = ChainOfThoughtReasoner(ChainOfThoughtReasonerConfig(max_reasoning_loops=2))
    reasoner.process("Analyze context", {"question": "status smoke"})

    assert reasoner.get_status()["history_size"] == 1
    reset = reasoner.reset()
    assert reset["cleared_history"] == 1
    assert reasoner.get_status()["history_size"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
