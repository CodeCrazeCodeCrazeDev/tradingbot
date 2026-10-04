# Phase 3 — Unified Scientific Architecture Specification (2026)

This document specifies the unified scientific architecture of AlphaAlgo (UCA-2026), synthesizing the strongest principles from all 8 mandatory research papers and extended literature while resolving contradictions and removing redundant components.

---

## Architectural Principles & Strict Invariants

1. **One Authoritative Singleton per Subsystem**:
   - **One Orchestrator / Brain**: `CognitiveSystemController` (`trading_bot/core/csc/controller.py`)
   - **One Router**: `SkillRouter` (`trading_bot/core/csc/router.py`)
   - **One Memory Engine**: `HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`)
   - **One Debate Engine**: `MultiAgentDebateSystem` (`trading_bot/agents/multi_agent_debate.py`)
   - **One Evolution Gate**: `EvolutionGate` (`trading_bot/governance/evolution_gate.py`)
   - **One Shared Event Bus**: `UnifiedDecisionBus` (`trading_bot/core/unified_event_bus.py`)

2. **Zero Duplication**:
   - Duplicate orchestrators, registries, sidecar databases, or secondary world models are prohibited.
   - All legacy entry points wrap or delegate directly to the authoritative singletons.

3. **12-Stage Active Inference Loop**:
   - Stage 0: Perception & Observation Normalization
   - Stage 1: Sensory Surprise ($VFE$) Calculation
   - Stage 2: Evidence Retrieval from HMS
   - Stage 3: HASP Program Guardrail Interventions
   - Stage 4: DiscoLoop Recurrence & PCA Internalization
   - Stage 5: Competing Hypothesis Generation
   - Stage 6: Causal World Model Simulation
   - Stage 7: AutoResearchClaw Pivot/Refine Strategy Selection
   - Stage 8: Optimal Trade Proposal Synthesis
   - Stage 8.5: Canonical Portfolio Risk Boundary Check
   - Stage 8.6: Governance & Human Approval Gate Check
   - Stage 9: LogAct Shared Log Proposal (`TRADE_PROPOSAL`)
   - Stage 10: Verification Swarm & Falsification Gate
   - Stage 11: Immutable Shield Validation
   - Stage 12: Memory Folding, Ledger Persistence, and Consensus Execution (`TRADE_EXECUTION`)

---

## Scientific Resolution of Conflicts

### Conflict 1: Latency Overhead vs Byzantine Consensus
- **Conflict**: LogAct SMR consensus adds latency, whereas NanoResearch demands sub-millisecond execution.
- **Resolution**: Fast-path tiering. Non-shielded tasks (perception, internal feature lookup, graph retrieval) bypass SMR voting and execute synchronously in $<1\text{ms}$. Capital-moving actions (`TRADE_PROPOSAL`, `TRADE_EXECUTION`) are routed through the LogAct shared log with parallel asynchronous voter execution.

### Conflict 2: Generative Freedom vs Safety Invariants
- **Conflict**: AutoResearchClaw generates unconstrained strategy mutations; HASP requires static safety guarantees.
- **Resolution**: Hierarchical sandbox isolation. Strategy generation and hypothesis search occur within a sandboxed AST-evaluated space (`SecureASTVisitor`). Synthetic candidate plans must pass compiled HASP guardrails and DSR gates before entering the live proposal queue.

### Conflict 3: Memory Index Growth vs Retrieval Latency
- **Conflict**: SAGE graph memory grows exponentially; AutoMem requires bounded lookup complexity.
- **Resolution**: Periodic TD-weighted compaction. Edges with weights below threshold $\epsilon = 0.05$ are pruned during background compaction, maintaining node degree $d \le 16$.
