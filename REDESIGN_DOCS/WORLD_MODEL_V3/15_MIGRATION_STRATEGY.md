# 15_MIGRATION_STRATEGY.md - Shadowing, Cutover, and Rollback

## Objective
Outline the safe transition from the legacy World Model (V1/V2) to the V3 Predictive Planning Engine.

## Phase 1: Side-by-Side Shadowing (1-2 Weeks)
1.  Deploy WM-V3 in "Passive Mode."
2.  The Cognitive System Controller (CSC) continues to use the legacy World Model for actual decisions.
3.  WM-V3 receives the same data streams and generates simulations and reasoning.
4.  **Shadow Audit:** Compare the utility of WM-V3's "Best Plan" vs. the legacy model's actual plan.
5.  **Success Criteria:** WM-V3's predicted best plan would have yielded > 15% better risk-adjusted returns in the shadow set.

## Phase 2: Reasoning Integration (Week 3)
1.  The CSC begins to consume WM-V3's **Reasoning Traces**.
2.  Traces are shown in the **Diagnostics Dashboard** for human review.
3.  The **Governance Shield** uses WM-V3 scenarios as an additional "Advisory Gate."

## Phase 3: Gradual Cutover (Week 4-5)
1.  Enable WM-V3 for a small subset of assets (e.g., EURUSD only).
2.  Increase the allocation of trades managed by the WM-V3 planning engine.
3.  Monitor the **Validation Framework** metrics in real-time.

## Phase 4: Full Cutover & Sunsetting (Week 6)
1.  Promote WM-V3 to the primary world model for all assets.
2.  Keep the legacy modules in "Hot Standby" for 7 days.
3.  After 7 days, delete the `latent_dynamics.py` and `v2_core.py` (skeleton) modules and archive the code.

## Rollback Strategy

### Trigger Conditions
*   **Latency Spikes:** Average planning latency > 500ms.
*   **Calibration Failure:** ECE > 0.15 for 3 consecutive hours.
*   **Financial Divergence:** Realized DD exceeds WM-V3 predicted DD by more than 20%.

### Rollback Process
1.  **Immediate Toggle:** Flip the `USE_WM_V3` flag in the `CSC_Config` to `False`.
2.  **State Reset:** The CSC flushes its current Episodic memory and reverts to the last stable state from the legacy World Model.
3.  **Audit:** Perform a Root Cause Analysis (RCA) using the HMS Research Ledger.

## Compatibility Note
Backward compatibility is **not** maintained. Migrating to V3 requires a full retraining of the model and a fresh initialization of the HMS Semantic Graph to populate the new causal nodes.
