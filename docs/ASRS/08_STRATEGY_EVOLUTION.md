# 08. STRATEGY EVOLUTION
## Strategy Evolution Laboratory & Quantitative Fitness Functions

### 1. Architectural Mission
The **Strategy Evolution Laboratory (SEL)** is the quantitative trading strategy incubator of ASRS. It operates entirely independently of the AI/Agent-harness evolution framework.

The SEL is dedicated exclusively to discovering, optimizing, and validating trading strategies. Its domain covers signal generation models, execution algorithms (TWAP, VWAP, Smart routing), dynamic portfolio allocation, hedging rules, stop placement, and dynamic risk limits.

---

### 2. Multi-Objective Quantitative Fitness Function
Trading strategies are evaluated across a highly rigorous, multi-dimensional mathematical landscape. To prevent overfitting to specific backtest periods and to penalize unrealistic trading behaviors, the SEL computes a **Unified Portfolio Fitness Score (UPFS)**:

$$\text{UPFS} = w_{\text{sharpe}} \cdot S_r + w_{\text{sortino}} \cdot S_o + w_{\text{drawdown}} \cdot C_a - w_{\text{risk}} \cdot \text{CVaR} - w_{\text{turnover}} \cdot T_p - w_{\text{cost}} \cdot E_c$$

Where:

* **Sharpe Ratio ($S_r$)** (Weight: 25%): Risk-adjusted return based on annualized excess return over portfolio volatility:
  $$S_r = \frac{\mathbb{E}[R_p - R_f]}{\sigma_p}$$
* **Sortino Ratio ($S_o$)** (Weight: 20%): Risk-adjusted return focusing exclusively on downside deviation:
  $$S_o = \frac{\mathbb{E}[R_p - R_f]}{\sigma_{\text{down}}}$$
* **Calmar Ratio ($C_a$)** (Weight: 15%): Ratio of annualized return to maximum historical drawdown:
  $$C_a = \frac{\text{Annualized Return}}{\text{Max Drawdown}}$$
* **Conditional Value at Risk ($\text{CVaR}$)** (Weight: 15%): The expected loss given that the loss exceeds the Value-at-Risk threshold at confidence level $\alpha = 0.95$:
  $$\text{CVaR}_{\alpha} = \mathbb{E}[L \mid L \ge \text{VaR}_{\alpha}]$$
* **Turnover Penalty ($T_p$)** (Weight: 15%): Penalizes excessive trading and high frequency churn, reducing strategy viability in high-impact environments:
  $$T_p = \frac{1}{N} \sum_{t=1}^N \sum_{i=1}^M |w_{i, t} - w_{i, t^-}|$$
* **Execution Cost Model ($E_c$)** (Weight: 10%): Integrates realistic slippage, commission, and estimated market impact:
  $$E_c = \text{Commission} + \text{Slippage}_{\text{bps}} + \gamma \cdot \left(\frac{\text{Volume}_{\text{trade}}}{\text{Volume}_{\text{market}}}\right)^2$$

---

### 3. Simulation & Execution Verification Loop
Every strategy proposed by the SEL undergoes a multi-stage execution check before being flagged as a promotion candidate:

```
  +--------------------------------------------------------+
  |                   STRATEGY TESTING PIPELINE            |
  +--------------------------------------------------------+
  |                                                        |
  |  (1) Multi-Regime Historical Backtest                  |
  |      - Run across 5+ years of M15 tick data            |
  |      - Ensure zero lookahead bias / leakage            |
  |                                                        |
  |  (2) Walk-Forward Optimization (WFO)                   |
  |      - In-Sample (IS) training vs. Out-of-Sample (OOS) |
  |      - Confirm no parameters collapse in OOS           |
  |                                                        |
  |  (3) Monte Carlo Permutation                           |
  |      - Scramble returns / resample execution noise      |
  |      - Assess probability of ruin and drawdown limits  |
  |                                                        |
  |  (4) Liquidity-Adjusted VaR Test                       |
  |      - Simulate market order book depth constraints    |
  |      - Ensure slippage models hold under stress        |
  |                                                        |
  +--------------------------------------------------------+
```

---

### 4. Regime-Aware Fitness Scaling
The SEL ensures that strategies do not over-perform on a single regime (e.g., highly trending bull market) while losing capital in others (e.g., choppy, high-volatility sideways market).

Backtest returns are partitioned into four distinct historical regimes (Trending Bull, Trending Bear, Volatile Range, Low-Vol Range) detected via the `regime_detection` engine. The global fitness is scaled down by the variance of returns across these regimes, ensuring **Regime Robustness**:

$$\text{Regime Robustness} = 1.0 - \text{Var}\left(\mathbb{E}[R_p \mid \text{Regime}_k]\right)$$

A candidate strategy that scores moderately across all regimes is highly prioritized over a strategy that performs exceptionally in one regime but suffers catastrophic drawdowns in another.
