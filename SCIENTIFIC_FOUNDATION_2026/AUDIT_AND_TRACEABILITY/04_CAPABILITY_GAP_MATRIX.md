# Capability Gap Matrix
### Consolidated Verification Gap Auditing

This table represents the gap analysis comparing actual production code structures against documented system standards.

| Capability ID | Document Reference | Expected Architectural Behavior | Existing Implementation Status | Gaps / Missing Functionality | Recommended Implementation Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CAP-001** | `05_UNIFIED_ARCHITECTURE.md` | Active Inference iteration minimizing Variational Free Energy. | Fully implemented inside `CognitiveSystemController` | None. All async mocks passed. | Retain unified CSC "One Brain" core. |
| **CAP-002** | `MEMORY_HMS_V5.md` | SAGE persistence of causal memory graphml nodes. | Fully implemented in `SAGEGraphMemory` | None. Tests passed cleanly. | Maintain SQLite/SAGE index coherence. |
| **CAP-003** | `AUTOMEM_DECOMPOSITION.md` | Bumps version and optimizes meta-memory based on success. | Fully implemented in `HMS.optimize_metamemory()` | None. Bumps float version correctly. | Retain simple schema increment. |
| **CAP-004** | `HASP_DECOMPOSITION.md` | Intercepts task when volatility > 0.3 to override to hold. | Fully implemented in `SkillRouter` | None. Standardized context volatility checks. | Keep HASP safety checks at step 4 of csc. |
| **CAP-005** | `S2L_DECOMPOSITION.md` | Maps hedging tasks to specialized LoRA adapters. | Fully implemented in `SkillRouter` | None. Aligned adapter schemas. | Integrate with portfolio hedging. |
| **CAP-006** | `LOGACT_DECOMPOSITION.md` | Processes voter transactions and secures consensus. | Fully implemented in `UnifiedDecisionBus` | None. Tests validated ordering. | Maintain sequential commit logging. |
| **CAP-007** | `06_MATHEMATICAL_FOUNDATION.md` | Bailey and Lopez de Prado DSR calculation. | Fully implemented in `quant_pipeline.py` | None. Calibrated sample size scaling. | Require DSR check for all alphas. |
| **CAP-008** | `12_PROMOTION_GATE.md` | Rank-sorts and corrects P-values under FDR. | Fully implemented in `multiple_testing_gate.py` | None. Enforces p-value rank checks. | Apply Benjamini-Yekutieli limits. |
| **CAP-009** | `13_ADDITIONAL_RESEARCH_INTEGRATION.md` | Enforces parent ID DAG tracking and sha256 hashes. | Fully implemented in `DataLineageRegistry` | None. Generates unique version index. | Auto-register lineage during backtests. |
| **CAP-010** | `17_MEMOHARNESS_INTEGRATION_ANALYSIS.md` | Sub-millisecond retrieval-based control engine for CSC. | Fully implemented in `AdaptiveControlPolicyEngine` | None. | Fully verified under high-volatility trials. |
