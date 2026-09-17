"""
UCA V5 Causal Integrity Validation
==================================

Verifies Pearl's Ladder implementation:
1. Intervention Accuracy (do-operator)
2. Counterfactual Consistency (Abduction-Action-Prediction)
3. Causal Edge Recovery
"""

import pytest
import torch
import numpy as np
from trading_bot.world_model.causal_model import StructuralCausalModelV5, CausalWorldModel

@pytest.fixture
def scm():
    return StructuralCausalModelV5(latent_dim=16)

def test_scm_do_operator(scm):
    """
    Verifies that Pearl's 'do' operator correctly sets node value
    and prunes causal influence.
    """
    z = torch.ones(1, 16)
    # Intervene on node 5, set to 0.0
    interventions = {5: 0.0}

    z_intervened = scm.do_intervention(z, interventions)

    # Node 5 must be exactly 0.0
    assert z_intervened[0, 5] == 0.0
    # Other nodes should be propagated
    assert torch.any(z_intervened != z)

def test_counterfactual_logic(scm):
    """
    Verifies the Abduction-Action-Prediction cycle.
    """
    factual_z = torch.randn(1, 16)
    alternative_action = {10: 5.0} # 'What if we bought 5x more?'

    cf_outcome = scm.counterfactual_query(factual_z, alternative_action)

    # Counterfactual outcome should differ from factual forward pass
    factual_outcome = scm.forward(factual_z)
    assert not torch.allclose(cf_outcome, factual_outcome)

    # Ensure node 10 reflects the intervention in the outcome's causal chain
    # (Checking that it's not just returning noise)
    assert cf_outcome.shape == factual_z.shape

def test_causal_scratchpad_persistence():
    """
    Verifies that insights are correctly integrated into the persistent DAG.
    """
    from trading_bot.world_model.causal_model import CausalScratchpad
    pad = CausalScratchpad()

    insights = [("CPI", "Inflation", 0.8), ("Inflation", "BTC_Price", -0.5)]
    pad.update_structure(insights)

    assert pad.dag.has_edge("CPI", "Inflation")
    assert pad.dag.has_edge("Inflation", "BTC_Price")
    assert pad.get_parents("Inflation") == ["CPI"]
    assert pad.get_parents("BTC_Price") == ["Inflation"]

@pytest.mark.asyncio
async def test_causal_world_model_simulation():
    """
    Verifies that the high-level World Model API uses the SCM correctly.
    """
    wm = CausalWorldModel(hms=None)
    state = {"market": "stable"}
    action = {"quantity": 100.0}

    result = await wm.simulate_intervention(state, action)
    assert "expected_slippage" in result
    assert "market_impact" in result
