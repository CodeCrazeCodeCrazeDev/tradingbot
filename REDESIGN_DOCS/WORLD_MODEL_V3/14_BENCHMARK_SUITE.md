# 14_BENCHMARK_SUITE.md - Performance and Financial Metrics

## Objective
Define the specific benchmarks the World Model V3 must beat to be considered successful.

## 1. Predictive Benchmarks (The "M" Metrics)

| Metric | Target | Baseline (JEPA) |
| :--- | :--- | :--- |
| **Prediction Horizon** | 50 steps @ 90% conf | 10 steps @ 70% conf |
| **Calibration Error (ECE)** | < 0.05 | 0.15 - 0.20 |
| **Log-Loss (Price)** | < 0.001 | 0.005 |
| **Causal Adjacency Score** | > 0.90 | N/A (Correlation only) |

## 2. Planning Benchmarks (The "P" Metrics)

| Metric | Target | Baseline (Legacy) |
| :--- | :--- | :--- |
| **Expected Utility Accuracy** | > 0.85 correlation | < 0.60 correlation |
| **Plan Robustness Score** | > 0.75 | < 0.40 |
| **Reasoning Transparency** | 100% auditable | 0% (Black box) |

## 3. Engineering Benchmarks (The "E" Metrics)

| Metric | Target | Baseline (V1) |
| :--- | :--- | :--- |
| **Inference Latency** | < 100ms | 150ms+ |
| **Memory Throughput** | 10k items/s | 1k items/s |
| **Training Efficiency** | $O(N)$ (Mamba) | $O(N^2)$ (Transformer) |

## 4. Financial Alpha Benchmarks (The "A" Metrics)

| Metric | Target |
| :--- | :--- |
| **Sharpe Ratio (OOS)** | > 3.5 |
| **Sortino Ratio (OOS)** | > 5.0 |
| **Max Drawdown (Institutional)** | < 8% |
| **Slippage Reduction** | > 20% compared to zero-foresight |
| **Execution Savings** | > 2bps per trade |

## 5. Benchmarking Dataset
The suite must be run on the **AlphaAlgo Gold Standard Dataset**:
*   **EURUSD:** High-volatility news events.
*   **S&P 500 E-mini:** Microstructure / order-book depth changes.
*   **BTCUSD:** Regime shifts and tail risk events.
*   **Period:** Jan 2021 - Dec 2025 (Cross-validation on 2026 data).
