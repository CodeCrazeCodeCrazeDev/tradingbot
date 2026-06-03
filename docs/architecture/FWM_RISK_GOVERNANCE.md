# FWM: Governance & Risk World Model (The Veto Layer)

## 1. The Shadow World Model
Institutional-grade survival requires a **Separation of Concerns**. We implement a "Shadow" World Model that is trained with an adversarial objective: **Find the path to maximum drawdown.**

### Risk States Tracked
*   **Correlation Breakdowns:** Modeling when "diversified" strategies suddenly align during panic.
*   **Liquidity Voids:** Forecasting the sudden disappearance of the order book.
*   **Tail Risk (3-Sigma+):** Using Extreme Value Theory (EVT) mapped to latent space.
*   **Model Drift:** Real-time monitoring of how much current market reality diverges from the training distribution.

## 2. The Veto Hierarchy
The Risk World Model sits at Layer 2 (RISK) of the Intelligence Core hierarchy. It has **Unilateral Veto Power** over any trade proposal from the Predictor or Strategy layers.

| Logic | Veto Condition | Recovery Action |
| :--- | :--- | :--- |
| **Ignorance Gate** | Epistemic Uncertainty > 0.8. | HALT: Stop all trading until clarity returns. |
| **Fragility Gate** | Liquidity Condition is "ILLIQUID" or "THIN". | REDUCE_RISK: Cut position sizes by 75%. |
| **Axiom Gate** | Trade violates immutable survival axioms. | BLOCK: Trade is rejected; developer alert. |
| **Regime Gate** | Predicted regime transition probability > 40%. | DEFENSIVE: Move to cash/neutral hedges. |

## 3. Stress Simulation
Before any large capital allocation, the Risk Model runs **10,000 Hostile Simulations**:
1.  Identify the "Worst Case" agent behavior (e.g. HFTs becoming toxic).
2.  Simulate the strategy's response to that behavior.
3.  If any simulation path leads to a breach of the Max Acceptable Drawdown, the allocation is denied.
