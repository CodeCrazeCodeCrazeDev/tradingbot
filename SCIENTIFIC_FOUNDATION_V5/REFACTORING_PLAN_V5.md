# Phase 6 — Refactoring Plan: AlphaAlgo UCA V5

This plan outlines the specific refactoring actions justified by the scientific literature synthesized in previous phases.

## 1. Components to KEEP (Foundation)
*   **Immutable Shield** (`trading_bot/core/immutable_shield.py`): Retain as the final "Voter" in the LogAct backbone.
*   **Hypothesis Generator** (`trading_bot/core/csc/hypothesis.py`): Retain multi-path generation but upgrade to support Causal World Models.

## 2. Components to REDESIGN (The "Consensus Brain")
*   **Cognitive System Controller** (`trading_bot/core/csc/controller.py`):
    *   **Action**: Implement the 12-step **Recursive Active Inference** pipeline.
    *   **Evidence**: Zhang et al. (Hyperagents), DiscoLoop (2607.00341).
*   **Hierarchical Memory System** (`trading_bot/core/hms/memory.py`):
    *   **Action**: Integrate **SAGE** feedback loops and **MSCL** surprise-driven replay.
    *   **Evidence**: SAGE (2605.12061), Scientific Amnesia (2606.21089).
*   **Unified Event Bus** (`trading_bot/core/unified_event_bus.py`):
    *   **Action**: Formalize as the **LogAct Shared-Log Backbone**.
    *   **Evidence**: LogAct (2604.07988).

## 3. Components to MERGE (Simplification)
*   **RiskEvaluators** $\to$ **UnifiedRiskEngine** (`trading_bot/core/risk/unified_risk_engine.py`):
    *   **Action**: Consolidate fragmented risk checks into a single **LogAct Voter**.
    *   **Evidence**: Bayesian DI, Strategic Decision Intelligence.

## 4. Components to REPLACE (Obsolescence)
*   **Static RAG** $\to$ **Graph-FM Retrieval**: Replace passive vector search with multi-hop SAGE retrieval.
*   **Heuristic Simulation** $\to$ **CWMI Simulation**: Replace linear world model propagation with Pearl's 'do-calculus' interventional inference.

## 5. Components to REMOVE (Cleanup)
*   **Fragmented Agents** (`trading_bot/agents/`): Remove redundant, uncoordinated agents in favor of the "One Brain" (CSC) + "Voter Swarm" model.
*   **Prompt-based Skills**: Remove hard-coded skills in favor of **HASP** (Executable Programs) and **S2L** (LoRAs).

---

## 6. Scientific Justification Matrix (Summary)

| Target Component | Scientific Evidence | Improvement |
| :--- | :--- | :--- |
| **CSC Loop** | DiscoLoop (arXiv:2607.00341) | Internalized multi-hop reasoning. |
| **HMS SAGE** | SAGE (arXiv:2605.12061) | Self-evolving agentic memory. |
| **LogAct Bus**| LogAct (arXiv:2604.07988) | Total ordering & transactional safety. |
| **Evolution Gate**| RSEA (arXiv:2606.28374) | Monotone-safe self-improvement. |
| **Folding Op** | HIPIF (arXiv:2606.10507) | Long-horizon context management. |
