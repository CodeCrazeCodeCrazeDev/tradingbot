# 03_RESEARCH_SYNTHESIS.md - Unified Scientific Foundation

## Objective
Synthesize multiple high-impact research directions into a single, coherent foundation for the AlphaAlgo World Model V3.

## Foundational Research Pillars

### 1. Agentic Predictive Planning (arXiv:2606.27483)
*   **Key Concept:** Internalizing the future. Training the model to generate multiple future trajectories and reasoning about them *before* acting.
*   **Application:** Replacing latent encoders with a capability-first "Imagination Engine."

### 2. State-Space sequence Models (Mamba-Family)
*   **Key Concept:** Selective State Spaces (S4) with associative scans. Linear scaling with sequence length.
*   **Application:** Efficiently processing years of high-frequency tick data and order-book snapshots without the quadratic memory cost of Transformers.

### 3. Structural Causal Models (CWMI / Pearl)
*   **Key Concept:** $do$-calculus and counterfactual reasoning. Distinguishing between observation ($P(y|x)$) and intervention ($P(y|do(x))$).
*   **Application:** Simulating the impact of institutional-sized orders and macro-economic shocks on the market.

### 4. Active Inference (Free Energy Principle / Friston)
*   **Key Concept:** Minimizing Variational Free Energy (VFE). Perceiving the world to minimize surprise; acting on the world to fulfill goals.
*   **Application:** The World Model as a Bayesian belief-updating engine that seeks to minimize "Expected Free Energy" in its plans.

### 5. Information Bottleneck & HIPIF
*   **Key Concept:** Compressing long histories into "sufficient statistics" for future prediction.
*   **Application:** Strategic folding of execution logs into the HMS Semantic Graph to prevent context-window saturation and strategic drift.

### 6. Probabilistic Trajectory Generation (Diffusion / Trajectory Transformers)
*   **Key Concept:** Modeling the full distribution of futures $P(\tau | s_t)$ rather than a point estimate.
*   **Application:** Generating diverse "Scenario Trees" (Bull, Bear, Flash Crash) using denoising diffusion or quantile regression.

### 7. Socratic Policy Optimization (SocraticPO)
*   **Key Concept:** Self-correcting reasoning via internal debate and feedback.
*   **Application:** The World Model "critiques" its own simulated futures by comparing them against the HMS "Research Memory."

## Synthesis: The "Capability-First" Unified Model

| Research Source | World Model V3 Capability |
| :--- | :--- |
| **arXiv:2606.27483** | Multi-horizon scenario generation and reasoning. |
| **Mamba** | Linear-scaling temporal backbone for HFT data. |
| **CWMI/Pearl** | Native $do(x)$ operator for market impact & macro shocks. |
| **Active Inference** | Bayesian objective for belief updating and planning. |
| **Diffusion** | High-fidelity probabilistic future sampling. |
| **HMS/HIPIF** | Strategic folding of market history into global memory. |

## References
* "Internalizing the Future: A Unified Agentic Training Paradigm for World Model Planning" (2026)
* "Mamba: Linear-Time Sequence Modeling with Selective State Spaces" (2023)
* "Causal World Models for Intervention" (2025)
* "Active Inference: The Free Energy Principle in Mind, Brain, and Behavior" (2022)
