# Baseline Benchmarking Plan

## Objective
Establish a reproducible baseline for the current AlphaAlgo system before Phase B evolution.

## 1. System Performance
- **Component Discovery Latency**: Time to retrieve components from `UnifiedComponentRegistry`.
- **Event Bus Throughput**: Messages per second through `UnifiedDecisionBus`.
- **Memory Access Latency**: HMS tier retrieval times.

## 2. Intelligence Metrics
- **Hypothesis Quality**: Bayesian evidence synthesis success rate in `intelligence_core`.
- **World Model Accuracy**: Multi-step prediction error (MSE) for market regimes.
- **Reasoning Calibration**: Alignment between plan confidence and execution success.

## 3. Risk & Safety
- **Circuit Breaker Trip Time**: Latency from risk threshold breach to shutdown.
- **Shield Overhead**: Performance impact of `ImmutableShield` validation.

## 4. Execution
- Baseline test in `tests/uca_vs_legacy_bench.py` to compare CSC-driven vs. Legacy-driven performance.
