# ARCHITECTURE_GAP_MATRIX.md

This document defines the comprehensive architecture gap matrix for AlphaAlgo, contrasting target scientific paper principles against current production implementations, and defining the path to superiority.

---

## 1. Comprehensive Gap Matrix

| Component | Target Scientific Principle | Paper Reference | Status in Current Codebase | Risk of Existing State | Path to Superiority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Learning Pipeline** | Entropy-KL selective token masking to preserve exploration capacity and prevent distribution sharpening. | **EKSFT** (arXiv:2605.29303) | **Missing entirely**. Update updates are applied without selective masking of high-entropy states. | Overfitting to noisy market sequences; policy collapse under regime shifts. | Add dynamic Entropy and KL divergence filters inside the ACPE training step. |
| **Reasoning Core** | Coupled discrete-continuous recurrence loop state tracking. | **DiscoLoop** (arXiv:2607.00341) | **Partially implemented**. Basic loop state exists, but lacks explicit coupled discrete-continuous state trackers. | logical fragmentation in multi-hop causal reasoning; localized representation errors. | Implement discrete subgoal trackers alongside continuous latent dynamics inside CSC. |
| **Memory System** | Metamemory schema utility optimization and sequential database migrations. | **AutoMem** (arXiv:2607.01224) | **Partially implemented**. Stubbed metamemory loop exists, but lacks actual sequential schema versioning and version increment. | Memory bloat; semantic retrieval degradation; lack of schema auditability. | Solidify schema version increment (current_version += 0.1) and entity compaction under feedback. |
| **Knowledge Engine** | Self-evolving associative graph memory driven by outcome utility feedback. | **SAGE** (arXiv:2605.12061) | **Partially implemented**. Vector DB and basic graph structure exist, but lack online edge weight updates. | Context fragmentation; semantic drift; inability to track non-stationary relationships. | Integrate online SAGE weight updates based on trade outcome utility feedback. |
| **Personalization** | Co-evolution of skill banks, experience modules, and preference policies. | **NanoResearch** (arXiv:2605.10813) | **Missing entirely**. Hand-coded heuristic prompts. | Inability to adapt to customized institutional risk profiles. | Set up localized skill bank updates governed by direct preference optimization (DPO). |
| **Self-Healing** | Pivot/Refine decision loop and multi-agent critique-refinement debate. | **AutoResearchClaw** (arXiv:2605.20025) | **Partially implemented**. Basic debate loop exists but has scoping and NameErrors under stress. | Failure under API crashes, slippage, or unexpected market states. | Harden the Pivot/Refine state tracking loop in `CognitiveSystemController` with exception isolation. |
| **Risk Guardrails** | Deterministic Program Functions intercepting agent states. | **HASP** (arXiv:2605.17734) | **Partially implemented**. Risk metrics exist, but lack flat and nested Python triggers acting as hard boundaries. | Conversational instruction drift; agent bypassing soft risk checks. | Implement HASP non-bypassable executable triggers in the `SkillRouter` and `ImmutableShield`. |
| **Evaluation** | Multi-dimensional calibration (ECE) and derivation evaluation. | **DeepWeb-Bench** (arXiv:2605.21482) | **Partially implemented**. Simple profit/loss testing, lacking rigorous confidence calibration audits. | High trade execution under LLM overconfidence; heavy capital losses under market drift. | Integrate ECE calculation and calibration interval checks into the Evolution Gate. |

---

## 2. Analysis of the "Delusion Loop" and GAO-V5 Regressions

The codebase audit reveals a critical architectural hazard: **Gaussian Noise Optimization**.
- **The Finding**: In `trading_bot/core_agent_system/self_play_loop.py`, market price paths under RL simulated self-play were generated using ungrounded random walks (`np.random.randn()`).
- **The Impact**: This bypasses reality grounding. The agent's self-improvement engine optimizes policy parameters against purely random walks, creating the "illusion of learning."
- **The Path to Superiority**: Ground all self-play simulations inside the `self_play_loop` using historical tick-data ingested directly from the database, using Geometric Brownian Motion (GBM) with calibrated drift/volatility parameters ONLY as a secondary fallback.

---

## 3. Subsystem Duplication Cleanup

To maintain the **One Authoritative Implementation** rule, the following duplication cleanup plan is enforced:
1. **Orchestrators**: Decommission all disjoint orchestrators (including legacy agents and redundant swarms) and route all cognitive workflow planning through the `CognitiveSystemController` (CSC).
2. **Registries**: Deprecate all redundant registry classes and route component lookup exclusively through `UnifiedComponentRegistry`.
3. **World Models**: Consolidate JEPA-based and latent dynamics models into the single authoritative `AgenticPlanningWorldModel` inside `trading_bot/world_model/latent_dynamics.py`.
