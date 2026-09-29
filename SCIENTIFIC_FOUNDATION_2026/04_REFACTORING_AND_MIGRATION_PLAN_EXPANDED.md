# Phase 4: Refactoring Plan, Migration Graph, & Validation Plan (2026)

This document details the refactoring plan, component dependency graph, risk analysis, rollback strategy, benchmark plan, and validation framework for AlphaAlgo.

---

## 1. System Dependency Graph

```
                   [UnifiedDecisionBus]
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
  [CognitiveSystemController] ──> [SkillRouter]
            │               │               │
            ▼               ▼               │
  [MultiAgentDebateSystem]  [HASPExecutor]  │
            │                               │
            ▼                               ▼
  [HierarchicalMemorySystem] <─── [EvolutionGate]
            │
            ▼
   [SAGEGraphMemory]
```

---

## 2. Migration Strategy & Phase Sequence

The refactoring follows a zero-downtime, non-disruptive migration plan:

1. **Phase A — Subsystem Singletons & Paper Traceability**:
   - Verify thread-safe `__new__` singleton pattern and docstring Paper Traceability Matrices for all 5 core singletons (`CSC`, `SkillRouter`, `HMS`, `MultiAgentDebateSystem`, `EvolutionGate`).
2. **Phase B — Active Inference Pipeline Alignment**:
   - Ensure `CognitiveSystemController` executes the complete 12-stage active inference pipeline with `DiscoLoopCell` and `HASP` pre-emption.
3. **Phase C — Risk Manager Position Sizing Scaling**:
   - Verify `PortfolioRiskManager.validate_trade` handles dollar-denominated trade inputs scaled by portfolio value.
4. **Phase D — Verification & Benchmark Testing**:
   - Run automated test suites across `tests/test_scientific_architecture_uca2026.py`, `tests/agents/`, `tests/decision_governance/`, and `tests/orchestrator/`.

---

## 3. Risk Analysis & Mitigation Matrix

| Potential Risk | Impact Level | Mitigation Strategy |
| :--- | :--- | :--- |
| **Singleton Instantiation Race** | High | Thread-safe double-checked locking (`with cls._lock:`) in `__new__` for all core singletons. |
| **Position Sizing Overflow** | High | Automatic dollar-to-fraction size conversion in `PortfolioRiskManager.validate_trade`. |
| **Memory Graph Traversal Latency** | Medium | Subgraph depth limits ($h \le 2$) and node compaction (`compact_graph`) in `SAGEGraphMemory`. |
| **Debate Consensus Deadlock** | Medium | Active fallback to `TradeAction.NO_TRADE` or `HOLD` when agent analysis fails or risk sentinel vetoes. |

---

## 4. Rollback Strategy & Validation Plan

- **Rollback Strategy**: Every core singleton includes an explicit `reset()` classmethod. If an isolated test or runtime cycle fails, `reset()` restores singletons to a clean state without process restarts.
- **Validation Plan**:
  1. `test_core_singletons_paper_traceability_matrix`: Verifies all 8 mandatory arXiv papers are cited across all 5 singletons.
  2. `test_discoloop_and_pivot_refine_integration`: Verifies discrete-continuous reasoning recurrence.
  3. `test_hasp_guardrail_preemption`: Verifies HASP volatility pre-emption.
  4. `test_sage_graph_memory_subgraph_retrieval`: Verifies multi-hop graph retrieval.
  5. Full test suite execution across agents, governance, and orchestrator modules.
