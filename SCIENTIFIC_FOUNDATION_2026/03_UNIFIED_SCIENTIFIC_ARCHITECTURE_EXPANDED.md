# Unified Scientific Architecture (Expanded 2026)

## Executive Summary
This document specifies AlphaAlgo's canonical, single-authoritative cognitive trading architecture. It unifies all mandatory research principles (EKSFT, DiscoLoop, AutoMem, SAGE, NanoResearch, AutoResearchClaw, HASP, DeepWeb-Bench) into five core singletons without duplicating orchestrators, registries, or world models.

---

## High-Level Architectural Flow Diagram

```
                 [ Raw Market Data / Observation ]
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  CognitiveSystemController (CSC) │
               │     12-Stage Active Inference    │
               └─────────────────┬────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SkillRouter   │     │   Hierarchical  │     │   Multi-Agent   │
│ (HASP & S2L)    │     │  Memory (HMS)   │     │  Debate System  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │     Evolution Gate    │
                     │  (Monotone-Safe EKSFT)│
                     └───────────────────────┘
```

---

## Canonical Core Singletons

1. **`CognitiveSystemController` (`trading_bot/core/csc/controller.py`)**:
   - Single authoritative cognitive brain orchestrating the 12-stage Recursive Active Inference cycle.
   - Houses `DiscoLoopCell` for dual-state recurrence and `AutoResearchClaw` for closed-loop strategy pivoting and simulation.

2. **`SkillRouter` (`trading_bot/core/csc/router.py`)**:
   - Single authoritative capability router dispatching tasks to HASP program functions or S2L adapters with capability resolution.

3. **`HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`)**:
   - Single authoritative memory substrate holding Working, Episodic, Semantic, and SAGE dynamic graph memory tiers.

4. **`MultiAgentDebateSystem` (`trading_bot/agents/multi_agent_debate.py`)**:
   - Single authoritative multi-agent debate engine performing consensus verification and epistemic uncertainty estimation.

5. **`EvolutionGate` (`trading_bot/governance/evolution_gate.py`)**:
   - Single authoritative evolution gatekeeper enforcing Entropy-KL selective fine-tuning bounds on all model mutations.

---

## Conflict Resolution Matrix

| Conflict Area | Original Proposal / Legacy | Selected Scientific Solution | Justification |
| :--- | :--- | :--- | :--- |
| **Orchestration** | Multiple orchestrators across directories | Single `CognitiveSystemController` | Eliminates race conditions and fragmented decision paths. |
| **Component Registry** | Distributed registries | `UnifiedComponentRegistry` | Single source of truth for component lifecycle and dependency lookup. |
| **Safety Overrides** | Soft probabilistic checks | Hard `HASP` invariant program functions | Guarantees zero execution when safety or loss invariants are violated. |
| **Model Mutations** | Unconstrained fine-tuning | `EKSFT` Entropy-KL divergence bounds | Prevents catastrophic forgetting and uncalibrated epistemic confidence drift. |
