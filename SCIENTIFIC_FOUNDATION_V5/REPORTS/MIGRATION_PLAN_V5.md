# Implementation Roadmap: UCA V5 Transition

The migration from UCA-2026 (V4) to UCA V5 follows a 4-Phase execution strategy designed to minimize disruption to existing trading operations while maximizing scientific gain.

## Phase 1: The Backbone Upgrade (Shared Log & QKG)
*   **Goal**: Establish the transactional and contextual foundations.
*   **Deliverables**:
    1.  Replace `UnifiedDecisionBus` with **LogAct Shared Log** (`trading_bot/core/backbone/log.py`).
    2.  Implement **LogAct Voters** in the `VerificationSwarm`.
    3.  Upgrade `KnowledgeBase` to **Quantum Knowledge Graph (QKG)** architecture.
    4.  *Benchmark*: 100% state recovery from simulated failures.

## Phase 2: Cognitive Strategy (Insight & HIPIF V5)
*   **Goal**: Improve planning coherence and strategic depth.
*   **Deliverables**:
    1.  Implement `DeepInsightAgent` for **Strategic Sketching**.
    2.  Integrate **Insight-Aware Folding** into the `PlannerAgent`.
    3.  Implement **Strategic Tool Interleaving** (ReTool RL strategy).
    4.  *Benchmark*: $H^*$ (Intrinsic Horizon) increase of $>50\%$.

## Phase 3: Formal Verification & Risk (Proof Search)
*   **Goal**: Upgrade from heuristic to provable safety.
*   **Deliverables**:
    1.  Implement **Invariant Checking** engine in the `GovernanceShield`.
    2.  Integrate **AI-Driven Proof Search** (Tsoukalas et al. 2026) for strategy validation.
    3.  Define formal specs for Max Exposure and Drawdown invariants.
    4.  *Benchmark*: Zero-Violation rate on adversarial "Red-Team" tests.

## Phase 4: Metacognitive Evolution (Hyperagents & LSE)
*   **Goal**: Enable autonomous, safe self-optimization.
*   **Deliverables**:
    1.  Transition `PersistentCognitiveAgent` to **Hyperagent V5** (Zhang et al. 2026).
    2.  Implement `EvolutionGate V5` with **Held-out Selection (RSEA)**.
    3.  Deploy **Meta-Harness** for automated context-optimization.
    4.  *Benchmark*: "Gain Metric" $G > 0.15$ in live-learning simulation.

## Component Replacement Plan

| Legacy/V4 Component | V5 Replacement | Target Directory |
| :--- | :--- | :--- |
| `UnifiedDecisionBus` | `LogAct Backbone` | `trading_bot/core/` |
| `StaticKnowledgeBase`| `Quantum KG` | `trading_bot/knowledge/` |
| `HeuristicPlanner` | `InsightHIPIFPlanner`| `trading_bot/core/csc/` |
| `SafetyShield` | `FormalInvariantShield`| `trading_bot/governance/` |
| `AgentRegistry` | `SharedLogArtifactStore`| `trading_bot/core/hms/` |
| `SelfImprovementCore`| `HyperagentMetaKernel` | `trading_bot/core/csc/` |
