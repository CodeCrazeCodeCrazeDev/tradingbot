# FWM: Regime Engine & Transition Modeling

## 1. Multi-Dimensional Regime Classification
Unlike standard HMMs (Hidden Markov Models), the FWM uses a **Latent Topological Embedding** to identify regimes. A regime is defined by the stability of causal relationships between variables.

| Dimension | Binary States | Institutional Nuance |
| :--- | :--- | :--- |
| **Price Trend** | Bull / Bear | Trend Strength & Decay Rate. |
| **Volatility** | Low / High | Vol-of-Vol & Skew Term Structure. |
| **Liquidity** | Deep / Thin | Order Book Fragility & Resilience. |
| **Correlation** | Stable / Broken | Multi-asset dispersion levels. |
| **Information** | Symmetric / Asymmetric | Flow toxicity & Informed trade presence. |

## 2. Transition Modeling: Phase Transitions
The FWM models regime shifts not as random jumps, but as **Causal Phase Transitions**:

1.  **Lead-Up:** Accumulation of latent inventory risk (e.g., Dealers becoming short Gamma).
2.  **Trigger:** An external or internal event (e.g., CPI print, large block trade).
3.  **Reflexive Feedback:** L1 dynamics (fast) trigger L2 jumps (slow).
4.  **New Equilibrium:** The system stabilizes in a new causal state (e.g., Trend-Following becomes Mean-Reverting).

## 3. Structural Transition Detection
The system monitors the **Reconstruction Loss** and **Prediction Error Acceleration**.
*   If the model's prediction error in the L1 (Fast RSSM) accelerates while the L2 (Macro) remains stable, it flags a **Structural Transition** (the rules of the current regime have changed).
*   This triggers the **Scientist Engine** to begin a new research cycle to update the world model's weights.
