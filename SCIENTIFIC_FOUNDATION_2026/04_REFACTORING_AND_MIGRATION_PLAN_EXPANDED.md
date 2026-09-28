# Architectural Refactoring & Migration Plan: AlphaAlgo 2026

This document details the refactoring, dependency graph, migration roadmap, risk mitigation strategy, and validation plan for incorporating the validated scientific principles across AlphaAlgo.

---

## 1. Subsystem Dependency Graph

```
[ UnifiedDecisionBus ]
         |
         +--> [ CognitiveSystemController ]
         |            |
         |            +--> [ SkillRouter ] ---> [ HASP Invariant Guards ]
         |            |
         |            +--> [ HierarchicalMemorySystem ] ---> [ SAGEGraphMemory ]
         |            |
         |            +--> [ MultiAgentDebateSystem ] ---> [ BayesianDecisionEngine ]
         |
         +--> [ EvolutionGate ] ---> [ Monotone-Safe & EKSFT Compliance ]
```

---

## 2. Migration Roadmap

### Step 1: Subsystem Single-Implementation Verification
- Verify `CognitiveSystemController`, `SkillRouter`, `HierarchicalMemorySystem`, `EvolutionGate`, and `MultiAgentDebateSystem` maintain exact single-instance singleton patterns with zero duplicate legacy wrappers.

### Step 2: SAGE Graph & Evolution Gate Refinement
- Ensure `SAGEGraphMemory` supports both default path initialization and batch `evolve()` interface.
- Ensure `EvolutionGate` correctly parses all benchmark metric representations (`val`, `score`, `reward`, `perf`).

### Step 3: End-to-End System-Wide Verification
- Run complete test suites (`tests/verification/test_scientific_correctness.py`, `tests/validation/test_uca_v5_scientific_benchmarks.py`, `tests/test_scientific_modules.py`).

---

## 3. Risk Analysis & Mitigation Matrix

| Risk Event | Severity | Impact Area | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| Metric Parsing Mismatch in Validation | Medium | `EvolutionGate` | Multi-key metric extraction fallback in `parse_metrics` supporting `val`, `score`, `reward`, `perf`. |
| SAGE Storage Directory Non-Existence | Low | `SAGEGraphMemory` | Check `dirname` validity before calling `os.makedirs(dirname, exist_ok=True)`. |
| Excessive Graph Density | Medium | `SAGEGraphMemory` | Automated BFS depth limiting ($h \le 2$) and low-confidence edge compaction (`compact_graph`). |
| Uncalibrated Multi-Agent Consensus | High | `MultiAgentDebateSystem` | Integrated Expected Calibration Error (ECE) thresholding and Bayesian uncertainty weighting. |

---

## 4. Rollback Strategy
1. **Automated Rollback Trigger:** If any test in `test_scientific_correctness.py` or `test_uca_v5_scientific_benchmarks.py` fails during deployment, `EvolutionGate` automatically rejects the candidate configuration.
2. **State Fallback:** HMS schema versioning and SAGE GraphML checkpointing maintain backward-compatible migration steps (`migrate_to_version`).

---

## 5. Benchmark & Validation Plan

### Target Benchmarks
1. **CL-Bench Gain Metric ($G \ge 0.05$):** Evaluated via `tests/validation/test_uca_v5_scientific_benchmarks.py::test_cl_bench_gain_metric`.
2. **Variational Free Energy Minimization Loop:** Evaluated via `tests/validation/test_uca_v5_scientific_benchmarks.py::test_vfe_minimization_loop`.
3. **HASP Invariant Verification:** Evaluated via `tests/validation/test_uca_v5_scientific_benchmarks.py::test_hasp_invariant_checking`.
4. **End-to-End Scientific Correctness:** Evaluated via `tests/verification/test_scientific_correctness.py`.
