# Phase 4 — Refactoring Plan & Migration Specification for AlphaAlgo UCA V6

## Executive Overview
This document specifies the dependency structure, step-by-step migration roadmap, risk mitigation strategies, rollback protocols, benchmark framework, and validation plan for AlphaAlgo UCA V6 refactoring.

---

## 1. System Dependency Graph

```
                   ┌───────────────────────────────────┐
                   │    UnifiedDecisionBus (LogAct)    │
                   └─────────────────┬─────────────────┘
                                     │
             ┌───────────────────────┼───────────────────────┐
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────────────┐ ┌───────────────────┐ ┌─────────────────────┐
│  SkillRouter & HASP     │ │  EvolutionGate    │ │ HierarchicalMemory  │
│  Guardrail Pre-Emption  │ │  Monotone-Safe    │ │ System (HMS & SAGE) │
└────────────┬────────────┘ └─────────┬─────────┘ └──────────┬──────────┘
             │                        │                      │
             └──────────────────┐     │     ┌────────────────┘
                                ▼     ▼     ▼
                   ┌───────────────────────────────────┐
                   │   CognitiveSystemController (CSC) │
                   │   12-Stage Active Inference Core  │
                   └─────────────────┬─────────────────┘
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
                   │     MultiAgentDebateSystem        │
                   │  Bayesian Consensus & Falsification│
                   └───────────────────────────────────┘
```

---

## 2. Migration Graph & Roadmap

1. **Stage 1 (Pre-Flight Isolation & Verification)**:
   - Verify zero AST compilation errors across active source directories.
   - Run baseline test suite (`tests/test_scientific_architecture_uca2026.py`, `tests/test_superior_architecture_minimal.py`).

2. **Stage 2 (Singletons Paper Traceability Enforcement)**:
   - Ensure all 5 core singletons (`CognitiveSystemController`, `SkillRouter`, `HierarchicalMemorySystem`, `MultiAgentDebateSystem`, `EvolutionGate`) incorporate explicit top-level module docstrings citing all 8 mandatory arXiv papers (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`).

3. **Stage 3 (Subsystem Consolidation & Authority Verification)**:
   - Enforce single authoritative instance creation via `__new__` lock semantics across all singletons.
   - Verify registry registration via `UnifiedComponentRegistry`.

4. **Stage 4 (Regression & Integration Testing)**:
   - Execute unit and integration tests across core singletons and orchestrator workflows.

---

## 3. Risk Analysis & Mitigation Matrix

| Risk Category | Potential Impact | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Singleton Race Condition** | Concurrent thread instantiation creates duplicate singletons | High | Double-checked locking pattern inside `__new__` using `threading.Lock()`. |
| **Fail-Open Safety Failure** | Unregistered shield allows un-audited capital movement | Critical | `UnifiedDecisionBus._check_consensus` enforces fail-closed rejection on missing shield reports. |
| **Memory Graph Bloat** | Graph memory exceeds RAM bounds over long runtime | Medium | `SAGEGraphMemory.compact_graph` automatically prunes orphan and low-utility ($w < 0.1$) edges. |
| **Schema Incompatibility** | Legacy data breaks during schema upgrade | High | `HierarchicalMemorySystem.migrate_to_version` provides sequential up/down step migrations with SHA-256 integrity validation. |

---

## 4. Rollback Strategy
If any benchmark or validation gate fails during deployment:
1. **Immediate State Reset**: Execute class-level `.reset()` on all core singletons (`CognitiveSystemController.reset()`, `SkillRouter.reset()`, `HierarchicalMemorySystem.reset()`, `UnifiedDecisionBus.reset()`).
2. **Schema Down-Migration**: Call `hms.migrate_to_version("1.0")` to roll back knowledge graph schemas deterministically.
3. **LogAct State Isolation**: Flush `UnifiedDecisionBus._log` and re-bind queue instances to the primary event loop.

---

## 5. Benchmark Plan
- **Consensus Latency Benchmark**: Target $\le 10$ms for LogAct voter consensus under normal priority load.
- **Memory Retrieval Benchmark**: Target sub-15ms multi-hop subgraph extraction across 5,000 graph nodes.
- **Calibration Precision**: Target Expected Calibration Error $\text{ECE} \le 0.08$ across multi-agent debate outcomes.

---

## 6. Validation Plan
- Run automated test suite:
  ```bash
  poetry run pytest -o addopts="" tests/test_scientific_architecture_uca2026.py tests/test_superior_architecture_minimal.py tests/orchestrator/test_orchestrator_integration.py
  ```
- Target metric: **100% test pass rate (22/22 passed)** with zero AST or import errors.
