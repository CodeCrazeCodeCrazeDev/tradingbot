# Learning & Self-Improvement V5: Metacognitive Evolution

The V5 Learning pipeline evolves AlphaAlgo from "Passive Experience" to "Metacognitive Self-Optimization" using **Hyperagents**, **Meta-Harness**, and **LSE**.

## 1. The Hyperagent Loop (Recursive Self-Improvement)
The core `PersistentCognitiveAgent` (PCA) is upgraded to a **Hyperagent V5**.

1.  **Task Rollout**: Agent executes trade research on the LogAct backbone.
2.  **Diagnostic Reflection**: The internal Meta-Agent analyzes the shared log.
    *   *Question*: "Why did my tool selection (Harness) fail to capture the alpha?"
    *   *Tool*: **LSE (Learning to Self-Evolve)** trained policy for context-refinement.
3.  **Harness Optimization**: The Meta-Agent proposes a rewrite of its own internal "Harness" (Paper 2, Meta-Harness).
    *   *Rewrite*: Adding a new "Slippage-Check" step to the `order_execution` skill.
4.  **Behavioral Internalization**: Successful harness optimizations are distilled into **S2L (Skill-to-LoRA)** adapters or **Grow** (Function-Preserving Growth) expansions of the core model weights.

## 2. The Evolution Gate V5 (Monotone Safety)
Every proposed self-modification (source code edit or LoRA update) must pass the **Evolution Gate**.

*   **Held-out Selection (RSEA)**: The candidate is tested on a "Held-out" market regime (OOD) and a "Held-in" regime.
*   **Formal Verification**: AI-driven proof search verifies the new code does not bypass safety invariants (e.g., risk limits).
*   **Ablation Study**: The system automatically runs an ablation study to ensure the *new* component provides measurable improvement over the *old* one (using the CL-Bench Gain Metric).

## 3. Training Architecture (Future Stack)
V5 defines the roadmap for the next generation of AlphaAlgo models:

1.  **Pre-training / Growth**: Use "Grow, Don't Overwrite" to expand foundational financial knowledge.
2.  **Insight-SFT**: Fine-tune on the "DeepInsightTheorem" dataset of financial reasoning sketches.
3.  **Strategic RL (ReTool)**: Train the policy for optimal tool-interleaving (e.g., when to call the backtester vs. when to use LLM intuition).
4.  **Self-Evolution RL (LSE)**: Train the model to become an "Evolution Proposer" by rewarding it for proposing verified, high-gain self-modifications.
