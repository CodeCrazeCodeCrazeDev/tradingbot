# FWM: Scenario Reasoning & Counterfactual Engine

## 1. Do-Calculus in Latent Space
Standard scenario analysis ("What if SPX drops 5%?") is linear and flawed. The FWM uses **Causal Interventions** (Pearl's Do-Calculus) to modify latent states:

*   **Operator:** $do(z_{liquidity} = \min)$
*   **Response:** The World Model propagates this change through the agent interaction network.
*   **Result:** Not just a price change, but a sequence of structural consequences (e.g. "Dealer hedging triggers stop-losses, leading to a 12% gap").

## 2. Scenario Probability Assignment
Probabilities are not derived from frequency (history), but from **Structural Path Likelihood**:
1.  Generate 1,000 potential paths.
2.  Assign each path a likelihood based on the transition probabilities of the Hierarchical RSSM.
3.  Filter for "High Confidence" scenarios where Epistemic Uncertainty is low.

## 3. Counterfactual Reasoning Examples

| Shock Type | Latent Variable Modification | Reasoned Outcome |
| :--- | :--- | :--- |
| **Rate Hike** | $do(z_{macro\_rate} + 25bps)$ | CTA deleveraging flow simulation. |
| **Geopolitical** | $do(z_{tail\_risk} = 1.0)$ | Correlation convergence to 1.0. |
| **Flash Crash** | $do(z_{hft\_toxicity} = 1.0)$ | Liquidity vacuum and limit-down gaps. |

## 4. Reasoning Loop
The system continuously asks:
*   "What is the most fragile part of the current latent state?"
*   "If that variable shifts, what is the probability of regime contagion?"
*   "Are we positioned for the most likely path, or the most robust path?"
