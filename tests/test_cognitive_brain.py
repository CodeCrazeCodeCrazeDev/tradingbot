"""
Tests for AlphaAlgo Cognitive Brain (REG-601 to REG-700)
"""

import pytest
from trading_bot.cognition.alpha_algo_cognitive_brain import AlphaAlgoCognitiveBrain

def test_cognitive_brain_vfe_minimization():
    brain = AlphaAlgoCognitiveBrain()
    obs = [1.1000, 1.1005, 1.1002]
    priors = [1.1000, 1.1000, 1.1000]
    res = brain.compute_variational_free_energy(obs, priors, sensory_precision=2.0)

    assert "vfe" in res
    assert res["vfe"] > 0
    assert res["precision"] == 2.0

def test_epistemic_uncertainty_estimation():
    brain = AlphaAlgoCognitiveBrain()
    predictions = [0.05, 0.04, 0.06, 0.05]
    res = brain.estimate_epistemic_uncertainty(predictions)

    assert "epistemic_variance" in res
    assert "epistemic_bound" in res
    assert res["epistemic_bound"] >= 0.0

def test_provenance_memory_and_capacity():
    brain = AlphaAlgoCognitiveBrain()
    h1 = brain.append_provenance_memory({"price": 100}, "BUY", 10.0)
    h2 = brain.append_provenance_memory({"price": 101}, "SELL", -2.0)

    assert len(h1) == 64
    assert len(h2) == 64
    assert h1 != h2
    assert len(brain.memory_buffer) == 2

def test_skill_routing():
    brain = AlphaAlgoCognitiveBrain()
    # High uncertainty -> Defensive
    skill1 = brain.route_execution_skill({"volatility": 0.01}, epistemic_bound=0.4)
    assert skill1 == "DEFENSIVE_LIQUIDITY_PRESERVATION"

    # High volatility -> TWAP
    skill2 = brain.route_execution_skill({"volatility": 0.08}, epistemic_bound=0.1)
    assert skill2 == "HIGH_VOLATILITY_SLICE_TWAP"
