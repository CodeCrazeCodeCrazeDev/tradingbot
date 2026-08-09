# Research-to-Code Traceability Matrix (UCA-2026)

This document provides explicit mapping and traceability between AlphaAlgo's core production code structures and the 16 foundational research papers.

---

## 1. Traceability Mapping Directory

### **Paper 1: Active Inference (Friston, 2010)**
*   **Scientific Concept**: Variational Free Energy (VFE) surprise perception and Expected Free Energy (EFE) minimization policy sampling.
*   **Production File**: `trading_bot/core/csc/controller.py`
*   **Production Class**: `CognitiveSystemController`
*   **Code Elements**:
    - Method `process_market_observation()` starts the 12-step recursive active inference pipeline.
    - Method `_calculate_sensory_surprise()` calculates real-time observation deviation error representing variational surprise.
    - Method `_calculate_composite_confidence()` generates confidence vectors to represent precision updates.

---

### **Paper 2: Recursive Self-Evolving Agents (RSEA, arXiv:2606.28374)**
*   **Scientific Concept**: Monotone-Safe policy promotion constraints to prevent code divergence and strategic degradation.
*   **Production File**: `trading_bot/governance/evolution_gate.py`
*   **Production Class**: `EvolutionGate`
*   **Code Elements**:
    - Method `validate_evolution()` enforces the multi-metric threshold matching module, rejecting proposals with latency or drawdown regressions.

---

### **Paper 3: Causal World Model Induction (CWMI, arXiv:2605.22119)**
*   **Scientific Concept**: Interventional do-calculus futures and counterfactual structural causal simulation.
*   **Production File**: `trading_bot/world_model/causal_model.py`, `trading_bot/world_model/unified_world_model.py`
*   **Production Class**: `CausalWorldModel`, `UnifiedWorldModel`
*   **Code Elements**:
    - Method `simulate_counterfactual_futures()` evaluates interventional states $do(TRADE\_VOLUME = x)$ using functional topological regressions.

---

### **Paper 4: Information Folding (HIPIF, arXiv:2605.29303)**
*   **Scientific Concept**: High-level semantic compression of low-level execution logs to eliminate long-context strategic drift.
*   **Production File**: `trading_bot/core/csc/folding.py`
*   **Production Class**: `InformationFolder`
*   **Code Elements**:
    - Method `fold_history()` takes the raw active episodic context and folds it into relational summary nodes.

---

### **Paper 5: Skill-to-LoRA (S2L, arXiv:2606.16769)**
*   **Scientific Concept**: Compressing procedural prompt rules into low-rank parametric weight adapters dynamically loaded at runtime.
*   **Production File**: `trading_bot/core/csc/router.py`
*   **Production Class**: `SkillRouter`
*   **Code Elements**:
    - Method `route_task()` dynamically maps requested task signatures to Skill artifacts. If the skill is an `S2L` adapter, it returns the custom adapter ID `lora_hedging_v2`.

---

### **Paper 6: Continual Learning Bench (CL-Bench, arXiv:2606.05661)**
*   **Scientific Concept**: Forward Transfer Gain Metric tracking and Elastic Weight Consolidation (EWC) parameter retention.
*   **Production File**: `trading_bot/ml/continual/ewc_learning.py`
*   **Production Class**: `EWCContinualLearner`
*   **Code Elements**:
    - Method `calculate_fisher_matrix()` computes the diagonal of the Fisher Information Matrix to penalize changes to historically-critical parameter dimensions.

---

### **Paper 7: Agents-K1 (Agent-Native Knowledge Graphs, arXiv:2606.13669)**
*   **Scientific Concept**: Relational graph memory mapping entity-relationship triples over flat RAG vectors.
*   **Production File**: `trading_bot/core/hms/memory.py`
*   **Production Class**: `HierarchicalMemorySystem`
*   **Code Elements**:
    - Method `query_sage_graph_memory()` traverses claims, evidence, and provenances sequentially via graph topological pathfinders.

---

### **Paper 8: Reward Hacking Safeguards (DeepMind, 2024)**
*   **Scientific Concept**: Immutable portfolio limits and relative entropy bounds to prevent agent specification gaming.
*   **Production File**: `trading_bot/core/immutable_shield.py`
*   **Production Class**: `ImmutableShield`
*   **Code Elements**:
    - Method `validate_action()` evaluates final trade proposals against hard-coded physical limits (absolute max drawdowns, position size maximums).
