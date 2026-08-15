
import asyncio
import sys
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.immutable_shield import shield

async def test_csc_v5_pipeline():
    print("Starting Tier 1 CSC Pipeline Verification (DiscoLoop/VFE)")

    # Mock HMS and World Model
    class MockHMS:
        async def retrieve_evidence_chain(self, obs): return []
        def store_ledger_entry(self, entry): pass
    class MockWM:
        async def generate_competing_branches(self, obs): return []
        async def simulate_branches(self, branches): return {}

    csc = CognitiveSystemController(world_model=MockWM(), hms=MockHMS(), shield=shield)

    # 1. Test Observation Processing with DiscoLoop and HASP
    print("Case 1: Observation Processing Pipeline")
    observation = {"market": {"volatility": 0.2}}

    # We expect it to run surprise calculation and DiscoLoop
    # (Since mock WM returns no branches, it will return TRADE_REJECTED at the end)
    result = await csc.process_market_observation(observation)

    print(f"CSC Result: {result.outcome}")
    print(f"VFE: {csc.variational_free_energy}")
    print(f"Discrete Embeddings: {csc.discrete_embeddings}")

    assert csc.variational_free_energy > 0
    assert "regime_shift_detected" in csc.discrete_embeddings
    assert csc.latent_hidden_state["reasoning_depth"] == 3

    print("PASS: DiscoLoop and VFE objective integrated in CSC")

    print("\nTier 1 CSC Verification COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_csc_v5_pipeline())
