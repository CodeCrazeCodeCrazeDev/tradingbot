import pytest
import asyncio
from trading_bot.core_agent_system.scientific_reasoning.core import ScientificReasoningEngine, HypothesisState, ScientificEvidence
from trading_bot.observability.scientific_metrics import ScientificMetrics

@pytest.mark.asyncio
async def test_sre_19_step_cycle():
    """Verify that a hypothesis progresses through the 19-step cycle correctly."""
    sre = ScientificReasoningEngine()
    observation = {"price": 1.05, "volume": 1000}

    hyp_id = await sre.run_cycle(observation)
    assert hyp_id in sre.registry
    hyp = sre.registry[hyp_id]

    # Check that it reached a terminal state or finished the cycle
    assert hyp.state in [
        HypothesisState.INSTITUTIONALIZED,
        HypothesisState.REJECTED,
        HypothesisState.INCONCLUSIVE,
        HypothesisState.DORMANT
    ]
    assert hyp.posterior != 0.5 # Should have been updated

@pytest.mark.asyncio
async def test_scientific_metrics_bottleneck_detection():
    """Verify that metrics correctly identify bottlenecks."""
    metrics = ScientificMetrics()

    # Mock a registry with high rejection rate
    class MockHyp:
        def __init__(self, state_name):
            self.state = type('State', (), {'name': state_name})
            self.posterior = 0.1
            self.novelty_score = 0.1
            self.vfe = 10.0
            self.validation_score = 0.2

    registry = {f"h{i}": MockHyp("REJECTED") for i in range(25)}
    metrics.update_from_registry(registry)

    assert any("GENERATION_NOISE" in b for b in metrics.bottlenecks_detected) or any("FILTERING_STRICTNESS" in b for b in metrics.bottlenecks_detected)

@pytest.mark.asyncio
async def test_terminal_states_enforcement():
    """Verify that the engine correctly assigns terminal states based on posterior."""
    sre = ScientificReasoningEngine()

    # Mock a high confidence hypothesis
    hyp_id_high = await sre.observe({})
    sre.registry[hyp_id_high].posterior = 0.95
    await sre.retire_hypothesis(hyp_id_high)
    assert sre.registry[hyp_id_high].state == HypothesisState.INSTITUTIONALIZED

    # Mock a failed hypothesis
    hyp_id_low = await sre.observe({})
    sre.registry[hyp_id_low].posterior = 0.05
    await sre.retire_hypothesis(hyp_id_low)
    assert sre.registry[hyp_id_low].state == HypothesisState.REJECTED

@pytest.mark.asyncio
async def test_sre_leni_and_self_improvement():
    """Verify Leni AI governance traces and recursive SRE parameter adaptation."""
    sre = ScientificReasoningEngine()

    # 1. Verify structured trace fields on evidence and hypothesis
    hyp_id = await sre.observe({})
    await sre.collect_evidence(hyp_id)
    hyp = sre.registry[hyp_id]

    assert hyp.leni_trust_score == 1.5
    assert hyp.approval_trace["reviewed_by"] == "Senior Quant Strategist"
    assert "Slippage is bounded" in hyp.approval_trace["assumptions_accepted"]

    # 2. Verify that high leni_trust_score elevates the Bayesian posterior
    hyp.prior = 0.5
    hyp.validation_score = 0.8
    await sre.bayesian_update(hyp_id)
    # With a high trust score, the posterior should update to > 0.65 (exactly ~0.6644)
    assert hyp.posterior > 0.65

    # 3. Verify SRE recursive self-improvement parameter adaptation (Step 19)
    # Seed registry with 10 rejected hypotheses to exceed the 60% rejection rate threshold
    for i in range(12):
        hid = await sre.observe({})
        sre.registry[hid].state = HypothesisState.REJECTED

    # Trigger Step 19 meta-discovery
    original_threshold = sre.anomaly_threshold
    await sre.discover_new_hypotheses()

    # Anomaly threshold should have been adjusted upwards to filter out noise
    assert sre.anomaly_threshold > original_threshold
    assert len(sre.self_improvement_logs) == 1
    assert "new_anomaly_threshold" in sre.self_improvement_logs[0]
