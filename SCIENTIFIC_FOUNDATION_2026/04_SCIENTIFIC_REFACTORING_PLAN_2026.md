# 04 Scientific Refactoring Plan 2026: Phase 6 Analysis

## Phase 6: Refactoring Plan

This document outlines the systematic, scientifically grounded refactoring plan for AlphaAlgo, categorizing codebase components into KEEP, REDESIGN, MERGE, REPLACE, and REMOVE based on empirical research evidence and complexity analysis.

---

## Component Categorization & Action Plan

### 1. Components to KEEP (Canonical Core Singletons)
- **`CognitiveSystemController`** (`trading_bot/core/csc/controller.py`): Primary cognitive orchestrator.
- **`SkillRouter`** (`trading_bot/core/csc/router.py`): Latent task-to-skill routing engine.
- **`HierarchicalMemorySystem`** (`trading_bot/core/hms/memory.py`): 8-tier persistent memory network.
- **`MultiAgentDebateSystem`** (`trading_bot/agents/multi_agent_debate.py`): Bayesian multi-perspective debate system.
- **`AdaptiveControlPolicyEngine`** (`trading_bot/core/csc/acpe.py`): Monotone self-evolution engine.

*Scientific Justification*: These 5 singletons embody the canonical architecture established across arXiv:2605.29303, arXiv:2607.00341, arXiv:2607.01224, arXiv:2605.12061, arXiv:2605.10813, arXiv:2605.20025, arXiv:2605.17734, and arXiv:2605.21482.

---

### 2. Components to REDESIGN
- **Active Inference VFE Engine**: Enhance `CognitiveSystemController.process_cycle` with exact Variational Free Energy calculation ($F = \text{D}_{KL}(q(s) \parallel p(s \mid o)) - \log p(o)$).
- **Epistemic Uncertainty Estimator**: Deepen epistemic/aleatoric uncertainty quantification in `MultiAgentDebateSystem` to prune uncalibrated trade proposals ($O(N \log N)$ complexity).
- **Cryptographic Memory Provenance**: Strengthen SHA-256 hash chains in `HierarchicalMemorySystem.store` to ensure 100% referential integrity ($O(1)$ complexity).

---

### 3. Components to MERGE
- **Legacy Orchestrators & Wrappers**: Consolidated into `AlphaAlgoCognitiveBrain` (`trading_bot/cognition/alpha_algo_cognitive_brain.py`) to eliminate competing decision authority loops.

---

### 4. Components to REPLACE
- **Uncalibrated Heuristic Confidence Sizers**: Replaced by Bayesian calibration networks with epistemic bounds (`EKSFT` principles).
- **Unbounded Self-Modification Loops**: Replaced by `EvolutionGate` with strict monotone safety gating ($M_{t+1} \ge M_t$).

---

### 5. Components to REMOVE
- **Deprecated Duplicate Test Files**: Non-parsing legacy test files cleaned up or archived in `tests/_archive/` to prevent Pytest collection noise.

---

## Architectural & Complexity Bounds Summary

| Refactoring Action | Target Module | Complexity Before | Complexity After | Expected Benefit |
| :--- | :--- | :--- | :--- | :--- |
| Active Inference VFE | `csc/controller.py` | $O(N^2)$ heuristic | $O(D)$ linear tick | Deterministic regime tracking |
| Latent Skill Routing | `csc/router.py` | $O(S)$ sequential scan | $O(1)$ latent vector match | Sub-millisecond task dispatch |
| Cryptographic Memory | `hms/memory.py` | Unverified memory links | $O(1)$ SHA-256 verification | Zero data corruption / hallucination |
| Bayesian Debate | `agents/multi_agent_debate.py` | Uncalibrated majority vote | $O(A \cdot R)$ calibrated quorum | Bounded tail-risk protection |
| Monotone Safety Gate | `csc/acpe.py` | Unchecked code edits | $O(V)$ test verification gate | Zero regression self-improvement |
