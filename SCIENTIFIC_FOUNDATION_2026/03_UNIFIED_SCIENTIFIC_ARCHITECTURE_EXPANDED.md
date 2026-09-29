# Phase 3: Unified Scientific Architecture Specification (2026)

This document specifies the synthesized, unified scientific architecture for AlphaAlgo. It integrates the strongest principles from all 8 mandatory arXiv research papers into one coherent, non-redundant system.

---

## Unified Architectural Layers

AlphaAlgo's scientific architecture is organized into five decoupled, non-overlapping layers operating through clean interfaces and thread-safe singletons:

```
+-----------------------------------------------------------------------------------+
| LAYER 1: COGNITIVE ORCHESTRATION & STRATEGIC REASONING                              |
| - CognitiveSystemController (CSC): 12-Stage Recursive Active Inference Pipeline     |
| - DiscoLoopCell: Discrete-Continuous Hidden State Recurrence                     |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| LAYER 2: MULTI-AGENT DEBATE & BAYESIAN CONSENSUS                                  |
| - MultiAgentDebateSystem: Macro / Tactical / Risk / Prosecutorial Debate            |
| - BayesianDecisionEngine: Scorecard-Weighted Posterior Synthesis                  |
| - FalsificationGate: Verification Swarm & Counterexample Testing                 |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| LAYER 3: CAPABILITY ROUTING & HASP PROGRAM GUARDRAILS                            |
| - SkillRouter: Task-to-Skill Artifact Mapping & Capability Resolution             |
| - HASPExecutor: Executable Program Function Invariant Harness                    |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| LAYER 4: HIERARCHICAL MEMORY SUBSTRATE & CAUSAL GRAPH                               |
| - HierarchicalMemorySystem (HMS): Working, Episodic, Semantic, Institutional Tiers|
| - SAGEGraphMemory: Multi-Hop Subgraph Retrieval & Autonomous Edge Evolution       |
| - AutoMem: Versioned Schema Migration & Integrity Checksumming                   |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| LAYER 5: GOVERNANCE, MONOTONE SAFETY & CALIBRATION                                |
| - EvolutionGate: Monotone-Safe Self-Evolution Gatekeeper (CL-Bench Gain)          |
| - EKSFT Compliance: Selective Token Entropy & KL-Drift Masking                    |
| - DeepWeb-Bench Calibration: Expected Calibration Error (ECE) Audit               |
+-----------------------------------------------------------------------------------+
```

---

## 12-Stage Recursive Active Inference Pipeline

The `CognitiveSystemController` (CSC) executes a 12-stage pipeline on every market observation:

1. **Stage 0: Normalization & Decision Identity** — Normalize observation input and assign deterministic UUID.
2. **Stage 1: Perception & VFE Estimation** — Calculate sensory surprise and update Variational Free Energy history.
3. **Stage 2: Evidence Retrieval** — Query `HierarchicalMemorySystem` (SAGE) for relevant historical evidence chains.
4. **Stage 3: Guardrail Pre-Emption** — Check HASP volatility guardrails via `SkillRouter`.
5. **Stage 4 & 4.5: Internalization & PCA Consultation** — Execute `DiscoLoopCell` discrete-continuous recurrence and consult persistent cognitive agents.
6. **Stage 5 & 6: Hypothesis Generation & Causal Simulation** — Generate competing reasoning branches and run causal scenario simulations.
7. **Stage 7: Pivot/Refine Control** — Evaluate simulation failure rates; pivot or refine strategy branches under `AutoResearchClaw` principles.
8. **Stage 8: Decision Synthesis** — Construct optimal trade proposal from winning branch.
9. **Stage 8.5 & 8.6: Portfolio Risk Boundary & Human Governance** — Enforce portfolio risk limits (`risk_engine`) and typed human governance approval (`governance_gate`).
10. **Stage 9: LogAct Proposal** — Dispatch `TRADE_PROPOSAL` to `UnifiedDecisionBus`.
11. **Stage 10: Verification Swarm & Bounded Refinement** — Run verification swarm on research ledger snapshot with bounded refinement pass.
12. **Stage 11 & 12: Immutable Shield & Execution Consensus** — Validate against `ImmutableShield`, persist ledger entry to HMS, and dispatch `TRADE_EXECUTION` for LogAct consensus.
