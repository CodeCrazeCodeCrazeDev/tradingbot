# Phase 4 — Refactoring & Migration Plan (UCA 2026)

This document details the dependency graph, migration path, risk analysis, rollback strategy, benchmark plan, and validation framework for the Scientific Architecture Refactoring Directive.

---

## 1. Dependency Graph & Module Hierarchy

```
[DeepWeb-Bench Ingestion (trading_bot/intel/news_pipeline.py)]
                         |
                         v
[CognitiveSystemController (trading_bot/core/csc/controller.py)] <---- [DiscoLoop Engine]
            |                                       |
            v                                       v
[SkillRouter (trading_bot/core/csc/router.py)]     [HierarchicalMemorySystem (trading_bot/core/hms/memory.py)]
   (HASP Safety Pre-emption)                          (AutoMem Decay & SAGE Graph)
            |                                       ^
            v                                       |
[MultiAgentDebateSystem (trading_bot/agents/multi_agent_debate.py)]
   (NanoResearch Epistemic Voting)
            |
            v
[EvolutionGate (trading_bot/governance/evolution_gate.py)]
   (EKSFT Policy Fine-Tuning & AutoResearchClaw Code Mutations)
```

---

## 2. Migration Plan & Sequence

1. **Step 1 — Documentation Traceability**:
   - Update module docstrings across all 5 core singletons (`CognitiveSystemController`, `SkillRouter`, `HierarchicalMemorySystem`, `MultiAgentDebateSystem`, `EvolutionGate`) to cite all 8 mandatory arXiv research papers.

2. **Step 2 — Singleton Integrity Verification**:
   - Verify that all core singletons strictly follow single-instance initialization (`__new__` singleton patterns) and eliminate legacy duplicate wrappers.

3. **Step 3 — Functional Pipeline Integration**:
   - Confirm seamless execution flow across news intelligence ingestion, active inference step, skill routing, multi-agent debate, memory persistence, and evolution gate mutation checks.

4. **Step 4 — Automated Test Suite Execution**:
   - Run `tests/test_scientific_architecture_uca2026.py` and core agent/scientific test suites.

---

## 3. Risk Analysis & Mitigation Strategies

| Identified Risk | Severity | Probable Root Cause | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Missing Paper Citations** | Medium | Omission in singleton module docstring header | Enforce automated docstring verification test (`test_core_singletons_paper_traceability_matrix`). |
| **Latent State Divergence** | High | Unconstrained DiscoLoop latent update rollouts | Enforce L2 norm bounds on latent continuous vectors $z_t$. |
| **Graph Query Overhead** | Medium | Multi-hop SAGE graph depth $> 3$ | Bound graph traversal depth to $d \le 3$ and node count $K \le 50$. |
| **Safety False Positives** | Medium | Overly strict HASP volatility threshold | Implement dynamic volatility percentile thresholding. |

---

## 4. Rollback Strategy
- **Version Pinning**: All architectural commits are tracked under atomic git commits.
- **Automated Rollback**: In case of regression or test failure, restore individual singleton files from clean git workspace (`git checkout HEAD -- <filepath>`).

---

## 5. Benchmark & Validation Framework
- **Traceability Benchmark**: 100% citation coverage across 5 core singletons for all 8 mandatory arXiv papers.
- **Functional Integration Benchmark**: 0 failures across `tests/test_scientific_architecture_uca2026.py`.
- **Execution Speed**: Sub-millisecond routing and memory retrieval latency bounds.
