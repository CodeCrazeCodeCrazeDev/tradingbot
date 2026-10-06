# 04 Refactoring & Migration Plan (Scientific Architecture Baseline)

This document specifies the operational refactoring, dependency mapping, migration graph, risk analysis, rollback strategies, and validation protocols for aligning AlphaAlgo with the 2026 Scientific Architecture Specification.

---

## 1. System Dependency Graph

```
[UnifiedComponentRegistry]
       |
       +---> [CognitiveSystemController] (Layer 1)
       |           |
       |           +---> [SkillRouter] (Layer 2) ---> [HASPExecutor]
       |           |
       |           +---> [MultiAgentDebateSystem] (Layer 3) ---> [HeadAI]
       |           |
       |           +---> [HierarchicalMemorySystem] (Layer 4) ---> [SAGEGraphMemory]
       |
       +---> [EvolutionGate] (Layer 5)
       |
       +---> [ImmutableShield] (Layer 5)
```

---

## 2. Migration Graph & Execution Sequence

The migration plan follows a non-breaking, step-by-step sequence:

```
Phase 1: Literature Synthesis & Documentation
   └─► Authored 01_MANDATORY_AND_EXTENDED_PAPERS_DECOMPOSITION.md
   └─► Authored 02_GAP_ANALYSIS_MATRIX_EXPANDED.md
   └─► Authored 03_UNIFIED_SCIENTIFIC_ARCHITECTURE_EXPANDED.md
   └─► Authored 04_REFACTORING_AND_MIGRATION_PLAN_EXPANDED.md

Phase 2: Core Singletons Traceability Matrix Alignment
   └─► Update module docstrings across core singletons:
         - `trading_bot/core/csc/controller.py`
         - `trading_bot/core/csc/router.py`
         - `trading_bot/core/hms/memory.py`
         - `trading_bot/agents/multi_agent_debate.py`
         - `trading_bot/governance/evolution_gate.py`

Phase 3: Automated Suite Verification
   └─► Run `tests/test_scientific_architecture_uca2026.py`
   └─► Verify 100% test pass rate
```

---

## 3. Risk Analysis & Mitigation Strategies

| Risk Factor | Severity | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Docstring Missing Citation** | Low | Low | Test failure in `test_core_singletons_paper_traceability_matrix` | Ensure all 8 mandatory arXiv IDs (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`) are explicitly present in top-level module docstrings. |
| **Duplicate Component Instantiation** | High | Low | Ambiguous state routing and memory fragmentation | Enforce singleton `__new__` pattern and registration in `UnifiedComponentRegistry`. |
| **Memory Migration Breakage** | Medium | Low | Failure during schema version transition ($v \rightarrow v+0.1$) | Use step-by-step up/down migrations in `HierarchicalMemorySystem.migrate_to_version`. |

---

## 4. Rollback Strategy

If any architectural issue is encountered during refactoring or testing:

1. **Local Rollback**:
   - Individual files can be restored using version control (`git checkout -- <filepath>`).
2. **Singleton Reset**:
   - Execute class-level lifecycle resets:
     - `CognitiveSystemController.reset()`
     - `SkillRouter.reset()`
     - `HierarchicalMemorySystem.reset()`
3. **Schema Preservation**:
   - `HierarchicalMemorySystem` maintains full schema backups in `memory_schema.json` prior to applying dynamic migration steps.

---

## 5. Benchmark & Validation Plan

Every change must be validated against the following benchmark suites:

1. **Traceability Verification**:
   - Test: `test_core_singletons_paper_traceability_matrix()` in `tests/test_scientific_architecture_uca2026.py`.
   - Threshold: 100% docstring match across all 5 core singletons.

2. **DiscoLoop Reasoning Verification**:
   - Test: `test_discoloop_and_pivot_refine_integration()`
   - Threshold: $\ge 2$ discrete tokens generated, valid continuous latent state vector.

3. **HASP Guardrail Pre-emption Verification**:
   - Test: `test_hasp_guardrail_preemption()`
   - Threshold: Status `"pf_intervention"`, Action `"override_to_hold"` when volatility $> 0.3$.

4. **SAGE Multi-Hop Graph Retrieval Verification**:
   - Test: `test_sage_graph_memory_subgraph_retrieval()`
   - Threshold: Non-empty evidence subgraph returned with valid edge attributes.
