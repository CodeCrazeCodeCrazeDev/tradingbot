# Financial World Model (FWM): Institutional Blueprint

## Executive Summary
The AlphaAlgo Financial World Model is a **Generative Digital Twin** of global financial markets. Unlike traditional trading systems that predict price, the FWM models the **Hidden States** (Liquidity, Positioning, Information Asymmetry) and **Causal Mechanisms** that generate price. It operates as a Hierarchical Neural State-Space Model, capable of reasoning about regimes and counterfactual scenarios.

---

## 1. Unified Architecture Hierarchy

### L1: Perception & Discovery (The Fast Path)
*   **Engine:** Mamba-based State-Space Model (SSM).
*   **Input:** L3 tick data, L2 order book, passive/aggressive flow.
*   **Output:** `z_micro` - Real-time liquidity and toxicity embedding.

### L2: Conceptual Synthesis (The Global Path)
*   **Engine:** Transformer with cross-modal attention.
*   **Input:** `z_micro`, Dealer Gamma/Vanna surfaces, Macro CPI/Rates, News embeddings.
*   **Output:** `z_macro` - Regime classification and structural stability score.

### L3: Generative Dynamics (The Dreamer)
*   **Engine:** Skip-Graph RSSM (Recurrent State-Space Model).
*   **Function:** Simulates the interaction of 7 agent types (Retail, HFT, Dealers, CTAs, etc.) to project $S_{t+H}$ across 10,000 paths.
*   **Causal Layer:** Pearl’s Do-Calculus for "What-If" intervention reasoning.

### L4: The Veto Layer (Governance)
*   **Engine:** Adversarial "Shadow" World Model.
*   **Logic:** Block any action where Epistemic Uncertainty > 0.8 or Liquidity Fragility > Threshold.

---

## 2. Core Capabilities

### State Understanding
*   **Inventory Risk:** Tracking dealer positioning to forecast gamma-squeezes.
*   **Information Asymmetry:** Detecting informed flow before it impacts price.

### Forecasting & Reasoning
*   **Scenario Reasoning:** Identifying the "Robust Path" that survives across multiple regime transitions.
*   **Counterfactual Analysis:** Reasoning about the impact of a 50bps hike on CTA deleveraging.

### Self-Improvement
*   **Structural Memory:** Remembering "Why" a failure occurred (e.g. "Correlation breakdown during low depth") rather than just tracking PnL.

---

## 3. Implementation Pathway

1.  **Phase 1: The Micro-Engine.** Implement the Mamba-RSSM stack for high-fidelity tick dynamics.
2.  **Phase 2: The Digital Twin.** Build the agent-based simulator focusing on Dealer Hedging flows.
3.  **Phase 3: The Causal Gate.** Integrate Do-Calculus for macro scenario reasoning.
4.  **Phase 4: The Governor.** Enforce survival axioms via the Risk Shadow Model.

---

## 4. Vision
The end goal is a system where the AI does not just "predict price," but acts as a **Lead Portfolio Manager** that reasons through the causal structure of the global economy, respects the fragility of liquidity, and prioritizes **Structural Survival** over simple returns.
