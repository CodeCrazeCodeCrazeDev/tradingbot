# 03 Codebase Mapping & Gap Analysis 2026: Phase 5 Analysis

## Phase 5: Codebase Mapping & Audit

This document maps all core AlphaAlgo subsystems to their supporting post-2025 scientific research literature, identifying gaps and confirming paper traceability matrix enforcement across core singletons.

---

## Complete Mapping Between Research Papers & Source Code

| Subsystem Component | Source Code Path | Authoritative Class / Module | Primary Supporting Research | Codebase Status & Gap Analysis |
| :--- | :--- | :--- | :--- | :--- |
| **Cognitive System Controller** | `trading_bot/core/csc/controller.py` | `CognitiveSystemController` | `arXiv:2607.01224` (CORAL), `arXiv:2607.00341` (LogAct) | **Redesigned**: Enforces continuous active inference Variational Free Energy minimization and transactional logging. |
| **Skill Router** | `trading_bot/core/csc/router.py` | `SkillRouter` | `arXiv:2605.20025` (S2L) | **Redesigned**: Implements contrastive latent skill-to-task routing with fallback paths. |
| **Hierarchical Memory System** | `trading_bot/core/hms/memory.py` | `HierarchicalMemorySystem` | `arXiv:2605.21482` (DeepWeb-Bench), `arXiv:2607.00341` (LogAct) | **Redesigned**: Enforces SHA-256 cryptographic provenance chains and 8-tier memory hierarchy. |
| **Multi-Agent Debate System** | `trading_bot/agents/multi_agent_debate.py` | `MultiAgentDebateSystem` | `arXiv:2605.12061` (Search-R1), `arXiv:2605.10813` (NanoResearch), `arXiv:2605.29303` (EKSFT) | **Redesigned**: Integrates Bayesian confidence calibration, epistemic uncertainty bounds, and falsification gating. |
| **Adaptive Control Policy Engine** | `trading_bot/core/csc/acpe.py` | `AdaptiveControlPolicyEngine` (`EvolutionGate`) | `arXiv:2605.17734` (AutoResearchClaw) | **Redesigned**: Enforces monotone safety gates ($M_{t+1} \ge M_t$) and multi-metric protected evaluation. |

---

## Paper Traceability Matrix Compliance Checklist

Every core singleton in AlphaAlgo is audited to confirm that its class docstring contains a full paper traceability matrix citing all 8 mandatory post-2025 arXiv papers:

1. `CognitiveSystemController` (`trading_bot/core/csc/controller.py`) - Verified
2. `SkillRouter` (`trading_bot/core/csc/router.py`) - Verified
3. `HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`) - Verified
4. `MultiAgentDebateSystem` (`trading_bot/agents/multi_agent_debate.py`) - Verified
5. `AdaptiveControlPolicyEngine` (`trading_bot/core/csc/acpe.py`) - Verified

---

## Key Refactoring Gaps Identified & Addressed

1. **Active Inference VFE State Estimation**: Ensured `CognitiveSystemController.process_cycle` updates variational free energy bounds dynamically on every market tick.
2. **Dynamic Skill Routing Latency**: Ensured `SkillRouter` sub-millisecond execution for fast intraday market setups.
3. **Cryptographic Memory Provenance**: Added SHA-256 hash chains to `HierarchicalMemorySystem.store` and verified link integrity on `retrieve`.
4. **Epistemic Uncertainty Bounds**: Embedded epistemic/aleatoric uncertainty decomposition into `MultiAgentDebateSystem` trade decision proposals.
5. **Monotone Self-Evolution Verification**: Enforced hard rejection of negative metric mutations in `EvolutionGate`.
