import cProfile
import pstats
import time
import numpy as np
import pandas as pd
from trading_bot.ml.reinforcement import StrategyOptimizer
from trading_bot.ml.predictive_models import PricePredictor

def run_pipeline():
    """Simulates a heavy workload to profile feature extraction and model prediction."""
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.normal(0, 0.5, 10000))  # 10k ticks
    df = pd.DataFrame({
        'open': prices - 0.5,
        'high': prices + 0.5,
        'low': prices - 0.5,
        'close': prices,
        'volume': [1000] * 10000
    })

    predictor = PricePredictor()
    X = predictor.prepare_features(df)

    optimizer = StrategyOptimizer()
    states = optimizer.define_state_space(df)

def main():
    print("=== Execution Pipeline Profiling ===")

    # Measure execution latency
    latencies = []
    for _ in range(5):
        start = time.perf_counter()
        run_pipeline()
        latencies.append((time.perf_counter() - start) * 1000)

    print(f"Mean Latency: {np.mean(latencies):.2f}ms")
    print(f"P95 Latency:  {np.percentile(latencies, 95):.2f}ms")
    print(f"P99 Latency:  {np.percentile(latencies, 99):.2f}ms")

    # Profile CPU hotspots and write report
    profiler = cProfile.Profile()
    profiler.enable()
    run_pipeline()
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    print("\n--- CPU Hotspots (Top 15 Cumulative Time) ---")
    stats.print_stats(15)

if __name__ == '__main__':
    main()
