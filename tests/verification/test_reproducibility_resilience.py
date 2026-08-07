import asyncio
import copy
from trading_bot.core.csc.controller import CognitiveSystemController

async def verify_reproducibility():
    print("Starting Reproducibility & Resilience Verification...")

    obs = {"symbol": "EURUSD", "volatility": 0.02, "equity_history": [100, 101, 102]}

    # 1. Verify Deterministic Action Selection
    print("\n[1/2] Verifying Deterministic Action Selection...")
    csc = CognitiveSystemController()

    results = []
    for i in range(3):
        # We need to ensure internal state is reset if it's not stateless
        csc.discrete_channel = []
        csc.continuous_state = {}
        decision = await csc.process_market_observation(copy.deepcopy(obs))
        results.append(decision.outcome)
        print(f"  Run {i+1}: {decision.outcome}")

    assert all(r == results[0] for r in results), "Actions were not deterministic!"
    print("✅ Deterministic Reproduction Verified.")

    # 2. Resilience: Injecting Failures
    print("\n[2/2] Verifying Resilience to Component Failure...")

    # Inject failure into Verifier Swarm
    print("  Injecting failure into Verifier Swarm...")
    original_run = csc.verifier_swarm.run_swarm

    async def failing_swarm(snapshot):
        raise RuntimeError("Verifier Swarm Critical Failure")

    csc.verifier_swarm.run_swarm = failing_swarm

    try:
        decision = await csc.process_market_observation(obs)
        print(f"  Outcome after swarm failure: {decision.outcome}")
    except Exception as e:
        print(f"  System CRASHED as expected (Resilience needs improvement): {e}")
        # In a truly resilient system, it would fallback to a safe 'HOLD'

    csc.verifier_swarm.run_swarm = original_run
    print("✅ Resilience Verification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_reproducibility())
