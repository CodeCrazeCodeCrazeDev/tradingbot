# ADR-004: Transition to Predictive Planning World Model (WM-V3)

## Status
Proposed

## Context
The current AlphaAlgo World Model relies on a JEPA-based latent transition architecture (V1) or a fragmented hybrid skeleton (V2). These models lack explicit causal reasoning, future scenario branching, and execution-grounding. They also maintain isolated memory states, violating the "One Brain" principle of the UCA-2026.

## Decision
We will replace the entire World Model subsystem with a **Predictive Planning Engine (WM-V3)**.

### Key Technical Decisions:
1.  **Backbone:** Standardize on **Mamba-family State-Space Models** for the temporal core to achieve linear-time scaling with high-frequency market data.
2.  **Paradigm Shift:** Move from "Next-State Latent Prediction" to "Multi-Horizon Scenario Generation" (Capability-First).
3.  **Causality:** Implement a **Hybrid Structural Causal Model (SCM)** using Pearl's $do$-calculus to model action-as-cause and macro interventions.
4.  **Memory:** Full integration with the **Hierarchical Memory System (HMS)**. The World Model will have no internal persistent state.
5.  **Uncertainty:** Use **Diffusion-based Probabilistic Generation** to capture the full multi-modal distribution of future market states.

## Alternatives Considered

### 1. Extending JEPA (V1)
*   **Reason for Rejection:** JEPA is fundamentally designed for latent representation matching. Adding multi-horizon branching and causal interventions would require "hacking" the architecture into something it wasn't meant to be, leading to significant technical debt.

### 2. Pure Transformer Architecture
*   **Reason for Rejection:** Quadratic memory cost $(O(N^2))$ makes Transformers unsuitable for long-horizon planning with years of tick-level context.

### 3. Isolated World Model Memory
*   **Reason for Rejection:** Violates UCA-2026 principles. Leads to "split-brain" syndrome where different agents have divergent world beliefs.

## Consequences

### Positive
*   **Institutional Explainability:** Reasoning traces and causal graphs provide clear audit trails for every trade.
*   **Improved Alpha:** Better foresight of execution dynamics (slippage/impact) directly improves net PnL.
*   **Scalability:** Mamba backbone allows for massive history context and multi-asset modeling.

### Negative
*   **Training Complexity:** Requires a complex 3-stage pipeline (WM-AMT, FE-SFT, FC-RL).
*   **No Backward Compatibility:** Requires full retraining and fresh HMS initialization.
*   **High Inference Cost:** Multi-scenario diffusion rollouts require dedicated GPU resources.

## References
* arXiv:2606.27483
* REDESIGN_DOCS/WORLD_MODEL_V3/01-16
