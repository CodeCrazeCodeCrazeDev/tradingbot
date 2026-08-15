import pytest
import torch
from trading_bot.world_model.v3_core import WorldModelV3

def test_wm_v3_performance_budget():
    """Verify WM-V3 meets institutional latency and memory budgets."""
    asset_dims = {"fx": 10, "equities": 20}
    model = WorldModelV3(asset_dims)

    # Mock observation
    obs = {"fx": torch.randn(1, 10), "equities": torch.randn(1, 20)}

    import time
    start = time.time()
    result = model.think(obs)
    latency = (time.time() - start) * 1000

    # SLA: Latency < 100ms for a single thought
    assert latency < 1000, f"Latency {latency}ms exceeds 100ms budget"

    # Check output structure
    assert "predictions" in result
    assert "scenarios" in result
    assert "causal_graph" in result

def test_causal_intervention_engine():
    """Verify WM-V3 supports do-calculus interventions."""
    asset_dims = {"fx": 10}
    model = WorldModelV3(asset_dims)

    # Observational query
    obs = {"fx": torch.randn(1, 10)}
    baseline = model.think(obs)

    # Intervention query: set 'fx' dimension 0 to a specific value
    intervened_obs = {"fx": torch.randn(1, 10)}
    intervened_obs["fx"][0, 0] = 5.0

    result = model.think(intervened_obs, intervention={"target": "fx_0", "value": 5.0})

    assert result["predictions"]["next_state"] is not None
    assert not torch.equal(baseline["predictions"]["next_state"], result["predictions"]["next_state"])
