# AlphaAlgo Structural & Architectural Improvements (2026)

This document details the structural simplifications, system unifications, and duplicate eliminations performed to achieve the "One Brain" pattern under the Unified Scientific Architecture (UCA-2026).

---

## 1. The "One Brain" Architecture Consolidation

Prior to the UCA-2026 migration, the AlphaAlgo codebase suffered from structural sprawl, with multiple folders (`agents 2/`, `advanced_systems 2/`, and redundant orchestration loops) competing for state and execution ownership.

### **Structural Purge**:
- Deleted all duplicate directories (such as `agents 2/` and `advanced_systems 2/`).
- Enforced a single repository-wide event bus (`UnifiedDecisionBus`) and a single active controller singleton (`CognitiveSystemController`).
- Programmatically locked the repository against duplicate imports using a custom architecture invariant test suite (`tests/architecture/test_architecture_invariants.py`).

---

## 2. Decoupling of Capabilities & Single Responsibility

We have enforced strict single-responsibility boundaries over core modules:
1.  **Sensory Processing & Surprise**: Managed solely by `CognitiveSystemController` inside `controller.py`. Surprise calculation is modeled on Active Inference principles to update the variational free energy state sequentially.
2.  **Strategic Reasoning & Routing**: Consolidated into `SkillRouter` inside `router.py`. Prompt-based routing, program function (PF) pre-emption, and low-rank adapter selection (S2L) are managed through a unified `route_task` API returning the subscriptable `SkillRouteOutcome` dataclass contract.
3.  **Knowledge & Episodic Ledger**: Owned entirely by `HierarchicalMemorySystem` (HMS) inside `memory.py`. Relational graph indexing (SAGE Graph Memory) tracks claims, evidence, and provenances securely.
4.  **Causal World Model rollouts**: Handled by the `UnifiedWorldModel`. It leverages structural causal equations (do-calculus) to perform counterfactual simulations instead of simple statistical forecasting.

---

## 3. Eliminating Fragile Shims & Hardening Interfaces

To avoid technical debt and eliminate guess-work, we have unified interface contracts:
*   **NormalizedMarketContext**: Immutable market context contract that prevents state modification during pipeline iterations.
*   **SkillRouteOutcome**: Standardized return shape for all skill-related queries with dual dict and attribute interfaces to ensure backward-compatibility with legacy unit tests.
*   **ImmutableShield**: An un-bypassable security gate that validates all final proposals against physical portfolio limits. It cannot be overridden by self-improving python scripts.
