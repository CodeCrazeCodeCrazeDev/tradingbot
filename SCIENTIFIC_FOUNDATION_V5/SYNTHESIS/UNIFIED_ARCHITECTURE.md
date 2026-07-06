# Unified Superior Architecture: AlphaAlgo UCA V5 (July 2026)

## 1. Architectural Philosophy: The "Recursive Active Inference" Brain
The UCA V5 unifies all 8 mandatory papers into a single mathematical objective: **Minimizing Variational Free Energy (VFE)** through a **Recursive Active Inference** loop.

## 2. Component Synthesis

### 2.1. The Cognitive System Controller (CSC) - Looped Multi-Hop Reasoning
- **DiscoLoop Core**: Replaces the linear forward pass with a looped Transformer architecture. Every "Thought" carries both a continuous hidden state and a discrete token embedding (Bridge Entity), allowing the model to "internalize" multi-hop market reasoning before proposing an action.
- **Pivot/Refine Strategy**: The CSC doesn't just fail; it utilizes a `Self-Healing Executor`. If a trade proposal fails verification, it enters a `Pivot` (strategic shift) or `Refine` (parameter adjustment) loop informed by the `Verifier Swarm`.

### 2.2. The Hierarchical Memory System (HMS) - Self-Evolving Substrate
- **AutoMem Optimizer**: The HMS is no longer a passive DB. A background `Metamemory Loop` optimizes file schemas and prompt instructions based on trajectory successes (Loop 1) and trains the agent's proficiency in memory actions (Loop 2).
- **SAGE Integration**: Knowledge is stored as a `Self-evolving Agentic Graph-Memory`. A Graph-FM memory reader performs multi-hop retrieval, while a memory writer incrementally evolves the graph based on interaction feedback.

### 2.3. The Skill & Governance Layer - Executable Guardrails (HASP)
- **Harnessing with Skill Programs (HASP)**: Advisory prompts are upgraded to executable `Program Functions (PFs)`. These act as hard guardrails in the CSC loop, intercepting failure-prone states (e.g., high volatility) and injecting corrective context or modifying actions before they reach the execution engine.
- **Skill-to-LoRA (S2L)**: High-frequency procedural behaviors are distilled from context into lightweight `LoRA adapters`, routed dynamically to ensure token efficiency and behavioral stability.

### 2.4. Evolution & Safety - Monotone-Safe Self-Improvement
- **RSEA & Evolution Gate**: Any self-proposed improvement to the CSC or HMS must pass through the `Evolution Gate`. This gate enforces a `Monotone-Safe` update rule: improvements are only committed if they exceed baseline performance on a held-out validation set.
- **EKSFT Fine-tuning**: Online learning from new market data utilizes `Entropy-KL Selective Fine-Tuning`. Tokens with high uncertainty or distribution shift are masked, preventing the "Delusion Loop" and preserving the pre-trained distribution.

## 3. The Unified Reasoning Pipeline (12 Steps)

1. **Active Perception**: Ingest market observation $o_t$.
2. **Internalization (DiscoLoop)**: Run $K$ reasoning loops to align hidden states with discrete market entities.
3. **Skill Routing (S2L)**: Activate relevant LoRA adapters based on identified regime.
4. **Graph Retrieval (SAGE)**: Traverse the self-evolving graph for multi-hop evidence.
5. **Executable Guardrails (HASP)**: Check state against PF-library for mandatory interventions.
6. **Hypothesis Generation**: Produce competing multi-path branches.
7. **Causal Simulation (CWMI)**: Run counterfactual "What-if" rollouts using SCMs.
8. **Decision Selection**: Select branch maximizing Expected Utility / minimizing VFE.
9. **Verification Swarm**: Peer-review the selected branch for hallucinations and logic errors.
10. **Decision Loop (Pivot/Refine)**: If verifiers reject, Pivot strategy or Refine parameters.
11. **Governance Gate (Shield)**: Final immutable check against hard risk/compliance limits.
12. **Execution & Folding (HIPIF)**: Execute trade and "fold" the history into a semantic update for the next horizon.

## 4. Resolution of Contradictions
- **Swarm vs. One Brain**: Resolved by using the `One Brain (CSC)` as the central controller while treating the `Swarm` as an external `Verification Service`.
- **RAG vs. Graph**: Resolved by using `SAGE` as the primary graph-memory engine, superseding passive vector-based RAG.
- **Prompts vs. Code**: Resolved by `HASP` - if a skill is critical/safety-related, it must be an executable PF; if it is behavioral/stylistic, it is a LoRA.
