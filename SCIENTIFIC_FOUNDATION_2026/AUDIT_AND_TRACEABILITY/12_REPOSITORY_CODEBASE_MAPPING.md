# Phase 5: Comprehensive Repository Codebase Mapping & Audit (2026)

## 1. Introduction

This document maps our selected scientific corpus against the actual implementation structure of AlphaAlgo. For every key subsystem, we perform an engineering audit and recommend whether to KEEP, MERGE, REDESIGN, REPLACE, or REMOVE the component, citing the supporting scientific literature.

---

## 2. Comprehensive Subsystem Audit & Mapping

### 1. Cognitive System Controller (CSC)
*   **Path:** `trading_bot/core/csc/controller.py`
*   **Supporting Research:** *Active Inference* (variational free energy minimization), *HIPIF* (DiscoLoop cell), and *SRE* (19-step reasoning engine).
*   **Contradictions / Gaps:** The conftest fixture assumes the existence of a mutable `reset()` method to wipe state between tests, but exposing mutable reset methods in production code is a lifecycle anti-pattern.
*   **Recommendation:** **REDESIGN**
    *   *Justification:* Keep the core variational inference and DiscoLoop architecture, but eliminate the class-level singleton state. Refactor to utilize constructor-based Dependency Injection (DI) and explicit asynchronous context managers for clean lifecycle management. Expose zero singleton state to the conftest.

### 2. Hierarchical Memory System (HMS)
*   **Path:** `trading_bot/core/hms/memory.py`
*   **Supporting Research:** *Agents-K1* (SAGE dynamic knowledge graph queries) and *Memory Survey* (WMR write-manage-read abstraction).
*   **Contradictions / Gaps:** Uses class-level singleton locks and lacks explicit scoped instance lifetimes, causing cross-test database collisions.
*   **Recommendation:** **REDESIGN**
    *   *Justification:* Transition HMS from a global singleton class to a scoped, factory-managed class. Use distinct database directories/paths injected at construction time for test isolation without requiring a global `reset()` API.

### 3. Unified Event Bus & Decision Bus
*   **Path:** `trading_bot/core/unified_event_bus.py`
*   **Supporting Research:** *LogAct* (Totally ordered shared-log commitment backbone).
*   **Contradictions / Gaps:** Background processing loops are bound to global instances, causing `cross-loop leakage` errors in async pytest suites if not cleanly stopped and re-bound.
*   **Recommendation:** **REDESIGN**
    *   *Justification:* Re-engineer the `UnifiedDecisionBus` to be fully scoped and lifecycle-aware. Replace the global instance with a container-managed connection pool or scoped instance per execution context.

### 4. Global World Model (GWM)
*   **Path:** `trading_bot/world_model/`
*   **Supporting Research:** *CWMI* (Causal structural modeling and intervention simulation).
*   **Contradictions / Gaps:** Contains multiple competing legacy world model files (e.g. `v2_adapter.py`, `v2_core.py`, `fwm_core.py`), violating the "One Brain" singular capability ownership standard.
*   **Recommendation:** **MERGE & REDESIGN**
    *   *Justification:* Consolidate all duplicate and fragmented world models into a single, authoritative `CausalWorldModel` under `trading_bot/world_model/causal_model.py`. Remove legacy adapters and stubs to eliminate redundant simulation logic.

### 5. Multi-Agent Debate Engine
*   **Path:** `trading_bot/agents/multi_agent_debate.py`
*   **Supporting Research:** *AI Safety via Debate* and *MATM* (Transactive memory sharing).
*   **Contradictions / Gaps:** High communication overhead and redundant validation passes without structured scorecards.
*   **Recommendation:** **KEEP & MERGE**
    *   *Justification:* Maintain the Byzantine-resilient debate system but explicitly merge its state queries into MATM's transactive index to avoid redundant model forward passes.

### 6. EvolutionGate (Model Optimization Gate)
*   **Path:** `trading_bot/governance/evolution_gate.py`
*   **Supporting Research:** *RSEA* (Monotone-safe evolution gating).
*   **Contradictions / Gaps:** Duplicate constructors existed previously. Needs strict execution boundaries preventing online production code modification.
*   **Recommendation:** **KEEP**
    *   *Justification:* The current `EvolutionGate` already enforces monotone-safety checks (latency, drawdown, Sharpe ratio validation) on offline validation sets prior to champion promotion. Keep as an immutable gate.

### 7. Strategic Skill Router
*   **Path:** `trading_bot/core/csc/router.py`
*   **Supporting Research:** *Skill-to-LoRA* (Low-rank weight distillation).
*   **Contradictions / Gaps:** The conftest fixture assumes a global `SkillRouter.reset()` exists.
*   **Recommendation:** **REDESIGN**
    *   *Justification:* Refactor to be fully stateless or container-scoped, removing global singletons.

---

## 3. Discovered Defects Register

The discovered defects identified during this audit are logged here to maintain the strict Implementation Lock:

1.  **DEFECT-01: Missing Singleton Reset Methods**
    *   *Impact:* Crashes conftest startup during testing.
    *   *Remediation Plan (Post-Lock):* Re-engineer conftest and production modules to utilize dependency injection and scoped test containers instead of global singletons.
2.  **DEFECT-02: World Model Architectural Fragmentation**
    *   *Impact:* Multiple duplicate implementations of simulation engines under `world_model/` causing bloated artifact sizes and conflicting predictions.
    *   *Remediation Plan (Post-Lock):* Delete legacy stubs and adapters, keeping only the single authoritative causal world model.
3.  **DEFECT-03: Cross-Loop Queue Leakage**
    *   *Impact:* Async event loops in pytest collide with the global decision bus PriorityQueue.
    *   *Remediation Plan (Post-Lock):* Bind queue resources dynamically to active scopes.
