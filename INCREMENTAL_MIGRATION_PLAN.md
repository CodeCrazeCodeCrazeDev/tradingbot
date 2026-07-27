# Architecture Verification Gate: Incremental Migration Plan

This document outlines the step-by-step transition from the Legacy architecture to the UCA-2026.

---

## 1. Phase 1: Foundation Consolidation (Day 1-15)
*   **Step 1.1: Registry Unification**
    *   Create `UnifiedComponentRegistry` (Singleton).
    *   Migrate all agents, tools, and services to this registry.
*   **Step 1.2: Governance Hardening**
    *   Implement the `ImmutableShield` as a mandatory interceptor for all execution calls.
*   **Step 1.3: Decision Bus Implementation**
    *   Deploy the `UnifiedDecisionBus` to replace fragmented event handlers.
*   *Validation*: All components register successfully; direct execution is blocked.

## 2. Phase 2: World Model & Grounding (Day 16-35)
*   **Step 2.1: Tick-Data Replay Integration**
    *   Replace random simulators with the `HistoricalReplayFeed`.
*   **Step 2.2: SCM Deployment**
    *   Implement the `CausalWorldModel` with basic Pearl's Do-Calculus for market impact.
*   *Validation*: Simulation rollouts match historical data; interventions yield consistent outcomes.

## 3. Phase 3: Cognitive System Controller (Day 36-60)
*   **Step 3.1: CSC Controller Launch**
    *   Deploy the `CSCController` in `integrated_system.py`.
    *   Merge logic from `MasterOrchestrator` and `MetaOrchestrator`.
*   **Step 3.2: HIPIF Planner Integration**
    *   Refactor `react_loop.py` to include the `FoldingOperator`.
*   *Validation*: Planning tasks complete with < 50% token growth; single entry point for all workflows.

## 4. Phase 4: Memory & Evolution (Day 61-80)
*   **Step 4.1: HMS Hierarchical Memory**
    *   Deploy the WMR loop and consolidate episodic memories into the Semantic Graph.
*   **Step 4.2: Evolution Gate Implementation**
    *   Deploy the `RSEAEvolver` with the "Strict Keep-Better" check on held-out data.
*   *Validation*: Retrieval precision > 0.8; zero regression in self-improvement cycles.

## 5. Phase 5: Legacy Removal & Final Polish (Day 81-90)
*   **Step 5.1: Deprecate Redundant Orchestrators**
    *   Remove all `*orchestrator.py` files.
*   **Step 5.2: Final Performance Benchmarking**
    *   Run HORIZON failure attribution and gain metric benchmarks.
*   *Validation*: Zero "Orchestrator" files remain; Gain Metric $G > 0$ across all regimes.

---

## 6. Rollback Strategy
*   **Atomic Commits**: Every step is a single, verifiable commit.
*   **Parallel Execution**: During Phase 2 & 3, both Legacy and UCA models run in parallel (Legacy as shadow) to verify consistency before cutting over.
*   **State Checkpoints**: All persistent state (Memory, Evolution) is backed up before every migration step.
