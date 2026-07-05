"""
Tests for verifier_agent
"""

import pytest
from trading_bot.agents.verifier_agent import VerificationResult, VerifierAgent

class TestVerificationResult:
    """Tests for VerificationResult"""

    def test_initialization(self):
        """Test VerificationResult initialization"""
        obj = VerificationResult(
            approved=True,
            reason="All checks passed",
            checks_passed={"check1": True},
            risk_metrics={"metric1": 0.5}
        )
        assert obj is not None
        assert obj.approved is True

class TestVerifierAgent:
    """Tests for VerifierAgent"""

    def test_initialization(self):
        """Test VerifierAgent initialization"""
        obj = VerifierAgent()
        assert obj is not None
