# Additional Research Integration: AlphaAlgo Scientific Foundation (2026)

This document provides engineering decompositions for the eight mandatory papers and key additional references required for the UCA V4 refactoring.

---

## 1. EKSFT: Entropy-KL Selective Fine-Tuning
*   **Reference**: arXiv:2605.29303 (2026)
*   **Core Hypothesis**: SFT should prioritize activating task-relevant capabilities rather than memorizing specific content, especially when used as a cold-start for RL.
*   **Mathematical Formulation**:
    - Masks tokens $t$ if $t \in \mathcal{M} = \mathcal{M}_H \cup \mathcal{M}_{KL}$.
    - $\mathcal{L}_{EKSFT} = \mathcal{L}_{CE}^{mask} - \lambda_H \mathcal{L}_H^{mask} + \lambda_{KL} \mathcal{L}_{KL}^{mask}$.
*   **Algorithms**: Union strategy for constructing the final selected token set based on Top-K ratios of entropy and KL-divergence.
*   **Architectural Contribution**: Selective fine-tuning mechanism that prevents "distribution sharpening" and "entropy collapse," preserving exploration capacity for subsequent RL phases.
*   **Failure Modes**: Excessive masking ($\rho > 0.3$) removes too much supervision signal.
*   **Financial Applicability**: Enables safe self-improvement of trading agents by preventing them from overfitting to specific historical trade sequences (memorization) while activating general reasoning capabilities.

## 2. DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States
*   **Reference**: arXiv:2607.00341 (2026)
*   **Core Hypothesis**: Standard Transformers suffer from depth-local storage problems; Looped Transformers with mixed discrete-continuous recurrence channels solve representational bottlenecks in multi-step reasoning.
*   **Mathematical Formulation**: Recurrence carrying both a discrete embedding channel and a continuous hidden-state channel.
*   **Algorithms**: Training-free realignment intervention to close the generalization gap in two-hop reasoning.
*   **Architectural Contribution**: "DiscoLoop" architecture for internalizing multi-step reasoning within single forward passes or compact recurrent loops.
*   **Financial Applicability**: Critical for real-time market reasoning where multi-hop causal inference (e.g., News A $\to$ Effect B $\to$ Trade C) must be internalized quickly without massive context-window overhead.

## 3. AutoMem: Automated Learning of Memory as a Cognitive Skill
*   **Reference**: arXiv:2607.01224 (2026)
*   **Core Hypothesis**: Memory management is an independently learnable cognitive skill (metamemory) that can be optimized through automated feedback loops.
*   **Algorithms**:
    - Loop 1: Strong LLM reviews trajectories to revise memory structure (prompts, schemas).
    - Loop 2: Agent's good memory decisions are identified to train model proficiency directly.
*   **Architectural Contribution**: Promotion of file-system operations (Write/Read/Manage) to first-class memory actions alongside task actions.
*   **Financial Applicability**: Allows AlphaAlgo to learn *what* specific market events are worth remembering in the Research Ledger and *how* to index them for institutional auditability.

## 4. SAGE: Self-evolving Agentic Graph-memory Engine
*   **Reference**: arXiv:2605.12061 (2026)
*   **Core Hypothesis**: Graph memory should be a dynamic, self-evolving substrate rather than static retrieval middleware.
*   **Architectural Contribution**: Couples a "Memory Writer" (incremental graph construction) with a GFM-based "Memory Reader" (retrieval + feedback to writer).
*   **Financial Applicability**: Replaces flat RAG with a dynamic Evidence Graph where market relationships (e.g., Correl(Gold, USD)) evolve and strengthen over time through direct feedback.

## 5. NanoResearch: Tri-level Co-evolving Research Automation
*   **Reference**: arXiv:2605.10813 (2026)
*   **Core Hypothesis**: Personalization is a precondition for usable research automation; requires co-evolution of skills, memory, and policy.
*   **Algorithms**:
    - Skill Bank: Compact procedural rules.
    - Memory Module: User/Project-specific experience.
    - Label-free Policy Learning: Internalizing preferences via parameter updates.
*   **Financial Applicability**: Customizes AlphaAlgo's research output to specific institutional mandates and risk tolerances without explicit re-coding.

## 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
*   **Reference**: arXiv:2605.20025 (2026)
*   **Core Hypothesis**: Real research is iterative and requires multi-perspective debate and self-healing executors.
*   **Algorithms**:
    - Pivot/Refine decision loop for self-healing execution.
    - Structured multi-agent debate for hypothesis generation.
*   **Architectural Contribution**: Verifiable result reporting and human-in-the-loop (HITL) intervention modes.
*   **Financial Applicability**: Pivot/Refine loop allows the execution agent to handle API failures or unexpected slippage by "pivoting" strategy mid-flight.

## 7. HASP: Harnessing LLM Agents with Skill Programs
*   **Reference**: arXiv:2605.17734 (2026)
*   **Core Hypothesis**: Textual guidance is advisory; agents need executable guardrails (Program Functions) to intervene in the agent loop.
*   **Algorithms**: Skill Program evolution; PFs activate on failure-prone states and inject corrective context.
*   **Architectural Contribution**: Upgrading passive "SKILL.md" files into executable `ProgramFunctions`.
*   **Financial Applicability**: Hard-coded risk guardrails (PFs) that trigger on high-volatility states to override LLM "overconfidence."

## 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark
*   **Reference**: arXiv:2605.21482 (2026)
*   **Core Contribution**: Harder benchmark focusing on Retrieval, Derivation, Reasoning, and Calibration.
*   **Insight**: Retrieval is rarely the bottleneck; derivation and calibration (confidence) account for 70% of failures.
*   **Financial Applicability**: Justifies the "Evidence-First" hard constraint in the CSC; emphasizes the need for rigorous multi-step derivation before trade approval.

---

## 9. Additional Key References (Integrated)
*   **PSFT (Proximal SFT)**: Trust-region inspired SFT to constrain policy drift. (arXiv:2508.17784)
*   **IW-SFT (Importance-Weighted SFT)**: Interprets SFT as a lower bound on sparse-reward RL. (arXiv:2507.12856)
*   **DAPO (Open-source RL System)**: Scalable RL system for post-training alignment. (arXiv:2503.14476)
