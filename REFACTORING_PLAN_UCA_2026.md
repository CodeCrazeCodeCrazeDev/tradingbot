# AlphaAlgo Scientific-First Refactoring Plan: UCA-2026 Transition

This plan details the systematic refactoring of the AlphaAlgo system into the Unified Cognitive Architecture (UCA-2026), grounded in verified scientific principles.

---

## 1. Objectives
1.  **Consolidate**: Eliminate the "Orchestration Explosion" by collapsing 80+ orchestrators into a single Cognitive System Controller (CSC).
2.  **Ground**: Eliminate the "Delusion Loop" by replacing Gaussian noise simulations with real market data and backtest oracles.
3.  **Enhance**: Implement scientifically validated mechanisms for Planning (Folding), Memory (Transactive), and Evolution (Monotone-Safe Gates).

---

## 2. Component Categorization

### 2.1 Keep (as-is or minimal update)
*   **Infrastructure**: `trading_bot/broker/`, `trading_bot/connectivity/` (Institutional connectivity is stable).
*   **Backbone**: `trading_bot/world_model/v2_core.py` (Transformer-Mamba backbone is scientifically sound).

### 2.2 Redesign (Architecture Change)
*   **Control Layer**: `trading_bot/core_agent_system/integrated_system.py` $\to$ **CSC (Cognitive System Controller)**.
*   **World Model**: `trading_bot/world_model/` $\to$ **GWM (Generative World Model)** with Causal Do-Calculus (CWMI).
*   **Evidence**: `trading_bot/core_agent_system/cds/evidence_graph.py` $\to$ **Causal Evidence Graph** (Agents-K1).

### 2.3 Merge (Consolidation)
*   **Orchestrators**: `SafeOrchestrator`, `MetaOrchestrator`, `MasterOrchestrator`, `AnalysisOrchestrator` $\to$ **CSC Workflow Engine**.
*   **Memory**: `WorkingMemory`, `EpisodicMemory`, `SemanticMemory` $\to$ **HMS (Hierarchical Memory System)** with WMR Loop and Transactive sharing.

### 2.4 Replace (Scientific Deficit)
*   **Simulators**: `self_play_loop.py` (Gaussian noise) $\to$ **High-Fidelity Replay Simulator** (Grounded in Tick Data).
*   **Planning**: `react_loop.py` (Infinite append) $\to$ **HIPIF Folding Operator**.
*   **Skills**: `SKILL.md` prompt injection $\to$ **Skill-to-LoRA (S2L) Router**.

### 2.5 Remove (Redundant/Legacy)
*   All fragmented `*orchestrator.py` files in `trading_bot/core/` and `trading_bot/core_agent_system/`.
*   Mock "Self-Coordinating" cores that lack grounding.

---

## 3. Implementation Roadmap

### Phase 1: The "One Brain" Consolidation
*   Migrate all orchestration logic to `trading_bot/core_agent_system/integrated_system.py`.
*   Establish the CSC as the single workflow manager.
*   *Scientific Justification*: *Effective Agents* (Anthropic Patterns), *Active Inference*.

### Phase 2: Grounding the World Model (Eliminating Delusion)
*   Replace `np.random.randn` in `self_play_loop.py` with calls to the `BacktestEngine` and real `MarketData`.
*   Implement Pearl's Do-Calculus in `world_model/causal_model.py`.
*   *Scientific Justification*: *CWMI* (Causal World Model Induction).

### Phase 3: Hierarchical Strategic Folding
*   Update `react_loop.py` to include a `FoldingOperator`.
*   Implement periodic context compression based on subgoal completion.
*   *Scientific Justification*: *HIPIF* (arXiv:2606.10507).

### Phase 4: Transactive Memory & Causal Evidence
*   Refactor `memory_system.py` to support population-level artifact sharing (MATM).
*   Enhance the `evidence_graph.py` to support multi-hop causal reasoning and provenance.
*   *Scientific Justification*: *MATM*, *Agents-K1*.

### Phase 5: The Evolution Gate
*   Complete the implementation in `recursive_improvement/` using the RSEA "Strict Keep-Better" logic.
*   Integrate a "Gain Metric" check against a stateless baseline.
*   *Scientific Justification*: *RSEA* (arXiv:2606.28374), *CL-Bench*.

---

## 4. Success Metrics
*   **Architectural Simplicity**: Number of orchestrators reduced from 80+ to 1.
*   **Grounding**: 100% of simulations anchored to real data/backtest oracles.
*   **Efficiency**: 60% reduction in average context-window tokens per task.
*   **Reliability**: Measurable reduction in "Strategic Drift" failures via HORIZON failure attribution.
