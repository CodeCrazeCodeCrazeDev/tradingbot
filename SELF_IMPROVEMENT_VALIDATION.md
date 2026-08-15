# Scientific Self-Improvement Validation Protocol

This document defines the quantitative validation protocol used to evaluate self-improvement candidates, ensuring that no apparent improvement is caused by data leakage, overfitting, or evaluator gaming.

---

## 1. Out-of-Sample Walk-Forward Validation

To evaluate a candidate strategy or model change, we use a non-overlapping, temporal walk-forward split to replicate real-world trading conditions:

```
[In-Sample Train/Tune] ──> [Untouched Out-of-Sample Validation] ──> [Regime Stress Test]
      (60% Data)                       (30% Data)                     (10% Data)
```

### Constraints:
*   **Zero Leakage**: No statistics from the out-of-sample dataset (mean, standard deviation, target distributions) may enter the feature engineering or training pipeline of the candidate.
*   **Transaction Costs**: All simulations must enforce realistic execution fees:
    - *Slippage*: Minimum of 1.5 basis points (BPS) per side.
    - *Commission*: Minimum of 0.5 BPS per side.
*   **Liquidity Constraints**: Positions are scaled proportional to order book depth, penalizing large quantities with exponential market-impact cost modeling.

---

## 2. Multi-Regime Performance Comparison

A candidate is audited across four distinct historical regimes to ensure robust stability:

| Metric | Baseline (Parent v5) | Candidate (v6) | Out-of-Sample Gain | Drawdown Impact | Regime Stability | Latency Delta | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **High-Vol Bear** (Aug 2024) | Sharpe: 1.25, DD: 4.2% | Sharpe: 1.54, DD: 3.5% | +0.29 Sharpe | Improved | Highly Stable | +2.1ms | **APPROVED** |
| **Low-Vol Bull** (Feb 2024) | Sharpe: 2.10, DD: 1.8% | Sharpe: 2.22, DD: 1.5% | +0.12 Sharpe | Improved | Stable | +1.5ms | **APPROVED** |
| **Mean-Reverting Range** | Sharpe: 0.95, DD: 3.1% | Sharpe: 1.10, DD: 2.8% | +0.15 Sharpe | Stable | Stable | +1.8ms | **APPROVED** |
| **Tail-Risk Event** (Mar 2020) | Sharpe: -0.45, DD: 12% | Sharpe: -0.12, DD: 7.8%| +0.33 Sharpe | Improved | Resilient | +2.5ms | **APPROVED** |

---

## 3. Multiple-Testing Correction

When testing hundreds of candidate changes, false discoveries arise by chance. AlphaAlgo applies the **Benjamini-Hochberg (FDR) Procedure** to adjust p-values and control the false discovery rate:
$$P_{(i)} \le \frac{i}{m} \alpha$$
Where $m$ is the total number of tested candidates. An improvement candidate is only promoted if its adjusted p-value remains below $\alpha = 0.05$.
