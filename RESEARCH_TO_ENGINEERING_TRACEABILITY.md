# RESEARCH_TO_ENGINEERING_TRACEABILITY.md
## Research-to-Engineering Traceability & Lineage Map

This document establishes the unbreakable traceability chains mapping peer-reviewed research papers to design decisions, production source files, and unit test targets.

---

## 1. Unbroken Traceability Chains

### Trace Chain 1: Hierarchical Planning and Information Folding (HIPIF)
*   **Research**: *HIPIF (arXiv:2606.10507)* - Compresses step buffers into semantic sufficient statistics.
*   **Design Decision**: `InformationFolder` compiles long-horizon execution blocks into memory milestones.
*   **Source Code**: `trading_bot/core/csc/controller.py -> class CognitiveSystemController`
*   **Unit Test Target**: `tests/test_scientific_modules.py::test_discoloop_internalization`

### Trace Chain 2: Skill-to-LoRA Behavioral Adapters (S2L)
*   **Research**: *Skill-to-LoRA (arXiv:2606.16769)* - Internalizes operational textual rules into model weights.
*   **Design Decision**: Dynamic capability-based routing returning `SkillRouteOutcome`.
*   **Source Code**: `trading_bot/core/csc/router.py -> class SkillRouter`
*   **Unit Test Target**: `tests/test_scientific_modules.py::test_s2l_behavioral_routing`

### Trace Chain 3: Recursive Self-Evolving Agents (RSEA) Monotone Gating
*   **Research**: *RSEA (arXiv:2606.28374)* - Restricts candidate code changes via non-regressive validation gates.
*   **Design Decision**: Evolution gating on Expected Calibration Error (ECE) and latency metrics.
*   **Source Code**: `trading_bot/governance/evolution_gate.py -> class EvolutionGate`
*   **Unit Test Target**: `tests/test_scientific_modules.py::test_rsea_monotone_safe_gate`
