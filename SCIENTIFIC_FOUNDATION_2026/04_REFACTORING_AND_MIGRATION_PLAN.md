# Scientific Refactoring Plan & Migration Specification (2026)

## Overview
This document specifies the dependency graph, migration steps, risk mitigation strategy, rollback procedures, and validation protocols for refactoring AlphaAlgo to incorporate the 8 mandatory arXiv research principles.

---

## 1. Dependency Graph

```
UnifiedEventBus (LogAct - arXiv:2607.00341)
  └─► CognitiveSystemController (Master CSC)
        ├─► HierarchicalMemorySystem (S2L - arXiv:2605.20025)
        ├─► SkillRouter (NanoResearch - arXiv:2605.10813)
        └─► MultiAgentDebateSystem (Search-R1 & DeepWeb - arXiv:2605.12061 / 2605.21482)
              └─► EvolutionGate (AutoResearchClaw & CORAL - arXiv:2605.17734 / 2607.01224)
```

---

## 2. Migration Graph & Sequential Stages

1. **Stage 1**: Verify `CognitiveSystemController` paper docstring traceability matrix and variational free energy calculation.
2. **Stage 2**: Verify `SkillRouter` sub-agent dynamic bandit routing and latency budgeting.
3. **Stage 3**: Verify `HierarchicalMemorySystem` latent embedding store and SHA-256 provenance hashes.
4. **Stage 4**: Verify `MultiAgentDebateSystem` MCTS lookahead, Quiet-STaR thought scratchpads, and multimodal verifier gates.
5. **Stage 5**: Verify `EvolutionGate` AST sandboxing (`SecureASTVisitor`) and out-of-sample backtest evaluation.
6. **Stage 6**: Run complete unit, integration, and stress test suites across multi-agent debate and decision governance.

---

## 3. Risk Analysis & Mitigation Strategy

| Identified Risk | Risk Severity | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| Dynamic AST execution error in `EvolutionGate` | High | Runtime exception during strategy mutation | Pre-evaluate code AST using `SecureASTVisitor` before `exec()` calls; revert on exception. |
| MCTS search tree lookahead explosion | Medium | Multi-agent debate latency exceedance | Bound maximum search depth ($D \le 5$) and rollout count ($N \le 100$). |
| Memory leak in continuous replay buffer | Medium | Memory overflow over long-horizon runs | Limit memory stores to fixed max-length deque ring buffers ($1,000$ entries). |
| Disagreement between multimodal verifiers | Low | Trade rejection / false negative | Fall back to `ABSTAIN` action whenever verifier confidence threshold is unreached. |

---

## 4. Rollback Strategy
* **Automated Rollback Trigger**: Any test failure in `pytest tests/agents/ tests/decision_governance/` triggers immediate file restoration.
* **Rollback Action**: Use git or `restore_file` to revert target files back to verified commit baseline (`b8f5957b`).

---

## 5. Benchmark & Validation Protocol
* **Automated Test Suite**:
  ```bash
  poetry run pytest tests/agents/ tests/decision_governance/
  ```
* **Success Criteria**:
  * 100% test pass rate across all 52 multi-agent and decision governance test cases.
  * Zero AST compilation or syntax errors across active Python source files.
  * Full docstring traceability matrix citing all 8 mandatory arXiv papers across core singletons.
