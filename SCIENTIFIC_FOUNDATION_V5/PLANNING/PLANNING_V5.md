# Planning V5: Insight-Aware HIPIF

The V5 Planning engine evolves the **HIPIF** (Information Folding) model by integrating **DeepInsight** (Strategic Sketching) and **LogAct** (Transactional Consensus).

## 1. The Planning Pipeline

### Stage 1: Insight Extraction (DeepInsight)
Before generating a detailed plan, the `PlannerAgent` must identify the **Core Strategic Insight**.
*   *Input*: Market Context (QKG) + Goal.
*   *Process*: Search the QKG for similar historical "Quantum" successes.
*   *Output*: An "Insight" (e.g., "Liquidity Gap during NY Open due to Bank Holiday") and a "Proof Sketch" (High-level sequence of logical steps).

### Stage 2: Hierarchical Plan Generation (HIPIF)
The system expands the Sketch into a detailed tree of subgoals.
*   *Mechanism*: Information Folding.
*   *Innovation*: Every subgoal is annotated with a **Formal Invariant** (e.g., "Max draw during this step < 0.2%").

### Stage 3: Shared-Log Proposing (LogAct)
The plan is not executed immediately.
1.  The `PlannerAgent` writes the *Insight* and the *Sketch* to the **Shared Log**.
2.  The `VerificationSwarm` performs a **Formal Proof Search** to verify that the Sketch logically leads to the goal without violating invariants.
3.  Upon "Voter Approval", the first subgoal is written to the Log.

## 2. Information Folding V5 (Strategic Anchoring)
In V4, folding was purely statistical compression. In V5, folding is **Insight-Preserving**.
*   **Keep**: The Core Insight, the Formal Invariants, and the Delta (Outcome - Prediction).
*   **Fold**: Raw execution traces, redundant tool calls, and benign logs.
*   **Anchor**: The folded summary is "Anchored" to the Insight in the QKG, making it a reusable fact for future planning.

## 3. Failure Attribution (HORIZON)
If a plan fails, the `ValidationAgent` uses the **HORIZON** taxonomy to attribute the failure:
1.  **Insight Failure**: Incorrect strategy identified.
2.  **Sketch Failure**: Correct insight, but logical roadmap was flawed.
3.  **Execution Failure**: Correct logic, but external market volatility broke the invariants.
4.  **Folding Failure**: Information lost during strategic compression.
