# ALPHAALGO UCA-2026 REFACTORING PLAN (PHASE 6)

This document provides the final, scientifically-grounded blueprint for refactoring AlphaAlgo into the Unified Cognitive Architecture (UCA-2026).

---

## 1. COMPONENT CATEGORIZATION & SCIENTIFIC JUSTIFICATION

### 1.1 KEEP (Preserve Core Strengths)
*   **Module**: `trading_bot/broker/`, `trading_bot/connectivity/`
    *   **Reason**: Connectivity to institutional FIX/REST APIs is stable and performance-optimized.
*   **Module**: `trading_bot/world_model/v2_core.py`
    *   **Reason**: The Transformer-Mamba hybrid backbone provides the required efficiency for modeling long sequences.
    *   **Scientific Evidence**: Foundational architecture for SSM-based latent dynamics.

### 1.2 REDESIGN (Architectural Shift)
*   **Target**: `trading_bot/core_agent_system/integrated_system.py` $\to$ **CSC (Cognitive System Controller)**
    *   **Scientific Justification**: *Effective Agents* (Anthropic), *Active Inference*. Consolidates the "One Brain" to prevent functional collapse.
*   **Target**: `trading_bot/world_model/` $\to$ **GWM (Generative World Model)**
    *   **Scientific Justification**: *CWMI (Causal World Model Induction)*. Shifts from correlational forecasting to counterfactual reasoning ($do(X)$).
*   **Target**: `trading_bot/core_agent_system/cds/evidence_graph.py` $\to$ **Causal Evidence Graph**
    *   **Scientific Justification**: *Agents-K1 (Shanghai AI Lab)*. Moves from passive RAG to agent-native graph orchestration.

### 1.3 MERGE (Consolidation)
*   **Target**: 80+ redundant `*orchestrator.py` files $\to$ **CSC Workflow Engine**
    *   **Scientific Justification**: *Effective Agents*. Reduces systemic entropy and simplifies the "Strategic Horizon."
*   **Target**: `WorkingMemory`, `EpisodicMemory`, `SemanticMemory` $\to$ **HMS (Hierarchical Memory System)**
    *   **Scientific Justification**: *Memory for Autonomous LLM Agents (Survey)*, *MATM*. Implements the formal WMR (Write-Manage-Read) loop.

### 1.4 REPLACE (Scientific Deficit)
*   **Target**: `self_play_loop.py` (Gaussian noise) $\to$ **High-Fidelity Replay Simulator**
    *   **Scientific Justification**: *Grounded Intelligence Principles*. Eliminates the "Delusion Loop" by anchoring simulations to real tick data and backtest oracles.
*   **Target**: `react_loop.py` (Infinite append) $\to$ **HIPIF Folding Operator**
    *   **Scientific Justification**: *HIPIF (arXiv:2606.10507)*. Solves long-context strategic drift via information folding.
*   **Target**: `SKILL.md` (Prompt injection) $\to$ **Skill-to-LoRA (S2L) Router**
    *   **Scientific Justification**: *Skill-to-LoRA (arXiv:2606.16769)*. Internalizes behaviors into weights for token efficiency and stability.

### 1.5 REMOVE (Redundant/Legacy)
*   **Modules**: Mock self-coordination cores, placeholder improvements, and every orchestrator moved to `_archive/`.

---

## 2. IMPLEMENTATION SEQUENCE (PHASE 7)

1.  **CSC Core Construction**: Establish the `CognitiveSystemController` in `trading_bot/core/csc/`.
2.  **Orchestrator Collapse**: Batch-migrate and delete redundant orchestrators.
3.  **HIPIF Integration**: Refactor the `ReActLoop` state management to include the `FoldingOperator`.
4.  **World Model Grounding**: Re-wire simulation components to use `backtesting/backtest_engine.py` and real `MarketData`.
5.  **Evolution Gate**: Implement the monotone-safe `EvolutionGate` in `trading_bot/governance/`.

---

## 3. VALIDATION GATES (PHASE 8)

*   **Gain Metric Check**: Every self-improvement must show a $> \epsilon$ improvement over a stateless baseline.
*   **Horizon Breakdown Attribution**: Use HORIZON to verify the strategic depth has improved from $s \approx 10$ to $s > 50$.
*   **Architecture Fitness**: Verify that exactly ONE instance of the CSC and Unified Registry exists.
