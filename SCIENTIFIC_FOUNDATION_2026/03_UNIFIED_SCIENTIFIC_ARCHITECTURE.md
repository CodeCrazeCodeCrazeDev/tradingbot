# Unified Scientific Architecture (AlphaAlgo UCA-2026)

This document specifies the unified scientific architecture synthesized from the 8 mandatory 2026 research papers for AlphaAlgo.

---

## Unified Cognitive Architecture (UCA-2026) Overview

AlphaAlgo integrates all 8 scientific principles into a single, cohesive 12-stage Recursive Active Inference Pipeline managed by the **CognitiveSystemController** ("One Brain").

```
                                 [ Market Observation ]
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 1: Perception & VFE    │ (Active Inference VFE Surprise)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 2: Evidence Retrieval │ (SAGE Graph + HMS AutoMem)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 3: HASP Guardrails     │ (Prescriptive Volatility Shield)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 4: DiscoLoop Recurrence│ (Discrete-Continuous Multi-Hop)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 5 & 6: NanoResearch    │ (Hypothesis Swarm & Simulation)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 7 & 8: Pivot / Refine  │ (AutoResearchClaw Strategy Selection)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 8.5 & 8.6: Risk & Gov  │ (Portfolio Risk + Human Governance)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 9: LogAct Proposal     │ (Shared-Log Event Bus)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 10: Verification Swarm │ (DeepWeb-Bench Calibrated Vectors)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 11: Immutable Shield   │ (Non-bypassable Safety Veto)
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │ Stage 12: Execution Consensus│ (LogAct Final Consensus & HMS Fold)
                            └──────────────────────────────┘
```

---

## Core Component Responsibilities & Guarantees

1. **Strategic Brain (CognitiveSystemController):**
   - Coordinates the 12-stage active inference loop.
   - Embeds `DiscoLoopCell` for recurrence loops.
   - Executes `AutoResearchClaw` pivot/refine logic on strategy failure.

2. **Hierarchical Memory System (HierarchicalMemorySystem):**
   - Manages four-tier memory structure (`AutoMem`).
   - Hosts `SAGE` graph-structured evidence store for relational queries.
   - Persists immutable `ResearchLedgerEntry` records.

3. **Routing & Guardrails (SkillRouter):**
   - Routes tasks across intelligence and execution layers.
   - Enforces `HASP` pre-emptive volatility overrides to prevent drawdowns.

4. **Shared-Log Backbone (UnifiedDecisionBus):**
   - Totally ordered event log (`LogAct`).
   - Enforces Byzantine voter consensus and fail-closed capital safety.

5. **Verification & Safety (VerificationSwarm & ImmutableShield):**
   - Multi-vector verification swarm computes calibrated confidence vectors (`DeepWeb-Bench`).
   - `ImmutableShield` acts as the non-bypassable safety veto for all trade proposals.
