# Phase 4: Refactoring and Migration Plan Expanded (2026)

This document specifies the dependency graph, migration path, risk analysis, rollback strategy, and verification plan for refactoring AlphaAlgo's core singletons.

---

## 1. System Dependency Graph

```
[UnifiedDecisionBus] (SMR Event Bus)
       ^
       |
[ImmutableShield] <---> [EvolutionGate] (Governance)
       ^                       ^
       |                       |
[CognitiveSystemController] (CSC - Strategic Brain)
       |
  +----+----+----+
  |         |    |
[SkillRouter] [HMS] [VerificationSwarm]
```

---

## 2. Migration Steps

1. **Step 1: Scientific Specifications & Traceability Mapping**: Author Phase 1-4 markdown files and update module docstrings across all 5 core singletons (`controller.py`, `router.py`, `memory.py`, `multi_agent_debate.py`, `evolution_gate.py`) citing all 8 mandatory arXiv paper IDs (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`).
2. **Step 2: Core Singleton Hardening**: Refactor `trading_bot/core/csc/controller.py` docstrings to cite all 8 mandatory papers.
3. **Step 3: Verification & Test Suite Execution**: Run `pytest` on `tests/test_scientific_architecture_uca2026.py` to confirm 100% test pass rate with zero failures.

---

## 3. Risk Analysis & Rollback Strategy

- **Risk**: Refactoring controller docstrings or methods could break import dependencies or test assertions.
- **Mitigation**: Perform isolated module test runs via `poetry run pytest -o addopts="" tests/test_scientific_architecture_uca2026.py` after editing.
- **Rollback Strategy**: Git restore specific Python files if regressions occur.
