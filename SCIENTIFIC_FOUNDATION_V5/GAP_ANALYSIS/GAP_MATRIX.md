# Gap Matrix: AlphaAlgo vs. Mandatory Scientific Papers (V5)

| Principle | Paper Reference | Status | Gap Description |
| :--- | :--- | :--- | :--- |
| **Entropy-KL Selective Fine-Tuning** | EKSFT (arXiv:2605.29303) | **Partially Implemented** | `EvolutionGate` exists but standard SFT/RL is likely used. Selective token masking for distribution preservation is missing in active training scripts. |
| **Discrete-Continuous Recurrence** | DiscoLoop (arXiv:2607.00341) | **Missing** | `CognitiveSystemController` uses a linear pipeline. No dual-channel (discrete/continuous) recurrence with projection/realignment is implemented. |
| **Automated Metamemory Learning** | AutoMem (arXiv:2607.01224) | **Missing** | `HierarchicalMemorySystem` (HMS) lacks the two-loop automated optimization (Loop 1: Schema optimization; Loop 2: Proficiency training). |
| **Self-Evolving Agentic Graph-Memory** | SAGE (arXiv:2605.12061) | **Partially Implemented** | `SAGEGraphMemory` skeleton exists in `memory.py`, but Reader/Writer feedback loops and GFM-based retrieval are not fully operational. |
| **Tri-Level Co-Evolution** | NanoResearch (arXiv:2605.10813) | **Missing** | No explicit co-evolution and alignment between the Skill Bank (S2L), User/Working Memory, and the Global Planner Policy. |
| **Pivot/Refine Decision Loop** | AutoResearchClaw (arXiv:2605.20025) | **Partially Implemented** | CSC has a basic "attempts" loop, but lacks formal Pivot (strategic) vs Refine (tactical) branch selection logic. |
| **Executable Skill Programs** | HASP (arXiv:2605.17734) | **Partially Implemented** | `SkillRouter` and `HASPExecutor` skeletons exist but lack a comprehensive library of Program Functions (PFs) and formal state-action intervention hooks. |
| **Massive Cross-Source Derivation** | DeepWeb-Bench (arXiv:2605.21482) | **Missing** | No dedicated benchmarking for multi-step derivation depth and calibration error (ECE) in the research discovery phase. |
| **LogAct Shared-Log Backbone** | LogAct (arXiv:2604.07988) | **Partially Implemented** | `UnifiedDecisionBus` implements the shared log, but consensus voting is basic and lacks deep integration with agent proposals. |
| **Information Folding (HIPIF)** | HIPIF (arXiv:2606.10507) | **Missing** | `InformationFolder` and `folding.py` are stubs; no active semantic compression of execution traces is performed in the main loop. |
| **Skill-to-LoRA Internalization** | S2L (arXiv:2606.16769) | **Missing** | Infrastructure for dynamic LoRA adapter routing and the S2L distillation loop is not implemented. |
| **Collaborative Alignment (CORAL)** | CORAL (arXiv:2605.13284) | **Missing** | No adversarial alignment protocol or evidence-grounded cross-verification between PCA specialists. |

## Key Findings
1. **Structural Fragmentation**: Subsystems like Risk and Intelligence are not fully integrated into the "One Brain" CSC.
2. **Static vs. Dynamic**: Memory and Knowledge are treated as static repositories rather than self-evolving agentic substrates.
3. **Advisory vs. Executable**: Guards and Skills are textual rather than executable programs.
4. **Linear vs. Looped**: Reasoning is linear; lacks the multi-hop internalization offered by DiscoLoop and the self-healing of Pivot/Refine.
5. **Missing Distillation**: The path from "Successful Prompt" to "Stable Adapter" (S2L) is not automated.
