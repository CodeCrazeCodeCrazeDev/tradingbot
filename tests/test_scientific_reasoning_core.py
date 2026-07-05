import pytest
import asyncio
from trading_bot.core_agent_system.scientific_reasoning.core import (
    ScientificReasoningEngine,
    ScientificEvidence,
    HypothesisState,
    ScientificHypothesis
)

@pytest.mark.asyncio
async def test_scientific_loop_full_cycle():
    sre = ScientificReasoningEngine()
    observation = {"is_anomaly": True, "feature": "volatility", "magnitude": "3 sigma"}

    # Run loop
    hypotheses = await sre.run_scientific_loop(observation)

    assert len(hypotheses) > 0
    hyp = hypotheses[0]
    assert hyp.id in sre.registry
    assert hyp.falsification_attempts > 0

@pytest.mark.asyncio
async def test_bayesian_evidence_synthesis():
    sre = ScientificReasoningEngine()
    hyp = ScientificHypothesis(name="Trend Hypothesis", posterior=0.5, uncertainty=1.0)
    sre.registry[hyp.id] = hyp

    # Supporting evidence
    evidence = ScientificEvidence(source="MarketData", confidence=0.8, is_contradicting=False)
    await sre.synthesize_evidence(hyp.id, evidence)

    assert hyp.posterior > 0.5
    assert hyp.uncertainty < 1.0

    # Contradicting evidence
    bad_evidence = ScientificEvidence(source="Sentiment", confidence=0.9, is_contradicting=True)
    await sre.synthesize_evidence(hyp.id, bad_evidence)

    assert hyp.posterior < 0.8 # Should drop

@pytest.mark.asyncio
async def test_lineage_tracking_merge():
    sre = ScientificReasoningEngine()
    h1 = ScientificHypothesis(name="H1")
    h2 = ScientificHypothesis(name="H2")
    sre.registry[h1.id] = h1
    sre.registry[h2.id] = h2

    merged_id = await sre.merge([h1.id, h2.id], "Unified Hypothesis")

    assert merged_id in sre.registry
    merged_hyp = sre.registry[merged_id]
    assert h1.id in merged_hyp.lineage.parent_ids
    assert h2.id in merged_hyp.lineage.parent_ids
    assert h1.state == HypothesisState.MERGED
    assert h2.state == HypothesisState.MERGED

@pytest.mark.asyncio
async def test_hypothesis_evolution():
    sre = ScientificReasoningEngine()
    hyp = ScientificHypothesis(name="Test Hyp", posterior=0.9, uncertainty=0.1)
    sre.registry[hyp.id] = hyp

    await sre.evolve(hyp.id)
    assert hyp.state == HypothesisState.CONFIRMED

    # Test rejection
    hyp.validation_score = -0.8
    await sre.evolve(hyp.id)
    assert hyp.state == HypothesisState.REJECTED
