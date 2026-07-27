import torch
import numpy as np
from trading_bot.world_model.causal_model import CausalWorldModel, CausalScratchpad
from trading_bot.world_model.counterfactual_engine import CounterfactualEngine, MarketFact

def test_causal_discovery():
    print("Testing Causal Discovery...")
    scratchpad = CausalScratchpad()
    links = [("YieldCurve", "BankLiquidity", 0.9), ("BankLiquidity", "BTCPricce", 0.7)]
    scratchpad.update_structure(links)

    path = scratchpad.get_causal_path("YieldCurve", "BTCPricce")
    print(f"Causal Path: {path}")
    assert path == ["YieldCurve", "BankLiquidity", "BTCPricce"]

    # Test cycle breaking
    links_with_cycle = [("BTCPricce", "YieldCurve", 0.1)]
    scratchpad.update_structure(links_with_cycle)
    assert len(scratchpad.dag.edges) == 2 # Weakest link should be broken if cycle detected
    print("Cycle breaking verified.")

def test_do_calculus():
    print("Testing Pearl's do-calculus...")
    hms = None # Mock
    cwm = CausalWorldModel(hms)

    z = torch.ones(1, 512)
    # factual prediction
    factual = cwm.scm.forward(z)

    # intervention: set latent 42 to 0.0
    interventions = {42: 0.0}
    counterfactual = cwm.scm.do_intervention(z, interventions)

    assert not torch.equal(factual, counterfactual)
    print("Do-calculus rollout complete.")

def test_counterfactual_cycle():
    print("Testing Abduction-Action-Prediction...")
    cwm = CausalWorldModel(None)
    engine = CounterfactualEngine(cwm)

    state_z = torch.randn(1, 512)
    action_idx = 42
    action_val = 1.0
    # factual outcome
    outcome_z = cwm.scm.forward(state_z) + 0.05 # Adding some noise

    fact = MarketFact(state_z, action_idx, action_val, outcome_z)

    # Alternative: action = 0.0
    alt_outcome = engine.run_counterfactual_cycle(fact, {action_idx: 0.0})

    analysis = engine.analyze_trade_attribution(fact)
    print(f"Attribution Analysis: {analysis}")
    assert "causal_impact_magnitude" in analysis
    print("Counterfactual cycle verified.")

if __name__ == "__main__":
    test_causal_discovery()
    test_do_calculus()
    test_counterfactual_cycle()
    print("✅ All CWM V6 Verifications Passed")
