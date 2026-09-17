# ARCHITECTURAL_OWNERSHIP_AUDIT.md
## Analysis of Capability Ownership & Elimination of Duplicated Logic

This audit assesses AlphaAlgo's codebase to identify overlapping implementations, duplicate capabilities, and specify the authoritative single sources of truth.

---

## 1. Capability Ownership Mapping

| Capability | Overlapping Implementations | Canonical Owner | Justification & Migration Path |
| :--- | :--- | :--- | :--- |
| **Event Bus / Decision Log** | `UnifiedDecisionBus` (`trading_bot/core/unified_event_bus.py`), `EventBus` (`_archive/legacy/`), `MessageBus` (`_archive/advanced/`) | **`UnifiedDecisionBus`** | **LogAct Shared-Log Backbone**: Unifies all transactional decision proposers and voter callbacks into a totally ordered append-only log. Purge legacy stubs. |
| **Strategic Brain / Controller** | `CognitiveSystemController` (`trading_bot/core/csc/controller.py`), `MasterOrchestrator`, `AgentOrchestrator` | **`CognitiveSystemController`** | **Unified Cognitive OS (UCA-2026)**: Integrates 12-step Active Inference, SAGE Graph Memory querying, and verifier feedback. Duplicate orchestrators are deleted or demoted to sub-modules. |
| **Memory System** | `HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`), `SharedMemoryManager` (`trading_bot/database/`), `LOBReplayBuffer` | **`HierarchicalMemorySystem`** | Consolidates SAGE Graph memory (entity-relation evidence tracks) and AutoMem schema-versioned serialization. Other databases delegate to HMS. |
| **Skill Routing & Dispatch** | `SkillRouter` (`trading_bot/core/csc/router.py`), `HASPExecutor` | **`SkillRouter`** | **S2L and HASP Consolidation**: Maps incoming tasks to model weights (LoRA adapters) or safety executables, returning structured `SkillRouteOutcome` packets. |
| **Evolution Gating** | `EvolutionGate` (`trading_bot/governance/evolution_gate.py`), `SafeEvolutionEngine` | **`EvolutionGate`** | **RSEA Monotone-Safe Gate**: Runs multi-metric check loops comparing stateful candidate metrics (latency, drawdown, calibration) against baseline configs. |
| **Risk Management** | `ImmutableShield` (`trading_bot/core/immutable_shield.py`), `MasterRiskManager`, `PortfolioRiskManager` | **`ImmutableShield`** | **Immutable Safety Kernel**: Final non-bypassable, python-immutable execution gate ensuring capital protection under zero-risk tolerances. |

---

## 2. Deletion and Archive Candidates

1.  **Duplicate `agents 2/` and `advanced_systems 2/` directories**:
    - Purged completely.
2.  **Legacy stateless ReAct loop scripts**:
    - Removed from main production path to prevent ungrounded reasoning drift.
3.  **Heuristic point-estimate risk sizing routines**:
    - Replaced by Bayesian uncertainty estimation and calibration ECE metrics from the World Model.
