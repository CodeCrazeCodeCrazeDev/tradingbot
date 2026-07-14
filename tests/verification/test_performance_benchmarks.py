import asyncio
import time
import statistics
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem

async def run_performance_benchmark():
    print("Starting UCA V5 Performance Benchmarking...")

    hms = HierarchicalMemorySystem("bench_hms")
    csc = CognitiveSystemController(hms=hms)
    obs = {"symbol": "EURUSD", "volatility": 0.02, "equity_history": [100, 101, 102]}

    latencies = []
    num_runs = 10

    print(f"\nRunning {num_runs} end-to-end cycles...")
    for i in range(num_runs):
        start = time.perf_counter()
        # Reset internal state to simulate fresh cycle
        csc.discrete_channel = []
        csc.continuous_state = {}

        await csc.process_market_observation(obs)

        end = time.perf_counter()
        latencies.append((end - start) * 1000) # ms

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)

    print(f"\nResults (N={num_runs}):")
    print(f"  Average E2E Latency: {avg_latency:.2f}ms")
    print(f"  P95 E2E Latency:     {p95_latency:.2f}ms")

    # Stage-wise estimation (using internal timing if instrumented, or approximations)
    # Verification Swarm has a sleep(0.1) * K verifiers (but run in parallel)
    print("\nStage Breakdown (Estimated):")
    print("  CSC Reasoning (DiscoLoop): < 5ms")
    print("  Verification Swarm:        ~105ms")
    print("  SAGE/HMS Storage:          < 10ms")

    # SLA Check
    if avg_latency < 500:
        print("\n✅ Institutional SLA (<500ms) SATISFIED.")
    else:
        print("\n❌ Institutional SLA (<500ms) VIOLATED.")

if __name__ == "__main__":
    asyncio.run(run_performance_benchmark())
