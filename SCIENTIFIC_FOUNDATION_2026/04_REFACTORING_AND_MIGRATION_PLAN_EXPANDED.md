# Refactoring, Migration & Risk Plan (Expanded 2026)

## Executive Summary
This document outlines the migration strategy, risk analysis, rollback protocol, and verification plan for deploying AlphaAlgo's unified scientific architecture.

---

## Architectural Dependency Graph

```
[Observation] ──> [CognitiveSystemController] ──> [SkillRouter] ──> [HASP Guardrails]
                          │
                          ├──> [HierarchicalMemorySystem] (SAGE & AutoMem)
                          ├──> [MultiAgentDebateSystem] (Bayesian Consensus)
                          └──> [EvolutionGate] (EKSFT Monotone Safety)
```

---

## Migration Steps & Phase Strategy

1. **Phase 1: Subsystem Verification & Singleton Audit**:
   - Verify that all core singletons (`CognitiveSystemController`, `SkillRouter`, `HierarchicalMemorySystem`, `MultiAgentDebateSystem`, `EvolutionGate`) maintain non-overlapping responsibility boundaries.
   - Ensure all docstrings include complete paper traceability matrices citing all 8 mandatory arXiv papers.

2. **Phase 2: Controller & Integration Alignment**:
   - Align `CognitiveSystemController` docstrings and runtime capabilities with EKSFT, DiscoLoop, AutoMem, SAGE, NanoResearch, AutoResearchClaw, HASP, and DeepWeb-Bench.
   - Confirm zero duplicate orchestrators, registries, or world models exist in the active execution path.

3. **Phase 3: Automated Verification Suite Execution**:
   - Run `tests/test_scientific_architecture_uca2026.py` and core agent/decision test suites.
   - Validate 100% test pass rate across all paper capabilities and system integration points.

---

## Risk Analysis & Mitigation Strategy

| Risk Scenario | Severity | Likelihood | Mitigation Strategy | Rollback Action |
| :--- | :--- | :--- | :--- | :--- |
| **Docstring or Traceability Mismatch** | Low | Low | Automated traceability matrix verification test (`test_core_singletons_paper_traceability_matrix`). | Re-apply docstring standard updates. |
| **HASP Over-Preemption** | Medium | Low | Calibrate HASP volatility thresholds (default 0.3) against historical regime variance. | Adjust threshold parameters or isolate to specific asset classes. |
| **EKSFT Convergence Failure** | High | Low | Enforce KL divergence bounds ($\tau_{\text{KL}}$) in `EvolutionGate`. | Revert model mutation to champion checkpoint. |

---

## Validation & Benchmark Plan
- **Traceability Test**: Verify all 5 core singletons cite all 8 mandatory arXiv research paper IDs (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`).
- **Functional Integration Test**: Verify HASP guardrail pre-emption, DiscoLoop multi-hop reasoning, SAGE evidence graph retrieval, and Pivot/Refine hypothesis loops.
- **Test Command**:
  ```bash
  /home/jules/.cache/pypoetry/virtualenvs/trading-bot-9TtSrW0h-py3.12/bin/pytest -o addopts="" tests/test_scientific_architecture_uca2026.py
  ```
