# Improvement Validation Report Specification (RSI-VALIDATION-2026)

## 1. Out-of-Sample (OOS) Validation Guidelines

To eliminate data leakage, lookahead bias, and overfitting, all candidate improvements must undergo a rigorous **OOS Validation Sequence** before they can proceed to human review:

### Cross-Validation & Separation
*   **Purged and Embargoed Partitioning:** The training set and the OOS test set are separated by an embargo window of at least **5 days** (to prevent leakage via serial correlation or overlapping indicators).
*   **Combinatorial Purged Cross-Validation (CPCV):** Evaluates strategy paths across multiple historical splits, ensuring that candidate performance is not a product of a single advantageous historical period.
*   **Multiple-Testing Adjustment:** Any performance claim must adjust the standard critical values using the **False Discovery Rate (FDR)** or **Bonferroni corrections** to account for the number of trial iterations ran.

---

## 2. Adversarial Falsification Stress Tests

An improvement must remain highly resilient under adverse market conditions. The candidate is subjected to **Adversarial Falsification Testing** by replaying specific high-stress historical scenarios:

| Scenario Code | Historical Market Scenario | Target Stress Condition | Minimal Permitted standard | Candidate Outcome Status |
| :--- | :--- | :--- | :--- | :--- |
| **ST-01** | May 2010 Flash Crash | Extreme multi-asset liquidity evaporation | Max drawdown < 1.1x VaR | PASSED |
| **ST-02** | March 2020 COVID Spillover | High volatility & rapid regime transition | Zero execution / latency timeout | PASSED |
| **ST-03** | January 2015 CHF Cap Removal | Liquidity void & spread widening | Absolute stop-loss enforcement | PASSED |

---

## 3. Walk-Forward Verification

The validation system utilizes a strict recursive walk-forward approach:
*   **Rolling Window Calibration:** Models are fitted on a rolling window and evaluated on an immediate, unseen future block.
*   **Regime-Specific Attribution:** Performance metrics are computed separately across categorized regimes (Low Volatility Mean Reverting, High Volatility Trending, and Transitional Shock Regimes) to verify that improvement is consistent and not purely optimized for one specific market condition.
*   **Complexity Penalty Assessment:** Candidates are penalized according to their parameter count. A candidate with higher complexity must demonstrate a statistically superior capability index ($\ge 5\%$) to survive over simpler, lower-complexity alternatives.
