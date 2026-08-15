# Recursive Improvement Engine Specification (RSI-ENGINE-2026)

## 1. Engine Core and Singleton Management

The **Recursive Improvement Engine** (`RecursiveSelfImprovementEngine` in `trading_bot/recursive_self_improvement/engine.py`) is the single authoritative system responsible for coordinating and scheduling recursive improvements. Multiple independent self-improvement loops are strictly prohibited to prevent coordination failure, duplicate resource utilization, or conflicting changes.

### Architectural Invariant
```
                   [RecursiveSelfImprovementEngine] (Authoritative Singleton)
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
[WorldModel Loop]         [Strategy Loop]            [Risk Loop]
(Schedules evaluation)    (Mutates alpha logic)      (Recalibrates VaR/limits)
```

### Main Class Layout
The engine implements:
*   `register_loop(loop: BaseImprovementLoop)`: Registers specialized adapters.
*   `start()`: Main async orchestration loop.
*   `stop()`: Safe shutdown, canceling pending tasks.
*   `deploy_improvement(domain: str, proposal: Dict, result: Dict)`: Invokes the Safety Kernel and triggers version locking.

---

## 2. Specialized Subsystem Adapters

To handle system-wide capabilities, the engine utilizes modular **domain-specific adapters** extending the unified `BaseImprovementLoop` contract. Every adapter must implement `observe()` and `analyze()`:

### A. World Model Adapter
*   **Target Improvements:** Transition functions, multi-asset correlations, latent space dimension size, spread and slippage models.
*   **Evaluation Baseline:** Compare prediction error (MSE, Cross-Entropy) and calibration scores of the candidate world model against:
    1.  Naive Constant Forecast (Hold-Last-Value)
    2.  Linear/Statistical baseline (ARIMA / Vector Autoregression)
    3.  Active production World Model
*   **Metric Bounds:** The candidate model must reduce out-of-sample prediction error by at least **5%** while keeping computational latency below **15ms**.

### B. Alpha / Strategy Discovery Adapter (Evolution Laboratory)
*   **Target Improvements:** Alpha mathematical formulas, signal combinations, and decision threshold parameters.
*   **Leakage Prevention:** Enforces strict purged and embargoed cross-validation (De Prado, 2018) to avoid information leakage from train to test sets.
*   **Multiple-Testing Controls:** Adjusts significance levels using Bonferroni correction or False Discovery Rate (FDR) adjustments to prevent selecting "lucky" backtested strategies.

### C. Trading Policy Adapter
*   **Target Improvements:** Position entry/exit thresholds, trade frequency, exposure limits, and confidence-driven trade abstention.
*   **Risk Subordination:** The policy candidate cannot increase risk bounds. Any recommendation that violates deterministic risk controls is instantly vetoed by the `ImmutableShield`.

### D. Sentiment Intelligence Adapter
*   **Target Improvements:** Source weighting, event extraction confidence, event decay curves, and entity relationship strengths.
*   **Incremental Value Rule:** Sentiment features are approved only if they exhibit incremental predictive value (measured via Granger Causality or out-of-sample Mutual Information) after controlling for price lag.

### E. Failure & Root-Cause Analysis Adapter
*   **Trigger:** Activated automatically upon execution failures, high slippage events, or strategy drawdowns.
*   **Output:** Rather than blind parameter-tuning, this adapter performs automated counterfactual analysis: "If parameter X was at value Y, would this failure have been averted?" It then designs targeted experiments based on this counterfactual.

---

## 3. Meta-Improvement (Self-Optimization)

The engine can recursively improve its own self-improvement heuristics via the `MetaOptimizer` (`meta_optimizer.py`).
*   **Permitted Modifiable Parameters:** Heuristic weights, selection priority, resource allocation per subtask, and stopping criteria for trials.
*   **Safety Restriction:** The Meta-Loop can **never** modify maximum risk thresholds, the human confirmation requirement, or audit logs.
