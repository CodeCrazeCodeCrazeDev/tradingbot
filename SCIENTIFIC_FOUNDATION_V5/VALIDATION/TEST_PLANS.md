# V5 Test Plans: Unit, Integration, Stress, and Chaos

To ensure the production-readiness of the UCA V5 architecture, the following test plans must be executed during implementation.

## 1. Unit Test Plan (Component Isolation)
*   **LogAct Shared Log**: Test atomic appends, log-order consistency, and persistence recovery.
*   **QKG Triplet Store**: Test context-filtering logic ($f(Context, MarketContext)$) and expiration.
*   **Formal Invariant Checker**: Test logical verification of basic safety invariants (e.g., $exposure < limit$).
*   **DeepInsight Extractor**: Test insight extraction accuracy against a gold-standard dataset of historical trades.

## 2. Integration Test Plan (Subsystem Cohesion)
*   **Planner-Verifier Loop**: Verify that the `PlannerAgent` correctly proposes plans to the `Shared Log` and the `VerificationSwarm` votes based on formal specs.
*   **Memory-World Model Sync**: Ensure the `WorldModel` correctly pulls context-valid evidence from the QKG to inform causal induction.
*   **Hyperagent Meta-Loop**: Verify that the Meta-Agent can read its own source and the Evolution Gate successfully intercepts/verifies code changes.

## 3. Stress Test Plan (Institutional Scale)
*   **Log Throughput**: Simulate 10,000 agents/voters writing to the `Shared Log` simultaneously. Measure latency and consistency.
*   **Long-Horizon Folding**: Run a simulated 30-day continuous trading session. Measure memory growth and "Strategic Drift" after 100 folding cycles.
*   **QKG Density**: Load the QKG with 1,000,000+ contextual triplets. Measure retrieval latency under high market volatility.

## 4. Chaos Test Plan (Fault Tolerance)
*   **Voter Outage**: Randomly kill 49% of the `VerificationSwarm` voters. Verify the `LogAct` backbone correctly halts or maintains safe operations without violating consensus.
*   **Log Corruption**: Manually inject corrupted entries into the `Shared Log`. Verify the `LogAct` recovery mechanism identifies the corruption and rolls back to the last valid checkpoint.
*   **Recursive Divergence**: Force the `Hyperagent` to propose "hallucinated" self-modifications. Verify the `Evolution Gate` (RSEA) rejects the modification and maintains the system's "Monotone Safety".

## 5. Ablation Study Plan (Quantifying Contribution)
For every new V5 component, run the following:
*   **Baseline**: UCA-2026 (V4).
*   **Exp 1**: V4 + LogAct.
*   **Exp 2**: V4 + QKG.
*   **Exp 3**: V4 + DeepInsight.
*   **Exp 4**: V4 + Formal Verification.
*   **Full V5**: All components.
*   *Requirement*: Each experiment must show a statistically significant improvement in the **CL-Bench Gain Metric** or **FIRE Accuracy** to be retained.
