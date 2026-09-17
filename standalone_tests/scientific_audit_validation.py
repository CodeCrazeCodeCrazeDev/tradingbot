import pytest
import asyncio
from trading_bot.core_agent_system.scientific_reasoning.core import ScientificReasoningEngine, HypothesisState
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

    assert "GENERATION_NOISE" in metrics.bottlenecks_detected or "FILTERING_STRICTNESS" in metrics.bottlenecks_detected

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
