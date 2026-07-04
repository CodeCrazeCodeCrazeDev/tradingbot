# UCA-2026: Migration Parity & Decommissioning Table

This table tracks the feature parity and migration status of all legacy orchestrators identified in the AlphaAlgo July 2026 audit.

---

| Legacy Orchestrator File | Primary Responsibilities | CSC (Unified) Equivalent | Migration Status | Tests Passing | Safe to Archive |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `master_orchestrator.py` (root) | Global coordination, Layer startup | `IntegratedAgentSystem` | **Delegated** | Yes | No (Entry Point) |
| `trading_bot/core/orchestrator.py` | Signal, Risk, Execution coordination | `IntegratedAgentSystem.think` | **Deprecated** | Yes | Yes (Archive) |
| `trading_bot/core_agent_system/master_orchestrator.py` | Hierarchical MCTS decision fusion | `IntegratedAgentSystem.orchestrator` | **Integrated** | Yes | No (Dependency) |
| `trading_bot/unified_architecture/layer6_orchestration.py` | Layer-based coordination | `IntegratedAgentSystem` | **Deprecated** | Yes | Yes (Archive) |
| `trading_bot/aads/orchestrator.py` | Advanced signal discovery | `Alpha PCA` + `HMS` | Pending | No | No |
| `trading_bot/autonomous_pipeline/pipeline_orchestrator.py` | Deployment & Discovery | `CSC Lifecycle` | Pending | No | No |
| `trading_bot/market_student/market_student_orchestrator.py` | Continuous learning from trades | `SocraticPO` + `HMS` | Pending | No | No |
| `trading_bot/phce_d/orchestrator.py` | Hypothesis generation | `SCM` + `PCA` | Pending | No | No |
| `trading_bot/self_coordinating_ai/orchestrator.py` | Multi-agent coordination | `Transactive Memory` | Pending | No | No |
| `trading_bot/superintelligence/superintelligence_orchestrator.py` | Recursive improvement | `RSEA Gate` | Pending | No | No |

---

## 2. Archiving Rules (MANDATORY)

Before any file is moved to `_archive/` or deleted:
1.  **Dependency Check**: Run `grep -r "import ..."` to verify no active components depend on the class.
2.  **Responsibility Mapping**: Every method in the legacy class must have a functional equivalent in the CSC or relevant PCA.
3.  **Benchmark**: Run the Shadow Deployment comparison to ensure no performance regression.
4.  **Shadow Validation**: The legacy orchestrator must be redundant in the `shadow_mode` logs.

---

## 3. Summary of Fragmentation (July 2026 Audit)

Total Unique Orchestrator Classes: **82**
Integrated into CSC: **4**
Deprecated/Marked for Archive: **3**
Pending Feature Parity: **75**
