# 13_VALIDATION_FRAMEWORK.md - Institutional Testing Protocols

## Objective
Establish a rigorous framework to validate the World Model V3 before deployment.

## 1. Multi-Dimensional Validation

### A. Prediction Fidelity (Numerical)
*   **Metric:** Log-Likelihood of realized outcomes under the predicted distribution.
*   **Check:** Does the model's Scenario Set cover the actual market trajectory 95% of the time?

### B. Calibration Accuracy (Probabilistic)
*   **Metric:** Expected Calibration Error (ECE).
*   **Check:** If the model predicts a 90% probability for Scenario A, does it occur 90% of the time in out-of-sample testing?

### C. Causal Faithfulness (Structural)
*   **Metric:** Interventional KL-Divergence.
*   **Check:** Does $P(y | do(x))$ (simulated impact) match the realized impact when the trade is executed in the `BacktestEngine` with L2 liquidity?

### D. Strategic Coherence (Agentic)
*   **Metric:** Plan Robustness.
*   **Check:** Does the selected plan remain optimal even if Scenario C (Adverse) occurs?

## 2. The "Red Team" Adversarial Test
We use an **Adversarial Market Generator** (part of `synthetic_data.py`) to challenge the World Model with:
*   **Regime Shifts:** Instant transitions from Bull to Bear.
*   **Flash Crashes:** Extreme liquidity withdrawal.
*   **Data Poisoning:** Simulated "Bad Ticks" or news-headline noise.

## 3. Backtest-to-Sim Alignment
We compare the World Model's simulated rewards with the rewards calculated by the gold-standard `BacktestEngine`.
*   **Acceptance Criteria:** Correlation between Simulated Utility and Realized Utility > 0.85.

## 4. Reasoning Audit
A panel of human traders or a "Superior Auditor LLM" reviews 100 randomly selected Reasoning Traces.
*   **Check:** Is the logic sound? Are the causal links explainable? Does it cite correct evidence from the HMS?

## 5. Performance Benchmarks
*   **Max Drawdown (Simulated vs Realized):** Error < 5%.
*   **Sharpe (Simulated vs Realized):** Error < 10%.
*   **Inference Latency:** 99th percentile < 150ms.
