# Phase 3 — Unified Scientific Architecture Specification (UCA 2026)

This document specifies the unified scientific architecture of AlphaAlgo, synthesizing the 8 mandatory arXiv research papers into a single authoritative system without duplicate orchestrators or redundant subsystems.

---

## Unified Subsystem Architecture

```
                                  +---------------------------------------+
                                  |     Real-Time Intelligence Stream     |
                                  |    (DeepWeb-Bench: arXiv:2605.21482)  |
                                  +-------------------+-------------------+
                                                      |
                                                      v
+-----------------------------------------------------+-----------------------------------------------------+
|                                            Cognitive System Controller                                     |
|                                       (DiscoLoop Engine: arXiv:2607.00341)                                |
|                                                                                                           |
|   +------------------------------------+                         +------------------------------------+   |
|   |   Discrete Symbolic Reasoning      | <======= EM Loop ======>|  Continuous Latent State Model     |   |
|   |   (Action Selection Channel)       |                         |  (Order Book / Regime Vector)      |   |
|   +-----------------+------------------+                         +-----------------+------------------+   |
+---------------------|--------------------------------------------------------------|----------------------+
                      |                                                              |
                      v                                                              v
+---------------------+--------------------+                        +----------------+----------------------+
|            Skill Router                  |                        |    Hierarchical Memory System         |
|     (HASP Guardrails: arXiv:2605.17734)  |                        |  (AutoMem & SAGE: arXiv:2607.01224)  |
|                                          |                        |                                       |
|  - Pre-emption Rules (& pf_intervention) |                        |  - 4-Tier Salience-Decay Store        |
|  - Dynamic Risk Envelope Validation      |                        |  - Multi-Hop Subgraph Retrieval       |
+---------------------+--------------------+                        +----------------+----------------------+
                      |                                                              ^
                      v                                                              |
+---------------------+--------------------------------------------------------------+----------------------+
|                                        Multi-Agent Debate System                                          |
|                                   (NanoResearch Micro-Agents: arXiv:2605.10813)                            |
|                                                                                                           |
|  - Parallel Micro-Analysts                                                                                |
|  - Epistemic Variance Consensus Voting                                                                    |
+-----------------------------------------------------+-----------------------------------------------------+
                                                      |
                                                      v
                                  +-------------------+-------------------+
                                  |             Evolution Gate            |
                                  |   (EKSFT & AutoResearchClaw:          |
                                  |    arXiv:2605.29303, arXiv:2605.20025)|
                                  +---------------------------------------+
```

---

## Core Authoritative Singletons

1. **CognitiveSystemController (`trading_bot/core/csc/controller.py`)**:
   - Master orchestrator for the 12-step recursive active inference pipeline.
   - Integrates DiscoLoop dual-loop reasoning (`_run_discoloop_reasoning`) with continuous latent updates.

2. **SkillRouter (`trading_bot/core/csc/router.py`)**:
   - Authoritative router and safety execution gateway.
   - Enforces HASP pre-emption rules and risk envelope boundaries.

3. **HierarchicalMemorySystem (`trading_bot/core/hms/memory.py`)**:
   - Single authoritative memory store across episodic, semantic, working, and graph tiers.
   - Integrates AutoMem salience decay compaction and SAGE subgraph multi-hop reasoning.

4. **MultiAgentDebateSystem (`trading_bot/agents/multi_agent_debate.py`)**:
   - Single debate platform unifying Head AI, Risk, Alpha, Macro, and NanoResearch micro-agents.
   - Uses epistemic variance calculation for robust consensus.

5. **EvolutionGate (`trading_bot/governance/evolution_gate.py`)**:
   - Single governance and continuous self-improvement gate.
   - Integrates EKSFT RKHS fine-tuning and AutoResearchClaw AST sandboxed code mutations.

---

## Non-Duplication Directives
- **Zero Duplicate Orchestrators**: `CognitiveSystemController` is the sole cognitive orchestrator.
- **Zero Duplicate Registries**: `HierarchicalMemorySystem` is the sole memory registry.
- **Zero Duplicate World Models**: The latent dynamics encoder within `CognitiveSystemController` is the sole world model representation.
