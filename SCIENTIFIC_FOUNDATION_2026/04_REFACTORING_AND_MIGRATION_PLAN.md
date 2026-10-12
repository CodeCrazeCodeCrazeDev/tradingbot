# Refactoring and Migration Plan (AlphaAlgo UCA-2026)

This document outlines the refactoring, migration, risk analysis, and rollback strategy for the AlphaAlgo scientific architecture refactoring.

---

## 1. Subsystem Dependency Graph

```
                                 [ UnifiedDecisionBus ]
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                        ▼                  ▼                  ▼
              [ ImmutableShield ]   [ EvolutionGate ]   [ SkillRouter ]
                        │                  │                  │
                        └──────────────────┼──────────────────┘
                                           │
                                           ▼
                            [ CognitiveSystemController ]
                                           │
                        ┌──────────────────┴──────────────────┐
                        │                                     │
                        ▼                                     ▼
           [ HierarchicalMemorySystem ]            [ VerificationSwarm ]
```

---

## 2. Migration Graph & Execution Sequence

1. **Step 1: Scientific Foundation Documentation**
   - Create/update `01_MANDATORY_PAPERS_DECOMPOSITION.md`, `02_GAP_ANALYSIS_MATRIX.md`, `03_UNIFIED_SCIENTIFIC_ARCHITECTURE.md`, and `04_REFACTORING_AND_MIGRATION_PLAN.md` under `SCIENTIFIC_FOUNDATION_2026/`.

2. **Step 2: Docstring Paper Traceability Matrix Update**
   - Update module docstrings across all 5 core singletons (`controller.py`, `router.py`, `memory.py`, `multi_agent_debate.py`, `evolution_gate.py`) to explicitly cite all 8 mandatory arXiv research papers:
     - `2605.29303` (LogAct)
     - `2607.00341` (DiscoLoop)
     - `2607.01224` (AutoMem)
     - `2605.12061` (SAGE)
     - `2605.10813` (NanoResearch)
     - `2605.20025` (AutoResearchClaw)
     - `2605.17734` (HASP)
     - `2605.21482` (DeepWeb-Bench)

3. **Step 3: Test Setup Remediation**
   - Repair mock shield voter setup in `tests/test_superior_architecture_minimal.py` by configuring `mock_shield.audit_log_action` as an `AsyncMock` returning `{"decision": "APPROVED", "approved": True}` to properly satisfy `UnifiedDecisionBus` consensus.

4. **Step 4: Scientific Architecture Verification**
   - Execute pytest suites `tests/test_superior_architecture_minimal.py` and `tests/test_scientific_architecture_uca2026.py` using `python3 -m pytest -o addopts=""`.

---

## 3. Risk Analysis & Mitigation Matrix

| Risk Event | Severity | Probability | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| Missing arXiv Paper Citation in Docstrings | High | Low | Run `test_core_singletons_paper_traceability_matrix` to verify all 5 core singletons cite all 8 papers. |
| LogAct Consensus Veto in Minimal Minimal Architecture Test | High | Medium | Configure `mock_shield.audit_log_action` as `AsyncMock(return_value={"decision": "APPROVED", "approved": True})`. |
| Unhandled Missing Dependencies in Test Runtime | Medium | Low | Ensure `torch`, `numpy`, `pandas`, `scipy`, `pytest`, `pytest-asyncio` are installed via `uv pip install --system`. |

---

## 4. Rollback Strategy & Validation Plan

- **Rollback Strategy:** All changes are non-breaking additions to module docstrings and test mocks. Git restore can revert specific files instantly without database or persistence schema migrations.
- **Validation Plan:** Verify 100% test pass rate across `test_superior_architecture_minimal.py` and `test_scientific_architecture_uca2026.py`.
