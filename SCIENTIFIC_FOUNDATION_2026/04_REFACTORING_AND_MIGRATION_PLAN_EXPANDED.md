# 04 Refactoring and Migration Plan Expanded (UCA 2026 Directive)

## Executive Summary
This document outlines the detailed refactoring, dependency, migration, risk, rollback, and validation plans for incorporating all 8 mandatory arXiv research papers into AlphaAlgo's codebase.

---

## 1. Dependency Graph

```
trading_bot/core/csc/controller.py (CognitiveSystemController)
 ├──> trading_bot/core/csc/router.py (SkillRouter)
 ├──> trading_bot/core/hms/memory.py (HierarchicalMemorySystem)
 ├──> trading_bot/agents/multi_agent_debate.py (MultiAgentDebateSystem)
 └──> trading_bot/governance/evolution_gate.py (EvolutionGate)
```

## 2. Migration Graph & Execution Sequence
1. **Stage 1 (Docstring & Traceability Matrix Alignment):** Update module docstrings across all 5 singletons to explicitly cite all 8 mandatory arXiv research papers (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`).
2. **Stage 2 (Functional Alignment Verification):** Verify that `CognitiveSystemController`, `SkillRouter`, `HierarchicalMemorySystem`, `MultiAgentDebateSystem`, and `EvolutionGate` correctly implement the required methods (`_run_discoloop_reasoning`, HASP guardrail pre-emption, SAGE subgraph retrieval, etc.).
3. **Stage 3 (Validation Test Suite):** Execute `tests/test_scientific_architecture_uca2026.py` to confirm 100% compliance across docstring traceability and functional integration tests.

## 3. Risk Analysis & Mitigation
- **Risk 1: Docstring Citation Mismatch:** Standardized paper IDs in docstrings to ensure exact regex and string matching (`2605.29303`, `2607.00341`, `2607.01224`, `2605.12061`, `2605.10813`, `2605.20025`, `2605.17734`, `2605.21482`).
- **Risk 2: Performance Overhead:** Fast-path sub-5ms NanoResearch distillation prevents latency degradation during high-frequency execution.

## 4. Rollback Strategy
- All modifications are additive to docstrings and methods within existing canonical singletons. Git commit checkpoints enable instant rollback if any regression occurs.

## 5. Benchmark & Validation Plan
- Run `poetry run pytest -o addopts="" tests/test_scientific_architecture_uca2026.py` to validate all 4 integration tests (docstring traceability matrix, DiscoLoop/Pivot-Refine integration, HASP guardrail pre-emption, SAGE graph memory retrieval).
