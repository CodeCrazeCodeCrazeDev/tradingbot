# Architecture Verification Gate: Validation & Fitness

This document defines the quantitative acceptance criteria and automated fitness tests for the UCA-2026.

---

## 1. Subsystem Acceptance Criteria

### World Model (GWM)
*   **Calibration Error**: ECE < 0.1 on price direction forecasts.
*   **Rollout Accuracy**: > 80% fidelity to tick-data replay over a 20-step horizon.
*   **Uncertainty Quality**: Epistemic uncertainty must correlate with forecast error ($r > 0.6$).
*   **Counterfactual Consistency**: $do(X)$ must yield stable, non-stochastic outcomes on deterministic inputs.

### Planner (CSC/HIPIF)
*   **Success Rate**: > 90% completion on standard institutional task set.
*   **Planning Depth**: Support for depth $\ge 10$ with zero context overflow.
*   **Folding Efficiency**: > 50% reduction in raw-to-semantic token ratio.

### Memory (HMS)
*   **Retrieval Precision**: > 0.8 on top-5 relevant trajectory search.
*   **Retrieval Latency**: < 50ms for vector/graph queries.
*   **Write Consistency**: Zero loss of high-importance episodic events during consolidation.

### Trading & Execution
*   **Sharpe Ratio**: Measurable improvement vs. legacy baseline in out-of-sample backtests.
*   **Execution Quality**: < 0.5 bps deviation from predicted slippage.
*   **Alpha Persistence**: Strategy performance decay rate $\lambda < 0.05$ per month.

---

## 2. Architecture Fitness Tests

These tests are to be integrated into the CI pipeline to enforce architectural integrity.

### 1. Singleton Orthogonality Check
*   *Test*: Verify that only one instance of `CSCController`, `UnifiedRegistry`, and `ImmutableShield` exists in the runtime.
*   *Failure*: Multiple orchestrators or registries detected.

### 2. Dependency Cycle Detection
*   *Test*: Run `pydeps` or equivalent to ensure zero circular imports between Level 1 and Level 3 components.
*   *Failure*: Circular dependency found.

### 3. Governance Bypass Test
*   *Test*: Attempt to execute a `TradeAction` directly via the `ExecutionLayer` without passing through the `ImmutableShield`.
*   *Failure*: Trade executes successfully without safety gate approval.

### 4. Grounding Verification
*   *Test*: Verify that `self_play_loop.py` imports and uses `MarketDataFeed` rather than `numpy.random`.
*   *Failure*: Reference to `np.random` found in core simulation logic.

### 5. Responsibility Uniqueness
*   *Test*: Scan for classes with the "Orchestrator" suffix outside of the `CSCController`.
*   *Failure*: Redundant orchestrator detected.
