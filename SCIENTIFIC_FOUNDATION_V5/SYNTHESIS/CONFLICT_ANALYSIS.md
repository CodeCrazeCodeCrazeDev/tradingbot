# Conflict Analysis & Resolution (V5)

As AlphaAlgo transitions to V5, several research-level contradictions must be resolved.

## Conflict 1: Autonomy vs. Safety (Hyperagents vs. Immutable Shield)
*   **The Conflict**: *Hyperagents* (Paper 7, New) promotes self-referential modification of the meta-agent itself. *Immutable Shield* (Foundation) and *Reward Hacking* (Paper 13, Foundation) mandate fixed, non-bypassable safety gates.
*   **The Resolution**: The **Separation of Concerns Principle**. The *Hyperagent* may modify its internal reasoning and tool logic, but it CANNOT modify the *Governance Layer* or the *Evolution Gate*. The Evolution Gate is a separate, compiled process (deterministic or formally verified) that acts as the "Outer Sandbox".

## Conflict 2: Folding vs. Insight (HIPIF vs. DeepInsight)
*   **The Conflict**: *HIPIF* (Paper 1, Foundation) focuses on *compressing* history (Information Folding) to save space. *DeepInsight* (Paper 5, New) focuses on *expanding* the forward plan with "Insight" and "Sketches".
*   **The Resolution**: **Insight-Aware Folding**. Insights are identified *before* execution (DeepInsight). These insights become the "Compression Anchors" for HIPIF. Instead of folding history blindly, the system preserves the "Insight-to-Outcome" relationship, discarding the raw execution traces but keeping the verified strategic discovery.

## Conflict 3: Adapters vs. Growth (S2L vs. Grow, Don't Overwrite)
*   **The Conflict**: *Skill-to-LoRA* (Paper 3, Foundation) suggests using lightweight LoRAs to stay token-efficient. *Grow, Don't Overwrite* (Paper 12, New) suggests expanding the model's native weights.
*   **The Resolution**: **Hybrid Tiered Internalization**.
    *   **Tier 1 (Ephemeral)**: S2L adapters for transient market conditions or specific tools.
    *   **Tier 2 (Structural)**: "Grow" expansion for core world model knowledge and foundational institutional logic (e.g., risk management principles).

## Conflict 4: Consensus vs. Workflow (LogAct vs. Effective Agents)
*   **The Conflict**: *Effective Agents* (Paper 16, Foundation) argues for simple, robust workflows over complex swarms. *LogAct* (Paper 8, New) and *CORAL* (Paper 4, New) introduce shared-log consensus and asynchronous evolution.
*   **The Resolution**: **Deconstructed Workflow State Machines**. We use the *LogAct* shared log as the "Backbone", but the agents on that log follow *Effective Agent* workflows. This gives us the simplicity of workflows with the reliability/concurrency of a shared-log system.

## Conflict 5: Causal Models vs. Quantum KGs (CWMI vs. QKG)
*   **The Conflict**: *CWMI* (Paper 11, Foundation) builds DAGs for causal structure. *Quantum KG* (Paper 3, New) uses context-sensitive triplets.
*   **The Resolution**: **Conditional Causal Graphs**. The nodes and edges in our Causal SCM (Structural Causal Model) are now "Quantum". An edge $X \to Y$ exists *if and only if* the current context (regime, vol) matches the edge's validity criteria in the QKG.

## Conflict 6: Probabilistic vs. Deterministic Evolution (HyEvo vs. Formal Verification)
*   **The Conflict**: *HyEvo* (Paper 26, New) uses evolutionary strategies (probabilistic mutation) to evolve workflow topology. *Formal Proof Search* (Paper 2, New) and *UCA V5 Stability* mandate deterministic, formally verified invariant preservation.
*   **The Resolution**: **Verification-Augmented Evolution**. HyEvo may propose stochastic mutations to the workflow graph (LLM nodes + Code nodes), but every mutation must pass a **Formal Invariant Checker** (Logic Voter in LogAct) before being committed to the authoritative shared log. We evolve stochastically but verify formally.

## Conflict 7: Harness-as-Code vs. Parametric Injection (Meta-Harness vs. PT-RAG)
*   **The Conflict**: *Meta-Harness* (Paper 25, New) optimizes the harness *code* (Python/JS wrappers). *PT-RAG* (Paper 20, Foundation) injects knowledge into *model activations* (Parametric).
*   **The Resolution**: **Dual-Channel Injection**. Meta-Harness is used to optimize the *Retriever* and *Context Assembler* (Code Layer), while PT-RAG is used to distill the assembled context into the model's intermediate hidden states (Parametric Layer).
