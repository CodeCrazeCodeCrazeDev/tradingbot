# Refactoring Plan: AlphaAlgo UCA V5 Implementation (July 2026)

This document specifies the authoritative refactoring roadmap for the AlphaAlgo Unified Cognitive Architecture (UCA V5), justified by the 34-paper scientific synthesis.

---

## 1. Components to KEEP (Foundation)

| Component | Status | Scientific Justification |
| :--- | :--- | :--- |
| `trading_bot/core/immutable_shield.py` | Authority | Implements **Reward Hacking Safety** (Paper 26) and provides a non-bypassable governance singleton. |
| `trading_bot/core/unified_event_bus.py` | Backbone | Implements **LogAct** (Paper 1) shared-log consensus; essential for transactional reliability. |
| `trading_bot/core/hms/models.py` | Schema | Standardized evidence/knowledge objects necessary for **SAGE** and **QKG** serialization. |

---

## 2. Components to REDESIGN (Intelligence)

### 2.1 `trading_bot/core/csc/controller.py`
*   **Action**: Transform the `CognitiveSystemController` into a 12-step Recursive Active Inference pipeline.
*   **Scientific Evidence**: **Active Inference** (Paper 13), **DiscoLoop** (Paper 2), and **HIPIF** (Paper 7).
*   **Implementation**: Integrate multi-hop discrete-continuous reasoning and semantic information folding.

### 2.2 `trading_bot/core/hms/memory.py`
*   **Action**: Upgrade `HierarchicalMemorySystem` to support Tier 1 **SimpleMem** and Tier 3 **L2CL**.
*   **Scientific Evidence**: **SAGE** (Paper 3), **SimpleMem** (Paper 30), and **L2CL-Mem** (Paper 34).
*   **Implementation**: Implement gated linear attention for episodic tiers and meta-learning for schema evolution.

### 2.3 `trading_bot/world_model/causal_model.py`
*   **Action**: Upgrade the World Model from a simple SCM to an interventional **Causal Scratchpad**.
*   **Scientific Evidence**: **CWMI** (Paper 12) and **CausalEvolve** (Paper 31).
*   **Implementation**: Enable counterfactual "Abduction-Action-Prediction" loops and Pearl's 'do' operator.

---

## 3. Components to MERGE / CONSOLIDATE (Efficiency)

| Source Components | Target Component | Scientific Justification |
| :--- | :--- | :--- |
| `SkillRouter` + `IntegratedAgentSystem` | `trading_bot/core/csc/hyevo_engine.py` | **HyEvo** (Paper 15) and **HASP** (Paper 5). Unifies skill programs and workflow evolution. |
| `StrategyDiscovery` + `PolicyOptimization` | `trading_bot/learning/self_play_loop.py` | **GASP** (Paper 33) and **LSE** (Paper 19). Unifies self-play and context-adaptation. |

---

## 4. Components to REPLACE (Innovation)

| Old Component | New Component | Scientific Justification |
| :--- | :--- | :--- |
| Legacy `SelfImprovementEngine` | `ACE (Adversarial Coding Evolution)` | **ACE** (Paper 32). Replaces heuristic improvement with adversarial unit-test-driven self-debugging. |
| Static `KnowledgeBase` | `QKG (Quantum Knowledge Graph)` | **QKG** (Paper 6). Replaces globally-valid triplets with context-sensitive validity functions. |
| Fragmented `ReasoningEngine` | `DiscoLoop Core` | **DiscoLoop** (Paper 2). Standardizes multi-hop reasoning across all agents. |

---

## 5. Components to REMOVE (Legacy Debt)

*   **Redundant Agent Logic**: `trading_bot/agents2/`, `trading_bot/ai_core/`, and `trading_bot/ai_engineer/` will be archived. All intelligence is centralized in the CSC-V5 "One Brain" architecture per the **Scientific-First Refactoring Directive**.
*   **Stateless ReAct Loops**: Removed in favor of **Persistent Cognitive Agents** with information folding (HIPIF).

---

## 6. Validation Roadmap

Every refactored component must pass:
1.  **FIRE Benchmark**: Zero regression on 3,000 institutional financial reasoning questions.
2.  **CL-Bench Gain Metric**: Measured improvement in adaptation rate to new regimes.
3.  **Formal Invariant Check**: Provable safety of all risk-management logic.
