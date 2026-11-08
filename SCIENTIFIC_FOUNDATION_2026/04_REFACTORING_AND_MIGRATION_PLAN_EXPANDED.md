# Phase 4 — Refactoring and Migration Plan: Graphs, Risks, Benchmarks, and Validation

## Executive Summary
This document fulfills Phase 4 of the **Scientific Architecture Refactoring Directive**. It defines the precise dependency graph, migration sequence, risk mitigation matrix, rollback protocol, benchmark suite, and validation plan required to execute code refactoring without disrupting operational continuity or test integrity.

---

## 4.1 Dependency Graph

```
[MANDATORY PAPERS: EKSFT, DiscoLoop, AutoMem, SAGE, NanoResearch, AutoResearchClaw, HASP, DeepWeb-Bench]
                                         |
                                         v
                      [SCIENTIFIC_FOUNDATION_2026 Docs]
                                         |
                                         v
                  [trading_bot/core/csc/controller.py (Docstring & Traceability)]
                                         |
                                         +---> [trading_bot/core/csc/router.py]
                                         +---> [trading_bot/core/hms/memory.py]
                                         +---> [trading_bot/agents/multi_agent_debate.py]
                                         +---> [trading_bot/governance/evolution_gate.py]
                                         |
                                         v
                [tests/test_scientific_architecture_uca2026.py Verification]
```

---

## 4.2 Migration Graph & Execution Stages

1. **Stage 1 — Docstring Traceability Alignment**:
   - Update `trading_bot/core/csc/controller.py` module docstring to cite all 8 mandatory arXiv research papers (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`).

2. **Stage 2 — Operational Singletons Audit**:
   - Verify that `router.py`, `memory.py`, `multi_agent_debate.py`, and `evolution_gate.py` maintain complete docstring traceability matrices.

3. **Stage 3 — Integration Test Suite Run**:
   - Execute `python3 -m pytest -o addopts="" tests/test_scientific_architecture_uca2026.py`.

---

## 4.3 Risk Analysis & Mitigation Matrix

| Risk Event | Severity | Impact | Mitigation Strategy |
|---|---|---|---|
| Missing Paper Citation in Docstrings | High | Test failure in `test_core_singletons_paper_traceability_matrix` | Explicitly list all 8 mandatory arXiv paper IDs in top-level module docstrings. |
| Import Side-Effects during Test Collection | Medium | Unhandled `ModuleNotFoundError` | Use try/except fallback wrappers or system dependency environment (`requirements_no_mt5.txt`). |
| Singleton Re-initialization Contamination | Medium | State leakage between test cases | Invoke `CognitiveSystemController.reset()` and `SkillRouter.reset()` in test fixtures. |

---

## 4.4 Rollback Strategy
If any refactoring step introduces regression or breaks existing test suites:
1. Revert target file using `restore_file` or git checkout.
2. Re-run `python3 -m pytest -o addopts="" tests/test_scientific_architecture_uca2026.py` to confirm clean recovery.

---

## 4.5 Benchmark & Validation Plan
- **Traceability Validation**: 100% pass rate on `test_core_singletons_paper_traceability_matrix`.
- **Reasoning Loop Validation**: 100% pass rate on `test_discoloop_and_pivot_refine_integration`.
- **HASP Safety Validation**: 100% pass rate on `test_hasp_guardrail_preemption`.
- **SAGE Memory Retrieval Validation**: 100% pass rate on `test_sage_graph_memory_subgraph_retrieval`.
