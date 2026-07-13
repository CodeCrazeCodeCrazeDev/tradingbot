# Gap Matrix: AlphaAlgo vs. Mandatory Scientific Papers (V5)

| Principle | Paper Reference | Status | Gap Description | Reusable Algorithm(s) |
| :--- | :--- | :--- | :--- | :--- |
| **Entropy-KL Selective Fine-Tuning** | EKSFT (arXiv:2605.29303) | **Missing** | Current fine-tuning likely uses standard SFT/RL without selective token masking. | `SelectiveMaskingOperator`, `DualModelLoss` |
| **Discrete-Continuous Recurrence** | DiscoLoop (arXiv:2607.00341) | **Missing** | CSC uses linear pipeline. Lacks dual-channel (discrete/continuous) recurrence. | `DiscoLoopRecurrence`, `RepresentationalAligner` |
| **Automated Metamemory Learning** | AutoMem (arXiv:2607.01224) | **Partially Implemented** | HMS exists but lacks two-loop optimization of schemas and proficiency. | `MetamemoryTeacher`, `MemoryActionDistiller` |
| **Self-Evolving Agentic Graph-Memory** | SAGE (arXiv:2605.12061) | **Partially Implemented** | EvidenceGraph exists but is mostly static. Lacks GFM-based reader feedback. | `SAGEEvolutionLoop`, `IncrementalGraphWriter` |
| **Tri-Level Co-Evolution** | NanoResearch (arXiv:2605.10813) | **Missing** | No explicit tri-level co-evolution of Skill Bank, Memory, and Planner Policy. | `TriLevelCoEvolver`, `SkillDistiller` |
| **Pivot/Refine Decision Loop** | AutoResearchClaw (arXiv:2605.20025) | **Missing** | CSC pipeline is forward-only; lacks explicit Pivot/Refine self-healing logic. | `PivotRefineOperator`, `DebateConsensusEngine` |
| **Executable Skill Programs** | HASP (arXiv:2605.17734) | **Missing** | Skills are prompt-based rather than executable Program Functions (PFs). | `HASPHarness`, `PFEvolutionaryGate` |
| **Massive Cross-Source Derivation** | DeepWeb-Bench (arXiv:2605.21482) | **Partially Implemented** | Verification swarm exists, but calibration and derivation depth aren't optimized. | `DerivationValidator`, `CalibrationMonitor` |

## Key Findings
1. **Structural Fragmentation**: Intelligence and Governance are not fully integrated into a looped reasoning core.
2. **Static vs. Agentic**: Memory is treated as a repository rather than a self-evolving cognitive skill.
3. **Advisory vs. Executable**: Guardrails are textual prompts instead of hardcoded executable programs.
4. **Linear vs. Looped**: Reasoning lacks multi-hop internalization and self-healing.
