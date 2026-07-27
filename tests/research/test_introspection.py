import pytest
import numpy as np

from trading_bot.research.research_os import ResearchWorkspace
from trading_bot.research.introspection.models import ReasoningHop
from trading_bot.research.introspection.core import IntrospectionEngine


@pytest.fixture
def workspace():
    """Initializes the central workspace."""
    return ResearchWorkspace()


@pytest.fixture
def ie():
    """Initializes the Introspection Engine."""
    return IntrospectionEngine()


def test_introspection_empty_chain(ie):
    """Verifies that an empty reasoning chain triggers fail-closed rejection."""
    report = ie.monitor_reasoning_chain("decision_001", [])
    assert report.is_decision_safe is False
    assert len(report.anomalies) == 1
    assert report.anomalies[0].anomaly_type == "EMPTY_REASONING_CHAIN"


def test_introspection_stable_chain(ie):
    """Verifies that a stable reasoning chain with low uncertainty and low surprise passes validation."""
    hops = [
        ReasoningHop(
            step_id=1,
            step_title="Macro Regime Inspection",
            evidence_claims=["Low volatility H1 regime detected", "Favorable bull market flow"],
            confidence_score=0.85,
            entropy=0.25,
            vfe_surprise=0.80
        ),
        ReasoningHop(
            step_id=2,
            step_title="Micro Liquidity Verification",
            evidence_claims=["Order book depth is thick", "Slippage expected under 0.5 pips"],
            confidence_score=0.90,
            entropy=0.15,
            vfe_surprise=0.45
        )
    ]

    report = ie.monitor_reasoning_chain("decision_002", hops)
    assert report.is_decision_safe is True
    assert len(report.anomalies) == 0
    assert report.overall_confidence >= 0.80
    assert report.evidence_consistency_score == 100.0
    assert "APPROVED" in report.decision_quality_explanation


def test_introspection_vfe_surprise_spike(ie):
    """Verifies that a spike in Variational Free Energy surprise triggers anomaly warnings."""
    hops = [
        ReasoningHop(
            step_id=1,
            step_title="Initial Prediction",
            evidence_claims=["Regime quiet"],
            confidence_score=0.80,
            entropy=0.30,
            vfe_surprise=1.10
        ),
        ReasoningHop(
            step_id=2,
            step_title="Microstructure Flash Check",
            # Spiking surprise indicates extreme hidden perturbation
            evidence_claims=["Flash crash order imbalance"],
            confidence_score=0.40,
            entropy=0.45,
            vfe_surprise=5.20  # Spike above 3.5 threshold
        )
    ]

    report = ie.monitor_reasoning_chain("decision_003", hops)
    # Spiking surprise reduces calibrated confidence and adds anomaly diagnosis
    assert any(anom.anomaly_type == "VFE_SURPRISE_SPIKE" for anom in report.anomalies)


def test_introspection_high_uncertainty_entropy(ie):
    """Verifies that high average reasoning entropy (high uncertainty) triggers warnings."""
    hops = [
        ReasoningHop(
            step_id=1,
            step_title="Uncertain step 1",
            evidence_claims=["Ambiguous indicators"],
            confidence_score=0.50,
            entropy=0.85,  # Exceeds max_acceptable_entropy
            vfe_surprise=1.20
        ),
        ReasoningHop(
            step_id=2,
            step_title="Uncertain step 2",
            evidence_claims=["Confused signals"],
            confidence_score=0.45,
            entropy=0.90,  # Exceeds max_acceptable_entropy
            vfe_surprise=1.50
        )
    ]

    report = ie.monitor_reasoning_chain("decision_004", hops)
    assert any(anom.anomaly_type == "HIGH_UNCERTAINTY_ENTROPY" for anom in report.anomalies)


def test_introspection_evidence_contradiction(ie):
    """Verifies that conflicting bullish and bearish signals with severe risk are flagged."""
    hops = [
        ReasoningHop(
            step_id=1,
            step_title="Strategy A Output",
            evidence_claims=["Highly Bullish momentum model card"],
            confidence_score=0.85,
            entropy=0.20,
            vfe_surprise=0.80
        ),
        ReasoningHop(
            step_id=2,
            step_title="Strategy B Output",
            evidence_claims=["Extreme Bearish breakout detected", "Critical drop risk flagged"],
            confidence_score=0.80,
            entropy=0.25,
            vfe_surprise=0.90
        )
    ]

    report = ie.monitor_reasoning_chain("decision_005", hops)
    assert any(anom.anomaly_type == "EVIDENCE_INCONSISTENCY" for anom in report.anomalies)
    assert report.evidence_consistency_score <= 50.0  # Heavy penalty
