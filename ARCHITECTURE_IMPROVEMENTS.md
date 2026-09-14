# AlphaAlgo Structural & Architectural Improvements (2026)

This document details the structural simplifications, system unifications, and duplicate eliminations performed to achieve the "One Brain" pattern under the Unified Scientific Architecture (UCA-2026).

---

## 1. The "One Brain" Architecture Consolidation

Prior to the UCA-2026 migration, the AlphaAlgo codebase suffered from structural sprawl, with multiple legacy modules and redundant orchestration loops competing for state and execution ownership.

### **Structural Purge & Remediation**:
- Fixed syntax errors and orphaned blocks in `trading_bot/database/production_database.py`, `trading_bot/core/service_registry.py`, and `trading_bot/core_agent_system/master_orchestrator.py`.
- Consolidated operational scripts in `scripts/` by fixing indentation and class method scoping across `deploy_5star_production.py`, `run_alphaalgo_5star.py`, and `alphaalgo_autonomous_operator.py`.
- Enforced a single repository-wide event bus (`UnifiedDecisionBus`) and a single active controller singleton (`CognitiveSystemController`).
- Programmatically locked the repository against duplicate imports using a custom architecture invariant test suite (`tests/architecture/test_architecture_invariants.py`).

---

## 2. Decoupling of Capabilities & Single Responsibility

We have enforced strict single-responsibility boundaries over core modules:
1.  **Sensory Processing & Surprise**: Managed solely by `CognitiveSystemController` inside `controller.py`. Surprise calculation is modeled on Active Inference principles to update the variational free energy state sequentially.
2.  **Strategic Reasoning & Routing**: Consolidated into `SkillRouter` inside `router.py`. Prompt-based routing, program function (PF) pre-emption, and low-rank adapter selection (S2L) are managed through a unified `route_task` API returning the subscriptable `SkillRouteOutcome` dataclass contract.
3.  **Knowledge & Episodic Ledger**: Owned entirely by `HierarchicalMemorySystem` (HMS) inside `memory.py`. Relational graph indexing (SAGE Graph Memory) tracks claims, evidence, and provenances securely.
4.  **Causal World Model Rollouts**: Handled by the `UnifiedWorldModel`. It leverages structural causal equations (do-calculus) to perform counterfactual simulations instead of simple statistical forecasting.
5.  **Multi-Agent Decision Synthesis**: Owned by `HeadAI` and `BayesianDecisionEngine` inside `trading_bot/agents/multi_agent_debate.py`, enforcing multi-verifier falsification prior to trade commitment.

---

## 3. Security Hardening & Interface Standardisation

- **AST Sandboxing**: Integrated `SecureASTVisitor` to validate dynamic strategy code before execution in parallel backtesting environments (`trading_bot/distributed/parallel_backtester.py`).
- **Safe Pickle Deserialization**: Replaced un-sanitized `pickle.load` with `safe_load` from `trading_bot.security.safe_pickle`.
- **Normalized Context Contracts**: `NormalizedMarketContext` ensures immutability across all debate, risk, and cognitive processing loops.
- **Hypothesis Collection Safety**: Refactored test mocks (`MockObj`) to raise `AttributeError` on dunder attribute lookups, ensuring clean test suite discovery under Hypothesis.
