"""Tests for Hypothesis Engine and Anti-Overfitting System."""

import pytest
from trading_bot.cognition.hypotheses import (
    Hypothesis,
    HypothesisStatus,
    HypothesisEngine,
)


def test_hypothesis_creation_and_validation():
    engine = HypothesisEngine()
    h = engine.create_hypothesis(
        hypothesis_id="hyp_001",
        origin="LLM_Research",
        mechanism="Liquidity sweep at Asian session high precedes London reversal",
        predictions=["Price reverses within 3 bars of Asian high sweep"],
        null_hypothesis="Sweep has no effect on directional probability",
        alternative_hypothesis="Sweep increases reversal probability by >15%"
    )

    assert h.status == HypothesisStatus.GENERATED

    evaluated = engine.evaluate_research_pipeline(
        hypothesis_id="hyp_001",
        p_value=0.01,
        deflated_sharpe=1.45,
        pbo_probability=0.12
    )

    assert evaluated.status == HypothesisStatus.VALIDATED
    assert evaluated.rejection_reason is None


def test_hypothesis_rejection_on_pbo():
    engine = HypothesisEngine(max_pbo=0.25)
    engine.create_hypothesis(
        hypothesis_id="hyp_002",
        origin="ML_GridSearch",
        mechanism="Overfitted 50-indicator strategy",
        predictions=["High Sharpe in backtest"],
        null_hypothesis="Random return",
        alternative_hypothesis="Alpha present"
    )

    evaluated = engine.evaluate_research_pipeline(
        hypothesis_id="hyp_002",
        p_value=0.02,
        deflated_sharpe=1.1,
        pbo_probability=0.45  # High probability of backtest overfitting
    )

    assert evaluated.status == HypothesisStatus.REJECTED
    assert "PBO probability" in evaluated.rejection_reason


def test_hypothesis_rejection_on_lookahead_bias():
    engine = HypothesisEngine()
    engine.create_hypothesis(
        hypothesis_id="hyp_003",
        origin="LLM",
        mechanism="Test",
        predictions=["P"],
        null_hypothesis="N",
        alternative_hypothesis="A"
    )

    evaluated = engine.evaluate_research_pipeline(
        hypothesis_id="hyp_003",
        p_value=0.001,
        deflated_sharpe=3.0,
        pbo_probability=0.01,
        lookahead_detected=True
    )

    assert evaluated.status == HypothesisStatus.REJECTED
    assert "Lookahead bias" in evaluated.rejection_reason
