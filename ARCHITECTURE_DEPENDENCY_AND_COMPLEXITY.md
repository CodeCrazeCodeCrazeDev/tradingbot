# Architecture Verification Gate: Dependency, Migration & Complexity

This document details the system dependencies, migration strategy, and computational complexity of the UCA-2026.

---

## 1. Unified Dependency Graph (Conceptual)

### Ownership & Startup Order
1.  **Level 0: Governance & Registry** (Immutable Shield, Unified Registry)
    *   *Startup*: First. Blocks all other components until active.
2.  **Level 1: Foundation Services** (Event Bus, Persistence/HMS)
    *   *Startup*: Second. Provides the communication and data substrate.
3.  **Level 2: Generative World Model (GWM)** (SCM, Simulator)
    *   *Startup*: Third. Requires data stream from Level 1.
4.  **Level 3: Cognitive System Controller (CSC)** (Brain, HIPIF Planner)
    *   *Startup*: Fourth. The central orchestrator.
5.  **Level 4: Persistent Cognitive Agents (PCAs)** (Macro, Risk, Alpha)
    *   *Startup*: Fifth. Managed by Level 3.
6.  **Level 5: Evolution Engine** (RSEA Gate)
    *   *Startup*: Last. Monitors Level 4 for improvement opportunities.

### Circular Dependency Risks
*   *Memory vs. World Model*: Resolved by World Model providing *predictions* to Memory, while Memory provides *observations* to World Model.
*   *Agent vs. Planner*: Resolved by Agent owning *intent*, while Planner (owned by CSC) provides *procedural decomposition*.

---

## 2. Migration Matrix

| Legacy Component | Path | Decision | Technical Justification | Rollback Plan |
| :--- | :--- | :--- | :--- | :--- |
| `SafeOrchestrator` | `trading_bot/core/` | **Archive** | Functionality absorbed by CSC Controller. | Restore from git; map CSC signals back. |
| `MasterOrchestrator` | `trading_bot/core_agent_system/` | **Merge** | Core delegation logic moved to CSC. | Maintain legacy API wrapper temporarily. |
| `ReActLoop` | `trading_bot/core_agent_system/` | **Rewrite** | Needs HIPIF Folding integration. | Keep `legacy_react.py` for parallel testing. |
| `SelfPlayLoop` | `trading_bot/core_agent_system/` | **Rewrite** | Grounding in backtest oracles required. | Keep noise-based version for unit test mocking. |
| `EpisodicMemory` | `trading_bot/core_agent_system/` | **Merge** | Integrates into HMS WMR loop. | Keep SQLite schema intact for data migration. |
| `QuantumForecaster` | `trading_bot/world_model/` | **Delete** | Unverified correlational logic. | None (not used in production). |
| `SpecializedPlanners` | `trading_bot/core_agent_system/` | **Merge** | Absorbed by HIPIF subgoal tree. | Restore individual planner classes. |
| `Registry` | `trading_bot/registry.py` | **Rewrite** | Needs singleton unified registry. | Keep as legacy adapter. |

---

## 3. Complexity Analysis

| Metric | Target Estimate | Scaling Behavior | Bottleneck |
| :--- | :--- | :--- | :--- |
| **Inference Latency** | 200ms - 800ms | $\mathcal{O}(1)$ (fixed model pass) | LLM provider response time. |
| **Memory Usage** | 8GB - 32GB | $\mathcal{O}(N)$ (nodes in graph) | Evidence Graph in RAM. |
| **GPU Utilization** | 100% (during S2L/RL) | $\mathcal{O}(K)$ (active LoRAs) | Multi-LoRA switching overhead. |
| **Token Growth** | Sub-linear | $\mathcal{O}(\log L)$ via Folding | HIPIF folding operator performance. |
| **Comm. Overhead** | Low (< 5ms) | $\mathcal{O}(A)$ (number of agents) | Decision Bus throughput. |
| **Scalability** | 100+ parallel agents | $\mathcal{O}(N)$ nodes | Graph database (Neo4j) queries. |

### Bottleneck Mitigation
*   **Quadratic Scaling**: Avoided in Memory via Shannon-entropy consolidation (fixed capacity).
*   **Exponential Planning**: Avoided via HIPIF subgoal trees (limited depth) and beam search.
