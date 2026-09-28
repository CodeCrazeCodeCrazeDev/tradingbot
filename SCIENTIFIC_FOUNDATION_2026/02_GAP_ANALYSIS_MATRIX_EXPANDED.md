# Phase 2: Expanded Gap Analysis Matrix (UCA-2026)

This document presents a comprehensive evaluation comparing every extracted scientific principle from the mandatory papers and extended literature against AlphaAlgo's current implementation state across all 25 core subsystems.

---

## 1. Subsystem Gap Analysis Matrix

| Research Paper | Extracted Scientific Principle | Subsystem Mapping | Current Status in AlphaAlgo | Detailed Implementation Gap Analysis | Target Refactoring Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EKSFT** (arXiv:2605.29303) | Entropy & KL Selective Token Masking | Fine-Tuning / Strategy Generator | **Partially Implemented** | Basic loss calculation exists, but KL divergence tracking against reference models during online learning loop was missing active token masking gates. | Integrate dual-model reference KL evaluator and dynamic token masking tensor in `trading_bot/core/eksft.py`. |
| **DiscoLoop** (arXiv:2607.00341) | Coupled Discrete-Continuous Recurrence Loop | Reasoning Engine (`CognitiveSystemController`) | **Partially Implemented** | Single continuous hidden state loop existed; lacked straight-through vector quantization discrete channel ($e_k$) realignment. | Upgrade `DiscoLoopCell` in `trading_bot/core/csc/controller.py` to couple discrete symbol embeddings with continuous latent states. |
| **AutoMem** (arXiv:2607.01224) | Metamemory Schema Evolution & File Actions | Memory System (`HierarchicalMemorySystem`) | **Partially Implemented** | Memory storage supported static schema tiers; lacked automated schema versioning ($V_t$) and action-utility policy updates. | Implement `optimize_metamemory()` in `trading_bot/core/hms/memory.py` with dynamic file schema migration and utility tracking. |
| **SAGE** (arXiv:2605.12061) | Structure-Aware Associative Graph Evolution | Knowledge Graph (`HMS`) | **Partially Implemented** | NetworkX causal graph existed, but reader-writer feedback loops lacked TD edge-weight update equations ($W_{t+1} = W_t + \gamma (R - W_t)$). | Integrate Bellman TD edge weight updates and automated node merging in `trading_bot/core/hms/memory.py`. |
| **NanoResearch** (arXiv:2605.10813) | Tri-Level Co-Evolution (Skills, Memory, Policy) | Strategy Engine (`ACPE`) | **Partially Implemented** | Skill router and memory existed in isolation; lacked unified tri-level optimization coupling skill rules with preference internalization. | Refactor `AdaptiveControlPolicyEngine` to enforce tri-level feedback loops between Skill Bank, Memory Ledger, and Policy. |
| **AutoResearchClaw** (arXiv:2605.20025) | Multi-Agent Debate & Pivot/Refine Loop | Multi-Agent System (`CSC`) | **Partially Implemented** | Multi-agent debate existed, but mid-flight execution failures triggered hard halts rather than strategy `Pivot`/`Refine` loops. | Implement `_pivot_refine_loop()` in `CognitiveSystemController` with failure-rate threshold triggers ($\tau_{pivot} > 0.40$). |
| **HASP** (arXiv:2605.17734) | Executable Skill Program Functions (PFs) | Guardrails / Risk Router | **Partially Implemented** | Volatility guardrail existed as natural language prompt advice; lacked deterministic Python Program Function interception logic. | Upgrade `SkillRouter` in `trading_bot/core/csc/router.py` with deterministic executable Python PFs returning override signals. |
| **DeepWeb-Bench** (arXiv:2605.21482) | Cross-Source Evidence & Calibration (ECE) | Verification Swarm | **Partially Implemented** | Verification swarm existed, but confidence vector sizing lacked Expected Calibration Error (ECE) adjustments and provenance checks. | Integrate source-provenance verification and ECE calibration scaling in `VerificationSwarm` and `ConfidenceVector`. |
| **LogAct** (arXiv:2601.04211) | Shared-Log Byzantine SMR Consensus | Decision Bus (`UnifiedDecisionBus`) | **Already Implemented** | Thread-safe LogAct backbone exists in `UnifiedDecisionBus` with $2f+1$ voter agreement and priority queues. | Enforce thread-safe `__new__` singleton initialization across all runtime reset invocations. |
| **Skill-to-LoRA** (arXiv:2602.08812) | Dynamic Behavioral Adapter Routing | Skill Router | **Partially Implemented** | Skill router selects rules; lacking low-rank dynamic weight adapter swapping for distinct market regimes. | Wire regime classification outputs directly to adapter routing masks in `SkillRouter`. |
| **DSR (Lopez de Prado)** | Deflated Sharpe Ratio Falsification | Evolution Gate | **Already Implemented** | DSR formula purging data snooping and multi-testing trial inflation implemented in `EvolutionGate`. | Ensure all proposed trading alphas pass DSR verification before production promotion. |

---

## 2. Synthesis of Deficiencies & Resolution Path

1. **Elimination of Duplication**: No new orchestrators, registries, or sidecar databases will be added. All enhancements will be applied directly to canonical singletons:
   - `CognitiveSystemController` (One Brain)
   - `UnifiedComponentRegistry` (One Registry)
   - `UnifiedDecisionBus` (One Bus)
   - `HierarchicalMemorySystem` (One Memory System)
   - `ImmutableShield` (One Risk Shield)

2. **Strict Invariant Verification**: All refactored singletons must maintain 100% backward compatibility while embedding the exact mathematical formulations defined in Phase 1.

---

This completes Phase 2: Expanded Gap Analysis Matrix.
