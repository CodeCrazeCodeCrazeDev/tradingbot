# Scientific Synthesis: Superior Architecture UCA V4 (2026)

This document synthesizes 24+ high-impact research papers into the Unified Cognitive Architecture V4 (UCA V4) for AlphaAlgo.

---

## 1. Unified Design Philosophy: "Recursive Active Inference"
UCA V4 moves beyond sequential pipelines into a **Recursive Active Inference** framework. Every cognitive step (Perception, Planning, Execution) is treated as an intervention on a causal world model, governed by the minimization of Variational Free Energy (VFE).

---

## 2. Component Architectures (Synthesized)

### 2.1. Cognitive System Controller (CSC) - The Recursive Brain
*   **Loop Architecture**: Implements **DiscoLoop** recurrence, maintaining dual channels:
    -   *Discrete Channel*: Strategic subgoals and semantic bridge tokens.
    -   *Continuous Channel*: Latent world-state embeddings and uncertainty vectors.
*   **Information Folding**: Integrates **HIPIF** `FoldingOperator` directly into the O-S-A loop. Completed subgoals are folded into "sufficient statistics" to prevent context-window saturation.
*   **Planning**: Hierarchical decomposition with **AutoResearchClaw** `Pivot/Refine` logic. If a simulation branch fails, the CSC "pivots" the latent strategy before re-execution.

### 2.2. Hierarchical Memory System (HMS) - The Agentic Substrate
*   **Evolutionary Graph**: Replaces static RAG with **SAGE** (Self-evolving Agentic Graph-memory). The HMS Writer incrementally builds a causal evidence graph from trade traces.
*   **Metamemory Skills**: Integrates **AutoMem**. Memory management (Write/Read/Optimize) is exposed as first-class actions to agents. The HMS autonomously learns to optimize its own indexing schemas based on retrieval success.
*   **Transactive Layer**: Implements **MATM** (Multi-Agent Transactive Memory). Agents share "Strategic Artifacts" (e.g., successful hedging patterns) rather than just raw data.

### 2.3. Persistent Cognitive Agents (PCA) - The Behavioral Layer
*   **Behavioral Cloning**: Agents are initialized via **EKSFT** (Entropy-KL Selective Fine-Tuning) to activate capabilities without distribution sharpening.
*   **Skill Management**: Stable behaviors are stored as **S2L** (Skill-to-LoRA) adapters. Complex procedural guardrails are implemented as **HASP** executable `ProgramFunctions` (PFs) that override LLM logic in failure-prone states.
*   **Self-Healing**: Agents utilize the `Pivot/Refine` loop to autonomously recover from execution-layer errors.

### 2.4. Governance & Self-Improvement - The Evolution Gate
*   **Monotone-Safe Updates**: The **EvolutionGate** (RSEA) enforces the **CL-Bench** Gain Metric. No self-modification is committed unless $G = Perf(online) - Perf(stateless) > \epsilon$.
*   **Drift Control**: **EKSFT** logic is used during self-improvement to mask high-entropy/high-KL tokens, preventing the system from "learning" the noise of a specific market regime (overfitting).
*   **Reward Hacking Protection**: Immutable governance gates (Deterministic PFs) prevent agents from editing their own success logs or risk limits.

---

## 3. Resolving Research Contradictions

| Contradiction | Resolution in UCA V4 | Justification |
| :--- | :--- | :--- |
| **Flat Planning (ReAct) vs. Hierarchical (HIPIF)** | Adopt **Hierarchical Planning**. | Long-horizon financial tasks fail under flat context appending. |
| **Static Graph (GraphRAG) vs. Self-Evolving (SAGE)** | Adopt **SAGE (Self-Evolving)**. | Market relationships are non-stationary; static graphs become stale. |
| **Prompt-based Skills vs. LoRA (S2L)** | Use **LoRA (S2L)** for core archetypes; **PFs (HASP)** for hard guardrails. | Maximizes token efficiency while maintaining non-bypassable safety. |
| **Pure RL vs. SFT-then-RL** | Adopt **EKSFT-then-DAPO**. | Pure RL is too compute-intensive for complex reasoning; standard SFT causes mode collapse. |

---

## 4. Mathematical Foundation (UCA V4)

1.  **Global Objective**: $\min \mathcal{F}$ (Variational Free Energy).
2.  **Folding Constraint**: $\max I(Fold(H_t), S_{future})$ s.t. $I(Fold(H_t), H_t) < \beta$. (Information Bottleneck).
3.  **Evolution Gate**: $\Delta \theta$ is committed iff $G(\theta + \Delta \theta) > 0$ on held-out AIME/DeepWeb-Bench data.
4.  **Representational Looping**: $h_{t+1} = \text{DiscoLoop}(h_t, e_t)$, where $e_t$ is the discrete embedding and $h_t$ is the continuous state.
