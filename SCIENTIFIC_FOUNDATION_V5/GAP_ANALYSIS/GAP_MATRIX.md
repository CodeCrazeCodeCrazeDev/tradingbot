# Gap Matrix: AlphaAlgo vs. Mandatory Scientific Papers (V5)

| Principle | Paper Reference | Status | Gap Description |
| :--- | :--- | :--- | :--- |
| **Entropy-KL Selective Fine-Tuning** | EKSFT (arXiv:2605.29303) | **Missing** | Current fine-tuning (if any) likely uses standard SFT/RL without selective token masking for distribution preservation. |
| **Discrete-Continuous Recurrence** | DiscoLoop (arXiv:2607.00341) | **Missing** | `CognitiveSystemController` uses a linear pipeline. No looping architecture with dual-channel (discrete/continuous) recurrence is implemented. |
| **Automated Metamemory Learning** | AutoMem (arXiv:2607.01224) | **Partially Implemented** | `HierarchicalMemorySystem` (HMS) exists but lacks the two-loop automated optimization of schemas and proficiency. |
| **Self-Evolving Agentic Graph-Memory** | SAGE (arXiv:2605.12061) | **Partially Implemented** | `EvidenceGraph` exists, but is treated as a static snapshot rather than a self-evolving dynamic substrate with GFM-based reading. |
| **Tri-Level Co-Evolution** | NanoResearch (arXiv:2605.10813) | **Missing** | No explicit tri-level co-evolution of Skill Bank, User Memory, and Planner Policy. |
| **Pivot/Refine Decision Loop** | AutoResearchClaw (arXiv:2605.20025) | **Missing** | CSC pipeline is mostly forward-only with simple verification rejection; lacks explicit Pivot/Refine self-healing logic. |
| **Executable Skill Programs** | HASP (arXiv:2605.17734) | **Missing** | Skills are likely advisory textual prompts rather than executable Program Functions (PFs) with loop intervention. |
| **Massive Cross-Source Derivation** | DeepWeb-Bench (arXiv:2605.21482) | **Partially Implemented** | Verification swarm exists, but calibration and multi-step derivation depth are not explicitly benchmarked/optimized. |
| **Information Folding** | HIPIF (arXiv:2606.10507) | **Missing** | `folding.py` exists in `trading_bot/core/csc/` but is likely a skeleton; no trained folding operator is active in the main loop. |
| **Interactive Policy Guidance** | SocraticPO (arXiv:2606.09887) | **Missing** | RL loops in `SelfPlayLoop` (if active) lack interactive teacher-based diagnostic feedback and reward decay. |
| **Skill-to-LoRA Internalization** | S2L (arXiv:2606.16769) | **Missing** | Skills are prompt-based; no infrastructure for dynamic LoRA adapter routing exists. |
| **Agent-Native Knowledge Orchestration** | Agents-K1 (arXiv:2606.13669) | **Partially Implemented** | Causal graphs exist but lack the Graph-Anything CLI and active orchestration principles. |

## Key Findings
1. **Structural Fragmentation**: Subsystems like Risk and Intelligence are not fully integrated into the "One Brain" CSC.
2. **Static vs. Dynamic**: Memory and Knowledge are treated as static repositories rather than self-evolving agentic substrates.
3. **Advisory vs. Executable**: Guards and Skills are textual rather than executable programs.
4. **Linear vs. Looped**: Reasoning is linear; lacks the multi-hop internalization offered by DiscoLoop and the self-healing of Pivot/Refine.
