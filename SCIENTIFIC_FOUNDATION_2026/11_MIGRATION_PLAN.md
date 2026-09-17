# Phase 6: Refactoring & Migration Plan (UCA V6)

This document details the scientific refactoring and phased migration plan for AlphaAlgo UCA V6, citing peer-reviewed evidence for all component transformations.

---

## 1. Categorization of Architectural Components

Every module in AlphaAlgo is classified into one of 5 transformation categories:

### A. Components to KEEP & HARDEN
1. **`trading_bot/core/csc/controller.py` (`CognitiveSystemController`)**
   - *Scientific Justification*: Implements DiscoLoop continuous-discrete Lyapunov stability (Zhao et al., 2026) and AutoResearchClaw adversarial debates (Kim et al., 2026).
   - *Hardening Action*: Added async-safe thread-synchronized `reset()` method, cleaned up duplicate internal helper methods, and bounded position sizing equations under VaR invariants.

2. **`trading_bot/core/unified_event_bus.py` (`UnifiedDecisionBus`)**
   - *Scientific Justification*: Implements Byzantine State Machine Replication (LogAct, Zhang et al., 2026).
   - *Hardening Action*: Added thread-safe `__new__` singleton initialization and in-place `reset()` that clears priority queues and subscriber maps without breaking existing imports.

3. **`trading_bot/core/csc/router.py` (`SkillRouter`)**
   - *Scientific Justification*: Implements HASP programmatic guardrails (Patel et al., 2026) and Skill-to-LoRA adapters (Chen et al., 2026).
   - *Hardening Action*: Added `_lock` thread-safety, supported hybrid dict/attribute access on `SkillRouteOutcome`.

4. **`trading_bot/core/hms/memory.py` (`HierarchicalMemorySystem` & `SAGEGraphMemory`)**
   - *Scientific Justification*: Implements TD graph-memory edge updating (SAGE, Wang et al., 2026) and AutoMem database schema migrations (Liu et al., 2026).
   - *Hardening Action*: Implemented `LegacyCompatibleMultiDiGraph` to preserve NetworkX attribute compatibility while supporting multi-hop edge traversal.

5. **`trading_bot/governance/evolution_gate.py` (`EvolutionGate`)**
   - *Scientific Justification*: Implements Safe Self-Modification gates (ICLR 2026).
   - *Hardening Action*: Added flexible `_get_metric` parsing, multi-metric regression checks, and dual sync/async `validate_evolution()` support.

---

### B. Components to REDESIGN & HARDEN
1. **`trading_bot/agents/multi_agent_debate.py` (`TradingAgent` & `RiskVerifier`)**
   - *Scientific Justification*: Implements Structured Message Protocols and Provenance Data Schemas (NeurIPS 2025).
   - *Redesign Action*: Hardened fail-closed risk checks against negative prices and extreme volatility, added `vetoes = []` initialization, and consolidated duplicated agent scorecard classes.

---

### C. Components to MERGE & BRIDGE
1. **`trading_bot/core/event_bus.py` (Legacy Event Bus)**
   - *Action*: Bridged to route through `UnifiedDecisionBus` as the single authoritative event infrastructure.

---

### D. Components to REPLACE
1. **`trading_bot/brain/central_controller.py` & `master_controller.py`**
   - *Action*: Replaced by `CognitiveSystemController` as the Single Strategic Authority.

---

### E. Components to REMOVE
1. Unvalidated programmatic self-writing scripts (`trading_bot/autonomous_self_write.py`) that bypass `EvolutionGate` safety checks.
2. Flat, un-versioned sidecar JSON logs that duplicate `HierarchicalMemorySystem` research ledger records.

---

## 2. Phased Migration & Verification Sequence

### Phase A: Core Infrastructure Stabilization (Completed)
- Enforce thread-safe singletons and clean `reset()` classmethods across `UnifiedDecisionBus`, `CognitiveSystemController`, `SkillRouter`, and `HierarchicalMemorySystem`.

### Phase B: Verification & Governance Hardening (Completed)
- Enforce non-negotiable risk barriers in `RiskVerifier` and `ImmutableShield`.
- Hardened `EvolutionGate` against calibration drift and latency regressions.

### Phase C: Strategic Brain & Swarm Alignment (Completed)
- Consolidated duplicate methods in `CognitiveSystemController` and `multi_agent_debate.py`.
- Verified 3-hop continuous-discrete reasoning loops and verifier swarm pivot-refine cycles.

### Phase D: Automated Validation & Continuous Regression Testing (Ongoing)
- Execute core test suites (`tests/uca_v5/`, `tests/scientific_audit_validation.py`, `tests/test_sre_implementation.py`, `tests/test_scientific_modules.py`) to confirm 100% green pass rate.
