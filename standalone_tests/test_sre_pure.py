import asyncio
import uuid
import numpy as np
from trading_bot.core_agent_system.scientific_reasoning.core import ScientificReasoningEngine, HypothesisState

async def test_sre_cycle():
    # Mock dependencies to avoid complex imports
    sre = ScientificReasoningEngine()
    sre.world_model = type('MockWM', (), {
        'predict_state': lambda self, x: asyncio.sleep(0, result={}),
        'simulate_intervention': lambda self, x: asyncio.sleep(0, result={"causal_stability": 0.8, "confidence": 0.9})
    })()

    # Observe
    hid = await sre.observe({"data": "test"})
    print(f"Observed: {hid}")

    # Step through cycle
    await sre.detect_anomalies(hid)
    assert sre.registry[hid].state == HypothesisState.ANOMALY_DETECTION

    await sre.generate_counterfactuals(hid)
    assert sre.registry[hid].state == HypothesisState.COUNTERFACTUAL_GENERATION
    assert sre.registry[hid].validation_score == 0.8

    await sre.bayesian_update(hid)
    assert sre.registry[hid].posterior > 0.5

    # Force high posterior to meet institutionalized threshold
    sre.registry[hid].posterior = 0.9
    await sre.retire_hypothesis(hid)
    assert sre.registry[hid].state == HypothesisState.INSTITUTIONALIZED

    print("SRE cycle test passed!")

if __name__ == "__main__":
    asyncio.run(test_sre_cycle())
