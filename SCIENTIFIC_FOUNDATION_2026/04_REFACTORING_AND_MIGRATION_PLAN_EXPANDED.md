# Phase 4: Refactoring & Migration Plan (UCA-2026)

This document specifies the exact dependency topology, migration phases, risk matrix, rollback procedures, benchmark metrics, and validation gates governing the refactoring of AlphaAlgo UCA-2026.

---

## 1. System Dependency Graph & Component Interaction Topology

```
                         ┌─────────────────────────────┐
                         │   UnifiedComponentRegistry  │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│     SkillRouter (HASP)    │ │ CognitiveSystemController │ │ HierarchicalMemorySystem  │
│  Executable Guardrails    │◄┤     "One Brain" (CSC)     ├─►│    (SAGE & AutoMem)       │
└──────────────┬────────────┘ └─────────────┬─────────────┘ └─────────────┬─────────────┘
               │                            │                             │
               │                            ▼                             │
               │              ┌───────────────────────────┐               │
               └─────────────►│    UnifiedDecisionBus    │◄──────────────┘
                              │      (LogAct SMR)         │
                              └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │      ImmutableShield      │
                              │     Hard Governance       │
                              └───────────────────────────┘
```

---

## 2. 6-Phase Migration Graph & Implementation Roadmap

1. **Phase 4.1: Foundation Stabilization**:
   - Enforce thread-safe singleton initialization (`__new__`) across `UnifiedDecisionBus`, `UnifiedComponentRegistry`, and `CognitiveSystemController`.
   - Validate zero sidecar registries or duplicate orchestrators exist in active source trees.

2. **Phase 4.2: Reasoning Core Refactoring (`CognitiveSystemController`)**:
   - Embed paper traceability docstrings citing all 8 mandatory arXiv research papers.
   - Integrate `DiscoLoopCell` continuous-discrete recurrence channel.
   - Implement `_pivot_refine_loop()` for strategy self-healing during simulation failure.

3. **Phase 4.3: Guardrails & Skill Programs (`SkillRouter`)**:
   - Refactor `SkillRouter` to compile textual advice into executable Python Program Functions (PFs).
   - Implement deterministic trigger checks (`volatility_guardrail`, `margin_guardrail`) returning structured action overrides.

4. **Phase 4.4: Graph Memory & Metamemory (`HierarchicalMemorySystem`)**:
   - Implement SAGE Bellman TD edge-weight update equations ($W_{t+1} = W_t + \gamma (R - W_t)$).
   - Implement AutoMem `optimize_metamemory()` with file-schema migration and utility tracking.

5. **Phase 4.5: Selective Fine-Tuning Integration (`EKSFT`)**:
   - Ensure `trading_bot/core/eksft.py` implements dual-model reference KL divergence evaluation and dynamic token loss masking tensors.

6. **Phase 4.6: Automated Testing & Validation**:
   - Author `tests/test_scientific_architecture_uca2026.py` covering all 8 mandatory paper principles and execute test suites via `poetry run pytest`.

---

## 3. Risk Analysis & Mitigation Matrix

| Risk Factor | Threat Level | Failure Impact | Concrete Technical Mitigation |
| :--- | :--- | :--- | :--- |
| **Quantization Drift in DiscoLoop** | Medium | Reasoning channel decouples from world state | Enforce straight-through realignment ($\alpha = 0.90$) every reasoning step $k$. |
| **Hub Node Saturation in SAGE Graph** | High | Retrieval latency increases exponentially | Trigger automatic graph compaction when $|V| > 10,000$ or node degree $> 500$. |
| **Overly Conservative HASP Guardrails** | High | Valid alpha trade opportunities are rejected | Set HASP trigger thresholds dynamically based on 30-day volatility quantiles. |
| **Over-Masking in EKSFT Fine-Tuning** | Medium | Gradient starvation slows policy convergence | Cap maximum masked token ratio at $\rho_{masked} \le 0.35$. |
| **Consensus Deadlock on Decision Bus** | High | Trade execution proposals time out | Enforce fallback to default Shield voter and 5.0-second timeout handling. |

---

## 4. Rollback Strategy & Verification Gates

1. **Rollback Strategy**:
   - Every file change is git-tracked. If any test in `tests/test_scientific_architecture_uca2026.py` fails during CI/CD, the deployment script executes `git checkout HEAD -- <filepath>` to revert to the previous verified commit.

2. **Benchmark Plan & Validation Metrics**:
   - **Reasoning Latency**: $\le 15.0\,\text{ms}$ per 12-step Active Inference pass.
   - **Memory Retrieval Precision**: $\ge 90.0\%$ Recall@5 on SAGE causal graph queries.
   - **Guardrail Interception Speed**: $\le 1.0\,\text{ms}$ execution for HASP Program Functions.
   - **Singleton Integrity**: $100\%$ identity match (`assert inst1 is inst2`) across concurrent threads.
   - **Test Suite Pass Rate**: $100\%$ pass rate across all core test suites.

---

This completes Phase 4: Refactoring & Migration Plan.
