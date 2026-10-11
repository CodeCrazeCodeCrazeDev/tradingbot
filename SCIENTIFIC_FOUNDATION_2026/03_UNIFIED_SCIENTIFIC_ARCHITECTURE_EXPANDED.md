# Phase 3: Unified Scientific Architecture Specification (UCA V6 / 2026)

This document provides the unified, superior architectural design synthesizing the eight mandatory research references and extended literature into a single authoritative design for AlphaAlgo UCA V6.

---

## 1. Executive Synthesis & Architectural Hierarchy

Rather than treating research papers as disconnected modules or superficial citations, AlphaAlgo UCA V6 unifies all scientific principles into a 6-layer cognitive hierarchy:

```
[ LAYER 6: MONOTONE SELF-EVOLUTION ]  <-- EvolutionGate (EKSFT + CL-Bench + Red-Teaming)
               │
[ LAYER 5: GOVERNANCE & CONSENSUS ]   <-- UnifiedDecisionBus (LogAct Shared-Log) + ImmutableShield
               │
[ LAYER 4: MULTI-AGENT REASONING ]   <-- MultiAgentDebateSystem (NanoResearch + Bayesian Engine)
               │
[ LAYER 3: LATENT ROUTING & HASP ]   <-- SkillRouter (S2L + Executable PFs)
               │
[ LAYER 2: RECURSIVE BRAIN / DISCO ] <-- CognitiveSystemController & CognitiveBrain (DiscoLoop + VFE)
               │
[ LAYER 1: DYNAMIC GRAPH MEMORY ]    <-- HierarchicalMemorySystem (SAGE Graph + AutoMem)
```

---

## 2. Integrated Principles & Contradiction Resolution

1. **Active Inference VFE vs. Passive LLM Inference**:
   - *Resolution*: Monolithic passive LLM calls are replaced by 12-stage active inference loops (`CognitiveSystemController`). Decisions are pruned when Variational Free Energy surprise exceeds the adaptive threshold $\mathcal{F}_{thresh}$.

2. **Textual Guardrails vs. Executable Program Functions (HASP)**:
   - *Resolution*: Advisory prompts are demoted to Layer 4. Layer 3 enforces hard, non-bypassable executable `ProgramFunctions` (PFs) that intercept execution under high volatility ($\sigma > 0.30$).

3. **Flat RAG vs. Dynamic Hebbian Graph Memory (SAGE)**:
   - *Resolution*: Flat vector lookups are replaced by `SAGEGraphMemory`. Graph edges evolve via Hebbian feedback ($w = w + \eta \Delta$) and auto-prune when utility drops below $0.10$.

4. **SFT Overfitting vs. Epistemic Selective Fine-Tuning (EKSFT)**:
   - *Resolution*: Policy updates in `EvolutionGate` require entropy retention ($\tau_H \ge 0.8$) and bounded KL drift ($\tau_{KL} \le 0.5$) to preserve policy exploration capabilities.

5. **Point Predictions vs. Conformal Prediction & Hawkes Order Flow**:
   - *Resolution*: Trade confidence is bounded using scipy non-parametric split conformal prediction intervals and Hawkes order flow intensity estimations.

---

## 3. Subsystem Authority & Canonical Guarantees

AlphaAlgo enforces strict architectural singletons to guarantee system integrity:
- **One Controller**: `CognitiveSystemController` in `trading_bot/core/csc/controller.py`.
- **One Memory Substrate**: `HierarchicalMemorySystem` in `trading_bot/core/hms/memory.py`.
- **One Decision Bus**: `UnifiedDecisionBus` in `trading_bot/core/unified_event_bus.py`.
- **One Router**: `SkillRouter` in `trading_bot/core/csc/router.py`.
- **One Debate Engine**: `MultiAgentDebateSystem` in `trading_bot/agents/multi_agent_debate.py`.
- **One Evolution Gate**: `EvolutionGate` in `trading_bot/governance/evolution_gate.py`.
