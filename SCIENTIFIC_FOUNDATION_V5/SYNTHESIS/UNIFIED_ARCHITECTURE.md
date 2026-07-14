# Unified Superior Architecture: AlphaAlgo UCA V5 (July 2026)

## 1. Architectural Philosophy: Recursive Active Inference
The AlphaAlgo UCA V5 architecture unifies all mandatory research principles into a single goal: **Minimizing Variational Free Energy (VFE)**. The system is no longer a linear pipeline but a **Recursive Active Inference** brain.

## 2. Integrated Systems

### 2.1. The Cognitive System Controller (CSC)
- **DiscoLoop Core**: Replaces linear reasoning with a $K$-hop discrete-continuous recurrence. Hidden states $h_k$ and discrete token embeddings $e_k$ are aligned at each hop, internalizing multi-step causal chains.
- **Pivot/Refine Decision Loop**: Instead of binary pass/fail, the CSC enters a self-healing loop. If a trade proposal fails verification, the `Verifier Swarm` provides feedback, triggering a `Pivot` (strategic change) or `Refine` (parameter tuning).
- **LogAct Backbone**: All proposed actions are written to a Shared-Log and must be approved by the `Verification Swarm` before execution.

### 2.2. The Hierarchical Memory System (HMS)
- **SAGE Substrate**: A self-evolving agentic graph-memory. A Memory Writer incrementally builds the graph, while a Graph-FM Reader performs multi-hop evidence chain retrieval.
- **AutoMem Optimizer**: A background loop optimizes memory schemas (Loop 1) and trains the agent's proficiency in memory-management actions (Loop 2).
- **HIPIF (Information Folding)**: Compresses completed subgoal histories into semantic updates, preserving strategic "insights" while reducing context noise.

### 2.3. The Skill & Execution Layer
- **HASP (Harnessing with Skill Programs)**: Procedural skills are implemented as executable Program Functions (PFs) that act as hard guardrails in the agent loop.
- **S2L (Skill-to-LoRA)**: High-frequency behavioral archetypes are distilled into dynamically loadable LoRA adapters, reducing context window consumption.
- **SkillRouter**: Dynamically routes tasks to PFs (for safety/procedural) or LoRAs (for behavioral/heuristic).

### 2.4. Evolution & Learning
- **EKSFT Training**: Online learning uses Entropy-KL Selective Fine-Tuning to prevent distribution collapse and preserve exploration capacity.
- **RSEA (Recursive Self-Evolution)**: All system improvements must pass through a Monotone-Safe `Evolution Gate` using held-out validation.

## 3. Unified Reasoning Pipeline (12 Steps)
1. **Active Perception**: Ingest market observation.
2. **Internalization (DiscoLoop)**: Run $K$ reasoning loops to align latent states with discrete entities.
3. **Skill Routing (S2L)**: Activate relevant LoRA adapters based on identified regime.
4. **Graph Retrieval (SAGE)**: Retrieve multi-hop evidence from the self-evolving graph.
5. **Executable Guardrails (HASP)**: Check state against PF-library for interventions.
6. **Multi-Hypothesis Generation**: Produce competing reasoning branches.
7. **Causal Simulation (WM-V3)**: Run counterfactual rollouts using the Hybrid Transformer-Mamba core.
8. **Decision Selection**: Select branch maximizing Expected Utility.
9. **Verification Swarm**: Peer-review the selected branch.
10. **Decision Loop (Pivot/Refine)**: Pivot strategy or Refine parameters based on verifier feedback.
11. **Governance Gate (Shield)**: Final immutable compliance check.
12. **Execution & Folding (HIPIF)**: Execute and fold history into a semantic update.

## 4. Resolution of Redundancies
- **Swarm vs. Brain**: Swarm is an external verification service; Brain is the strategic authority.
- **RAG vs. Graph**: SAGE Graph-Memory supersedes static RAG.
- **Prompts vs. Code**: HASP PFs for hard skills; S2L LoRAs for behavioral styles.
