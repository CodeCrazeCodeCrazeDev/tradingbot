# Unified Scientific Architecture Specification: AlphaAlgo 2026

This document presents the unified scientific architecture of AlphaAlgo, synthesizing the strongest principles from all 8 mandatory arXiv papers (arXiv:2605.29303, arXiv:2607.00341, arXiv:2607.01224, arXiv:2605.12061, arXiv:2605.10813, arXiv:2605.20025, arXiv:2605.17734, arXiv:2605.21482) and extended literature into a single, cohesive, non-redundant cognitive trading system.

---

## Architectural Principles & Resolution of Contradictions

1. **Resolution of Prompting vs. Programmatic Control (HASP vs LLM Autonomy):**
   - *Contradiction:* LLMs require open-ended prompt reasoning, while safety requires hard bounds.
   - *Unified Solution:* Open-ended LLM argument generation is allowed during System-2 debate, but every candidate action must pass through HASP Program Functions (`SkillRouter.route_task`) before execution. Non-compliant actions trigger deterministic fallback logic (`ABSTAIN` or risk reduction).

2. **Resolution of Online Learning vs. Stability (EKSFT vs Continuous Evolution):**
   - *Contradiction:* Continuous online adaptation causes distribution sharpening and catastrophic forgetting.
   - *Unified Solution:* All policy modifications are subjected to EKSFT dynamic entropy and KL divergence masking. Updates are only committed if approved by the `EvolutionGate` under the RSEA monotone-safe protocol ($G \ge \tau_G$).

3. **Resolution of Symbolic Graph Memory vs. Vector Embeddings (SAGE vs Deep Learning):**
   - *Contradiction:* Pure vector RAG lacks explicit causal structure, while pure symbolic graphs struggle with continuous market features.
   - *Unified Solution:* DiscoLoop recurrence couples continuous hidden vectors $z_t$ with discrete symbol nodes $d_t$ in the `SAGEGraphMemory`. Multi-hop graph retrieval returns both structured relation edges and continuous embedding contexts.

---

## Canonical Subsystem Ownership & Single-Implementation Guarantees

AlphaAlgo strictly enforces single authoritative implementations across the entire codebase:

```
                  +-----------------------------------+
                  |   CognitiveSystemController (CSC) |
                  |   (Master Active Inference Brain) |
                  +-----------------+-----------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
+-------------------+     +-------------------+     +-------------------+
|    SkillRouter    |     | HierarchicalMemory|     | MultiAgentDebate  |
|  (HASP Guardrails |     |  System (HMS V6)  |     |  System (MADS)    |
| & System-1/2 S2L) |     | (SAGE Graph +     |     | (Bayesian         |
+---------+---------+     |  AutoMem Schema)  |     |  Consensus + ECE) |
          |               +---------+---------+     +---------+---------+
          |                         |                         |
          +-------------------------+-------------------------+
                                    |
                                    v
                        +-----------------------+
                        |     EvolutionGate     |
                        | (RSEA Monotone-Safe & |
                        |  EKSFT Masking Audit) |
                        +-----------------------+
```

1. **Authoritative Brain Controller:** `trading_bot.core.csc.controller.CognitiveSystemController`
2. **Authoritative Skill & Invariant Router:** `trading_bot.core.csc.router.SkillRouter`
3. **Authoritative Memory Substrate:** `trading_bot.core.hms.memory.HierarchicalMemorySystem` & `SAGEGraphMemory`
4. **Authoritative Decision & Debate Engine:** `trading_bot.agents.multi_agent_debate.MultiAgentDebateSystem`
5. **Authoritative Self-Improvement Gate:** `trading_bot.governance.evolution_gate.EvolutionGate`
6. **Authoritative Shared Event Backbone:** `trading_bot.core.unified_event_bus.UnifiedDecisionBus`

---

## End-to-End Decision & Self-Improvement Pipeline

```
[ Market Observation x_t ]
            |
            v
[ CSC Active Inference / DiscoLoop Recurrence ]
            |
            +--> System-1 Fast Path (< 5ms) --> [ Direct Execution / HASP Guardrail ]
            |
            +--> System-2 Deliberative Path --> [ MultiAgentDebateSystem ]
                                                        |
                                                        v
                                            [ Bayesian Consensus & ECE Calibration ]
                                                        |
                                                        v
                                            [ HASP Safety Guardrail Verification ]
                                                        |
                                                        +-- Approved --> [ Order Routing / Execution ]
                                                        |
                                                        +-- Rejected --> [ AutoResearchClaw Pivot/Refine ]
                                                                                   |
                                                                                   v
                                                                     [ EKSFT Masking & RSEA Gate Audit ]
                                                                                   |
                                                                                   v
                                                                     [ SAGE Graph & HMS AutoMem Update ]
```

---

## Scientific Guarantees
- **Zero Duplication:** No secondary orchestrators, Registries, or World Models are instantiated.
- **Deterministic Reproducibility:** All random seeds, graph traversals, and decision logs are bound to the deterministic execution mode.
- **Fail-Safe Governance:** `ABSTAIN` is supported as a first-class cognitive action when epistemic uncertainty exceeds calibrated thresholds.
