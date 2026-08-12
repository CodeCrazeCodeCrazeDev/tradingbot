# SELF_IMPROVEMENT_SAFETY_MODEL.md
## Self-Improvement Safety Model and Human Governance Boundaries

This document defines the strict, non-bypassable safety models, risk boundaries, and human-in-the-loop gates for AlphaAlgo's self-improvement layers.

---

## 1. Governance Boundary Classification

To ensure that the self-improving brain remains structurally aligned with risk objectives, capabilities are segregated into three explicit governance zones:

### Zone A: Autonomous (No Human Intervention Required)
*   **Research**: Academic literature parsing, paper database indexing.
*   **Hypothesis Generation**: Proposing candidate alphas and strategies in the sandbox.
*   **Simulation & Benchmarking**: Running backtests, tracing lineage, and computing out-of-sample metrics.
*   **Diagnostics**: Parsing logs to locate performance bottlenecks or trace memory leaks.

### Zone B: Restricted (Automated Safety Check + Human Notification)
*   **Model Promotion**: Moving an evaluated neural model from the sandbox to the active registry.
*   **Policy & Strategy Activation**: Engaging a candidate strategy within low-exposure paper/canary trading.

### Zone C: Human Approval Required (Hard Cryptographic Verification Gate)
*   **Risk Limits Modification**: Any change to drawdown tolerances, leverage, or daily loss bounds.
*   **Disabling Safety Gates**: Pausing or bypassing verification swarms or the `ImmutableShield`.
*   **Self-Modification Authority**: Altering the code of the `EvolutionGate` or rollback scripts themselves.

---

## 2. Preventing Self-Improvement Reward Hacking

The system differentiates between **improving capability** and **improving capability measurement**.
*   **The Constraint**: Any candidate proposal that improves its reported evaluation scores by degrading confidence estimates, increasing calibration errors, or modifying the target reward function itself is instantly and permanently rejected.
*   **Independent Evaluation**: The evaluator component is structurally independent of the candidate code and is written in read-only modules that cannot be accessed by self-evolution loops.
