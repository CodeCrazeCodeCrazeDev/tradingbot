# Phase 4: Refactoring, Migration & Risk Analysis Plan (UCA V6 / 2026)

This document outlines the dependency graphs, migration graphs, risk mitigation strategies, rollback procedures, and benchmark plans for the UCA V6 scientific architecture refactoring.

---

## 1. Subsystem Dependency Graph

```
                   [ CognitiveSystemController ]
                        /        |        \
                       /         |         \
         [ SkillRouter ]  [ MultiAgentDebate ] [ HierarchicalMemory ]
               |                 |                   |
        [ HASP / S2L ]    [ Bayesian Engine ]  [ SAGE Graph Memory ]
               \                 |                   /
                \                |                  /
              [ LogAct UnifiedDecisionBus Backbone ]
                                 │
                   [ Monotone EvolutionGate ]
```

---

## 2. Migration Sequence Graph

```
[ Phase 4A: Docstring Paper Traceability Matrices ]
                 │
                 ▼
[ Phase 4B: Cognitive Brain Scientific Enhancements ]
  (VFE Bounds + Hawkes Intensity + Split Conformal + SHA-256 Provenance)
                 │
                 ▼
[ Phase 4C: Single Subsystem Canonicalization & Controller Alignment ]
                 │
                 ▼
[ Phase 4D: Test Suite Verification & Validation ]
```

---

## 3. Risk Analysis & Mitigation Matrix

| Risk Factor | Threat Level | Impact | Mitigation Strategy |
|---|---|---|---|
| **Concurrency Deadlock on Shared Bus** | High | System Stalls | Non-blocking queue migration with per-task loop re-binding in `UnifiedDecisionBus`. |
| **Recurrent State Exploding/Vanishing** | Medium | Incorrect Inference | Squashing continuous states with `tanh` and realigning with $\alpha=0.9$ in `DiscoLoopCell`. |
| **SAGE Graph Memory Bloat** | Medium | Latency Degradation | Automated graph compaction with degree/weight pruning ($w < 0.10$). |
| **EKSFT Mode Collapse** | Medium | Lost Exploration | Enforcement of $\tau_H \ge 0.8$ entropy threshold in `EvolutionGate`. |

---

## 4. Rollback Strategy & Verification Plan

1. **Rollback Strategy**:
   - Every file change is git-tracked and verified with targeted test suite runs.
   - Schema updates in `HierarchicalMemorySystem` support step-by-step down-migrations (`2.0` -> `1.1` -> `1.0`).

2. **Benchmark Plan**:
   - Measure consensus latency ($\le 10$ ms), test pass rate ($100\%$), and memory compaction efficiency.
   - Run active architecture test suites (`tests/test_superior_architecture_minimal.py`, `tests/test_uca_foundations.py`, `tests/orchestrator/test_orchestrator_integration.py`).
