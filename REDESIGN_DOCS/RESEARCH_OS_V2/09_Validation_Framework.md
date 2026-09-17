# 09. Statistical Validation and Overfitting Framework

This document specifies the advanced statistical metrics and overfitting protections implemented in the Research OS V2.

---

## 1. Multiple Testing Correction: Deflated Sharpe Ratio (DSR)

To protect against selection bias (p-hacking) during iterative backtesting, the Research OS V2 implements Bailey and Lopez de Prado's **Deflated Sharpe Ratio (DSR)**.

### Mathematical Formulation

Given an observed Sharpe Ratio $SR_0$ calculated from a backtest with $N$ bars, and a historical search process where $M$ independent trials were executed, the expected maximum Sharpe Ratio ($E[SR_{max}]$) under the null hypothesis of zero alpha is:

$$E[SR_{max}] = \sqrt{\text{Var}[SR]} \left( (1-\gamma)\Phi^{-1}\left(1 - \frac{1}{M}\right) + \gamma\Phi^{-1}\left(1 - \frac{1}{M e}\right) \right)$$

where:
*   $\text{Var}[SR]$ is the variance of the nominal Sharpe Ratios across all $M$ trials.
*   $\gamma \approx 0.577215$ is the Euler-Mascheroni constant.
*   $\Phi^{-1}$ is the cumulative standard normal inverse function.

The standard deviation of the observed Sharpe Ratio distribution ($\sigma_{SR}$) accounting for non-normality (skewness $\hat{s}$ and kurtosis $\hat{k}$) is:

$$\sigma_{SR} = \sqrt{\frac{1 + \frac{1 + \hat{s} \cdot SR_0}{4} SR_0^2 - \hat{s} \cdot SR_0^3 + \frac{\hat{k}-1}{4} SR_0^4}{N - 1}}$$

The Deflated Sharpe Ratio (DSR) is the probability that the actual Sharpe is greater than zero after correcting for the maximum expected Sharpe:

$$\text{DSR} = \Phi\left( \frac{SR_0 - E[SR_{max}]}{\sigma_{SR}} \right)$$

*   **Rule:** For a strategy to be approved, its **DSR must be $\ge 0.95$** (equivalent to a 5% significance level).

---

## 2. Advanced Validation Schemes

### 2.1 Walk-Forward Split (WFA) with Purging
To prevent leakage across training and test splits, the validator enforces **Purged Walk-Forward splits**.
*   **Purging:** Removes historical data points near the training/testing boundary. This ensures that features incorporating lookbacks or lagged filters (such as moving averages) do not carry information from the training split into the test split.

### 2.2 Relative Benchmarking
A strategy cannot be evaluated in isolation. It must yield statistically significant outperformance over multiple baselines simultaneously.
*   The validator automatically executes the strategy against a series of baseline models (e.g., Buy & Hold, Simple Crossover, Random Wald, and basic Linear Regression models) over identical historical splits.
*   **Ablation Check:** If a simple technical crossover model yields identical risk-adjusted returns to a complex machine learning strategy, the complex strategy is **REJECTED** due to unnecessary model complexity.
