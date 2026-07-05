# 07_MEMORY_INTEGRATION.md - HMS Interaction Protocols

## Objective
Detail how the World Model V3 integrates with the 6-tier Hierarchical Memory System (HMS) to ensure global state consistency and strategic persistence.

## 1. Unified Memory Interface
The World Model (WM) does not own an internal memory state. It interacts with the HMS via a standard Write-Manage-Read (WMR) loop.

### Memory Tier Mapping for World Model

| HMS Tier | World Model Usage (Read) | World Model Usage (Write) |
| :--- | :--- | :--- |
| **Working** | Current tick/L2 data, active orders. | Immediate prediction residuals. |
| **Episodic** | Recent trajectories, failed plans. | Newly simulated future scenarios. |
| **Semantic** | Causal graphs, regime definitions. | Refined causal weights, regime shifts. |
| **Procedural** | Alpha/Execution LoRA parameters. | Feedback on LoRA effectiveness. |
| **Research** | Historical backtest results, papers. | Validated world-state hypotheses. |
| **Long-Term** | Institutional risk priors, macro epochs. | Significant structural changes. |

## 2. The WMR Loop (Write-Manage-Read)

### Step 1: Read (Contextualization)
Before simulation, the WM queries the HMS for:
*   **Semantic Layer:** Current market regime and active causal nodes.
*   **Episodic Layer:** Success/failure of similar scenarios in the last 24 hours.
*   **Long-Term Layer:** Hard risk constraints and historical macro analogs.

### Step 2: Write (Insight Generation)
After simulation, the WM writes:
*   **Scenario Trees:** Stored in Episodic Memory for cross-agent evaluation.
*   **Causal Evidence:** New causal links discovered during $do$-calculus are written to the Semantic Graph.
*   **Reasoning Traces:** Human-readable logs are written to the Research Ledger.

### Step 3: Manage (Information Folding)
The **Folding Operator** periodically compresses World Model interactions:
*   **Trajectory Compression:** Detailed 100-step simulations are folded into a single "Strategic Summary" in the Semantic Tier.
*   **Uncertainty Pruning:** Stale or low-confidence predictions are purged from Episodic memory.

## 3. Data Schema (Simplified)

```json
{
  "hms_entry": {
    "tier": "EPISODIC",
    "origin": "WORLD_MODEL_V3",
    "timestamp": "2026-07-24T12:00:00Z",
    "content": {
      "scenarios": ["Scenario_A", "Scenario_B"],
      "causal_intervention": "do(OrderSize=1000)",
      "uncertainty_metrics": {"epistemic": 0.12, "aleatoric": 0.45},
      "reasoning_trace_id": "RT-9921"
    }
  }
}
```

## 4. Architectural Safeguard: No Duplication
The World Model is strictly prohibited from maintaining any persistent state in its own `.py` modules. All state MUST be passed through the HMS `MemoryRegistry`. This ensures that if the World Model container restarts, it can reconstruct its belief state instantly from the HMS.

## 5. Failure Modes
*   **Memory Latency:** High-frequency updates to the HMS could bottleneck the simulation.
    *   *Mitigation:* Use the **Working Memory** (Redis/In-memory) for tick-level state and async batching for Semantic/Research updates.
*   **State Conflict:** Multiple agents writing conflicting world states.
    *   *Mitigation:* The **Cognitive System Controller (CSC)** acts as the final arbiter for HMS Semantic updates.
